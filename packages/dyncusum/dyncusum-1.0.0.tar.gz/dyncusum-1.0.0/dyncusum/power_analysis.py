"""
Power Analysis for CUSUM Tests in Dynamic Models

Based on: Krämer, W., Ploberger, W., & Alt, R. (1988). 
"Testing for Structural Change in Dynamic Models"
Econometrica, Vol. 56, No. 6, pp. 1355-1369.

This module implements:
1. Local power analysis under structural change (Section 3)
2. Theorem 2: Power depends on angle between structural shift and mean regressor
3. Monte Carlo power simulations replicating Table I

Author: Dr. Merwan Roudane
Email: merwanroudane920@gmail.com
"""

import numpy as np
from typing import Tuple, Dict, List, Optional, Union
from dataclasses import dataclass
from .core import dynamic_cusum_test, dufour_test, CUSUMResult
import warnings


@dataclass
class PowerResult:
    """
    Container for power analysis results.
    
    Attributes
    ----------
    power : float
        Estimated power (rejection rate under alternative)
    n_simulations : int
        Number of Monte Carlo simulations
    gamma : float
        Coefficient of lagged dependent variable
    psi : float
        Angle between structural shift and mean regressor (degrees)
    z_star : float
        Timing of structural break (as fraction of sample)
    b : float
        Intensity parameter for structural shift
    T : int
        Sample size
    significance_level : float
        Nominal significance level
    test_type : str
        Type of test ('dynamic_cusum' or 'dufour')
    """
    power: float
    n_simulations: int
    gamma: float
    psi: float
    z_star: float
    b: float
    T: int
    significance_level: float
    test_type: str


def compute_mean_regressor(gamma: float, c: np.ndarray) -> np.ndarray:
    """
    Compute the mean regressor d as defined in equation (6).
    
    d = [β'c/(1-γ), c']'
    
    For the model in equation (17) where x_t = [(-1)^t, 1]',
    we have c = [0, 1]' and d = [β_2/(1-γ), 0, 1]'.
    
    Parameters
    ----------
    gamma : float
        Coefficient of lagged dependent variable
    c : np.ndarray
        Mean of exogenous regressors (equation 2)
    
    Returns
    -------
    np.ndarray
        Mean regressor d
        
    References
    ----------
    Equation (6) and (19) in Krämer, Ploberger, and Alt (1988)
    """
    beta_c_term = c / (1 - gamma)  # This assumes β = 1 for simplicity
    d = np.concatenate([[beta_c_term[0]], c])
    return d


def compute_structural_shift(psi: float, b: float, 
                              d: np.ndarray) -> np.ndarray:
    """
    Compute the structural shift Δδ as in equation (18).
    
    Δδ = b * [0, sin(ψ), cos(ψ)]'
    
    where ψ is the angle between Δδ and the mean regressor d.
    
    Parameters
    ----------
    psi : float
        Angle in degrees between shift and mean regressor
    b : float
        Intensity of the structural shift
    d : np.ndarray
        Mean regressor (not used but kept for reference)
    
    Returns
    -------
    np.ndarray
        Structural shift vector Δδ
        
    References
    ----------
    Equation (18) in Krämer, Ploberger, and Alt (1988)
    """
    psi_rad = np.radians(psi)
    delta_delta = b * np.array([0, np.sin(psi_rad), np.cos(psi_rad)])
    return delta_delta


