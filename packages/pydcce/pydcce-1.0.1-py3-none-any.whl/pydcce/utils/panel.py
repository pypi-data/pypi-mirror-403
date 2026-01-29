"""
Panel Data Utilities
====================

Handles panel data in long format with cross-sectional unit and time identifiers.
"""

import numpy as np
import pandas as pd
from typing import List, Optional, Tuple, Union


class PanelData:
    """
    Panel data container for long-format panel datasets.
    
    Parameters
    ----------
    data : pd.DataFrame
        Panel data in long format with unit and time identifiers.
    unit_col : str
        Name of the cross-sectional unit identifier column.
    time_col : str
        Name of the time identifier column.
    
    Attributes
    ----------
    data : pd.DataFrame
        The panel data.
    unit_col : str
        Unit identifier column name.
    time_col : str
        Time identifier column name.
    N : int
        Number of cross-sectional units.
    T : int
        Number of time periods.
    is_balanced : bool
        Whether the panel is balanced.
    
    Examples
    --------
    >>> import pandas as pd
    >>> from pydcce import PanelData
    >>> 
    >>> # Create sample data
    >>> data = pd.DataFrame({
    ...     'country': ['A', 'A', 'B', 'B'],
    ...     'year': [2000, 2001, 2000, 2001],
    ...     'gdp': [100, 110, 200, 220],
    ...     'investment': [20, 22, 40, 44]
    ... })
    >>> 
    >>> panel = PanelData(data, unit_col='country', time_col='year')
    >>> print(f"N={panel.N}, T={panel.T}, Balanced={panel.is_balanced}")
    N=2, T=2, Balanced=True
    """
    
    def __init__(
        self,
        data: pd.DataFrame,
        unit_col: str,
        time_col: str
    ):
        self.data = data.copy()
        self.unit_col = unit_col
        self.time_col = time_col
        
        # Validate inputs
        self._validate()
        
        # Sort data
        self.data = self.data.sort_values([unit_col, time_col]).reset_index(drop=True)
        
        # Compute panel dimensions
        self._compute_dimensions()
    
    def _validate(self) -> None:
        """Validate panel data structure."""
        if not isinstance(self.data, pd.DataFrame):
            raise TypeError("data must be a pandas DataFrame")
        
        if self.unit_col not in self.data.columns:
            raise ValueError(f"Unit column '{self.unit_col}' not found in data")
        
        if self.time_col not in self.data.columns:
            raise ValueError(f"Time column '{self.time_col}' not found in data")
        
        # Check for duplicates
        duplicates = self.data.duplicated(subset=[self.unit_col, self.time_col])
        if duplicates.any():
            raise ValueError("Data contains duplicate (unit, time) observations")
    
    def _compute_dimensions(self) -> None:
        """Compute panel dimensions and balance status."""
        self.units = self.data[self.unit_col].unique()
        self.times = self.data[self.time_col].unique()
        self.N = len(self.units)
        self.T = len(self.times)
        
        # Check balance
        obs_per_unit = self.data.groupby(self.unit_col).size()
        self.is_balanced = (obs_per_unit == self.T).all()
        
        # Store T for each unit
        self.T_i = obs_per_unit.to_dict()
    
    def get_unit_data(self, unit: Union[str, int]) -> pd.DataFrame:
        """
        Get data for a specific cross-sectional unit.
        
        Parameters
        ----------
        unit : str or int
            Unit identifier.
        
        Returns
        -------
        pd.DataFrame
            Data for the specified unit.
        """
        return self.data[self.data[self.unit_col] == unit].copy()
    
    def get_variable(self, var: str) -> np.ndarray:
        """
        Get variable as N x T matrix.
        
        Parameters
        ----------
        var : str
            Variable name.
        
        Returns
        -------
        np.ndarray
            Variable data as N x T matrix.
        """
        if var not in self.data.columns:
            raise ValueError(f"Variable '{var}' not found in data")
        
        # Pivot to wide format
        wide = self.data.pivot(
            index=self.unit_col,
            columns=self.time_col,
            values=var
        )
        return wide.values
    
    def add_lag(self, var: str, lags: int = 1, prefix: str = "L") -> None:
        """
        Add lagged variable to the panel.
        
        Parameters
        ----------
        var : str
            Variable name to lag.
        lags : int
            Number of lags.
        prefix : str
            Prefix for lagged variable name.
        """
        for lag in range(1, lags + 1):
            new_col = f"{prefix}{lag}_{var}"
            self.data[new_col] = self.data.groupby(self.unit_col)[var].shift(lag)
    
    def add_difference(self, var: str, order: int = 1, prefix: str = "D") -> None:
        """
        Add differenced variable to the panel.
        
        Parameters
        ----------
        var : str
            Variable name to difference.
        order : int
            Order of differencing.
        prefix : str
            Prefix for differenced variable name.
        """
        new_col = f"{prefix}{order}_{var}" if order > 1 else f"{prefix}_{var}"
        self.data[new_col] = self.data.groupby(self.unit_col)[var].diff(order)
    
    def compute_cross_sectional_mean(self, var: str) -> pd.Series:
        """
        Compute cross-sectional mean at each time period.
        
        Parameters
        ----------
        var : str
            Variable name.
        
        Returns
        -------
        pd.Series
            Cross-sectional mean for each time period.
        """
        return self.data.groupby(self.time_col)[var].mean()
    
    def add_cross_sectional_mean(
        self,
        vars: List[str],
        lags: int = 0,
        suffix: str = "_bar"
    ) -> None:
        """
        Add cross-sectional averages to the data.
        
        Parameters
        ----------
        vars : list of str
            Variable names to compute CSA for.
        lags : int
            Number of lags of CSA to include.
        suffix : str
            Suffix for CSA variable names.
        """
        for var in vars:
            # Compute contemporaneous CSA
            csa = self.data.groupby(self.time_col)[var].transform('mean')
            self.data[f"{var}{suffix}"] = csa
            
            # Add lags of CSA
            for lag in range(1, lags + 1):
                self.data[f"L{lag}_{var}{suffix}"] = (
                    self.data.groupby(self.unit_col)[f"{var}{suffix}"].shift(lag)
                )
    
    def balance(self, method: str = "drop") -> "PanelData":
        """
        Balance the panel.
        
        Parameters
        ----------
        method : str
            Method to balance: 'drop' (remove units with missing), 
            'fill' (forward fill missing values).
        
        Returns
        -------
        PanelData
            Balanced panel data.
        """
        if self.is_balanced:
            return self
        
        if method == "drop":
            # Keep only units with complete observations
            complete_units = [
                u for u, t in self.T_i.items() if t == self.T
            ]
            balanced_data = self.data[
                self.data[self.unit_col].isin(complete_units)
            ]
        elif method == "fill":
            # Create balanced index and fill
            idx = pd.MultiIndex.from_product(
                [self.units, self.times],
                names=[self.unit_col, self.time_col]
            )
            balanced_data = (
                self.data.set_index([self.unit_col, self.time_col])
                .reindex(idx)
                .groupby(level=0)
                .ffill()
                .reset_index()
            )
        else:
            raise ValueError(f"Unknown balance method: {method}")
        
        return PanelData(balanced_data, self.unit_col, self.time_col)
    
    def summary(self) -> str:
        """
        Return summary of panel structure.
        
        Returns
        -------
        str
            Panel summary.
        """
        balance_status = "balanced" if self.is_balanced else "unbalanced"
        
        summary = f"""
╔══════════════════════════════════════════════════════════════╗
║                    Panel Data Summary                         ║
╠══════════════════════════════════════════════════════════════╣
║  Panel Variable (i): {self.unit_col:<40}║
║  Time Variable (t):  {self.time_col:<40}║
╠══════════════════════════════════════════════════════════════╣
║  Number of units (N):      {self.N:<34}║
║  Time periods (T):         {self.T:<34}║
║  Total observations:       {len(self.data):<34}║
║  Panel type:               {balance_status:<34}║
╚══════════════════════════════════════════════════════════════╝
"""
        return summary
    
    def __repr__(self) -> str:
        balance = "balanced" if self.is_balanced else "unbalanced"
        return f"PanelData(N={self.N}, T={self.T}, obs={len(self.data)}, {balance})"
