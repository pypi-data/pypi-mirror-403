# ==============================================================================
# FILE: 3_Source_Code/decyphr/analysis_plugins/p10_clustering/create_visualization.py
# ==============================================================================
# PURPOSE: Generates rich HTML content for Advanced Clustering Analysis, 
#          visualizing 15+ features/metrics using Antigravity UI.

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

def create_visuals(ddf, overview_results: Dict[str, Any], analysis_results: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Creates rich HTML content for advanced clustering.
    """
    print("     -> Generating details & visualizations for Advanced Clustering...")
    
    if "error" in analysis_results:
        return {"error": analysis_results["error"]}
    if not analysis_results or "message" in analysis_results:
        return {"message": "Clustering analysis was not performed."}

    all_details_html: List[str] = []
    all_visuals: List[go.Figure] = []

    try:
        # Extract Results
        k = analysis_results.get("suggested_k", 3)
        inertia = analysis_results.get("inertia_scores", {})
        sil_score = analysis_results.get("silhouette_score", 0)
        db_score = analysis_results.get("davies_bouldin", 0)
        ch_score = analysis_results.get("calinski_harabasz", 0)
        profiles = analysis_results.get("cluster_profiles", {})
        proj_data = analysis_results.get("projection_data", [])
        counts = analysis_results.get("cluster_counts", {})
        dbscan_res = analysis_results.get("dbscan", {})

        # --- 1. Summary Metrics ---
        summary_rows = [
            ["Suggested Clusters (k)", f"<strong>{k}</strong>"],
            ["Silhouette Score (Quality)", f"{sil_score:.3f} (Higher is better)"],
            ["Davies-Bouldin (Separation)", f"{db_score:.3f} (Lower is better)"],
            ["Calinski-Harabasz", f"{ch_score:,.1f}"],
            ["DBSCAN Estimates", f"{dbscan_res.get('n_clusters', 0)} Clusters, {dbscan_res.get('n_noise', 0)} Noise Pts"]
        ]
        all_details_html.append(_create_card("Clustering Performance", 
             _create_table(["Metric", "Result"], summary_rows),
             "Evaluation metrics for cluster quality and separation."))

        # --- 2. Cluster Profiles ---
        if profiles:
            prof_rows = []
            for c_id, feats in profiles.items():
                count = counts.get(int(c_id), 0)
                pct = count / sum(counts.values()) if counts else 0
                prof_rows.append([
                    f"Cluster {c_id}",
                    f"{count} ({pct:.1%})",
                    ", ".join([f"<code>{f}</code>" for f in feats])
                ])
            all_details_html.append(_create_card("Cluster Characteristics",
                 _create_table(["Cluster", "Size", "Defining Features (vs Global Context)"], prof_rows),
                 "What makes each cluster unique? 'High/Low' indicates deviation from the global average."))

        # --- 3. t-SNE Projection Plot ---
        if proj_data:
            df_proj = pd.DataFrame(proj_data)
            fig_tsne = go.Figure()
            for c_id in sorted(df_proj['cluster'].unique()):
                subset = df_proj[df_proj['cluster'] == c_id]
                fig_tsne.add_trace(go.Scattergl(
                    x=subset['x'], y=subset['y'],
                    mode='markers', name=f'Cluster {c_id}',
                    marker=dict(size=6, opacity=0.7)
                ))
            
            fig_tsne = apply_antigravity_theme(fig_tsne)
            fig_tsne.update_layout(
                title="t-SNE Projection of Clusters", 
                xaxis_title="t-SNE 1", yaxis_title="t-SNE 2", 
                height=450, legend_title="Cluster"
            )
            all_visuals.append(fig_tsne)
            
            all_details_html.append(_create_card("Cluster Visualization (t-SNE)",
                 "<div class='plot-placeholder-target'></div>",
                 "Non-linear projection of high-dimensional data into 2D space to visualize natural groupings."))

        # --- 4. Elbow Plot ---
        if inertia:
            ks = list(inertia.keys())
            vals = list(inertia.values())
            fig_elbow = go.Figure(data=go.Scatter(x=ks, y=vals, mode='lines+markers', marker_color=THEME_COLORS["primary_accent"]))
            
            fig_elbow = apply_antigravity_theme(fig_elbow)
            fig_elbow.update_layout(title="Elbow Method (Inertia)", xaxis_title="k", yaxis_title="Inertia", height=350)
            all_visuals.append(fig_elbow)
            
            all_details_html.append(_create_card("Optimization: Elbow Plot", 
                 "<div class='plot-placeholder-target'></div>",
                 "Inertia decrease as k increases. The 'elbow' suggests the optimal balance between granularity and simplicity."))

        final_html = f"<div class='details-grid' style='display: flex; flex-direction: column; gap: 24px;'>{''.join(all_details_html)}</div>"

        print("     ... Details and visualizations for Advanced Clustering complete.")
        return {
            "details_html": final_html,
            "visuals": all_visuals
        }

    except Exception as e:
        error_message = f"Failed during clustering visualization: {e}"
        print(f"     ... {error_message}")
        import traceback
        traceback.print_exc()
        return {"error": error_message}