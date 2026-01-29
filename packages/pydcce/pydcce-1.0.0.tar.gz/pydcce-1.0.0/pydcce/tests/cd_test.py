"""
Cross-Sectional Dependence Tests
================================

Implementation of CD tests from xtcd2 (Pesaran, 2015, 2021).
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union
from scipy import stats, linalg
from dataclasses import dataclass
from tabulate import tabulate


@dataclass
class CDTestResult:
    """
    Container for CD test results.
    
    Attributes
    ----------
    cd : float
        CD test statistic.
    p_value : float
        p-value.
    cdw : float
        Weighted CD test statistic (Juodis & Reese).
    cdw_p : float
        p-value for CDw.
    cdw_plus : float
        Power enhanced CDw.
    cdw_plus_p : float
        p-value for CDw+.
    cd_star : float
        CD* test statistic (Pesaran & Xie).
    cd_star_p : float
        p-value for CD*.
    rho_mean : float
        Mean of pairwise correlations.
    N : int
        Number of units.
    T : int
        Number of time periods.
    """
    cd: float = np.nan
    p_value: float = np.nan
    cdw: float = np.nan
    cdw_p: float = np.nan
    cdw_plus: float = np.nan
    cdw_plus_p: float = np.nan
    cd_star: float = np.nan
    cd_star_p: float = np.nan
    rho_mean: float = np.nan
    N: int = 0
    T: int = 0
    
    def summary_table(self) -> str:
        """Generate beautiful summary table."""
        header = """
╔══════════════════════════════════════════════════════════════════════════════╗
║           Testing for Weak Cross-Sectional Dependence (CSD)                  ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  H0: Weak cross-sectional dependence                                         ║
║  H1: Strong cross-sectional dependence                                        ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  N (units):     {N:<15}  T (periods):    {T:<15}            ║
╚══════════════════════════════════════════════════════════════════════════════╝
""".format(N=self.N, T=self.T)
        
        rows = []
        if not np.isnan(self.cd):
            rows.append(["CD (Pesaran)", f"{self.cd:.4f}", f"{self.p_value:.4f}"])
        if not np.isnan(self.cdw):
            rows.append(["CDw (Juodis & Reese)", f"{self.cdw:.4f}", f"{self.cdw_p:.4f}"])
        if not np.isnan(self.cdw_plus):
            rows.append(["CDw+ (Power Enhanced)", f"{self.cdw_plus:.4f}", f"{self.cdw_plus_p:.4f}"])
        if not np.isnan(self.cd_star):
            rows.append(["CD* (Pesaran & Xie)", f"{self.cd_star:.4f}", f"{self.cd_star_p:.4f}"])
        
        headers = ["Test", "Statistic", "P-value"]
        table = tabulate(rows, headers=headers, tablefmt="fancy_grid", numalign="right")
        
        notes = f"""
Mean ρ(i,j) = {self.rho_mean:.4f}

References:
  CD:   Pesaran (2015, 2021)
  CDw:  Juodis & Reese (2021)
  CDw+: CDw with power enhancement (Fan et al., 2015)
  CD*:  Pesaran & Xie (2021)
