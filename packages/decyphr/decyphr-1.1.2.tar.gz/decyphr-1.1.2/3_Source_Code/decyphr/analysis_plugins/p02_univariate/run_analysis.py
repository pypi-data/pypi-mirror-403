# ==============================================================================
# FILE: 3_Source_Code/decyphr/analysis_plugins/p02_univariate/run_analysis.py
# ==============================================================================
# PURPOSE: This file contains the logic for univariate analysis, calculating
#          detailed statistics for each individual column (variable) in the dataset.

import dask.dataframe as dd
import pandas as pd
from typing import Dict, Any, Optional, List

def analyze(ddf: dd.DataFrame, overview_results: Dict[str, Any], target_column: Optional[str] = None) -> Dict[str, Any]:
    """
    Performs univariate analysis on each column of the dataframe.

    It uses the pre-computed column classifications from the 'overview' plugin
    to apply the correct statistical measures to each column type (numeric vs. categorical).

    Args:
        ddf (dd.DataFrame): The Dask DataFrame to be analyzed.
        overview_results (Dict[str, Any]): The results dictionary from the p01_overview plugin.
                                           This is crucial for identifying column types.
        target_column (Optional[str]): The target column, currently ignored but kept for
                                       a consistent function signature.

    Returns:
        A dictionary containing detailed univariate statistics for each column.
    """
    print("     -> Performing univariate analysis on numeric and categorical columns...")

    # Ensure the required 'column_details' from the overview plugin are present
    column_details = overview_results.get("column_details")
    if not column_details:
        return {"error": "Univariate analysis requires 'column_details' from the overview plugin."}
    
    # DEBUG PRINT
    print("DEBUG: Column Details:", column_details)


    # --- Segregate columns by their classified type ---
    numeric_cols: List[str] = [
        col for col, details in column_details.items() if details['decyphr_type'] == 'Numeric'
    ]
    categorical_cols: List[str] = [
        col for col, details in column_details.items() if details['decyphr_type'] in ['Categorical', 'Categorical (Numeric)', 'Boolean']
    ]

    results: Dict[str, Any] = {
        "numeric_stats": {},
        "categorical_stats": {}
    }

    try:
        # --- 1. Process Numeric Columns in Parallel ---
        if numeric_cols:
            print(f"     ... Analyzing {len(numeric_cols)} numeric columns.")
            
            # --- A. Basic Aggregations ---
            # Use describe with custom percentiles which is well-supported in Dask
            # We compute descriptive stats, skew, and kurtosis. 
            # Note: describe() in dask triggers a compute unless we use dask.compat... 
            # actually ddf.describe() returns a Dask DataFrame, so we must .compute() it.
            
            percentiles = [0.01, 0.05, 0.25, 0.50, 0.75, 0.95, 0.99]
            desc_stats_df = ddf[numeric_cols].describe(percentiles=percentiles).compute()
            
            # Skew and Kurtosis separately
            skewness = ddf[numeric_cols].skew().compute()
            kurtosis = ddf[numeric_cols].kurt().compute()
            
            # --- B. Data Quality & Special Counts ---
            total_rows = ddf.shape[0].compute() if hasattr(ddf, 'shape') else len(ddf)

            for col in numeric_cols:
                col_series = ddf[col]
                # Extract stats for the current column from the computed describe DataFrame
                # The index of desc_stats_df contains the stat names (e.g., 'mean', 'std', '5%')
                stats = desc_stats_df[col].to_dict()
                
                # Rename percentiles to match previous output format (e.g., '5%' instead of '50%')
                # Dask's describe uses '50%' for median, '25%' for Q1, etc.
                # We need to ensure the keys match the expected output format.
                # Mapping dask describe keys to our keys
                key_map = {
                    '1%': '1%', '5%': '5%', '25%': '25%', '50%': '50%', 
                    '75%': '75%', '95%': '95%', '99%': '99%'
                }
                for dask_key, target_key in key_map.items():
                    if dask_key in stats:
                        stats[target_key] = stats.pop(dask_key)
                
                # Basic Stats enrichment
                stats['skew'] = round(skewness[col], 4)
                stats['kurtosis'] = round(kurtosis[col], 4)
                
                # Advanced Stats
                # IQR
                q1 = stats.get('25%', 0)
                q3 = stats.get('75%', 0)
                iqr = q3 - q1
                stats['iqr'] = iqr
                
                # CV (Coefficient of Variation)
                mean_val = stats.get('mean', 0)
                std_val = stats.get('std', 0)
                stats['cv'] = (std_val / mean_val) if mean_val != 0 else 0.0
                
                # Range
                stats['range'] = stats.get('max', 0) - stats.get('min', 0)
                
                # Outliers (1.5 * IQR Rule)
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr
                
                # Compute specific counts (expensive, but necessary for "Real World" depth)
                # Optimization: We could batch these, but per-column ensures isolation on failure
                
                # Zero / Negative / Inf checks
                # Note: This computes immediately. For huge data, consider dask.delayed or similar if too slow.
                zeros = (col_series == 0).sum().compute()
                negatives = (col_series < 0).sum().compute()
                
                # Outliers count
                outliers = ((col_series < lower_bound) | (col_series > upper_bound)).sum().compute()
                
                stats['zeros'] = zeros
                stats['negatives'] = negatives
                stats['outliers'] = outliers
                stats['outlier_pct'] = (outliers / total_rows) * 100 if total_rows > 0 else 0
                stats['missing'] = total_rows - stats.get('count', 0)
                stats['missing_pct'] = (stats['missing'] / total_rows) * 100 if total_rows > 0 else 0
                
                results["numeric_stats"][col] = stats

        # --- 2. Process Categorical Columns ---
        if categorical_cols:
            print(f"     ... Analyzing {len(categorical_cols)} categorical columns.")
            total_rows = ddf.shape[0].compute() if hasattr(ddf, 'shape') else len(ddf)

            for col in categorical_cols:
                # Value Counts (Top 20)
                # Compute full value counts first to get accurate mode/unique stats
                value_counts_series = ddf[col].value_counts().compute()
                
                # Top 20 for chart
                top_20 = value_counts_series.nlargest(20)
                
                # Basic Stats
                unique_count = len(value_counts_series)
                if not value_counts_series.empty:
                    most_freq_val = value_counts_series.idxmax()
                    most_freq_count = value_counts_series.max()
                else:
                    most_freq_val = "N/A"
                    most_freq_count = 0
                
                # Missing (Total rows - sum of counts if NaNs are excluded by value_counts default)
                # dask's value_counts typically excludes nulls by default
                non_null_count = value_counts_series.sum()
                missing_count = total_rows - non_null_count
                
                # [NEW] Cumulative Percentage for Pareto
                # Convert to pandas series for easy cumulative calculation (top 20 is small)
                top_20_df = top_20.to_frame(name='count')
                top_20_df['cumulative_sum'] = top_20_df['count'].cumsum()
                top_20_df['cumulative_pct'] = (top_20_df['cumulative_sum'] / non_null_count) * 100
                
                # Store value counts with cumulative info
                value_counts_data = {}
                for idx, row in top_20_df.iterrows():
                    value_counts_data[str(idx)] = {
                        "count": int(row['count']),
                        "cumulative_pct": float(row['cumulative_pct'])
                    }
                
                # [NEW] Cardinality / ID Column Check
                is_high_cardinality = False
                if total_rows > 0 and (unique_count / total_rows) > 0.5:
                    is_high_cardinality = True

                results["categorical_stats"][col] = {
                    "value_counts": value_counts_data, # Updated structure
                    "total_unique": unique_count,
                    "is_high_cardinality": is_high_cardinality,
                    "mode": most_freq_val,
                    "mode_freq": most_freq_count,
                    "mode_pct": (most_freq_count / total_rows) * 100 if total_rows > 0 else 0,
                    "missing": missing_count,
                    "missing_pct": (missing_count / total_rows) * 100 if total_rows > 0 else 0
                }
        
        print("     ... Univariate analysis complete.")
        return results

    except Exception as e:
        error_message = f"Failed during univariate analysis: {e}"
        print(f"     ... {error_message}")
        import traceback
        traceback.print_exc()
        return {"error": error_message}