"""
OLS Estimation Module

Provides ordinary least squares estimation for regression models.

Reference:
    Godfrey, L. G. (1987). Equation (2): y = Xβ + ε
"""

import numpy as np
from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class OLSResult:
    """Results from OLS estimation."""
    beta: np.ndarray          # Coefficient estimates
    residuals: np.ndarray     # OLS residuals
    fitted_values: np.ndarray # Fitted values
    ssr: float               # Sum of squared residuals
    tss: float               # Total sum of squares
    r_squared: float         # R-squared
    adj_r_squared: float     # Adjusted R-squared
    sigma_squared: float     # Estimated variance of errors
    std_errors: np.ndarray   # Standard errors of coefficients
    t_stats: np.ndarray      # t-statistics
    n: int                   # Number of observations
    k: int                   # Number of regressors


class OLSEstimator:
    """
    Ordinary Least Squares Estimator.
    
    Implements the standard OLS estimator for the regression model:
        y = Xβ + ε
    
    The OLS estimator minimizes the sum of squared residuals:
        b = argmin_β (y - Xβ)'(y - Xβ) = (X'X)^(-1)X'y
    
    Reference:
        Godfrey (1987), Equations (1)-(2)
    """
    
    def __init__(self, add_constant: bool = True):
        """
        Initialize OLS estimator.
        
        Parameters
        ----------
        add_constant : bool
            Whether to add a constant term to the regressors.
        """
        self.add_constant = add_constant
        self._result: Optional[OLSResult] = None
    
    def fit(self, y: np.ndarray, X: np.ndarray) -> OLSResult:
        """
        Fit OLS regression.
        
        Parameters
        ----------
        y : np.ndarray
            Dependent variable (T x 1)
        X : np.ndarray
            Regressor matrix (T x k)
            
        Returns
        -------
        OLSResult
            Complete OLS estimation results
        """
        y = np.asarray(y).flatten()
        X = np.asarray(X)
        
        if X.ndim == 1:
            X = X.reshape(-1, 1)
        
        # Add constant if requested
        if self.add_constant:
            ones = np.ones((X.shape[0], 1))
            X = np.hstack([ones, X])
        
        n, k = X.shape
        
        # OLS estimation: b = (X'X)^(-1)X'y
        XtX = X.T @ X
        XtX_inv = np.linalg.inv(XtX)
        Xty = X.T @ y
        beta = XtX_inv @ Xty
        
        # Fitted values and residuals
        fitted_values = X @ beta
        residuals = y - fitted_values
        
        # Sum of squared residuals
        ssr = residuals @ residuals
        
        # Total sum of squares
        y_mean = np.mean(y)
        tss = (y - y_mean) @ (y - y_mean)
        
        # R-squared and adjusted R-squared
        r_squared = 1 - ssr / tss if tss > 0 else 0.0
        adj_r_squared = 1 - (1 - r_squared) * (n - 1) / (n - k) if n > k else 0.0
        
        # Estimated variance of errors
        sigma_squared = ssr / (n - k) if n > k else ssr / n
        
        # Standard errors of coefficients
        var_beta = sigma_squared * XtX_inv
        std_errors = np.sqrt(np.diag(var_beta))
        
        # t-statistics
        t_stats = beta / std_errors
        
        self._result = OLSResult(
            beta=beta,
            residuals=residuals,
            fitted_values=fitted_values,
            ssr=ssr,
            tss=tss,
            r_squared=r_squared,
            adj_r_squared=adj_r_squared,
            sigma_squared=sigma_squared,
            std_errors=std_errors,
            t_stats=t_stats,
            n=n,
            k=k
        )
        
        # Store design matrix for later use
        self._X = X
        self._y = y
        
        return self._result
    
    @property
    def result(self) -> Optional[OLSResult]:
        """Get the most recent estimation result."""
        return self._result
    
    def get_design_matrix(self) -> np.ndarray:
        """Get the design matrix used in estimation."""
        if not hasattr(self, '_X'):
            raise ValueError("Model has not been fitted yet.")
        return self._X
    
    def get_XtX_inv(self) -> np.ndarray:
        """Get (X'X)^(-1) matrix."""
        if not hasattr(self, '_X'):
            raise ValueError("Model has not been fitted yet.")
        return np.linalg.inv(self._X.T @ self._X)


def ols_residuals(y: np.ndarray, X: np.ndarray, add_constant: bool = True) -> np.ndarray:
    """
    Convenience function to get OLS residuals.
    
    Parameters
    ----------
    y : np.ndarray
        Dependent variable
    X : np.ndarray
        Regressor matrix
    add_constant : bool
        Whether to add a constant term
        
    Returns
    -------
    np.ndarray
        OLS residuals
    """
    estimator = OLSEstimator(add_constant=add_constant)
    result = estimator.fit(y, X)
    return result.residuals
