"""
dyncusum: CUSUM Tests for Structural Change in Dynamic Models

A Python library implementing the CUSUM tests for structural change
as described in:

Krämer, W., Ploberger, W., & Alt, R. (1988). 
"Testing for Structural Change in Dynamic Models"
Econometrica, Vol. 56, No. 6, pp. 1355-1369.

This library provides:
1. Dynamic CUSUM test (straightforward CUSUM for dynamic models)
2. Dufour test (modified procedure from Dufour, 1982)
3. Critical value computation via Monte Carlo simulation
4. Power analysis tools
5. Publication-quality visualization and tables

Author: Dr. Merwan Roudane
Email: merwanroudane920@gmail.com
GitHub: https://github.com/merwanroudane/cusum

License: MIT
"""

__version__ = "1.0.0"
__author__ = "Dr. Merwan Roudane"
__email__ = "merwanroudane920@gmail.com"

# Core test functions
from .core import (
    dynamic_cusum_test,
    dufour_test,
    cusum_ols,
    CUSUMResult,
    compute_recursive_residuals,
    compute_cusum_process,
    compute_test_statistic,
    estimate_sigma_harvey,
    estimate_sigma_ols,
)

# Critical values
from .critical_values import (
    CriticalValueTable,
    simulate_cusum_distribution,
    generate_critical_value_table,
    finite_sample_critical_value,
    get_best_critical_value,
    BDE_CRITICAL_VALUES,
)

# Power analysis
from .power_analysis import (
    PowerResult,
    monte_carlo_power,
    replicate_table_1,
    verify_theorem_2,
    analyze_power_vs_angle,
    size_analysis,
    generate_dynamic_data,
    compute_structural_shift,
    compute_mean_regressor,
)

# Visualization
from .visualization import (
    plot_cusum,
    plot_recursive_residuals,
    plot_power_curve,
    plot_comparison,
    plot_size_analysis,
    create_summary_figure,
    set_publication_style,
)

# Tables
from .tables import (
    format_test_result,
    format_multiple_results,
    format_power_table,
    format_power_table_latex,
    format_critical_values_table,
    format_size_analysis_table,
    print_test_summary,
    create_regression_diagnostics_table,
    export_results_to_csv,
)

# Utilities
from .utils import (
    check_stationarity,
    prepare_data,
    validate_inputs,
    estimate_ar1_coefficient,
    ols_regression,
    durbin_watson,
    breusch_godfrey_test,
    simulate_ar1,
    compute_information_criteria,
    check_multicollinearity,
)

# Define what's available when using "from dyncusum import *"
__all__ = [
    # Version info
    '__version__',
    '__author__',
    '__email__',
    
    # Core
    'dynamic_cusum_test',
    'dufour_test',
    'cusum_ols',
    'CUSUMResult',
    'compute_recursive_residuals',
    'compute_cusum_process',
    'compute_test_statistic',
    'estimate_sigma_harvey',
    'estimate_sigma_ols',
    
    # Critical values
    'CriticalValueTable',
    'simulate_cusum_distribution',
    'generate_critical_value_table',
    'finite_sample_critical_value',
    'get_best_critical_value',
    'BDE_CRITICAL_VALUES',
    
    # Power analysis
    'PowerResult',
    'monte_carlo_power',
    'replicate_table_1',
    'verify_theorem_2',
    'analyze_power_vs_angle',
    'size_analysis',
    'generate_dynamic_data',
    'compute_structural_shift',
    'compute_mean_regressor',
    
    # Visualization
    'plot_cusum',
    'plot_recursive_residuals',
    'plot_power_curve',
    'plot_comparison',
    'plot_size_analysis',
    'create_summary_figure',
    'set_publication_style',
    
    # Tables
    'format_test_result',
    'format_multiple_results',
    'format_power_table',
    'format_power_table_latex',
    'format_critical_values_table',
    'format_size_analysis_table',
    'print_test_summary',
    'create_regression_diagnostics_table',
    'export_results_to_csv',
    
    # Utilities
    'check_stationarity',
    'prepare_data',
    'validate_inputs',
    'estimate_ar1_coefficient',
    'ols_regression',
    'durbin_watson',
    'breusch_godfrey_test',
    'simulate_ar1',
    'compute_information_criteria',
    'check_multicollinearity',
]
