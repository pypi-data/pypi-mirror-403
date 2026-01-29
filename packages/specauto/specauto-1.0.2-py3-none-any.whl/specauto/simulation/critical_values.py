"""
Critical Values Simulation Module

Generates critical values for the AutoSpec tests through Monte Carlo simulation.
This is used when analytical critical values are not available.

Reference:
    Godfrey, L. G. (1987). The Review of Economics and Statistics, 69(1), 128-134.
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from scipy import stats


@dataclass
class CriticalValueTable:
    """
    Critical values table from Monte Carlo simulation.
    
    Attributes
    ----------
    test_name : str
        Name of the test
    sample_sizes : list
        Sample sizes used in simulation
    significance_levels : list
        Significance levels (e.g., [0.01, 0.05, 0.10])
    critical_values : pd.DataFrame
        DataFrame containing critical values
    n_simulations : int
        Number of Monte Carlo replications
    """
    test_name: str
    sample_sizes: List[int]
    significance_levels: List[float]
    critical_values: pd.DataFrame
    n_simulations: int


def simulate_misspecification_critical_values(
    n_simulations: int = 10000,
    sample_sizes: List[int] = None,
    k_regressors: int = 3,
    m_test_vars: int = 2,
    truncation_j: int = 4,
    significance_levels: List[float] = None,
    seed: int = None
) -> CriticalValueTable:
    """
    Simulate critical values for the HAC-robust misspecification test.
    
    Under the null hypothesis (correct specification with possibly
    autocorrelated errors), we simulate the distribution of the test
    statistic and find empirical quantiles.
    
    Parameters
    ----------
    n_simulations : int
        Number of Monte Carlo replications
    sample_sizes : list of int
        Sample sizes to simulate
    k_regressors : int
        Number of regressors (excluding constant)
    m_test_vars : int
        Number of test variables
    truncation_j : int
        HAC truncation parameter
    significance_levels : list of float
        Significance levels for critical values
    seed : int, optional
        Random seed for reproducibility
        
    Returns
    -------
    CriticalValueTable
        Table of critical values
    """
    if sample_sizes is None:
        sample_sizes = [50, 100, 200, 500]
    if significance_levels is None:
        significance_levels = [0.01, 0.05, 0.10]
    if seed is not None:
        np.random.seed(seed)
    
    results = {}
    
    for T in sample_sizes:
        statistics = []
        
        for _ in range(n_simulations):
            # Generate data under null: y = Xβ + ε with i.i.d. N(0,1) errors
            X = np.random.randn(T, k_regressors)
            beta_true = np.ones(k_regressors + 1)  # Including constant
            X_full = np.hstack([np.ones((T, 1)), X])
            epsilon = np.random.randn(T)
            y = X_full @ beta_true + epsilon
            
            # OLS estimation
            XtX_inv = np.linalg.inv(X_full.T @ X_full)
            beta_hat = XtX_inv @ X_full.T @ y
            y_hat = X_full @ beta_hat
            residuals = y - y_hat
            
            # RESET test variables (powers of fitted values)
            Z = np.column_stack([y_hat ** 2, y_hat ** 3])[:, :m_test_vars]
            
            # Augmented regression: y = Wθ + ε where W = (X, Z)
            W = np.hstack([X_full, Z])
            k_aug = W.shape[1]
            
            WtW = W.T @ W
            WtW_inv = np.linalg.inv(WtW)
            theta_hat = WtW_inv @ W.T @ y
            resid_aug = y - W @ theta_hat
            
            # HAC covariance matrix (White-Domowitz)
            Sigma_j = np.zeros((T, T))
            for t in range(T):
                for s in range(max(0, t - truncation_j), min(T, t + truncation_j + 1)):
                    Sigma_j[t, s] = resid_aug[t] * resid_aug[s]
            
            meat = W.T @ Sigma_j @ W
            V_theta = WtW_inv @ meat @ WtW_inv
            
            # Selection matrix R = (0, I_m)
            R = np.hstack([np.zeros((m_test_vars, k_regressors + 1)), np.eye(m_test_vars)])
            alpha_hat = theta_hat[-m_test_vars:]
            
            # Test statistic
            RVR = R @ V_theta @ R.T
            try:
                RVR_inv = np.linalg.inv(RVR)
                chi2_stat = alpha_hat @ RVR_inv @ alpha_hat
                statistics.append(chi2_stat)
            except np.linalg.LinAlgError:
                continue
        
        # Compute empirical quantiles
        statistics = np.array(statistics)
        quantiles = {}
        for alpha in significance_levels:
            quantiles[f"{int((1-alpha)*100)}%"] = np.percentile(statistics, (1 - alpha) * 100)
        results[f"T={T}"] = quantiles
    
    # Create DataFrame
    df = pd.DataFrame(results).T
    df.index.name = "Sample Size"
    
    # Add asymptotic chi-squared critical values for comparison
    asymptotic = {}
    for alpha in significance_levels:
        asymptotic[f"{int((1-alpha)*100)}%"] = stats.chi2.ppf(1 - alpha, df=m_test_vars)
    results["Asymptotic χ²"] = asymptotic
    
    df = pd.DataFrame(results).T
    df.index.name = "Sample Size"
    
    return CriticalValueTable(
        test_name="Misspecification Test (HAC-robust χ²)",
        sample_sizes=sample_sizes,
        significance_levels=significance_levels,
        critical_values=df,
        n_simulations=n_simulations
    )


def simulate_ar_structure_critical_values(
    n_simulations: int = 10000,
    sample_sizes: List[int] = None,
    k_regressors: int = 3,
    p: int = 1,
    q: int = 4,
    significance_levels: List[float] = None,
    seed: int = None
) -> CriticalValueTable:
    """
    Simulate critical values for the AR structure F-test.
    
    Under the null hypothesis that AR(p) is adequate, we simulate
    the distribution of the F-statistic for testing against AR(p+q).
    
    Parameters
    ----------
    n_simulations : int
        Number of Monte Carlo replications
    sample_sizes : list of int
        Sample sizes to simulate
    k_regressors : int
        Number of regressors in original model
    p : int
        AR order for null hypothesis
    q : int
        Additional lags for alternative
    significance_levels : list of float
        Significance levels
    seed : int, optional
        Random seed
        
    Returns
    -------
    CriticalValueTable
        Table of critical values
    """
    if sample_sizes is None:
        sample_sizes = [50, 100, 200, 500]
    if significance_levels is None:
        significance_levels = [0.01, 0.05, 0.10]
    if seed is not None:
        np.random.seed(seed)
    
    results = {}
    max_lag = p + q
    
    for T in sample_sizes:
        if T <= max_lag + k_regressors + 5:
            continue
            
        statistics = []
        
        for _ in range(n_simulations):
            # Generate AR(p) errors under null
            epsilon = np.zeros(T)
            rho = 0.5  # AR(1) coefficient under H0
            for t in range(1, T):
                epsilon[t] = rho * epsilon[t-1] + np.random.randn()
            
            # Generate data
            X = np.random.randn(T, k_regressors)
            X_full = np.hstack([np.ones((T, 1)), X])
            beta_true = np.ones(k_regressors + 1)
            y = X_full @ beta_true + epsilon
            
            # OLS residuals
            XtX_inv = np.linalg.inv(X_full.T @ X_full)
            beta_hat = XtX_inv @ X_full.T @ y
            e = y - X_full @ beta_hat
            
            # Create lagged residuals for autoregression
            effective_T = T - max_lag
            e_t = e[max_lag:]
            X_lags = np.zeros((effective_T, max_lag))
            for lag in range(1, max_lag + 1):
                X_lags[:, lag - 1] = e[max_lag - lag:-lag if lag < T else None]
            
            # Unrestricted: AR(p+q)
            XtX_u = X_lags.T @ X_lags
            try:
                XtX_u_inv = np.linalg.inv(XtX_u)
            except np.linalg.LinAlgError:
                continue
            delta_u = XtX_u_inv @ X_lags.T @ e_t
            resid_u = e_t - X_lags @ delta_u
            ssr_u = resid_u @ resid_u
            
            # Restricted: AR(p)
            X_lags_r = X_lags[:, :p]
            XtX_r = X_lags_r.T @ X_lags_r
            try:
                XtX_r_inv = np.linalg.inv(XtX_r)
            except np.linalg.LinAlgError:
                continue
            delta_r = XtX_r_inv @ X_lags_r.T @ e_t
            resid_r = e_t - X_lags_r @ delta_r
            ssr_r = resid_r @ resid_r
            
            # F-statistic
            df2 = effective_T - max_lag
            if df2 > 0 and ssr_u > 0:
                f_stat = ((ssr_r - ssr_u) / q) / (ssr_u / df2)
                statistics.append(f_stat)
        
        # Compute empirical quantiles
        statistics = np.array(statistics)
        quantiles = {}
        for alpha in significance_levels:
            quantiles[f"{int((1-alpha)*100)}%"] = np.percentile(statistics, (1 - alpha) * 100)
        results[f"T={T}"] = quantiles
    
    # Add asymptotic F critical values
    if sample_sizes:
        T_large = max(sample_sizes)
        effective_T = T_large - max_lag
        df2_large = effective_T - max_lag
        asymptotic = {}
        for alpha in significance_levels:
            asymptotic[f"{int((1-alpha)*100)}%"] = stats.f.ppf(1 - alpha, q, df2_large)
        results[f"Asymptotic F({q},{df2_large})"] = asymptotic
    
    df = pd.DataFrame(results).T
    df.index.name = "Sample Size"
    
    return CriticalValueTable(
        test_name=f"AR Structure Test F({q}, T-{max_lag})",
        sample_sizes=sample_sizes,
        significance_levels=significance_levels,
        critical_values=df,
        n_simulations=n_simulations
    )


def simulate_critical_values(
    test_type: str = "all",
    n_simulations: int = 10000,
    sample_sizes: List[int] = None,
    significance_levels: List[float] = None,
    seed: int = None,
    **kwargs
) -> Dict[str, CriticalValueTable]:
    """
    Master function to simulate critical values for all tests.
    
    Parameters
    ----------
    test_type : str
        Type of test: "misspecification", "ar_structure", "all"
    n_simulations : int
        Number of Monte Carlo replications
    sample_sizes : list of int
        Sample sizes to simulate
    significance_levels : list of float
        Significance levels
    seed : int, optional
        Random seed for reproducibility
    **kwargs
        Additional arguments passed to specific simulation functions
        
    Returns
    -------
    dict
        Dictionary mapping test names to CriticalValueTable objects
    """
    if sample_sizes is None:
        sample_sizes = [50, 100, 200, 500]
    if significance_levels is None:
        significance_levels = [0.01, 0.05, 0.10]
    
    results = {}
    
    if test_type in ["misspecification", "all"]:
        results["misspecification"] = simulate_misspecification_critical_values(
            n_simulations=n_simulations,
            sample_sizes=sample_sizes,
            significance_levels=significance_levels,
            seed=seed,
            **{k: v for k, v in kwargs.items() if k in ['k_regressors', 'm_test_vars', 'truncation_j']}
        )
    
    if test_type in ["ar_structure", "all"]:
        results["ar_structure"] = simulate_ar_structure_critical_values(
            n_simulations=n_simulations,
            sample_sizes=sample_sizes,
            significance_levels=significance_levels,
            seed=seed,
            **{k: v for k, v in kwargs.items() if k in ['k_regressors', 'p', 'q']}
        )
    
    return results


def print_critical_value_tables(tables: Dict[str, CriticalValueTable]) -> None:
    """
    Print all critical value tables in a nicely formatted way.
    
    Parameters
    ----------
    tables : dict
        Dictionary of CriticalValueTable objects
    """
    from tabulate import tabulate
    
    for name, table in tables.items():
        print("=" * 70)
        print(f"CRITICAL VALUES: {table.test_name}")
        print(f"Monte Carlo simulations: {table.n_simulations:,}")
        print("=" * 70)
        print()
        print(tabulate(table.critical_values, headers='keys', tablefmt='fancy_grid', floatfmt='.4f'))
        print()
