"""
Base Estimator Classes
======================

Base classes for all panel data estimators in pydcce.
"""

import numpy as np
import pandas as pd
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union
from tabulate import tabulate
from scipy import stats


@dataclass
class EstimationResult:
    """
    Container for estimation results.
    
    Attributes
    ----------
    coefficients : dict
        Estimated coefficients.
    std_errors : dict
        Standard errors.
    t_stats : dict
        t-statistics.
    p_values : dict
        p-values.
    conf_int : dict
        Confidence intervals.
    individual_coefs : pd.DataFrame
        Unit-specific coefficients (for MG estimators).
    residuals : np.ndarray
        Residuals.
    fitted_values : np.ndarray
        Fitted values.
    r_squared : float
        R-squared.
    r_squared_adj : float
        Adjusted R-squared.
    N : int
        Number of cross-sectional units.
    T : int
        Number of time periods.
    n_obs : int
        Total observations.
    df_model : int
        Model degrees of freedom.
    df_resid : int
        Residual degrees of freedom.
    ssr : float
        Sum of squared residuals.
    estimator_name : str
        Name of the estimator.
    """
    coefficients: Dict[str, float] = field(default_factory=dict)
    std_errors: Dict[str, float] = field(default_factory=dict)
    t_stats: Dict[str, float] = field(default_factory=dict)
    p_values: Dict[str, float] = field(default_factory=dict)
    conf_int: Dict[str, tuple] = field(default_factory=dict)
    individual_coefs: Optional[pd.DataFrame] = None
    residuals: Optional[np.ndarray] = None
    fitted_values: Optional[np.ndarray] = None
    r_squared: float = 0.0
    r_squared_adj: float = 0.0
    N: int = 0
    T: int = 0
    n_obs: int = 0
    df_model: int = 0
    df_resid: int = 0
    ssr: float = 0.0
    estimator_name: str = ""
    dep_var: str = ""
    aic: float = np.nan
    bic: float = np.nan
    
    def summary_table(
        self,
        title: str = None,
        stars: bool = True,
        conf_level: float = 0.95
    ) -> str:
        """
        Generate beautiful summary table.
        
        Parameters
        ----------
        title : str, optional
            Custom title.
        stars : bool
            Include significance stars.
        conf_level : float
            Confidence level for intervals.
        
        Returns
        -------
        str
            Formatted table string.
        """
        def get_stars(pval):
            if not stars:
                return ""
            if pval < 0.001:
                return "***"
            elif pval < 0.01:
                return "**"
            elif pval < 0.05:
                return "*"
            elif pval < 0.1:
                return "."
            return ""
        
        # Build table data
        rows = []
        for var in self.coefficients:
            coef = self.coefficients[var]
            se = self.std_errors.get(var, np.nan)
            t = self.t_stats.get(var, np.nan)
            p = self.p_values.get(var, np.nan)
            ci = self.conf_int.get(var, (np.nan, np.nan))
            star = get_stars(p)
            
            rows.append([
                var,
                f"{coef:.6f}{star}",
                f"{se:.6f}",
                f"{t:.4f}",
                f"{p:.4f}",
                f"[{ci[0]:.4f}, {ci[1]:.4f}]"
            ])
        
        headers = ["Variable", "Coefficient", "Std. Error", "t-stat", "P>|t|", f"{int(conf_level*100)}% Conf. Int."]
        
        table = tabulate(rows, headers=headers, tablefmt="fancy_grid", numalign="right")
        
        # Build header
        title_str = title or f"{self.estimator_name} Estimation Results"
        header = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  {title_str:^74}  ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Dependent Variable: {self.dep_var:<55}  ║
