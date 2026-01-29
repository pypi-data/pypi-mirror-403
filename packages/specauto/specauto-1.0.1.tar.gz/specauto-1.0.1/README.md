# specauto

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Godfrey's (1987) Alternative Test Strategy for Discriminating Between Autocorrelation and Misspecification in Regression Analysis**

## Overview

`specauto` is a Python library implementing the sequential hypothesis testing strategy from:

> **Godfrey, L. G. (1987).** "Discriminating Between Autocorrelation and Misspecification in Regression Analysis: An Alternative Test Strategy." *The Review of Economics and Statistics*, Vol. 69, No. 1, pp. 128-134.

The library provides publication-ready diagnostic tools for regression analysis, helping researchers distinguish between:
- **Misspecification** of the regression function
- **Higher-order autocorrelation** (non-AR(1) errors)
- **AR(1) autocorrelation**
- **Independent errors** (no problem)

## Installation

```bash
pip install specauto
```

Or install from source:
```bash
git clone https://github.com/merwanroudane/specauto.git
cd specauto
pip install -e .
```

## Quick Start

```python
import numpy as np
from specauto import AutoSpec

# Generate sample data
np.random.seed(42)
T = 100
X = np.random.randn(T, 2)
y = 1 + 2*X[:, 0] + 3*X[:, 1] + np.random.randn(T)

# Run the complete test strategy
model = AutoSpec(y, X)
results = model.run_full_strategy()

# Print publication-ready results
print(model.summary())
```

## The Four Hypotheses

Godfrey's strategy tests an **ordered sequence of hypotheses**:

| Hypothesis | Description | Test Used |
|------------|-------------|-----------|
| **(a)** | Regression function is **misspecified**; disturbances ARMA | HAC-robust χ² test |
| **(b)** | Correct specification; disturbances general ARMA | — |
| **(c)** | Correct specification; disturbances **AR(1)** | F-test: AR(1) vs AR(1+q) |
| **(d)** | Correct specification; disturbances **independent** | t-test / Durbin-Watson |

The strategy tests along this sequence until rejection. The last non-rejected hypothesis is adopted.

---

## Complete API Reference

### Main Classes

#### `specauto`

The main class implementing Godfrey's (1987) complete test strategy.

```python
from specauto import specauto

specauto = specauto(y, X, significance_level=0.05, add_constant=True)
```

**Parameters:**
- `y` (np.ndarray): Dependent variable (T x 1)
- `X` (np.ndarray): Regressor matrix (T x k), excluding constant
- `significance_level` (float): Significance level for tests (default: 0.05)
- `add_constant` (bool): Whether to add a constant term (default: True)

**Methods:**

| Method | Description |
|--------|-------------|
| `run_full_strategy(reset_powers, truncation_j, ar_p, ar_q)` | Execute complete test sequence |
| `test_misspecification(Z, reset_powers, truncation_j)` | HAC-robust misspecification test (Eq. 10) |
| `test_ar_structure(p, q)` | AR structure F-test (Eq. 18) |
| `test_serial_independence()` | Serial independence test (t-test & DW) |
| `summary()` | Generate formatted results table |
| `to_dict()` | Convert results to dictionary |
| `residuals` | Property: Get OLS residuals |
| `ols_result` | Property: Get OLS estimation results |
| `results` | Property: Get most recent test results |

**Example:**

```python
# Full strategy with custom parameters
results = specauto.run_full_strategy(
    reset_powers=[2, 3],    # Powers for RESET test
    truncation_j=4,         # HAC truncation parameter
    ar_p=1,                 # AR order for null
    ar_q=4                  # Additional AR terms
)

# Individual tests
misspec = specauto.test_misspecification(reset_powers=[2, 3])
ar_test = specauto.test_ar_structure(p=1, q=4)
serial = specauto.test_serial_independence()
```

---

#### `specautoResults`

Complete results from Godfrey's (1987) test strategy.

```python
from specauto import specautoResults
```

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `ols_result` | OLSResult | Results from initial OLS estimation |
| `misspec_result` | MisspecTestResult | Misspecification test results |
| `ar_structure_result` | ARStructureTestResult | AR structure test results |
| `serial_indep_result` | SerialIndepTestResult | Serial independence test results |
| `adopted_hypothesis` | str | Adopted hypothesis: "(a)", "(b)", "(c)", or "(d)" |
| `conclusion` | str | Human-readable conclusion |
| `recommendation` | str | Recommendation for the analyst |

---

### Test Classes

#### `MisspecificationTest` & `MisspecTestResult`

HAC-robust test for misspecification using Equation (10).

