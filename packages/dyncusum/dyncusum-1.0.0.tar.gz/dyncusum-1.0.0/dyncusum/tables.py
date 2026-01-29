"""
Publication-Ready Tables for CUSUM Test Results

Based on: Krämer, W., Ploberger, W., & Alt, R. (1988). 
"Testing for Structural Change in Dynamic Models"
Econometrica, Vol. 56, No. 6, pp. 1355-1369.

Provides formatted tables for:
1. Test results summary
2. Power analysis results (replicating Table I)
3. Critical values
4. Size analysis

Author: Dr. Merwan Roudane
Email: merwanroudane920@gmail.com
"""

import numpy as np
from typing import Dict, List, Optional, Any, Union
from tabulate import tabulate
from .core import CUSUMResult


def format_test_result(result: CUSUMResult, 
                       table_format: str = 'grid',
                       float_fmt: str = '.4f') -> str:
    """
    Format CUSUM test result as a publication-ready table.
    
    Parameters
    ----------
    result : CUSUMResult
        Result object from CUSUM test
    table_format : str
        Table format for tabulate (e.g., 'grid', 'latex', 'html', 'pipe')
    float_fmt : str
        Float format string
    
    Returns
    -------
    str
        Formatted table string
    """
    test_name = 'Dynamic CUSUM Test' if result.test_type == 'dynamic_cusum' else 'Dufour Test'
    decision = 'Reject H₀' if result.reject_null else 'Do not reject H₀'
    
    data = [
        ['Test Type', test_name],
        ['Number of Observations (T)', result.n_obs],
        ['Number of Regressors (K+1)', result.n_regressors],
        ['', ''],
        ['Test Statistic (S)', f'{result.statistic:{float_fmt}}'],
        ['Critical Value (a)', f'{result.critical_value:{float_fmt}}'],
        ['P-value', f'{result.p_value:{float_fmt}}'],
        ['', ''],
        ['Significance Level (α)', f'{result.significance_level}'],
        ['Decision', decision],
        ['', ''],
        ['Estimated σ', f'{result.sigma_hat:{float_fmt}}'],
    ]
    
    return tabulate(data, headers=['Parameter', 'Value'], 
                    tablefmt=table_format, stralign='left')


def format_multiple_results(results: List[CUSUMResult],
                            labels: Optional[List[str]] = None,
                            table_format: str = 'grid',
                            float_fmt: str = '.4f') -> str:
    """
    Format multiple CUSUM test results for comparison.
    
    Parameters
    ----------
    results : list of CUSUMResult
        List of test results
    labels : list of str, optional
        Labels for each result
    table_format : str
        Table format
    float_fmt : str
        Float format
    
    Returns
    -------
    str
        Formatted comparison table
    """
    if labels is None:
        labels = [f'Model {i+1}' for i in range(len(results))]
    
    headers = ['Statistic'] + labels
    
    data = [
        ['Test Type'] + [r.test_type.replace('_', ' ').title() for r in results],
        ['T'] + [r.n_obs for r in results],
        ['K+1'] + [r.n_regressors for r in results],
        ['S'] + [f'{r.statistic:{float_fmt}}' for r in results],
        ['Critical Value'] + [f'{r.critical_value:{float_fmt}}' for r in results],
        ['P-value'] + [f'{r.p_value:{float_fmt}}' for r in results],
        ['Decision'] + ['Reject H₀' if r.reject_null else 'Accept H₀' for r in results],
        ['σ̂'] + [f'{r.sigma_hat:{float_fmt}}' for r in results],
    ]
    
    return tabulate(data, headers=headers, tablefmt=table_format)


