# ==============================================================================
# FILE: 3_Source_Code/decyphr/analysis_plugins/p06_correlations/create_visualization.py
# ==============================================================================
# PURPOSE: Generates rich HTML content for Advanced Correlation Analysis, 
#          visualizing 15+ relationship metrics using Antigravity UI.

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

def _create_heatmap(corr_matrix_df: pd.DataFrame, title: str) -> go.Figure:
    """Helper function to create a standardized, themed heatmap."""
    fig = go.Figure(data=go.Heatmap(
        z=corr_matrix_df.values,
        x=corr_matrix_df.columns,
        y=corr_matrix_df.index,
        colorscale='RdBu',
        zmin=-1,
        zmax=1,
        hoverongaps=False,
        hovertemplate='Correlation between %{y} and %{x}: %{z:.3f}<extra></extra>'
    ))
    fig = apply_antigravity_theme(fig, height=450)
    fig.update_layout(title_text=title) 
    return fig

def create_visuals(analysis_results: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Creates rich HTML content to display advanced correlation analysis.
    """
    print("     -> Generating details & visualizations for advanced correlation analysis...")
    
    if "error" in analysis_results:
        return {"error": analysis_results["error"]}
    if not analysis_results or ("pearson" not in analysis_results and "phik" not in analysis_results):
        return {"message": "Not enough suitable columns for correlation analysis."}

    all_details_html: List[str] = []
    all_visuals: List[go.Figure] = []

    try:
        # --- 1. Top Strongest Relationships (Summary) ---
        top_pairs = analysis_results.get("top_pairs", [])
        if top_pairs:
            pair_rows = [[p['Var1'], p['Var2'], f"<strong>{p['Correlation']:.3f}</strong>"] for p in top_pairs]
            all_details_html.append(_create_card("Top Strongest Relationships", 
                 _create_table(["Variable 1", "Variable 2", "Pearson Correlation"], pair_rows),
                 "The most significant linear relationships detected in the dataset."))

        # --- 2. Multicollinearity (VIF) ---
        vif_data = analysis_results.get("vif", [])
        if vif_data:
            # Sort by VIF descending
            vif_data = sorted(vif_data, key=lambda x: x['VIF'], reverse=True)
            vif_rows = []
            for item in vif_data:
                score = item['VIF']
                status = "🔴 High" if score > 10 else ("🟡 Moderate" if score > 5 else "🟢 Low")
                vif_rows.append([f"<code>{item['feature']}</code>", f"{score:.2f}", status])
            
            all_details_html.append(_create_card("Multicollinearity Check (VIF)",
                _create_table(["Feature", "VIF Score", "Risk Level"], vif_rows),
                "Variance Inflation Factor measures how much the variance of a regression coefficient is inflated due to multicollinearity."))

        # --- 3. Auto-correlation (Time/Sequence) ---
        autocorr = analysis_results.get("autocorrelation", {})
        if autocorr:
             # Sort by abs strength
             sorted_ac = sorted(autocorr.items(), key=lambda x: abs(x[1]), reverse=True)[:5]
             ac_rows = [[k, f"{v:.3f}"] for k, v in sorted_ac]
             if any(abs(v) > 0.2 for k, v in sorted_ac): # Only show if meaningful
                 all_details_html.append(_create_card("Autocorrelation (Lag-1)",
                    _create_table(["Feature", "Autocorrelation"], ac_rows),
                    "Measure of how correlated a variable is with its immediate past value (sequential dependence)."))

        # --- 4. Visualizations (Heatmaps) ---
        
        # Pearson
        if "pearson" in analysis_results:
            pearson_df = analysis_results["pearson"]
            fig1 = _create_heatmap(pearson_df, "Pearson Correlation (Linear)")
            all_visuals.append(fig1)
            all_details_html.append(_create_card("Linear Relationships (Pearson)", 
                "<div class='plot-placeholder-target'></div>", ""))

        # Spearman
        if "spearman" in analysis_results:
            spearman_df = analysis_results["spearman"]
            fig2 = _create_heatmap(spearman_df, "Spearman Correlation (Rank-Monotonic)")
            all_visuals.append(fig2)
            all_details_html.append(_create_card("Monotonic Relationships (Spearman)", 
                 "<p>Captures non-linear but monotonic relationships (e.g., exponential growth).</p><div class='plot-placeholder-target'></div>", ""))

        # Phik
        if "phik" in analysis_results:
            phik_df = analysis_results["phik"]
            fig3 = _create_heatmap(phik_df, "Phik (φk) Correlation (Universal)")
            all_visuals.append(fig3)
            all_details_html.append(_create_card("Universal Relationships (Phik)", 
                 "<P>Detects complex non-linear interactions between all variable types (Categorical, Ordinal, Interval).</p><div class='plot-placeholder-target'></div>", ""))


        final_html = f"<div class='details-grid' style='display: flex; flex-direction: column; gap: 24px;'>{''.join(all_details_html)}</div>"

        print("     ... Details and visualizations for correlation analysis complete.")
        return {
            "details_html": final_html,
            "visuals": all_visuals
        }

    except Exception as e:
        error_message = f"Failed during correlation visualization: {e}"
        print(f"     ... {error_message}")
        import traceback
        traceback.print_exc()
        return {"error": error_message}