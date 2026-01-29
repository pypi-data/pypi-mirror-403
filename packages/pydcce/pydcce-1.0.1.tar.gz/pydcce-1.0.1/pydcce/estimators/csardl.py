"""
Cross-Section Augmented ARDL (CS-ARDL) Estimator
=================================================

Implementation of CS-ARDL for long-run coefficient estimation.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from scipy import stats

from pydcce.estimators.base import BaseEstimator, EstimationResult
from pydcce.utils.cross_sectional import compute_cross_sectional_averages


class CSARDL(BaseEstimator):
    """
    Cross-Section Augmented ARDL Estimator (Chudik et al., 2016).
    
    Estimates ARDL model with cross-sectional averages and computes
    long-run coefficients from short-run estimates.
    
    Model:
        y(i,t) = b0(i) + sum_{l=1}^{py} b1(i,l)*y(i,t-l) 
                 + sum_{l=0}^{px} b2(i,l)*x(i,t-l) + CSA + e(i,t)
    
    Long-run coefficients:
        w(i) = sum_{l=0}^{px} b2(i,l) / (1 - sum_{l=1}^{py} b1(i,l))
    
    Parameters
    ----------
    data : pd.DataFrame
        Panel data.
    depvar : str
        Dependent variable.
    indepvars : list of str
        Independent variables (levels).
    py : int
        Lags of dependent variable.
    px : int
        Lags of independent variables.
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
    >>> from pydcce import CSARDL
    >>> 
    >>> csardl = CSARDL(
    ...     data=panel_data,
    ...     depvar='log_gdp',
    ...     indepvars=['log_capital', 'log_labor'],
    ...     py=1,  # 1 lag of dependent
    ...     px=1,  # 1 lag of independent
    ...     unit_col='country',
    ...     time_col='year',
    ...     csa_lags=2
    ... )
    >>> result = csardl.fit()
    
    References
    ----------
    Chudik, A., Mohaddes, K., Pesaran, M.H., & Raissi, M. (2016).
    """
    
    def __init__(
        self,
        data: pd.DataFrame,
        depvar: str,
        indepvars: List[str],
        py: int = 1,
        px: int = 1,
        unit_col: str = 'id',
        time_col: str = 'time',
        csa_vars: Optional[List[str]] = None,
        csa_lags: int = 0,
        constant: bool = True
    ):
        super().__init__(data, depvar, indepvars, unit_col, time_col)
        
        self.py = py  # Lags of y
        self.px = px  # Lags of x
        self.csa_vars = csa_vars or [depvar] + indepvars
        self.csa_lags = csa_lags
        self.constant = constant
        self.estimator_name = f"CS-ARDL({py},{px})"
        
        self._prepare_data()
    
    def _prepare_data(self) -> None:
        """Prepare ARDL data with lags and CSA."""
        # Add lags of dependent variable
        self.y_lags = []
        for lag in range(1, self.py + 1):
            lag_name = f"L{lag}_{self.depvar}"
            self.data[lag_name] = self.data.groupby(self.unit_col)[self.depvar].shift(lag)
            self.y_lags.append(lag_name)
        
        # Add lags of independent variables
        self.x_lags = []
        for var in self.indepvars:
            for lag in range(1, self.px + 1):
                lag_name = f"L{lag}_{var}"
                self.data[lag_name] = self.data.groupby(self.unit_col)[var].shift(lag)
                self.x_lags.append(lag_name)
        
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
        Fit CS-ARDL model and compute long-run coefficients.
        
        Returns
        -------
        EstimationResult
            Short-run and long-run coefficient estimates.
        """
        unit_coefs = []
        all_residuals = []
        
        # All short-run variables
        sr_vars = self.y_lags + self.indepvars + self.x_lags
        
        for unit in self.units:
            unit_data = self.data[self.data[self.unit_col] == unit].copy()
            
            req_cols = [self.depvar] + sr_vars + self.csa_cols
            unit_data = unit_data.dropna(subset=req_cols)
            
            if len(unit_data) < len(sr_vars) + len(self.csa_cols) + 2:
                continue
            
            y = unit_data[self.depvar].values
            X_sr = unit_data[sr_vars].values
            Z = unit_data[self.csa_cols].values
            
            if self.constant:
                Z = np.column_stack([np.ones(len(y)), Z])
            
            try:
                # Partial out CSA
                ZtZ_inv = np.linalg.pinv(Z.T @ Z)
                M_Z = np.eye(len(y)) - Z @ ZtZ_inv @ Z.T
                
                y_tilde = M_Z @ y
                X_tilde = M_Z @ X_sr
                
                # OLS
                XtX_inv = np.linalg.pinv(X_tilde.T @ X_tilde)
                b = XtX_inv @ X_tilde.T @ y_tilde
                
                resid = y_tilde - X_tilde @ b
                all_residuals.extend(resid)
                
                coef_dict = {'_unit': unit}
                for i, var in enumerate(sr_vars):
                    coef_dict[var] = b[i]
                unit_coefs.append(coef_dict)
                
            except Exception:
                continue
        
        if not unit_coefs:
            raise ValueError("No valid unit estimates")
        
        individual_coefs = pd.DataFrame(unit_coefs).set_index('_unit')
        
        # Compute long-run coefficients for each unit
        # LR = sum(b_x) / (1 - sum(b_y))
        lr_coefs_unit = {}
        
        for var in self.indepvars:
            lr_name = f"LR_{var}"
            lr_vals = []
            
            for unit in individual_coefs.index:
                # Sum of x coefficients (contemporaneous + lags)
                sum_bx = individual_coefs.loc[unit, var]
                for lag in range(1, self.px + 1):
                    lag_name = f"L{lag}_{var}"
                    if lag_name in individual_coefs.columns:
                        sum_bx += individual_coefs.loc[unit, lag_name]
                
                # Sum of y lag coefficients
                sum_by = 0
                for lag in range(1, self.py + 1):
                    lag_name = f"L{lag}_{self.depvar}"
                    if lag_name in individual_coefs.columns:
                        sum_by += individual_coefs.loc[unit, lag_name]
                
                # LR coefficient
                denom = 1 - sum_by
                if abs(denom) > 1e-10:
                    lr_vals.append(sum_bx / denom)
            
            lr_coefs_unit[lr_name] = lr_vals
        
        # Mean Group for long-run
        lr_mg = {k: np.mean(v) for k, v in lr_coefs_unit.items()}
        lr_var = {k: np.var(v, ddof=1) / len(v) for k, v in lr_coefs_unit.items()}
        lr_se = {k: np.sqrt(v) for k, v in lr_var.items()}
        
        # MG for short-run
        sr_mg = self._compute_mean_group_coef(individual_coefs)
        sr_var = self._compute_mean_group_variance(individual_coefs, sr_mg)
        sr_se = self._compute_std_errors(sr_var)
        
        # Combine
        all_coefs = {**sr_mg, **lr_mg}
        all_se = {**sr_se, **lr_se}
        
        df = len(unit_coefs) - 1
        t_stats = self._compute_t_stats(all_coefs, all_se)
        p_values = self._compute_p_values(t_stats, df)
        conf_int = self._compute_conf_int(all_coefs, all_se, df)
        
        residuals = np.array(all_residuals)
        ss_res = np.sum(residuals ** 2)
        y_all = self.data[self.depvar].dropna().values[:len(residuals)]
        ss_tot = np.sum((y_all - np.mean(y_all)) ** 2)
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
            df_model=len(sr_vars),
            df_resid=df,
            ssr=ss_res,
            estimator_name=self.estimator_name,
            dep_var=self.depvar
        )
        
        return self.result
