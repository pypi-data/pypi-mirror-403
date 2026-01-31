# © 2025 EDF
"""
This module implements core optimization algorithms for survey weight calibration,
providing distance functions and calibration gap calculations used in the iterative
calibration process using Newton's method.

The module supports different calibration methods through appropriate distance functions:
- Linear
- Raking
- Logit
- Truncated Linear

These methods determine how initial weights are adjusted during calibration while
maintaining calibration constraints.

Main Components:
----------------
get_distance_function:
    Returns the appropriate distance function for each calibration method
get_distance_derivative:
    Returns the derivative of the distance function for Newton's method
compute_calibration_gaps:
    Calculates differences between current estimates and target margins
compute_jacobian:
    Computes the Jacobian used in Newton's method
optimize_calibration:
    Performs the main optimization process using Newton's method

Technical Details:
------------------
The optimization process uses Newton's method to iteratively solve the calibration
equations. At each iteration, it computes the Jacobian matrix and updates the
Lagrange multipliers using the Newton step.

The Newton algorithm:
1. Initialize lambda = 0
2. Compute weights: w = d * F(X @ lambda)
3. Compute margin gaps: g = X^T @ w - total
4. Compute Jacobian: J = X^T @ diag(d * F'(X @ lambda)) @ X
5. Solve: J @ step = g
6. Update: lambda = lambda - step
7. Repeat until convergence

This approach provides quadratic convergence when close to the solution.
"""

from typing import Callable, Dict, List, Optional, Tuple, Union

import numpy as np
from scipy.linalg import LinAlgError, solve

from pycarus.exceptions import CalibrationError


_EPS_DENOM = 1e-10


def get_distance_function(
    method: str, bounds: Optional[Union[List[float], Tuple[float, float]]] = None
) -> Callable[[np.ndarray], np.ndarray]:
    """
    Returns the distance function for the specified calibration method.

    Parameters
    ----------
    method : str
        The calibration method to use. Must be one of:
            - Linear: F(u) = 1 + u
            - Raking: F(u) = exp(u)
            - Logit: F(u) = (L*(U-1) + U*(1-L)*exp(A*u)) / ((U-1) + (1-L)*exp(A*u))
            - Truncated Linear: F(u) = clip(1 + u, L, U)
    bounds : Optional[Union[List[float], Tuple[float, float]]], default=None
        Weight bounds (L, U) to constrain weights. Required for 'logit'
        and 'truncated_linear' methods.

    Returns
    -------
    Callable[[np.ndarray], np.ndarray]
        A function that takes a numpy array and returns transformed values
    """
    if method == "linear":
        return lambda x: 1 + x

    if method == "raking":
        return lambda x: np.exp(x)

    if method == "logit":
        if bounds is None:
            raise ValueError("Bounds required for logit method")
        lower, upper = bounds
        A = (upper - lower) / ((1 - lower) * (upper - 1))

        def logit_fn(x: np.ndarray) -> np.ndarray:
            exp_term = np.exp(A * x)
            numerator = lower * (upper - 1) + upper * (1 - lower) * exp_term
            denominator = (upper - 1) + (1 - lower) * exp_term
            return numerator / denominator

        return logit_fn

    if method == "truncated_linear":
        if bounds is None:
            raise ValueError("Bounds required for truncated linear method")
        lower, upper = bounds
        return lambda x: np.clip(1 + x, lower, upper)

    raise ValueError(f"Unknown calibration method: {method}")


def get_distance_derivative(
    method: str, bounds: Optional[Union[List[float], Tuple[float, float]]] = None
) -> Callable[[np.ndarray], np.ndarray]:
    """
    Returns the derivative of the distance function for the specified calibration method.

    Parameters
    ----------
    method : str
        The calibration method
    bounds : Optional[Union[List[float], Tuple[float, float]]], default=None
        Weight bounds for bounded methods

    Returns
    -------
    Callable[[np.ndarray], np.ndarray]
        A function that returns the derivative of the distance function
    """
    if method == "linear":
        return lambda x: np.ones_like(x)

    if method == "raking":
        return lambda x: np.exp(x)

    if method == "logit":
        if bounds is None:
            raise ValueError("Bounds required for logit method")
        lower, upper = bounds
        A = (upper - lower) / ((1 - lower) * (upper - 1))

        def logit_derivative(x: np.ndarray) -> np.ndarray:
            exp_term = np.exp(A * x)
            denominator = (upper - 1) + (1 - lower) * exp_term
            numerator = ((upper - lower) ** 2) * exp_term
            return numerator / (denominator**2)

        return logit_derivative

    if method == "truncated_linear":
        if bounds is None:
            raise ValueError("Bounds required for truncated linear method")
        lower, upper = bounds

        def truncated_derivative(x: np.ndarray) -> np.ndarray:
            linear_vals = 1 + x
            # Derivative is 1 where not clipped, 0 where clipped
            return np.where((linear_vals >= lower) & (linear_vals <= upper), 1.0, 0.0)

        return truncated_derivative

    raise ValueError(f"Unknown calibration method: {method}")


def compute_calibration_gaps(
    lagrange_multipliers: np.ndarray,
    X_matrix: np.ndarray,
    initial_weights: np.ndarray,
    target_totals: np.ndarray,
    method: str,
    bounds: Optional[Union[List[float], Tuple[float, float]]] = None,
) -> np.ndarray:
    """
    Calculates differences between current weighted estimates and target margins.

    Returns
    -------
    np.ndarray
        Array of differences between estimated and target margins (margin_gaps)
    """
    F = get_distance_function(method, bounds)
    u = X_matrix @ lagrange_multipliers
    weights_calibrated = initial_weights * F(u)
    estimated_totals = X_matrix.T @ weights_calibrated
    margin_gaps = estimated_totals - target_totals
    return margin_gaps


