# © 2025 EDF
"""
Preprocessing Functions for Survey Weight Calibration
=====================================================

This module provides preprocessing utilities for survey weight calibration,
including input validation, weight initialization, and matrix creation functions.
These functions handle data preparation and validation before the actual
calibration process.
"""

from typing import Any, Dict, List, Optional, Tuple, Union

import warnings

import numpy as np
import pandas as pd

from pycarus.methods import BOUNDED_METHODS, VALID_METHODS


_EPS_DENOM = 1e-10


def maybe_initialize_weights(
    survey_data: pd.DataFrame,
    initial_weights_column: Optional[str] = None,
    population_total: Optional[float] = None,
) -> np.ndarray:
    """
    Initialize survey weights.

    - If initial_weights_column is None: create uniform weights scaled to population_total.
    - Otherwise: read weights from the given column and validate them.
    """
    if initial_weights_column is None:
        if population_total is None:
            raise ValueError("population_total must be provided when initial_weights_column is None")

        n_samples = len(survey_data)
        uniform_weight = population_total / n_samples
        return np.full(n_samples, uniform_weight)

    if initial_weights_column not in survey_data.columns:
        raise ValueError(f"Weight column '{initial_weights_column}' not found in survey_data")

    initial_weights = survey_data[initial_weights_column].to_numpy()

    if not np.issubdtype(initial_weights.dtype, np.number):
        raise ValueError("Weights must be numeric")

    if np.any(initial_weights <= 0):
        raise ValueError("Initial weights must be strictly positive")

    if np.any(~np.isfinite(initial_weights)):
        raise ValueError("Initial weights must be finite")

    return initial_weights


def validate_variable_in_data(var_name: str, survey_data: pd.DataFrame) -> None:
    """Check if a variable exists in the survey data."""
    if var_name not in survey_data.columns:
        raise ValueError(f"Variable '{var_name}' not found in survey data.")


def validate_numeric_margin(margin: Union[int, float], var_name: str) -> None:
    """Validate a numeric margin."""
    if not isinstance(margin, (int, float)):
        raise ValueError(f"Invalid margin value for variable '{var_name}': {margin}. Margin must be a number.")


def validate_categorical_margin(
    var_name: str,
    margins: Dict[Any, float],
    survey_data: pd.DataFrame,
    margins_as_proportions: bool = False,
) -> None:
    """Validate a categorical margin."""
    categories_in_data = set(survey_data[var_name].unique())
    margin_categories = set(margins.keys())

    if categories_in_data != margin_categories:
        missing_cats = categories_in_data - margin_categories
        extra_cats = margin_categories - categories_in_data
        raise ValueError(
            f"Mismatch in categories for variable '{var_name}'. Missing: {missing_cats}, Extra: {extra_cats}."
        )

    if any(not isinstance(v, (int, float)) or v < 0 for v in margins.values()):
        raise ValueError(f"Invalid margin values for categorical variable '{var_name}'.")

    if margins_as_proportions:
        total = sum(margins.values())
        if not np.isclose(total, 1.0, rtol=1e-5):
            raise ValueError(f"Proportions for '{var_name}' sum to {total}, but should sum to 1.")


def validate_categorical_margin_sums(
    margins_dict: Dict[str, Union[float, Dict[str, float]]],
) -> None:
    """Validate the consistency of margins across categorical variables."""
    categorical_margins = {var_name: margins for var_name, margins in margins_dict.items() if isinstance(margins, dict)}
    if not categorical_margins:
        return

    categorical_sums = {var_name: sum(margins.values()) for var_name, margins in categorical_margins.items()}

    margin_sums = list(categorical_sums.values())
    min_margin_sum = min(margin_sums)
    max_margin_sum = max(margin_sums)

    if np.isclose(min_margin_sum, max_margin_sum, rtol=1e-5, atol=1e-8):
        return

    min_var = next(var_name for var_name, s in categorical_sums.items() if np.isclose(s, min_margin_sum))
    max_var = next(var_name for var_name, s in categorical_sums.items() if np.isclose(s, max_margin_sum))

    raise ValueError(
        "Categorical margin sums are inconsistent across variables.\n"
        f"Variable '{min_var}' has margin sum: {categorical_sums[min_var]}\n"
        f"Variable '{max_var}' has margin sum: {categorical_sums[max_var]}\n"
        "Ensure all categorical variables have consistent margin summation."
    )


def validate_margins(
    survey_data: pd.DataFrame,
    margins_dict: Dict[str, Union[float, Dict[str, float]]],
    margins_as_proportions: bool = False,
) -> None:
    """Validate the margins dictionary against the survey data."""
    if not isinstance(margins_dict, dict):
        raise TypeError("margins_dict must be a dictionary.")

    for var_name, margins in margins_dict.items():
        validate_variable_in_data(var_name, survey_data)

        if isinstance(margins, dict):
            validate_categorical_margin(var_name, margins, survey_data, margins_as_proportions)
        else:
            validate_numeric_margin(margins, var_name)

    validate_categorical_margin_sums(margins_dict)


def validate_bounds(bounds: Union[List[float], Tuple[float, float]], method: str) -> None:
    """Validate weight bounds."""
    if method not in BOUNDED_METHODS and bounds:
        warnings.warn(
            f"Bounds are ignored with method '{method}'. Use 'logit' or 'truncated_linear' for bounded calibration."
        )
        return

    if method not in BOUNDED_METHODS and bounds is None:
        return

    if method in BOUNDED_METHODS and bounds is None:
        raise ValueError(f"The '{method}' method requires bounds. Please provide (lower, upper) bounds.")

    if not isinstance(bounds, (tuple, list)):
        raise ValueError("`bounds` must be a list or tuple of two floats (lower, upper).")

    if len(bounds) != 2:
        raise ValueError("`bounds` must be a list or tuple of two floats (lower, upper).")

    lower, upper = bounds
    if not (isinstance(lower, (int, float)) and isinstance(upper, (int, float))):
        raise ValueError("Bounds must be numeric values")

    if lower >= 1 or upper <= 1:
        raise ValueError(f"Lower bound must be < 1, upper bound must be > 1. Got (lower, upper)=({lower}, {upper})")


