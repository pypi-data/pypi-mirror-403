"""
Visualization Tools for CUSUM Tests

Based on: Krämer, W., Ploberger, W., & Alt, R. (1988). 
"Testing for Structural Change in Dynamic Models"
Econometrica, Vol. 56, No. 6, pp. 1355-1369.

Provides publication-quality plots for:
1. CUSUM process with critical boundaries
2. Power curves
3. Recursive residuals
4. Comparison plots

Author: Dr. Merwan Roudane
Email: merwanroudane920@gmail.com
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from typing import Optional, Tuple, List, Dict, Any, Union
from .core import CUSUMResult


# Publication-quality plot settings
PLOT_STYLE = {
    'figure.figsize': (10, 6),
    'axes.labelsize': 12,
    'axes.titlesize': 14,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 10,
    'font.family': 'serif',
    'font.serif': ['Times New Roman', 'DejaVu Serif'],
    'axes.linewidth': 1.0,
    'lines.linewidth': 1.5,
    'axes.grid': True,
    'grid.alpha': 0.3,
}


def set_publication_style():
    """Set matplotlib parameters for publication-quality plots."""
    plt.rcParams.update(PLOT_STYLE)


def plot_cusum(result: CUSUMResult, 
               title: Optional[str] = None,
               figsize: Tuple[float, float] = (10, 6),
               show_critical_values: bool = True,
               show_legend: bool = True,
               save_path: Optional[str] = None,
               dpi: int = 300) -> Figure:
    """
    Plot the CUSUM process with critical boundaries.
    
    Creates a publication-quality plot showing:
    - The CUSUM process W^(r)
    - Upper and lower critical boundaries
    - Test outcome annotation
    
    Parameters
    ----------
    result : CUSUMResult
        Result object from dynamic_cusum_test or dufour_test
    title : str, optional
        Plot title. If None, auto-generated.
    figsize : tuple
        Figure size (width, height)
    show_critical_values : bool
        Whether to show critical boundary lines
    show_legend : bool
        Whether to show legend
    save_path : str, optional
        If provided, save figure to this path
    dpi : int
        Resolution for saved figure
    
    Returns
    -------
    Figure
        Matplotlib figure object
    """
    set_publication_style()
    
    fig, ax = plt.subplots(figsize=figsize)
    
    T = result.n_obs
    K = result.n_regressors - 1  # K in paper notation
    
    # x-axis: r values from K+2 to T
    r_values = np.arange(K + 2, T + 1)
    
    # Ensure W_process matches r_values length
    W = result.W_process
    if len(W) != len(r_values):
        # Truncate or pad as needed
        min_len = min(len(W), len(r_values))
        W = W[:min_len]
        r_values = r_values[:min_len]
    
    # Plot CUSUM process
    ax.plot(r_values, W, 'b-', linewidth=1.5, label='CUSUM Process $W^{(r)}$')
    
    # Plot critical boundaries if requested
    if show_critical_values:
        upper = result.critical_lines_upper[:len(r_values)]
        lower = result.critical_lines_lower[:len(r_values)]
        
        ax.plot(r_values, upper, 'r--', linewidth=1.2, 
                label=f'Critical Boundaries ($\\alpha = {result.significance_level}$)')
        ax.plot(r_values, lower, 'r--', linewidth=1.2)
        
        # Shade rejection region
        ax.fill_between(r_values, upper, np.max(upper) * 1.5, 
                        alpha=0.1, color='red')
        ax.fill_between(r_values, lower, np.min(lower) * 1.5, 
                        alpha=0.1, color='red')
    
    # Add horizontal line at zero
    ax.axhline(y=0, color='gray', linestyle='-', linewidth=0.5)
    
    # Annotations
    test_outcome = "Reject $H_0$" if result.reject_null else "Do not reject $H_0$"
    ax.annotate(f'{test_outcome}\n$S = {result.statistic:.4f}$\n$p = {result.p_value:.4f}$',
                xy=(0.02, 0.98), xycoords='axes fraction',
                verticalalignment='top', fontsize=10,
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    # Labels
    ax.set_xlabel('Observation $r$')
    ax.set_ylabel('$W^{(r)}$')
    
    if title is None:
        test_name = 'Dynamic CUSUM Test' if result.test_type == 'dynamic_cusum' else 'Dufour Test'
        title = f'{test_name} for Structural Change'
    ax.set_title(title)
    
    if show_legend:
        ax.legend(loc='upper right')
    
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        fig.savefig(save_path, dpi=dpi, bbox_inches='tight')
    
    return fig


def plot_recursive_residuals(result: CUSUMResult,
                              title: Optional[str] = None,
                              figsize: Tuple[float, float] = (10, 6),
                              show_bounds: bool = True,
                              save_path: Optional[str] = None,
                              dpi: int = 300) -> Figure:
    """
    Plot the recursive residuals w_r.
    
    Parameters
    ----------
    result : CUSUMResult
        Result object from CUSUM test
    title : str, optional
        Plot title
    figsize : tuple
        Figure size
    show_bounds : bool
        Whether to show ±2σ bounds
    save_path : str, optional
        Path to save figure
    dpi : int
        Resolution
    
    Returns
    -------
    Figure
        Matplotlib figure
    """
    set_publication_style()
    
    fig, ax = plt.subplots(figsize=figsize)
    
    T = result.n_obs
    K = result.n_regressors - 1
    
    w = result.recursive_residuals
    r_values = np.arange(K + 2, K + 2 + len(w))
    
    # Plot residuals
    ax.plot(r_values, w, 'b-', linewidth=1, marker='o', markersize=3,
            label='Recursive Residuals $w_r$')
    
    # Add ±2σ bounds
    if show_bounds:
        sigma = result.sigma_hat
        ax.axhline(y=2*sigma, color='red', linestyle='--', linewidth=1,
                   label=r'$\pm 2\hat{\sigma}$' + f' ($\\hat{{\\sigma}} = {sigma:.3f}$)')
        ax.axhline(y=-2*sigma, color='red', linestyle='--', linewidth=1)
    
    ax.axhline(y=0, color='gray', linestyle='-', linewidth=0.5)
    
    ax.set_xlabel('Observation $r$')
    ax.set_ylabel('Recursive Residual $w_r$')
    
    if title is None:
        title = 'Recursive Residuals'
    ax.set_title(title)
    
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        fig.savefig(save_path, dpi=dpi, bbox_inches='tight')
    
    return fig


def plot_power_curve(angles: np.ndarray, powers: np.ndarray,
                     gamma: float = 0.0, z_star: float = 0.5,
                     b: float = 12, T: int = 120,
                     title: Optional[str] = None,
                     figsize: Tuple[float, float] = (8, 6),
                     save_path: Optional[str] = None,
                     dpi: int = 300) -> Figure:
    """
    Plot power as a function of the angle ψ.
    
    Demonstrates the key finding from Theorem 2 that power
    depends on the angle between structural shift and mean regressor.
    
    Parameters
    ----------
    angles : np.ndarray
        Angles in degrees
    powers : np.ndarray
        Corresponding power values
    gamma, z_star, b, T : float/int
        Parameters used in simulation
    title : str, optional
        Plot title
    figsize : tuple
        Figure size
    save_path : str, optional
        Path to save figure
    dpi : int
        Resolution
    
    Returns
    -------
    Figure
        Matplotlib figure
    """
    set_publication_style()
    
    fig, ax = plt.subplots(figsize=figsize)
    
    ax.plot(angles, powers, 'b-o', linewidth=2, markersize=6)
    
    # Add reference line at nominal size
    ax.axhline(y=0.05, color='red', linestyle='--', linewidth=1,
               label='Nominal Size ($\\alpha = 0.05$)')
    
    ax.set_xlabel('Angle $\\psi$ (degrees)')
    ax.set_ylabel('Power')
    ax.set_xlim(0, 90)
    ax.set_ylim(0, 1)
    
    if title is None:
        title = f'Power vs. Angle\n($\\gamma = {gamma}$, $z^* = {z_star}$, $b = {b}$, $T = {T}$)'
    ax.set_title(title)
    
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        fig.savefig(save_path, dpi=dpi, bbox_inches='tight')
    
    return fig


def plot_comparison(result_dc: CUSUMResult, result_duf: CUSUMResult,
                    title: Optional[str] = None,
                    figsize: Tuple[float, float] = (12, 5),
                    save_path: Optional[str] = None,
                    dpi: int = 300) -> Figure:
    """
    Plot side-by-side comparison of Dynamic CUSUM and Dufour tests.
    
    Parameters
    ----------
    result_dc : CUSUMResult
        Result from dynamic_cusum_test
    result_duf : CUSUMResult
        Result from dufour_test
    title : str, optional
        Overall title
    figsize : tuple
        Figure size
    save_path : str, optional
        Path to save figure
    dpi : int
        Resolution
    
    Returns
    -------
    Figure
        Matplotlib figure
    """
    set_publication_style()
    
    fig, axes = plt.subplots(1, 2, figsize=figsize)
    
    for ax, result, name in zip(axes, [result_dc, result_duf], 
                                 ['Dynamic CUSUM', 'Dufour']):
        T = result.n_obs
        K = result.n_regressors - 1
        r_values = np.arange(K + 2, T + 1)
        
        W = result.W_process
        min_len = min(len(W), len(r_values))
        W = W[:min_len]
        r_values = r_values[:min_len]
        
        ax.plot(r_values, W, 'b-', linewidth=1.5)
        
        upper = result.critical_lines_upper[:min_len]
        lower = result.critical_lines_lower[:min_len]
        
        ax.plot(r_values, upper, 'r--', linewidth=1.2)
        ax.plot(r_values, lower, 'r--', linewidth=1.2)
        
        ax.axhline(y=0, color='gray', linestyle='-', linewidth=0.5)
        
        outcome = "Reject $H_0$" if result.reject_null else "Do not reject $H_0$"
        ax.annotate(f'{outcome}\n$S = {result.statistic:.4f}$',
                    xy=(0.02, 0.98), xycoords='axes fraction',
                    verticalalignment='top', fontsize=9,
                    bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        ax.set_xlabel('Observation $r$')
        ax.set_ylabel('$W^{(r)}$')
        ax.set_title(f'{name} Test')
        ax.grid(True, alpha=0.3)
    
    if title:
        fig.suptitle(title, fontsize=14, y=1.02)
    
    plt.tight_layout()
    
    if save_path:
        fig.savefig(save_path, dpi=dpi, bbox_inches='tight')
    
    return fig


def plot_size_analysis(results: Dict,
                       figsize: Tuple[float, float] = (10, 6),
                       save_path: Optional[str] = None,
                       dpi: int = 300) -> Figure:
    """
    Plot size analysis results showing actual vs nominal size.
    
    Demonstrates finding from paper that true size is smaller than
    nominal size and that Dufour test is extremely nonsimilar.
    
    Parameters
    ----------
    results : dict
        Results from size_analysis function
    figsize : tuple
        Figure size
    save_path : str, optional
        Path to save figure
    dpi : int
        Resolution
    
    Returns
    -------
    Figure
        Matplotlib figure
    """
    set_publication_style()
    
    fig, ax = plt.subplots(figsize=figsize)
    
    gamma_values = list(results['dynamic_cusum'].keys())
    dc_sizes = [results['dynamic_cusum'][g] for g in gamma_values]
    duf_sizes = [results['dufour'][g] for g in gamma_values]
    
    x = np.arange(len(gamma_values))
    width = 0.35
    
    bars1 = ax.bar(x - width/2, dc_sizes, width, label='Dynamic CUSUM', color='blue', alpha=0.7)
    bars2 = ax.bar(x + width/2, duf_sizes, width, label='Dufour', color='orange', alpha=0.7)
    
    # Nominal size reference line
    ax.axhline(y=results['nominal_size'], color='red', linestyle='--', 
               linewidth=2, label=f"Nominal Size ($\\alpha = {results['nominal_size']}$)")
    
    ax.set_xlabel('$\\gamma$ (Coefficient of Lagged Dependent Variable)')
    ax.set_ylabel('Actual Rejection Rate')
    ax.set_title(f'Size Analysis: True vs Nominal Size ($T = {results["T"]}$)')
    ax.set_xticks(x)
    ax.set_xticklabels([f'{g:.1f}' for g in gamma_values])
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    
    ax.set_ylim(0, max(max(dc_sizes), max(duf_sizes), results['nominal_size']) * 1.3)
    
    plt.tight_layout()
    
    if save_path:
        fig.savefig(save_path, dpi=dpi, bbox_inches='tight')
    
    return fig


def create_summary_figure(result: CUSUMResult,
                          figsize: Tuple[float, float] = (14, 10),
                          save_path: Optional[str] = None,
                          dpi: int = 300) -> Figure:
    """
    Create a comprehensive summary figure with multiple panels.
    
    Includes:
    1. CUSUM process with critical boundaries
    2. Recursive residuals
    3. Histogram of recursive residuals
    4. Q-Q plot for normality check
    
    Parameters
    ----------
    result : CUSUMResult
        Result from CUSUM test
    figsize : tuple
        Figure size
    save_path : str, optional
        Path to save figure
    dpi : int
        Resolution
    
    Returns
    -------
    Figure
        Matplotlib figure
    """
    set_publication_style()
    
    fig = plt.figure(figsize=figsize)
    
    # Create grid
    gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)
    
    T = result.n_obs
    K = result.n_regressors - 1
    
    # Panel 1: CUSUM process
    ax1 = fig.add_subplot(gs[0, 0])
    r_values = np.arange(K + 2, T + 1)
    W = result.W_process
    min_len = min(len(W), len(r_values))
    
    ax1.plot(r_values[:min_len], W[:min_len], 'b-', linewidth=1.5)
    ax1.plot(r_values[:min_len], result.critical_lines_upper[:min_len], 'r--', linewidth=1.2)
    ax1.plot(r_values[:min_len], result.critical_lines_lower[:min_len], 'r--', linewidth=1.2)
    ax1.axhline(y=0, color='gray', linestyle='-', linewidth=0.5)
    ax1.set_xlabel('Observation $r$')
    ax1.set_ylabel('$W^{(r)}$')
    ax1.set_title('(a) CUSUM Process')
    ax1.grid(True, alpha=0.3)
    
    # Panel 2: Recursive residuals
    ax2 = fig.add_subplot(gs[0, 1])
    w = result.recursive_residuals
    r_w = np.arange(K + 2, K + 2 + len(w))
    
    ax2.plot(r_w, w, 'b-', linewidth=1, marker='o', markersize=2)
    ax2.axhline(y=0, color='gray', linestyle='-', linewidth=0.5)
    ax2.axhline(y=2*result.sigma_hat, color='red', linestyle='--', linewidth=1)
    ax2.axhline(y=-2*result.sigma_hat, color='red', linestyle='--', linewidth=1)
    ax2.set_xlabel('Observation $r$')
    ax2.set_ylabel('$w_r$')
    ax2.set_title('(b) Recursive Residuals')
    ax2.grid(True, alpha=0.3)
    
    # Panel 3: Histogram
    ax3 = fig.add_subplot(gs[1, 0])
    w_clean = w[~np.isnan(w)]
    ax3.hist(w_clean, bins=30, density=True, alpha=0.7, color='blue', edgecolor='black')
    
    # Overlay normal distribution
    x_norm = np.linspace(w_clean.min(), w_clean.max(), 100)
    y_norm = (1/(result.sigma_hat * np.sqrt(2*np.pi))) * \
             np.exp(-0.5 * ((x_norm) / result.sigma_hat)**2)
    ax3.plot(x_norm, y_norm, 'r-', linewidth=2, label='$N(0, \\hat{\\sigma}^2)$')
    ax3.set_xlabel('Recursive Residual')
    ax3.set_ylabel('Density')
    ax3.set_title('(c) Distribution of Recursive Residuals')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # Panel 4: Test summary
    ax4 = fig.add_subplot(gs[1, 1])
    ax4.axis('off')
    
    test_name = 'Dynamic CUSUM' if result.test_type == 'dynamic_cusum' else 'Dufour'
    decision = 'Reject $H_0$' if result.reject_null else 'Do not reject $H_0$'
    
    summary_text = f"""
    Test Summary
    ────────────────────────────
    Test Type: {test_name}
    
    Observations: {result.n_obs}
    Regressors: {result.n_regressors}
    
    Test Statistic: S = {result.statistic:.4f}
    Critical Value: a = {result.critical_value:.4f}
    P-value: {result.p_value:.4f}
    
    Significance Level: α = {result.significance_level}
    
    Decision: {decision}
    
    σ̂ = {result.sigma_hat:.4f}
    """
    
    ax4.text(0.1, 0.9, summary_text, transform=ax4.transAxes,
             fontsize=11, verticalalignment='top', fontfamily='monospace',
             bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.5))
    ax4.set_title('(d) Test Summary')
    
    if save_path:
        fig.savefig(save_path, dpi=dpi, bbox_inches='tight')
    
    return fig