def compute_jacobian(
    lagrange_multipliers: np.ndarray,
    X_matrix: np.ndarray,
    initial_weights: np.ndarray,
    method: str,
    bounds: Optional[Union[List[float], Tuple[float, float]]] = None,
) -> np.ndarray:
    """
    Computes the Jacobian matrix for Newton's method.

    Returns
    -------
    np.ndarray
        Jacobian matrix
    """
    F_prime = get_distance_derivative(method, bounds)
    u = X_matrix @ lagrange_multipliers
    jacobian_weights = initial_weights * F_prime(u)

    # Jacobian: X^T @ diag(jacobian_weights) @ X
    # Efficient computation: (X * jacobian_weights[:, None]).T @ X
    jacobian = (X_matrix * jacobian_weights[:, None]).T @ X_matrix
    return jacobian


def _validate_opt_inputs(X_matrix: np.ndarray, initial_weights: np.ndarray, target_totals: np.ndarray) -> None:
    if not isinstance(X_matrix, np.ndarray) or not isinstance(initial_weights, np.ndarray):
        raise ValueError("X_matrix and initial_weights must be numpy arrays")

    if X_matrix.shape[0] != initial_weights.shape[0]:
        raise ValueError("Number of rows in X_matrix must match length of initial_weights")

    if X_matrix.shape[1] != target_totals.shape[0]:
        raise ValueError("Number of columns in X_matrix must match length of target_totals")


def _relative_margin_gaps(margin_gaps: np.ndarray, target_totals: np.ndarray) -> np.ndarray:
    return np.abs(margin_gaps) / (np.abs(target_totals) + _EPS_DENOM)


def _compute_margin_gaps(
    lagrange_multipliers: np.ndarray,
    X_matrix: np.ndarray,
    initial_weights: np.ndarray,
    target_totals: np.ndarray,
    F: Callable[[np.ndarray], np.ndarray],
) -> Tuple[np.ndarray, np.ndarray]:
    u = X_matrix @ lagrange_multipliers
    weights = initial_weights * F(u)

    if np.any(~np.isfinite(weights)):
        raise CalibrationError("Invalid weights encountered during optimization")

    estimated_totals = X_matrix.T @ weights
    margin_gaps = estimated_totals - target_totals
    return margin_gaps, weights


def _solve_newton_step(jacobian: np.ndarray, margin_gaps: np.ndarray, svd_tol: float) -> np.ndarray:
    """
    Solve Jacobian @ step = margin_gaps.

    First tries a direct solve; if it fails, falls back to an SVD-based pseudoinverse.
    """
    # 1) Fast path: direct solve
    try:
        return solve(jacobian, margin_gaps, assume_a="pos")
    except LinAlgError:
        pass

    # 2) Robust fallback: pseudoinverse via SVD
    try:
        U, S, Vt = np.linalg.svd(jacobian, full_matrices=False)
    except np.linalg.LinAlgError as e:
        raise CalibrationError("Failed to factorize Jacobian (SVD) in Newton step") from e

    S_inv = np.where(S > svd_tol, 1.0 / S, 0.0)
    jacobian_pinv = (Vt.T * S_inv) @ U.T  # avoids np.diag(S_inv)
    return jacobian_pinv @ margin_gaps


def optimize_calibration(
    X_matrix: np.ndarray,
    initial_weights: np.ndarray,
    target_totals: np.ndarray,
    method: str,
    bounds: Optional[Union[List[float], Tuple[float, float]]],
    max_iter: int,
    tolerance: float,
) -> Tuple[np.ndarray, np.ndarray, Dict[str, float], int]:
    """
    Computes optimal weights using Newton's method for calibration.

    Returns
    -------
    Tuple[np.ndarray, np.ndarray, Dict[str, float], int]
        - Final Lagrange multipliers
        - Optimized weights
        - Dictionary of relative margin gaps between estimated and target margins
        - Number of iterations
    """
    _validate_opt_inputs(X_matrix, initial_weights, target_totals)

    lagrange_multipliers = np.zeros(X_matrix.shape[1])
    svd_tol = np.finfo(float).eps
    F = get_distance_function(method, bounds)

    for iteration in range(1, max_iter + 1):
        try:
            margin_gaps, _ = _compute_margin_gaps(lagrange_multipliers, X_matrix, initial_weights, target_totals, F)

            if np.max(_relative_margin_gaps(margin_gaps, target_totals)) < tolerance:
                break

            jacobian = compute_jacobian(lagrange_multipliers, X_matrix, initial_weights, method, bounds)
            newton_step = _solve_newton_step(jacobian, margin_gaps, svd_tol)
            lagrange_multipliers = lagrange_multipliers - newton_step

        except CalibrationError:
            raise
        except Exception as e:
            raise CalibrationError(f"Optimization failed at iteration {iteration}: {e}") from e
    else:
        raise CalibrationError(f"No convergence in {max_iter} iterations")

    # Final weights + diagnostics
    u_final = X_matrix @ lagrange_multipliers
    final_weights = initial_weights * F(u_final)
    final_estimated_totals = X_matrix.T @ final_weights

    final_relative_gaps = {
        f"Variable {i}": abs(est - target) / (abs(target) + _EPS_DENOM)
        for i, (est, target) in enumerate(zip(final_estimated_totals, target_totals))
    }

    return lagrange_multipliers, final_weights, final_relative_gaps, iteration