def format_power_table(power_results: Dict,
                       table_format: str = 'grid',
                       float_fmt: str = '.2f') -> str:
    """
    Format power analysis results as Table I from the paper.
    
    Parameters
    ----------
    power_results : dict
        Results from replicate_table_1 function
    table_format : str
        Table format ('grid', 'latex', 'pipe', etc.)
    float_fmt : str
        Float format for power values
    
    Returns
    -------
    str
        Formatted power table
        
    References
    ----------
    Table I (p. 1361) in Krämer, Ploberger, and Alt (1988)
    """
    params = power_results['parameters']
    
    tables = []
    
    for test_type, test_name in [('dynamic_cusum', 'Dynamic CUSUM Test'),
                                  ('dufour', 'Dufour Test')]:
        tables.append(f"\n{'='*60}")
        tables.append(f"{test_name}")
        tables.append(f"(T = {params['T']}, α = {params['significance_level']}, "
                     f"n_simulations = {params['n_simulations']})")
        tables.append('='*60)
        
        for gamma in params['gamma_values']:
            tables.append(f"\nγ = {gamma}")
            tables.append('-'*50)
            
            # Headers: z*, b, then ψ values
            headers = ['z*', 'b'] + [f"ψ={psi}°" for psi in params['psi_values']]
            
            data = []
            for z_star in params['z_star_values']:
                for b in params['b_values']:
                    row = [f'{z_star}', f'{b}']
                    for psi in params['psi_values']:
                        power = power_results[test_type][gamma][z_star][b][psi]
                        row.append(f'{power:{float_fmt}}')
                    data.append(row)
            
            tables.append(tabulate(data, headers=headers, tablefmt=table_format))
    
    return '\n'.join(tables)


def format_power_table_latex(power_results: Dict,
                              float_fmt: str = '.2f') -> str:
    """
    Format power table in LaTeX format for publication.
    
    Parameters
    ----------
    power_results : dict
        Results from replicate_table_1
    float_fmt : str
        Float format
    
    Returns
    -------
    str
        LaTeX table code
    """
    params = power_results['parameters']
    
    latex_lines = []
    
    for test_type, test_name in [('dynamic_cusum', '(a) Dynamic CUSUM test'),
                                  ('dufour', '(b) Dufour test')]:
        latex_lines.append(f"\\multicolumn{{{6 + len(params['psi_values'])}}}{{c}}{{{test_name}}} \\\\")
        latex_lines.append("\\hline")
        
        # Header row
        psi_headers = ' & '.join([f"$\\psi={psi}^\\circ$" for psi in params['psi_values']])
        
        for gamma in params['gamma_values']:
            latex_lines.append(f"\\multicolumn{{{len(params['psi_values']) + 2}}}{{c}}{{$\\gamma = {gamma}$}} \\\\")
            latex_lines.append(f"$z^*$ & $b$ & {psi_headers} \\\\")
            latex_lines.append("\\hline")
            
            for z_star in params['z_star_values']:
                for b in params['b_values']:
                    row_values = []
                    for psi in params['psi_values']:
                        power = power_results[test_type][gamma][z_star][b][psi]
                        row_values.append(f'{power:{float_fmt}}'.replace('0.', '.'))
                    
                    row = f"{z_star} & {b} & " + ' & '.join(row_values) + " \\\\"
                    latex_lines.append(row)
            
            latex_lines.append("\\hline")
    
    # Wrap in table environment
    header = """\\begin{table}[htbp]
\\centering
\\caption{The Power of the Tests ($T = """ + str(params['T']) + """$, $\\alpha = """ + str(params['significance_level']) + """$)}
\\label{tab:power}
\\begin{tabular}{cc""" + 'c' * len(params['psi_values']) + """}
\\hline"""
    
    footer = """\\end{tabular}
\\end{table}"""
    
    return header + '\n' + '\n'.join(latex_lines) + '\n' + footer


def format_critical_values_table(critical_values: Dict[float, float],
                                  table_format: str = 'grid') -> str:
    """
    Format critical values as a table.
    
    Parameters
    ----------
    critical_values : dict
        Dictionary mapping significance levels to critical values
    table_format : str
        Table format
    
    Returns
    -------
    str
        Formatted table
    """
    data = [[f'{alpha}', f'{cv:.4f}'] 
            for alpha, cv in sorted(critical_values.items())]
    
    return tabulate(data, headers=['Significance Level (α)', 'Critical Value (a)'],
                    tablefmt=table_format)


