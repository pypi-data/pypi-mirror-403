"""
Utility Functions for CUSUM Tests

Based on: Krämer, W., Ploberger, W., & Alt, R. (1988). 
"Testing for Structural Change in Dynamic Models"
Econometrica, Vol. 56, No. 6, pp. 1355-1369.

Author: Dr. Merwan Roudane
Email: merwanroudane920@gmail.com
"""

import numpy as np
from typing import Tuple, Optional, Union
import warnings


def check_stationarity(gamma: float, tol: float = 1e-10) -> bool:
    """
    Check if the AR(1) coefficient satisfies stationarity condition.
    
    The model y_t = γy_{t-1} + ... + u_t is stationary if |γ| < 1.
    
    Parameters
    ----------
    gamma : float
        Coefficient of lagged dependent variable
    tol : float
        Tolerance for boundary check
    
    Returns
    -------
    bool
        True if stationary
    """
    return np.abs(gamma) < 1 - tol


def prepare_data(y: np.ndarray, X: np.ndarray, 
                  include_lag: bool = True,
                  include_constant: bool = True) -> Tuple[np.ndarray, np.ndarray, Optional[np.ndarray]]:
    """
    Prepare data for CUSUM test.
    
    Parameters
    ----------
    y : np.ndarray
        Dependent variable (T x 1)
    X : np.ndarray
        Exogenous regressors (T x K)
    include_lag : bool
        Whether to include lagged dependent variable
    include_constant : bool
        Whether to include constant term
    
    Returns
    -------
    y_prepared : np.ndarray
        Adjusted dependent variable
    X_prepared : np.ndarray
        Adjusted regressor matrix
    y_lagged : np.ndarray or None
        Lagged dependent variable (if include_lag=True)
    """
    y = np.asarray(y).flatten()
    X = np.asarray(X)
    
    if X.ndim == 1:
        X = X.reshape(-1, 1)
    
    T = len(y)
    
    if include_lag:
        # Remove first observation for lagged model
        y_lagged = y[:-1]
        y_prepared = y[1:]
        X_prepared = X[1:, :]
    else:
        y_lagged = None
        y_prepared = y
        X_prepared = X
    
    if include_constant:
        ones = np.ones((X_prepared.shape[0], 1))
        X_prepared = np.column_stack([X_prepared, ones])
    
    return y_prepared, X_prepared, y_lagged


def validate_inputs(y: np.ndarray, X: np.ndarray, 
                    y_lagged: Optional[np.ndarray] = None) -> None:
    """
    Validate inputs for CUSUM test.
    
    Parameters
    ----------
    y : np.ndarray
        Dependent variable
    X : np.ndarray
        Regressor matrix
    y_lagged : np.ndarray, optional
        Lagged dependent variable
    
    Raises
    ------
    ValueError
        If inputs are invalid
    """
    y = np.asarray(y)
    X = np.asarray(X)
    
    if y.ndim != 1 and (y.ndim != 2 or y.shape[1] != 1):
        raise ValueError("y must be a 1-dimensional array")
    
    T = len(y)
    
    if X.ndim == 1:
        X = X.reshape(-1, 1)
    
    if X.shape[0] != T:
        raise ValueError(f"X has {X.shape[0]} rows but y has {T} elements")
    
    K = X.shape[1]
    
    if y_lagged is not None:
        y_lagged = np.asarray(y_lagged)
        if len(y_lagged) != T:
            raise ValueError(f"y_lagged has {len(y_lagged)} elements but y has {T}")
        K += 1  # Include lagged variable in regressor count
    
    # Check minimum sample size
    min_T = K + 3  # Need at least K+2 observations for recursive estimation
    if T < min_T:
        raise ValueError(f"Sample size T={T} is too small. Need at least {min_T} observations.")
    
    # Check for missing values
    if np.any(np.isnan(y)):
        raise ValueError("y contains missing values")
    
    if np.any(np.isnan(X)):
        raise ValueError("X contains missing values")
    
    if y_lagged is not None and np.any(np.isnan(y_lagged)):
        raise ValueError("y_lagged contains missing values")


def estimate_ar1_coefficient(y: np.ndarray) -> float:
    """
    Estimate AR(1) coefficient γ from time series.
    
    Uses OLS: y_t = γ*y_{t-1} + ε_t
    
    Parameters
    ----------
    y : np.ndarray
        Time series
    
    Returns
    -------
    float
        Estimated γ
    """
    y = np.asarray(y).flatten()
    y_t = y[1:]
    y_lag = y[:-1]
    
    # OLS estimate
    gamma = np.sum(y_t * y_lag) / np.sum(y_lag**2)
    
    return gamma


