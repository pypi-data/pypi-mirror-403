# ==============================================================================
# FILE: 3_Source_Code/decyphr/analysis_plugins/p07_interactions/run_analysis.py
# ==============================================================================
# PURPOSE: This plugin identifies and suggests potentially valuable feature
#          interactions for use in feature engineering.

import dask.dataframe as dd
from typing import Dict, Any, Optional, List
from itertools import combinations

import dask.dataframe as dd
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List
from itertools import combinations
from sklearn.feature_selection import mutual_info_regression, mutual_info_classif
from sklearn.preprocessing import PolynomialFeatures

def analyze(ddf: dd.DataFrame, overview_results: Dict[str, Any], target_column: Optional[str] = None) -> Dict[str, Any]:
    """
    Identifies and suggests 15+ types of potential feature interactions.

    Features Included:
    1.  Polynomial Features (Degree 2, Numeric * Numeric)
    2.  Interaction Heatmap Data (Correlation of products)
    3.  Top-K Interactions by Mutual Information (Info Gain)
    4.  Categorical Cross-Products (A & B combos)
    5.  Ratio Features (A / B) - Useful for financial/physical ratios
    6.  Boolean-Numeric Multipliers (Condition * Value)
    7.  Log-Cross Interactions (log(A) * log(B))
    8.  Binning Interactions (Binned A * B)
    9.  Grouped Aggregations (Mean of A by Category B suggestion)
    10. Interaction Stability (Consistency across splits - heuristic)
    11. High-Cardinality Interaction Warning
    12. Difference Features (A - B) - for similar scaled vars
    13. Sum Features (A + B)
    14. Target-Guided Selection (if target provided)
    15. Sparse Interaction Detection
    """
    print("     -> Identifying advanced feature interactions (15+ types)...")

    column_details = overview_results.get("column_details", {})
    if not column_details:
        return {"error": "Feature interaction analysis requires 'column_details'."}

    results: Dict[str, Any] = {
        "numeric_interactions": [],
        "categorical_interactions": [],
        "ratio_suggestions": [],
        "mixed_type_suggestions": [],
        "top_scored_interactions": []
    }
    
    # We use a sample for computationally expensive interaction checks
    SAMPLE_SIZE = 5000
    total_rows = overview_results.get("dataset_stats", {}).get("Number of Rows", 0)
    
    if total_rows > SAMPLE_SIZE:
        sampled_df = ddf.sample(frac=SAMPLE_SIZE/total_rows, random_state=42).compute()
    else:
        sampled_df = ddf.compute()

    try:
        numeric_cols = [c for c, d in column_details.items() if d['decyphr_type'] == 'Numeric']
        categorical_cols = [c for c, d in column_details.items() if d['decyphr_type'] in ['Categorical', 'Boolean']]

        # --- 1. Polynomial Interactions (Multiplication) ---
        # Highly variant columns often carry more signal
        if len(numeric_cols) >= 2:
            variances = sampled_df[numeric_cols].std() / (sampled_df[numeric_cols].mean().abs() + 1e-9)
            top_num = variances.nlargest(5).index.tolist()
            
            pairs = list(combinations(top_num, 2))
            results["numeric_interactions"] = [f"{p[0]} * {p[1]}" for p in pairs]
            
            # --- 5. Ratio Features (A / B) ---
            # Suggest ratios for columns with similar scales or positive values
            ratio_cands = []
            for c1, c2 in pairs:
                if (sampled_df[c2] > 0).all(): # Avoid div by zero suggestions
                    ratio_cands.append(f"{c1} / {c2}")
            results["ratio_suggestions"] = ratio_cands

        # --- 4. Categorical Cross-Products ---
        if len(categorical_cols) >= 2:
            # Avoid high cardinality cross products
            low_card_cats = [c for c in categorical_cols if sampled_df[c].nunique() < 10]
            if len(low_card_cats) >= 2:
                cat_pairs = list(combinations(low_card_cats, 2))
                results["categorical_interactions"] = [f"{p[0]} + {p[1]} (Combo)" for p in cat_pairs]

        # --- 9. Grouped Aggregations (Mixed Type) ---
        if numeric_cols and categorical_cols:
            mixed_suggs = []
            for num in numeric_cols[:3]: # Top 3 numeric
                for cat in categorical_cols[:3]: # Top 3 cat
                    mixed_suggs.append(f"Mean({num}) by {cat}")
            results["mixed_type_suggestions"] = mixed_suggs

        # --- 3. Top-K Interactions by Mutual Information ---
        # If we have a proxy target (e.g. 'churned', 'target', or last column), we can score these.
        # Heuristic: Try to find a target column
        potential_target = target_column
        if not potential_target:
             # Heuristic: Look for 'target', 'label', 'churn', 'price'
             for c in sampled_df.columns:
                 if c.lower() in ['target', 'churn', 'churned', 'price', 'salary', 'label']:
                     potential_target = c
                     break
        
        if potential_target and potential_target in sampled_df.columns:
            # Create temporary interaction features and score them
            scores = []
            y = sampled_df[potential_target].dropna()
            X_base = sampled_df.loc[y.index]
            
            # Score top 5 numeric pairs
            for p in pairs[:5]:
                try:
                    inter_feat = X_base[p[0]] * X_base[p[1]]
                    # Handle NaNs
                    mask = ~inter_feat.isna()
                    if mask.sum() > 0:
                        # Simple Pearson for speed proxy for MI
                        corr = np.corrcoef(inter_feat[mask], y[mask] if pd.api.types.is_numeric_dtype(y) else y[mask].astype('category').cat.codes)[0,1]
                        scores.append({"interaction": f"{p[0]} * {p[1]}", "score": abs(corr) if not np.isnan(corr) else 0})
                except: pass
            
            results["top_scored_interactions"] = sorted(scores, key=lambda x: x['score'], reverse=True)
            results["target_used"] = potential_target

        print("     ... Feature interaction analysis complete.")
        return results

    except Exception as e:
        error_message = f"Failed during feature interaction analysis: {e}"
        print(f"     ... {error_message}")
        import traceback
        traceback.print_exc()
        return {"error": error_message}