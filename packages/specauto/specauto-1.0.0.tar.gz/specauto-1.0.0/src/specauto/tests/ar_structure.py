"""
AR Structure Test Module

Tests whether AR(1) errors are adequate vs. higher-order AR(1+q) or ARMA(1,q).
This tests hypothesis (b) vs (c) in Godfrey's (1987) strategy.

Reference:
    Godfrey, L. G. (1987). Equation (18):
        e_t = δ₁e_{t-1} + δ₂e_{t-2} + ... + δ_{1+q}e_{t-1-q} + a_t
    
    Test: H₀: δ₂ = δ₃ = ... = δ_{1+q} = 0
    
    "Hence a large sample test of H_s can be obtained simply by calculating
    the OLS residuals e_t for the original regression model (1) and then
    applying the standard F-test of δ₂ = ... = δ_{1+q} = 0 in the
    autoregression (18)."
    
    The test is:
    - Asymptotically equivalent to LM, LR, and Wald tests
    - Also appropriate for ARMA(1, q) alternatives
    - Consistent for several other error processes
"""

import numpy as np
from scipy import stats
from dataclasses import dataclass
from typing import Optional
from ..estimation.ols import OLSEstimator


@dataclass
class ARStructureTestResult:
    """Results from AR structure test."""
    f_statistic: float         # F test statistic
    p_value: float             # p-value
    df1: int                   # Numerator degrees of freedom (q)
    df2: int                   # Denominator degrees of freedom (T-1-q)
    critical_value_1: float    # Critical value at 1%
    critical_value_5: float    # Critical value at 5%
    critical_value_10: float   # Critical value at 10%
    reject_1: bool             # Reject at 1%?
    reject_5: bool             # Reject at 5%?
    reject_10: bool            # Reject at 10%?
    p: int                     # AR order for null hypothesis
    q: int                     # Additional lags for alternative
    ssr_restricted: float      # SSR from AR(p) model
    ssr_unrestricted: float    # SSR from AR(p+q) model
    rho_estimates: np.ndarray  # Estimated AR coefficients
    conclusion: str            # Verbal conclusion


