"""
Cross-Section Augmented Distributed Lag (CS-DL) Estimator
==========================================================

Implementation of Chudik et al. (2016) CS-DL estimator for 
direct long-run coefficient estimation.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from scipy import stats

from pydcce.estimators.base import BaseEstimator, EstimationResult
from pydcce.utils.cross_sectional import compute_cross_sectional_averages


class CSDL(BaseEstimator):
    """
    Cross-Section Augmented Distributed Lag Estimator.
    
    Directly estimates long-run effects without estimating short-run dynamics.
    
    Model:
        y(i,t) = w0(i) + x(i,t)*w(i) + sum_{l=1}^{px} δ(i,l)*Δx(i,t-l) 
                 + sum_{s=0}^{pT} d(i)*z_bar(t-s) + e(i,t)
    
    where w(i) are the long-run coefficients.
    
    Parameters
    ----------
    data : pd.DataFrame
        Panel data.
    depvar : str
        Dependent variable.
    lr_vars : list of str
        Long-run variables (levels).
    px : int
        Number of lags of differences to include.
    unit_col : str
        Unit identifier.
    time_col : str
        Time identifier.
    csa_vars : list of str, optional
        Variables for CSA.
    csa_lags : int
        Lags of CSA.
    
    Examples
    --------
    >>> from pydcce import CSDL
    >>> 
    >>> csdl = CSDL(
    ...     data=panel_data,
    ...     depvar='log_gdp',
    ...     lr_vars=['log_capital', 'log_labor'],
    ...     px=2,  # Include 2 lags of differences
    ...     unit_col='country',
    ...     time_col='year',
    ...     csa_lags=2
    ... )
    >>> result = csdl.fit()
    
    Notes
    -----
    The CS-DL approach avoids estimating short-run coefficients, making
    it more efficient when only long-run effects are of interest.
    
    References
    ----------
    Chudik, A., Mohaddes, K., Pesaran, M.H., & Raissi, M. (2016).
    Long-run effects in large heterogeneous panel data models with 
    cross-sectionally correlated errors.
    """
    
    def __init__(
        self,
        data: pd.DataFrame,
        depvar: str,
        lr_vars: List[str],
        px: int = 1,
        unit_col: str = 'id',
        time_col: str = 'time',
        csa_vars: Optional[List[str]] = None,
        csa_lags: int = 0,
        constant: bool = True
    ):
        super().__init__(data, depvar, lr_vars, unit_col, time_col)
        
        self.lr_vars = lr_vars
        self.px = px
        self.csa_vars = csa_vars or [depvar] + lr_vars
        self.csa_lags = csa_lags
        self.constant = constant
        self.estimator_name = "CS-DL"
        
        # Add differences and CSA
        self._prepare_data()
    
    def _prepare_data(self) -> None:
        """Prepare data with differences and CSA."""
        # Add differences of LR variables
        self.diff_vars = []
        for var in self.lr_vars:
            for lag in range(1, self.px + 1):
                diff_name = f"DL{lag}_{var}"
                # First difference, then lag
                self.data[f"D_{var}"] = self.data.groupby(self.unit_col)[var].diff()
                self.data[diff_name] = self.data.groupby(self.unit_col)[f"D_{var}"].shift(lag - 1)
                self.diff_vars.append(diff_name)
        
        # Add CSA
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
        Fit CS-DL model.
        
        Returns
        -------
        EstimationResult
            Long-run coefficient estimates.
        """
        unit_coefs = []
        all_residuals = []
        
        all_vars = self.lr_vars + self.diff_vars
        
        for unit in self.units:
            unit_data = self.data[self.data[self.unit_col] == unit].copy()
            
            req_cols = [self.depvar] + all_vars + self.csa_cols
            unit_data = unit_data.dropna(subset=req_cols)
            
            if len(unit_data) < len(all_vars) + len(self.csa_cols) + 2:
                continue
            
            y = unit_data[self.depvar].values
            X_lr = unit_data[self.lr_vars].values
            X_diff = unit_data[self.diff_vars].values if self.diff_vars else np.zeros((len(y), 0))
            Z = unit_data[self.csa_cols].values
            
            # Build X matrix
            X = np.column_stack([X_lr, X_diff]) if X_diff.shape[1] > 0 else X_lr
            
            if self.constant:
                Z = np.column_stack([np.ones(len(y)), Z])
            
            try:
                # Partial out CSA
                ZtZ_inv = np.linalg.pinv(Z.T @ Z)
                M_Z = np.eye(len(y)) - Z @ ZtZ_inv @ Z.T
                
                y_tilde = M_Z @ y
                X_tilde = M_Z @ X
                
                # OLS
                XtX_inv = np.linalg.pinv(X_tilde.T @ X_tilde)
                b = XtX_inv @ X_tilde.T @ y_tilde
                
                resid = y_tilde - X_tilde @ b
                all_residuals.extend(resid)
                
                coef_dict = {'_unit': unit}
                for i, var in enumerate(all_vars):
                    coef_dict[var] = b[i]
                unit_coefs.append(coef_dict)
                
            except Exception:
                continue
        
        if not unit_coefs:
            raise ValueError("No valid unit estimates")
        
        individual_coefs = pd.DataFrame(unit_coefs).set_index('_unit')
        
        # Extract only LR coefficients for mean group
        lr_individual = individual_coefs[self.lr_vars]
        
        mg_coefs = self._compute_mean_group_coef(lr_individual)
        mg_var = self._compute_mean_group_variance(lr_individual, mg_coefs)
        std_errors = self._compute_std_errors(mg_var)
        
        df = len(unit_coefs) - 1
        t_stats = self._compute_t_stats(mg_coefs, std_errors)
        p_values = self._compute_p_values(t_stats, df)
        conf_int = self._compute_conf_int(mg_coefs, std_errors, df)
        
        residuals = np.array(all_residuals)
        ss_res = np.sum(residuals ** 2)
        y_all = self.data[self.depvar].dropna().values[:len(residuals)]
        ss_tot = np.sum((y_all - np.mean(y_all)) ** 2)
        r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
        
        self.result = EstimationResult(
            coefficients=mg_coefs,
            std_errors=std_errors,
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
