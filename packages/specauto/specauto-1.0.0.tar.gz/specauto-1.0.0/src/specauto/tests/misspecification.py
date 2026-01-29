"""
Misspecification Test Module

Implements the HAC-robust test for misspecification from Godfrey (1987).
This tests hypothesis (a) vs (b) - whether the regression function is correctly specified.

Reference:
    Godfrey, L. G. (1987). Equations (7)-(10):
    
    Augmented model: y = Xβ + Zα + ε  (Equation 7)
    
    Test statistic (Equation 10):
        χ² = (Rθ̂)'[R(W'W)^(-1)(W'Σ̂_j W)(W'W)^(-1)R']^(-1)(Rθ̂)
    
    Where:
        - W = (X, Z) is the augmented regressor matrix
        - R = (0, I_m) selects the coefficients of test variables Z
        - Σ̂_j is the White-Domowitz HAC estimator
        - Under H₀: χ² ~ χ²(m) asymptotically
"""

import numpy as np
from scipy import stats
from dataclasses import dataclass
from typing import Optional, List, Tuple
from ..estimation.ols import OLSEstimator, OLSResult
from ..estimation.hac import HACEstimator


@dataclass
class MisspecTestResult:
    """Results from misspecification test."""
    statistic: float           # Chi-squared test statistic
    p_value: float             # p-value
    df: int                    # Degrees of freedom (number of test variables m)
    critical_value_1: float    # Critical value at 1%
    critical_value_5: float    # Critical value at 5%
    critical_value_10: float   # Critical value at 10%
    reject_1: bool             # Reject at 1%?
    reject_5: bool             # Reject at 5%?
    reject_10: bool            # Reject at 10%?
    truncation_j: int          # HAC truncation parameter used
    test_variable_type: str    # Type of test variables used
    conclusion: str            # Verbal conclusion


def compute_reset_variables(y_hat: np.ndarray, powers: List[int] = None) -> np.ndarray:
    """
    Compute RESET test variables.
    
    Following Ramsey (1969) and Thursby-Schmidt (1977), the test variables
    are powers of fitted values.
    
    Reference:
        Godfrey (1987), p. 128: "z_t is a vector of test variables, e.g., 
        squares and cubes of the regressors"
    
    Parameters
    ----------
    y_hat : np.ndarray
        Fitted values from OLS regression
    powers : list of int
        Powers to use (default: [2, 3] for squares and cubes)
        
    Returns
    -------
    np.ndarray
        Matrix of test variables (T x m)
    """
    if powers is None:
        powers = [2, 3]
    
    y_hat = np.asarray(y_hat).flatten()
    T = len(y_hat)
    m = len(powers)
    
    Z = np.zeros((T, m))
    for i, p in enumerate(powers):
        Z[:, i] = y_hat ** p
    
    return Z


def compute_regressor_powers(X: np.ndarray, powers: List[int] = None) -> np.ndarray:
    """
    Compute test variables as powers of original regressors.
    
    Reference:
        Godfrey (1987), p. 128: "squares and cubes of the regressors"
    
    Parameters
    ----------
    X : np.ndarray
        Original regressor matrix (excluding constant)
    powers : list of int
        Powers to use (default: [2])
        
    Returns
    -------
    np.ndarray
        Matrix of test variables
    """
    if powers is None:
        powers = [2]
    
    X = np.asarray(X)
    if X.ndim == 1:
        X = X.reshape(-1, 1)
    
    T, k = X.shape
    
    test_vars = []
    for p in powers:
        for j in range(k):
            test_vars.append(X[:, j] ** p)
    
    return np.column_stack(test_vars) if test_vars else np.array([]).reshape(T, 0)


