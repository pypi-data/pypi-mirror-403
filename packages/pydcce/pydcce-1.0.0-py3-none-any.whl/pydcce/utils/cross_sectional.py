"""
Cross-Sectional Averaging Utilities
====================================

Functions for computing cross-sectional averages (CSA) for CCE estimation.
"""

import numpy as np
import pandas as pd
from typing import List, Optional, Union


def compute_cross_sectional_averages(
    data: pd.DataFrame,
    vars: List[str],
    unit_col: str,
    time_col: str,
    lags: int = 0
) -> pd.DataFrame:
    """
    Compute cross-sectional averages and their lags.
    
    Parameters
    ----------
    data : pd.DataFrame
        Panel data in long format.
    vars : list of str
        Variable names to compute CSA for.
    unit_col : str
        Unit identifier column.
    time_col : str
        Time identifier column.
    lags : int
        Number of lags to include (for Dynamic CCE).
    
    Returns
    -------
    pd.DataFrame
        Original data with CSA columns added.
    
    Notes
    -----
    Cross-sectional averages are computed as:
    
        z_bar(t) = (1/N) * sum_{i=1}^{N} z(i,t)
    
    For Dynamic CCE (Chudik & Pesaran, 2015), lags of CSA are included
    to achieve consistency when lagged dependent variables are present.
    
    Examples
    --------
    >>> import pandas as pd
    >>> from pydcce.utils.cross_sectional import compute_cross_sectional_averages
    >>> 
    >>> data = pd.DataFrame({
    ...     'id': [1, 1, 2, 2],
    ...     'time': [1, 2, 1, 2],
    ...     'y': [10, 12, 20, 22]
    ... })
    >>> 
    >>> result = compute_cross_sectional_averages(
    ...     data, ['y'], 'id', 'time', lags=1
    ... )
    >>> print(result.columns.tolist())
    ['id', 'time', 'y', 'y_bar', 'L1_y_bar']
    """
    result = data.copy()
    
    for var in vars:
        # Compute contemporaneous CSA: z_bar(t) = mean over i
        csa_col = f"{var}_bar"
        result[csa_col] = result.groupby(time_col)[var].transform('mean')
        
        # Add lags of CSA for Dynamic CCE
        for lag in range(1, lags + 1):
            lag_col = f"L{lag}_{csa_col}"
            result[lag_col] = result.groupby(unit_col)[csa_col].shift(lag)
    
    return result


def compute_global_csa(
    data: pd.DataFrame,
    vars: List[str],
    time_col: str
) -> pd.DataFrame:
    """
    Compute global cross-sectional averages (same for all units).
    
    Parameters
    ----------
    data : pd.DataFrame
        Panel data.
    vars : list of str
        Variable names.
    time_col : str
        Time column.
    
    Returns
    -------
    pd.DataFrame
        DataFrame with CSA for each time period.
    """
    return data.groupby(time_col)[vars].mean().reset_index()


def compute_cluster_csa(
    data: pd.DataFrame,
    vars: List[str],
    unit_col: str,
    time_col: str,
    cluster_col: str,
    lags: int = 0
) -> pd.DataFrame:
    """
    Compute cluster-specific cross-sectional averages.
    
    Parameters
    ----------
    data : pd.DataFrame
        Panel data.
    vars : list of str
        Variable names.
    unit_col : str
        Unit column.
    time_col : str
        Time column.
    cluster_col : str
        Cluster identifier column.
    lags : int
        Number of lags.
    
    Returns
    -------
    pd.DataFrame
        Data with cluster-specific CSA columns.
    
    Notes
    -----
    Cluster CSA is useful when cross-sectional dependence varies
    by group (e.g., regions, industries).
    """
    result = data.copy()
    
    for var in vars:
        csa_col = f"{var}_bar_cluster"
        result[csa_col] = result.groupby([cluster_col, time_col])[var].transform('mean')
        
        for lag in range(1, lags + 1):
            lag_col = f"L{lag}_{csa_col}"
            result[lag_col] = result.groupby(unit_col)[csa_col].shift(lag)
    
    return result


def partial_out_csa(
    y: np.ndarray,
    X: np.ndarray,
    Z: np.ndarray
) -> tuple:
    """
    Partial out cross-sectional averages from y and X.
    
    Parameters
    ----------
    y : np.ndarray
        Dependent variable (N*T x 1).
    X : np.ndarray
        Independent variables (N*T x K).
    Z : np.ndarray
        Cross-sectional averages to partial out (N*T x M).
    
    Returns
    -------
    tuple
        (y_tilde, X_tilde) - Partialled out variables.
    
    Notes
    -----
    This implements the partialling out approach:
    
        y_tilde = M_Z * y
        X_tilde = M_Z * X
    
    where M_Z = I - Z(Z'Z)^{-1}Z'
    
    This is used for efficient computation in large panels.
    """
    # Projection matrix: M_Z = I - Z(Z'Z)^-1 Z'
    ZtZ_inv = np.linalg.pinv(Z.T @ Z)
    P_Z = Z @ ZtZ_inv @ Z.T
    M_Z = np.eye(len(y)) - P_Z
    
    y_tilde = M_Z @ y
    X_tilde = M_Z @ X
    
    return y_tilde, X_tilde
