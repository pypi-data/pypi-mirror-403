# ==============================================================================
# FILE: 3_Source_Code/decyphr/analysis_plugins/p01_overview/run_analysis.py
# ==============================================================================
# PURPOSE: Core logic for the Overview analysis plugin. Performs high-level
#          characterization, structural analysis, and deep profiling of the dataset.
#          Includes 30+ features including Big Data resilience.

import dask.dataframe as dd
import pandas as pd
import numpy as np
import re
import hashlib
import itertools
from typing import Dict, Any, Optional, List, Tuple

# Try importing scipy for distribution analysis
try:
    from scipy.stats import shapiro, skew, kurtosis
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

# --- Constants & Regex Patterns ---
REGEX_PATTERNS = {
    "email": r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
    "url": r'^(https?|ftp)://[^\s/$.?#].[^\s]*$',
    "ip_address": r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$',
    "phone": r'^\+?1?\d{9,15}$', # Basic international phone regex
}

def _classify_column(dtype: Any, nunique: int, col_size: int, col_name: str, sample_values: pd.Series) -> str:
    """Classifies a column with enhanced logic including semantic types."""
    
    # 1. Semantic Checks (on Object/String columns)
    if pd.api.types.is_string_dtype(dtype) or pd.api.types.is_object_dtype(dtype):
        # Check a sample for semantic matches
        valid_sample = sample_values.dropna().astype(str)
        if len(valid_sample) > 0:
            for type_name, pattern in REGEX_PATTERNS.items():
                matches = valid_sample.str.match(pattern).sum()
                if matches / len(valid_sample) > 0.8: # 80% threshold
                    return f"Text ({type_name.title()})"

    # 2. Standard Structural Checks
    CATEGORICAL_THRESHOLD = 50
    if nunique == 1:
        return "Constant"
    if nunique == 2:
        return "Boolean"
    if pd.api.types.is_datetime64_any_dtype(dtype):
        return "Datetime"
    if pd.api.types.is_numeric_dtype(dtype):
        if nunique <= CATEGORICAL_THRESHOLD:
            return "Categorical (Numeric)"
        return "Numeric"
    
    # 3. ID vs Text
    if nunique == col_size:
        return "Unique ID"
    if nunique / col_size > 0.9: # High cardinality ratio
        return "High Cardinality ID"
    
    if nunique <= CATEGORICAL_THRESHOLD:
        return "Categorical"
        
    return "Text (High Cardinality)"

def _calculate_health_score(missing_pct: float, duplicate_pct: float, outlier_pct: float = 0) -> float:
    """Calculates a 0-100 health score based on data quality metrics."""
    # Weights: Missing (40%), Duplicates (30%), Outliers (30%)
    score = 100 - (missing_pct * 0.4 + duplicate_pct * 0.3 + outlier_pct * 0.3)
    return max(0, round(score, 1))

def _get_memory_optimization_tips(df: pd.DataFrame) -> List[str]:
    """Suggests memory optimizations."""
    tips = []
    for col in df.select_dtypes(include=['float64']).columns:
        tips.append(f"Column '{col}' (float64) can likely be downcast to float32.")
    for col in df.select_dtypes(include=['int64']).columns:
        tips.append(f"Column '{col}' (int64) can likely be downcast to int32 or int16.")
    for col in df.select_dtypes(include=['object']).columns:
        if df[col].nunique() / len(df) < 0.5:
             tips.append(f"Column '{col}' (object) has low cardinality and should be 'category'.")
    return tips[:5] # Return top 5 tips

def _find_composite_keys(df: pd.DataFrame) -> List[str]:
    """Finds combinations of 2 columns that form a unique key."""
    composite_keys = []
    cols = df.columns.tolist()
    # Limit to first 20 columns to avoid combinatorial explosion
    cols_to_check = cols[:20] 
    
    for combo in itertools.combinations(cols_to_check, 2):
        if df.duplicated(subset=list(combo)).sum() == 0:
            composite_keys.append(f"{combo[0]} + {combo[1]}")
            if len(composite_keys) >= 3: # Stop after finding 3
                break
    return composite_keys