class MisspecificationTest:
    """
    HAC-Robust Misspecification Test.
    
    Tests the null hypothesis that the regression function is correctly specified,
    i.e., H₀: α = 0 in the augmented model y = Xβ + Zα + ε.
    
    This test is robust to autocorrelation of unknown form by using the
    White-Domowitz (1984) HAC covariance estimator.
    
    Reference:
        Godfrey (1987), Section III "Testing for Misspecification"
    """
    
    def __init__(self, significance_level: float = 0.05, 
                 truncation_j: Optional[int] = None):
        """
        Initialize misspecification test.
        
        Parameters
        ----------
        significance_level : float
            Significance level for testing (default: 0.05)
        truncation_j : int, optional
            HAC truncation parameter. If None, uses floor(T^(1/3)).
            Paper recommends j ≥ 4 for quarterly data.
        """
        self.significance_level = significance_level
        self.truncation_j = truncation_j
        self._result: Optional[MisspecTestResult] = None
    
    def test(self, y: np.ndarray, X: np.ndarray, 
             Z: Optional[np.ndarray] = None,
             reset_powers: List[int] = None,
             add_constant: bool = True) -> MisspecTestResult:
        """
        Perform HAC-robust misspecification test.
        
        Implements Equation (10) from Godfrey (1987):
            χ² = (Rθ̂)'[R(W'W)^(-1)(W'Σ̂_j W)(W'W)^(-1)R']^(-1)(Rθ̂)
        
        Parameters
        ----------
        y : np.ndarray
            Dependent variable (T x 1)
        X : np.ndarray
            Original regressors (T x k)
        Z : np.ndarray, optional
            Test variables. If None, RESET-style variables are computed.
        reset_powers : list of int, optional
            Powers for RESET test variables (default: [2, 3])
        add_constant : bool
            Whether to add a constant to X
            
        Returns
        -------
        MisspecTestResult
            Complete test results
        """
        y = np.asarray(y).flatten()
        X = np.asarray(X)
        if X.ndim == 1:
            X = X.reshape(-1, 1)
        
        T = len(y)
        
        # First, get fitted values from original regression
        ols = OLSEstimator(add_constant=add_constant)
        ols_result = ols.fit(y, X)
        
        # Get the design matrix (with constant if added)
        X_full = ols.get_design_matrix()
        k = X_full.shape[1]
        
        # Compute test variables if not provided
        test_var_type = "custom"
        if Z is None:
            if reset_powers is None:
                reset_powers = [2, 3]
            Z = compute_reset_variables(ols_result.fitted_values, powers=reset_powers)
            test_var_type = f"RESET powers {reset_powers}"
        
        Z = np.asarray(Z)
        if Z.ndim == 1:
            Z = Z.reshape(-1, 1)
        
        m = Z.shape[1]  # Number of test variables
        
        # Construct augmented regressor matrix W = (X, Z)
        W = np.hstack([X_full, Z])
        
        # Fit augmented regression: y = Wθ + ε
        # θ = (β', α')'
        WtW = W.T @ W
        WtW_inv = np.linalg.inv(WtW)
        theta_hat = WtW_inv @ W.T @ y
        
        # Get residuals from augmented regression
        residuals = y - W @ theta_hat
        
        # Determine truncation parameter
        if self.truncation_j is not None:
            j = self.truncation_j
        else:
            j = int(np.floor(T ** (1/3)))
        
        # Compute HAC covariance matrix using White-Domowitz estimator
        hac = HACEstimator(truncation_j=j)
        hac_result = hac.estimate(W, residuals)
        V_theta = hac_result.covariance_matrix
        
        # Construct selection matrix R = (0, I_m)
        R = np.hstack([np.zeros((m, k)), np.eye(m)])
        
        # Extract α̂ (coefficients on test variables)
        alpha_hat = theta_hat[k:]  # Last m elements
        
        # Compute test statistic (Equation 10):
        # χ² = (Rθ̂)'[R V(θ̂) R']^(-1)(Rθ̂)
        #    = α̂'[V(α̂)]^(-1)α̂
        RVR = R @ V_theta @ R.T
        RVR_inv = np.linalg.inv(RVR)
        
        chi2_stat = alpha_hat @ RVR_inv @ alpha_hat
        
        # p-value from chi-squared distribution
        p_value = 1 - stats.chi2.cdf(chi2_stat, df=m)
        
        # Critical values
        cv_1 = stats.chi2.ppf(0.99, df=m)
        cv_5 = stats.chi2.ppf(0.95, df=m)
        cv_10 = stats.chi2.ppf(0.90, df=m)
        
        # Make decisions
        reject_1 = chi2_stat > cv_1
        reject_5 = chi2_stat > cv_5
        reject_10 = chi2_stat > cv_10
        
        # Conclusion
        if reject_5:
            conclusion = "Reject H₀: Evidence of misspecification"
        else:
            conclusion = "Do not reject H₀: No evidence of misspecification"
        
        self._result = MisspecTestResult(
            statistic=float(chi2_stat),
            p_value=float(p_value),
            df=m,
            critical_value_1=float(cv_1),
            critical_value_5=float(cv_5),
            critical_value_10=float(cv_10),
            reject_1=reject_1,
            reject_5=reject_5,
            reject_10=reject_10,
            truncation_j=j,
            test_variable_type=test_var_type,
            conclusion=conclusion
        )
        
        return self._result
    
    @property
    def result(self) -> Optional[MisspecTestResult]:
        """Get the most recent test result."""
        return self._result


def misspecification_test(y: np.ndarray, X: np.ndarray, 
                          Z: Optional[np.ndarray] = None,
                          truncation_j: Optional[int] = None,
                          reset_powers: List[int] = None) -> MisspecTestResult:
    """
    Convenience function for HAC-robust misspecification test.
    
    Parameters
    ----------
    y : np.ndarray
        Dependent variable
    X : np.ndarray
        Regressors
    Z : np.ndarray, optional
        Test variables (default: RESET-style)
    truncation_j : int, optional
        HAC truncation parameter
    reset_powers : list of int, optional
        Powers for RESET test variables
        
    Returns
    -------
    MisspecTestResult
        Test results
    """
    test = MisspecificationTest(truncation_j=truncation_j)
    return test.test(y, X, Z=Z, reset_powers=reset_powers)
