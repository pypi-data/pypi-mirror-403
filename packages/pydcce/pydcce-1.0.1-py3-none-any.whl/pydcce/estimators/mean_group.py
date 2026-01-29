"""
Mean Group Estimator
====================

Implementation of Pesaran & Smith (1995) Mean Group Estimator.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from scipy import stats

from pydcce.estimators.base import BaseEstimator, EstimationResult


class MeanGroup(BaseEstimator):
    """
    Mean Group Estimator (Pesaran & Smith, 1995).
    
    Estimates heterogeneous panel data models by running separate
    regressions for each cross-sectional unit and averaging coefficients.
    
    Model:
        y(i,t) = b0(i) + b1(i)*y(i,t-1) + x(i,t)*b2(i) + e(i,t)
    
    The mean group estimator:
        b_MG = (1/N) * sum_{i=1}^{N} b_i
    
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
    constant : bool
        Include constant term.
    
    Examples
    --------
    >>> import pandas as pd
    >>> from pydcce import MeanGroup
    >>> 
    >>> # Load your panel data
    >>> data = pd.read_csv('panel_data.csv')
    >>> 
    >>> # Estimate Mean Group model
    >>> mg = MeanGroup(
    ...     data=data,
    ...     depvar='log_gdp',
    ...     indepvars=['log_capital', 'log_labor'],
    ...     unit_col='country',
    ...     time_col='year'
    ... )
    >>> result = mg.fit()
    >>> print(result)
    
    References
    ----------
    Pesaran, M.H., & Smith, R. (1995). Estimating long-run relationships 
    from dynamic heterogeneous panels. Journal of Econometrics, 68(1), 79-113.
    """
    
    def __init__(
        self,
        data: pd.DataFrame,
        depvar: str,
        indepvars: List[str],
        unit_col: str,
        time_col: str,
        constant: bool = True
    ):
        super().__init__(data, depvar, indepvars, unit_col, time_col)
        self.constant = constant
        self.estimator_name = "Mean Group"
    
    def fit(self) -> EstimationResult:
        """
        Fit Mean Group model.
        
        Returns
        -------
        EstimationResult
            Estimation results with coefficients, standard errors, etc.
        """
        # Storage for unit-specific coefficients
        unit_coefs = []
        unit_resids = {}
        
        # Variables list
        vars_list = self.indepvars.copy()
        if self.constant:
            vars_list = ['_cons'] + vars_list
        
        # Estimate for each unit
        for unit in self.units:
            unit_data = self.data[self.data[self.unit_col] == unit].copy()
            
            # Prepare matrices
            y = unit_data[self.depvar].values
            X = unit_data[self.indepvars].values
            
            if self.constant:
                X = np.column_stack([np.ones(len(y)), X])
            
            # Remove missing values
            valid = ~(np.isnan(y) | np.any(np.isnan(X), axis=1))
            y_valid = y[valid]
            X_valid = X[valid]
            
            if len(y_valid) < X_valid.shape[1]:
                continue  # Skip units with insufficient observations
            
            # OLS estimation: b = (X'X)^-1 X'y
            try:
                XtX_inv = np.linalg.pinv(X_valid.T @ X_valid)
                b = XtX_inv @ X_valid.T @ y_valid
                
                # Residuals
                resid = y_valid - X_valid @ b
                
                # Store coefficients
                coef_dict = {vars_list[i]: b[i] for i in range(len(b))}
                coef_dict['_unit'] = unit
                unit_coefs.append(coef_dict)
                
                # Store residuals
                unit_resids[unit] = resid
                
            except np.linalg.LinAlgError:
                continue  # Skip singular matrices
        
        # Convert to DataFrame
        individual_coefs = pd.DataFrame(unit_coefs)
        individual_coefs = individual_coefs.set_index('_unit')
        
        # Compute Mean Group coefficients
        mg_coefs = self._compute_mean_group_coef(individual_coefs)
        
        # Compute variance using MG formula
        # var(b_MG) = (1/N(N-1)) * sum_i (b_i - b_MG)^2
        mg_var = self._compute_mean_group_variance(individual_coefs, mg_coefs)
        
        # Standard errors
        std_errors = self._compute_std_errors(mg_var)
        
        # Degrees of freedom
        df = self.N - 1
        
        # t-statistics
        t_stats = self._compute_t_stats(mg_coefs, std_errors)
        
        # p-values
        p_values = self._compute_p_values(t_stats, df)
        
        # Confidence intervals
        conf_int = self._compute_conf_int(mg_coefs, std_errors, df)
        
        # Compute fitted values and residuals
        all_residuals = np.concatenate([r for r in unit_resids.values()])
        
        # R-squared (computed from individual regressions)
        y_all = self.data[self.depvar].dropna().values
        y_mean = np.mean(y_all)
        ss_res = np.sum(all_residuals ** 2)
        ss_tot = np.sum((y_all[:len(all_residuals)] - y_mean) ** 2)
        r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
        
        # Adjusted R-squared (MG version from Holly et al. 2010)
        k = len(self.indepvars) + (1 if self.constant else 0)
        r_squared_adj = 1 - (1 - r_squared) * (self.n_obs - 1) / (self.n_obs - self.N * k - 1)
        
        # Create result
        self.result = EstimationResult(
            coefficients=mg_coefs,
            std_errors=std_errors,
            t_stats=t_stats,
            p_values=p_values,
            conf_int=conf_int,
            individual_coefs=individual_coefs,
            residuals=all_residuals,
            r_squared=r_squared,
            r_squared_adj=r_squared_adj,
            N=self.N,
            T=self.T,
            n_obs=self.n_obs,
            df_model=k,
            df_resid=df,
            ssr=ss_res,
            estimator_name=self.estimator_name,
            dep_var=self.depvar
        )
        
        return self.result
    
    def get_individual_coefficients(self) -> pd.DataFrame:
        """
        Get unit-specific coefficient estimates.
        
        Returns
        -------
        pd.DataFrame
            DataFrame with coefficients for each unit.
        """
        if self.result is None:
            raise ValueError("Model must be fitted first")
        return self.result.individual_coefs