```python
from specauto import MisspecificationTest, MisspecTestResult

# Direct usage
test = MisspecificationTest()
result = test.test(residuals, X, Z, truncation_j=4)
```

**MisspecTestResult Attributes:**
- `statistic` (float): χ² test statistic
- `p_value` (float): p-value
- `df` (int): Degrees of freedom
- `critical_value` (float): Critical value at significance level
- `reject_null` (bool): Whether to reject null hypothesis
- `reset_powers` (list): RESET powers used

---

#### `ARStructureTest` & `ARStructureTestResult`

Tests AR(p) vs AR(p+q) using Equation (18).

```python
from specauto import ARStructureTest, ARStructureTestResult

test = ARStructureTest()
result = test.test(residuals, X, p=1, q=4)
```

**ARStructureTestResult Attributes:**
- `f_statistic` (float): F-test statistic
- `p_value` (float): p-value
- `df1` (int): Numerator degrees of freedom
- `df2` (int): Denominator degrees of freedom
- `critical_value` (float): Critical value
- `reject_null` (bool): Whether to reject null hypothesis

---

#### `SerialIndependenceTest` & `SerialIndepTestResult`

Tests for serial independence vs AR(1).

```python
from specauto import SerialIndependenceTest, SerialIndepTestResult

test = SerialIndependenceTest()
result = test.test(residuals, X)
```

**SerialIndepTestResult Attributes:**
- `t_statistic` (float): t-test statistic
- `p_value` (float): p-value
- `dw_statistic` (float): Durbin-Watson statistic
- `rho_estimate` (float): Estimated AR(1) coefficient
- `critical_value` (float): Critical value
- `reject_null` (bool): Whether to reject null hypothesis

---

### Estimation Classes

#### `OLSEstimator` & `OLSResult`

Ordinary Least Squares estimation.

```python
from specauto import OLSEstimator

estimator = OLSEstimator(add_constant=True)
result = estimator.fit(y, X)
```

**OLSResult Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `beta` | np.ndarray | Coefficient estimates |
| `residuals` | np.ndarray | OLS residuals |
| `fitted_values` | np.ndarray | Fitted values |
| `ssr` | float | Sum of squared residuals |
| `tss` | float | Total sum of squares |
| `r_squared` | float | R-squared |
| `adj_r_squared` | float | Adjusted R-squared |
| `sigma_squared` | float | Estimated variance of errors |
| `std_errors` | np.ndarray | Standard errors of coefficients |
| `t_stats` | np.ndarray | t-statistics |
| `n` | int | Number of observations |
| `k` | int | Number of regressors |

