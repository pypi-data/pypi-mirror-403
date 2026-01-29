"""
HAC (Heteroskedasticity and Autocorrelation Consistent) Covariance Estimation

Implements the White-Domowitz (1984) HAC estimator as described in Godfrey (1987).

Reference:
    Godfrey, L. G. (1987). Equation (9):
        V(θ̂) = (W'W)^(-1) (W'Σ̂_j W) (W'W)^(-1)
    
    Where Σ̂_j has elements:
        σ̂_ts = ε̂_t ε̂_s  if |t - s| ≤ j
        σ̂_ts = 0         otherwise
    
    White, H., & Domowitz, I. (1984). "Nonlinear Regression with Dependent 
    Observations." Econometrica, 52, 143-161.
"""

import numpy as np
from dataclasses import dataclass
from typing import Optional


@dataclass
class HACResult:
    """Results from HAC covariance estimation."""
    covariance_matrix: np.ndarray  # HAC covariance matrix
    robust_std_errors: np.ndarray  # HAC robust standard errors
    truncation_j: int              # Truncation parameter used
    meat_matrix: np.ndarray        # The "meat" W'Σ̂_j W
    bread_matrix: np.ndarray       # The "bread" (W'W)^(-1)


class HACEstimator:
    """
    White-Domowitz HAC Covariance Matrix Estimator.
    
    This estimator is robust to both heteroskedasticity and autocorrelation
    of unknown form, using a truncation parameter j to limit the bandwidth.
    
    The HAC estimator replaces Σ with Σ̂_j where:
        Σ̂_j[t,s] = ε̂_t × ε̂_s  if |t - s| ≤ j
        Σ̂_j[t,s] = 0           otherwise
    
    Reference:
        Godfrey (1987), p. 131: "White and Domowitz (1984) who suggest that
        Σ in (9) be replaced by Σ̂_j, where Σ̂_j has elements equal to ε̂_t ε̂_s
        if |t - s| ≤ j and zero otherwise."
        
    Note from paper:
        "It would seem sensible to take account of seasonality in the data
        when choosing the value of the truncation parameter j, e.g., use
        j ≥ 4 when the observations are quarterly."
    """
    
    def __init__(self, truncation_j: Optional[int] = None, auto_bandwidth: bool = False):
        """
        Initialize HAC estimator.
        
        Parameters
        ----------
        truncation_j : int, optional
            Truncation parameter. If None, defaults to floor(T^(1/3)).
            Paper recommends j ≥ 4 for quarterly data.
        auto_bandwidth : bool
            If True, use automatic bandwidth selection.
        """
        self.truncation_j = truncation_j
        self.auto_bandwidth = auto_bandwidth
        self._result: Optional[HACResult] = None
    
    def _compute_default_bandwidth(self, T: int) -> int:
        """
        Compute default bandwidth using Newey-West rule of thumb.
        
        Parameters
        ----------
        T : int
            Sample size
            
        Returns
        -------
        int
            Default bandwidth
        """
        return int(np.floor(T ** (1/3)))
    
    def _compute_sigma_j(self, residuals: np.ndarray, j: int) -> np.ndarray:
        """
        Compute the truncated covariance matrix Σ̂_j.
        
        Implements Godfrey (1987) specification:
            Σ̂_j[t,s] = ε̂_t × ε̂_s  if |t - s| ≤ j
            Σ̂_j[t,s] = 0           otherwise
        
        Parameters
        ----------
        residuals : np.ndarray
            OLS residuals (T x 1)
        j : int
            Truncation parameter
            
        Returns
        -------
        np.ndarray
            T x T truncated covariance matrix
        """
        T = len(residuals)
        sigma_j = np.zeros((T, T))
        
        for t in range(T):
            for s in range(T):
                if abs(t - s) <= j:
                    sigma_j[t, s] = residuals[t] * residuals[s]
        
        return sigma_j
    
    def estimate(self, X: np.ndarray, residuals: np.ndarray, 
                 truncation_j: Optional[int] = None) -> HACResult:
        """
        Estimate HAC covariance matrix.
        
        Implements Equation (9) from Godfrey (1987):
            V(θ̂) = (W'W)^(-1) (W'Σ̂_j W) (W'W)^(-1)
        
        Parameters
        ----------
        X : np.ndarray
            Regressor matrix W = (X, Z) of dimension T x (k+m)
        residuals : np.ndarray
            OLS residuals ε̂
        truncation_j : int, optional
            Override for truncation parameter
            
        Returns
        -------
        HACResult
            Complete HAC estimation results
        """
        X = np.asarray(X)
        residuals = np.asarray(residuals).flatten()
        
        T, k = X.shape
        
        # Determine truncation parameter
        if truncation_j is not None:
            j = truncation_j
        elif self.truncation_j is not None:
            j = self.truncation_j
        else:
            j = self._compute_default_bandwidth(T)
        
        # Compute (W'W)^(-1)
        WtW = X.T @ X
        WtW_inv = np.linalg.inv(WtW)
        
        # Compute Σ̂_j (the truncated covariance matrix)
        sigma_j = self._compute_sigma_j(residuals, j)
        
        # Compute the "meat": W'Σ̂_j W
        meat = X.T @ sigma_j @ X
        
        # Compute HAC covariance matrix: (W'W)^(-1) (W'Σ̂_j W) (W'W)^(-1)
        hac_cov = WtW_inv @ meat @ WtW_inv
        
        # Extract robust standard errors
        robust_std_errors = np.sqrt(np.diag(hac_cov))
        
        self._result = HACResult(
            covariance_matrix=hac_cov,
            robust_std_errors=robust_std_errors,
            truncation_j=j,
            meat_matrix=meat,
            bread_matrix=WtW_inv
        )
        
        return self._result
    
    @property
    def result(self) -> Optional[HACResult]:
        """Get the most recent estimation result."""
        return self._result


