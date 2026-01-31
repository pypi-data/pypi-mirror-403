# © 2024 EDF
"""
This module contains the core function allowing to calibrate survey weights to match known population totals
or proportions. It implements multiple bounded and unbounded calibration methods.

Core Functionality:
-------------------
The calibration process adjusts initial survey weights to ensure that weighted estimates
from the survey match known population margins (control totals) while minimizing the
distance between initial and final weights according to the chosen method.

Calibration Methods:
--------------------
- Linear: G(w) = (1 - w)^2 / 2 and F(u) = 1 + u
    Simple and fast, but allows negative weights
- Raking (exponential): G(w) = w * log(w) - w + 1 and F(u) = exp(u)
    Ensures positive weights, most widely used
- Logit: G(w) as in [1] and F(u) = L + (U-L)/(1 + exp(-A*u)) with A defined in [1]
    Bounded weights between L and U derived from raking method
- Truncated Linear: G(w) as in [1] and F(u) = min(max(1 + u, L), U)
    Simple bounded approach derived from linear method

Features:
---------
- Multiple calibration methods with different properties
- Support for both categorical and continuous variables
- Flexible margin specification (totals or proportions)
- Detailed convergence monitoring and diagnostics
- Bounded and unbounded weight adjustments
- Comprehensive input validation

References:
-----------
.. [1] Deville, J.-C. and Särndal, C.-E. (1992) "Calibration Estimators in Survey Sampling"
       *Journal of the American Statistical Association*, 87(418), 376-382.
.. [2] Le Guennec, J. and Sautory, O. (2002) "CALMAR 2: Une nouvelle version de la macro Calmar de redressement d'échantillon par calage"
       *Journées de Méthodologie Statistique, INSEE*
.. [3] Rebecq, A. (2017) "Icarus : an R package for calibration in survey sampling"
"""

import time
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

from pycarus.optimization import optimize_calibration
from pycarus.preprocess import (
    maybe_convert_relative_margins_to_totals,
    create_calibration_matrix,
    maybe_initialize_weights,
    validate_inputs,
)
from pycarus.utils import (
    CalibrationResult,
    display_calibration_stats,
    display_margins_comparison,
    plot_weight_ratios_distribution,
)


