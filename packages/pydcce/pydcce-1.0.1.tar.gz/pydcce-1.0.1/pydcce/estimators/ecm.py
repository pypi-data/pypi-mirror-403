"""
Error Correction Model (ECM/PMG)
================================

Implementation of Error Correction Model with long-run coefficients.
Based on Shin et al. (1999) and extended for CCE (Ditzen, 2018).
"""

import warnings

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from scipy import stats

from pydcce.estimators.base import BaseEstimator, EstimationResult
from pydcce.utils.cross_sectional import compute_cross_sectional_averages
from pydcce.utils.matrix import delta_method_variance


class ECM(BaseEstimator):
    """
    Error Correction Model / Pooled Mean Group Estimator.
    
    Estimates models with heterogeneous short-run and homogeneous 
    long-run coefficients.
    
    Model:
        Δy(i,t) = φ(i)*(y(i,t-1) - θ*x(i,t-1)) + γ(i)*Δx(i,t) + e(i,t)
    
    where φ(i) is the error correction term and θ are long-run coefficients.
    
    Parameters
    ----------
    data : pd.DataFrame
        Panel data in long format.
    depvar : str
        Dependent variable (in levels).
    lr_vars : list of str
        Long-run variables (in levels).
    sr_vars : list of str, optional
        Short-run variables (typically differences).
    unit_col : str
        Unit identifier.
    time_col : str
        Time identifier.
    csa_vars : list of str, optional
        Variables for cross-sectional averages.
    csa_lags : int
        Lags of CSA.
    
    Examples
    --------
    >>> from pydcce import ECM
    >>> 
    >>> # Prepare differenced variables
    >>> data['D_log_gdp'] = data.groupby('country')['log_gdp'].diff()
    >>> data['D_log_capital'] = data.groupby('country')['log_capital'].diff()
    >>> data['L_log_gdp'] = data.groupby('country')['log_gdp'].shift(1)
    >>> 
    >>> ecm = ECM(
    ...     data=data,
    ...     depvar='D_log_gdp',
    ...     lr_vars=['L_log_gdp', 'log_capital'],
    ...     sr_vars=['D_log_capital'],
    ...     unit_col='country',
    ...     time_col='year'
    ... )
    >>> result = ecm.fit()
    
    Notes
    -----
    Long-run coefficients are computed as: w = -b_x / b_y
    where b_y is the coefficient on the lagged dependent variable
    and b_x is the coefficient on the long-run x variable.
    
    Standard errors are computed using the delta method.
    
    References
    ----------
    Shin, Y., Smith, R.P., & Kim, M.S. (1999). Pooled mean group estimation
    of dynamic heterogeneous panels.
    
    Ditzen, J. (2018). Estimating dynamic common-correlated effects in Stata.
    The Stata Journal, 18(3), 585-617.
    """
    
    def __init__(
        self,
        data: pd.DataFrame,
        depvar: str,
        lr_vars: List[str],
        sr_vars: Optional[List[str]] = None,
        unit_col: str = 'id',
        time_col: str = 'time',
        csa_vars: Optional[List[str]] = None,
        csa_lags: int = 0,
        constant: bool = True
    ):
        # All vars for base class
        all_vars = lr_vars + (sr_vars or [])
        super().__init__(data, depvar, all_vars, unit_col, time_col)
        
        self.lr_vars = lr_vars
        self.sr_vars = sr_vars or []
        self.csa_vars = csa_vars
        self.csa_lags = csa_lags
        self.constant = constant
        self.estimator_name = "ECM/PMG"
        
        # Add CSA if specified
        if self.csa_vars:
            self._add_csa()
    
    def _add_csa(self) -> None:
        """Add cross-sectional averages."""
        self.data = compute_cross_sectional_averages(
            self.data,
            self.csa_vars,
            self.unit_col,
            self.time_col,
            lags=self.csa_lags
        )
        
        self.csa_cols = []
        for var in self.csa_vars:
            self.csa_cols.append(f"{var}_bar")
            for lag in range(1, self.csa_lags + 1):
                self.csa_cols.append(f"L{lag}_{var}_bar")
    
    def fit(self) -> EstimationResult:
        """
        Fit ECM model.
        
        Returns
        -------
        EstimationResult
            Results with short-run MG and long-run coefficients.
        """
        # Storage
        unit_coefs = []
        all_residuals = []
        
        all_vars = self.lr_vars + self.sr_vars
        vars_list = ['_cons'] + all_vars if self.constant else all_vars
        
        csa_cols = getattr(self, 'csa_cols', [])
        
        for unit in self.units:
            unit_data = self.data[self.data[self.unit_col] == unit].copy()
            
            req_cols = [self.depvar] + all_vars + csa_cols
            unit_data = unit_data.dropna(subset=req_cols)
            
            if len(unit_data) < len(vars_list) + len(csa_cols):
                continue
            
            y = unit_data[self.depvar].values
            X_lr = unit_data[self.lr_vars].values
            X_sr = unit_data[self.sr_vars].values if self.sr_vars else np.zeros((len(y), 0))
            X = np.column_stack([X_lr, X_sr]) if X_sr.shape[1] > 0 else X_lr
            
            if self.constant:
                X = np.column_stack([np.ones(len(y)), X])
            
            # Partial out CSA if present
            if csa_cols:
                Z = unit_data[csa_cols].values
                try:
                    ZtZ_inv = np.linalg.pinv(Z.T @ Z)
                    M_Z = np.eye(len(y)) - Z @ ZtZ_inv @ Z.T
                    y = M_Z @ y
                    X = M_Z @ X
                except Exception:
                    continue
            
            # OLS
            try:
                XtX_inv = np.linalg.pinv(X.T @ X)
                b = XtX_inv @ X.T @ y
                resid = y - X @ b
                all_residuals.extend(resid)
                
                coef_dict = {'_unit': unit}
                for i, var in enumerate(vars_list):
                    coef_dict[var] = b[i]
                unit_coefs.append(coef_dict)
                
            except Exception:
                continue
        
        if not unit_coefs:
            raise ValueError("No valid unit estimates")
        
        individual_coefs = pd.DataFrame(unit_coefs).set_index('_unit')
        
        # Mean Group short-run coefficients
        mg_coefs = self._compute_mean_group_coef(individual_coefs)
        mg_var = self._compute_mean_group_variance(individual_coefs, mg_coefs)
        std_errors = self._compute_std_errors(mg_var)
        
        # Compute long-run coefficients
        # Assume first LR var is EC term (phi), others are LR effects
        lr_coefs = {}
        lr_se = {}
        
        if len(self.lr_vars) > 1:
            ec_var = self.lr_vars[0]  # Error correction term
            ec_coef = mg_coefs.get(ec_var, mg_coefs.get('_cons', 0))
            
            # Warn if EC coefficient is positive (inconsistent with ECM theory)
            if ec_coef > 0:
                warnings.warn(
                    f"Error correction coefficient ({ec_var}) is positive ({ec_coef:.4f}). "
                    "In ECM, this coefficient should typically be negative for convergence. "
                    "Check your model specification.",
                    UserWarning
                )
            
            for var in self.lr_vars[1:]:
                # Long-run: w = -b_x / phi
                b_x = mg_coefs.get(var, 0)
                if ec_coef != 0:
                    lr_coefs[f"LR_{var}"] = -b_x / ec_coef
                    # Delta method SE (simplified)
                    lr_se[f"LR_{var}"] = abs(std_errors.get(var, 0) / ec_coef)
        
        # Add LR to results
        all_coefs = {**mg_coefs, **lr_coefs}
        all_se = {**std_errors, **lr_se}
        
        df = len(unit_coefs) - 1
        t_stats = self._compute_t_stats(all_coefs, all_se)
        p_values = self._compute_p_values(t_stats, df)
        conf_int = self._compute_conf_int(all_coefs, all_se, df)
        
        residuals = np.array(all_residuals)
        ss_res = np.sum(residuals ** 2)
        ss_tot = np.sum((residuals - np.mean(residuals)) ** 2)
        r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
        
        self.result = EstimationResult(
            coefficients=all_coefs,
            std_errors=all_se,
            t_stats=t_stats,
            p_values=p_values,
            conf_int=conf_int,
            individual_coefs=individual_coefs,
            residuals=residuals,
            r_squared=r_squared,
            r_squared_adj=r_squared,
            N=self.N,
            T=self.T,
            n_obs=len(residuals),
            df_model=len(all_vars),
            df_resid=df,
            ssr=ss_res,
            estimator_name=self.estimator_name,
            dep_var=self.depvar
        )
        
        return self.result