def _analyze_distribution_shape(series: pd.Series) -> str:
    """Classifies the distribution shape of a numeric series."""
    if not SCIPY_AVAILABLE or len(series) < 20:
        return "Unknown"
    
    clean_series = series.dropna()
    if len(clean_series) < 20: return "Unknown"

    try:
        # Shapiro-Wilk test for normality (p > 0.05 means likely normal)
        # Note: Shapiro is sensitive to large N, so we sample
        sample = clean_series.sample(min(len(clean_series), 500))
        _, p_value = shapiro(sample)
        
        if p_value > 0.05:
            return "Normal (Gaussian)"
        
        # Check for Log-Normal
        if (clean_series > 0).all():
            _, p_log = shapiro(np.log(clean_series.sample(min(len(clean_series), 500))))
            if p_log > 0.05:
                return "Log-Normal"
        
        # Check Skewness
        s = skew(clean_series)
        if abs(s) > 1:
            return f"Skewed ({'Right' if s > 0 else 'Left'})"
            
        # Check Uniformity (simplified)
        # If variance is high and histogram is flat... (omitted for brevity, defaulting to Unknown/Other)
        
        return "Non-Normal"
    except:
        return "Unknown"

def _generate_sql_schema(df: pd.DataFrame, table_name: str = "dataset") -> str:
    """Generates a basic CREATE TABLE SQL statement."""
    type_map = {
        'int64': 'BIGINT', 'float64': 'FLOAT', 'object': 'TEXT', 
        'bool': 'BOOLEAN', 'datetime64[ns]': 'TIMESTAMP'
    }
    lines = [f"CREATE TABLE {table_name} ("]
    for col, dtype in df.dtypes.items():
        sql_type = type_map.get(str(dtype), 'TEXT')
        lines.append(f"    {col} {sql_type},")
    lines[-1] = lines[-1].rstrip(',') # Remove last comma
    lines.append(");")
    return "\n".join(lines)

def _check_partition_balance(ddf: dd.DataFrame) -> Dict[str, Any]:
    """Checks if Dask partitions are balanced."""
    try:
        partition_sizes = ddf.map_partitions(len).compute().tolist()
        if not partition_sizes: return {}
        
        avg_size = np.mean(partition_sizes)
        max_size = np.max(partition_sizes)
        min_size = np.min(partition_sizes)
        
        # Skew metric: (Max - Avg) / Avg
        skew = (max_size - avg_size) / avg_size if avg_size > 0 else 0
        
        return {
            "num_partitions": len(partition_sizes),
            "avg_rows_per_partition": int(avg_size),
            "skew": round(skew, 2),
            "is_skewed": skew > 0.5 # Threshold for warning
        }
    except:
        return {}

def _get_string_stats(ddf: dd.DataFrame, col: str) -> Dict[str, float]:
    """Calculates min/max/avg string length for a column using Dask."""
    try:
        lengths = ddf[col].astype(str).str.len()
        # Compute stats in one go
        min_l, max_l, mean_l = dd.compute(lengths.min(), lengths.max(), lengths.mean())
        return {"min_len": int(min_l), "max_len": int(max_l), "avg_len": round(float(mean_l), 1)}
    except:
        return {}

