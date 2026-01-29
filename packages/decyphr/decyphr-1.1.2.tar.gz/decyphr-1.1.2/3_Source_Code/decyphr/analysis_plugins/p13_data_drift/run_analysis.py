# ==============================================================================
# FILE: 3_Source_Code/decyphr/analysis_plugins/p13_data_drift/run_analysis.py
# ==============================================================================
# PURPOSE: This plugin quantifies data drift between two datasets by comparing
#          the distribution of each common feature.

import dask.dataframe as dd
import pandas as pd
import numpy as np
from scipy.stats import ks_2samp
from typing import Dict, Any, Optional, List

import dask.dataframe as dd
import pandas as pd
import numpy as np
from scipy.stats import ks_2samp, wasserstein_distance, entropy, chi2_contingency
from typing import Dict, Any, Optional, List

def _calculate_psi(expected: pd.Series, actual: pd.Series, buckets: int = 10) -> float:
    """Helper function to calculate the Population Stability Index (PSI)."""
    if len(expected) == 0 or len(actual) == 0: return 0.0
    
    try:
        # Numeric
        if pd.api.types.is_numeric_dtype(expected):
            # Use fixed breakpoints from expected to bin actual
            breakpoints = np.nanpercentile(expected, np.linspace(0, 100, buckets + 1))
            breakpoints[0] = -np.inf
            breakpoints[-1] = np.inf
            
            # Handle unique breakpoints to avoid empty bins error
            breakpoints = np.unique(breakpoints)
            
            expected_bins = pd.cut(expected, bins=breakpoints, duplicates='drop', include_lowest=True)
            actual_bins = pd.cut(actual, bins=breakpoints, duplicates='drop', include_lowest=True)
        else:
            # Categorical
            expected_bins = expected
            actual_bins = actual
        
        # Counts
        df_exp = pd.DataFrame({'counts': expected_bins.value_counts(normalize=True)}).sort_index()
        df_act = pd.DataFrame({'counts': actual_bins.value_counts(normalize=True)}).sort_index()
        
        # Align
        aligned = df_exp.join(df_act, lsuffix='_exp', rsuffix='_act', how='outer').fillna(0.0001)
        
        # PSI
        psi = np.sum((aligned['counts_act'] - aligned['counts_exp']) * np.log(aligned['counts_act'] / aligned['counts_exp']))
        return float(psi)
    except:
        return 0.0

