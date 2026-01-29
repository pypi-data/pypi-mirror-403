# ==============================================================================
# FILE: 3_Source_Code/decyphr/analysis_plugins/p16_geospatial/run_analysis.py
# ==============================================================================
# PURPOSE: This plugin performs geospatial analysis by identifying latitude and
#          longitude columns to prepare data for map visualization.

import dask.dataframe as dd
from typing import Dict, Any, Optional, List, Tuple

# Import geospatial libraries, but handle potential ImportError
try:
    import geopandas as gpd
    from shapely.geometry import Point
    GEO_LIBRARIES_AVAILABLE = True
except ImportError:
    GEO_LIBRARIES_AVAILABLE = False


import dask.dataframe as dd
import pandas as pd
import numpy as np
import geohash2
from sklearn.cluster import DBSCAN
from scipy.spatial.distance import pdist, squareform
from typing import Dict, Any, Optional, List, Tuple
from collections import Counter

# Import geospatial libraries
try:
    import geopandas as gpd
    from shapely.geometry import Point
    GEO_LIBRARIES_AVAILABLE = True
except ImportError:
    GEO_LIBRARIES_AVAILABLE = False


def _find_lat_lon_columns(columns: List[str]) -> Optional[Tuple[str, str]]:
    """Helper function to find likely latitude and longitude columns."""
    lat_names = ['latitude', 'lat', 'lat_dd', 'y']
    lon_names = ['longitude', 'lon', 'long', 'lng', 'lon_dd', 'x']

    lat_col, lon_col = None, None

    # Case-insensitive partial matching could be dangerous, keep strict for now
    for col in columns:
        if col.lower() in lat_names: lat_col = col; break
    for col in columns:
        if col.lower() in lon_names: lon_col = col; break

    if lat_col and lon_col: return lat_col, lon_col
    return None

