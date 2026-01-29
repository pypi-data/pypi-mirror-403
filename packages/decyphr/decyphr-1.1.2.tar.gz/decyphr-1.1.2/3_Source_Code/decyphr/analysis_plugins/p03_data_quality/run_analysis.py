# ==============================================================================
# FILE: 3_Source_Code/decyphr/analysis_plugins/p03_data_quality/run_analysis.py
# ==============================================================================
# PURPOSE: This plugin performs a deep scan for common data quality issues, such
#          as constant columns, leading/trailing whitespace, and mixed data types.

import dask.dataframe as dd
import dask.array as da
import numpy as np
from typing import Dict, Any, Optional, List

def analyze(ddf: dd.DataFrame, overview_results: Dict[str, Any], target_column: Optional[str] = None) -> Dict[str, Any]:
    """
    Analyzes the dataframe for common data integrity and quality issues.

    Args:
        ddf (dd.DataFrame): The Dask DataFrame to be analyzed.
        overview_results (Dict[str, Any]): The results from the p01_overview plugin,
                                           used to identify column types.
        target_column (Optional[str]): The target column, ignored here.

    Returns:
        A dictionary summarizing the data quality issues found.
    """
    print("     -> Performing extended data quality scan (12 checks)...")

    column_details = overview_results.get("column_details")
    if not column_details:
        return {"error": "Data quality analysis requires 'column_details' from the overview plugin."}

    results: Dict[str, Any] = {
        "constant_columns": [],
        "whitespace_issues": [],
        "duplicate_rows": {},
        "null_analysis": {},
        "outliers": {},
        "numeric_as_string": [],
        "negative_values": {},
        "empty_strings": {},
        "unique_candidates": [],
        "high_correlation": [],
        "high_cardinality": [],
        "quasi_constant": []
    }

    try:
        # Categorize columns
        numeric_cols = [c for c, d in column_details.items() if d['decyphr_type'] == 'Numeric']
        # Categorical/Text for detailed string analysis
        string_cols = [c for c, d in column_details.items() if d['decyphr_type'] in ['Categorical', 'Text (High Cardinality)', 'Text']]
        
        # --- 1. Identify Constant Columns (Existing) ---
        constant_cols = [col for col, details in column_details.items() if details['decyphr_type'] == 'Constant']
        results["constant_columns"] = constant_cols
        
        # --- 2. Check for Whitespace Issues (Existing) ---
        if string_cols:
            ws_issues = []
            for col_name in string_cols:
                # We do a basic check here. Optimization: compute all in one graph if strict performance needed
                leading = ddf[col_name].str.startswith(' ').sum()
                trailing = ddf[col_name].str.endswith(' ').sum()
                l_count, t_count = dd.compute(leading, trailing)
                if l_count > 0 or t_count > 0:
                    ws_issues.append({"column": col_name, "leading_spaces": int(l_count), "trailing_spaces": int(t_count)})
            results["whitespace_issues"] = ws_issues

        # --- 3. Duplicate Rows (New) ---
        # Note: drop_duplicates() in dask can be expensive. We'll estimate or compute exact if dataset small enough.
        # For 'Real Data', we'll try an exact count but wrapped safely.
        total_rows = len(ddf)
        deduped_rows = len(ddf.drop_duplicates())
        dup_count = total_rows - deduped_rows
        results["duplicate_rows"] = {
            "count": int(dup_count),
            "percentage": round((dup_count / total_rows) * 100, 2) if total_rows > 0 else 0
        }

        # --- 4. Detailed Null Analysis (New) ---
        # null_count per column is partially in overview, but we explicitly list high-null columns here
        null_counts = ddf.isnull().sum().compute()
        high_nulls = []
        for col, count in null_counts.items():
            if count > 0:
                pct = (count / total_rows) * 100
                if pct > 0: # Report all nulls for quality check
                    high_nulls.append({"column": col, "count": int(count), "percentage": round(pct, 2)})
        results["null_analysis"] = high_nulls

        # --- 5. Outliers (IQR Method) (New) ---
        # Only feasible effectively on numeric columns
        outlier_data = []
        if numeric_cols:
            # Calculate Q1, Q3 for all numeric columns
            quantiles = ddf[numeric_cols].quantile([0.25, 0.75]).compute()
            for col in numeric_cols:
                q1 = quantiles.loc[0.25, col]
                q3 = quantiles.loc[0.75, col]
                iqr = q3 - q1
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr
                
                # Count outliers
                # Filter rows where val < lower or val > upper
                outlier_count = ((ddf[col] < lower_bound) | (ddf[col] > upper_bound)).sum().compute()
                if outlier_count > 0:
                    outlier_data.append({
                        "column": col,
                        "count": int(outlier_count),
                        "percentage": round((outlier_count / total_rows) * 100, 2),
                        "lower_limit": float(lower_bound),
                        "upper_limit": float(upper_bound)
                    })
        results["outliers"] = outlier_data

        # --- 6. Numeric-as-String (New) ---
        # Check string columns if they can optionally be converted to numbers
        num_as_str_cols = []
        for col in string_cols:
             # Sample check or regex check
             # Regex: ^-?\d+(\.\d+)?$ matches integer or float
             match_count = ddf[col].astype(str).str.match(r'^-?\d+(\.\d+)?$').sum().compute()
             # If > 90% match, it's likely a misclassified numeric
             if match_count > 0.9 * total_rows:
                 num_as_str_cols.append({"column": col, "match_percentage": round((match_count/total_rows)*100, 2)})
        results["numeric_as_string"] = num_as_str_cols

        # --- 7. Negative Values (New) ---
        neg_val_list = []
        for col in numeric_cols:
            neg_count = (ddf[col] < 0).sum().compute()
            if neg_count > 0:
                neg_val_list.append({"column": col, "count": int(neg_count)})
        results["negative_values"] = neg_val_list

        # --- 8. Empty Strings vs Nulls (New) ---
        empty_str_list = []
        for col in string_cols:
            empty_count = (ddf[col] == "").sum().compute()
            if empty_count > 0:
                empty_str_list.append({"column": col, "count": int(empty_count)})
        results["empty_strings"] = empty_str_list

        # --- 9. Unique Candidates (IDs) (New) ---
        unique_cand_list = []
        # Check uniqueness for string/int columns
        candidates = string_cols + [c for c in numeric_cols]
        for col in candidates:
             approx_unique = ddf[col].nunique().compute()
             if approx_unique == total_rows:
                 unique_cand_list.append(col)
        results["unique_candidates"] = unique_cand_list

        # --- 10. High Correlation (New) ---
        # Correlation matrix for numeric columns
        high_corr_list = []
        if len(numeric_cols) >= 2:
            corr_matrix = ddf[numeric_cols].corr().compute()
            # Iterate upper triangle
            cols = corr_matrix.columns
            for i in range(len(cols)):
                for j in range(i+1, len(cols)):
                    val = corr_matrix.iloc[i, j]
                    if abs(val) > 0.95:
                        high_corr_list.append({
                            "col1": cols[i],
                            "col2": cols[j],
                            "correlation": round(val, 4)
                        })
        results["high_correlation"] = high_corr_list

        # --- 11. High Cardinality (New) ---
        # Already have nunique from overview potentially, but let's be explicit
        high_card_list = []
        for col, details in column_details.items():
            # If not unique but very high cardinality
            if details['decyphr_type'] == 'Text (High Cardinality)':
                 # We already flagged it in overview, but let's add specific stat
                 pass 
            # Check categorical cols that might have too many values for a chart
            if details['decyphr_type'] == 'Categorical':
                n_uniq = ddf[col].nunique().compute()
                if n_uniq > 50: # Threshold for "High" in categorical context
                    high_card_list.append({"column": col, "unique_count": int(n_uniq)})
        results["high_cardinality"] = high_card_list

        # --- 12. Quasi-Constant Columns (New) ---
        quasi_list = []
        for col in ddf.columns:
            # Find most frequent value count
            # value_counts can be expensive, do Top-1
            top_val_count = ddf[col].value_counts().head(1).values[0] if len(ddf[col].value_counts().head(1)) > 0 else 0
            if top_val_count > 0:
                dominance = top_val_count / total_rows
                if 0.99 <= dominance < 1.0:
                    quasi_list.append({"column": col, "dominance_pct": round(dominance*100, 2)})
        results["quasi_constant"] = quasi_list

        print("     ... Data quality scan complete.")
        return results

    except Exception as e:
        error_message = f"Failed during data quality analysis: {e}"
        print(f"     ... {error_message}")
        import traceback
        traceback.print_exc()
        return {"error": error_message}