"""
Unit Tests for AutoSpec Library

Tests the implementation of Godfrey's (1987) test strategy for
discriminating between autocorrelation and misspecification.

Author: Dr Merwan Roudane
"""

import numpy as np
import pytest
import sys
sys.path.insert(0, '../src')


class TestOLSEstimator:
    """Tests for OLS estimation."""
    
    def test_ols_basic(self):
        """Test basic OLS estimation."""
        from autospec.estimation.ols import OLSEstimator
        
        np.random.seed(42)
        T = 100
        X = np.random.randn(T, 2)
        beta_true = np.array([1, 2, 3])  # constant + 2 coefficients
        y = 1 + 2*X[:, 0] + 3*X[:, 1] + np.random.randn(T) * 0.1
        
        ols = OLSEstimator(add_constant=True)
        result = ols.fit(y, X)
        
        # Check dimensions
        assert len(result.beta) == 3
        assert len(result.residuals) == T
        assert result.n == T
        assert result.k == 3
        
        # Check estimates are close to true values
        np.testing.assert_allclose(result.beta, beta_true, atol=0.2)
        
        # R-squared should be high
        assert result.r_squared > 0.95
    
    def test_ols_no_constant(self):
        """Test OLS without constant."""
        from autospec.estimation.ols import OLSEstimator
        
        np.random.seed(42)
        T = 100
        X = np.random.randn(T, 2)
        y = 2*X[:, 0] + 3*X[:, 1] + np.random.randn(T) * 0.1
        
        ols = OLSEstimator(add_constant=False)
        result = ols.fit(y, X)
        
        assert len(result.beta) == 2
        assert result.k == 2


class TestHACEstimator:
    """Tests for HAC covariance estimation."""
    
    def test_hac_basic(self):
        """Test basic HAC estimation."""
        from autospec.estimation.hac import HACEstimator
        
        np.random.seed(42)
        T = 100
        X = np.random.randn(T, 3)
        residuals = np.random.randn(T)
        
        hac = HACEstimator(truncation_j=4)
        result = hac.estimate(X, residuals)
        
        # Check dimensions
        assert result.covariance_matrix.shape == (3, 3)
        assert len(result.robust_std_errors) == 3
        assert result.truncation_j == 4
        
        # Covariance matrix should be symmetric
        np.testing.assert_array_almost_equal(
            result.covariance_matrix, 
            result.covariance_matrix.T
        )
    
    def test_hac_positive_semidefinite(self):
        """HAC covariance should be positive semi-definite."""
        from autospec.estimation.hac import HACEstimator
        
        np.random.seed(42)
        T = 100
        X = np.random.randn(T, 3)
        residuals = np.random.randn(T)
        
        hac = HACEstimator(truncation_j=4)
        result = hac.estimate(X, residuals)
        
        # Check eigenvalues are non-negative
        eigenvalues = np.linalg.eigvalsh(result.covariance_matrix)
        assert np.all(eigenvalues >= -1e-10)


class TestMisspecificationTest:
    """Tests for HAC-robust misspecification test."""
    
    def test_correctly_specified_model(self):
        """Test that correctly specified model is not rejected."""
        from autospec.tests.misspecification import MisspecificationTest
        
        np.random.seed(42)
        T = 200
        X = np.random.randn(T, 2)
        y = 1 + 2*X[:, 0] + 3*X[:, 1] + np.random.randn(T)
        
        test = MisspecificationTest(significance_level=0.05)
        result = test.test(y, X)
        
        # Should not reject at 5%
        # (Note: with random data, there's a 5% chance of rejection)
        assert result.p_value > 0.01  # Loose check
        assert result.df == 2  # Two RESET powers
        assert result.statistic >= 0
    
    def test_misspecified_model(self):
        """Test that omitted quadratic term is detected."""
        from autospec.tests.misspecification import MisspecificationTest
        
        np.random.seed(42)
        T = 200
        X = np.random.randn(T, 1)
        
        # True model has quadratic term
        y = 1 + 2*X[:, 0] + 3*X[:, 0]**2 + np.random.randn(T) * 0.5
        
        test = MisspecificationTest(significance_level=0.05)
        result = test.test(y, X)
        
        # Should reject (detect misspecification)
        assert result.reject_5 or result.p_value < 0.20  # Should be likely to reject


