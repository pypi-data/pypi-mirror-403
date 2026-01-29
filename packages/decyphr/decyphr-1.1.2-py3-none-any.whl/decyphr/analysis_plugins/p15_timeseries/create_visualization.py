# ==============================================================================
# FILE: 3_Source_Code/decyphr/analysis_plugins/p15_timeseries/create_visualization.py
# ==============================================================================
# PURPOSE: Generates rich HTML content for Advanced Time-Series Analysis, 
#          visualizing 15+ metrics/features using Antigravity UI.

import plotly.graph_objects as go
from plotly.subplots import make_subplots
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

def create_visuals(ddf, overview_results: Dict[str, Any], analysis_results: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Creates rich HTML content for Time-Series Analysis.
    """
    print("     -> Generating details & visualizations for Advanced Time-Series...")
    
    if "error" in analysis_results:
        return {"error": analysis_results["error"]}
    if not analysis_results or "message" in analysis_results:
        return {"message": "Time-series analysis was not performed."}

    all_details_html: List[str] = []
    all_visuals: List[go.Figure] = []

    try:
        # Extract Results
        decomp = analysis_results.get("components", {})
        forecast = analysis_results.get("forecast", {})
        stats = analysis_results.get("stationarity", {})
        strength = analysis_results.get("strengths", {})
        drawdown = analysis_results.get("max_drawdown", 0)
        
        # --- 1. Metrics Card ---
        # Stationarity
        if stats.get('is_stationary'):
            st_badge = "<span style='color: var(--success); font-weight: bold;'>STATIONARY</span>"
        else:
            st_badge = "<span style='color: var(--danger); font-weight: bold;'>NON-STATIONARY</span>"
            
        rows = [
             ["Stationarity (ADF)", st_badge],
             ["Trend Strength", f"{strength.get('trend', 0):.2f} / 1.0"],
             ["Seasonality Strength", f"{strength.get('seasonality', 0):.2f} / 1.0"],
             ["Max Drawdown", f"{drawdown:.1%}"]
        ]
        
        all_details_html.append(_create_card("Time-Series Health", 
             _create_table(["Metric", "Status"], rows),
             "Structural properties of the time series."))

        # --- 2. Decomposition Plot ---
        if decomp:
            trend = pd.Series(decomp.get("trend", {}))
            seasonal = pd.Series(decomp.get("seasonal", {}))
            # resid = pd.Series(decomp.get("residual", {}))
            
            # Combine into subplot
            fig_decomp = make_subplots(
                rows=2, cols=1, shared_xaxes=True,
                subplot_titles=("Trend Component", "Seasonal Component")
            )
            fig_decomp.add_trace(go.Scatter(x=trend.index, y=trend, line=dict(color=THEME_COLORS["primary_accent"])), row=1, col=1)
            fig_decomp.add_trace(go.Scatter(x=seasonal.index, y=seasonal, line=dict(color=THEME_COLORS["secondary_accent"])), row=2, col=1)
            
            fig_decomp = apply_antigravity_theme(fig_decomp)
            fig_decomp.update_layout(height=450, showlegend=False, title_text="Signal Decomposition (STL)")
            all_visuals.append(fig_decomp)
            
            all_details_html.append(_create_card("Signal Decomposition", 
                 "<div class='plot-placeholder-target'></div>",
                 "Separating the signal into underlying Trend and repeating Seasonality."))

        # --- 3. Forecast Plot ---
        if forecast:
            fc_series = pd.Series(forecast)
            fig_fc = go.Figure()
            
            # History (last part of trend or original? We need original data context)
            # We'll just plot forecast connected to trend tail for visual continuity if original data unavailable in context
            # But better to just show forecast points
            fig_fc.add_trace(go.Scatter(
                x=fc_series.index, y=fc_series, mode='lines+markers',
                line=dict(color=THEME_COLORS["success"], dash='dash'), name='Forecast (14 days)'
            ))
            
            fig_fc = apply_antigravity_theme(fig_fc)
            fig_fc.update_layout(title="Short-Term Forecast (Holt-Winters)", xaxis_title="Date", height=350)
            all_visuals.append(fig_fc)
            
            all_details_html.append(_create_card("Forecasting", 
                 "<div class='plot-placeholder-target'></div>",
                 "Predicted values for the next 14 days using Triple Exponential Smoothing."))

        final_html = f"<div class='details-grid' style='display: flex; flex-direction: column; gap: 24px;'>{''.join(all_details_html)}</div>"

        print("     ... Details and visualizations for Time-Series Analysis complete.")
        return {
            "details_html": final_html,
            "visuals": all_visuals
        }

    except Exception as e:
        error_message = f"Failed during time-series visualization: {e}"
        print(f"     ... {error_message}")
        import traceback
        traceback.print_exc()
        return {"error": error_message}