"""
Common Correlated Effects Estimators
=====================================

Implementation of CCE (Pesaran, 2006) and Dynamic CCE (Chudik & Pesaran, 2015).
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Union
from scipy import stats

from pydcce.estimators.base import BaseEstimator, EstimationResult
from pydcce.utils.cross_sectional import compute_cross_sectional_averages


class CCE(BaseEstimator):
    """
    Common Correlated Effects Estimator (Pesaran, 2006).
    
    Accounts for cross-sectional dependence by augmenting regressions
    with cross-sectional averages of dependent and independent variables.
    
    Model:
        y(i,t) = b0(i) + x(i,t)*b(i) + d(i)*z_bar(t) + e(i,t)
    
    where z_bar(t) are cross-sectional averages.
    
    Parameters
    ----------
    data : pd.DataFrame
        Panel data in long format.
    depvar : str
        Dependent variable name.
    indepvars : list of str
        Independent variable names.
    unit_col : str
        Cross-sectional unit identifier.
    time_col : str
        Time identifier.
    csa_vars : list of str, optional
        Variables for cross-sectional averages. If None, uses depvar + indepvars.
    constant : bool
        Include constant term (default True).
    pooled_vars : list of str, optional
        Variables with homogeneous (pooled) coefficients.
    
    Examples
    --------
    >>> from pydcce import CCE
    >>> 
    >>> # Static CCE estimation
    >>> cce = CCE(
    ...     data=panel_data,
    ...     depvar='log_gdp',
    ...     indepvars=['log_capital', 'log_labor'],
    ...     unit_col='country',
    ...     time_col='year'
    ... )
    >>> result = cce.fit()
    >>> print(result)
    
    References
    ----------
    Pesaran, M.H. (2006). Estimation and inference in large heterogeneous 
    panels with a multifactor error structure. Econometrica, 74(4), 967-1012.
    """
    
    def __init__(
        self,
        data: pd.DataFrame,
        depvar: str,
        indepvars: List[str],
        unit_col: str,
        time_col: str,
        csa_vars: Optional[List[str]] = None,
        constant: bool = True,
        pooled_vars: Optional[List[str]] = None
    ):
        super().__init__(data, depvar, indepvars, unit_col, time_col)
        
        # CSA variables (default: depvar + indepvars)
        self.csa_vars = csa_vars or [depvar] + indepvars
        self.constant = constant
        self.pooled_vars = pooled_vars or []
        self.csa_lags = 0
        self.estimator_name = "CCE Mean Group"
        
        # Add cross-sectional averages
        self._add_csa()
    
    def _add_csa(self) -> None:
        """Add cross-sectional averages to data."""
        self.data = compute_cross_sectional_averages(
            self.data,
            self.csa_vars,
            self.unit_col,
            self.time_col,
            lags=self.csa_lags
        )
        
        # Build CSA variable names
        self.csa_cols = []
        for var in self.csa_vars:
            self.csa_cols.append(f"{var}_bar")
            for lag in range(1, self.csa_lags + 1):
                self.csa_cols.append(f"L{lag}_{var}_bar")
    
    def fit(self) -> EstimationResult:
        """
        Fit CCE model.
        
        Returns
        -------
        EstimationResult
            Estimation results.
        """
        # Storage
        unit_coefs = []
        all_residuals = []
        
        # Variables for regression
        mg_vars = [v for v in self.indepvars if v not in self.pooled_vars]
        vars_list = mg_vars.copy()
        if self.constant:
            vars_list = ['_cons'] + vars_list
        
        # Estimate for each unit (partialling out CSA)
        for unit in self.units:
            unit_data = self.data[self.data[self.unit_col] == unit].copy()
            unit_data = unit_data.dropna(subset=[self.depvar] + self.indepvars + self.csa_cols)
            
            if len(unit_data) < len(vars_list) + len(self.csa_cols):
                continue
            
            # Prepare matrices
            y = unit_data[self.depvar].values
            X_mg = unit_data[mg_vars].values if mg_vars else np.zeros((len(y), 0))
            Z = unit_data[self.csa_cols].values
            
            # Add constant to Z for partialling out
            Z_aug = np.column_stack([np.ones(len(y)), Z]) if self.constant else Z
            
            # Partial out CSA: M_Z = I - Z(Z'Z)^-1 Z'
            try:
                ZtZ_inv = np.linalg.pinv(Z_aug.T @ Z_aug)
                M_Z = np.eye(len(y)) - Z_aug @ ZtZ_inv @ Z_aug.T
                
                y_tilde = M_Z @ y
                X_tilde = M_Z @ X_mg if X_mg.shape[1] > 0 else X_mg
                
                # OLS on partialled out data
                if X_tilde.shape[1] > 0:
                    XtX_inv = np.linalg.pinv(X_tilde.T @ X_tilde)
                    b = XtX_inv @ X_tilde.T @ y_tilde
                else:
                    b = np.array([])
                
                # Residuals
                resid = y_tilde - X_tilde @ b if len(b) > 0 else y_tilde
                all_residuals.extend(resid)
                
                # Store coefficients
                coef_dict = {'_unit': unit}
                for i, var in enumerate(mg_vars):
                    coef_dict[var] = b[i] if len(b) > i else np.nan
                unit_coefs.append(coef_dict)
                
            except np.linalg.LinAlgError:
                continue
        
        # Process results
        if not unit_coefs:
            raise ValueError("No valid unit estimates obtained")
        
        individual_coefs = pd.DataFrame(unit_coefs).set_index('_unit')
        
        # Mean Group coefficients
        mg_coefs = self._compute_mean_group_coef(individual_coefs)
        mg_var = self._compute_mean_group_variance(individual_coefs, mg_coefs)
        std_errors = self._compute_std_errors(mg_var)
        
        df = len(unit_coefs) - 1
        t_stats = self._compute_t_stats(mg_coefs, std_errors)
        p_values = self._compute_p_values(t_stats, df)
        conf_int = self._compute_conf_int(mg_coefs, std_errors, df)
        
        # R-squared
        residuals = np.array(all_residuals)
        ss_res = np.sum(residuals ** 2)
        y_all = self.data[self.depvar].dropna().values
        ss_tot = np.sum((y_all[:len(residuals)] - np.mean(y_all[:len(residuals)])) ** 2)
        r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
        
        k = len(mg_vars) + len(self.csa_cols)
        r_squared_adj = 1 - (1 - r_squared) * (len(residuals) - 1) / (len(residuals) - k - 1)
        
        self.result = EstimationResult(
            coefficients=mg_coefs,
            std_errors=std_errors,
            t_stats=t_stats,
            p_values=p_values,
            conf_int=conf_int,
            individual_coefs=individual_coefs,
            residuals=residuals,
            r_squared=r_squared,
            r_squared_adj=r_squared_adj,
            N=self.N,
            T=self.T,
            n_obs=len(residuals),
            df_model=k,
            df_resid=df,
            ssr=ss_res,
            estimator_name=self.estimator_name,
            dep_var=self.depvar
        )
        
        return self.result


class DynamicCCE(CCE):
    """
    Dynamic Common Correlated Effects Estimator (Chudik & Pesaran, 2015).
    
    Extends CCE for dynamic panels with lagged dependent variables by
    including lags of cross-sectional averages.
    
    Model:
        y(i,t) = b0(i) + b1(i)*y(i,t-1) + x(i,t)*b2(i) + sum_{s=0}^{p_T} d(i)*z_bar(t-s) + e(i,t)
    
    Parameters
    ----------
    data : pd.DataFrame
        Panel data in long format.
    depvar : str
        Dependent variable name.
    indepvars : list of str
        Independent variables (can include lags like 'L.y').
    unit_col : str
        Cross-sectional unit identifier.
    time_col : str
        Time identifier.
    csa_lags : int
        Number of lags for cross-sectional averages (p_T).
    csa_vars : list of str, optional
        Variables for CSA. Default: depvar + indepvars.
    constant : bool
        Include constant.
    
    Examples
    --------
    >>> from pydcce import DynamicCCE
    >>> 
    >>> # Add lagged dependent variable
    >>> data['L_log_gdp'] = data.groupby('country')['log_gdp'].shift(1)
    >>> 
    >>> # Dynamic CCE with 2 CSA lags
    >>> dcce = DynamicCCE(
    ...     data=data,
    ...     depvar='log_gdp',
    ...     indepvars=['L_log_gdp', 'log_capital'],
    ...     unit_col='country',
    ...     time_col='year',
    ...     csa_lags=2
    ... )
    >>> result = dcce.fit()
    
    References
    ----------
    Chudik, A., & Pesaran, M.H. (2015). Common correlated effects estimation
    of heterogeneous dynamic panel data models with weakly exogenous regressors.
    Journal of Econometrics, 188(2), 393-420.
    """
    
    def __init__(
        self,
        data: pd.DataFrame,
        depvar: str,
        indepvars: List[str],
        unit_col: str,
        time_col: str,
        csa_lags: int = 0,
        csa_vars: Optional[List[str]] = None,
        constant: bool = True,
        pooled_vars: Optional[List[str]] = None
    ):
        # Store csa_lags before parent init (which calls _add_csa)
        self._init_csa_lags = csa_lags
        
        # Initialize parent
        super().__init__(
            data, depvar, indepvars, unit_col, time_col,
            csa_vars, constant, pooled_vars
        )
        
        self.csa_lags = csa_lags
        self.estimator_name = f"Dynamic CCE (p={csa_lags})"
        
        # Re-add CSA with proper lags
        self._add_csa()
    
    def _add_csa(self) -> None:
        """Add cross-sectional averages with lags."""
        lags = getattr(self, '_init_csa_lags', self.csa_lags)
        
        self.data = compute_cross_sectional_averages(
            self.data,
            self.csa_vars,
            self.unit_col,
            self.time_col,
            lags=lags
        )
        
        # Build CSA variable names including lags
        self.csa_cols = []
        for var in self.csa_vars:
            self.csa_cols.append(f"{var}_bar")
            for lag in range(1, lags + 1):
                self.csa_cols.append(f"L{lag}_{var}_bar")
