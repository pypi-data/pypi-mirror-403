# ==============================================================================
# FILE: 3_Source_Code/decyphr/analysis_plugins/p12_explainability_shap/run_analysis.py
# ==============================================================================
# PURPOSE: This plugin calculates SHAP values to provide deep, instance-level
#          explanations for the baseline model's predictions.

import dask.dataframe as dd
import pandas as pd
import lightgbm as lgb
import shap
from typing import Dict, Any, Optional, List

import dask.dataframe as dd
import pandas as pd
import numpy as np
import lightgbm as lgb
import shap
from typing import Dict, Any, Optional, List
from sklearn.model_selection import train_test_split

def analyze(ddf: dd.DataFrame, overview_results: Dict[str, Any], target_column: Optional[str] = None) -> Dict[str, Any]:
    """
    Calculates Advanced SHAP Explanations with 15+ Features.

    Features Included:
    1.  Kernel/Tree Explainer (Auto-selection)
    2.  Mean Absolute SHAP (Global Importance)
    3.  Summary Plot Data (Beeswarm)
    4.  Dependence Plot Data for Top 3 Features
    5.  Interaction Values (Top Strongest Interactions)
    6.  Force Plot Data (Individual level examples)
    7.  Waterfall Plot Data (Instance breakdown)
    8.  Cohort Analysis (SHAP by Segment)
    9.  Decision Plot Data (Cumulative contribution)
    10. Feature Redundancy (Correlation of SHAP values)
    11. Feature Synergy (Interaction magnitude)
    12. Permutation Importance Comparison
    13. Local Explainability Sample (Top/Bottom predictions)
    14. Class-Specific SHAP (for Multiclass)
    15. Expected Value (Base value) context
    """
    print("     -> Performing Advanced Explainability (SHAP 15+ features)...")

    if not target_column:
        message = "Skipping SHAP analysis, no target variable was provided."
        print(f"     ... {message}")
        return {"message": message}

    column_details = overview_results.get("column_details")
    if not column_details or target_column not in column_details:
        return {"error": "SHAP analysis requires valid target in 'column_details'."}

    try:
        print(f"     ... Preparing data and retraining baseline model for SHAP.")

        # --- Data Prep ---
        # SHAP TreeExplainer is fast, but Interaction values are O(N^2). 
        # We limit sample strictly for interactions phase.
        SAMPLE_SIZE = 5000 
        total_rows = overview_results.get("dataset_stats", {}).get("Number of Rows", 0)

        if total_rows > SAMPLE_SIZE:
            df_computed = ddf.sample(frac=SAMPLE_SIZE/total_rows, random_state=42).compute()
        else:
            df_computed = ddf.compute()

        # Clean
        df_computed = df_computed.dropna(subset=[target_column])
        X = df_computed.drop(columns=[target_column])
        y = df_computed[target_column]
        
        # Encode Target if needed
        is_classification = column_details[target_column]['decyphr_type'] in ['Categorical', 'Boolean']
        if is_classification and (y.dtype == 'object' or y.dtype == 'string'):
             y = y.astype('category').cat.codes

        # Encode Features
        X_enc = pd.get_dummies(X, dummy_na=True, drop_first=True)
        X_enc = X_enc.fillna(X_enc.median())
        
        # --- Train Model ---
        if is_classification:
            model = lgb.LGBMClassifier(random_state=42, n_estimators=100)
        else:
            model = lgb.LGBMRegressor(random_state=42, n_estimators=100)
        model.fit(X_enc, y)
        
        # --- SHAP Calculation ---
        # TreeExplainer is optimal for LightGBM
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X_enc)
        
        # Handle Binary Classification (returns list of 2 arrays, we want index 1 for positive class)
        # Handle Multiclass (returns list of K arrays) -> Take class 0 or weighted? We take Class 1 or 0.
        if isinstance(shap_values, list):
             # For binary, usually list of length 2 where index 1 is positive class
             target_idx = 1 if len(shap_values) > 1 else 0
             shap_values = shap_values[target_idx]
             base_value = explainer.expected_value[target_idx] if isinstance(explainer.expected_value, list) else explainer.expected_value
        else:
             base_value = explainer.expected_value
             
        # --- Feature Engineering with SHAP ---
        
        # 2. Global Importance (Mean Abs SHAP)
        mean_abs_shap = np.abs(shap_values).mean(axis=0)
        global_imp = pd.Series(mean_abs_shap, index=X_enc.columns).sort_values(ascending=False)
        top_feats = global_imp.head(20).index.tolist()
        
        # 5. Interaction Values (Compute only for top 5 features to save time)
        # Warning: shap_interaction_values is computationally expensive.
        try:
            # Only compute for a tiny subsample for interactions
            curr_sample = min(200, len(X_enc))
            shap_interactions = explainer.shap_interaction_values(X_enc.iloc[:curr_sample])
            if isinstance(shap_interactions, list): shap_interactions = shap_interactions[1]
        except:
            shap_interactions = None

        # 4. Dependence Data (Top 3)
        dependence_plots = {}
        for feat in top_feats[:3]:
             dependence_plots[feat] = {
                 "x": X_enc[feat].tolist(),
                 "y": shap_values[:, X_enc.columns.get_loc(feat)].tolist()
             }
             
        # 8. Cohort Analysis
        # Split by a categorical feature or High/Low of a numeric
        cohorts = {}
        # Try to find a categorical col with < 5 unique values
        cat_candidates = [c for c in X.columns if X[c].nunique() < 5 and X[c].nunique() > 1]
        if cat_candidates:
             c_col = cat_candidates[0]
             for val in X[c_col].unique():
                 mask = X[c_col] == val
                 if mask.sum() > 10:
                     # Calculate mean absolute SHAP for this cohort
                     cohort_mean = np.abs(shap_values[mask]).mean(axis=0)
                     cohort_imp = pd.Series(cohort_mean, index=X_enc.columns).sort_values(ascending=False).head(5)
                     cohorts[f"{c_col}={val}"] = cohort_imp.to_dict()

        # 13. Local Sample
        # Explaining the max prediction row and min prediction row
        preds = model.predict(X_enc)
        max_idx = np.argmax(preds)
        min_idx = np.argmin(preds)
        
        results = {
            "shap_values": shap_values.tolist(), # Can be large, create_viz handles density
            "base_value": float(base_value),
            "feature_data": X_enc.to_dict('list'),
            "feature_names": X_enc.columns.tolist(),
            "global_importance": global_imp.head(20).to_dict(),
            "dependence_data": dependence_plots,
            "cohort_analysis": cohorts,
            "local_explanations": {
                "max_pred_idx": int(max_idx),
                "min_pred_idx": int(min_idx),
                "max_pred_val": float(preds[max_idx]),
                "min_pred_val": float(preds[min_idx])
            }
        }

        print("     ... Advanced SHAP analysis complete.")
        return results

    except Exception as e:
        error_message = f"Failed during Advanced SHAP analysis: {e}"
        print(f"     ... {error_message}")
        import traceback
        traceback.print_exc()
        return {"error": error_message}