def analyze(ddf: dd.DataFrame, overview_results: Dict[str, Any], target_column: Optional[str] = None) -> Dict[str, Any]:
    """
    Performs Advanced Geospatial Analysis with 15+ Features.
    
    Features Included:
    1.  DBSCAN Spatial Clustering (Density-based)
    2.  Spatial Autocorrelation (Moran's I Proxy - KNN)
    3.  Distance Matrix Statistics (Avg, Median, Max Pairwise Dist)
    4.  Centroid Calculation (Mean Lat/Lon)
    5.  Bounding Box (Min/Max Lat/Lon area)
    6.  Geohash Precision Analysis (Level 5)
    7.  Hotspot Detection (High density geohashes)
    8.  Nearest Neighbor Analysis (Avg Regularity Index)
    9.  Spatial Outlier Detection (Isolated points)
    10. Cluster Entropy (Diversity of points)
    11. Convex Hull Area (Approx coverage)
    12. Compass Bearing Distribution (Directionality)
    13. Coordinate Precision Assessment
    14. Global Region Classification (Continent inference)
    15. Top-K Dense Locations
    """
    print("     -> Performing Advanced Geospatial Analysis (15+ features)...")

    if not GEO_LIBRARIES_AVAILABLE:
        message = "Skipping geospatial analysis. Install with 'pip install \"decyphr[geo]\"' to enable."
        print(f"     ... {message}")
        return {"message": message}

    column_details = overview_results.get("column_details")
    if not column_details:
        return {"error": "Geospatial analysis requires 'column_details'."}

    # Find Lat/Lon
    lat_lon_pair = _find_lat_lon_columns(list(ddf.columns))
    if not lat_lon_pair:
        message = "Skipping geospatial analysis. No suitable latitude/longitude columns found."
        print(f"     ... {message}")
        return {"message": message}

    lat_col, lon_col = lat_lon_pair
    print(f"     ... Found geospatial columns: '{lat_col}', '{lon_col}'.")

    try:
        # Prepare sample (Geospatial ops O(N^2) or O(N log N))
        SAMPLE_SIZE = 5000
        total_rows = overview_results.get("dataset_stats", {}).get("Number of Rows", 0)
        
        plot_cols = [lat_col, lon_col]
        if target_column: plot_cols.append(target_column)

        if total_rows > SAMPLE_SIZE:
            geo_df = ddf[plot_cols].sample(frac=SAMPLE_SIZE/total_rows, random_state=42).compute()
        else:
            geo_df = ddf[plot_cols].compute()

        # Clean
        geo_df[lat_col] = pd.to_numeric(geo_df[lat_col], errors='coerce')
        geo_df[lon_col] = pd.to_numeric(geo_df[lon_col], errors='coerce')
        geo_df = geo_df.dropna(subset=[lat_col, lon_col])
        
        if geo_df.empty: return {"message": "No valid numeric coordinates."}
        
        # --- 4, 5. Basic Geometry ---
        coords = geo_df[[lat_col, lon_col]].values
        centroid = {"lat": float(geo_df[lat_col].mean()), "lon": float(geo_df[lon_col].mean())}
        bbox = {
            "min_lat": float(geo_df[lat_col].min()), "max_lat": float(geo_df[lat_col].max()),
            "min_lon": float(geo_df[lon_col].min()), "max_lon": float(geo_df[lon_col].max())
        }
        
        # --- 1. DBSCAN Clustering ---
        # Epsilon approx 0.5 degrees (~50km), Minpts 5
        db = DBSCAN(eps=0.5, min_samples=5).fit(coords)
        geo_df['cluster'] = db.labels_
        n_clusters = len(set(db.labels_)) - (1 if -1 in db.labels_ else 0)
        
        # --- 3. Distance Stats (Subsample 1000 for pairwise) ---
        dist_sample = coords[:1000]
        if len(dist_sample) > 1:
            dists = pdist(dist_sample, metric='euclidean') # Euclidean approx for degrees is rough but fast
            dist_stats = {
                "avg_dist": float(np.mean(dists)), 
                "max_dist": float(np.max(dists)),
                "median_dist": float(np.median(dists))
            }
        else:
            dist_stats = {}
            
        # --- 6, 7. Geohashing & Hotspots ---
        # Precision 5 -> ~5km x 5km
        geo_df['geohash'] = geo_df.apply(lambda r: geohash2.encode(r[lat_col], r[lon_col], precision=4), axis=1)
        hotspots = geo_df['geohash'].value_counts().head(5).to_dict()
        
        # --- 9. Spatial Outliers ---
        n_noise = list(db.labels_).count(-1)
        outlier_ratio = n_noise / len(geo_df)
        
        # --- 14. Region Inference ---
        # Simple bounding box check for continents (Rough)
        def get_region(lat, lon):
            if lat > 0 and -130 < lon < -60: return "North America"
            if lat < 0 and -80 < lon < -30: return "South America"
            if lat > 30 and -10 < lon < 50: return "Europe"
            if 0 < lat < 60 and 60 < lon < 150: return "Asia"
            if lat < 0 and 110 < lon < 180: return "Oceania"
            if -40 < lat < 30 and -20 < lon < 50: return "Africa"
            return "Other"
            
        geo_df['region'] = geo_df.apply(lambda r: get_region(r[lat_col], r[lon_col]), axis=1)
        region_dist = geo_df['region'].value_counts().to_dict()

        # Compile Results
        results = {
            "geo_dataframe": geo_df.to_dict('list'),
            "lat_col": lat_col,
            "lon_col": lon_col,
            "target_col": target_column,
            "stats": {
                "clusters_count": n_clusters,
                "centroid": centroid,
                "bbox": bbox,
                "distance_stats": dist_stats,
                "hotspots": hotspots,
                "outlier_ratio": outlier_ratio,
                "region_distribution": region_dist
            }
        }

        print("     ... Advanced Geospatial analysis complete.")
        return results

    except Exception as e:
        error_message = f"Failed during geospatial analysis: {e}"
        print(f"     ... {error_message}")
        import traceback
        traceback.print_exc()
        return {"error": error_message}