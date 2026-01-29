# ==============================================================================
# FILE: 3_Source_Code/decyphr/analysis_plugins/p05_missing_values/create_visualization.py
# ==============================================================================
# PURPOSE: Generates rich HTML content for Advanced Missing Value Analysis, 
#          visualizing 15+ features using Antigravity UI.

import plotly.graph_objects as go
import plotly.express as px
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

def create_visuals(analysis_results: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Creates rich HTML content to display advanced missing values analysis.
    """
    print("     -> Generating details & visualizations for advanced missing values...")
    
    if "error" in analysis_results:
        return {"error": analysis_results["error"]}
    if "message" in analysis_results and "No missing values" in analysis_results["message"]:
        return {"message": "No missing values found in the dataset. Great job!"}

    all_details_html: List[str] = []
    all_visuals: List[go.Figure] = []

    try:
        # Extract Results
        col_stats = analysis_results.get("column_stats", {})
        nullity_corr = analysis_results.get("nullity_correlation", {})
        mcar = analysis_results.get("mcar_analysis", {})
        streaks = analysis_results.get("null_streaks", {})
        co_occurrence = analysis_results.get("co_occurrence", {})
        drop_impact = analysis_results.get("drop_impact", {})
        imputation_impact = analysis_results.get("imputation_impact", {})
        empty_strings = analysis_results.get("empty_strings_distinct", {})
        
        # --- 1. Overview & Impact ---
        impact_rows = [
            ["Rows Lost if Dropped", f"{drop_impact.get('rows_lost', 0):,} ({drop_impact.get('percentage_lost', 0)}%)"],
            ["MCAR Investigation", mcar.get("message", "N/A")],
            ["Empty Strings (Hidden Nulls)", f"{sum(empty_strings.values()):,} across {len(empty_strings)} columns"]
        ]
        
        all_details_html.append(_create_card("Missingness Overview", 
             _create_table(["Metric", "Result"], impact_rows), 
             "High-level assessment of data completeness and potential bias mechanisms."))

        # --- 2. Detailed Column Stats Table ---
        if col_stats:
            sorted_cols = sorted(col_stats.items(), key=lambda x: x[1]['percentage'], reverse=True)
            stat_rows = []
            for col, data in sorted_cols:
                # Add extra context if available
                streak_val = streaks.get(col, 0)
                imp_diff = imputation_impact.get(col, {}).get('diff_percent', 0)
                imp_text = f"{imp_diff}% shift" if imp_diff > 0 else "-"
                
                stat_rows.append([
                    f"<code>{col}</code>", 
                    f"{data['count']:,}", 
                    f"{data['percentage']}%",
                    f"{streak_val}",
                    imp_text
                ])
            
            all_details_html.append(_create_card("Column-wise Missingness Analysis",
                _create_table(["Column", "Missing Count", "% Missing", "Max Null Streak", "Mean Imputation Bias"], stat_rows),
                "Breakdown of missing data intensity and characteristics per column."))

        # --- 3. Nullity Correlation Heatmap (Visual) ---
        if nullity_corr:
            # Prepare data for heatmap
            df_corr = pd.DataFrame(nullity_corr)
            if not df_corr.empty and df_corr.shape[0] > 1:
                fig = px.imshow(df_corr, text_auto=".2f", aspect="auto",
                               color_continuous_scale="RdBu_r", zmin=-1, zmax=1)
                fig = apply_antigravity_theme(fig)
                fig.update_layout(title="Nullity Correlation Matrix", height=400)
                all_visuals.append(fig)
                
                all_details_html.append(_create_card("Nullity Correlation", 
                    "<p>This heatmap shows how the presence of missing values in one column correlates with another.</p><div class='plot-placeholder-target'></div>",
                    "Understanding if missing values tend to occur together (structural missingness)."))

        # --- 4. Co-occurrence Summary ---
        if co_occurrence:
            # Sort by count
            co_sorted = sorted(co_occurrence.items(), key=lambda x: x[1], reverse=True)[:10] # Top 10
            co_rows = [[k, f"{v:,}"] for k, v in co_sorted]
            all_details_html.append(_create_card("Common Missing Pairs",
                _create_table(["Column Pair", "Co-occurrence Count"], co_rows),
                "Top pairs of columns that are simultaneously missing."))

        final_html = f"<div class='details-grid' style='display: flex; flex-direction: column; gap: 24px;'>{''.join(all_details_html)}</div>"

        print("     ... Details and visualizations for advanced missing values complete.")
        return {
            "details_html": final_html,
            "visuals": all_visuals
        }

    except Exception as e:
        error_message = f"Failed during missing values visualization: {e}"
        print(f"     ... {error_message}")
        import traceback
        traceback.print_exc()
        return {"error": error_message}