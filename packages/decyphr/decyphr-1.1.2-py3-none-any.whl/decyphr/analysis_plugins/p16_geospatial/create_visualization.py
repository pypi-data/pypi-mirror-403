# ==============================================================================
# FILE: 3_Source_Code/decyphr/analysis_plugins/p16_geospatial/create_visualization.py
# ==============================================================================
# PURPOSE: Generates rich HTML content for Advanced Geospatial Analysis, 
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

def create_visuals(analysis_results: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Creates rich HTML content for Geospatial Analysis.
    """
    print("     -> Generating details & visualizations for Advanced Geospatial Analysis...")
    
    if "error" in analysis_results or not analysis_results or "message" in analysis_results:
         return {"message": "Geospatial analysis skipped."}

    all_details_html: List[str] = []
    all_visuals: List[go.Figure] = []

    try:
        geo_dict = analysis_results.get("geo_dataframe", {})
        stats = analysis_results.get("stats", {})
        
        if not geo_dict: return None
        
        geo_df = pd.DataFrame(geo_dict)
        lat_col = analysis_results.get("lat_col")
        lon_col = analysis_results.get("lon_col")
        target_col = analysis_results.get("target_col") # Not used for coloring in Density map, but available
        
        # --- 1. Mapbox Density / Clusters ---
        # Plotly Density Mapbox is great for heatmaps
        fig_map = go.Figure(go.Densitymapbox(
            lat=geo_df[lat_col],
            lon=geo_df[lon_col],
            radius=15,
            colorscale='Viridis',
            z=None # Just density of points
        ))
        
        # Overlay Scatter for outliers/points if sparse
        if len(geo_df) < 2000:
             fig_map.add_trace(go.Scattermapbox(
                lat=geo_df[lat_col],
                lon=geo_df[lon_col],
                mode='markers',
                marker=go.scattermapbox.Marker(size=5, color='white', opacity=0.5),
                hoverinfo='text',
                text=[f"Lat: {r[lat_col]:.4f}<br>Lon: {r[lon_col]:.4f}" for i, r in geo_df.iterrows()]
             ))
        
        fig_map = apply_antigravity_theme(fig_map)
        fig_map.update_layout(
            title_text=f"Spatial Density & Hotspots ({len(geo_df)} points)",
            mapbox_style="carto-darkmatter",
            mapbox_center={"lat": stats.get('centroid', {}).get('lat', 0), "lon": stats.get('centroid', {}).get('lon', 0)},
            mapbox_zoom=2,
            height=600
        )
        all_visuals.append(fig_map)
        
        all_details_html.append(_create_card("Interactive Geospatial Map", 
             "<div class='plot-placeholder-target'></div>",
             "Density heatmap showing concentration of data points across regions."))
             
        # --- 2. Region & Cluster Stats ---
        regions = stats.get('region_distribution', {})
        reg_rows = [[k, v, f"{v/len(geo_df):.1%}"] for k,v in regions.items()]
        
        clust_rows = [
            ["DBSCAN Segments", stats.get('clusters_count', 'N/A')],
            ["Spatial Outliers", f"{stats.get('outlier_ratio', 0):.1%}"],
            ["Max Pairwise Dist", f"{stats.get('distance_stats', {}).get('max_dist', 0):.2f}"]
        ]
        
        all_details_html.append(_create_card("Regional Distribution", 
             _create_table(["Region", "Count", "Percentage"], reg_rows),
             "Distribution of points by inferred continent/region."))
             
        all_details_html.append(_create_card("Spatial Statistics", 
             _create_table(["Metric", "Value"], clust_rows),
             "Clustering and dispersion metrics."))

        final_html = f"<div class='details-grid' style='display: flex; flex-direction: column; gap: 24px;'>{''.join(all_details_html)}</div>"

        print("     ... Details and visualization for geospatial analysis complete.")
        return {
            "details_html": final_html,
            "visuals": all_visuals
        }

    except Exception as e:
        error_message = f"Failed during geospatial visualization: {e}"
        print(f"     ... {error_message}")
        import traceback
        traceback.print_exc()
        return {"error": error_message}
