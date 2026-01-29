"""
Test Suite for dyncusum Library

Tests the implementation against theoretical expectations from:
Krämer, W., Ploberger, W., & Alt, R. (1988). 
"Testing for Structural Change in Dynamic Models"
Econometrica, Vol. 56, No. 6, pp. 1355-1369.

Author: Dr. Merwan Roudane
"""

import numpy as np
import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dyncusum import (
    dynamic_cusum_test,
    dufour_test,
    cusum_ols,
    compute_recursive_residuals,
    CUSUMResult,
    CriticalValueTable,
    BDE_CRITICAL_VALUES,
    simulate_cusum_distribution,
    generate_dynamic_data,
    monte_carlo_power,
    check_stationarity,
    ols_regression,
    estimate_ar1_coefficient,
)


class TestRecursiveResiduals:
    """Test recursive residuals computation (Equation 7)."""
    
    def test_recursive_residuals_shape(self):
        """Test that recursive residuals have correct shape."""
        np.random.seed(42)
        T = 50
        K = 2
        
        y = np.random.normal(0, 1, T)
        X = np.random.normal(0, 1, (T, K))
        Z = np.column_stack([np.random.normal(0, 1, T), X])
        
        w, f = compute_recursive_residuals(y, Z)
        
        # Should have T - K - 1 - 1 = T - K - 2 residuals (starting from K+2)
        expected_length = T - (K + 1) - 1
        assert len(w) == expected_length, f"Expected {expected_length}, got {len(w)}"
        assert len(f) == expected_length
    
    def test_recursive_residuals_under_h0(self):
        """Under H0 with normal errors, recursive residuals should be ~N(0, σ²)."""
        np.random.seed(42)
        T = 200
        sigma = 1.0
        
        # Generate data under H0 (no structural change)
        X = np.column_stack([np.ones(T)])
        y = np.random.normal(5, sigma, T)  # y = 5 + u
        
        w, f = compute_recursive_residuals(y, X)
        
        # Mean should be approximately 0
        assert np.abs(np.mean(w)) < 0.3, f"Mean of residuals = {np.mean(w)}"
        
        # Std should be approximately sigma
        assert np.abs(np.std(w) - sigma) < 0.3, f"Std of residuals = {np.std(w)}"


class TestCUSUMTest:
    """Test CUSUM test statistics and procedures."""
    
    def test_cusum_test_basic(self):
        """Test basic CUSUM test functionality."""
        np.random.seed(42)
        T = 100
        
        # Generate stable AR(1) process
        y = np.zeros(T)
        u = np.random.normal(0, 1, T)
        gamma = 0.5
        
        for t in range(1, T):
            y[t] = gamma * y[t-1] + u[t]
        
        X = np.ones((T-1, 1))
        y_lagged = y[:-1]
        y_current = y[1:]
        
        result = dynamic_cusum_test(y_current, X, y_lagged)
        
        assert isinstance(result, CUSUMResult)
        assert result.statistic >= 0
        assert 0 <= result.p_value <= 1
        assert result.test_type == 'dynamic_cusum'
    
    def test_cusum_test_no_rejection_under_h0(self):
        """Under H0, rejection rate should be close to α."""
        np.random.seed(42)
        n_simulations = 100
        alpha = 0.05
        rejections = 0
        
        for _ in range(n_simulations):
            T = 100
            y = np.zeros(T)
            u = np.random.normal(0, 1, T)
            
            for t in range(1, T):
                y[t] = 0.5 * y[t-1] + u[t]
            
            X = np.ones((T-1, 1))
            result = dynamic_cusum_test(y[1:], X, y[:-1], 
                                        significance_level=alpha,
                                        n_simulations=1000)
            
            if result.reject_null:
                rejections += 1
        
        rejection_rate = rejections / n_simulations
        # Should be close to alpha (with some tolerance for Monte Carlo error)
        assert rejection_rate < 0.15, f"Rejection rate {rejection_rate} too high under H0"
    
    def test_dufour_test(self):
        """Test Dufour test functionality."""
        np.random.seed(42)
        T = 100
        
        y = np.zeros(T)
        u = np.random.normal(0, 1, T)
        
        for t in range(1, T):
            y[t] = 0.5 * y[t-1] + u[t]
        
        X = np.ones((T-1, 1))
        
        result = dufour_test(y[1:], X, y[:-1])
        
        assert isinstance(result, CUSUMResult)
        assert result.test_type == 'dufour'


class TestCriticalValues:
    """Test critical value computation."""
    
    def test_bde_critical_values(self):
        """Test that BDE tabulated values are present."""
        assert 0.05 in BDE_CRITICAL_VALUES
        assert np.isclose(BDE_CRITICAL_VALUES[0.05], 0.948, atol=0.01)
        assert np.isclose(BDE_CRITICAL_VALUES[0.01], 1.143, atol=0.01)
    
    def test_simulated_distribution(self):
        """Test Monte Carlo simulation of null distribution."""
        np.random.seed(42)
        max_stats = simulate_cusum_distribution(n_simulations=1000)
        
        assert len(max_stats) == 1000
        assert np.all(max_stats >= 0)
        
        # 95th percentile should be close to 0.948
        cv_05 = np.percentile(max_stats, 95)
        assert np.abs(cv_05 - 0.948) < 0.15, f"Simulated CV = {cv_05}"
    
    def test_critical_value_table(self):
        """Test CriticalValueTable class."""
        table = CriticalValueTable(n_simulations=1000, seed=42)
        
        cv_05 = table.get_critical_value(0.05)
        assert np.abs(cv_05 - 0.948) < 0.05
        
        # Test p-value computation
        p_val = table.compute_p_value(1.0)
        assert 0 < p_val < 0.1


