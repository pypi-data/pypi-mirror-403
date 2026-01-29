"""
Serial Independence Test Module

Tests hypothesis (c) vs (d) - whether errors are AR(1) vs independent.
This is the final step in Godfrey's (1987) test strategy.

Reference:
    Godfrey, L. G. (1987), p. 133:
    
    "The problem of testing the null hypothesis of serial independence 
    against the alternative of a stationary AR(1) process has been examined
    at length in the literature and several tests are available."
    
    Two approaches:
    1. t-test: Test ρ = 0 in e_t = ρe_{t-1} + a_t
    2. Durbin-Watson test: DW = Σ(e_t - e_{t-1})² / Σe_t²
    
    "Whichever test of ρ = 0 is used, an insignificant value indicates
    that, in Thursby's terminology, there is 'no problem' with the
    initial specification and that the OLS estimator b is appropriate."
"""

import numpy as np
from scipy import stats
from dataclasses import dataclass
from typing import Optional, Tuple
from ..estimation.ols import OLSEstimator


@dataclass
class SerialIndepTestResult:
    """Results from serial independence test."""
    # t-test results
    t_statistic: float
    t_pvalue: float
    rho_estimate: float
    rho_std_error: float
    # DW test results
    dw_statistic: float
    dw_pvalue_approx: float
    # Critical values and decisions
    t_critical_1: float
    t_critical_5: float
    t_critical_10: float
    reject_t_1: bool
    reject_t_5: bool
    reject_t_10: bool
    # Conclusion
    conclusion: str


