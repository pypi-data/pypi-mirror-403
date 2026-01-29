# ==============================================================================
# FILE: 3_Source_Code/decyphr/report_builder/builder.py
# ==============================================================================
# PURPOSE: This is the master script for assembling the final HTML report.
#          VERSION 4.0: Re-architected for LAZY LOADING to handle large reports.

import os
import json
from jinja2 import Environment, FileSystemLoader
from datetime import datetime
from typing import Dict, Any, List
import plotly.io as pio

# --- Import all visualization functions ---
from ..analysis_plugins.p01_overview import create_visualization as viz_overview
from ..analysis_plugins.p02_univariate import create_visualization as viz_univariate
from ..analysis_plugins.p03_data_quality import create_visualization as viz_data_quality
from ..analysis_plugins.p04_advanced_outliers import create_visualization as viz_outliers
from ..analysis_plugins.p05_missing_values import create_visualization as viz_missing
from ..analysis_plugins.p06_correlations import create_visualization as viz_correlations
from ..analysis_plugins.p07_interactions import create_visualization as viz_interactions
from ..analysis_plugins.p08_hypothesis_testing import create_visualization as viz_hypothesis
from ..analysis_plugins.p09_pca import create_visualization as viz_pca
from ..analysis_plugins.p10_clustering import create_visualization as viz_clustering
from ..analysis_plugins.p11_target_analysis import create_visualization as viz_target
from ..analysis_plugins.p12_explainability_shap import create_visualization as viz_shap
from ..analysis_plugins.p13_data_drift import create_visualization as viz_data_drift
from ..analysis_plugins.p14_deep_text_analysis import create_visualization as viz_text_analysis
from ..analysis_plugins.p15_timeseries import create_visualization as viz_timeseries
from ..analysis_plugins.p16_geospatial import create_visualization as viz_geospatial

# --- Mappings for Title and Visualization Functions ---
VISUALIZATION_MAP = {
    "p01_overview": viz_overview.create_visuals, "p02_univariate": viz_univariate.create_visuals,
    "p03_data_quality": viz_data_quality.create_visuals, "p04_advanced_outliers": viz_outliers.create_visuals,
    "p05_missing_values": viz_missing.create_visuals, "p06_correlations": viz_correlations.create_visuals,
    "p07_interactions": viz_interactions.create_visuals, "p08_hypothesis_testing": viz_hypothesis.create_visuals,
    "p09_pca": viz_pca.create_visuals, "p10_clustering": viz_clustering.create_visuals,
    "p11_target_analysis": viz_target.create_visuals, "p12_explainability_shap": viz_shap.create_visuals,
    "p13_data_drift": viz_data_drift.create_visuals, "p14_deep_text_analysis": viz_text_analysis.create_visuals,
    "p15_timeseries": viz_timeseries.create_visuals, "p16_geospatial": viz_geospatial.create_visuals,
}
SECTION_TITLE_MAP = {
    "p01_overview": "Overview", "p02_univariate": "Univariate Analysis", "p03_data_quality": "Data Quality",
    "p04_advanced_outliers": "Outlier Analysis", "p05_missing_values": "Missing Values",
    "p06_correlations": "Correlations", "p07_interactions": "Feature Interactions",
    "p08_hypothesis_testing": "Hypothesis Tests", "p09_pca": "PCA", "p10_clustering": "Clustering",
    "p11_target_analysis": "Target Analysis", "p12_explainability_shap": "Explainable AI (SHAP)",
    "p13_data_drift": "Data Drift", "p14_deep_text_analysis": "Text Analysis", "p15_timeseries": "Time-Series",
    "p16_geospatial": "Geospatial",
}

def build_html_report(
    ddf, all_analysis_results: Dict[str, Any], output_path: str,
    decyphr_version: str, dataset_name: str
) -> None:
    print("Decyphr 🏗️: Assembling high-performance HTML report...")

    base_dir = os.path.dirname(__file__)
    template_dir = os.path.join(base_dir, 'templates')
    env = Environment(loader=FileSystemLoader(template_dir), autoescape=True)
    try:
        template = env.get_template('base_layout.html')
    except Exception as e:
        # If template loading fails, we still need to load assets to potentially render an error page or log.
        # The original instruction moved asset loading here, which might be intended for a fallback.
        with open(os.path.join(base_dir, 'assets', 'styles', 'main_theme.css'), 'r', encoding='utf-8') as f:
            css_styles = f.read()
        with open(os.path.join(base_dir, 'assets', 'scripts', 'interactivity.js'), 'r', encoding='utf-8') as f:
            js_script = f.read()
        print(f"Decyphr ❌: Failed to load report template: {e}. Cannot build report.")
        return

    try:
        with open(os.path.join(base_dir, 'assets', 'styles', 'main_theme.css'), 'r', encoding='utf-8') as f:
            css_styles = f.read()
        with open(os.path.join(base_dir, 'assets', 'scripts', 'interactivity.js'), 'r', encoding='utf-8') as f:
            js_script = f.read()
    except FileNotFoundError as e:
        print(f"Decyphr ❌: Critical asset file not found: {e}. Cannot build report.")
        return

    sidebar_sections, sections_data, all_plots_data = [], {}, {}
    all_columns = list(all_analysis_results.get("p01_overview", {}).get("column_details", {}).keys())
    sorted_section_ids = sorted(all_analysis_results.keys(), key=lambda x: list(SECTION_TITLE_MAP.keys()).index(x) if x in SECTION_TITLE_MAP else 99)

    for section_id in sorted_section_ids:
        results = all_analysis_results.get(section_id)
        if section_id in VISUALIZATION_MAP:
            if not results or "error" in results or ("message" in results and len(results) == 1):
                continue
            
            import inspect
            sig = inspect.signature(VISUALIZATION_MAP[section_id])
            viz_args = {k: v for k, v in [('ddf', ddf), ('overview_results', all_analysis_results.get('p01_overview')), ('analysis_results', results)] if k in sig.parameters}
            processed_content = VISUALIZATION_MAP[section_id](**viz_args)
            
            if processed_content and "error" not in processed_content:
                section_title = SECTION_TITLE_MAP.get(section_id, "Unnamed Section")
                sidebar_sections.append((section_id, section_title))
                
                # --- NEW LAZY LOADING LOGIC ---
                # Convert Plotly figures to JSON instead of HTML
                visuals_json = [json.loads(pio.to_json(fig)) for fig in processed_content.get("visuals", [])]
                
                # Store the plot data in a separate dict, keyed by section_id
                all_plots_data[section_id] = visuals_json

                # Check if the plugin wants to suppress the automatic grid generation
                # (allowing it to place plot placeholders manually in details_html)
                suppress_grid = processed_content.get("suppress_plot_grid", False)
                
                sections_data[section_id] = {
                    "title": section_title,
                    "details_html": processed_content.get("details_html", ""),
                    # If grid is suppressed, tell template there are 0 visuals to render automatically
                    # The JS will still find the plot data via section_id and the IDs we manually placed.
                    "visuals_count": 0 if suppress_grid else len(visuals_json)
                }

    final_html = template.render(
        decyphr_version=decyphr_version, dataset_name=dataset_name,
        generation_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        sections=sidebar_sections,
        all_columns=all_columns,
        sections_data=sections_data,
        all_plots_data_json=json.dumps(all_plots_data), # Embed all plot data as a single JSON string
        embedded_css=css_styles,
        embedded_js=js_script
    )

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(final_html)
        print(f"Decyphr ✅: Report successfully generated at '{output_path}'")
    except Exception as e:
        print(f"Decyphr ❌: Failed to save the final report. Error: {e}")