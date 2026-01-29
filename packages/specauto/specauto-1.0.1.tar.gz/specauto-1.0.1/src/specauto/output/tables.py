"""
Publication-Ready Output Tables

Generates formatted tables for publication in academic journals.
Uses the tabulate library for high-quality table formatting.

Reference:
    Godfrey, L. G. (1987). The Review of Economics and Statistics, 69(1), 128-134.
"""

import numpy as np
from tabulate import tabulate
from typing import Optional, List, Dict, Any


def format_significance_stars(p_value: float) -> str:
    """
    Format p-value with significance stars.
    
    *** p < 0.01
    **  p < 0.05  
    *   p < 0.10
    """
    if p_value < 0.01:
        return "***"
    elif p_value < 0.05:
        return "**"
    elif p_value < 0.10:
        return "*"
    return ""


def format_pvalue(p_value: float, precision: int = 4) -> str:
    """Format p-value for display."""
    if p_value < 0.0001:
        return "<0.0001"
    return f"{p_value:.{precision}f}"


def format_autospec_results(results, tablefmt: str = "fancy_grid") -> str:
    """
    Generate publication-ready formatted output for AutoSpec results.
    
    Parameters
    ----------
    results : AutoSpecResults
        Complete results from AutoSpec.run_full_strategy()
    tablefmt : str
        Table format for tabulate (default: "fancy_grid")
        Options: "grid", "fancy_grid", "pipe", "latex", "latex_booktabs"
        
    Returns
    -------
    str
        Formatted table string suitable for publication
    """
    lines = []
    
    # Header
    lines.append("=" * 80)
    lines.append("     GODFREY (1987) AUTOSPEC TEST STRATEGY RESULTS")
    lines.append("     Discriminating Between Autocorrelation and Misspecification")
    lines.append("=" * 80)
    lines.append("")
    
    # OLS Summary
    ols = results.ols_result
    ols_data = [
        ["Number of Observations", ols.n],
        ["Number of Regressors", ols.k],
        ["R-squared", f"{ols.r_squared:.4f}"],
        ["Adjusted R-squared", f"{ols.adj_r_squared:.4f}"],
        ["Residual Std. Error", f"{np.sqrt(ols.sigma_squared):.4f}"]
    ]
    
    lines.append("MODEL SUMMARY")
    lines.append("-" * 40)
    lines.append(tabulate(ols_data, tablefmt="plain"))
    lines.append("")
    
    # Main Test Results Table
    misspec = results.misspec_result
    ar_struct = results.ar_structure_result
    serial = results.serial_indep_result
    
    test_data = [
        [
            "Misspecification",
            f"χ²({misspec.df})",
            f"{misspec.statistic:.4f}",
            format_pvalue(misspec.p_value) + format_significance_stars(misspec.p_value),
            f"{misspec.critical_value_5:.4f}",
            "Reject" if misspec.reject_5 else "Do not reject"
        ],
        [
            f"AR Structure (AR(1) vs AR({1 + ar_struct.q}))",
            f"F({ar_struct.df1},{ar_struct.df2})",
            f"{ar_struct.f_statistic:.4f}",
            format_pvalue(ar_struct.p_value) + format_significance_stars(ar_struct.p_value),
            f"{ar_struct.critical_value_5:.4f}",
            "Reject" if ar_struct.reject_5 else "Do not reject"
        ],
        [
            "Serial Independence",
            "t",
            f"{serial.t_statistic:.4f}",
            format_pvalue(serial.t_pvalue) + format_significance_stars(serial.t_pvalue),
            f"±{serial.t_critical_5:.4f}",
            "Reject" if serial.reject_t_5 else "Do not reject"
        ]
    ]
    
    headers = ["Test", "Statistic", "Value", "p-value", "Critical (5%)", "Decision"]
    
    lines.append("SEQUENTIAL TEST RESULTS (at 5% significance level)")
    lines.append("-" * 80)
    lines.append(tabulate(test_data, headers=headers, tablefmt=tablefmt))
    lines.append("")
    
    # Additional Statistics
    add_stats = [
        ["Durbin-Watson Statistic", f"{serial.dw_statistic:.4f}"],
        ["Estimated ρ (AR(1) coefficient)", f"{serial.rho_estimate:.4f}"],
        ["HAC Truncation Parameter", f"{misspec.truncation_j}"],
        ["Test Variables Type", misspec.test_variable_type]
    ]
    
    lines.append("ADDITIONAL STATISTICS")
    lines.append("-" * 40)
    lines.append(tabulate(add_stats, tablefmt="plain"))
    lines.append("")
    
    # Final Diagnosis
    lines.append("=" * 80)
    lines.append("DIAGNOSIS")
    lines.append("=" * 80)
    lines.append(f"Adopted Hypothesis: {results.adopted_hypothesis}")
    lines.append(f"Conclusion: {results.conclusion}")
    lines.append("")
    lines.append("Recommendation:")
    lines.append(f"  {results.recommendation}")
    lines.append("")
    
    # Significance codes
    lines.append("-" * 80)
    lines.append("Signif. codes: *** p<0.01, ** p<0.05, * p<0.10")
    lines.append("")
    lines.append("Reference: Godfrey, L.G. (1987). The Review of Economics and Statistics, 69(1), 128-134.")
    lines.append("=" * 80)
    
    return "\n".join(lines)


