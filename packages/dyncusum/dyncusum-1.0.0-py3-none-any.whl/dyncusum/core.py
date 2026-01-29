"""
Core CUSUM Test Implementation for Dynamic Models

Based on: Krämer, W., Ploberger, W., & Alt, R. (1988). 
"Testing for Structural Change in Dynamic Models"
Econometrica, Vol. 56, No. 6, pp. 1355-1369.

This module implements:
1. Dynamic CUSUM test (straightforward CUSUM for dynamic models)
2. Dufour test (modified procedure from Dufour, 1982)

Author: Dr. Merwan Roudane
Email: merwanroudane920@gmail.com
"""

import numpy as np
from scipy import stats
from typing import Tuple, Optional, Dict, Any, Union
from dataclasses import dataclass
import warnings


@dataclass
class CUSUMResult:
    """
    Container for CUSUM test results.
    
    Attributes
    ----------
    statistic : float
        The CUSUM test statistic S (equation 9 in the paper)
    critical_value : float
        Critical value at the specified significance level
    p_value : float
        Approximate p-value (computed via simulation)
    reject_null : bool
        True if null hypothesis of parameter constancy is rejected
    significance_level : float
        Significance level used for the test
    W_process : np.ndarray
        The standardized CUSUM process W^(r) (equation 10)
    recursive_residuals : np.ndarray
        The recursive residuals w_r (equation 7)
    critical_lines_upper : np.ndarray
        Upper critical boundary
    critical_lines_lower : np.ndarray
        Lower critical boundary
    sigma_hat : float
        Estimated disturbance standard deviation
    test_type : str
        Type of test performed ('dynamic_cusum' or 'dufour')
    n_obs : int
        Number of observations
    n_regressors : int
        Number of regressors (including lagged dependent variable)
    """
    statistic: float
    critical_value: float
    p_value: float
    reject_null: bool
    significance_level: float
    W_process: np.ndarray
    recursive_residuals: np.ndarray
    critical_lines_upper: np.ndarray
    critical_lines_lower: np.ndarray
    sigma_hat: float
    test_type: str
    n_obs: int
    n_regressors: int


