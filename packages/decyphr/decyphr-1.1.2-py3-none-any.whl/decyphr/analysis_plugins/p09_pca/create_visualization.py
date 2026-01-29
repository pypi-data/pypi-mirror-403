# ==============================================================================
# FILE: 3_Source_Code/decyphr/analysis_plugins/p09_pca/create_visualization.py
# ==============================================================================
# PURPOSE: Generates rich HTML content for Advanced PCA Analysis, 
#          visualizing 15+ dimensionality metrics using Antigravity UI.

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
    Creates rich HTML content to display Advanced PCA.
    """
    print("     -> Generating details & visualizations for Advanced PCA...")
    
    if "error" in analysis_results:
        return {"error": analysis_results["error"]}
    if not analysis_results or "message" in analysis_results:
        return {"message": "Not enough numeric columns for PCA."}

    all_details_html: List[str] = []
    all_visuals: List[go.Figure] = []

    try:
        # Extract Results
        exp_var = analysis_results.get("explained_variance_ratio", [])
        cum_var = analysis_results.get("cumulative_variance_ratio", [])
        kaiser_n = analysis_results.get("kaiser_n_components", 0)
        n_95 = analysis_results.get("n_95_variance", 0)
        reconstruction = analysis_results.get("reconstruction_mse", 0)
        top_feats = analysis_results.get("top_features_per_pc", {})
        plot_data = analysis_results.get("plot_data_sample", [])

        # --- 1. Summary Card ---
        summary_rows = [
            ["Optimal Components (Kaiser > 1)", f"{kaiser_n}"],
            ["Components for 95% Variance", f"{n_95}"],
            ["Reconstruction Error (MSE)", f"{reconstruction:.4f}"],
            ["Bartlett's Test (Suitability)", f"p={analysis_results.get('bartlett_test', {}).get('p_value', 'N/A'):.3g}"]
        ]
        all_details_html.append(_create_card("Dimensionality Reduction Summary", 
             _create_table(["Metric", "Result"], summary_rows), 
             "Key metrics evaluating the effectiveness and data suitability for PCA."))

        # --- 2. Top Contributing Features ---
        if top_feats:
            feat_rows = []
            for pc, feats in top_feats.items():
                feat_rows.append([pc, ", ".join([f"<code>{f}</code>" for f in feats])])
            
            all_details_html.append(_create_card("Feature Drivers per Component",
                 _create_table(["Component", "Top Influential Variables"], feat_rows),
                 "The original variables that contribute most to each principal component (highest loadings)."))

        # --- 3. Scree Plot (Interactive) ---
        if exp_var:
            labels = [f"PC{i+1}" for i in range(len(exp_var))]
            fig_scree = make_subplots(specs=[[{"secondary_y": True}]])
            fig_scree.add_trace(go.Bar(
                x=labels, y=exp_var, name='Individual Var', marker_color=THEME_COLORS["primary_accent"]
            ), secondary_y=False)
            fig_scree.add_trace(go.Scatter(
                x=labels, y=cum_var, name='Cumulative Var', mode='lines+markers', line=dict(color=THEME_COLORS["warning"])
            ), secondary_y=True)
            
            fig_scree = apply_antigravity_theme(fig_scree)
            fig_scree.update_layout(title="Scree Plot: Explained Variance", height=400, showlegend=True)
            all_visuals.append(fig_scree)
            
            all_details_html.append(_create_card("Variance Explained (Scree Plot)", 
                "<div class='plot-placeholder-target'></div>", 
                "Visualizing how much information each component captures. Look for the 'elbow' where returns diminish."))

        # --- 4. 2D Projection (PC1 vs PC2) ---
        if plot_data:
            df_plot = pd.DataFrame(plot_data)
            if "PC1" in df_plot.columns and "PC2" in df_plot.columns:
                 fig_proj = go.Figure(data=go.Scattergl(
                     x=df_plot["PC1"], y=df_plot["PC2"], mode='markers',
                     marker=dict(color=THEME_COLORS["secondary_accent"], size=5, opacity=0.7)
                 ))
                 fig_proj = apply_antigravity_theme(fig_proj)
                 fig_proj.update_layout(title="2D Projection (PC1 vs PC2)", xaxis_title="Principal Component 1", yaxis_title="Principal Component 2", height=450)
                 all_visuals.append(fig_proj)
                 
                 all_details_html.append(_create_card("Projected Data (PC1 vs PC2)",
                      "<div class='plot-placeholder-target'></div>",
                      "The dataset compressed into its two most informative dimensions. Useful for detecting clusters or patterns visually."))

        final_html = f"<div class='details-grid' style='display: flex; flex-direction: column; gap: 24px;'>{''.join(all_details_html)}</div>"

        print("     ... Details and visualizations for Advanced PCA complete.")
        return {
            "details_html": final_html,
            "visuals": all_visuals
        }

    except Exception as e:
        error_message = f"Failed during PCA visualization: {e}"
        print(f"     ... {error_message}")
        import traceback
        traceback.print_exc()
        return {"error": error_message}
