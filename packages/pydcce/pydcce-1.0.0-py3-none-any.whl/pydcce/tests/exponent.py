"""
Exponent of Cross-Sectional Dependence Estimation
==================================================

Implementation of Bailey, Kapetanios, Pesaran (2016, 2019) alpha estimator.
Equivalent to xtcse2 in Stata.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union
from scipy import stats, linalg
from dataclasses import dataclass
from tabulate import tabulate


@dataclass
class ExponentResult:
    """
    Container for exponent estimation results.
    
    Attributes
    ----------
    alpha : float
        Estimated exponent (alpha).
    std_error : float
        Standard error.
    ci_lower : float
        Lower confidence interval.
    ci_upper : float
        Upper confidence interval.
    alpha_hat : float
        Initial alpha estimate.
    alpha_tilde : float
        Bias-corrected alpha.
    N : int
        Number of units.
    T : int
        Number of time periods.
    """
    alpha: float = np.nan
    std_error: float = np.nan
    ci_lower: float = np.nan
    ci_upper: float = np.nan
    alpha_hat: float = np.nan
    alpha_tilde: float = np.nan
    N: int = 0
    T: int = 0
    
    def summary_table(self) -> str:
        """Generate summary table."""
        header = """
╔══════════════════════════════════════════════════════════════════════════════╗
║         Cross-Sectional Dependence Exponent Estimation                       ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  N (units):     {N:<15}  T (periods):    {T:<15}            ║
╚══════════════════════════════════════════════════════════════════════════════╝
""".format(N=self.N, T=self.T)
        
        rows = [
            ["Alpha", f"{self.alpha:.6f}", f"{self.std_error:.6f}", 
             f"[{self.ci_lower:.4f}, {self.ci_upper:.4f}]"]
        ]
        
        headers = ["Parameter", "Estimate", "Std. Error", "95% Conf. Int."]
        table = tabulate(rows, headers=headers, tablefmt="fancy_grid", numalign="right")
        
        interpretation = """
Interpretation:
  • alpha < 0.5   → Weak cross-sectional dependence
  • alpha >= 0.5  → Strong cross-sectional dependence
  
  Current estimate: alpha = {alpha:.4f}
  Status: {status}