**OLSEstimator Methods:**
- `fit(y, X)` → OLSResult
- `result` → Get most recent result
- `get_design_matrix()` → Get X matrix
- `get_XtX_inv()` → Get (X'X)^(-1) matrix

---

#### `HACEstimator`

White-Domowitz (1984) HAC covariance matrix estimator (Equation 9).

```python
from specauto import HACEstimator

hac = HACEstimator(truncation_j=4, auto_bandwidth=False)
result = hac.estimate(X, residuals, truncation_j=4)
```

**Parameters:**
- `truncation_j` (int): Truncation parameter (default: floor(T^(1/3)))
- `auto_bandwidth` (bool): Use automatic bandwidth selection

**HACResult Attributes:**
- `covariance_matrix` (np.ndarray): HAC covariance matrix
- `robust_std_errors` (np.ndarray): Robust standard errors
- `truncation_j` (int): Truncation parameter used
- `meat_matrix` (np.ndarray): X'Σ̂X matrix
- `bread_matrix` (np.ndarray): (X'X)^(-1) matrix

---

### Output Functions

#### `format_specauto_results`

Generate publication-ready formatted output.

```python
from specauto import format_specauto_results

output = format_specauto_results(results, tablefmt="fancy_grid")
print(output)
```

**Parameters:**
- `results` (specautoResults): Complete results from `run_full_strategy()`
- `tablefmt` (str): Table format (default: "fancy_grid")

---

#### `format_test_summary`

Generate a compact summary table.

```python
from specauto import format_test_summary

summary = format_test_summary(results, tablefmt="fancy_grid")
print(summary)
```

---

#### `format_critical_values`

Format critical values table for publication.

```python
from specauto import format_critical_values

table = format_critical_values(critical_values_df, tablefmt="fancy_grid")
print(table)
```

---

#### `format_latex_table`

Generate LaTeX table for academic publications.

```python
from specauto.output.tables import format_latex_table

latex = format_latex_table(
    results, 
    caption="Godfrey (1987) Diagnostic Test Results",
    label="tab:specauto"
)
print(latex)
```

**Parameters:**
- `results` (specautoResults): Complete results
- `caption` (str): Table caption
- `label` (str): Table label for referencing

---

### Simulation Functions

#### `simulate_critical_values`

Master function to simulate critical values via Monte Carlo.

```python
from specauto import simulate_critical_values

cv_tables = simulate_critical_values(
    test_type="all",           # "misspecification", "ar_structure", or "all"
    n_simulations=10000,       # Number of Monte Carlo replications
    sample_sizes=[50, 100, 200, 500],
    significance_levels=[0.01, 0.05, 0.10],
    seed=42
)
```

**Returns:** Dictionary of `CriticalValueTable` objects

---

#### `CriticalValueTable`

Dataclass holding critical values from simulation.

```python
from specauto import CriticalValueTable
```

**Attributes:**
- `test_name` (str): Name of the test
- `sample_sizes` (list): Sample sizes used
- `significance_levels` (list): Significance levels
- `critical_values` (pd.DataFrame): Critical values table
- `n_simulations` (int): Number of simulations

---

#### `print_critical_value_tables`

Print all critical value tables formatted nicely.

```python
from specauto.simulation.critical_values import print_critical_value_tables

print_critical_value_tables(cv_tables)
```

---

### Utility Functions

#### `compute_reset_variables`

Compute RESET test variables (powers of fitted values).

```python
from specauto import compute_reset_variables

Z = compute_reset_variables(fitted_values, powers=[2, 3])
```

---

## Example Output

```
================================================================================
     GODFREY (1987) specauto TEST STRATEGY RESULTS
     Discriminating Between Autocorrelation and Misspecification
================================================================================

MODEL SUMMARY
----------------------------------------
Number of Observations       100
Number of Regressors           3
R-squared                 0.8542
Adjusted R-squared        0.8512
Residual Std. Error       1.0234

SEQUENTIAL TEST RESULTS (at 5% significance level)
--------------------------------------------------------------------------------
| Test                          | Statistic | Value    | p-value  | Decision          |
|-------------------------------|-----------|----------|----------|-------------------|
| Misspecification              | χ²(2)     | 1.2345   | 0.5392   | Do not reject     |
| AR Structure (AR(1) vs AR(5)) | F(4,91)   | 0.8765   | 0.4812   | Do not reject     |
| Serial Independence           | t         | 0.4321   | 0.6665   | Do not reject     |

================================================================================
DIAGNOSIS
================================================================================
Adopted Hypothesis: (d)
Conclusion: NO PROBLEM - Correct specification with independent errors

Recommendation:
  OLS estimator is appropriate. No correction needed.

--------------------------------------------------------------------------------
Signif. codes: *** p<0.01, ** p<0.05, * p<0.10

Reference: Godfrey, L.G. (1987). The Review of Economics and Statistics, 69(1), 128-134.
================================================================================
```

---

## Complete Import Reference

```python
# Main classes
from specauto import specauto, specautoResults

# Test classes
from specauto import (
    MisspecificationTest, MisspecTestResult,
    ARStructureTest, ARStructureTestResult,
    SerialIndependenceTest, SerialIndepTestResult
)

# Estimation classes
from specauto import HACEstimator, OLSEstimator

# Output functions
from specauto import format_specauto_results, format_test_summary, format_critical_values
from specauto.output.tables import format_latex_table

# Simulation
from specauto import simulate_critical_values, CriticalValueTable
from specauto.simulation.critical_values import print_critical_value_tables

# Utilities
from specauto import compute_reset_variables
```

---

## References

- **Godfrey, L. G. (1987).** "Discriminating Between Autocorrelation and Misspecification in Regression Analysis: An Alternative Test Strategy." *The Review of Economics and Statistics*, 69(1), 128-134.

- **White, H., & Domowitz, I. (1984).** "Nonlinear Regression with Dependent Observations." *Econometrica*, 52, 143-161.

- **Thursby, J. G. (1981).** "A Test Strategy for Discriminating between Autocorrelation and Misspecification in Regression Analysis." *The Review of Economics and Statistics*, 63, 117-123.

- **Ramsey, J. B. (1969).** "Tests for Specification Errors in Classical Linear Least Squares Regression Analysis." *JRSS-B*, 31, 350-371.

---

## Author

**Dr Merwan Roudane**  
📧 merwanroudane920@gmail.com  
🔗 https://github.com/merwanroudane/specauto

## License

MIT License - see [LICENSE](LICENSE) for details.