def _check_inputs_types(survey_data: pd.DataFrame, margins_dict: Dict[str, Union[float, Dict[str, float]]]) -> None:
    if not isinstance(survey_data, pd.DataFrame):
        raise TypeError("survey_data must be a pandas DataFrame")
    if not isinstance(margins_dict, dict):
        raise TypeError("margins_dict must be a dictionary")


def _check_method(method: str) -> None:
    if not isinstance(method, str):
        raise TypeError("method must be a string")
    if method not in VALID_METHODS:
        raise ValueError(f"Unknown method '{method}'. Valid methods are: {VALID_METHODS}")


def _check_population_total(
    margins_as_proportions: bool,
    population_total: Optional[Union[int, float]],
) -> None:
    if not isinstance(margins_as_proportions, bool):
        raise TypeError("margins_as_proportions must be a boolean")

    if margins_as_proportions and population_total is None:
        raise ValueError("population_total is required when margins_as_proportions=True")

    if population_total is None:
        return

    if not isinstance(population_total, (int, float)):
        raise TypeError("population_total must be numeric")
    if population_total <= 0:
        raise ValueError("population_total must be positive")


def _check_weights_spec(
    survey_data: pd.DataFrame,
    population_total: Optional[Union[int, float]],
    initial_weights_column: Optional[str],
) -> None:
    if population_total is None and initial_weights_column is None:
        raise ValueError("Either population_total or initial_weights_column must be specified")

    if initial_weights_column is not None and initial_weights_column not in survey_data.columns:
        raise ValueError(f"Column {initial_weights_column} not found in survey_data")


def _check_optimizer_settings(max_iter: int, tolerance: float, verbose: bool) -> None:
    if not isinstance(max_iter, int) or max_iter <= 0:
        raise ValueError("max_iter must be a positive integer")

    if not isinstance(tolerance, float) or tolerance <= 0:
        raise ValueError("tolerance must be a positive float")

    if not isinstance(verbose, bool):
        raise TypeError("verbose must be a boolean")


def validate_inputs(
    survey_data: pd.DataFrame,
    margins_dict: Dict[str, Union[float, Dict[str, float]]],
    method: str,
    bounds: Optional[Union[List[float], Tuple[float, float]]],
    margins_as_proportions: bool,
    population_total: Optional[int],
    max_iter: int,
    tolerance: float,
    initial_weights_column: Optional[str] = None,
    verbose: bool = True,
) -> None:
    """Validate all input parameters for the calibration function."""
    _check_inputs_types(survey_data, margins_dict)

    validate_margins(survey_data, margins_dict, margins_as_proportions)

    _check_method(method)
    validate_bounds(bounds, method)

    _check_population_total(margins_as_proportions, population_total)
    _check_weights_spec(survey_data, population_total, initial_weights_column)
    _check_optimizer_settings(max_iter, tolerance, verbose)


def create_calibration_matrix(
    survey_data: pd.DataFrame,
    margins_dict: Dict[str, Union[float, Dict[Any, float]]],
) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """Create design matrix and target margins for calibration."""
    columns = list(margins_dict.keys())
    if survey_data.loc[:, columns].isna().any().any():
        raise ValueError("Survey data contains missing values.")

    matrix_pieces: List[np.ndarray] = []
    margins_pieces: List[float] = []
    variable_names: List[str] = []

    for var_name, margin in margins_dict.items():
        validate_variable_in_data(var_name, survey_data)

        if isinstance(margin, dict):  # Categorical variable
            for category, target in margin.items():
                validate_numeric_margin(target, f"{var_name}[{category}]")
                indicator = (survey_data[var_name] == category).astype(float)
                matrix_pieces.append(indicator.values.reshape(-1, 1))
                margins_pieces.append(float(target))
                variable_names.append(f"{var_name}[{category}]")
        else:  # Numeric variable
            validate_numeric_margin(margin, var_name)
            values = survey_data[var_name].to_numpy()
            if not np.issubdtype(values.dtype, np.number):
                raise ValueError(f"Variable '{var_name}' must be numeric.")
            matrix_pieces.append(values.reshape(-1, 1))
            margins_pieces.append(float(margin))
            variable_names.append(var_name)

    X_matrix = np.hstack(matrix_pieces)
    margins_array = np.array(margins_pieces)

    return X_matrix, margins_array, variable_names


def maybe_convert_relative_margins_to_totals(
    target_margins: np.ndarray,
    population_total: Optional[float] = None,
    margins_as_proportions: bool = False,
) -> np.ndarray:
    """Convert proportion margins into absolute totals if requested."""
    if not isinstance(target_margins, np.ndarray):
        raise ValueError("target_margins must be a numpy array")

    if not np.issubdtype(target_margins.dtype, np.number):
        raise ValueError("target_margins must contain numeric values")

    if np.any(~np.isfinite(target_margins)):
        raise ValueError("target_margins contains invalid values")

    if margins_as_proportions:
        if population_total is None:
            raise ValueError("population_total must be provided when margins are proportions")
        if population_total <= 0:
            raise ValueError("population_total must be positive")
        return target_margins * population_total

    return target_margins.copy()