def generate_dynamic_data(T: int, gamma: float, beta: np.ndarray,
                          sigma: float = 1.0, y0: float = 0.0,
                          structural_break: Optional[Dict] = None,
                          seed: Optional[int] = None) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Generate data from the dynamic model in equation (17).
    
    y_t = γ*y_{t-1} + β_1*(-1)^t + β_2 + u_t
    
    with optional structural break.
    
    Parameters
    ----------
    T : int
        Number of observations
    gamma : float
        Coefficient of lagged dependent variable (|γ| < 1)
    beta : np.ndarray
        Coefficients [β_1, β_2] for exogenous regressors
    sigma : float
        Standard deviation of disturbances
    y0 : float
        Initial value y_0
    structural_break : dict, optional
        Dictionary with keys:
        - 'z_star': Break timing as fraction of T
        - 'delta_delta': Shift vector [Δγ, Δβ_1, Δβ_2]
    seed : int, optional
        Random seed
    
    Returns
    -------
    y : np.ndarray
        Dependent variable (T x 1)
    X : np.ndarray
        Exogenous regressors (T x 2)
    y_lagged : np.ndarray
        Lagged dependent variable (T x 1)
        
    References
    ----------
    Equation (17) in Krämer, Ploberger, and Alt (1988)
    """
    if seed is not None:
        np.random.seed(seed)
    
    if np.abs(gamma) >= 1:
        warnings.warn("gamma should satisfy |gamma| < 1 for stationarity")
    
    # Generate exogenous regressors: x_t = [(-1)^t, 1]'
    X = np.column_stack([
        np.array([(-1)**t for t in range(1, T+1)]),  # (-1)^t
        np.ones(T)  # constant
    ])
    
    # Generate disturbances
    u = np.random.normal(0, sigma, T)
    
    # Generate y series with possible structural break
    y = np.zeros(T)
    y_lagged = np.zeros(T)
    
    # Coefficients: δ = [γ, β_1, β_2]
    delta_t = np.concatenate([[gamma], beta])
    
    # Break timing
    if structural_break is not None:
        T_star = int(structural_break['z_star'] * T)
        delta_delta = structural_break['delta_delta']
    else:
        T_star = T + 1  # No break
        delta_delta = np.zeros(3)
    
    # Generate data
    y_prev = y0
    for t in range(T):
        y_lagged[t] = y_prev
        z_t = np.concatenate([[y_prev], X[t, :]])
        
        # Apply structural shift if after break point
        # Shift intensity scales with 1/sqrt(T) for local alternatives
        if t + 1 > T_star:
            delta_current = delta_t + delta_delta / np.sqrt(T)
        else:
            delta_current = delta_t
        
        y[t] = z_t @ delta_current + u[t]
        y_prev = y[t]
    
    return y, X, y_lagged


def monte_carlo_power(gamma: float, psi: float, z_star: float, b: float,
                      T: int = 120, n_simulations: int = 1000,
                      significance_level: float = 0.05,
                      test_type: str = 'dynamic_cusum',
                      beta: np.ndarray = None,
                      seed: int = 42) -> PowerResult:
    """
    Compute power via Monte Carlo simulation.
    
    Replicates the Monte Carlo experiments in Section 3 and Table I.
    
    Parameters
    ----------
    gamma : float
        Coefficient of lagged dependent variable
    psi : float
        Angle (degrees) between structural shift and mean regressor
    z_star : float
        Timing of break (fraction of sample)
    b : float
        Intensity of structural shift
    T : int
        Sample size
    n_simulations : int
        Number of Monte Carlo replications
    significance_level : float
        Nominal significance level
    test_type : str
        'dynamic_cusum' or 'dufour'
    beta : np.ndarray, optional
        Regression coefficients [β_1, β_2]. Default: [2, 10]
    seed : int
        Random seed
    
    Returns
    -------
    PowerResult
        Object containing power analysis results
        
    References
    ----------
    Table I in Krämer, Ploberger, and Alt (1988)
    """
    if beta is None:
        beta = np.array([2, 10])  # Default from paper
    
    np.random.seed(seed)
    
    # Compute structural shift
    d = compute_mean_regressor(gamma, np.array([0, 1]))  # c = [0, 1] from eq (17)
    delta_delta = compute_structural_shift(psi, b, d)
    
    structural_break = {
        'z_star': z_star,
        'delta_delta': delta_delta
    }
    
    rejections = 0
    
    for sim in range(n_simulations):
        # Generate data
        y, X, y_lagged = generate_dynamic_data(
            T=T, gamma=gamma, beta=beta,
            structural_break=structural_break,
            seed=seed + sim
        )
        
        try:
            if test_type == 'dynamic_cusum':
                result = dynamic_cusum_test(
                    y, X, y_lagged,
                    significance_level=significance_level,
                    n_simulations=1000  # Fewer sims for inner test
                )
            elif test_type == 'dufour':
                result = dufour_test(
                    y, X, y_lagged,
                    significance_level=significance_level,
                    n_simulations=1000
                )
            else:
                raise ValueError(f"Unknown test_type: {test_type}")
            
            if result.reject_null:
                rejections += 1
                
        except Exception as e:
            warnings.warn(f"Simulation {sim} failed: {e}")
    
    power = rejections / n_simulations
    
    return PowerResult(
        power=power,
        n_simulations=n_simulations,
        gamma=gamma,
        psi=psi,
        z_star=z_star,
        b=b,
        T=T,
        significance_level=significance_level,
        test_type=test_type
    )


def replicate_table_1(T: int = 120, n_simulations: int = 1000,
                       gamma_values: List[float] = None,
                       psi_values: List[float] = None,
                       z_star_values: List[float] = None,
                       b_values: List[float] = None,
                       significance_level: float = 0.05) -> Dict:
    """
    Replicate Table I from Krämer, Ploberger, and Alt (1988).
    
    Table I shows the power of the Dynamic CUSUM and Dufour tests
    for various combinations of:
    - γ: coefficient of lagged dependent variable
    - ψ: angle between structural shift and mean regressor
    - z*: timing of structural break
    - b: intensity of structural shift
    
    Parameters
    ----------
    T : int
        Sample size (default: 120)
    n_simulations : int
        Number of Monte Carlo replications per cell
    gamma_values : list
        Values of γ to test
    psi_values : list
        Angles ψ in degrees
    z_star_values : list
        Break timings z*
    b_values : list
        Intensity values b
    significance_level : float
        Nominal significance level
    
    Returns
    -------
    dict
        Dictionary containing power results organized as in Table I
        
    References
    ----------
    Table I (p. 1361) in Krämer, Ploberger, and Alt (1988)
    """
    if gamma_values is None:
        gamma_values = [-0.5, 0, 0.5]
    if psi_values is None:
        psi_values = [0, 30, 60, 90]
    if z_star_values is None:
        z_star_values = [0.3, 0.5, 0.7]
    if b_values is None:
        b_values = [3, 6, 12]
    
    results = {
        'parameters': {
            'T': T,
            'n_simulations': n_simulations,
            'significance_level': significance_level,
            'gamma_values': gamma_values,
            'psi_values': psi_values,
            'z_star_values': z_star_values,
            'b_values': b_values
        },
        'dynamic_cusum': {},
        'dufour': {}
    }
    
    total_cells = len(gamma_values) * len(psi_values) * len(z_star_values) * len(b_values)
    cell_count = 0
    
    for gamma in gamma_values:
        results['dynamic_cusum'][gamma] = {}
        results['dufour'][gamma] = {}
        
        for z_star in z_star_values:
            results['dynamic_cusum'][gamma][z_star] = {}
            results['dufour'][gamma][z_star] = {}
            
            for b in b_values:
                results['dynamic_cusum'][gamma][z_star][b] = {}
                results['dufour'][gamma][z_star][b] = {}
                
                for psi in psi_values:
                    cell_count += 1
                    print(f"Computing cell {cell_count}/{total_cells}: "
                          f"γ={gamma}, z*={z_star}, b={b}, ψ={psi}°")
                    
                    # Dynamic CUSUM
                    power_dc = monte_carlo_power(
                        gamma=gamma, psi=psi, z_star=z_star, b=b,
                        T=T, n_simulations=n_simulations,
                        significance_level=significance_level,
                        test_type='dynamic_cusum'
                    )
                    results['dynamic_cusum'][gamma][z_star][b][psi] = power_dc.power
                    
                    # Dufour test
                    power_duf = monte_carlo_power(
                        gamma=gamma, psi=psi, z_star=z_star, b=b,
                        T=T, n_simulations=n_simulations,
                        significance_level=significance_level,
                        test_type='dufour'
                    )
                    results['dufour'][gamma][z_star][b][psi] = power_duf.power
    
    return results


def verify_theorem_2(n_simulations: int = 1000,
                      T: int = 120,
                      gamma: float = 0.5) -> Dict:
    """
    Verify Theorem 2: Power is trivial when g(z) is orthogonal to d.
    
    Theorem 2 states that if the structural shift is orthogonal to the
    mean regressor d for almost all z, the limiting rejection probability
    equals the nominal significance level (no power).
    
    This corresponds to ψ = 90° in the Monte Carlo experiments.
    
    Parameters
    ----------
    n_simulations : int
        Number of simulations
    T : int
        Sample size
    gamma : float
        Coefficient of lagged dependent variable
    
    Returns
    -------
    dict
        Results verifying Theorem 2
        
    References
    ----------
    Theorem 2 and proof (p. 1360) in Krämer, Ploberger, and Alt (1988)
    """
    results = {
        'theorem': 'Theorem 2: Power is trivial when shift orthogonal to mean regressor',
        'gamma': gamma,
        'T': T,
        'n_simulations': n_simulations,
        'results': []
    }
    
    # Test at ψ = 90° (orthogonal) vs ψ = 0° (parallel)
    for psi in [0, 90]:
        for b in [6, 12]:
            power_result = monte_carlo_power(
                gamma=gamma, psi=psi, z_star=0.5, b=b,
                T=T, n_simulations=n_simulations,
                test_type='dynamic_cusum'
            )
            results['results'].append({
                'psi': psi,
                'b': b,
                'power': power_result.power,
                'interpretation': 'orthogonal (no power expected)' if psi == 90 else 'parallel (power expected)'
            })
    
    return results


def analyze_power_vs_angle(gamma: float = 0.0, z_star: float = 0.5,
                           b: float = 12, T: int = 120,
                           n_simulations: int = 500,
                           n_angles: int = 10) -> Dict:
    """
    Analyze how power varies with the angle ψ.
    
    This demonstrates the key finding from the paper that power
    depends crucially on the angle between structural shift and
    mean regressor.
    
    Parameters
    ----------
    gamma : float
        Coefficient of lagged dependent variable
    z_star : float
        Break timing
    b : float
        Intensity of shift
    T : int
        Sample size
    n_simulations : int
        Number of simulations per angle
    n_angles : int
        Number of angles to test
    
    Returns
    -------
    dict
        Results showing power vs angle
    """
    angles = np.linspace(0, 90, n_angles)
    powers = []
    
    for psi in angles:
        result = monte_carlo_power(
            gamma=gamma, psi=psi, z_star=z_star, b=b,
            T=T, n_simulations=n_simulations,
            test_type='dynamic_cusum'
        )
        powers.append(result.power)
    
    return {
        'angles': angles.tolist(),
        'powers': powers,
        'gamma': gamma,
        'z_star': z_star,
        'b': b,
        'T': T,
        'n_simulations': n_simulations
    }


def size_analysis(gamma_values: List[float] = None,
                   T: int = 120, n_simulations: int = 1000,
                   significance_level: float = 0.05) -> Dict:
    """
    Analyze the actual size of the tests under H0.
    
    From the paper (p. 1359-1360):
    - True size is almost always smaller than nominal size
    - The gap narrows as sample size increases
    - Dufour test is extremely nonsimilar (size depends on γ)
    
    Parameters
    ----------
    gamma_values : list
        Values of γ to test
    T : int
        Sample size
    n_simulations : int
        Number of simulations
    significance_level : float
        Nominal significance level
    
    Returns
    -------
    dict
        Size analysis results
        
    References
    ----------
    Section 2 discussion and footnote 2 in Krämer et al. (1988)
    """
    if gamma_values is None:
        gamma_values = [-0.8, -0.5, -0.2, 0.0, 0.2, 0.5, 0.8]
    
    results = {
        'nominal_size': significance_level,
        'T': T,
        'n_simulations': n_simulations,
        'dynamic_cusum': {},
        'dufour': {}
    }
    
    for gamma in gamma_values:
        # Under H0, no structural break (b = 0)
        power_dc = monte_carlo_power(
            gamma=gamma, psi=0, z_star=0.5, b=0,
            T=T, n_simulations=n_simulations,
            significance_level=significance_level,
            test_type='dynamic_cusum'
        )
        results['dynamic_cusum'][gamma] = power_dc.power
        
        power_duf = monte_carlo_power(
            gamma=gamma, psi=0, z_star=0.5, b=0,
            T=T, n_simulations=n_simulations,
            significance_level=significance_level,
            test_type='dufour'
        )
        results['dufour'][gamma] = power_duf.power
    
    return results