"""
        
        return header + "\n" + table + notes
    
    def __str__(self) -> str:
        return self.summary_table()


class CDTest:
    """
    Cross-Sectional Dependence Test (xtcd2 equivalent).
    
    Tests for weak cross-sectional dependence in panel data residuals.
    
    Parameters
    ----------
    data : pd.DataFrame or np.ndarray
        Panel data residuals in long format (DataFrame) or N x T matrix.
    unit_col : str, optional
        Unit identifier column (if DataFrame).
    time_col : str, optional
        Time identifier column (if DataFrame).
    var : str, optional
        Variable to test (if DataFrame).
    
    Examples
    --------
    >>> from pydcce import CDTest
    >>> 
    >>> # Test residuals from estimation
    >>> cd = CDTest(
    ...     data=panel_data,
    ...     var='residuals',
    ...     unit_col='country',
    ...     time_col='year'
    ... )
    >>> result = cd.test()
    >>> print(result)
    
    >>> # Or test a variable directly
    >>> cd = CDTest(data=residuals_matrix)  # N x T matrix
    >>> result = cd.test()
    
    References
    ----------
    Pesaran, M.H. (2015). Testing weak cross-sectional dependence in 
    large panels. Econometric Reviews, 34(6-10), 1089-1117.
    
    Pesaran, M.H. (2021). General diagnostic tests for cross-sectional 
    dependence in panels. Empirical Economics, 60, 13-50.
    
    Juodis, A., & Reese, S. (2021). The incidental parameters problem 
    in testing for remaining cross-section correlation.
    """
    
    def __init__(
        self,
        data: Union[pd.DataFrame, np.ndarray],
        unit_col: Optional[str] = None,
        time_col: Optional[str] = None,
        var: Optional[str] = None
    ):
        if isinstance(data, np.ndarray):
            # Data is N x T matrix
            self.residuals = data
            self.N, self.T = data.shape
        else:
            # Data is DataFrame
            if var is None or unit_col is None or time_col is None:
                raise ValueError("var, unit_col, and time_col required for DataFrame")
            
            self._prepare_from_dataframe(data, var, unit_col, time_col)
    
    def _prepare_from_dataframe(
        self,
        data: pd.DataFrame,
        var: str,
        unit_col: str,
        time_col: str
    ) -> None:
        """Convert DataFrame to N x T matrix."""
        pivot = data.pivot(index=unit_col, columns=time_col, values=var)
        self.residuals = pivot.values
        self.N, self.T = self.residuals.shape
        self.units = pivot.index.tolist()
        self.times = pivot.columns.tolist()
    
    def _compute_rho_matrix(self) -> np.ndarray:
        """
        Compute pairwise correlation matrix.
        
        Returns
        -------
        np.ndarray
            N x N correlation matrix (lower triangular).
        """
        # Demean residuals by unit
        e = self.residuals.copy()
        e = e - np.nanmean(e, axis=1, keepdims=True)
        
        # Compute correlations
        rho = np.zeros((self.N, self.N))
        
        for i in range(self.N):
            for j in range(i + 1, self.N):
                ei = e[i, :]
                ej = e[j, :]
                
                # Handle missing values
                valid = ~(np.isnan(ei) | np.isnan(ej))
                if valid.sum() < 2:
                    continue
                
                ei_valid = ei[valid]
                ej_valid = ej[valid]
                T_ij = valid.sum()
                
                # Correlation * sqrt(T)
                num = np.sum(ei_valid * ej_valid)
                denom = np.sqrt(np.sum(ei_valid**2) * np.sum(ej_valid**2))
                
                if denom > 0:
                    rho[i, j] = num / denom * np.sqrt(T_ij)
        
        return rho
    
    def _cd_pesaran(self, rho: np.ndarray) -> Tuple[float, float]:
        """
        Pesaran (2015) CD test.
        
        CD = sqrt(2 / (N*(N-1))) * sum_{i<j} rho_ij * sqrt(T)
        
        Under H0: CD ~ N(0,1)
        """
        # Sum of upper triangular
        rho_sum = np.nansum(np.triu(rho, k=1))
        
        cd = np.sqrt(2 / (self.N * (self.N - 1))) * rho_sum
        p_value = 2 * (1 - stats.norm.cdf(abs(cd)))
        
        return cd, p_value
    
    def _cd_weighted(
        self,
        rho: np.ndarray,
        reps: int = 30
    ) -> Tuple[float, float]:
        """
        Weighted CD test (Juodis & Reese, 2021).
        
        Uses Rademacher weights applied to the data to improve size properties.
        This matches Stata xtcd2.ado implementation.
        
        Notes
        -----
        The weights are applied to the data: data_cdw = data * weights
        Then correlations are computed on the weighted data.
        """
        cdw_list = []
        
        for _ in range(reps):
            # Rademacher weights: +1 or -1 with equal probability
            weights = 2 * np.random.randint(0, 2, size=self.N) - 1
            
            # Apply weights to data (columns), matching Stata: data_cdw = data_start :* weights
            e_weighted = self.residuals * weights[:, np.newaxis].T
            
            # Demean weighted residuals
            e_weighted = e_weighted - np.nanmean(e_weighted, axis=1, keepdims=True)
            
            # Compute correlations on weighted data
            rho_weighted = np.zeros((self.N, self.N))
            for i in range(self.N):
                for j in range(i + 1, self.N):
                    ei = e_weighted[i, :]
                    ej = e_weighted[j, :]
                    
                    valid = ~(np.isnan(ei) | np.isnan(ej))
                    if valid.sum() < 2:
                        continue
                    
                    ei_valid = ei[valid]
                    ej_valid = ej[valid]
                    T_ij = valid.sum()
                    
                    num = np.sum(ei_valid * ej_valid)
                    denom = np.sqrt(np.sum(ei_valid**2) * np.sum(ej_valid**2))
                    
                    if denom > 0:
                        rho_weighted[i, j] = num / denom * np.sqrt(T_ij)
            
            rho_sum = np.nansum(np.triu(rho_weighted, k=1))
            cdw = np.sqrt(2 / (self.N * (self.N - 1))) * rho_sum
            cdw_list.append(cdw)
        
        # Average over replications (matching Stata: rowsum(CD_w) / sqrt(reps))
        cdw = np.sum(cdw_list) / np.sqrt(reps)
        p_value = 2 * (1 - stats.norm.cdf(abs(cdw)))
        
        return cdw, p_value
    
    def _cd_power_enhanced(
        self,
        rho: np.ndarray,
        reps: int = 30
    ) -> Tuple[float, float]:
        """
        Power enhanced CDw test (Fan et al., 2015).
        
        Adds power enhancement for detecting strong correlations.
        """
        cdw, _ = self._cd_weighted(rho, reps)
        
        # Critical value for PEA
        crit = 2 * np.sqrt(np.log(self.N) / self.T)
        
        # Add correlations exceeding threshold
        rho_abs = np.abs(np.triu(rho, k=1))
        enhancement = np.nansum(rho_abs[rho_abs > crit * np.sqrt(self.T)])
        
        cdw_plus = cdw + enhancement / np.sqrt(self.T)
        p_value = 2 * (1 - stats.norm.cdf(abs(cdw_plus)))
        
        return cdw_plus, p_value
    
    def _cd_star(self, n_pca: int = 4) -> Tuple[float, float]:
        """
        CD* test (Pesaran & Xie, 2021).
        
        Defactors residuals before computing CD.
        """
        e = self.residuals.copy()
        e = e - np.nanmean(e, axis=1, keepdims=True)
        
        # Handle missing values with mean imputation
        e = np.nan_to_num(e, nan=0)
        
        # Standardize
        std = np.std(e, axis=1, keepdims=True)
        std[std < 1e-10] = 1
        e_std = e / std
        
        # Extract factors via PCA
        try:
            eigvals, eigvecs = linalg.eigh(e_std @ e_std.T)
            idx = np.argsort(eigvals)[::-1][:n_pca]
            F = eigvecs[:, idx]
            
            # Project out factors
            e_defac = e_std - F @ F.T @ e_std
            
            # Compute CD on defactored residuals
            rho_defac = np.zeros((self.N, self.N))
            for i in range(self.N):
                for j in range(i + 1, self.N):
                    ei = e_defac[i, :]
                    ej = e_defac[j, :]
                    num = np.sum(ei * ej)
                    denom = np.sqrt(np.sum(ei**2) * np.sum(ej**2))
                    if denom > 0:
                        rho_defac[i, j] = num / denom * np.sqrt(self.T)
            
            cd_star, p_value = self._cd_pesaran(rho_defac)
            
        except:
            cd_star, p_value = np.nan, np.nan
        
        return cd_star, p_value
    
    def test(
        self,
        pesaran: bool = True,
        cdw: bool = True,
        pea: bool = True,
        cdstar: bool = True,
        cdw_reps: int = 30,
        n_pca: int = 4
    ) -> CDTestResult:
        """
        Perform CD tests.
        
        Parameters
        ----------
        pesaran : bool
            Compute Pesaran CD test.
        cdw : bool
            Compute weighted CD test.
        pea : bool
            Compute power enhanced CDw.
        cdstar : bool
            Compute CD* test.
        cdw_reps : int
            Replications for CDw.
        n_pca : int
            Number of factors for CD*.
        
        Returns
        -------
        CDTestResult
            Test results.
        """
        # Compute correlation matrix
        rho = self._compute_rho_matrix()
        
        result = CDTestResult(N=self.N, T=self.T)
        
        # Mean correlation
        rho_vals = np.triu(rho, k=1).flatten()
        rho_vals = rho_vals[rho_vals != 0] / np.sqrt(self.T)
        result.rho_mean = np.nanmean(rho_vals) if len(rho_vals) > 0 else 0
        
        # Run tests
        if pesaran:
            result.cd, result.p_value = self._cd_pesaran(rho)
        
        if cdw:
            result.cdw, result.cdw_p = self._cd_weighted(rho, cdw_reps)
        
        if pea:
            result.cdw_plus, result.cdw_plus_p = self._cd_power_enhanced(rho, cdw_reps)
        
        if cdstar:
            result.cd_star, result.cd_star_p = self._cd_star(n_pca)
        
        return result
    
    def get_rho_matrix(self) -> np.ndarray:
        """
        Get pairwise correlation matrix.
        
        Returns
        -------
        np.ndarray
            N x N correlation matrix.
        """
        rho = self._compute_rho_matrix()
        # Make symmetric
        return rho + rho.T
