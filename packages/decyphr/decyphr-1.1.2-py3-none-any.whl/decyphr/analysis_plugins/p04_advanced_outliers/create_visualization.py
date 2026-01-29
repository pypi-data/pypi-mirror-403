# ==============================================================================
# FILE: 3_Source_Code/decyphr/analysis_plugins/p04_advanced_outliers/create_visualization.py
# ==============================================================================
# PURPOSE: Generates rich HTML content for Advanced Outlier Analysis, visualizing 
#          15+ statistical and ML-based anomaly detection metrics using Antigravity UI.

import plotly.graph_objects as go
from typing import Dict, Any, Optional, List, Tuple
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
    if not rows: return "<p style='color: var(--text-tertiary); font-style: italic;'>No data available.</p>"
    
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

def create_visuals(ddf, analysis_results: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Creates rich HTML content to display advanced outlier analysis.
    """
    print("     -> Generating details & visualizations for advanced outlier analysis...")
    
    if "error" in analysis_results:
        return {"error": analysis_results["error"]}
    
    # Extract global analysis (ML models)
    global_stats = analysis_results.pop("global_analysis", {})
    
    all_details_html: List[str] = []
    all_visuals: List[go.Figure] = []

    try:
        # --- 1. Global Anomaly Summary (ML Models) ---
        if global_stats:
            ml_rows = [
                ["Isolation Forest (Global)", f"{global_stats.get('isolation_forest_count', 0):,}"],
                ["Local Outlier Factor (Density)", f"{global_stats.get('lof_count', 0):,}"],
                ["DBSCAN (Clustering)", f"{global_stats.get('dbscan_count', 0):,}"]
            ]
            
            top_anomalies = global_stats.get('top_anomalies', [])
            preview_html = ""
            if top_anomalies:
                # Create a mini table for top 5 anomalies
                import pandas as pd
                preview_df = pd.DataFrame(top_anomalies)
                preview_html = "<div style='margin-top: 24px;'><h4>Top 5 Most Anomalous Records</h4><div class='table-responsive'>" + \
                               preview_df.to_html(classes='preview-table', index=False, border=0, float_format=lambda x: f'{x:.2f}') + \
                               "</div></div>"

            all_details_html.append(_create_card("Global Anomaly Detection (ML)", 
                f"<div style='display: grid; grid-template-columns: 1fr 2fr; gap: 32px;'><div>{_create_table(['Method', 'Outliers Detected'], ml_rows)}</div><div>{preview_html}</div></div>",
                "Results from diverse machine learning algorithms scanning the entire dataset structure."))

        # --- 2. Univariate Analysis (Column by Column) ---
        # We'll create a grid of cards for each column
        column_cards = []
        
        for col_name, stats in analysis_results.items():
            if not isinstance(stats, dict) or col_name == "global_analysis": continue # potential safety check
            if "iqr_stats" not in stats: continue

            print(f"        - Creating details & box plot for '{col_name}'")
            
            # Extract stats
            iqr = stats["iqr_stats"]
            z_count = stats.get("z_score_count", 0)
            mod_z_count = stats.get("modified_z_score_count", 0)
            is_heavy = stats.get("is_heavy_tailed", False)

            # Create Table
            rows = [
                ["IQR Method", f"{iqr['count']:,} ({iqr['percentage']}%)"],
                ["Z-Score (>3σ)", f"{z_count:,}"],
                ["Modified Z-Score (>3.5)", f"{mod_z_count:,}"],
                ["Distribution Shape", "Heavy Tailed" if is_heavy else "Normal-like"]
            ]
            table_html = _create_table(["Method", "Outliers"], rows)
            
            # create container for plot placeholder
            # Note: We rely on the layout builder to inject plots, but we can structure the HTML
            # The 'create_visualization' contract returns visuals list. 
            # In builder.py, visuals are placed into placeholders plot-{section}-{i}
            
            card_html = f"""
            <div class='details-card'>
                <h4>Analysis: <code>{col_name}</code></h4>
                <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 24px; align-items: start;'>
                    <div>{table_html}</div>
                    <div class="plot-placeholder-target"></div> 
                </div>
            </div>
            """
            # Note: The 'plot-placeholder-target' is a marker. 
            # Actually, standard builder just appends plots at the bottom of the section usually. 
            # TO FIX: We want plots integrated. 
            # New Strategy: We return strict HTML structure. 
            # But the builder.py iterates visuals and puts them in a grid at the bottom. 
            # For V2, let's keep the box plots simple and let them be at the bottom for now, OR 
            # we can suppress the auto-grid in builder and do manual placement.
            # Reviewing builder.py... it puts `analysis-card` at bottom.
            # Let's Stick to the standard: Details first, then plots.
            
            column_cards.append([col_name, table_html])

            # Create Box Plot
            fig = go.Figure(data=[go.Box(
                y=ddf[col_name].compute(), # Note: compute() here is expensive for loop, verify if needed
                name=col_name,
                marker_color=THEME_COLORS["primary_accent"],
                boxpoints='outliers',
                jitter=0.3
            )])
            fig = apply_antigravity_theme(fig)
            fig.update_layout(title_text=f'{col_name}: Distribution & Outliers', height=350, margin=dict(l=40, r=40, t=60, b=40))
            all_visuals.append(fig)

        # Assemble Column Cards (2 per row Grid)
        if column_cards:
            grid_html = "<div class='details-grid'>"
            for col_name, table in column_cards:
                 grid_html += f"<div class='details-card'><h4><code>{col_name}</code> Stats</h4>{table}</div>"
            grid_html += "</div>"
            all_details_html.append(grid_html)

        
        final_html = f"<div class='details-container'>{''.join(all_details_html)}</div>"
            
        print("     ... Details and visualizations for advanced outlier analysis complete.")
        return {
            "details_html": final_html,
            "visuals": all_visuals
        }

    except Exception as e:
        error_message = f"Failed during outlier visualization: {e}"
        print(f"     ... {error_message}")
        import traceback
        traceback.print_exc()
        return {"error": error_message}