"""
Core AutoSpec Module

Main class implementing Godfrey's (1987) complete test strategy for
discriminating between autocorrelation and misspecification.

Reference:
    Godfrey, L. G. (1987). "Discriminating Between Autocorrelation and 
    Misspecification in Regression Analysis: An Alternative Test Strategy."
    The Review of Economics and Statistics, Vol. 69, No. 1, pp. 128-134.

The strategy tests an ordered sequence of hypotheses:
    (a) Regression function is incorrectly specified; disturbances ARMA
    (b) Regression function is correctly specified; disturbances ARMA  
    (c) Regression function is correctly specified; disturbances AR(1)
    (d) Regression function is correctly specified; disturbances independent
"""

import numpy as np
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from .tests.misspecification import MisspecificationTest, MisspecTestResult
from .tests.ar_structure import ARStructureTest, ARStructureTestResult
from .tests.serial_independence import SerialIndependenceTest, SerialIndepTestResult
from .estimation.ols import OLSEstimator, OLSResult
from .estimation.hac import HACEstimator


@dataclass
class AutoSpecResults:
    """
    Complete results from Godfrey's (1987) test strategy.
    
    Attributes
    ----------
    ols_result : OLSResult
        Results from initial OLS estimation
    misspec_result : MisspecTestResult
        Results from HAC-robust misspecification test (a vs b)
    ar_structure_result : ARStructureTestResult
        Results from AR structure test (b vs c)
    serial_indep_result : SerialIndepTestResult
        Results from serial independence test (c vs d)
    adopted_hypothesis : str
        The adopted hypothesis from the sequence (a, b, c, or d)
    conclusion : str
        Verbal conclusion about the diagnostic outcome
    recommendation : str
        Recommended action based on the diagnosis
    """
    ols_result: OLSResult
    misspec_result: MisspecTestResult
    ar_structure_result: ARStructureTestResult
    serial_indep_result: SerialIndepTestResult
    adopted_hypothesis: str
    conclusion: str
    recommendation: str


