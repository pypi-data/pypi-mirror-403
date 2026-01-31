# © 2025 EDF
"""
Pycarus: Survey Weight Calibration in Python
============================================

Pycarus is a Python package dedicated to survey weight calibration. The package implements
various calibration methods to adjust survey weights to match known population totals, inspired by SAS Calmar.

.. versionadded:: 0.1.0

Key Features
------------
- Survey weight calibration using multiple methods:

  * Raking
  * Linear calibration
  * Logit calibration (bounded)
  * Truncated linear calibration (bounded)
- Support for both categorical and continuous variables
- Flexible handling of calibration margins (totals or percentages)
- Detailed convergence diagnostics and results
- Comprehensive input validation
- Visualization of calibration results

Main Components
---------------
:func:`~pycarus.calibrate`
    Main function to perform survey weight calibration
:class:`~pycarus.CalibrationResult`
    Data class containing detailed results of the calibration process
:exc:`~pycarus.CalibrationError`
    Custom exception for calibration-related errors

Notes
-----
.. note::
    - The package assumes that input data is properly cleaned and formatted
    - For categorical variables, all categories in margins must be present in the data
    - The optimization process may not converge if margins are incompatible
    - Weight bounds can be specified for bounded calibration methods

See Also
--------
`R package icarus <https://cran.r-project.org/web/packages/icarus/index.html>`_
    Original R implementation that inspired this package, providing similar functionality
    for survey calibration in R

References
----------
.. [1] Deville, J.-C. and Särndal, C.-E. (1992) "Calibration Estimators in Survey Sampling"
       *Journal of the American Statistical Association*, 87(418), 376-382.
.. [2] Le Guennec, J. and Sautory, O. (2002) "CALMAR 2: Une nouvelle version de la macro Calmar de redressement d'échantillon par calage"
       *Journées de Méthodologie Statistique, INSEE*
.. [3] Rebecq, A. (2017) "Icarus : an R package for calibration in survey sampling"
"""

from pycarus.calibration import CalibrationResult, calibrate
from pycarus.exceptions import CalibrationError

__all__ = ["calibrate", "CalibrationResult", "CalibrationError"]

__author__ = "Nathan Etourneau"
__email__ = "nathan.etourneau@edf.fr"
__license__ = "BSD-3-Clause"
__version__ = "1.0.0"