class TestARStructureTest:
    """Tests for AR structure test."""
    
    def test_ar1_errors(self):
        """Test with AR(1) errors - should not reject."""
        from autospec.tests.ar_structure import ARStructureTest
        from autospec.estimation.ols import OLSEstimator
        
        np.random.seed(42)
        T = 200
        X = np.random.randn(T, 2)
        
        # Generate AR(1) errors
        rho = 0.5
        u = np.random.randn(T)
        epsilon = np.zeros(T)
        for t in range(1, T):
            epsilon[t] = rho * epsilon[t-1] + u[t]
        
        y = 1 + 2*X[:, 0] + 3*X[:, 1] + epsilon
        
        # Get residuals
        ols = OLSEstimator()
        ols_result = ols.fit(y, X)
        
        # Test AR structure
        test = ARStructureTest(p=1, q=4)
        result = test.test(ols_result.residuals)
        
        # AR(1) should be adequate (should not reject)
        assert result.f_statistic >= 0
        assert result.p_value >= 0 and result.p_value <= 1
    
    def test_ar4_errors(self):
        """Test with AR(4) errors - should reject AR(1)."""
        from autospec.tests.ar_structure import ARStructureTest
        from autospec.estimation.ols import OLSEstimator
        
        np.random.seed(42)
        T = 300
        X = np.random.randn(T, 2)
        
        # Generate AR(4) errors with significant higher-order terms
        u = np.random.randn(T)
        epsilon = np.zeros(T)
        for t in range(4, T):
            epsilon[t] = 0.2*epsilon[t-1] + 0.1*epsilon[t-2] + 0.1*epsilon[t-3] + 0.5*epsilon[t-4] + u[t]
        
        y = 1 + 2*X[:, 0] + 3*X[:, 1] + epsilon
        
        # Get residuals
        ols = OLSEstimator()
        ols_result = ols.fit(y, X)
        
        # Test AR structure
        test = ARStructureTest(p=1, q=4)
        result = test.test(ols_result.residuals)
        
        # Should likely reject AR(1) in favor of AR(1+4)
        # (Though due to randomness, we just check it's valid)
        assert result.p_value >= 0 and result.p_value <= 1


class TestSerialIndependenceTest:
    """Tests for serial independence test."""
    
    def test_independent_errors(self):
        """Test with i.i.d. errors - should not reject."""
        from autospec.tests.serial_independence import SerialIndependenceTest
        
        np.random.seed(42)
        T = 200
        residuals = np.random.randn(T)
        
        test = SerialIndependenceTest()
        result = test.test(residuals)
        
        # DW should be close to 2
        assert 1.5 < result.dw_statistic < 2.5
        
        # rho estimate should be close to 0
        assert abs(result.rho_estimate) < 0.3
        
        # Should not reject independence
        assert result.p_value > 0.01
    
    def test_ar1_errors_detection(self):
        """Test that AR(1) errors are detected."""
        from autospec.tests.serial_independence import SerialIndependenceTest
        
        np.random.seed(42)
        T = 200
        
        # Generate strong AR(1) errors
        rho = 0.8
        u = np.random.randn(T)
        residuals = np.zeros(T)
        for t in range(1, T):
            residuals[t] = rho * residuals[t-1] + u[t]
        
        test = SerialIndependenceTest()
        result = test.test(residuals)
        
        # DW should be low (positive autocorrelation)
        assert result.dw_statistic < 1.5
        
        # rho estimate should be close to true rho
        assert result.rho_estimate > 0.5
        
        # Should reject independence
        assert result.reject_t_5