def format_size_analysis_table(results: Dict,
                                table_format: str = 'grid',
                                float_fmt: str = '.3f') -> str:
    """
    Format size analysis results as a table.
    
    Parameters
    ----------
    results : dict
        Results from size_analysis function
    table_format : str
        Table format
    float_fmt : str
        Float format
    
    Returns
    -------
    str
        Formatted table
    """
    gamma_values = list(results['dynamic_cusum'].keys())
    
    headers = ['γ', 'Dynamic CUSUM', 'Dufour', 'Nominal Size']
    
    data = []
    for gamma in gamma_values:
        row = [
            f'{gamma:.1f}',
            f'{results["dynamic_cusum"][gamma]:{float_fmt}}',
            f'{results["dufour"][gamma]:{float_fmt}}',
            f'{results["nominal_size"]}'
        ]
        data.append(row)
    
    table = tabulate(data, headers=headers, tablefmt=table_format)
    
    header_text = f"""
Size Analysis Results
T = {results['T']}, n_simulations = {results['n_simulations']}
Nominal Size = {results['nominal_size']}

Note: True size should be ≤ nominal size under H₀.
Dufour test shows higher variation across γ values.
"""
    
    return header_text + '\n' + table


def print_test_summary(result: CUSUMResult):
    """
    Print a comprehensive summary of the test result.
    
    Parameters
    ----------
    result : CUSUMResult
        Result from CUSUM test
    """
    print("\n" + "="*60)
    print("CUSUM TEST FOR STRUCTURAL CHANGE IN DYNAMIC MODELS")
    print("Based on Krämer, Ploberger, and Alt (1988), Econometrica")
    print("="*60)
    print()
    print(format_test_result(result))
    print()
    
    if result.reject_null:
        print("CONCLUSION: There is statistically significant evidence of")
        print("            structural change at the specified significance level.")
    else:
        print("CONCLUSION: There is insufficient evidence to reject the null")
        print("            hypothesis of parameter constancy.")
    print()


def create_regression_diagnostics_table(result: CUSUMResult,
                                         additional_stats: Optional[Dict] = None,
                                         table_format: str = 'grid') -> str:
    """
    Create a comprehensive diagnostics table.
    
    Parameters
    ----------
    result : CUSUMResult
        CUSUM test result
    additional_stats : dict, optional
        Additional statistics to include
    table_format : str
        Table format
    
    Returns
    -------
    str
        Formatted diagnostics table
    """
    w = result.recursive_residuals
    w_clean = w[~np.isnan(w)]
    
    # Basic statistics of recursive residuals
    stats_data = [
        ['Mean of Recursive Residuals', f'{np.mean(w_clean):.4f}'],
        ['Std. Dev. of Recursive Residuals', f'{np.std(w_clean):.4f}'],
        ['Min', f'{np.min(w_clean):.4f}'],
        ['Max', f'{np.max(w_clean):.4f}'],
        ['Skewness', f'{_skewness(w_clean):.4f}'],
        ['Kurtosis', f'{_kurtosis(w_clean):.4f}'],
    ]
    
    if additional_stats:
        for key, value in additional_stats.items():
            if isinstance(value, float):
                stats_data.append([key, f'{value:.4f}'])
            else:
                stats_data.append([key, str(value)])
    
    return tabulate(stats_data, headers=['Diagnostic', 'Value'],
                    tablefmt=table_format)


def _skewness(x: np.ndarray) -> float:
    """Compute sample skewness."""
    n = len(x)
    m = np.mean(x)
    s = np.std(x, ddof=1)
    return np.sum((x - m)**3) / ((n - 1) * s**3)


def _kurtosis(x: np.ndarray) -> float:
    """Compute sample excess kurtosis."""
    n = len(x)
    m = np.mean(x)
    s = np.std(x, ddof=1)
    return np.sum((x - m)**4) / ((n - 1) * s**4) - 3


def export_results_to_csv(results: List[CUSUMResult],
                          labels: List[str],
                          filepath: str):
    """
    Export multiple test results to CSV.
    
    Parameters
    ----------
    results : list of CUSUMResult
        Test results
    labels : list of str
        Labels for each result
    filepath : str
        Output file path
    """
    import csv
    
    with open(filepath, 'w', newline='') as f:
        writer = csv.writer(f)
        
        # Header
        writer.writerow(['Label', 'Test_Type', 'T', 'K_plus_1', 'Statistic',
                        'Critical_Value', 'P_value', 'Reject_H0', 'Alpha', 'Sigma_hat'])
        
        # Data
        for label, result in zip(labels, results):
            writer.writerow([
                label,
                result.test_type,
                result.n_obs,
                result.n_regressors,
                result.statistic,
                result.critical_value,
                result.p_value,
                result.reject_null,
                result.significance_level,
                result.sigma_hat
            ])