class ARStructureTest:
    """
    Test AR(1) vs AR(1+q) Error Structure.
    
    Tests whether the error autocorrelation can be adequately captured
    by a simple AR(1) process, or whether higher-order terms are needed.
    
    The test uses OLS residuals from the original regression and fits
    an autoregression, then tests the joint significance of higher-order
    coefficients.
    
    Reference:
        Godfrey (1987), p. 132:
        "The choice of the parameter q in (18) is obviously important.
        As suggested above, it seems reasonable to take account of the
        nature of the data by using q = 3 or for quarterly data, q = 11
        or 12 for monthly data and so on, otherwise the test will lack
        power in the presence of pure seasonal autocorrelation."
    """
    
    def __init__(self, p: int = 1, q: int = 4, significance_level: float = 0.05):
        """
        Initialize AR structure test.
        
        Parameters
        ----------
        p : int
            AR order for null hypothesis (default: 1 for AR(1))
        q : int
            Additional lags for alternative (default: 4 for quarterly data)
            Use q=3 or 4 for quarterly, q=11 or 12 for monthly
        significance_level : float
            Significance level for testing
        """
        self.p = p
        self.q = q
        self.significance_level = significance_level
        self._result: Optional[ARStructureTestResult] = None
    
    def _create_lag_matrix(self, e: np.ndarray, max_lag: int) -> tuple:
        """
        Create lagged variable matrix for autoregression.
        
        Parameters
        ----------
        e : np.ndarray
            Residuals
        max_lag : int
            Maximum lag to include
            
        Returns
        -------
        tuple
            (y, X) where y is e_t and X contains e_{t-1}, ..., e_{t-max_lag}
        """
        T = len(e)
        effective_T = T - max_lag
        
        y = e[max_lag:]  # e_t for t = max_lag+1, ..., T
        
        X = np.zeros((effective_T, max_lag))
        for lag in range(1, max_lag + 1):
            X[:, lag - 1] = e[max_lag - lag:-lag if lag < T else None]
        
        return y, X
    
    def test(self, residuals: np.ndarray) -> ARStructureTestResult:
        """
        Perform AR structure test on residuals.
        
        Tests H₀: δ_{p+1} = δ_{p+2} = ... = δ_{p+q} = 0
        in the autoregression:
            e_t = δ₁e_{t-1} + ... + δ_p e_{t-p} + δ_{p+1}e_{t-p-1} + ... + δ_{p+q}e_{t-p-q} + a_t
        
        Parameters
        ----------
        residuals : np.ndarray
            OLS residuals from original regression
            
        Returns
        -------
        ARStructureTestResult
            Complete test results
        """
        e = np.asarray(residuals).flatten()
        T = len(e)
        
        max_lag = self.p + self.q
        
        if T <= max_lag + 1:
            raise ValueError(f"Not enough observations. Need T > {max_lag + 1}, got T = {T}")
        
        # Create lagged variables
        y, X_full = self._create_lag_matrix(e, max_lag)
        effective_T = len(y)
        
        # Unrestricted model: AR(p+q)
        ols_unrestricted = OLSEstimator(add_constant=False)
        result_u = ols_unrestricted.fit(y, X_full)
        ssr_u = result_u.ssr
        
        # Restricted model: AR(p) - only first p lags
        X_restricted = X_full[:, :self.p]
        ols_restricted = OLSEstimator(add_constant=False)
        result_r = ols_restricted.fit(y, X_restricted)
        ssr_r = result_r.ssr
        
        # F-test statistic
        # F = [(SSR_r - SSR_u) / q] / [SSR_u / (T - p - q)]
        df1 = self.q  # Number of restrictions
        df2 = effective_T - max_lag  # Denominator df
        
        if df2 <= 0:
            raise ValueError(f"Not enough degrees of freedom: df2 = {df2}")
        
        f_stat = ((ssr_r - ssr_u) / df1) / (ssr_u / df2)
        
        # p-value from F distribution
        p_value = 1 - stats.f.cdf(f_stat, df1, df2)
        
        # Critical values
        cv_1 = stats.f.ppf(0.99, df1, df2)
        cv_5 = stats.f.ppf(0.95, df1, df2)
        cv_10 = stats.f.ppf(0.90, df1, df2)
        
        # Make decisions
        reject_1 = f_stat > cv_1
        reject_5 = f_stat > cv_5
        reject_10 = f_stat > cv_10
        
        # Conclusion
        if reject_5:
            conclusion = f"Reject H₀: AR({self.p}) inadequate, need AR({self.p + self.q}) or ARMA({self.p},{self.q})"
        else:
            conclusion = f"Do not reject H₀: AR({self.p}) errors may be adequate"
        
        self._result = ARStructureTestResult(
            f_statistic=float(f_stat),
            p_value=float(p_value),
            df1=df1,
            df2=df2,
            critical_value_1=float(cv_1),
            critical_value_5=float(cv_5),
            critical_value_10=float(cv_10),
            reject_1=reject_1,
            reject_5=reject_5,
            reject_10=reject_10,
            p=self.p,
            q=self.q,
            ssr_restricted=float(ssr_r),
            ssr_unrestricted=float(ssr_u),
            rho_estimates=result_u.beta,
            conclusion=conclusion
        )
        
        return self._result
    
    def test_from_regression(self, y: np.ndarray, X: np.ndarray,
                              add_constant: bool = True) -> ARStructureTestResult:
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
        ARStructureTestResult
            Test results
        """
        ols = OLSEstimator(add_constant=add_constant)
        result = ols.fit(y, X)
        return self.test(result.residuals)
    
    @property
    def result(self) -> Optional[ARStructureTestResult]:
        """Get the most recent test result."""
        return self._result


def ar_structure_test(residuals: np.ndarray, p: int = 1, q: int = 4) -> ARStructureTestResult:
    """
    Convenience function for AR structure test.
    
    Parameters
    ----------
    residuals : np.ndarray
        OLS residuals
    p : int
        AR order for null hypothesis
    q : int
        Additional lags to test
        
    Returns
    -------
    ARStructureTestResult
        Test results
    """
    test = ARStructureTest(p=p, q=q)
    return test.test(residuals)


def godfrey_test(residuals: np.ndarray, p: int = 1, q: int = 4) -> ARStructureTestResult:
    """
    Alias for ar_structure_test following Godfrey (1987).
    
    This is the test from Equation (18) of the paper.
    """
    return ar_structure_test(residuals, p=p, q=q)
