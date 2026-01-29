"""
Regularized CCE (rCCE) Estimator
================================

Implementation of Juodis (2022) regularized CCE approach.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from scipy import stats, linalg

from pydcce.estimators.base import BaseEstimator, EstimationResult
from pydcce.utils.cross_sectional import compute_cross_sectional_averages


class RCCE(BaseEstimator):
    """
    Regularized Common Correlated Effects Estimator (Juodis, 2022).
    
    Uses eigenvalue decomposition to reduce dimensionality of CSA,
    avoiding the bias from using too many cross-sectional averages.
    
    The rCCE approach:
    1. Compute cross-sectional averages
    2. Estimate number of factors using ER/GR criterion (Ahn & Horenstein, 2013)
    3. Replace CSA with principal components
    
    Parameters
    ----------
    data : pd.DataFrame
        Panel data.
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
    n_factors : int or str
        Number of factors. Use 'auto' for ER criterion selection.
    
    Examples
    --------
    >>> from pydcce import RCCE
    >>> 
    >>> rcce = RCCE(
    ...     data=panel_data,
    ...     depvar='log_gdp',
    ...     indepvars=['log_capital', 'log_labor'],
    ...     unit_col='country',
    ...     time_col='year',
    ...     n_factors='auto'
    ... )
    >>> result = rcce.fit()
    
    Notes
    -----
    Bootstrap standard errors are recommended with rCCE.
    
    References
    ----------
    Juodis, A. (2022). A regularized estimator for linear regression
    models with common shocks.
    
    Ahn, S.C., & Horenstein, A.R. (2013). Eigenvalue ratio test for 
    the number of factors. Econometrica, 81(3), 1203-1227.
    """
    
    def __init__(
        self,
        data: pd.DataFrame,
        depvar: str,
        indepvars: List[str],
        unit_col: str,
        time_col: str,
        csa_vars: Optional[List[str]] = None,
        n_factors: int = 4,
        constant: bool = True,
        bootstrap_reps: int = 0
    ):
        super().__init__(data, depvar, indepvars, unit_col, time_col)
        
        self.csa_vars = csa_vars or [depvar] + indepvars
        self.n_factors = n_factors
        self.constant = constant
        self.bootstrap_reps = bootstrap_reps
        self.estimator_name = "Regularized CCE"
        
        self._prepare_data()
    
    def _prepare_data(self) -> None:
        """Prepare CSA data."""
        self.data = compute_cross_sectional_averages(
            self.data,
            self.csa_vars,
            self.unit_col,
            self.time_col,
            lags=0
        )
        
        self.csa_cols = [f"{var}_bar" for var in self.csa_vars]
    
    def _estimate_n_factors(self, Z: np.ndarray) -> int:
        """
        Estimate number of factors using ER criterion.
        
        Parameters
        ----------
        Z : np.ndarray
            Cross-sectional averages matrix (T x K).
        
        Returns
        -------
        int
            Estimated number of factors.
        """
        # Compute eigenvalues
        ZtZ = Z.T @ Z / len(Z)
        eigenvalues = np.sort(np.real(linalg.eigvals(ZtZ)))[::-1]
        
        # ER criterion: argmax(lambda_j / lambda_{j+1})
        max_factors = min(len(eigenvalues) - 1, 10)
        
        if max_factors < 1:
            return 1
        
        er_ratios = eigenvalues[:max_factors] / eigenvalues[1:max_factors + 1]
        n_factors = np.argmax(er_ratios) + 1
        
        return max(1, min(n_factors, len(eigenvalues) - 1))
    
    def _extract_factors(self, Z: np.ndarray, n_factors: int) -> np.ndarray:
        """
        Extract factors using PCA.
        
        Parameters
        ----------
        Z : np.ndarray
            Cross-sectional averages.
        n_factors : int
            Number of factors.
        
        Returns
        -------
        np.ndarray
            Factor estimates (T x n_factors).
        """
        # Standardize
        Z_std = (Z - np.mean(Z, axis=0)) / (np.std(Z, axis=0) + 1e-10)
        
        # SVD
        U, S, Vt = linalg.svd(Z_std, full_matrices=False)
        
        # Extract first n_factors
        n = min(n_factors, len(S))
        factors = U[:, :n] * S[:n]
        
        return factors
    
    def fit(self) -> EstimationResult:
        """
        Fit rCCE model.
        
        Returns
        -------
        EstimationResult
            Estimation results.
        """
        unit_coefs = []
        all_residuals = []
        
        for unit in self.units:
            unit_data = self.data[self.data[self.unit_col] == unit].copy()
            
            req_cols = [self.depvar] + self.indepvars + self.csa_cols
            unit_data = unit_data.dropna(subset=req_cols)
            
            if len(unit_data) < len(self.indepvars) + 5:
                continue
            
            y = unit_data[self.depvar].values
            X = unit_data[self.indepvars].values
            Z = unit_data[self.csa_cols].values
            
            # Determine number of factors
            if self.n_factors == 'auto':
                n_factors = self._estimate_n_factors(Z)
            else:
                n_factors = self.n_factors
            
            # Extract factors
            F = self._extract_factors(Z, n_factors)
            
            # Add constant
            if self.constant:
                F = np.column_stack([np.ones(len(y)), F])
            
            try:
                # Partial out factors
                FtF_inv = np.linalg.pinv(F.T @ F)
                M_F = np.eye(len(y)) - F @ FtF_inv @ F.T
                
                y_tilde = M_F @ y
                X_tilde = M_F @ X
                
                # OLS
                XtX_inv = np.linalg.pinv(X_tilde.T @ X_tilde)
                b = XtX_inv @ X_tilde.T @ y_tilde
                
                resid = y_tilde - X_tilde @ b
                all_residuals.extend(resid)
                
                coef_dict = {'_unit': unit}
                for i, var in enumerate(self.indepvars):
                    coef_dict[var] = b[i]
                unit_coefs.append(coef_dict)
                
            except Exception:
                continue
        
        if not unit_coefs:
            raise ValueError("No valid unit estimates")
        
        individual_coefs = pd.DataFrame(unit_coefs).set_index('_unit')
        
        # Mean Group
        mg_coefs = self._compute_mean_group_coef(individual_coefs)
        mg_var = self._compute_mean_group_variance(individual_coefs, mg_coefs)
        std_errors = self._compute_std_errors(mg_var)
        
        # Bootstrap if requested
        if self.bootstrap_reps > 0:
            std_errors = self._bootstrap_se(individual_coefs, self.bootstrap_reps)
        
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
            df_model=len(self.indepvars),
            df_resid=df,
            ssr=ss_res,
            estimator_name=self.estimator_name,
            dep_var=self.depvar
        )
        
        return self.result
    
    def _bootstrap_se(
        self,
        individual_coefs: pd.DataFrame,
        reps: int
    ) -> Dict[str, float]:
        """
        Bootstrap standard errors.
        
        Parameters
        ----------
        individual_coefs : pd.DataFrame
            Unit-specific coefficients.
        reps : int
            Number of bootstrap replications.
        
        Returns
        -------
        dict
            Bootstrap standard errors.
        """
        N = len(individual_coefs)
        vars = individual_coefs.columns.tolist()
        
        boot_means = {var: [] for var in vars}
        
        for _ in range(reps):
            # Resample units with replacement
            idx = np.random.choice(N, size=N, replace=True)
            sample = individual_coefs.iloc[idx]
            
            for var in vars:
                boot_means[var].append(sample[var].mean())
        
        return {var: np.std(vals) for var, vals in boot_means.items()}
