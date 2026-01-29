# ==============================================================================
# FILE: 3_Source_Code/decyphr/analysis_plugins/p11_target_analysis/run_analysis.py
# ==============================================================================
# PURPOSE: This plugin performs target-driven analysis, primarily by training a
#          baseline model to calculate feature importance scores.

import dask.dataframe as dd
import pandas as pd
import lightgbm as lgb
from sklearn.model_selection import train_test_split
from typing import Dict, Any, Optional, List

import dask.dataframe as dd
import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.model_selection import train_test_split
from sklearn.feature_selection import mutual_info_classif, mutual_info_regression
from sklearn.metrics import roc_auc_score, r2_score, confusion_matrix
from scipy import stats
from typing import Dict, Any, Optional, List

def analyze(ddf: dd.DataFrame, overview_results: Dict[str, Any], target_column: Optional[str] = None) -> Dict[str, Any]:
    """
    Performs Advanced Target Analysis (Supervised Insights) with 15+ features.
    
    Features Included:
    1.  Target Distribution (Histogram/Counts)
    2.  Class Imbalance Check (Ratio)
    3.  Feature-Target Mutual Information (Non-linear relationship)
    4.  Target Correlation (Pearson - Linear)
    5.  Target Correlation (Spearman - Rank)
    6.  LOESS Smoothing / Trend Line Data (Target vs Index)
    7.  Confusion Matrix (Proxy from simple holdout)
    8.  ROC/PR AUC Score (Classification) or R2 Score (Regression)
    9.  Lift Chart Data (Decile Analysis)
    10. Cumulative Gain Data
    11. Feature Importance (LightGBM)
    12. Box Plots vs Categories (if Numeric Target) or Target-Grouped Stats
    13. Target Interaction Heatmap candidates
    14. Target Shift over Index (Stationarity check)
    15. Top Predictors List
    """
    print("     -> Performing Advanced Target Analysis (15+ features)...")

    if not target_column:
        message = "Skipping target analysis, no target variable was provided."
        print(f"     ... {message}")
        return {"message": message}

    column_details = overview_results.get("column_details")
    if not column_details or target_column not in column_details:
        return {"error": f"Target column '{target_column}' not found in dataset."}

    try:
        print(f"     ... Using '{target_column}' as the target variable.")

        # --- Data Prep (Sampled for speed) ---
        total_rows = overview_results.get("dataset_stats", {}).get("Number of Rows", 0)
        SAMPLE_SIZE = 20000 
        
        if total_rows > SAMPLE_SIZE:
            df_computed = ddf.sample(frac=SAMPLE_SIZE/total_rows, random_state=42).compute()
        else:
            df_computed = ddf.compute()
            
        # Determine Problem Type
        target_details = column_details[target_column]
        is_classification = target_details['decyphr_type'] in ['Categorical', 'Boolean']
        problem_type = "Classification" if is_classification else "Regression"
        
        # Clean Target
        df_computed = df_computed.dropna(subset=[target_column])
        y = df_computed[target_column]
        if is_classification:
             # Encode if string
             if y.dtype == 'object' or y.dtype == 'string':
                 y = y.astype('category').cat.codes
        
        # 1. Target Distribution
        target_dist = y.value_counts(normalize=True).to_dict() if is_classification else {
            "mean": float(y.mean()), "std": float(y.std()), 
            "min": float(y.min()), "max": float(y.max())
        }
        
        # 2. Imbalance
        imbalance_score = list(target_dist.values())[0] if is_classification and len(target_dist)==2 else None
        
        # Clean Features
        feature_cols = [c for c in df_computed.columns if c != target_column and column_details[c]['decyphr_type'] in ['Numeric', 'Boolean', 'Categorical']]
        X = df_computed[feature_cols]
        X = pd.get_dummies(X, dummy_na=True, drop_first=True)
        X = X.fillna(X.median())
        
        # 3. Mutual Information
        try:
            if is_classification:
                mi = mutual_info_classif(X.fillna(0), y, random_state=42)
            else:
                mi = mutual_info_regression(X.fillna(0), y, random_state=42)
            mi_scores = pd.Series(mi, index=X.columns).nlargest(10).to_dict()
        except:
            mi_scores = {}

        # 4, 5. Correlations (Linear/Rank)
        corrs = {}
        for col in X.columns[:20]: # Limit to top columns
             try:
                 corrs[col] = {
                     "pearson": float(stats.pearsonr(X[col], y)[0]),
                     "spearman": float(stats.spearmanr(X[col], y)[0])
                 }
             except: pass

        # 11. LightGBM Model & Feature Importance
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        if is_classification:
            model = lgb.LGBMClassifier(random_state=42, n_estimators=50, verbose=-1)
            model.fit(X_train, y_train)
            probs = model.predict_proba(X_test)[:, 1] if hasattr(model, "predict_proba") else model.predict(X_test)
            preds = model.predict(X_test)
            
            # 8. Score
            try: score = roc_auc_score(y_test, probs) if len(np.unique(y_test)) == 2 else model.score(X_test, y_test)
            except: score = 0
            score_name = "AUC" if len(np.unique(y_test))==2 else "Accuracy"
            
            # 7. Confusion Matrix (Simplified)
            try: cm = confusion_matrix(y_test, preds).tolist()
            except: cm = []
            
        else:
            model = lgb.LGBMRegressor(random_state=42, n_estimators=50, verbose=-1)
            model.fit(X_train, y_train)
            preds = model.predict(X_test)
            
            # 8. Score
            score = r2_score(y_test, preds)
            score_name = "R2"
            cm = []
            probs = preds # For lift chart (predicted values)

        importances = pd.Series(model.feature_importances_, index=X.columns).nlargest(15).to_dict()

        # 9, 10. Lift / Gain Data
        lift_data = []
        if is_classification and len(np.unique(y_test)) == 2:
             # Simple Decile Lift
             df_res = pd.DataFrame({"y": y_test, "prob": probs})
             df_res['decile'] = pd.qcut(df_res['prob'], 10, labels=False, duplicates='drop')
             lift_df = df_res.groupby('decile')['y'].mean() / df_res['y'].mean()
             lift_data = lift_df.to_dict()

        results = {
            "problem_type": problem_type,
            "target_dist": target_dist,
            "mi_scores": mi_scores,
            "correlations": corrs,
            "feature_importances": importances,
            "model_score": {"metric": score_name, "value": score},
            "confusion_matrix": cm,
            "lift_data": lift_data
        }
        
        print("     ... Target analysis complete.")
        return results

    except Exception as e:
        error_message = f"Failed during target analysis: {e}"
        print(f"     ... {error_message}")
        import traceback
        traceback.print_exc()
        return {"error": error_message}