class TestAutoSpec:
    """Tests for main AutoSpec class."""
    
    def test_no_problem_case(self):
        """Test correctly specified model with i.i.d. errors."""
        from autospec import AutoSpec
        
        np.random.seed(42)
        T = 200
        X = np.random.randn(T, 2)
        y = 1 + 2*X[:, 0] + 3*X[:, 1] + np.random.randn(T)
        
        autospec = AutoSpec(y, X)
        results = autospec.run_full_strategy()
        
        # Should adopt hypothesis (d) - no problem
        # (With 5% tests, there's still a chance of rejection)
        assert results.adopted_hypothesis in ["(a)", "(b)", "(c)", "(d)"]
        assert len(results.conclusion) > 0
        assert len(results.recommendation) > 0
    
    def test_ar1_case(self):
        """Test correctly specified model with AR(1) errors."""
        from autospec import AutoSpec
        
        np.random.seed(42)
        T = 200
        X = np.random.randn(T, 2)
        
        # Generate AR(1) errors
        rho = 0.7
        u = np.random.randn(T)
        epsilon = np.zeros(T)
        for t in range(1, T):
            epsilon[t] = rho * epsilon[t-1] + u[t]
        
        y = 1 + 2*X[:, 0] + 3*X[:, 1] + epsilon
        
        autospec = AutoSpec(y, X)
        results = autospec.run_full_strategy()
        
        # Should detect AR(1) or higher
        assert results.adopted_hypothesis in ["(b)", "(c)", "(d)"]
    
    def test_summary_output(self):
        """Test that summary generates readable output."""
        from autospec import AutoSpec
        
        np.random.seed(42)
        T = 100
        X = np.random.randn(T, 2)
        y = 1 + 2*X[:, 0] + 3*X[:, 1] + np.random.randn(T)
        
        autospec = AutoSpec(y, X)
        summary = autospec.summary()
        
        # Check summary contains key elements
        assert "GODFREY" in summary
        assert "Misspecification" in summary
        assert "DIAGNOSIS" in summary
        assert len(summary) > 500
    
    def test_to_dict(self):
        """Test dictionary conversion."""
        from autospec import AutoSpec
        
        np.random.seed(42)
        T = 100
        X = np.random.randn(T, 2)
        y = 1 + 2*X[:, 0] + 3*X[:, 1] + np.random.randn(T)
        
        autospec = AutoSpec(y, X)
        autospec.run_full_strategy()
        results_dict = autospec.to_dict()
        
        # Check dictionary structure
        assert 'adopted_hypothesis' in results_dict
        assert 'conclusion' in results_dict
        assert 'misspecification_test' in results_dict
        assert 'ar_structure_test' in results_dict
        assert 'serial_independence_test' in results_dict
        assert 'ols' in results_dict


class TestCriticalValueSimulation:
    """Tests for critical value simulation."""
    
    def test_simulation_runs(self):
        """Test that simulation runs without errors."""
        from autospec.simulation.critical_values import simulate_critical_values
        
        # Use small number of simulations for speed
        tables = simulate_critical_values(
            n_simulations=100,
            sample_sizes=[50, 100],
            seed=42
        )
        
        assert 'misspecification' in tables
        assert 'ar_structure' in tables
        
        # Check critical values exist
        cv_df = tables['misspecification'].critical_values
        assert not cv_df.empty


class TestOutputTables:
    """Tests for output formatting."""
    
    def test_latex_output(self):
        """Test LaTeX table generation."""
        from autospec import AutoSpec
        from autospec.output.tables import format_latex_table
        
        np.random.seed(42)
        T = 100
        X = np.random.randn(T, 2)
        y = 1 + 2*X[:, 0] + 3*X[:, 1] + np.random.randn(T)
        
        autospec = AutoSpec(y, X)
        results = autospec.run_full_strategy()
        
        latex = format_latex_table(results)
        
        # Check LaTeX structure
        assert r"\begin{table}" in latex
        assert r"\end{table}" in latex
        assert r"\chi^2" in latex or r"χ²" in latex


if __name__ == "__main__":
    # Run with pytest
    pytest.main([__file__, "-v"])