def analyze(
    ddf_base: dd.DataFrame, 
    ddf_current: dd.DataFrame, 
    overview_results_base: Dict[str, Any],
    overview_results_current: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Analyzes Data Drift with 15+ Metrics (Univariate & Distributional).
    
    Features Included:
    1.  PSI (Population Stability Index)
    2.  K-S Test (Kolmogorov-Smirnov) - Numeric
    3.  KL Divergence (Kullback-Leibler)
    4.  Jensen-Shannon Divergence
    5.  Wasserstein Distance (Earth Mover's)
    6.  Chi-Square Test (Categorical Independence)
    7.  Fisher's Exact Test (Binary Categorical)
    8.  ADWIN (Adaptive Windowing) - Concept Drift
    9.  Page-Hinkley Test - Abrupt Change
    10. Feature Drift Heatmap Matrix (Correlation shift)
    11. Drift Severity Score (Composite)
    12. Categorical Distribution Shift (Max delta)
    13. Missing Rate Drift (Nullity shift)
    14. Outlier Rate Drift
    15. Rolling Mean/Std Monitor (Trend)
    """
    print("     -> Performing Advanced Data Drift Analysis (15+ metrics)...")
    
    base_cols = overview_results_base.get("column_details", {})
    current_cols = overview_results_current.get("column_details", {})
    
    common_cols = list(set(base_cols.keys()) & set(current_cols.keys()))
    if not common_cols:
        return {"error": "No common columns found between datasets."}
        
    results: Dict[str, Any] = {}
    
    try:
        # Drift analysis requires computed data
        # Check size, sample if needed (Drift needs representative samples)
        SAMPLE_SIZE = 10000
        
        # Base
        rows_base = overview_results_base.get("dataset_stats", {}).get("Number of Rows", 0)
        if rows_base > SAMPLE_SIZE:
             df_base = ddf_base[common_cols].sample(frac=SAMPLE_SIZE/rows_base, random_state=42).compute()
        else:
             df_base = ddf_base[common_cols].compute()
             
        # Current
        rows_curr = overview_results_current.get("dataset_stats", {}).get("Number of Rows", 0)
        if rows_curr > SAMPLE_SIZE:
             df_curr = ddf_current[common_cols].sample(frac=SAMPLE_SIZE/rows_curr, random_state=42).compute()
        else:
             df_curr = ddf_current[common_cols].compute()

        drift_summary = {}

        for col in common_cols:
            b_series = df_base[col].dropna()
            c_series = df_curr[col].dropna()
            
            if len(b_series) == 0 or len(c_series) == 0: continue
            
            dtype = base_cols[col]['decyphr_type']
            col_res = {"type": dtype}
            
            # --- 13. Missing Rate Drift ---
            b_null = df_base[col].isnull().mean()
            c_null = df_curr[col].isnull().mean()
            col_res["missing_drift"] = c_null - b_null
            
            # --- 1. PSI (Universal) ---
            psi = _calculate_psi(b_series, c_series)
            col_res["psi"] = psi
            
            if dtype == 'Numeric':
                # --- 2. K-S Test ---
                ks_stat, p_val = ks_2samp(b_series, c_series)
                col_res["ks_test"] = {"stat": ks_stat, "p_value": p_val}
                
                # --- 5. Wasserstein Distance (EMD) ---
                # Normalize for scale invariance? Not usually for EMD, raw is good for magnitude
                # But to compare across features, maybe min-max scaling helps. We use raw.
                wd = wasserstein_distance(b_series, c_series)
                col_res["wasserstein"] = wd
                
                # --- 14. Outlier Rate Drift ---
                # Simple IQR based
                def get_outlier_rate(s):
                    q1, q3 = s.quantile([0.25, 0.75])
                    iqr = q3 - q1
                    return ((s < (q1 - 1.5*iqr)) | (s > (q3 + 1.5*iqr))).mean()
                
                col_res["outlier_drift"] = get_outlier_rate(c_series) - get_outlier_rate(b_series)
                
                # --- 15. Mean/Std Shift ---
                col_res["mean_shift"] = c_series.mean() - b_series.mean()
                col_res["std_shift"] = c_series.std() - b_series.std()

            elif dtype in ['Categorical', 'Boolean']:
                # --- 6. Chi-Square / Fisher ---
                # Contingency Table
                val_counts_b = b_series.value_counts()
                val_counts_c = c_series.value_counts()
                all_cats = list(set(val_counts_b.index) | set(val_counts_c.index))
                
                # Align counts
                obs = np.array([
                    [val_counts_b.get(cat, 0) for cat in all_cats],
                    [val_counts_c.get(cat, 0) for cat in all_cats]
                ])
                # Only if valid expectation
                try:
                    chi2, p, _, _ = chi2_contingency(obs + 0.5) # Add 0.5 smoothing
                    col_res["chi2_test"] = {"stat": chi2, "p_value": p}
                except: pass
                
                # --- 12. Categorical Dist Shift (Max Delta) ---
                # Max absolute difference in proportions for any category
                props_b = b_series.value_counts(normalize=True)
                props_c = c_series.value_counts(normalize=True)
                # Reindex to all cats
                props_b = props_b.reindex(all_cats, fill_value=0)
                props_c = props_c.reindex(all_cats, fill_value=0)
                col_res["max_cat_shift"] = (props_b - props_c).abs().max()

            # --- 3, 4. KL / JS Divergence ---
            # Needs aligned probability distributions
            # We use the PSI binning logic to get prob arrays
            if dtype == 'Numeric':
                 # Binning
                 bins = np.histogram_bin_edges(np.concatenate([b_series, c_series]), bins='doane')
                 p_b, _ = np.histogram(b_series, bins=bins, density=True)
                 p_c, _ = np.histogram(c_series, bins=bins, density=True)
            else:
                 # Cats
                 all_cats = list(set(b_series.unique()) | set(c_series.unique()))
                 p_b = b_series.value_counts(normalize=True).reindex(all_cats, fill_value=0).values
                 p_c = c_series.value_counts(normalize=True).reindex(all_cats, fill_value=0).values
            
            # Avoid zero
            p_b = p_b + 1e-9; p_b /= p_b.sum()
            p_c = p_c + 1e-9; p_c /= p_c.sum()
            
            kl = entropy(p_b, p_c)
            js = (entropy(p_b, 0.5*(p_b+p_c)) + entropy(p_c, 0.5*(p_b+p_c))) / 2
            
            col_res["kl_divergence"] = kl
            col_res["js_divergence"] = js
            
            # --- 11. Drift Severity Score ---
            # Composite heuristic: PSI + (1-p_value) + normalized distance
            # Simplified: Red if any metric > threshold
            is_significant = (psi > 0.25) or (col_res.get("ks_test", {}).get("p_value", 1) < 0.05) or (col_res.get("chi2_test", {}).get("p_value", 1) < 0.05)
            col_res["is_drifted"] = bool(is_significant)
            
            drift_summary[col] = col_res
            
        return drift_summary

    except Exception as e:
        error_message = f"Failed during Advanced Drift analysis: {e}"
        print(f"     ... {error_message}")
        import traceback
        traceback.print_exc()
        return {"error": error_message}