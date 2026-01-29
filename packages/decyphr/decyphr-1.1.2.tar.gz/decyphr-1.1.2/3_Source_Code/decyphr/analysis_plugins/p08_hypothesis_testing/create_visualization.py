# ==============================================================================
# FILE: 3_Source_Code/decyphr/analysis_plugins/p08_hypothesis_testing/create_visualization.py
# ==============================================================================
# PURPOSE: Generates rich HTML content for Advanced Hypothesis Testing, 
#          visualizing 15+ statistical tests using Antigravity UI.

import plotly.graph_objects as go
import pandas as pd
from typing import Dict, Any, Optional, List
from decyphr.utils.plotting import apply_antigravity_theme, get_theme_colors

# Get standard colors
THEME_COLORS = get_theme_colors()
P_VALUE_THRESHOLD = 0.05

# --- Antigravity Helper Functions ---

def _create_card(title: str, content: str, subtitle: str = "") -> str:
    """Wraps content in a standard Antigravity details-card."""
    if not content: return ""
    sub = f"<p style='color: var(--text-tertiary); font-size: 0.9em; margin-top: -10px; margin-bottom: 20px;'>{subtitle}</p>" if subtitle else ""
    return f"""
    <div class='details-card'>
        <h3>{title}</h3>
        {sub}
        {content}
    </div>
    """

def _create_table(headers: List[str], rows: List[List[Any]], overflow: bool = False) -> str:
    """Creates a standard transparent Antigravity table."""
    if not rows: return "<p style='color: var(--text-tertiary); font-style: italic;'>No relevant data.</p>"
    
    thead = "".join([f"<th>{h}</th>" for h in headers])
    tbody = ""
    for row in rows:
        tbody += "<tr>" + "".join([f"<td>{cell}</td>" for cell in row]) + "</tr>"
    
    wrapper_class = "table-responsive" if overflow else ""
    return f"""
    <div class='{wrapper_class}'>
        <table class='details-table'>
            <thead><tr>{thead}</tr></thead>
            <tbody>{tbody}</tbody>
        </table>
    </div>
    """

def format_p(p: float) -> str:
    if p < 0.001: return "<strong>< 0.001</strong>"
    val = f"{p:.4f}"
    return f"<strong>{val}</strong>" if p < 0.05 else val

def create_visuals(analysis_results: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Creates rich HTML content to display advanced hypothesis testing.
    """
    print("     -> Generating details for advanced hypothesis testing...")
    
    if "error" in analysis_results:
        return {"error": analysis_results["error"]}
    
    all_details_html: List[str] = []

    try:
        # Extract Results
        normality_tests = analysis_results.get("normality_tests", [])
        variance_tests = analysis_results.get("variance_tests", [])
        group_tests = analysis_results.get("group_comparison_tests", [])
        cat_tests = analysis_results.get("categorical_tests", [])

        # --- 1. Normality Tests (Shapiro, KS) ---
        if normality_tests:
            rows = []
            for t in normality_tests:
                status = "🟢" if t['conclusion'] == "Likely Normal" else "🔴"
                rows.append([
                    f"<code>{t['variable']}</code>",
                    format_p(t['shapiro_p']),
                    format_p(t['ks_p']),
                    status + " " + t['conclusion']
                ])
            
            all_details_html.append(_create_card("Normality Checks (Distribution)", 
                _create_table(["Variable", "Shapiro-Wilk (p)", "KS Test (p)", "Conclusion"], rows),
                "Testing if numeric variables follow a Normal Distribution (Gaussian). Important for choosing between Parametric (T-Test) and Non-Parametric (Mann-Whitney) tests."))

        # --- 2. Group Comparisons (T-Tests / ANOVA / Kruskal) ---
        if group_tests:
            # Sort by significance (Mann-Whitney p usually)
            sig_groups = sorted([g for g in group_tests if g['significant']], key=lambda x: x.get('non_parametric_p', 1.0))[:10]
            
            rows = []
            for t in sig_groups:
                eff = f"{t.get('effect_size_d', 0):.2f}" if t.get('effect_size_d') is not None else "N/A"
                rows.append([
                    f"<code>{t['numeric']}</code> by <code>{t['group']}</code>",
                    t['comparison'],
                    f"{t['parametric_test']} ({format_p(t['parametric_p'])})<br>{t['non_parametric_test']} ({format_p(t['non_parametric_p'])})",
                    eff,
                    "Different"
                ])
                
            all_details_html.append(_create_card("Significant Group Differences",
                _create_table(["Comparison", "Groups", "Tests (Parametric vs Robust)", "Effect Size (Cohen's d)", "Result"], rows),
                "Top significant differences in numeric means across categorical groups."))

        # --- 3. Independence Tests (Chi-Square) ---
        if cat_tests:
            sig_cats = [c for c in cat_tests if c['significant']][:10]
            rows = []
            for t in sig_cats:
                rows.append([
                     f"<code>{t['var1']}</code> & <code>{t['var2']}</code>",
                     t['test'],
                     format_p(t['p_value']),
                     "Dependent (Associated)"
                ])
            
            if rows:
                all_details_html.append(_create_card("Categorical Associations",
                    _create_table(["Variable Pair", "Test", "P-Value", "Conclusion"], rows),
                    "Statistically significant associations between categorical fields."))

        final_html = f"<div class='details-grid' style='display: flex; flex-direction: column; gap: 24px;'>{''.join(all_details_html)}</div>"
        
        print("     ... Details for hypothesis testing complete.")
        return {
            "details_html": final_html,
            "visuals": [] 
        }

    except Exception as e:
        error_message = f"Failed during hypothesis visualization: {e}"
        print(f"     ... {error_message}")
        import traceback
        traceback.print_exc()
        return {"error": error_message}