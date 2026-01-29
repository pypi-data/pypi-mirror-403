"""
Pooled CCE Estimator
====================

Implementation of Pooled CCE with homogeneous coefficients (Pesaran, 2006).
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from scipy import stats

from pydcce.estimators.base import BaseEstimator, EstimationResult
from pydcce.utils.cross_sectional import compute_cross_sectional_averages


class PooledCCE(BaseEstimator):
    """
    Pooled Common Correlated Effects Estimator.
    
    Estimates homogeneous (pooled) coefficients across units while
    accounting for cross-sectional dependence via CSA.
    
    Model:
        y(i,t) = b0 + x(i,t)*b + d(i)*z_bar(t) + e(i,t)
    
    Parameters
    ----------
    data : pd.DataFrame
        Panel data in long format.
    depvar : str
        Dependent variable.
    indepvars : list of str
        Independent variables.
    unit_col : str
        Unit identifier.
    time_col : str
        Time identifier.
    csa_vars : list of str, optional
        Variables for CSA.
    csa_lags : int
        Lags of CSA.
    constant : bool
        Include constant.
    
    Examples
    --------
    >>> from pydcce import PooledCCE
    >>> 
    >>> pcce = PooledCCE(
    ...     data=panel_data,
    ...     depvar='log_gdp',
    ...     indepvars=['log_capital', 'log_labor'],
    ...     unit_col='country',
    ...     time_col='year'
    ... )
    >>> result = pcce.fit()
    
    Notes
    -----
    The standard errors are computed using the formula from Pesaran (2006)
    for pooled estimations with cross-sectional dependence.
    """
    
    def __init__(
        self,
        data: pd.DataFrame,
        depvar: str,
        indepvars: List[str],
        unit_col: str,
        time_col: str,
        csa_vars: Optional[List[str]] = None,
        csa_lags: int = 0,
        constant: bool = True
    ):
        super().__init__(data, depvar, indepvars, unit_col, time_col)
        
        self.csa_vars = csa_vars or [depvar] + indepvars
        self.csa_lags = csa_lags
        self.constant = constant
        self.estimator_name = "Pooled CCE"
        
        # Add CSA
        self._add_csa()
        
        # Build CSA column names
        self.csa_cols = []
        for var in self.csa_vars:
            self.csa_cols.append(f"{var}_bar")
            for lag in range(1, self.csa_lags + 1):
                self.csa_cols.append(f"L{lag}_{var}_bar")
    
    def _add_csa(self) -> None:
        """Add cross-sectional averages."""
        self.data = compute_cross_sectional_averages(
            self.data,
            self.csa_vars,
            self.unit_col,
            self.time_col,
            lags=self.csa_lags
        )
    
    def fit(self) -> EstimationResult:
        """
        Fit Pooled CCE model.
        
        Returns
        -------
        EstimationResult
            Estimation results.
        """
        # Drop missing
        valid_cols = [self.depvar] + self.indepvars + self.csa_cols
        working_data = self.data.dropna(subset=valid_cols).copy()
        
        # Storage for partialled-out data by unit
        y_tilde_all = []
        X_tilde_all = []
        
        for unit in self.units:
            unit_data = working_data[working_data[self.unit_col] == unit]
            
            if len(unit_data) < len(self.csa_cols) + 2:
                continue
            
            y = unit_data[self.depvar].values
            X = unit_data[self.indepvars].values
            Z = unit_data[self.csa_cols].values
            
            # Add constant to Z
            Z_aug = np.column_stack([np.ones(len(y)), Z])
            
            try:
                # Partial out CSA
                ZtZ_inv = np.linalg.pinv(Z_aug.T @ Z_aug)
                M_Z = np.eye(len(y)) - Z_aug @ ZtZ_inv @ Z_aug.T
                
                y_tilde = M_Z @ y
                X_tilde = M_Z @ X
                
                y_tilde_all.append(y_tilde)
                X_tilde_all.append(X_tilde)
                
            except np.linalg.LinAlgError:
                continue
        
        # Stack all data
        y_tilde = np.concatenate(y_tilde_all)
        X_tilde = np.vstack(X_tilde_all)
        
        # Pooled OLS
        XtX_inv = np.linalg.pinv(X_tilde.T @ X_tilde)
        b = XtX_inv @ X_tilde.T @ y_tilde
        
        # Residuals
        residuals = y_tilde - X_tilde @ b
        
        # Variance (using mean group approach for robustness)
        # First get unit-specific coefficients for variance
        n_vars = len(self.indepvars)
        unit_coefs_list = []
        
        for unit in self.units:
            unit_data = working_data[working_data[self.unit_col] == unit]
            if len(unit_data) < len(self.csa_cols) + n_vars + 2:
                continue
            
            y = unit_data[self.depvar].values
            X = unit_data[self.indepvars].values
            Z = unit_data[self.csa_cols].values
            Z_aug = np.column_stack([np.ones(len(y)), Z])
            
            try:
                ZtZ_inv = np.linalg.pinv(Z_aug.T @ Z_aug)
                M_Z = np.eye(len(y)) - Z_aug @ ZtZ_inv @ Z_aug.T
                
                y_t = M_Z @ y
                X_t = M_Z @ X
                
                XtX_inv_i = np.linalg.pinv(X_t.T @ X_t)
                b_i = XtX_inv_i @ X_t.T @ y_t
                unit_coefs_list.append(b_i)
            except Exception:
                continue
        
        # Compute variance from unit coefficients
        unit_coefs_arr = np.array(unit_coefs_list)
        N_valid = len(unit_coefs_list)
        
        variances = {}
        for i, var in enumerate(self.indepvars):
            dev = unit_coefs_arr[:, i] - b[i]
            variances[var] = np.sum(dev ** 2) / (N_valid * (N_valid - 1))
        
        # Build result dictionaries
        coefs = {self.indepvars[i]: b[i] for i in range(len(b))}
        std_errors = {k: np.sqrt(v) for k, v in variances.items()}
        
        df = N_valid - 1
        t_stats = self._compute_t_stats(coefs, std_errors)
        p_values = self._compute_p_values(t_stats, df)
        conf_int = self._compute_conf_int(coefs, std_errors, df)
        
        # R-squared
        ss_res = np.sum(residuals ** 2)
        ss_tot = np.sum((y_tilde - np.mean(y_tilde)) ** 2)
        r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
        
        k = len(self.indepvars) + len(self.csa_cols)
        n = len(residuals)
        r_squared_adj = 1 - (1 - r_squared) * (n - 1) / (n - k - 1) if n > k + 1 else 0.0
        
        self.result = EstimationResult(
            coefficients=coefs,
            std_errors=std_errors,
            t_stats=t_stats,
            p_values=p_values,
            conf_int=conf_int,
            residuals=residuals,
            r_squared=r_squared,
            r_squared_adj=r_squared_adj,
            N=self.N,
            T=self.T,
            n_obs=n,
            df_model=k,
            df_resid=df,
            ssr=ss_res,
            estimator_name=self.estimator_name,
            dep_var=self.depvar
        )
        
        return self.result
