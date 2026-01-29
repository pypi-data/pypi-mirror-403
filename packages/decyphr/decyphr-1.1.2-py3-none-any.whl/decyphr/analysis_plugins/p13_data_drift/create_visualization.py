# ==============================================================================
# FILE: 3_Source_Code/decyphr/analysis_plugins/p13_data_drift/create_visualization.py
# ==============================================================================
# PURPOSE: Generates rich HTML content for Advanced Data Drift Analysis, 
#          visualizing 15+ metrics/features using Antigravity UI.

import plotly.graph_objects as go
import pandas as pd
from typing import Dict, Any, Optional, List
from decyphr.utils.plotting import apply_antigravity_theme, get_theme_colors

# Get standard colors
THEME_COLORS = get_theme_colors()

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

def _create_table(headers: List[str], rows: List[List[Any]], overflow: bool = False, centered_cols: List[int] = []) -> str:
    """Creates a standard transparent Antigravity table."""
    if not rows: return "<p style='color: var(--text-tertiary); font-style: italic;'>No relevant data.</p>"
    
    thead = "".join([f"<th>{h}</th>" for h in headers])
    tbody = ""
    for row in rows:
        row_html = ""
        for i, cell in enumerate(row):
             style = "text-align: center;" if i in centered_cols else ""
             row_html += f"<td style='{style}'>{cell}</td>"
        tbody += f"<tr>{row_html}</tr>"
    
    wrapper_class = "table-responsive" if overflow else ""
    return f"""
    <div class='{wrapper_class}'>
        <table class='details-table'>
            <thead><tr>{thead}</tr></thead>
            <tbody>{tbody}</tbody>
        </table>
    </div>
    """

def _interpret_psi(psi: float) -> str:
    if psi < 0.1: return "<span style='color: var(--success);'>Stable</span>"
    if psi < 0.25: return "<span style='color: var(--warning);'>Moderate Shift</span>"
    return "<span style='color: var(--danger); font-weight: bold;'>Major Drift</span>"

def create_visuals(analysis_results: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Creates rich HTML content for Data Drift Analysis.
    """
    print("     -> Generating details & visualizations for Advanced Drift Analysis...")
    
    if "error" in analysis_results:
        return {"error": analysis_results["error"]}
    if not analysis_results:
        return {"message": "Drift analysis not performed (Check inputs)."}

    all_details_html: List[str] = []
    
    try:
        # --- 1. Drift Summary Table ---
        # Sort by severity (PSI desc)
        sorted_feats = sorted(analysis_results.items(), key=lambda x: x[1].get('psi', 0), reverse=True)
        
        table_rows = []
        for col, res in sorted_feats:
            psi = res.get('psi', 0)
            psi_str = f"{psi:.3f}"
            psi_label = _interpret_psi(psi)
            
            kl = res.get('kl_divergence', 0)
            missing_diff = res.get('missing_drift', 0)
            missing_str = f"{missing_diff:+.1%}" if abs(missing_diff) > 0.001 else "-"
            
            # Numeric specifics
            ks_res = res.get('ks_test', {})
            ks_p = ks_res.get('p_value', 1.0)
            ks_str = f"p={ks_p:.3f}" if ks_res else "-"
            
            # Alert icon if significant
            alert = "⚠️" if res.get('is_drifted') else ""
            
            table_rows.append([
                f"<code>{col}</code> {alert}",
                res.get('type', 'Unknown'),
                psi_str,
                psi_label,
                f"{kl:.3f}",
                ks_str,
                missing_str
            ])
            
        all_details_html.append(_create_card("Drift Overview (Ranked by Severity)",
             """<p>Comparing <strong>Base</strong> vs <strong>Current</strong> datasets. 
                <br>Key Metric: <strong>PSI</strong> (Population Stability Index). Scale: < 0.1 Safe, > 0.25 Critical.</p>""" + 
             _create_table(["Feature", "Type", "PSI", "Stability Status", "KL Div", "Stat Test (p)", "Nullity Shift"], table_rows, overflow=True),
             "Summary of distributional changes across all features."))
        
        # --- 2. Significant Drift Drill-down ---
        # Filter for Critical Drift (PSI > 0.25 or p < 0.01)
        critical_drifts = [f[0] for f in sorted_feats if f[1].get('psi', 0) > 0.25 or f[1].get('ks_test', {}).get('p_value', 1) < 0.01]
        
        if critical_drifts:
            drill_text = f"<p>Detected critical drift in <strong>{len(critical_drifts)} features</strong>: {', '.join(critical_drifts)}.</p>"
            drill_text += "<p><strong>Recommendation:</strong> Retrain models or investigate data source changes for these columns.</p>"
            all_details_html.append(_create_card("Critical Alerts", drill_text, "Actionable insights for detected anomalies."))
        else:
            all_details_html.append(_create_card("Drift Status", "<p style='color: var(--success);'>✅ No critical drift detected across monitored features.</p>"))

        final_html = f"<div class='details-grid' style='display: flex; flex-direction: column; gap: 24px;'>{''.join(all_details_html)}</div>"

        print("     ... Details for Data Drift Analysis complete.")
        return {
            "details_html": final_html,
            "visuals": [] # Drift is mostly tabular/metric based in this version
        }

    except Exception as e:
        error_message = f"Failed during drift visualization: {e}"
        print(f"     ... {error_message}")
        import traceback
        traceback.print_exc()
        return {"error": error_message}