def compute_hac_covariance(X: np.ndarray, residuals: np.ndarray, 
                           truncation_j: Optional[int] = None) -> np.ndarray:
    """
    Convenience function to compute HAC covariance matrix.
    
    Parameters
    ----------
    X : np.ndarray
        Regressor matrix
    residuals : np.ndarray
        OLS residuals
    truncation_j : int, optional
        Truncation parameter (default: floor(T^(1/3)))
        
    Returns
    -------
    np.ndarray
        HAC covariance matrix
    """
    estimator = HACEstimator(truncation_j=truncation_j)
    result = estimator.estimate(X, residuals)
    return result.covariance_matrix


def compute_newey_west_covariance(X: np.ndarray, residuals: np.ndarray,
                                   max_lag: Optional[int] = None) -> np.ndarray:
    """
    Alternative: Newey-West (1987) HAC estimator with Bartlett kernel.
    
    This uses declining weights for higher lags (Bartlett kernel):
        weight(l) = 1 - l/(max_lag + 1)
    
    Parameters
    ----------
    X : np.ndarray
        Regressor matrix
    residuals : np.ndarray
        OLS residuals  
    max_lag : int, optional
        Maximum lag for autocorrelation. Default: floor(T^(1/3))
        
    Returns
    -------
    np.ndarray
        Newey-West HAC covariance matrix
    """
    X = np.asarray(X)
    residuals = np.asarray(residuals).flatten()
    
    T, k = X.shape
    
    if max_lag is None:
        max_lag = int(np.floor(T ** (1/3)))
    
    # Compute (X'X)^(-1)
    XtX_inv = np.linalg.inv(X.T @ X)
    
    # Compute the meat with Bartlett weights
    # S_0 = Σ_t ε̂_t² x_t x_t'
    S = np.zeros((k, k))
    
    # Lag 0 component
    for t in range(T):
        xt = X[t].reshape(-1, 1)
        S += (residuals[t] ** 2) * (xt @ xt.T)
    
    # Higher lag components with Bartlett weights
    for lag in range(1, max_lag + 1):
        weight = 1 - lag / (max_lag + 1)
        for t in range(lag, T):
            xt = X[t].reshape(-1, 1)
            xt_lag = X[t - lag].reshape(-1, 1)
            cross_term = residuals[t] * residuals[t - lag] * (xt @ xt_lag.T + xt_lag @ xt.T)
            S += weight * cross_term
    
    # HAC covariance matrix
    nw_cov = XtX_inv @ S @ XtX_inv
    
    return nw_cov