def calibrate(
    survey_data: pd.DataFrame,
    margins_dict: Dict[str, Union[float, Dict[str, float]]],
    method: str = "raking",
    initial_weights_column: Optional[str] = None,
    population_total: Optional[float] = None,
    margins_as_proportions: bool = False,
    max_iter: int = 1000,
    tolerance: float = 1e-6,
    bounds: Optional[Union[List[float], Tuple[float, float]]] = None,
    verbose: bool = True,
) -> Tuple[np.ndarray, CalibrationResult]:
    """
    Calibrate survey weights to match specified population margins.

    This function adjusts survey weights to ensure weighted estimates match target
    margins while minimizing the distance from initial weights according to the
    chosen calibration method.

    Parameters
    ----------
    survey_data : pd.DataFrame
        Survey data containing variables to be calibrated
    margins_dict : Dict[str, Union[float, Dict[str, float]]]
        Maps variable names to their target margins:
        - For numeric variables: {var_name: target_total}
        - For categorical variables: {var_name: {modality: target_total}}
    method : str, default="raking"
        Calibration method to use, one of:
        - "raking"
        - "linear"
        - "logit" (bounded)
        - "truncated_linear" (bounded)
    initial_weights_column : Optional[str], default=None
        Column name containing initial weights. If None, uses uniform weights
    population_total : Optional[float], default=None
        Total population size, required if margins_as_proportions=True
    margins_as_proportions : bool, default=False
        Whether margins are given as proportions (True) or totals (False)
    max_iter : int, default=1000
        Maximum number of iterations for optimization
    tolerance : float, default=1e-6
        Convergence tolerance for optimization
    bounds : Optional[Union[List[float], Tuple[float, float]]], default=None
        Weight bounds (lower, upper) for bounded methods. None for unbounded methods
    verbose : bool, default=True
        Whether to output stats about the calibration process as well as the
        graph of the density of the ratio calibrated weights / initial weights

    Returns
    -------
    Tuple[np.ndarray, CalibrationResult]
        - Array of calibrated weights
        - Object containing calibration details and diagnostics

    Raises
    ------
    ValueError
        For invalid inputs or incompatible parameters
    TypeError
        For incorrect input types
    CalibrationError
        If optimization fails to converge

    Notes
    -----
    - For categorical variables, all categories in margins must exist in data.
    - Convergence may fail if margins are incompatible or initial weights
      are too far from a feasible solution.
    - Bounded methods require bounds parameter.
    - When using proportions, ensure they sum to 1 within each variable.

    See Also
    --------
    `pycarus.optimization.optimize_calibration` : Core optimization routine
    `pycarus.utils.create_calibration_matrix` : Matrix creation utilities

    Methods
    -------
    - **Linear**: G(w) = (1 - w)^2 / 2 and F(u) = 1 + u
        Simple and fast, but allows negative weights.
    - **Raking (exponential)**: G(w) = w * log(w) - w + 1 and F(u) = exp(u)
        Ensures positive weights, most widely used.
    - **Logit**: G(w) as in [1] and F(u) = L + (U-L)/(1 + exp(-A*u)) with A defined in [1]
        Bounded weights between L and U derived from raking method.
    - **Truncated Linear**: G(w) as in [1] and F(u) = min(max(1 + u, L), U)
        Simple bounded approach derived from linear method.

    Examples
    --------
    >>> import pandas as pd
    >>> from pycarus.calibration import calibrate
    >>>
    >>> # Example survey data
    >>> data = pd.DataFrame({
    >>>     'age': [25, 30, 45, 50],
    >>>     'gender': ['M', 'F', 'M', 'F'],
    >>>     'income': [50000, 60000, 70000, 80000],
    >>>     'initial_weights': [1, 1, 1, 1]
    >>> })
    >>>
    >>> # Target margins
    >>> margins = {
    >>>     'age': 100,  # Total age
    >>>     'gender': {'M': 50, 'F': 50},  # Gender proportions
    >>>     'income': 260000  # Total income
    >>> }
    >>>
    >>> # Calibrate weights
    >>> calibrated_weights, result = calibrate(
    >>>     survey_data=data,
    >>>     margins_dict=margins,
    >>>     initial_weights_column='initial_weights',
    >>>     method='raking',
    >>>     verbose=True
    >>> )
    >>>
    >>> print(calibrated_weights)
    >>> print(result)

    References
    ----------
    .. [1] Deville, J.-C. and Särndal, C.-E. (1992) "Calibration Estimators in Survey Sampling"
        *Journal of the American Statistical Association*, 87(418), 376-382.

    .. [2] Rebecq, A. (2017) "Icarus : an R package for calibration in survey sampling"

    .. [3] Le Guennec, J. and Sautory, O. (2002) "CALMAR 2: Une nouvelle version de la macro Calmar de redressement d'échantillon par calage"
        *Journées de Méthodologie Statistique, INSEE*
    """
    start_time = time.time()

    # Validate all inputs
    validate_inputs(
        survey_data=survey_data,
        margins_dict=margins_dict,
        method=method,
        initial_weights_column=initial_weights_column,
        population_total=population_total,
        margins_as_proportions=margins_as_proportions,
        max_iter=max_iter,
        tolerance=tolerance,
        bounds=bounds,
    )

    # Create calibration matrix and margins vector
    X_matrix, target_margins, var_names = create_calibration_matrix(survey_data, margins_dict)

    # Force conversion of margins to totals
    target_totals = maybe_convert_relative_margins_to_totals(
        target_margins=target_margins,
        population_total=population_total,
        margins_as_proportions=margins_as_proportions,
    )

    # Initialize weights if they aren't explicitly provided
    initial_weights = maybe_initialize_weights(
        survey_data=survey_data,
        initial_weights_column=initial_weights_column,
        population_total=population_total,
    )

    # Perform calibration
    _, weights, relative_gaps, n_iter = optimize_calibration(
        X_matrix=X_matrix,
        initial_weights=initial_weights,
        target_totals=target_totals,
        method=method,
        bounds=bounds,
        max_iter=max_iter,
        tolerance=tolerance,
    )

    # Create result object
    execution_time = time.time() - start_time
    weight_ratios = weights / initial_weights
    named_gaps = dict(zip(var_names, relative_gaps.values()))

    result = CalibrationResult(
        method=method,
        converged=True,
        iterations=n_iter,
        relative_gaps=named_gaps,
        calibrated_weights=weights,
        initial_weights=initial_weights,
        execution_time=execution_time,
    )

    # If needed, display calibration statistics and plot
    if verbose:
        # Calibration statistics
        display_calibration_stats(weight_ratios=weight_ratios, method=method, bounds=bounds)

        # Margins comparison
        display_margins_comparison(
            X_matrix=X_matrix,
            initial_weights=initial_weights,
            calibrated_weights=weights,
            target_totals=target_totals,
            var_names=var_names,
            population_total=population_total,
            margins_as_proportions=margins_as_proportions,
        )

        # Plot weight ratios distribution
        plot_weight_ratios_distribution(weight_ratios)

    return weights, result