def format_test_summary(results, tablefmt: str = "fancy_grid") -> str:
    """
    Generate a compact summary table of test results.
    
    Parameters
    ----------
    results : AutoSpecResults
        Complete results from AutoSpec
    tablefmt : str
        Table format
        
    Returns
    -------
    str
        Compact summary table
    """
    misspec = results.misspec_result
    ar_struct = results.ar_structure_result
    serial = results.serial_indep_result
    
    data = [
        ["(a) vs (b): Misspecification", 
         f"{misspec.statistic:.3f}", 
         f"{misspec.p_value:.4f}",
         "Yes" if misspec.reject_5 else "No"],
        [f"(b) vs (c): AR({1 + ar_struct.q}) vs AR(1)", 
         f"{ar_struct.f_statistic:.3f}", 
         f"{ar_struct.p_value:.4f}",
         "Yes" if ar_struct.reject_5 else "No"],
        ["(c) vs (d): AR(1) vs Independence", 
         f"{serial.t_statistic:.3f}", 
         f"{serial.t_pvalue:.4f}",
         "Yes" if serial.reject_t_5 else "No"]
    ]
    
    headers = ["Hypothesis Test", "Statistic", "p-value", "Reject H₀?"]
    
    table = tabulate(data, headers=headers, tablefmt=tablefmt)
    
    conclusion = f"\nAdopted: {results.adopted_hypothesis} - {results.conclusion}"
    
    return table + conclusion


def format_critical_values(critical_values_df, tablefmt: str = "fancy_grid") -> str:
    """
    Format critical values table for publication.
    
    Parameters
    ----------
    critical_values_df : pd.DataFrame
        DataFrame with critical values from simulation
    tablefmt : str
        Table format
        
    Returns
    -------
    str
        Formatted critical values table
    """
    lines = []
    lines.append("SIMULATED CRITICAL VALUES")
    lines.append("-" * 60)
    lines.append("Monte Carlo simulation under the null hypothesis")
    lines.append("")
    
    table = tabulate(
        critical_values_df, 
        headers='keys', 
        tablefmt=tablefmt,
        floatfmt=".4f"
    )
    lines.append(table)
    
    return "\n".join(lines)


def format_latex_table(results, caption: str = None, label: str = None) -> str:
    """
    Generate LaTeX table for publication.
    
    Parameters
    ----------
    results : AutoSpecResults
        Complete results from AutoSpec
    caption : str, optional
        Table caption
    label : str, optional
        Table label for referencing
        
    Returns
    -------
    str
        LaTeX table code
    """
    misspec = results.misspec_result
    ar_struct = results.ar_structure_result
    serial = results.serial_indep_result
    
    lines = []
    lines.append(r"\begin{table}[htbp]")
    lines.append(r"\centering")
    if caption:
        lines.append(rf"\caption{{{caption}}}")
    if label:
        lines.append(rf"\label{{{label}}}")
    
    lines.append(r"\begin{tabular}{lcccc}")
    lines.append(r"\hline\hline")
    lines.append(r"Test & Statistic & Value & $p$-value & Decision \\")
    lines.append(r"\hline")
    
    # Misspecification
    stars = format_significance_stars(misspec.p_value)
    lines.append(
        rf"Misspecification & $\chi^2({misspec.df})$ & "
        rf"{misspec.statistic:.4f} & {misspec.p_value:.4f}{stars} & "
        rf"{'Reject' if misspec.reject_5 else 'Do not reject'} \\"
    )
    
    # AR Structure
    stars = format_significance_stars(ar_struct.p_value)
    lines.append(
        rf"AR Structure & $F({ar_struct.df1},{ar_struct.df2})$ & "
        rf"{ar_struct.f_statistic:.4f} & {ar_struct.p_value:.4f}{stars} & "
        rf"{'Reject' if ar_struct.reject_5 else 'Do not reject'} \\"
    )
    
    # Serial Independence
    stars = format_significance_stars(serial.t_pvalue)
    lines.append(
        rf"Serial Independence & $t$ & "
        rf"{serial.t_statistic:.4f} & {serial.t_pvalue:.4f}{stars} & "
        rf"{'Reject' if serial.reject_t_5 else 'Do not reject'} \\"
    )
    
    lines.append(r"\hline")
    lines.append(rf"\multicolumn{{5}}{{l}}{{Adopted hypothesis: {results.adopted_hypothesis}}} \\")
    lines.append(rf"\multicolumn{{5}}{{l}}{{{results.conclusion}}} \\")
    lines.append(r"\hline\hline")
    lines.append(r"\end{tabular}")
    
    lines.append(r"\begin{tablenotes}")
    lines.append(r"\small")
    lines.append(r"\item Note: *** $p<0.01$, ** $p<0.05$, * $p<0.10$.")
    lines.append(r"\end{tablenotes}")
    
    lines.append(r"\end{table}")
    
    return "\n".join(lines)
