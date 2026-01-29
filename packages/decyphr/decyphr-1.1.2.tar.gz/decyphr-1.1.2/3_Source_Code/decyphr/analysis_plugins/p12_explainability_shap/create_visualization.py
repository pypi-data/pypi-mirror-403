# ==============================================================================
# FILE: 3_Source_Code/decyphr/analysis_plugins/p12_explainability_shap/create_visualization.py
# ==============================================================================
# PURPOSE: Generates rich HTML content for Advanced Explainability (SHAP), 
#          visualizing 15+ features/metrics using Antigravity UI.

import plotly.graph_objects as go
import pandas as pd
import numpy as np
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
    Creates rich HTML content for SHAP analysis.
    """
    print("     -> Generating details & visualizations for Advanced SHAP...")
    
    if "error" in analysis_results:
        return {"error": analysis_results["error"]}
    if not analysis_results or "message" in analysis_results:
        return {"message": "SHAP analysis was not performed."}

    all_details_html: List[str] = []
    all_visuals: List[go.Figure] = []

    try:
        # Extract Results
        shap_values = np.array(analysis_results.get("shap_values", []))
        feature_data_dict = analysis_results.get("feature_data", {})
        feature_names = analysis_results.get("feature_names", [])
        dependence_data = analysis_results.get("dependence_data", {})
        cohorts = analysis_results.get("cohort_analysis", {})
        local_expl = analysis_results.get("local_explanations", {})

        if shap_values.size == 0 or not feature_data_dict:
            return {"message": "No SHAP values calculated."}

        # --- 1. Summary Card ---
        all_details_html.append(_create_card("Model Explainability (SHAP)", 
             """<p>
                SHAP (SHapley Additive exPlanations) breaks down prediction scores into the contribution of each feature. 
                Plots below show <em>Global</em> (overall trends) and <em>Local</em> (individual instances) explanations.
             </p>""",
             "Understand HOW the model makes decisions, not just WHAT it predicts."))

        # --- 2. Beeswarm Plot (Summary Plot) ---
        feature_data = pd.DataFrame(feature_data_dict)
        mean_abs_shap = np.abs(shap_values).mean(axis=0)
        # Sort top 20
        idx = np.argsort(mean_abs_shap)[::-1][:20]
        sorted_feats = [feature_names[i] for i in idx]
        sorted_shap = shap_values[:, idx]
        sorted_data = feature_data.iloc[:, idx]

        fig_bee = go.Figure()
        
        # Add a vertical zero line
        fig_bee.add_shape(type='line', x0=0, y0=-0.5, x1=0, y1=len(sorted_feats)-0.5, line=dict(color=THEME_COLORS["grid"], width=1, dash='dot'))

        for i, feat in enumerate(sorted_feats):
            # Normalize for color
            vals = sorted_data[feat].values
            min_v, max_v = np.nanmin(vals), np.nanmax(vals)
            colors = (vals - min_v) / (max_v - min_v + 1e-9) if min_v != max_v else 0.5
            
            # Jitter y
            y_jitter = np.random.normal(loc=i, scale=0.1, size=len(vals))
            
            fig_bee.add_trace(go.Scattergl(
                x=sorted_shap[:, i], y=y_jitter,
                mode='markers', name=feat,
                marker=dict(
                    color=colors, colorscale='RdBu', showscale=(i==0),
                    colorbar=dict(title="Feature Value", len=0.5, y=0.5) if i==0 else None,
                    size=3, opacity=0.6
                ),
                text=[f"{feat}={v:.2f}" for v in vals],
                hovertemplate="SHAP: %{x:.3f}<br>%{text}"
            ))

        fig_bee = apply_antigravity_theme(fig_bee)
        fig_bee.update_layout(
             title="SHAP Summary (Beeswarm)", 
             xaxis_title="SHAP Value (Impact on Prediction)",
             yaxis=dict(tickvals=list(range(len(sorted_feats))), ticktext=sorted_feats, autorange="reversed"),
             width=None, height=500, showlegend=False
        )
        all_visuals.append(fig_bee)
        
        all_details_html.append(_create_card("Global Feature Impact", 
             "<div class='plot-placeholder-target'></div>",
             "Red points = High feature values. Blue = Low. Right side = Positive impact on prediction."))

        # --- 3. Dependence Plots ---
        if dependence_data:
            for feat, data in dependence_data.items():
                fig_dep = go.Figure(data=go.Scatter(
                    x=data['x'], y=data['y'], mode='markers',
                    marker=dict(color=THEME_COLORS["primary_accent"], size=4, opacity=0.6)
                ))
                fig_dep = apply_antigravity_theme(fig_dep)
                fig_dep.update_layout(title=f"SHAP Dependence: {feat}", xaxis_title=feat, yaxis_title="SHAP Value", height=350)
                all_visuals.append(fig_dep)
            
            all_details_html.append(_create_card("Feature Dependence (Top 3)", 
                 "<div class='plot-placeholder-target'></div>", 
                 "Shows how a single feature's value affects its contribution (SHAP value). Non-linear patterns usually appear here."))

        # --- 4. Cohort Analysis ---
        if cohorts:
            cohort_html = ""
            for seg, imps in cohorts.items():
                cohort_html += f"<h5>Segment: {seg}</h5>"
                rows = [[k, f"{v:.4f}"] for k,v in imps.items()]
                cohort_html += _create_table(["Top Driver", "Mean SHAP"], rows)
            
            all_details_html.append(_create_card("Cohort Analysis (Segmentation)", 
                 cohort_html,
                 "Top drivers for specific subgroups of data."))

        final_html = f"<div class='details-grid' style='display: flex; flex-direction: column; gap: 24px;'>{''.join(all_details_html)}</div>"

        print("     ... Details and visualizations for Advanced SHAP complete.")
        return {
            "details_html": final_html,
            "visuals": all_visuals
        }

    except Exception as e:
        error_message = f"Failed during SHAP visualization: {e}"
        print(f"     ... {error_message}")
        import traceback
        traceback.print_exc()
        return {"error": error_message}