║  Estimator:          {self.estimator_name:<55}  ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  N (units):     {self.N:<15}  T (periods):    {self.T:<15}            ║
║  Observations:  {self.n_obs:<15}  DF Residual:    {self.df_resid:<15}            ║
║  R-squared:     {self.r_squared:<15.6f}  Adj. R-squared: {self.r_squared_adj:<15.6f}            ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
        
        # Significance legend
        legend = """
Note: *** p<0.001, ** p<0.01, * p<0.05, . p<0.1
""" if stars else ""
        
        return header + "\n" + table + legend
    
    def __str__(self) -> str:
        return self.summary_table()
    
    def __repr__(self) -> str:
        return f"EstimationResult(estimator={self.estimator_name}, N={self.N}, T={self.T})"
    
    def compute_ic(self) -> None:
        """
        Compute information criteria (AIC, BIC).
        
        Notes
        -----
        AIC = n * log(SSR/n) + 2*k
        BIC = n * log(SSR/n) + k * log(n)
        
        where n is the number of observations and k is the number of parameters.
        """
        if self.n_obs > 0 and self.ssr > 0:
            n = self.n_obs
            k = self.df_model + 1  # +1 for constant if present
            log_ssr_n = np.log(self.ssr / n)
            self.aic = n * log_ssr_n + 2 * k
            self.bic = n * log_ssr_n + k * np.log(n)
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert results to DataFrame."""
        data = {
            "Coefficient": self.coefficients,
            "Std. Error": self.std_errors,
            "t-stat": self.t_stats,
            "P>|t|": self.p_values,
        }
        df = pd.DataFrame(data)
        
        # Add confidence intervals
        if self.conf_int:
            df["CI Lower"] = [self.conf_int[v][0] for v in self.coefficients]
            df["CI Upper"] = [self.conf_int[v][1] for v in self.coefficients]
        
        return df


class BaseEstimator(ABC):
    """
    Abstract base class for panel data estimators.
    
    All estimators (MG, CCE, DCCE, etc.) inherit from this class.
    
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
    """
    
    def __init__(
        self,
        data: pd.DataFrame,
        depvar: str,
        indepvars: List[str],
        unit_col: str,
        time_col: str
    ):
        self.data = data.copy()
        self.depvar = depvar
        self.indepvars = indepvars
        self.unit_col = unit_col
        self.time_col = time_col
        
        # Validate inputs
        self._validate_data()
        
        # Sort and setup
        self.data = self.data.sort_values([unit_col, time_col]).reset_index(drop=True)
        self._setup_panel()
        
        # Results storage
        self.result = None
    
    def _validate_data(self) -> None:
        """Validate input data."""
        required_cols = [self.depvar] + self.indepvars + [self.unit_col, self.time_col]
        missing = [c for c in required_cols if c not in self.data.columns]
        if missing:
            raise ValueError(f"Missing columns: {missing}")
    
    def _setup_panel(self) -> None:
        """Setup panel dimensions."""
        self.units = self.data[self.unit_col].unique()
        self.times = self.data[self.time_col].unique()
        self.N = len(self.units)
        self.T = len(self.times)
        self.n_obs = len(self.data)
        
        # Check balance
        obs_per_unit = self.data.groupby(self.unit_col).size()
        self.is_balanced = (obs_per_unit == self.T).all()
    
    @abstractmethod
    def fit(self) -> EstimationResult:
        """
        Fit the model.
        
        Returns
        -------
        EstimationResult
            Estimation results.
        """
        pass
    
    def _compute_mean_group_coef(
        self,
        individual_coefs: pd.DataFrame
    ) -> Dict[str, float]:
        """
        Compute mean group coefficients.
        
        Parameters
        ----------
        individual_coefs : pd.DataFrame
            DataFrame with unit-specific coefficients.
        
        Returns
        -------
        dict
            Mean group coefficients.
        """
        return individual_coefs.mean().to_dict()
    
    def _compute_mean_group_variance(
        self,
        individual_coefs: pd.DataFrame,
        mg_coefs: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Compute mean group variance.
        
        var(b_mg) = (1/N) * sum_i (b_i - b_mg)^2
        
        Parameters
        ----------
        individual_coefs : pd.DataFrame
            Unit-specific coefficients.
        mg_coefs : dict
            Mean group coefficients.
        
        Returns
        -------
        dict
            Variance for each coefficient.
        """
        N = len(individual_coefs)
        variances = {}
        
        for var in mg_coefs:
            deviations = (individual_coefs[var] - mg_coefs[var]) ** 2
            variances[var] = deviations.sum() / (N * (N - 1))
        
        return variances
    
    def _compute_std_errors(self, variances: Dict[str, float]) -> Dict[str, float]:
        """Compute standard errors from variances."""
        return {k: np.sqrt(v) for k, v in variances.items()}
    
    def _compute_t_stats(
        self,
        coefs: Dict[str, float],
        std_errors: Dict[str, float]
    ) -> Dict[str, float]:
        """Compute t-statistics."""
        return {k: coefs[k] / std_errors[k] if std_errors[k] > 0 else np.nan
                for k in coefs}
    
    def _compute_p_values(
        self,
        t_stats: Dict[str, float],
        df: int
    ) -> Dict[str, float]:
        """Compute p-values from t-statistics."""
        return {k: 2 * (1 - stats.t.cdf(abs(v), df)) if not np.isnan(v) else np.nan
                for k, v in t_stats.items()}
    
    def _compute_conf_int(
        self,
        coefs: Dict[str, float],
        std_errors: Dict[str, float],
        df: int,
        alpha: float = 0.05
    ) -> Dict[str, tuple]:
        """Compute confidence intervals."""
        t_crit = stats.t.ppf(1 - alpha/2, df)
        return {
            k: (coefs[k] - t_crit * std_errors[k],
                coefs[k] + t_crit * std_errors[k])
            for k in coefs
        }
    
    def _compute_r_squared(
        self,
        y: np.ndarray,
        y_hat: np.ndarray
    ) -> float:
        """Compute R-squared."""
        ss_res = np.sum((y - y_hat) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        return 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
    
    def _compute_adj_r_squared(
        self,
        r_squared: float,
        n: int,
        k: int
    ) -> float:
        """Compute adjusted R-squared."""
        return 1 - (1 - r_squared) * (n - 1) / (n - k - 1) if n > k + 1 else 0.0
    
    def predict(self, data: pd.DataFrame = None) -> np.ndarray:
        """
        Generate predictions.
        
        Parameters
        ----------
        data : pd.DataFrame, optional
            Data to predict on. Uses training data if None.
        
        Returns
        -------
        np.ndarray
            Predicted values.
        """
        if self.result is None:
            raise ValueError("Model must be fitted before prediction")
        
        if data is None:
            return self.result.fitted_values
        
        # Generate predictions using coefficients
        X = data[self.indepvars].values
        y_pred = X @ np.array(list(self.result.coefficients.values()))
        
        return y_pred
    
    def summary(self) -> str:
        """Return summary table."""
        if self.result is None:
            return "Model not yet fitted. Call .fit() first."
        return str(self.result)