class AutoSpec:
    """
    Godfrey's (1987) Alternative Test Strategy for Discriminating
    Between Autocorrelation and Misspecification.
    
    This class implements the complete ordered hypothesis testing sequence:
    
    1. Test for misspecification (HAC-robust): (a) vs (b)
       - If rejected: adopt (a) - regression function is misspecified
       
    2. Test AR structure: (b) vs (c)  
       - If rejected: adopt (b) - need higher-order AR or ARMA errors
       
    3. Test serial independence: (c) vs (d)
       - If rejected: adopt (c) - AR(1) errors present
       - If not rejected: adopt (d) - independent errors, OLS appropriate
    
    Usage
    -----
    >>> from specauto import AutoSpec
    >>> import numpy as np
    >>> 
    >>> # Generate sample data
    >>> np.random.seed(42)
    >>> T = 100
    >>> X = np.random.randn(T, 2)
    >>> y = 1 + 2*X[:, 0] + 3*X[:, 1] + np.random.randn(T)
    >>>
    >>> # Run the complete test strategy
    >>> autospec = AutoSpec(y, X)
    >>> results = autospec.run_full_strategy()
    >>> print(results.conclusion)
    
    Reference
    ---------
    Godfrey, L. G. (1987). The Review of Economics and Statistics, 69(1), 128-134.
    """
    
    def __init__(self, y: np.ndarray, X: np.ndarray, 
                 significance_level: float = 0.05,
                 add_constant: bool = True):
        """
        Initialize AutoSpec with data.
        
        Parameters
        ----------
        y : np.ndarray
            Dependent variable (T x 1)
        X : np.ndarray
            Regressor matrix (T x k), excluding constant
        significance_level : float
            Significance level for all tests (default: 0.05)
        add_constant : bool
            Whether to add a constant term (default: True)
        """
        self.y = np.asarray(y).flatten()
        self.X = np.asarray(X)
        if self.X.ndim == 1:
            self.X = self.X.reshape(-1, 1)
        
        self.significance_level = significance_level
        self.add_constant = add_constant
        self.T = len(self.y)
        
        # Fit initial OLS
        self._ols = OLSEstimator(add_constant=add_constant)
        self._ols_result = self._ols.fit(self.y, self.X)
        
        # Store results
        self._results: Optional[AutoSpecResults] = None
    
    @property
    def residuals(self) -> np.ndarray:
        """Get OLS residuals."""
        return self._ols_result.residuals
    
    @property
    def ols_result(self) -> OLSResult:
        """Get OLS estimation results."""
        return self._ols_result
    
    def test_misspecification(self, 
                               Z: Optional[np.ndarray] = None,
                               reset_powers: List[int] = None,
                               truncation_j: Optional[int] = None) -> MisspecTestResult:
        """
        Test for misspecification (hypothesis a vs b).
        
        Uses HAC-robust test statistic from Equation (10) of Godfrey (1987).
        
        Parameters
        ----------
        Z : np.ndarray, optional
            Custom test variables. If None, uses RESET-style variables.
        reset_powers : list of int, optional
            Powers for RESET test variables (default: [2, 3])
        truncation_j : int, optional
            HAC truncation parameter. If None, uses floor(T^(1/3)).
            
        Returns
        -------
        MisspecTestResult
            Complete test results including χ² statistic and p-value
        """
        test = MisspecificationTest(
            significance_level=self.significance_level,
            truncation_j=truncation_j
        )
        return test.test(
            self.y, self.X, 
            Z=Z, 
            reset_powers=reset_powers,
            add_constant=self.add_constant
        )
    
    def test_ar_structure(self, p: int = 1, q: int = 4) -> ARStructureTestResult:
        """
        Test AR structure (hypothesis b vs c).
        
        Tests whether AR(p) is adequate vs AR(p+q) using Equation (18).
        
        Parameters
        ----------
        p : int
            AR order for null hypothesis (default: 1)
        q : int
            Additional lags for alternative (default: 4 for quarterly data)
            Use q=3 or 4 for quarterly, q=11 or 12 for monthly data.
            
        Returns
        -------
        ARStructureTestResult
            Complete test results including F-statistic and p-value
        """
        test = ARStructureTest(
            p=p, q=q,
            significance_level=self.significance_level
        )
        return test.test(self.residuals)
    
    def test_serial_independence(self) -> SerialIndepTestResult:
        """
        Test for serial independence (hypothesis c vs d).
        
        Tests H₀: ρ = 0 using both t-test and Durbin-Watson.
        
        Returns
        -------
        SerialIndepTestResult
            Complete test results including t-statistic, DW, and p-value
        """
        test = SerialIndependenceTest(
            significance_level=self.significance_level
        )
        return test.test(
            self.residuals, 
            n_regressors=self._ols_result.k
        )
    
    def run_full_strategy(self, 
                          reset_powers: List[int] = None,
                          truncation_j: Optional[int] = None,
                          ar_p: int = 1,
                          ar_q: int = 4) -> AutoSpecResults:
        """
        Execute the complete Godfrey (1987) test strategy.
        
        Tests the ordered sequence of hypotheses:
        1. Misspecification test (a vs b)
        2. AR structure test (b vs c)
        3. Serial independence test (c vs d)
        
        The strategy stops at the first rejection and adopts the 
        corresponding hypothesis.
        
        Parameters
        ----------
        reset_powers : list of int, optional
            Powers for RESET test variables (default: [2, 3])
        truncation_j : int, optional
            HAC truncation parameter for misspecification test
        ar_p : int
            AR order for null (default: 1)
        ar_q : int
            Additional AR lags for alternative (default: 4)
            
        Returns
        -------
        AutoSpecResults
            Complete results from all tests with final diagnosis
        """
        # Step 1: Test for misspecification (a vs b)
        misspec_result = self.test_misspecification(
            reset_powers=reset_powers,
            truncation_j=truncation_j
        )
        
        # Step 2: Test AR structure (b vs c)
        ar_result = self.test_ar_structure(p=ar_p, q=ar_q)
        
        # Step 3: Test serial independence (c vs d)
        serial_result = self.test_serial_independence()
        
        # Determine adopted hypothesis and conclusion
        adopted, conclusion, recommendation = self._determine_diagnosis(
            misspec_result, ar_result, serial_result, ar_p, ar_q
        )
        
        self._results = AutoSpecResults(
            ols_result=self._ols_result,
            misspec_result=misspec_result,
            ar_structure_result=ar_result,
            serial_indep_result=serial_result,
            adopted_hypothesis=adopted,
            conclusion=conclusion,
            recommendation=recommendation
        )
        
        return self._results
    
    def _determine_diagnosis(self, 
                              misspec: MisspecTestResult,
                              ar_struct: ARStructureTestResult,
                              serial: SerialIndepTestResult,
                              ar_p: int,
                              ar_q: int) -> tuple:
        """
        Determine the final diagnosis based on test results.
        
        The strategy tests along the sequence until rejection.
        The last non-rejected hypothesis is adopted.
        """
        # Check at 5% significance level
        if misspec.reject_5:
            adopted = "(a)"
            conclusion = "Regression function is MISSPECIFIED"
            recommendation = (
                "Re-specify the regression model. Consider adding omitted "
                "variables, different functional form, or interaction terms."
            )
        elif ar_struct.reject_5:
            adopted = "(b)"
            conclusion = f"Correct specification but errors are non-AR({ar_p})"
            recommendation = (
                f"Use generalized least squares with AR({ar_p + ar_q}) or "
                f"ARMA({ar_p},{ar_q}) error correction. Alternatively, use OLS "
                "with HAC standard errors."
            )
        elif serial.reject_t_5:
            adopted = "(c)"
            conclusion = f"Correct specification with AR({ar_p}) errors"
            recommendation = (
                f"Re-estimate using Cochrane-Orcutt, Hildreth-Liu, or FGLS "
                f"allowing for AR({ar_p}) disturbances."
            )
        else:
            adopted = "(d)"
            conclusion = "NO PROBLEM - Correct specification with independent errors"
            recommendation = (
                "OLS estimator is appropriate. No correction needed."
            )
        
        return adopted, conclusion, recommendation
    
    @property
    def results(self) -> Optional[AutoSpecResults]:
        """Get the most recent test results."""
        return self._results
    
    def summary(self) -> str:
        """
        Generate a text summary of the test results.
        
        Returns
        -------
        str
            Formatted summary of all test results
        """
        if self._results is None:
            self.run_full_strategy()
        
        from .output.tables import format_autospec_results
        return format_autospec_results(self._results)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert results to dictionary format.
        
        Returns
        -------
        dict
            Dictionary containing all test results
        """
        if self._results is None:
            self.run_full_strategy()
        
        r = self._results
        return {
            'adopted_hypothesis': r.adopted_hypothesis,
            'conclusion': r.conclusion,
            'recommendation': r.recommendation,
            'misspecification_test': {
                'statistic': r.misspec_result.statistic,
                'p_value': r.misspec_result.p_value,
                'df': r.misspec_result.df,
                'reject_5pct': r.misspec_result.reject_5
            },
            'ar_structure_test': {
                'f_statistic': r.ar_structure_result.f_statistic,
                'p_value': r.ar_structure_result.p_value,
                'df1': r.ar_structure_result.df1,
                'df2': r.ar_structure_result.df2,
                'reject_5pct': r.ar_structure_result.reject_5
            },
            'serial_independence_test': {
                't_statistic': r.serial_indep_result.t_statistic,
                'p_value': r.serial_indep_result.t_pvalue,
                'dw_statistic': r.serial_indep_result.dw_statistic,
                'rho_estimate': r.serial_indep_result.rho_estimate,
                'reject_5pct': r.serial_indep_result.reject_t_5
            },
            'ols': {
                'r_squared': r.ols_result.r_squared,
                'adj_r_squared': r.ols_result.adj_r_squared,
                'n_obs': r.ols_result.n,
                'n_regressors': r.ols_result.k
            }
        }