class SerialIndependenceTest:
    """
    Test for Serial Independence vs AR(1) Errors.
    
    This test determines whether the regression errors are serially
    independent (d) or follow an AR(1) process (c).
    
    If we reject H₀: ρ = 0, the regression should be re-estimated
    allowing for AR(1) errors (e.g., Cochrane-Orcutt or Hildreth-Liu).
    
    If we do not reject H₀, there is "no problem" with the original
    specification and OLS is appropriate.
    
    Reference:
        Godfrey (1987), Section "Testing the Hypothesis of Serial Independence"
    """
    
    def __init__(self, significance_level: float = 0.05, 
                 two_sided: bool = True):
        """
        Initialize serial independence test.
        
        Parameters
        ----------
        significance_level : float
            Significance level for testing
        two_sided : bool
            Whether to use two-sided test (default: True)
        """
        self.significance_level = significance_level
        self.two_sided = two_sided
        self._result: Optional[SerialIndepTestResult] = None
    
    def _compute_dw_statistic(self, residuals: np.ndarray) -> float:
        """
        Compute Durbin-Watson statistic.
        
        DW = Σ(e_t - e_{t-1})² / Σe_t²
        
        Parameters
        ----------
        residuals : np.ndarray
            OLS residuals
            
        Returns
        -------
        float
            Durbin-Watson statistic
        """
        diff = np.diff(residuals)
        numerator = np.sum(diff ** 2)
        denominator = np.sum(residuals ** 2)
        
        return numerator / denominator if denominator > 0 else np.nan
    
    def _dw_pvalue_approx(self, dw: float, n: int, k: int) -> float:
        """
        Approximate p-value for Durbin-Watson statistic.
        
        Uses the asymptotic approximation that (1 - DW/2) ~ N(0, 1/n)
        as described in Godfrey (1987), p. 129.
        
        Parameters
        ----------
        dw : float
            Durbin-Watson statistic
        n : int
            Sample size
        k : int
            Number of regressors
            
        Returns
        -------
        float
            Approximate two-sided p-value
        """
        # Asymptotic approximation: (1 - DW/2) ~ N(0, 1/n)
        z = (1 - dw / 2) * np.sqrt(n)
        p_value = 2 * (1 - stats.norm.cdf(abs(z)))
        return p_value
    
    def test(self, residuals: np.ndarray, n_regressors: int = 1) -> SerialIndepTestResult:
        """
        Perform serial independence test.
        
        Tests H₀: ρ = 0 (independence) vs H₁: ρ ≠ 0 (AR(1))
        
        Implements both:
        1. t-test on ρ in: e_t = ρe_{t-1} + a_t
        2. Durbin-Watson test
        
        Parameters
        ----------
        residuals : np.ndarray
            OLS residuals from original regression
        n_regressors : int
            Number of regressors in original model (for DW critical values)
            
        Returns
        -------
        SerialIndepTestResult
            Complete test results
        """
        e = np.asarray(residuals).flatten()
        T = len(e)
        
        if T < 3:
            raise ValueError(f"Need at least 3 observations, got {T}")
        
        # ===== t-test for ρ = 0 =====
        # Regress e_t on e_{t-1}
        e_t = e[1:]      # e_2, e_3, ..., e_T
        e_lag = e[:-1]   # e_1, e_2, ..., e_{T-1}
        
        # OLS: e_t = ρ e_{t-1} + a_t (no constant)
        ols = OLSEstimator(add_constant=False)
        result = ols.fit(e_t, e_lag)
        
        rho_hat = result.beta[0]
        se_rho = result.std_errors[0]
        t_stat = result.t_stats[0]
        
        # p-value for t-test
        df = T - 2  # degrees of freedom
        if self.two_sided:
            t_pvalue = 2 * (1 - stats.t.cdf(abs(t_stat), df))
        else:
            t_pvalue = 1 - stats.t.cdf(t_stat, df)
        
        # Critical values for t-test
        if self.two_sided:
            t_cv_1 = stats.t.ppf(0.995, df)
            t_cv_5 = stats.t.ppf(0.975, df)
            t_cv_10 = stats.t.ppf(0.95, df)
        else:
            t_cv_1 = stats.t.ppf(0.99, df)
            t_cv_5 = stats.t.ppf(0.95, df)
            t_cv_10 = stats.t.ppf(0.90, df)
        
        # Decisions based on t-test
        reject_t_1 = abs(t_stat) > t_cv_1 if self.two_sided else t_stat > t_cv_1
        reject_t_5 = abs(t_stat) > t_cv_5 if self.two_sided else t_stat > t_cv_5
        reject_t_10 = abs(t_stat) > t_cv_10 if self.two_sided else t_stat > t_cv_10
        
        # ===== Durbin-Watson test =====
        dw_stat = self._compute_dw_statistic(e)
        dw_pvalue = self._dw_pvalue_approx(dw_stat, T, n_regressors)
        
        # Conclusion
        if reject_t_5:
            conclusion = "Reject H₀: Evidence of AR(1) autocorrelation. Use GLS/Cochrane-Orcutt."
        else:
            conclusion = "Do not reject H₀: No evidence of autocorrelation. OLS is appropriate."
        
        self._result = SerialIndepTestResult(
            t_statistic=float(t_stat),
            t_pvalue=float(t_pvalue),
            rho_estimate=float(rho_hat),
            rho_std_error=float(se_rho),
            dw_statistic=float(dw_stat),
            dw_pvalue_approx=float(dw_pvalue),
            t_critical_1=float(t_cv_1),
            t_critical_5=float(t_cv_5),
            t_critical_10=float(t_cv_10),
            reject_t_1=reject_t_1,
            reject_t_5=reject_t_5,
            reject_t_10=reject_t_10,
            conclusion=conclusion
        )
        
        return self._result
    
    def test_from_regression(self, y: np.ndarray, X: np.ndarray,
                              add_constant: bool = True) -> SerialIndepTestResult:
        """
        Convenience method to test from original data.
        
        Parameters
        ----------
        y : np.ndarray
            Dependent variable
        X : np.ndarray
            Regressors
        add_constant : bool
            Whether to add constant to regression
            
        Returns
        -------
        SerialIndepTestResult
            Test results
        """
        ols = OLSEstimator(add_constant=add_constant)
        result = ols.fit(y, X)
        n_regressors = result.k
        return self.test(result.residuals, n_regressors=n_regressors)
    
    @property
    def result(self) -> Optional[SerialIndepTestResult]:
        """Get the most recent test result."""
        return self._result


def serial_independence_test(residuals: np.ndarray, 
                              n_regressors: int = 1) -> SerialIndepTestResult:
    """
    Convenience function for serial independence test.
    
    Parameters
    ----------
    residuals : np.ndarray
        OLS residuals
    n_regressors : int
        Number of regressors in original model
        
    Returns
    -------
    SerialIndepTestResult
        Test results
    """
    test = SerialIndependenceTest()
    return test.test(residuals, n_regressors=n_regressors)


def durbin_watson(residuals: np.ndarray) -> float:
    """
    Compute Durbin-Watson statistic.
    
    Parameters
    ----------
    residuals : np.ndarray
        OLS residuals
        
    Returns
    -------
    float
        DW statistic (values near 2 indicate no autocorrelation)
    """
    test = SerialIndependenceTest()
    return test._compute_dw_statistic(residuals)
