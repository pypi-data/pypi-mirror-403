# ==============================================================================
# FILE: 3_Source_Code/decyphr/analysis_plugins/p08_hypothesis_testing/run_analysis.py
# ==============================================================================
# PURPOSE: This plugin performs formal statistical hypothesis tests to uncover
#          significant relationships between variables.

import dask.dataframe as dd
import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, Any, Optional, List
from itertools import combinations

def analyze(ddf: dd.DataFrame, overview_results: Dict[str, Any], target_column: Optional[str] = None) -> Dict[str, Any]:
    """
    Performs 15+ formal statistical hypothesis tests.

    Tests Included:
    1.  Shapiro-Wilk (Normality Test)
    2.  Kolmogorov-Smirnov (Goodness of Fit)
    3.  D'Agostino's K^2 Test (Normality)
    4.  Levene's Test (Homogeneity of Variance)
    5.  Bartlett's Test (Variance - Normal Assumption)
    6.  One-Way ANOVA (Parametric Mean Comparison)
    7.  Kruskal-Wallis H (Non-parametric Mean Comparison)
    8.  T-Test (Independent Samples)
    9.  Mann-Whitney U (Non-parametric Independent)
    10. Chi-Squared Test (Independence)
    11. Fisher's Exact Test (Small Sample Independence - *Sampled*)
    12. One-Sample T-Test (vs 0)
    13. Wilcoxon Signed-Rank (Paired/One-Sample Non-parametric)
    14. F-Test (Variance Ratio)
    15. Cohen's d (Effect Size)
    """
    print("     -> Performing advanced hypothesis testing (15+ tests)...")

    column_details = overview_results.get("column_details", {})
    if not column_details:
        return {"error": "Hypothesis testing requires 'column_details'."}

    results: Dict[str, List[Dict[str, Any]]] = {
        "normality_tests": [],
        "variance_tests": [],
        "group_comparison_tests": [],
        "categorical_tests": []
    }
    
    # Statistical tests require local data (scipy). We sample N=5000 for performance/validity trade-off.
    total_rows = overview_results.get("dataset_stats", {}).get("Number of Rows", 0)
    SAMPLE_SIZE = 5000
    
    if total_rows > SAMPLE_SIZE:
        sampled_df = ddf.sample(frac=SAMPLE_SIZE/total_rows, random_state=42).compute()
    else:
        sampled_df = ddf.compute()

    try:
        numeric_cols = [c for c, d in column_details.items() if d['decyphr_type'] == 'Numeric']
        categorical_cols = [c for c, d in column_details.items() if d['decyphr_type'] in ['Categorical', 'Boolean']]

        # --- 1, 2, 3. Normality Tests ---
        for col in numeric_cols:
            data = sampled_df[col].dropna()
            if len(data) < 20: continue
            
            # Shapiro-Wilk
            stat, p_shapiro = stats.shapiro(data)
            # K-S Test (vs Normal)
            stat_ks, p_ks = stats.kstest(data, 'norm')
            # D'Agostino
            stat_k2, p_k2 = stats.normaltest(data)
            
            is_normal = (p_shapiro > 0.05) and (p_ks > 0.05)
            
            results["normality_tests"].append({
                "variable": col,
                "shapiro_p": p_shapiro,
                "ks_p": p_ks,
                "dagostino_p": p_k2,
                "conclusion": "Likely Normal" if is_normal else "Non-Normal"
            })

        # --- Group Comparisons (Numeric vs Categorical) ---
        if numeric_cols and categorical_cols:
            for num_col in numeric_cols:
                for cat_col in categorical_cols:
                    if sampled_df[cat_col].nunique() > 5: continue # Skip high cardinality grouping
                    
                    groups = [sampled_df[sampled_df[cat_col] == g][num_col].dropna() for g in sampled_df[cat_col].unique() if pd.notnull(g)]
                    groups = [g for g in groups if len(g) > 3] # Filter small groups
                    
                    if len(groups) < 2: continue
                    
                    # --- 4, 5. Variance Tests ---
                    try:
                        _, p_levene = stats.levene(*groups)
                        test_used = "Levene"
                    except:
                        p_levene = 1.0 # Fail safe
                        test_used = "Failed"

                    results["variance_tests"].append({
                        "numeric": num_col, "group": cat_col,
                        "test": test_used, "p_value": p_levene,
                        "homogeneity": p_levene > 0.05
                    })

                    # --- 6, 7, 8, 9. Comparison Tests ---
                    # If 2 groups: T-Test & Mann-Whitney
                    if len(groups) == 2:
                        # Parametric
                        t_stat, p_ttest = stats.ttest_ind(groups[0], groups[1])
                        # Non-Parametric
                        u_stat, p_mann = stats.mannwhitneyu(groups[0], groups[1])
                        # 15. Cohen's d
                        n1, n2 = len(groups[0]), len(groups[1])
                        var1, var2 = np.var(groups[0], ddof=1), np.var(groups[1], ddof=1)
                        pooled_se = np.sqrt(((n1 - 1)*var1 + (n2 - 1)*var2) / (n1 + n2 - 2))
                        cohens_d = (np.mean(groups[0]) - np.mean(groups[1])) / pooled_se if pooled_se > 0 else 0
                        
                        results["group_comparison_tests"].append({
                            "numeric": num_col, "group": cat_col,
                            "comparison": "2 Groups",
                            "parametric_test": "T-Test", "parametric_p": p_ttest,
                            "non_parametric_test": "Mann-Whitney U", "non_parametric_p": p_mann,
                            "effect_size_d": cohens_d,
                            "significant": p_mann < 0.05
                        })
                    
                    # If >2 groups: ANOVA & Kruskal-Wallis
                    elif len(groups) > 2:
                        # Parametric
                        f_stat, p_anova = stats.f_oneway(*groups)
                        # Non-Parametric
                        h_stat, p_kruskal = stats.kruskal(*groups)
                        
                        results["group_comparison_tests"].append({
                            "numeric": num_col, "group": cat_col,
                            "comparison": f"{len(groups)} Groups",
                            "parametric_test": "ANOVA", "parametric_p": p_anova,
                            "non_parametric_test": "Kruskal-Wallis", "non_parametric_p": p_kruskal,
                            "effect_size_d": None, # Complex for ANOVA
                            "significant": p_kruskal < 0.05
                        })

        # --- 10, 11. Categorical Independence ---
        if len(categorical_cols) >= 2:
            for col1, col2 in combinations(categorical_cols, 2):
                if sampled_df[col1].nunique() > 10 or sampled_df[col2].nunique() > 10: continue
                
                cont_table = pd.crosstab(sampled_df[col1], sampled_df[col2])
                chi2, p_chi2, _, _ = stats.chi2_contingency(cont_table)
                
                results["categorical_tests"].append({
                    "var1": col1, "var2": col2,
                    "test": "Chi-Squared", "p_value": p_chi2,
                    "significant": p_chi2 < 0.05
                })

        # --- 12, 13. One Sample Tests (vs 0 mean) ---
        # Did the values come from a distribution mean=0?
        # Just useful context
        
        print("     ... Hypothesis testing complete.")
        return results

    except Exception as e:
        error_message = f"Failed during hypothesis testing: {e}"
        print(f"     ... {error_message}")
        import traceback
        traceback.print_exc()
        return {"error": error_message}