"""
SpecAuto: Godfrey's (1987) Alternative Test Strategy for Discriminating
Between Autocorrelation and Misspecification in Regression Analysis

Author: Dr Merwan Roudane
Email: merwanroudane920@gmail.com
GitHub: https://github.com/merwanroudane/specauto

Reference:
    Godfrey, L. G. (1987). "Discriminating Between Autocorrelation and 
    Misspecification in Regression Analysis: An Alternative Test Strategy."
    The Review of Economics and Statistics, Vol. 69, No. 1, pp. 128-134.
"""

from .core import AutoSpec, AutoSpecResults
from .tests.misspecification import (
    MisspecificationTest,
    MisspecTestResult,
    compute_reset_variables
)
from .tests.ar_structure import (
    ARStructureTest,
    ARStructureTestResult
)
from .tests.serial_independence import (
    SerialIndependenceTest,
    SerialIndepTestResult
)
from .estimation.hac import HACEstimator
from .estimation.ols import OLSEstimator
from .output.tables import (
    format_autospec_results,
    format_test_summary,
    format_critical_values
)
from .simulation.critical_values import (
    simulate_critical_values,
    CriticalValueTable
)

__version__ = "1.0.0"
__author__ = "Dr Merwan Roudane"
__email__ = "merwanroudane920@gmail.com"

__all__ = [
    # Main classes
    "AutoSpec",
    "AutoSpecResults",
    # Test classes
    "MisspecificationTest",
    "MisspecTestResult",
    "ARStructureTest", 
    "ARStructureTestResult",
    "SerialIndependenceTest",
    "SerialIndepTestResult",
    # Estimation
    "HACEstimator",
    "OLSEstimator",
    # Output
    "format_autospec_results",
    "format_test_summary",
    "format_critical_values",
    # Simulation
    "simulate_critical_values",
    "CriticalValueTable",
    # Utilities
    "compute_reset_variables"
]
