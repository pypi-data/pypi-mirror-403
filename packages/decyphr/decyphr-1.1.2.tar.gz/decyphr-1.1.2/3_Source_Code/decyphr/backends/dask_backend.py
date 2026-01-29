# ==============================================================================
# FILE: 3_Source_Code/decyphr/backends/dask_backend.py
# ==============================================================================
# PURPOSE: This module handles efficient, robust data loading using Dask.

import dask.dataframe as dd
import pandas as pd
from typing import Optional, Union

# Define a type hint for dataframes for clarity
DataFrameType = Union[dd.DataFrame, pd.DataFrame]

def load_dataframe_from_file(filepath: str) -> Optional[DataFrameType]:
    """
    Loads a dataset from a given file path into a Dask DataFrame.

    This function intelligently detects the file type (CSV or Excel) and uses the
    most efficient method to load it. It includes robust error handling for
    common Dask dtype inference issues.

    Args:
        filepath (str): The absolute or relative path to the data file.

    Returns:
        An optional Dask DataFrame. Returns the dataframe on successful loading,
        otherwise returns None if an error occurs.
    """
    print(f"Decyphr 🔮: Initializing data loading for '{filepath}'...")

    try:
        # --- CSV File Handling (Primary, High-Performance Path) ---
        if filepath.lower().endswith('.csv'):
            print("Decyphr 🔮: Detected CSV file. Loading with Dask backend...")
            
            # CORRECTED: Dask's type inference is generally good. Forcing object type
            # prevents numeric analysis in p01/p02. We rely on Dask's inference.
            # If specific issues arise, users should specify dtypes in loading config.
            ddf = dd.read_csv(filepath, blocksize=None)
            
            print("Decyphr 🔮: Successfully created Dask DataFrame.")
            return ddf

        # --- Excel File Handling ---
        elif filepath.lower().endswith(('.xlsx', '.xls')):
            print("Decyphr 🔮: Detected Excel file. Loading with pandas backend...")
            pdf = pd.read_excel(filepath)
            
            import multiprocessing
            n_partitions = multiprocessing.cpu_count()
            ddf = dd.from_pandas(pdf, npartitions=n_partitions)
            print(f"Decyphr 🔮: Successfully converted to Dask DataFrame with {n_partitions} partitions.")
            return ddf

        # --- Unsupported File Type ---
        else:
            print(f"Decyphr ❌: Error: Unsupported file type. Please provide a CSV or Excel file.")
            return None

    except FileNotFoundError:
        print(f"Decyphr ❌: Error: The file was not found at the specified path: {filepath}")
        return None
    except Exception as e:
        print(f"Decyphr ❌: An unexpected error occurred during file loading: {e}")
        return None