# © 2025 EDF

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


@dataclass
class CalibrationResult:
    """
    Contains the results and diagnostics of a calibration operation.

    Attributes
    ----------
    method : str
        The calibration method used
    converged : bool
        Whether the calibration algorithm converged
    iterations : int
        Number of iterations performed
    relative_gaps : dict
        Dictionary of relative differences between estimated and target margins
    calibrated_weights : np.ndarray
        Final calibrated weights
    initial_weights : np.ndarray
        Initial weights, before calibration.
        If not provided by user, they are initialized as N/n
        where N is pop_total and n is sample size.
    execution_time : float
        Time taken for calibration in seconds
    """

    method: str
    converged: bool
    iterations: int
    relative_gaps: Dict[str, float]
    calibrated_weights: np.ndarray
    initial_weights: np.ndarray
    execution_time: float


def display_calibration_stats(
    weight_ratios: np.ndarray, method: str, bounds: Optional[Tuple[float, float]] = None
) -> None:
    """
    Display summary statistics of weight ratios after calibration.

    This function prints a summary of the weight ratios (calibrated weights / initial weights)
    after the calibration process. It includes the mean and various percentiles of the weight ratios.

    Parameters
    ----------
    weight_ratios : np.ndarray
        Array of weight ratios (calibrated weights / initial weights)
    method : str
        Calibration method used
    bounds : Optional[Tuple[float, float]]
        Weight bounds used (if any)
    """
    print(
        "\n################### Summary of before/after weight ratios ###################"
    )
    if not bounds:
        print(f"Calibration method: {method}")
    else:
        print(f"Calibration method: {method} with bounds ({bounds[0]}, {bounds[1]})")

    print(f"Mean: {np.mean(weight_ratios):.4f}")

    percentiles = np.percentile(weight_ratios, [0, 1, 10, 25, 50, 75, 90, 99, 100])
    percentiles_labels = ["0%", "1%", "10%", "25%", "50%", "75%", "90%", "99%", "100%"]

    # Format the output to ensure alignment
    percentiles_row = " ".join([f"{p:>6}" for p in percentiles_labels])
    percentiles_values = " ".join([f"{v:6.4f}" for v in percentiles])
    print(percentiles_row)
    print(percentiles_values)


def display_margins_comparison(
    X_matrix: np.ndarray,
    initial_weights: np.ndarray,
    calibrated_weights: np.ndarray,
    target_totals: np.ndarray,
    var_names: List[str],
    population_total: Optional[float],
    margins_as_proportions: bool,
) -> None:
    """
    Display comparison of margins before and after calibration.

    This function prints a comparison of the margins before and after the calibration process.
    It shows the initial margins, the calibrated margins, and the target margins for each variable.

    Parameters
    ----------
    X_matrix : np.ndarray
        Calibration matrix
    initial_weights : np.ndarray
        Initial weights
    calibrated_weights : np.ndarray
        Calibrated weights
    target_totals : np.ndarray
        Target totals for calibration
    var_names : List[str]
        Names of variables used in calibration
    population_total : Optional[float]
        Total population size
    margins_as_proportions : bool
        Whether margins are given as proportions
    """
    print(
        "\n################ Comparison Margins Before/After calibration ################"
    )
    before_margins = (
        (X_matrix.T @ initial_weights) / population_total
        if margins_as_proportions
        else (X_matrix.T @ initial_weights)
    )
    after_margins = (
        (X_matrix.T @ calibrated_weights) / population_total
        if margins_as_proportions
        else (X_matrix.T @ calibrated_weights)
    )

    df_calibration_stats = pd.DataFrame(
        {
            "column": var_names,
            "before": before_margins,
            "after": after_margins,
            "total": target_totals / population_total
            if margins_as_proportions
            else target_totals,
        }
    )

    # Format the output to ensure alignment
    print(
        df_calibration_stats.rename(
            columns={
                "column": "Variable",
                "before": "Before Calibration",
                "after": "After Calibration",
                "total": "Target Margin",
            }
        ).to_string(index=False, float_format="{:.4f}".format, justify="left")
    )


def plot_weight_ratios_distribution(weight_ratios: np.ndarray) -> None:
    """
    Plot the distribution of weight ratios.

    This function plots the distribution of the weight ratios (calibrated weights / initial weights)
    using a kernel density estimate (KDE) plot. It also includes a vertical line at ratio = 1 for reference.

    Parameters
    ----------
    weight_ratios : np.ndarray
        Array of weight ratios (calibrated weights / initial weights)
    """
    plt.figure(figsize=(10, 6))
    sns.kdeplot(
        weight_ratios, fill=True, color="red", alpha=0.3, linewidth=2, label="Density"
    )
    plt.axvline(1, color="black", linestyle="--", linewidth=1, label="Ratio = 1")
    plt.title(
        "Distribution of Weight Ratios (After Calibration / Initial)", fontsize=14
    )
    plt.xlabel("Weight Ratios", fontsize=12)
    plt.ylabel("Density", fontsize=12)
    plt.legend()
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    plt.tight_layout()
    plt.show()