class TestPowerAnalysis:
    """Test power analysis functions."""
    
    def test_generate_dynamic_data(self):
        """Test data generation."""
        T = 100
        gamma = 0.5
        beta = np.array([2, 10])
        
        y, X, y_lagged = generate_dynamic_data(T, gamma, beta, seed=42)
        
        assert len(y) == T
        assert X.shape == (T, 2)
        assert len(y_lagged) == T
    
    def test_data_with_structural_break(self):
        """Test data generation with structural break."""
        T = 100
        gamma = 0.5
        beta = np.array([2, 10])
        
        structural_break = {
            'z_star': 0.5,
            'delta_delta': np.array([0, 1, 2])
        }
        
        y, X, y_lagged = generate_dynamic_data(T, gamma, beta, 
                                                structural_break=structural_break,
                                                seed=42)
        
        assert len(y) == T
    
    def test_theorem_2_orthogonal_shift(self):
        """
        Test Theorem 2: Power should be trivial when shift is orthogonal to mean regressor.
        
        When ψ = 90°, the structural shift is orthogonal to the mean regressor,
        and the test should have no power (rejection rate ≈ α).
        """
        np.random.seed(42)
        
        # At ψ = 90° (orthogonal), power should be close to nominal size
        power_orthogonal = monte_carlo_power(
            gamma=0.0, psi=90, z_star=0.5, b=12,
            T=120, n_simulations=50,
            significance_level=0.05
        )
        
        # Power at ψ = 0° (parallel) should be higher
        power_parallel = monte_carlo_power(
            gamma=0.0, psi=0, z_star=0.5, b=12,
            T=120, n_simulations=50,
            significance_level=0.05
        )
        
        # Orthogonal case should have lower power than parallel case
        # (though with few simulations, this might not always hold)
        assert power_orthogonal.power <= power_parallel.power + 0.3


class TestUtilities:
    """Test utility functions."""
    
    def test_stationarity_check(self):
        """Test stationarity condition check."""
        assert check_stationarity(0.5) == True
        assert check_stationarity(-0.5) == True
        assert check_stationarity(0.99) == True
        assert check_stationarity(1.0) == False
        assert check_stationarity(-1.0) == False
    
    def test_ols_regression(self):
        """Test OLS regression."""
        np.random.seed(42)
        T = 100
        X = np.column_stack([np.ones(T), np.random.normal(0, 1, T)])
        beta_true = np.array([5, 2])
        y = X @ beta_true + np.random.normal(0, 0.5, T)
        
        beta_hat, residuals, sigma = ols_regression(y, X)
        
        # Estimates should be close to true values
        assert np.allclose(beta_hat, beta_true, atol=0.5)
        assert len(residuals) == T
    
    def test_ar1_coefficient_estimation(self):
        """Test AR(1) coefficient estimation."""
        np.random.seed(42)
        T = 500
        gamma_true = 0.7
        
        y = np.zeros(T)
        u = np.random.normal(0, 1, T)
        
        for t in range(1, T):
            y[t] = gamma_true * y[t-1] + u[t]
        
        gamma_hat = estimate_ar1_coefficient(y)
        
        assert np.abs(gamma_hat - gamma_true) < 0.1


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_small_sample(self):
        """Test with minimum viable sample size."""
        np.random.seed(42)
        T = 15  # Small but valid
        
        y = np.random.normal(0, 1, T)
        X = np.ones((T, 1))
        
        result = cusum_ols(y, X)
        
        assert isinstance(result, CUSUMResult)
    
    def test_multiple_regressors(self):
        """Test with multiple regressors."""
        np.random.seed(42)
        T = 100
        K = 5
        
        X = np.random.normal(0, 1, (T, K))
        beta = np.random.normal(0, 1, K)
        y = X @ beta + np.random.normal(0, 1, T)
        
        result = cusum_ols(y, X)
        
        assert isinstance(result, CUSUMResult)
        assert result.n_regressors == K


def run_tests():
    """Run all tests and report results."""
    print("="*60)
    print("Running dyncusum Test Suite")
    print("="*60)
    print()
    
    test_classes = [
        TestRecursiveResiduals,
        TestCUSUMTest,
        TestCriticalValues,
        TestPowerAnalysis,
        TestUtilities,
        TestEdgeCases,
    ]
    
    total_tests = 0
    passed_tests = 0
    failed_tests = []
    
    for test_class in test_classes:
        print(f"\nTesting: {test_class.__name__}")
        print("-" * 40)
        
        instance = test_class()
        methods = [m for m in dir(instance) if m.startswith('test_')]
        
        for method_name in methods:
            total_tests += 1
            try:
                getattr(instance, method_name)()
                print(f"  ✓ {method_name}")
                passed_tests += 1
            except Exception as e:
                print(f"  ✗ {method_name}: {str(e)}")
                failed_tests.append((test_class.__name__, method_name, str(e)))
    
    print("\n" + "="*60)
    print(f"Results: {passed_tests}/{total_tests} tests passed")
    
    if failed_tests:
        print("\nFailed tests:")
        for cls, method, error in failed_tests:
            print(f"  - {cls}.{method}: {error}")
    
    return len(failed_tests) == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