def compute_recursive_residuals(y: np.ndarray, Z: np.ndarray, 
                                 start_index: Optional[int] = None) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute recursive residuals w_r as defined in equation (7) of the paper.
    
    The recursive residual for observation r is:
        w_r = (y_r - z'_r * δ^(r-1)) / f_r
    
    where:
        δ^(r-1) is the OLS estimate from the first r-1 observations
        f_r = (1 + z'_r * (Z^(r-1)'Z^(r-1))^(-1) * z_r)^(1/2)
    
    Parameters
    ----------
    y : np.ndarray
        Dependent variable vector (T x 1)
    Z : np.ndarray
        Regressor matrix (T x (K+1)) including lagged dependent variable
    start_index : int, optional
        Index to start computing recursive residuals. 
        Default is K+2 (minimum needed for OLS estimation).
    
    Returns
    -------
    w : np.ndarray
        Recursive residuals
    f : np.ndarray
        Standardization factors f_r
        
    References
    ----------
    Equations (7) and (8) in Krämer, Ploberger, and Alt (1988)
    """
    T, K_plus_1 = Z.shape
    K = K_plus_1 - 1  # Number of regressors excluding constant/lagged dep var
    
    if start_index is None:
        start_index = K_plus_1 + 1  # K + 2 in the paper's notation (1-indexed)
    
    # Arrays to store results
    n_residuals = T - start_index + 1
    w = np.zeros(n_residuals)
    f = np.zeros(n_residuals)
    
    for i, r in enumerate(range(start_index - 1, T)):
        # Use observations 0 to r-1 (indices 0 to r-1, which is r observations)
        Z_prev = Z[:r, :]  # Z^(r-1) in paper notation
        y_prev = y[:r]
        
        # Current observation
        z_r = Z[r, :]
        y_r = y[r]
        
        # OLS estimate from first r observations
        # δ^(r-1) = (Z^(r-1)'Z^(r-1))^(-1) Z^(r-1)'y^(r-1)
        try:
            ZtZ_inv = np.linalg.inv(Z_prev.T @ Z_prev)
            delta_prev = ZtZ_inv @ Z_prev.T @ y_prev
            
            # Compute f_r = (1 + z'_r * (Z^(r-1)'Z^(r-1))^(-1) * z_r)^(1/2)
            # Equation (8)
            f_r = np.sqrt(1 + z_r @ ZtZ_inv @ z_r)
            
            # Compute recursive residual w_r = (y_r - z'_r * δ^(r-1)) / f_r
            # Equation (7)
            w_r = (y_r - z_r @ delta_prev) / f_r
            
            w[i] = w_r
            f[i] = f_r
            
        except np.linalg.LinAlgError:
            warnings.warn(f"Singular matrix at observation {r}. Setting residual to NaN.")
            w[i] = np.nan
            f[i] = np.nan
    
    return w, f


def estimate_sigma_harvey(w: np.ndarray) -> float:
    """
    Estimate disturbance standard deviation using Harvey's (1975) method.
    
    Unlike the OLS-based estimate, this uses the mean of recursive residuals
    which is not necessarily zero under structural change.
    
    σ̂ = (1/(T-K-2) * Σ(w_r - w̄)²)^(1/2)
    
    Parameters
    ----------
    w : np.ndarray
        Recursive residuals
    
    Returns
    -------
    float
        Estimated standard deviation
        
    References
    ----------
    Equation (13) in Krämer, Ploberger, and Alt (1988)
    Harvey, A. (1975), comment on Brown, Durbin, and Evans paper
    """
    w_clean = w[~np.isnan(w)]
    n = len(w_clean)
    if n <= 1:
        return np.nan
    
    w_bar = np.mean(w_clean)
    sigma_hat = np.sqrt(np.sum((w_clean - w_bar)**2) / (n - 1))
    
    return sigma_hat


def estimate_sigma_ols(y: np.ndarray, Z: np.ndarray) -> float:
    """
    Estimate disturbance standard deviation using OLS-based formula.
    
    σ̂ = ((y - Zδ̂)'(y - Zδ̂)/(T - K - 1))^(1/2)
    
    Parameters
    ----------
    y : np.ndarray
        Dependent variable
    Z : np.ndarray
        Regressor matrix
    
    Returns
    -------
    float
        Estimated standard deviation
    """
    T, K_plus_1 = Z.shape
    
    # OLS estimate
    delta_hat = np.linalg.lstsq(Z, y, rcond=None)[0]
    
    # Residuals
    residuals = y - Z @ delta_hat
    
    # Standard deviation estimate
    sigma_hat = np.sqrt(np.sum(residuals**2) / (T - K_plus_1))
    
    return sigma_hat


def compute_cusum_process(w: np.ndarray, sigma_hat: float, 
                           T: int, K: int) -> np.ndarray:
    """
    Compute the standardized CUSUM process W^(r).
    
    W^(r) = (1/σ̂) * Σ_{t=K+2}^{r} w_t
    
    Parameters
    ----------
    w : np.ndarray
        Recursive residuals
    sigma_hat : float
        Estimated standard deviation
    T : int
        Total number of observations
    K : int
        Number of regressors (excluding lagged dependent variable)
    
    Returns
    -------
    np.ndarray
        Standardized CUSUM process
        
    References
    ----------
    Equation (10) in Krämer, Ploberger, and Alt (1988)
    """
    # Cumulative sum of recursive residuals
    W = np.cumsum(w) / sigma_hat
    
    return W


def compute_test_statistic(W: np.ndarray, T: int, K: int) -> float:
    """
    Compute the CUSUM test statistic S.
    
    S = max_{K+1 < r ≤ T} |W^(r)/√(T-K-1)| / (1 + 2*(r-K-1)/(T-K-1))
    
    Parameters
    ----------
    W : np.ndarray
        Standardized CUSUM process
    T : int
        Total number of observations
    K : int
        Number of regressors (excluding lagged dependent variable)
    
    Returns
    -------
    float
        Test statistic S
        
    References
    ----------
    Equation (9) in Krämer, Ploberger, and Alt (1988)
    """
    n = len(W)
    sqrt_T_K_1 = np.sqrt(T - K - 1)
    
    S_values = np.zeros(n)
    for i in range(n):
        r = K + 2 + i  # r ranges from K+2 to T
        numerator = np.abs(W[i]) / sqrt_T_K_1
        denominator = 1 + 2 * (r - K - 1) / (T - K - 1)
        S_values[i] = numerator / denominator
    
    return np.max(S_values)


def compute_critical_boundaries(T: int, K: int, 
                                 critical_value: float) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute the critical boundary lines for the CUSUM plot.
    
    Upper boundary: a*√(T-K-1) + 2a*(r-K-1)/√(T-K-1)
    Lower boundary: -a*√(T-K-1) - 2a*(r-K-1)/√(T-K-1)
    
    Parameters
    ----------
    T : int
        Total number of observations
    K : int
        Number of regressors
    critical_value : float
        Critical value 'a' from Brownian motion theory
    
    Returns
    -------
    upper : np.ndarray
        Upper critical boundary
    lower : np.ndarray
        Lower critical boundary
    """
    r_values = np.arange(K + 2, T + 1)
    sqrt_T_K_1 = np.sqrt(T - K - 1)
    
    upper = critical_value * sqrt_T_K_1 + 2 * critical_value * (r_values - K - 1) / sqrt_T_K_1
    lower = -critical_value * sqrt_T_K_1 - 2 * critical_value * (r_values - K - 1) / sqrt_T_K_1
    
    return upper, lower


def dynamic_cusum_test(y: np.ndarray, X: np.ndarray, 
                       y_lagged: Optional[np.ndarray] = None,
                       significance_level: float = 0.05,
                       sigma_method: str = 'harvey',
                       n_simulations: int = 10000) -> CUSUMResult:
    """
    Perform the Dynamic CUSUM test for structural change.
    
    This is the straightforward CUSUM test applied to dynamic models
    with lagged dependent variables among the regressors.
    
    Model: y_t = γ*y_{t-1} + β_1*x_{t1} + ... + β_K*x_{tK} + u_t
    
    Parameters
    ----------
    y : np.ndarray
        Dependent variable vector (T x 1)
    X : np.ndarray
        Exogenous regressors matrix (T x K), can include constant
    y_lagged : np.ndarray, optional
        Lagged dependent variable. If None, assumes no dynamic component.
    significance_level : float
        Significance level for the test (default: 0.05)
    sigma_method : str
        Method for estimating sigma: 'harvey' (recommended) or 'ols'
    n_simulations : int
        Number of simulations for critical value computation
    
    Returns
    -------
    CUSUMResult
        Object containing test results
        
    References
    ----------
    Theorem 1 in Krämer, Ploberger, and Alt (1988)
    
    Examples
    --------
    >>> import numpy as np
    >>> np.random.seed(42)
    >>> T = 100
    >>> y = np.zeros(T)
    >>> u = np.random.normal(0, 1, T)
    >>> for t in range(1, T):
    ...     y[t] = 0.5 * y[t-1] + u[t]
    >>> X = np.ones((T-1, 1))  # constant term
    >>> y_lagged = y[:-1]
    >>> y_current = y[1:]
    >>> result = dynamic_cusum_test(y_current, X, y_lagged)
    >>> print(f"Test statistic: {result.statistic:.4f}")
    """
    y = np.asarray(y).flatten()
    X = np.asarray(X)
    
    if X.ndim == 1:
        X = X.reshape(-1, 1)
    
    T = len(y)
    
    # Construct regressor matrix Z
    if y_lagged is not None:
        y_lagged = np.asarray(y_lagged).flatten()
        Z = np.column_stack([y_lagged, X])
    else:
        Z = X
    
    K_plus_1 = Z.shape[1]  # K + 1 in paper notation (includes lagged y or constant)
    K = K_plus_1 - 1
    
    # Verify dimensions
    if Z.shape[0] != T:
        raise ValueError(f"Dimension mismatch: y has {T} obs, Z has {Z.shape[0]} obs")
    
    # Compute recursive residuals (starting from K+2)
    w, f = compute_recursive_residuals(y, Z, start_index=K_plus_1 + 1)
    
    # Estimate sigma
    if sigma_method == 'harvey':
        sigma_hat = estimate_sigma_harvey(w)
    elif sigma_method == 'ols':
        sigma_hat = estimate_sigma_ols(y, Z)
    else:
        raise ValueError(f"Unknown sigma_method: {sigma_method}")
    
    # Compute CUSUM process
    W = compute_cusum_process(w, sigma_hat, T, K)
    
    # Compute test statistic
    S = compute_test_statistic(W, T, K)
    
    # Get critical value
    critical_value = get_critical_value(significance_level, T, K, n_simulations)
    
    # Compute p-value via simulation
    p_value = compute_p_value(S, T, K, n_simulations)
    
    # Compute critical boundaries for plotting
    upper, lower = compute_critical_boundaries(T, K, critical_value)
    
    return CUSUMResult(
        statistic=S,
        critical_value=critical_value,
        p_value=p_value,
        reject_null=S > critical_value,
        significance_level=significance_level,
        W_process=W,
        recursive_residuals=w,
        critical_lines_upper=upper,
        critical_lines_lower=lower,
        sigma_hat=sigma_hat,
        test_type='dynamic_cusum',
        n_obs=T,
        n_regressors=K_plus_1
    )


def dufour_test(y: np.ndarray, X: np.ndarray, 
                y_lagged: np.ndarray,
                significance_level: float = 0.05,
                sigma_method: str = 'harvey',
                n_simulations: int = 10000) -> CUSUMResult:
    """
    Perform the Dufour (1982) modified CUSUM test.
    
    This test first estimates γ from the full sample, transforms
    the model to remove dynamics, then applies the standard CUSUM test.
    
    Transformation: Δy_t - γ̂*y_{t-1} = β_1*x_{t1} + ... + β_K*x_{tK} + u_t
    
    Parameters
    ----------
    y : np.ndarray
        Dependent variable vector (T x 1)
    X : np.ndarray
        Exogenous regressors matrix (T x K), can include constant
    y_lagged : np.ndarray
        Lagged dependent variable (required for Dufour test)
    significance_level : float
        Significance level for the test (default: 0.05)
    sigma_method : str
        Method for estimating sigma: 'harvey' (recommended) or 'ols'
    n_simulations : int
        Number of simulations for critical value computation
    
    Returns
    -------
    CUSUMResult
        Object containing test results
        
    References
    ----------
    Dufour, J. M. (1982). "Recursive Stability Analysis of Linear 
    Regression Relationships," Journal of Econometrics, 19, 31-76.
    
    Notes
    -----
    As noted in Krämer, Ploberger, and Alt (1988), this test is extremely
    nonsimilar, with true size depending crucially on the nuisance parameter γ.
    The Dynamic CUSUM test is generally preferred.
    """
    y = np.asarray(y).flatten()
    X = np.asarray(X)
    y_lagged = np.asarray(y_lagged).flatten()
    
    if X.ndim == 1:
        X = X.reshape(-1, 1)
    
    T = len(y)
    K = X.shape[1]
    
    # Construct full regressor matrix for γ estimation
    Z_full = np.column_stack([y_lagged, X])
    
    # Estimate γ from full sample using OLS
    delta_hat = np.linalg.lstsq(Z_full, y, rcond=None)[0]
    gamma_hat = delta_hat[0]
    
    # Transform dependent variable: Δy_t = y_t - γ̂*y_{t-1}
    y_transformed = y - gamma_hat * y_lagged
    
    # Now apply standard CUSUM test to transformed model
    # Model: y_transformed = X*β + u
    
    # Compute recursive residuals for transformed model
    w, f = compute_recursive_residuals(y_transformed, X, start_index=K + 1)
    
    # Estimate sigma
    if sigma_method == 'harvey':
        sigma_hat = estimate_sigma_harvey(w)
    elif sigma_method == 'ols':
        sigma_hat = estimate_sigma_ols(y_transformed, X)
    else:
        raise ValueError(f"Unknown sigma_method: {sigma_method}")
    
    # Compute CUSUM process (note: K here is number of X regressors)
    W = compute_cusum_process(w, sigma_hat, T, K - 1)
    
    # Compute test statistic
    S = compute_test_statistic(W, T, K - 1)
    
    # Get critical value (using K-1 because we've removed the lagged y)
    critical_value = get_critical_value(significance_level, T, K - 1, n_simulations)
    
    # Compute p-value
    p_value = compute_p_value(S, T, K - 1, n_simulations)
    
    # Compute critical boundaries
    upper, lower = compute_critical_boundaries(T, K - 1, critical_value)
    
    return CUSUMResult(
        statistic=S,
        critical_value=critical_value,
        p_value=p_value,
        reject_null=S > critical_value,
        significance_level=significance_level,
        W_process=W,
        recursive_residuals=w,
        critical_lines_upper=upper,
        critical_lines_lower=lower,
        sigma_hat=sigma_hat,
        test_type='dufour',
        n_obs=T,
        n_regressors=K
    )


def get_critical_value(significance_level: float, T: int, K: int,
                       n_simulations: int = 10000) -> float:
    """
    Get critical value for the CUSUM test.
    
    The critical values are determined from the distribution of:
    max_{0<z≤1} |W̃(z)|/(1+2z)
    
    where W̃(z) is a standard Brownian motion.
    
    Parameters
    ----------
    significance_level : float
        Significance level (e.g., 0.05, 0.10)
    T : int
        Sample size
    K : int
        Number of regressors
    n_simulations : int
        Number of Monte Carlo simulations
    
    Returns
    -------
    float
        Critical value 'a'
        
    References
    ----------
    BDE (Brown, Durbin, Evans, 1975), p. 154
    Equation (12) in Krämer, Ploberger, and Alt (1988)
    """
    # Standard critical values from BDE (1975) for common significance levels
    # These are asymptotic values based on Brownian motion
    standard_critical_values = {
        0.01: 1.143,
        0.05: 0.948,
        0.10: 0.850
    }
    
    # If we have a standard level, use tabulated value
    if significance_level in standard_critical_values:
        return standard_critical_values[significance_level]
    
    # Otherwise, compute via simulation
    return _simulate_critical_value(significance_level, n_simulations)


def _simulate_critical_value(significance_level: float, 
                              n_simulations: int = 10000,
                              n_points: int = 1000) -> float:
    """
    Simulate critical value using Brownian motion.
    
    Computes the (1-α) quantile of max_{0<z≤1} |W(z)|/(1+2z)
    where W(z) is a standard Brownian motion.
    """
    np.random.seed(42)  # For reproducibility
    
    max_stats = np.zeros(n_simulations)
    z_values = np.linspace(0.001, 1, n_points)
    
    for sim in range(n_simulations):
        # Simulate standard Brownian motion
        increments = np.random.normal(0, np.sqrt(1/n_points), n_points)
        W = np.cumsum(increments)
        
        # Compute statistic at each point
        stats = np.abs(W) / (1 + 2 * z_values)
        max_stats[sim] = np.max(stats)
    
    # Return (1 - significance_level) quantile
    return np.percentile(max_stats, (1 - significance_level) * 100)


def compute_p_value(statistic: float, T: int, K: int,
                    n_simulations: int = 10000) -> float:
    """
    Compute p-value for the CUSUM test statistic via simulation.
    
    Parameters
    ----------
    statistic : float
        Observed test statistic
    T : int
        Sample size
    K : int
        Number of regressors
    n_simulations : int
        Number of Monte Carlo simulations
    
    Returns
    -------
    float
        Approximate p-value
    """
    np.random.seed(42)
    
    n_points = T - K - 1
    if n_points < 10:
        n_points = 100
    
    max_stats = np.zeros(n_simulations)
    z_values = np.linspace(0.001, 1, n_points)
    
    for sim in range(n_simulations):
        # Simulate standard Brownian motion
        increments = np.random.normal(0, np.sqrt(1/n_points), n_points)
        W = np.cumsum(increments)
        
        # Compute statistic
        stats = np.abs(W) / (1 + 2 * z_values)
        max_stats[sim] = np.max(stats)
    
    # P-value is proportion of simulated statistics >= observed
    p_value = np.mean(max_stats >= statistic)
    
    return p_value


def cusum_ols(y: np.ndarray, X: np.ndarray,
              significance_level: float = 0.05,
              n_simulations: int = 10000) -> CUSUMResult:
    """
    Perform the standard CUSUM-OLS test (static model without lagged y).
    
    This is the original BDE (1975) test for models without dynamics.
    
    Parameters
    ----------
    y : np.ndarray
        Dependent variable
    X : np.ndarray
        Regressor matrix (can include constant)
    significance_level : float
        Significance level
    n_simulations : int
        Number of simulations for critical values
    
    Returns
    -------
    CUSUMResult
        Test results
    """
    return dynamic_cusum_test(y, X, y_lagged=None, 
                              significance_level=significance_level,
                              n_simulations=n_simulations)
