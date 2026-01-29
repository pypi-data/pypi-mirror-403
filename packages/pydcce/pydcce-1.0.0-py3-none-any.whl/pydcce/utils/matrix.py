"""
Matrix Operation Utilities
==========================

Matrix inversion and solving routines with robust handling.
"""

import numpy as np
from scipy import linalg
from typing import Optional, Tuple


def invert_matrix(
    A: np.ndarray,
    method: str = "auto"
) -> np.ndarray:
    """
    Robust matrix inversion with multiple methods.
    
    Parameters
    ----------
    A : np.ndarray
        Matrix to invert.
    method : str
        Inversion method: 'auto', 'cholesky', 'qr', 'pinv'.
    
    Returns
    -------
    np.ndarray
        Inverted matrix.
    
    Notes
    -----
    The 'auto' method tries in order:
    1. Cholesky decomposition (fastest, for positive definite)
    2. QR decomposition (stable)
    3. Moore-Penrose pseudo-inverse (handles singular matrices)
    """
    if method == "cholesky" or method == "auto":
        try:
            L = linalg.cholesky(A, lower=True)
            L_inv = linalg.solve_triangular(L, np.eye(len(A)), lower=True)
            return L_inv.T @ L_inv
        except linalg.LinAlgError:
            if method == "cholesky":
                raise
            # Fall through to QR
    
    if method == "qr" or method == "auto":
        try:
            Q, R = linalg.qr(A)
            R_inv = linalg.solve_triangular(R, np.eye(len(A)))
            return R_inv @ Q.T
        except linalg.LinAlgError:
            if method == "qr":
                raise
            # Fall through to pinv
    
    # Use pseudo-inverse as last resort
    return np.linalg.pinv(A)


def solve_system(
    A: np.ndarray,
    b: np.ndarray,
    method: str = "auto"
) -> np.ndarray:
    """
    Solve linear system Ax = b.
    
    Parameters
    ----------
    A : np.ndarray
        Coefficient matrix.
    b : np.ndarray
        Right-hand side vector/matrix.
    method : str
        Solution method: 'auto', 'cholesky', 'qr', 'lstsq'.
    
    Returns
    -------
    np.ndarray
        Solution vector x.
    """
    if method == "cholesky" or method == "auto":
        try:
            return linalg.cho_solve(linalg.cho_factor(A), b)
        except linalg.LinAlgError:
            if method == "cholesky":
                raise
    
    if method == "qr" or method == "auto":
        try:
            return linalg.solve(A, b)
        except linalg.LinAlgError:
            if method == "qr":
                raise
    
    # Least squares solution
    x, _, _, _ = np.linalg.lstsq(A, b, rcond=None)
    return x


def check_rank(
    X: np.ndarray,
    tol: float = 1e-10
) -> Tuple[int, bool]:
    """
    Check rank of matrix and return full rank status.
    
    Parameters
    ----------
    X : np.ndarray
        Matrix to check.
    tol : float
        Tolerance for singular values.
    
    Returns
    -------
    tuple
        (rank, is_full_rank)
    """
    rank = np.linalg.matrix_rank(X, tol=tol)
    is_full_rank = (rank == min(X.shape))
    return rank, is_full_rank


def make_symmetric(A: np.ndarray) -> np.ndarray:
    """Make matrix symmetric by averaging with transpose."""
    return (A + A.T) / 2


def block_diagonal(matrices: list) -> np.ndarray:
    """
    Create block diagonal matrix from list of matrices.
    
    Parameters
    ----------
    matrices : list
        List of numpy arrays.
    
    Returns
    -------
    np.ndarray
        Block diagonal matrix.
    """
    return linalg.block_diag(*matrices)


def delta_method_variance(
    gradient: np.ndarray,
    cov_matrix: np.ndarray
) -> np.ndarray:
    """
    Compute variance using delta method.
    
    Parameters
    ----------
    gradient : np.ndarray
        Gradient vector (K x 1).
    cov_matrix : np.ndarray
        Covariance matrix (K x K).
    
    Returns
    -------
    np.ndarray
        Variance of transformed parameter.
    
    Notes
    -----
    The delta method computes:
        Var(g(theta)) ≈ g'(theta)' * Var(theta) * g'(theta)
    
    This is used for computing standard errors of long-run
    coefficients in ECM and CS-ARDL models.
    """
    return gradient.T @ cov_matrix @ gradient