def ols_regression(y: np.ndarray, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray, float]:
    """
    Perform OLS regression.
    
    Parameters
    ----------
    y : np.ndarray
        Dependent variable
    X : np.ndarray
        Regressor matrix
    
    Returns
    -------
    beta : np.ndarray
        Coefficient estimates
    residuals : np.ndarray
        OLS residuals
    sigma : float
        Estimated standard error
    """
    y = np.asarray(y).flatten()
    X = np.asarray(X)
    
    if X.ndim == 1:
        X = X.reshape(-1, 1)
    
    # OLS estimate
    beta = np.linalg.lstsq(X, y, rcond=None)[0]
    
    # Residuals
    residuals = y - X @ beta
    
    # Standard error
    T, K = X.shape
    sigma = np.sqrt(np.sum(residuals**2) / (T - K))
    
    return beta, residuals, sigma


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
        Durbin-Watson statistic
    """
    residuals = np.asarray(residuals).flatten()
    diff_residuals = np.diff(residuals)
    
    dw = np.sum(diff_residuals**2) / np.sum(residuals**2)
    
    return dw


def breusch_godfrey_test(y: np.ndarray, X: np.ndarray, 
                          order: int = 1) -> Tuple[float, float]:
    """
    Breusch-Godfrey test for serial correlation.
    
    Parameters
    ----------
    y : np.ndarray
        Dependent variable
    X : np.ndarray
        Regressor matrix
    order : int
        Number of lags to test
    
    Returns
    -------
    statistic : float
        LM test statistic
    p_value : float
        P-value
    """
    from scipy import stats
    
    y = np.asarray(y).flatten()
    X = np.asarray(X)
    
    if X.ndim == 1:
        X = X.reshape(-1, 1)
    
    T, K = X.shape
    
    # Get OLS residuals
    _, residuals, _ = ols_regression(y, X)
    
    # Auxiliary regression
    lagged_resids = np.column_stack([
        np.roll(residuals, i)[order:] for i in range(1, order + 1)
    ])
    
    X_aux = np.column_stack([X[order:], lagged_resids])
    y_aux = residuals[order:]
    
    # R² from auxiliary regression
    _, resid_aux, _ = ols_regression(y_aux, X_aux)
    
    tss = np.sum((y_aux - np.mean(y_aux))**2)
    rss = np.sum(resid_aux**2)
    r_squared = 1 - rss / tss
    
    # LM statistic
    lm_stat = (T - order) * r_squared
    
    # P-value from chi-squared distribution
    p_value = 1 - stats.chi2.cdf(lm_stat, order)
    
    return lm_stat, p_value


def simulate_ar1(T: int, gamma: float, sigma: float = 1.0,
                  y0: float = 0.0, seed: Optional[int] = None) -> np.ndarray:
    """
    Simulate AR(1) process.
    
    y_t = γ*y_{t-1} + ε_t, ε_t ~ N(0, σ²)
    
    Parameters
    ----------
    T : int
        Number of observations
    gamma : float
        AR coefficient
    sigma : float
        Innovation standard deviation
    y0 : float
        Initial value
    seed : int, optional
        Random seed
    
    Returns
    -------
    np.ndarray
        Simulated series
    """
    if seed is not None:
        np.random.seed(seed)
    
    y = np.zeros(T)
    eps = np.random.normal(0, sigma, T)
    
    y[0] = y0 + eps[0]
    for t in range(1, T):
        y[t] = gamma * y[t-1] + eps[t]
    
    return y


def compute_information_criteria(y: np.ndarray, X: np.ndarray) -> dict:
    """
    Compute AIC and BIC for model selection.
    
    Parameters
    ----------
    y : np.ndarray
        Dependent variable
    X : np.ndarray
        Regressor matrix
    
    Returns
    -------
    dict
        Dictionary with AIC, BIC, and log-likelihood
    """
    y = np.asarray(y).flatten()
    X = np.asarray(X)
    
    if X.ndim == 1:
        X = X.reshape(-1, 1)
    
    T, K = X.shape
    
    # Get residuals
    _, residuals, sigma = ols_regression(y, X)
    
    # Log-likelihood (assuming normality)
    ll = -T/2 * (1 + np.log(2*np.pi) + np.log(np.sum(residuals**2)/T))
    
    # Information criteria
    aic = -2 * ll + 2 * K
    bic = -2 * ll + K * np.log(T)
    
    return {
        'log_likelihood': ll,
        'aic': aic,
        'bic': bic,
        'n_params': K,
        'n_obs': T
    }


def check_multicollinearity(X: np.ndarray, threshold: float = 10) -> dict:
    """
    Check for multicollinearity using VIF.
    
    Parameters
    ----------
    X : np.ndarray
        Regressor matrix
    threshold : float
        VIF threshold (default: 10)
    
    Returns
    -------
    dict
        VIF values and warning flags
    """
    X = np.asarray(X)
    
    if X.ndim == 1:
        X = X.reshape(-1, 1)
    
    K = X.shape[1]
    vif = np.zeros(K)
    
    for j in range(K):
        # Regress x_j on other regressors
        x_j = X[:, j]
        X_other = np.delete(X, j, axis=1)
        
        if X_other.shape[1] > 0:
            _, residuals, _ = ols_regression(x_j, X_other)
            
            tss = np.sum((x_j - np.mean(x_j))**2)
            rss = np.sum(residuals**2)
            r_squared = 1 - rss / tss
            
            if r_squared < 1:
                vif[j] = 1 / (1 - r_squared)
            else:
                vif[j] = np.inf
        else:
            vif[j] = 1
    
    return {
        'vif': vif,
        'warnings': [i for i, v in enumerate(vif) if v > threshold],
        'threshold': threshold
    }