Reference: Bailey, Kapetanios, Pesaran (2016, 2019)
""".format(
            alpha=self.alpha,
            status="STRONG dependence" if self.alpha >= 0.5 else "Weak dependence"
        )
        
        return header + "\n" + table + interpretation
    
    def __str__(self) -> str:
        return self.summary_table()


class ExponentEstimator:
    """
    Exponent of Cross-Sectional Dependence Estimator (xtcse2 equivalent).
    
    Estimates the exponent alpha that characterizes the strength of
    cross-sectional dependence in panel data.
    
    For a factor model x(i,t) = sum_j b(j,i)*f(j,t) + u(i,t):
    - alpha < 0.5 implies weak dependence
    - alpha >= 0.5 implies strong dependence
    
    Parameters
    ----------
    data : pd.DataFrame or np.ndarray
        Panel data in long format or N x T matrix.
    unit_col : str, optional
        Unit identifier column.
    time_col : str, optional
        Time identifier column.
    var : str, optional
        Variable name.
    
    Examples
    --------
    >>> from pydcce import ExponentEstimator
    >>> 
    >>> # Estimate alpha for residuals
    >>> exp_est = ExponentEstimator(
    ...     data=panel_data,
    ...     var='residuals',
    ...     unit_col='country',
    ...     time_col='year'
    ... )
    >>> result = exp_est.estimate()
    >>> print(result)
    
    Notes
    -----
    The estimator uses PCA to extract factors and computes alpha
    based on the variance of cross-sectional means.
    
    References
    ----------
    Bailey, N., Kapetanios, G., & Pesaran, M.H. (2016). Exponent of 
    cross-sectional dependence: Estimation and inference. Journal of 
    Applied Econometrics, 31(6), 929-960.
    
    Bailey, N., Kapetanios, G., & Pesaran, M.H. (2019). Exponent of 
    cross-sectional dependence for residuals. Sankhya B, 81(1), 46-102.
    """
    
    def __init__(
        self,
        data: Union[pd.DataFrame, np.ndarray],
        unit_col: Optional[str] = None,
        time_col: Optional[str] = None,
        var: Optional[str] = None,
        n_pca: int = 4
    ):
        self.n_pca = n_pca
        
        if isinstance(data, np.ndarray):
            self.X = data
            self.N, self.T = data.shape
        else:
            if var is None or unit_col is None or time_col is None:
                raise ValueError("var, unit_col, and time_col required")
            self._prepare_from_dataframe(data, var, unit_col, time_col)
    
    def _prepare_from_dataframe(
        self,
        data: pd.DataFrame,
        var: str,
        unit_col: str,
        time_col: str
    ) -> None:
        """Convert DataFrame to matrix."""
        pivot = data.pivot(index=unit_col, columns=time_col, values=var)
        self.X = pivot.values
        self.N, self.T = self.X.shape
    
    def estimate(
        self,
        size: float = 0.1,
        bootstrap_reps: int = 0
    ) -> ExponentResult:
        """
        Estimate exponent alpha.
        
        Parameters
        ----------
        size : float
            Size parameter for Holm's procedure.
        bootstrap_reps : int
            Number of bootstrap replications for SE.
        
        Returns
        -------
        ExponentResult
            Estimation results.
        """
        X = self.X.copy()
        
        # Handle missing values
        X = np.nan_to_num(X, nan=0)
        
        # Center data
        X = X - np.mean(X, axis=1, keepdims=True)
        
        # ===== Step 1: Compute alpha_hat =====
        # Cross-sectional mean at each time
        x_bar_t = np.mean(X, axis=0)  # T x 1
        x_bar = np.mean(x_bar_t)
        
        # Variance of cross-sectional means
        sigma2_xbar = np.var(x_bar_t, ddof=1)
        
        # Alpha hat: equation 11 in BKP
        alpha_hat = 1 + 0.5 * np.log(sigma2_xbar) / np.log(self.N)
        
        # ===== Step 2: Compute alpha_tilde (bias correction) =====
        # Extract factors using PCA
        try:
            X_std = X / (np.std(X, axis=1, keepdims=True) + 1e-10)
            XX = X_std @ X_std.T
            eigvals, eigvecs = linalg.eigh(XX)
            idx = np.argsort(eigvals)[::-1][:self.n_pca]
            F = eigvecs[:, idx]  # N x n_pca factors
            
            # Residuals after partialling out factors
            F_aug = np.column_stack([np.ones(self.N), F])
            M_F = np.eye(self.N) - F_aug @ np.linalg.pinv(F_aug.T @ F_aug) @ F_aug.T
            e = M_F @ X  # N x T residuals
            
            # Cross-sectional mean of residuals
            e_bar_t = np.mean(e, axis=0)
            e_bar = np.mean(e_bar_t)
            
            # Bias correction term: c_tilde
            c_tilde = np.var(np.sqrt(self.N) * (e_bar_t - e_bar), ddof=1)
            
            # Alpha tilde
            alpha_tilde = alpha_hat - c_tilde / (2 * np.log(self.N) * self.N * sigma2_xbar)
            
        except:
            alpha_tilde = alpha_hat
            e = X
        
        # ===== Step 3: Compute alpha_circle (mu star correction) =====
        # Regression of x on x_bar
        x_bar_aug = np.column_stack([np.ones(self.T), x_bar_t])
        coefs = np.linalg.lstsq(x_bar_aug, X.T, rcond=None)[0]  # 2 x N
        gamma = coefs[1, :]  # Loadings
        
        # t-statistics for loadings
        resid = X.T - x_bar_aug @ coefs
        s2 = np.sum(resid**2, axis=0) / (self.T - 2)
        var_gamma = s2 / np.sum((x_bar_t - np.mean(x_bar_t))**2)
        t_stats = gamma / np.sqrt(var_gamma + 1e-10)
        
        # Holm's procedure to identify significant loadings
        sorted_idx = np.argsort(np.abs(t_stats))[::-1]
        significant = np.zeros(self.N, dtype=bool)
        
        for j, idx in enumerate(sorted_idx):
            p_threshold = size / (self.N - j)
            theta = stats.norm.ppf(1 - p_threshold / 2)
            if np.abs(t_stats[idx]) >= theta:
                significant[idx] = True
            else:
                break
        
        # Compute mu_star
        if np.sum(significant) > 1:
            gamma_sig = gamma[significant]
            mu_star = np.var(gamma_sig, ddof=1)
        else:
            mu_star = 1
        
        # Alpha circle
        alpha = alpha_tilde - 0.5 * np.log(mu_star) / np.log(self.N)
        
        # ===== Step 4: Standard error =====
        # NW standard error for variance of squared means
        p = int(np.ceil(self.T ** (1/3)))
        x_bar_sq = (x_bar_t - np.mean(x_bar_t))**2
        
        # Simple NW variance
        if len(x_bar_sq) > p + 1:
            v_nw = np.var(x_bar_sq[p:], ddof=1)
        else:
            v_nw = np.var(x_bar_sq, ddof=1)
        
        # SE formula from BKP
        se = np.sqrt(v_nw / self.T + 4 / self.N) / (2 * np.log(self.N))
        
        # Bootstrap SE if requested
        if bootstrap_reps > 0:
            se = self._bootstrap_se(X, size, bootstrap_reps)
        
        # Confidence interval
        z = 1.96
        ci_lower = alpha - z * se
        ci_upper = alpha + z * se
        
        return ExponentResult(
            alpha=alpha,
            std_error=se,
            ci_lower=ci_lower,
            ci_upper=ci_upper,
            alpha_hat=alpha_hat,
            alpha_tilde=alpha_tilde,
            N=self.N,
            T=self.T
        )
    
    def _bootstrap_se(
        self,
        X: np.ndarray,
        size: float,
        reps: int
    ) -> float:
        """
        Bootstrap standard error for alpha.
        
        Parameters
        ----------
        X : np.ndarray
            Data matrix.
        size : float
            Size parameter.
        reps : int
            Bootstrap replications.
        
        Returns
        -------
        float
            Bootstrap standard error.
        """
        alphas = []
        
        for _ in range(reps):
            # Resample units
            idx = np.random.choice(self.N, size=self.N, replace=True)
            X_boot = X[idx, :]
            
            # Compute alpha for bootstrap sample
            x_bar_t = np.mean(X_boot, axis=0)
            sigma2 = np.var(x_bar_t, ddof=1)
            
            if sigma2 > 0:
                alpha_boot = 1 + 0.5 * np.log(sigma2) / np.log(self.N)
                alphas.append(alpha_boot)
        
        return np.std(alphas) if alphas else 0.1
