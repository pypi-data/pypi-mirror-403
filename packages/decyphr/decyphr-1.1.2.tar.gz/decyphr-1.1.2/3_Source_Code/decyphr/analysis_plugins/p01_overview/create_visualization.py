# ==============================================================================
# FILE: 3_Source_Code/decyphr/analysis_plugins/p01_overview/create_visualization.py
# ==============================================================================
# PURPOSE: Generates rich HTML content for the Overview section, visualizing
#          28+ features including Health Score, SQL Schema, and Data Preview.

import plotly.graph_objects as go
import pandas as pd
from typing import Dict, Any, Optional, List

def _create_html_table(data_dict: Dict[str, Any], title: str = "") -> str:
    """Creates a structured HTML table with the new Antigravity CSS."""
    if not data_dict:
        return ""
    
    rows = ""
    for k, v in data_dict.items():
        # Clean key names for display
        clean_key = k.replace('_', ' ').title()
        rows += f"<tr><td>{clean_key}</td><td><strong>{v}</strong></td></tr>"
    
    html = f"""
    <div class="details-card">
        <h3>{title}</h3>
        <table class="details-table">
            <thead>
                <tr>
                    <th style="width: 40%">Metric</th>
                    <th>Value</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
    </div>
    """
    return html

def _create_list_card(title: str, items: List[str], empty_msg: str = "None") -> str:
    """Helper to generate a card with a bulleted list."""
    html = f"<div class='details-card'><h3>{title}</h3>"
    if not items:
        html += f"<p style='color: var(--text-tertiary);'>{empty_msg}</p></div>"
        return html
    html += "<ul style='padding-left: 20px; line-height: 1.8; color: var(--text-secondary);'>"
    for item in items:
        html += f"<li>{item}</li>"
    html += "</ul></div>"
    return html

def _create_alert_card(alerts: List[str]) -> str:
    """Helper to generate a styled alert box (Antigravity Style)."""
    if not alerts: return ""
    
    # Using the warning colors from CSS variables
    html = "<div style='background: var(--status-warning-bg); color: var(--status-warning-text); padding: 32px; border-radius: var(--radius-card); margin-bottom: 32px;'>"
    html += "<h3 style='margin-bottom: 16px; font-weight: 500;'>Data Alerts</h3>"
    html += "<ul style='padding-left: 20px; margin-bottom: 0;'>"
    for alert in alerts:
        html += f"<li>{alert}</li>"
    html += "</ul></div>"
    return html


def _create_code_card(title: str, code: str, lang: str = "sql") -> str:
    """Helper to generate a code block card."""
    if not code: return ""
    html = f"<div class='details-card'><h3>{title}</h3>"
    html += f"<pre style='padding: 24px; overflow-x: auto; font-family: monospace; font-size: 0.9em;'><code>{code}</code></pre></div>"
    return html

def _create_dataframe_preview(title: str, data_list: List[Dict]) -> str:
    """Helper to create a scrollable table from a list of dicts (records)."""
    if not data_list: return ""
    df = pd.DataFrame(data_list)
    html = f"<div class='details-card'><h3>{title}</h3>"
    html += "<div class='table-responsive'>"
    html += df.to_html(classes='preview-table', index=False, border=0)
    html += "</div></div>"
    return html

def create_visuals(analysis_results: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Creates the rich HTML content for the overview section.
    """
    print("     -> Generating details & visualizations for overview...")
    
    if "error" in analysis_results:
        return {"error": analysis_results["error"]}

    try:
        # --- Extract Data ---
        stats = analysis_results.get("dataset_stats", {})
        struct = analysis_results.get("structural_analysis", {})
        variable_types = analysis_results.get("variable_types", {})
        preview = analysis_results.get("data_preview", {})

        # --- 1. Key Metrics (Top Row) ---
        health_score = stats.pop("Health Score", "N/A")
        density_score = stats.pop("Dataset Density", "N/A")
        
        # --- 2. HTML Components ---
        
        # Alerts
        alerts_html = _create_alert_card(struct.get("Alerts", []))
        
        # Stats Table
        stats_display = {"Health Score": health_score, "Dataset Density": density_score, **stats}
        stats_html = _create_html_table(stats_display, "Dataset Statistics") # Swapped args to match func sig: dict, title
        
        # Variable Types
        filtered_types = {k: v for k, v in variable_types.items() if v > 0}
        types_html = _create_html_table(filtered_types, "Variable Types")
        
        # Optimization Tips
        tips_html = _create_list_card("Optimization Tips", struct.get("Optimization Tips", []), "No optimizations found.")
        
        # Structural Insights
        dup_cols = struct.get("Duplicate Columns", [])
        pii_risks = struct.get("PII Risks", [])
        composite_keys = struct.get("Composite Keys", [])
        
        insights_data = {}
        if dup_cols: insights_data["Duplicate Columns"] = ", ".join(dup_cols)
        if pii_risks: insights_data["PII Risks"] = ", ".join(pii_risks)
        if composite_keys: insights_data["Composite Keys"] = "<br>".join(composite_keys)
        
        insights_html = _create_html_table(insights_data, "Structural Insights") if insights_data else ""
        
        # SQL Schema
        schema_html = _create_code_card("Inferred SQL Schema", struct.get("SQL Schema", ""), "sql")
        
        # Data Preview (Head)
        preview_html = _create_dataframe_preview("Data Preview (First 5 Rows)", preview.get("head", []))
        
        # [NEW] Data Preview (Tail & Random)
        tail_html = _create_dataframe_preview("Data Preview (Last 5 Rows)", preview.get("tail", []))
        random_html = _create_dataframe_preview("Data Preview (Random 5 Rows)", preview.get("random", []))

        # --- 3. Assemble Layout ---
        
        final_html = f"""
        <div class='overview-container'>
            {alerts_html}
            <div class='details-grid'>
                {stats_html}
                {types_html}
            </div>
            <div class='details-grid'>
                {insights_html}
                {tips_html}
            </div>
            {schema_html}
            {preview_html}
            {tail_html}
            {random_html}
        </div>
        """
        
        return {
            "details_html": final_html,
            "visuals": [] # No plotly charts needed for overview yet
        }

    except Exception as e:
        error_message = f"Failed during overview visualization: {e}"
        print(f"     ... {error_message}")
        import traceback
        traceback.print_exc()
        return {"error": error_message}