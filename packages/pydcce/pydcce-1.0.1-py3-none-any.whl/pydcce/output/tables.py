"""
Output Tables
=============

Beautiful table formatting using tabulate.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Union
from tabulate import tabulate


class ResultsTable:
    """
    Beautiful results table formatting.
    
    Provides Stata-like output tables using tabulate.
    
    Examples
    --------
    >>> from pydcce.output import ResultsTable
    >>> 
    >>> table = ResultsTable(
    ...     title="Dynamic CCE Estimation Results",
    ...     dep_var="log_gdp"
    ... )
    >>> table.add_coefficient("log_capital", 0.352, 0.045)
    >>> table.add_coefficient("log_labor", 0.648, 0.032)
    >>> print(table)
    """
    
    def __init__(
        self,
        title: str = "Estimation Results",
        dep_var: str = "",
        estimator: str = "",
        n_obs: int = 0,
        n_groups: int = 0,
        time_periods: int = 0,
        r_squared: float = 0.0
    ):
        self.title = title
        self.dep_var = dep_var
        self.estimator = estimator
        self.n_obs = n_obs
        self.n_groups = n_groups
        self.time_periods = time_periods
        self.r_squared = r_squared
        
        self.rows = []
        self.notes = []
    
    def add_coefficient(
        self,
        name: str,
        coef: float,
        se: float,
        t_stat: Optional[float] = None,
        p_value: Optional[float] = None,
        ci_low: Optional[float] = None,
        ci_high: Optional[float] = None
    ) -> None:
        """
        Add coefficient row.
        
        Parameters
        ----------
        name : str
            Variable name.
        coef : float
            Coefficient value.
        se : float
            Standard error.
        t_stat : float, optional
            t-statistic.
        p_value : float, optional
            p-value.
        ci_low : float, optional
            Lower CI bound.
        ci_high : float, optional
            Upper CI bound.
        """
        if t_stat is None:
            t_stat = coef / se if se > 0 else np.nan
        
        if p_value is None:
            from scipy import stats
            p_value = 2 * (1 - stats.t.cdf(abs(t_stat), self.n_obs - 1))
        
        if ci_low is None:
            ci_low = coef - 1.96 * se
        if ci_high is None:
            ci_high = coef + 1.96 * se
        
        # Significance stars
        stars = self._get_stars(p_value)
        
        self.rows.append({
            'name': name,
            'coef': coef,
            'se': se,
            't_stat': t_stat,
            'p_value': p_value,
            'ci_low': ci_low,
            'ci_high': ci_high,
            'stars': stars
        })
    
    def _get_stars(self, p_value: float) -> str:
        """Get significance stars."""
        if np.isnan(p_value):
            return ""
        if p_value < 0.001:
            return "***"
        elif p_value < 0.01:
            return "**"
        elif p_value < 0.05:
            return "*"
        elif p_value < 0.1:
            return "."
        return ""
    
    def add_note(self, note: str) -> None:
        """Add footnote."""
        self.notes.append(note)
    
    def to_string(
        self,
        format: str = "fancy_grid",
        show_stars: bool = True,
        show_ci: bool = True
    ) -> str:
        """
        Generate table string.
        
        Parameters
        ----------
        format : str
            Tabulate format ('fancy_grid', 'simple', 'github', etc.)
        show_stars : bool
            Show significance stars.
        show_ci : bool
            Show confidence intervals.
        
        Returns
        -------
        str
            Formatted table.
        """
        # Header
        header = self._build_header()
        
        # Build table data
        table_data = []
        for row in self.rows:
            coef_str = f"{row['coef']:.6f}"
            if show_stars:
                coef_str += row['stars']
            
            row_data = [
                row['name'],
                coef_str,
                f"{row['se']:.6f}",
                f"{row['t_stat']:.4f}",
                f"{row['p_value']:.4f}"
            ]
            
            if show_ci:
                row_data.append(f"[{row['ci_low']:.4f}, {row['ci_high']:.4f}]")
            
            table_data.append(row_data)
        
        # Headers
        headers = ["Variable", "Coefficient", "Std. Error", "t-stat", "P>|t|"]
        if show_ci:
            headers.append("95% Conf. Int.")
        
        table = tabulate(table_data, headers=headers, tablefmt=format, numalign="right")
        
        # Footer
        footer = self._build_footer(show_stars)
        
        return header + "\n" + table + "\n" + footer
    
    def _build_header(self) -> str:
        """Build header section."""
        width = 78
        border = "═" * width
        
        lines = [
            f"╔{border}╗",
            f"║  {self.title:^{width-2}}║",
            f"╠{border}╣"
        ]
        
        if self.dep_var:
            lines.append(f"║  Dependent Variable: {self.dep_var:<{width-23}}║")
        if self.estimator:
            lines.append(f"║  Estimator:          {self.estimator:<{width-23}}║")
        
        lines.append(f"╠{border}╣")
        
        info = f"N: {self.n_groups}    T: {self.time_periods}    Obs: {self.n_obs}    R²: {self.r_squared:.4f}"
        lines.append(f"║  {info:<{width-2}}║")
        lines.append(f"╚{border}╝")
        
        return "\n".join(lines)
    
    def _build_footer(self, show_stars: bool) -> str:
        """Build footer section."""
        lines = []
        
        if show_stars:
            lines.append("Significance: *** p<0.001, ** p<0.01, * p<0.05, . p<0.1")
        
        for note in self.notes:
            lines.append(f"Note: {note}")
        
        return "\n".join(lines)
    
    def __str__(self) -> str:
        return self.to_string()
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert to DataFrame."""
        return pd.DataFrame(self.rows)
    
    def to_latex(self) -> str:
        """Generate LaTeX table."""
        return self.to_string(format="latex")
    
    def to_html(self) -> str:
        """Generate HTML table."""
        return self.to_string(format="html")


def print_summary_stats(
    data: pd.DataFrame,
    vars: List[str],
    title: str = "Summary Statistics"
) -> str:
    """
    Print summary statistics table.
    
    Parameters
    ----------
    data : pd.DataFrame
        Data to summarize.
    vars : list of str
        Variables to include.
    title : str
        Table title.
    
    Returns
    -------
    str
        Formatted table.
    """
    stats = data[vars].describe().T
    stats = stats[['count', 'mean', 'std', 'min', '25%', '50%', '75%', 'max']]
    stats.columns = ['N', 'Mean', 'Std.Dev', 'Min', 'P25', 'Median', 'P75', 'Max']
    
    header = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  {title:^74}  ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
    
    table = tabulate(
        stats.values,
        headers=stats.columns.tolist(),
        showindex=stats.index.tolist(),
        tablefmt="fancy_grid",
        floatfmt=".4f"
    )
    
    return header + table


def print_test_comparison(
    tests: Dict[str, tuple],
    title: str = "Model Comparison"
) -> str:
    """
    Print test statistics comparison table.
    
    Parameters
    ----------
    tests : dict
        Dictionary of test names to (statistic, p_value) tuples.
    title : str
        Table title.
    
    Returns
    -------
    str
        Formatted table.
    """
    rows = []
    for name, (stat, pval) in tests.items():
        sig = "***" if pval < 0.001 else ("**" if pval < 0.01 else ("*" if pval < 0.05 else ""))
        rows.append([name, f"{stat:.4f}", f"{pval:.4f}", sig])
    
    table = tabulate(
        rows,
        headers=["Test", "Statistic", "P-value", ""],
        tablefmt="fancy_grid",
        numalign="right"
    )
    
    return f"\n{title}\n" + "=" * len(title) + "\n" + table
