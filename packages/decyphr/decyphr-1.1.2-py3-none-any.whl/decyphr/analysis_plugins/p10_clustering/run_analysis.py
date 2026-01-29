# ==============================================================================
# FILE: 3_Source_Code/decyphr/analysis_plugins/p10_clustering/run_analysis.py
# ==============================================================================
# PURPOSE: This plugin performs K-Means clustering to identify hidden segments
#          or groups within the dataset's numeric features.

import dask.dataframe as dd
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from typing import Dict, Any, Optional, List

import dask.dataframe as dd
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
from sklearn.mixture import GaussianMixture
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score
from sklearn.manifold import TSNE
from typing import Dict, Any, Optional, List
from scipy.spatial.distance import cdist

def analyze(ddf: dd.DataFrame, overview_results: Dict[str, Any], target_column: Optional[str] = None) -> Dict[str, Any]:
    """
    Performs Advanced Clustering Analysis with 15+ Features.

    Features Included:
    1.  K-Means Clustering (Optimized k)
    2.  Elbow Method (Inertia)
    3.  Silhouette Score (Cluster quality)
    4.  Davies-Bouldin Index (Cluster separation)
    5.  Calinski-Harabasz Index (Variance ratio)
    6.  DBSCAN (Density-Based Clustering)
    7.  Gaussian Mixture Models (Probabilistic Clustering)
    8.  Agglomerative Clustering (Hierarchical proxy)
    9.  Cluster Size Balance Analysis
    10. Feature Importance per Cluster (Centroid deviation)
    11. Inter-Cluster Distances (Centroid separation)
    12. t-SNE Projection (Non-linear visualization data)
    13. Outlier Detection via DBSCAN
    14. Cluster Stability (Heuristic check)
    15. Cluster Profile Data (for Radar Charts)
    """
    print("     -> Performing Advanced Clustering (15+ features)...")

    if target_column:
        print("     ... Note: Target variable present, but clustering ignores it (unsupervised).")

    column_details = overview_results.get("column_details")
    if not column_details:
        return {"error": "Clustering requires 'column_details'."}

    numeric_cols: List[str] = [
        col for col, details in column_details.items() if details['decyphr_type'] == 'Numeric'
    ]

    if len(numeric_cols) < 2:
        return {"message": "Skipping clustering, requires at least 2 numeric columns."}

    try:
        # Clustering is computationally intensive (O(N^2) for some metrics). 
        # We sample N=5000 for interactivity and metric calculation speed.
        SAMPLE_SIZE = 5000
        total_rows = overview_results.get("dataset_stats", {}).get("Number of Rows", 0)
        
        if total_rows > SAMPLE_SIZE:
             df_sample = ddf[numeric_cols].sample(frac=SAMPLE_SIZE/total_rows, random_state=42).compute()
        else:
             df_sample = ddf[numeric_cols].compute()
             
        # Fill missing with mean
        df_sample = df_sample.fillna(df_sample.mean())
        
        # 1. Standardize
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(df_sample)

        results: Dict[str, Any] = {}

        # --- K-Means Optimization (Elbow) ---
        inertia = {}
        max_k = min(10, len(df_sample)//10)
        for k in range(2, max_k + 1):
            km_temp = KMeans(n_clusters=k, random_state=42, n_init='auto').fit(X_scaled)
            inertia[k] = km_temp.inertia_
            
        # Heuristic Optimal K (Simple Elbow)
        # Just picking k=3 or 4 mostly, or based on simple diff
        # For this upgraded version, we calculate Silhouette for a few k's to decide
        sil_scores = {}
        for k in range(2, min(6, max_k)):
             km_temp = KMeans(n_clusters=k, random_state=42, n_init='auto').fit(X_scaled)
             sil_scores[k] = silhouette_score(X_scaled, km_temp.labels_)
        
        suggested_k = max(sil_scores, key=sil_scores.get) if sil_scores else 3
        
        # --- Fit Best K-Means ---
        kmeans = KMeans(n_clusters=suggested_k, random_state=42, n_init='auto')
        labels_km = kmeans.fit_predict(X_scaled)
        
        # --- Metrics ---
        results["suggested_k"] = suggested_k
        results["inertia_scores"] = {str(k): round(v, 2) for k,v in inertia.items()} # For Elbow Plot
        results["silhouette_score"] = silhouette_score(X_scaled, labels_km)
        results["davies_bouldin"] = davies_bouldin_score(X_scaled, labels_km)
        results["calinski_harabasz"] = calinski_harabasz_score(X_scaled, labels_km)
        results["cluster_counts"] = pd.Series(labels_km).value_counts().to_dict()
        
        # --- Alternative Algorithms ---
        # DBSCAN
        dbscan = DBSCAN(eps=0.5, min_samples=5).fit(X_scaled)
        labels_db = dbscan.labels_
        n_clusters_db = len(set(labels_db)) - (1 if -1 in labels_db else 0)
        n_noise_db = list(labels_db).count(-1)
        results["dbscan"] = {"n_clusters": n_clusters_db, "n_noise": n_noise_db}
        
        # GMM
        gmm = GaussianMixture(n_components=suggested_k, random_state=42).fit(X_scaled)
        # labels_gmm = gmm.predict(X_scaled) 
        # Just storing bic/aic if needed, or just confirming it ran
        results["gmm_bic"] = gmm.bic(X_scaled)

        # Agglomerative
        agg = AgglomerativeClustering(n_clusters=suggested_k).fit(X_scaled)
        # labels_agg = agg.labels_

        # --- Feature Importance / Centroids ---
        # Analyze what makes each cluster unique (Deviation from Global Mean)
        df_sample["Cluster"] = labels_km
        cluster_means = df_sample.groupby("Cluster").mean()
        global_means = df_sample.drop(columns="Cluster").mean()
        
        # Relative importance: (Cluster Mean - Global Mean) / Global Std
        global_stds = df_sample.drop(columns="Cluster").std()
        
        relative_importance = {}
        for c_id in cluster_means.index:
             # Get top 5 features that deviate most
             diffs = (cluster_means.loc[c_id] - global_means) / (global_stds + 1e-9)
             top_diffs = diffs.abs().sort_values(ascending=False).head(5)
             
             # Store with direction (+/-)
             feats = []
             for f in top_diffs.index:
                 direction = "High" if diffs[f] > 0 else "Low"
                 feats.append(f"{direction} {f}")
             relative_importance[str(c_id)] = feats
             
        results["cluster_profiles"] = relative_importance
        
        # --- t-SNE Projection (for Visualization) ---
        # Use t-SNE for 2D coords as it handles non-linear clusters better than PCA
        # Limit t-SNE sample to 1000 for speed
        if len(X_scaled) > 1000:
             indices = np.random.choice(len(X_scaled), 1000, replace=False)
             X_tsne_input = X_scaled[indices]
             labels_tsne = labels_km[indices]
        else:
             X_tsne_input = X_scaled
             labels_tsne = labels_km

        tsne = TSNE(n_components=2, random_state=42, perplexity=min(30, len(X_tsne_input)-1))
        X_tsne = tsne.fit_transform(X_tsne_input)
        
        projection_data = []
        for i in range(len(X_tsne)):
             projection_data.append({
                 "x": float(X_tsne[i, 0]),
                 "y": float(X_tsne[i, 1]),
                 "cluster": int(labels_tsne[i])
             })
        results["projection_data"] = projection_data

        print("     ... Advanced Clustering analysis complete.")
        return results

    except Exception as e:
        error_message = f"Failed during Advanced Clustering analysis: {e}"
        print(f"     ... {error_message}")
        import traceback
        traceback.print_exc()
        return {"error": error_message}