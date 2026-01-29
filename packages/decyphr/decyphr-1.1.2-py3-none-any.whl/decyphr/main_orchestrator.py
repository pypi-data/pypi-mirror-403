# ==============================================================================
# FILE: 3_Source_Code/decyphr/main_orchestrator.py
# ==============================================================================
# PURPOSE: This is the central brain of decyphr. It orchestrates the entire
#          analysis pipeline from data loading to final reporting.

import os
import json
from typing import Dict, Any, Optional

# --- Import Core Modules (Using Absolute Imports) ---
from decyphr.backends.dask_backend import load_dataframe_from_file
from decyphr.report_builder.builder import build_html_report

# --- Import All Analysis Plugin Functions (Using Absolute Imports) ---
from decyphr.analysis_plugins.p01_overview import run_analysis as overview_analysis
from decyphr.analysis_plugins.p02_univariate import run_analysis as univariate_analysis
from decyphr.analysis_plugins.p03_data_quality import run_analysis as data_quality_analysis
from decyphr.analysis_plugins.p04_advanced_outliers import run_analysis as outliers_analysis
from decyphr.analysis_plugins.p05_missing_values import run_analysis as missing_values_analysis
from decyphr.analysis_plugins.p06_correlations import run_analysis as correlations_analysis
from decyphr.analysis_plugins.p07_interactions import run_analysis as interactions_analysis
from decyphr.analysis_plugins.p08_hypothesis_testing import run_analysis as hypothesis_testing_analysis
from decyphr.analysis_plugins.p09_pca import run_analysis as pca_analysis
from decyphr.analysis_plugins.p10_clustering import run_analysis as clustering_analysis
from decyphr.analysis_plugins.p11_target_analysis import run_analysis as target_analysis
from decyphr.analysis_plugins.p12_explainability_shap import run_analysis as shap_analysis
from decyphr.analysis_plugins.p13_data_drift import run_analysis as data_drift_analysis
from decyphr.analysis_plugins.p14_deep_text_analysis import run_analysis as text_analysis
from decyphr.analysis_plugins.p15_timeseries import run_analysis as timeseries_analysis
from decyphr.analysis_plugins.p16_geospatial import run_analysis as geospatial_analysis


def run_analysis_pipeline(filepath: str, target: Optional[str] = None, compare_filepath: Optional[str] = None) -> Optional[str]:
    """
    Executes the full, end-to-end decyphr analysis pipeline.
    
    Returns:
        The file path to the generated HTML report, or None if it fails.
    """
    ddf = load_dataframe_from_file(filepath)
    if ddf is None:
        print("Decyphr 🚩: Halting execution due to primary data loading failure.")
        return None

    print("\nDecyphr ⚙️: Starting analysis pipeline...")
    print("  -> Running plugin [1/17]: p01_overview")
    overview_results = overview_analysis.analyze(ddf)
    
    analysis_results: Dict[str, Any] = {"p01_overview": overview_results}
    if "error" in overview_results:
        print(f"Decyphr 🚩: Halting execution due to critical failure in overview analysis: {overview_results['error']}")
        return None

    pipeline_steps = [
        ("p02_univariate", univariate_analysis.analyze, False, [overview_results]),
        ("p03_data_quality", data_quality_analysis.analyze, False, [overview_results]),
        ("p04_advanced_outliers", outliers_analysis.analyze, False, [overview_results]),
        ("p05_missing_values", missing_values_analysis.analyze, False, [overview_results]),
        ("p06_correlations", correlations_analysis.analyze, False, [overview_results]),
        ("p07_interactions", interactions_analysis.analyze, False, [overview_results]),
        ("p08_hypothesis_testing", hypothesis_testing_analysis.analyze, False, [overview_results]),
        ("p09_pca", pca_analysis.analyze, False, [overview_results]),
        ("p10_clustering", clustering_analysis.analyze, False, [overview_results, target]),
        ("p11_target_analysis", target_analysis.analyze, True, [overview_results, target]),
        ("p12_explainability_shap", shap_analysis.analyze, True, [overview_results, target]),
        ("p14_deep_text_analysis", text_analysis.analyze, False, [overview_results]),
        ("p15_timeseries", timeseries_analysis.analyze, False, [overview_results, target]),
        ("p16_geospatial", geospatial_analysis.analyze, False, [overview_results, target]),
    ]

    for i, (name, func, req_target, args) in enumerate(pipeline_steps, start=2):
        print(f"  -> Running plugin [{i}/17]: {name}")
        if req_target and not target:
            print(f"     ... Skipping '{name}', no target variable provided.")
            continue
        try:
            result = func(ddf, *args)
            analysis_results[name] = result
        except Exception as e:
            print(f"Decyphr ❌: Error in plugin '{name}': {e}")
            analysis_results[name] = {"error": str(e)}

    if compare_filepath:
        pass

    print("Decyphr ✅: Analysis pipeline complete.")

    from decyphr import __version__ as decyphr_version
    
    output_dir = "Reports"
    # CORRECTED: Use exist_ok=True to prevent errors or nested directories
    # if the 'Reports' folder already exists in the current working directory.
    os.makedirs(output_dir, exist_ok=True)
    
    report_num = 1
    while os.path.exists(os.path.join(output_dir, f"Report_{report_num}.html")):
        report_num += 1
    report_path = os.path.join(output_dir, f"Report_{report_num}.html")

    build_html_report(
        ddf=ddf,
        all_analysis_results=analysis_results,
        output_path=report_path,
        decyphr_version=decyphr_version,
        dataset_name=os.path.basename(filepath)
    )
    
    return report_path