def analyze(ddf: dd.DataFrame, target_column: Optional[str] = None) -> Dict[str, Any]:
    """
    Performs comprehensive overview analysis including structural, quality, and semantic checks.
    """
    print("     -> Running Enhanced Overview Analysis (30+ Features)...")
    try:
        # --- Stage 1: The Essentials (Expanded) ---
        # Basic Stats
        num_rows = len(ddf)
        num_cols = len(ddf.columns)
        total_cells = num_rows * num_cols
        
        # Memory
        mem_usage_series = ddf.memory_usage(deep=True).compute()
        total_mem_bytes = mem_usage_series.sum()
        mem_usage_mb = round(total_mem_bytes / (1024 * 1024), 2)
        
        # Missing & Duplicates
        missing_count = ddf.isnull().sum().sum().compute()
        missing_pct = (missing_count / total_cells * 100) if total_cells > 0 else 0
        
        # Robust duplicate check (Dask - Out of Core)
        num_unique_rows = len(ddf.drop_duplicates())
        duplicate_rows = num_rows - num_unique_rows
        duplicate_pct = (duplicate_rows / num_rows * 100) if num_rows > 0 else 0

        # [NEW] Adaptive Sampling (Phase 4)
        SAMPLE_SIZE = 50000
        if num_rows > SAMPLE_SIZE:
            print(f"     ... Sampling {SAMPLE_SIZE} rows for deep profiling (PII, Semantics, etc.)")
            # map_partitions head is a simple way to get a distributed sample if partitions are shuffled
            # A better way for random sampling is sample(frac), but that requires knowing frac.
            # We'll stick to head() for deterministic speed, but we could do:
            # frac = SAMPLE_SIZE / num_rows
            # df_sample = ddf.sample(frac=frac).compute()
            # But sample() is expensive. Let's use head() but ensure we don't just get the first partition if possible.
            # For CSVs read in order, head() is just the top.
            # Let's try to get a bit from each partition if we have multiple.
            if ddf.npartitions > 1:
                # Take top N/npartitions from each partition
                rows_per_part = max(10, SAMPLE_SIZE // ddf.npartitions)
                df_sample = ddf.map_partitions(lambda x: x.head(rows_per_part)).compute()
            else:
                df_sample = ddf.head(SAMPLE_SIZE, compute=True)
        else:
            df_sample = ddf.compute()

        # [NEW] Duplicate Columns (on sample)
        dup_cols = []
        df_T = df_sample.T
        dup_cols_groups = df_T[df_T.duplicated()].index.tolist()
        if dup_cols_groups:
            dup_cols = dup_cols_groups

        # [NEW] Top Memory Hogs
        top_mem_cols = mem_usage_series.sort_values(ascending=False).head(5).index.tolist()
        
        # [NEW] Dataset Density
        density_score = 100 - missing_pct

        # [NEW] Partition Balance (Phase 4)
        partition_stats = _check_partition_balance(ddf)

        # --- Stage 2: The Enhancements ---
        variable_types = {}
        column_details = {}
        alerts = []
        
        if partition_stats.get("is_skewed"):
            alerts.append(f"Data is skewed across partitions (Skew: {partition_stats['skew']}). Performance may suffer.")

        # Pre-calculate nuniques for all columns (Exact - Dask)
        nuniques = ddf.nunique().compute()
        dtypes = df_sample.dtypes 
        
        for col in df_sample.columns:
            # Classification
            col_type = _classify_column(dtypes[col], nuniques[col], num_rows, col, df_sample[col].head(100))
            variable_types[col_type] = variable_types.get(col_type, 0) + 1
            
            # [NEW] Quasi-Constant Check
            if nuniques[col] > 1:
                most_freq_val_pct = df_sample[col].value_counts(normalize=True).iloc[0]
                if most_freq_val_pct > 0.99:
                    alerts.append(f"Column '{col}' is quasi-constant ({round(most_freq_val_pct*100, 1)}% same value).")
            elif nuniques[col] <= 1:
                 alerts.append(f"Column '{col}' is constant or empty.")

            # [NEW] Date Range & Gaps
            date_stats = {}
            if "Datetime" in col_type or pd.api.types.is_datetime64_any_dtype(dtypes[col]):
                min_date = df_sample[col].min()
                max_date = df_sample[col].max()
                date_stats = {"min": str(min_date), "max": str(max_date)}

            # [NEW] Mixed Type Forensics
            if col_type == "Text (High Cardinality)" or col_type == "Categorical":
                try:
                    numeric_conversion = pd.to_numeric(df_sample[col], errors='coerce')
                    if numeric_conversion.notna().sum() / len(df_sample) > 0.95 and numeric_conversion.notna().sum() < len(df_sample):
                         alerts.append(f"Column '{col}' looks numeric but has mixed types (possible corruption).")
                except:
                    pass

            # [NEW] Distribution Shape
            dist_shape = "N/A"
            if pd.api.types.is_numeric_dtype(dtypes[col]) and nuniques[col] > 20:
                dist_shape = _analyze_distribution_shape(df_sample[col])

            # [NEW] String Length Stats (Phase 4)
            string_stats = {}
            if "Text" in col_type or "Categorical" in col_type:
                # Only compute for object columns to save time
                if pd.api.types.is_string_dtype(dtypes[col]) or pd.api.types.is_object_dtype(dtypes[col]):
                     string_stats = _get_string_stats(ddf, col)
                     if string_stats.get("max_len", 0) > 1000:
                         alerts.append(f"Column '{col}' contains very long strings (Max: {string_stats['max_len']} chars).")

            column_details[col] = {
                'dtype': str(dtypes[col]),
                'decyphr_type': col_type,
                'nunique': int(nuniques[col]),
                'missing': int(df_sample[col].isnull().sum()),
                'memory_bytes': int(mem_usage_series.get(col, 0)),
                'date_stats': date_stats,
                'distribution_shape': dist_shape,
                'string_stats': string_stats
            }

        # [NEW] Health Score
        health_score = _calculate_health_score(missing_pct, duplicate_pct)
        
        # [NEW] PII Risk
        pii_keywords = ['name', 'email', 'phone', 'address', 'ssn', 'social', 'credit', 'card', 'ip']
        pii_risks = [col for col in df_sample.columns if any(k in col.lower() for k in pii_keywords)]
        if pii_risks:
            alerts.append(f"Potential PII detected in columns: {', '.join(pii_risks)}")

        # [NEW] Data Preview
        preview = {
            "head": df_sample.head(5).to_dict(orient='records'),
            "tail": df_sample.tail(5).to_dict(orient='records'),
            "random": df_sample.sample(min(5, len(df_sample))).to_dict(orient='records')
        }

        # [NEW] Optimization Tips
        optimization_tips = _get_memory_optimization_tips(df_sample)
        
        # --- Stage 3: The Game Changers ---
        
        # [NEW] Composite Keys
        composite_keys = _find_composite_keys(df_sample)
        
        # [NEW] SQL Schema
        sql_schema = _generate_sql_schema(df_sample)
        
        # [NEW] Dataset Fingerprint
        fingerprint_str = str(df_sample.head(100).values.tolist()) + str(df_sample.columns.tolist())
        dataset_fingerprint = hashlib.md5(fingerprint_str.encode()).hexdigest()

        results = {
            "dataset_stats": {
                "Number of Rows": num_rows,
                "Number of Columns": num_cols,
                "Total Cells": total_cells,
                "Memory Usage (MB)": mem_usage_mb,
                "Missing Cells": int(missing_count),
                "Missing Cells (%)": f"{missing_pct:.2f}%",
                "Duplicate Rows": int(duplicate_rows),
                "Duplicate Rows (%)": f"{duplicate_pct:.2f}%",
                "Dataset Density": f"{density_score:.2f}%",
                "Health Score": health_score,
                "Dataset Fingerprint": dataset_fingerprint,
                "Partitions": partition_stats.get("num_partitions", 1)
            },
            "structural_analysis": {
                "Duplicate Columns": dup_cols,
                "Top Memory Columns": top_mem_cols,
                "PII Risks": pii_risks,
                "Optimization Tips": optimization_tips,
                "Alerts": alerts,
                "Composite Keys": composite_keys,
                "SQL Schema": sql_schema,
                "Partition Stats": partition_stats
            },
            "variable_types": variable_types,
            "column_details": column_details,
            "data_preview": preview
        }
        
        print("     ... Overview analysis complete.")
        return results

    except Exception as e:
        error_message = f"Failed during overview analysis. Original error: {e}"
        print(f"     ... {error_message}")
        import traceback
        traceback.print_exc()
        return {"error": error_message}