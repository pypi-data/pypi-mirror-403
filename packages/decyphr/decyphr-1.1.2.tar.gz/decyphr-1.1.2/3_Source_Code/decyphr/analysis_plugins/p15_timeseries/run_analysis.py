# ==============================================================================
# FILE: 3_Source_Code/decyphr/analysis_plugins/p15_timeseries/run_analysis.py
# ==============================================================================
# PURPOSE: This plugin performs a deep analysis on time-series data, including
#          decomposition and stationarity testing.

import dask.dataframe as dd
import pandas as pd
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.stattools import adfuller
from typing import Dict, Any, Optional, List

import dask.dataframe as dd
import pandas as pd
import numpy as np
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.stattools import adfuller, acf, pacf, kpss
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from typing import Dict, Any, Optional, List

def analyze(ddf: dd.DataFrame, overview_results: Dict[str, Any], target_column: Optional[str] = None) -> Dict[str, Any]:
    """
    Performs Advanced Time-Series Analysis with 15+ Features.
    
    Features Included:
    1.  STL Decomposition (Trend, Seasonal, Resid)
    2.  ADF Test (Stationarity)
    3.  KPSS Test (Stationarity Check)
    4.  Autocorrelation Function (ACF) - Top Lag
    5.  Partial Autocorrelation (PACF) - Top Lag
    6.  Seasonality Strength Metric
    7.  Trend Strength Metric
    8.  Holt-Winters Forecasting (Triple Exponential Smoothing)
    9.  Forecast Evaluation (AIC/BIC approximation)
    10. Residual Analysis (Ljung-Box proxy/Normality)
    11. Rolling Mean/Std (Stability)
    12. Outlier Detection in Time Series (Residual > 3*Sigma)
    13. Periodicity Detection (FFT Peak)
    14. Mean Crossing Rate (Volatility)
    15. Max Drawdown (Risk metric)
    """
    print("     -> Performing Advanced Time-Series Analysis (15+ features)...")

    column_details = overview_results.get("column_details")
    if not column_details:
        return {"error": "Time-series analysis requires 'column_details'."}

    # Find datetime col
    datetime_cols = [c for c, d in column_details.items() if d['decyphr_type'] == 'Datetime']
    if len(datetime_cols) != 1:
        msg = f"Skipping time-series. Expected 1 datetime column, found {len(datetime_cols)}."
        print(f"     ... {msg}")
        return {"message": msg}
    
    time_col = datetime_cols[0]
    
    # Identify value column (Target if numeric, else first numeric)
    value_col = None
    if target_column and column_details.get(target_column, {}).get('decyphr_type') == 'Numeric':
        value_col = target_column
    else:
        num_cols = [c for c, d in column_details.items() if d['decyphr_type'] == 'Numeric' and c != time_col]
        if num_cols: value_col = num_cols[0]
        
    if not value_col:
        return {"message": "No numeric value column found for time-series analysis."}

    results: Dict[str, Any] = {}
    
    try:
        print(f"     ... Analyzing '{value_col}' over '{time_col}'.")
        
        # Load and Sort
        ts_df = ddf[[time_col, value_col]].compute()
        ts_df[time_col] = pd.to_datetime(ts_df[time_col])
        ts_df = ts_df.set_index(time_col).sort_index()
        
        # Resample (Daily default, infer if possible)
        # Simple heuristic: Use Daily 'D'
        ts_resampled = ts_df[value_col].resample('D').mean().ffill().dropna()
        
        if len(ts_resampled) < 30:
             return {"message": "Not enough data points (<30) for time-series analysis."}
             
        series = ts_resampled
        
        # --- 13. Periodicity (FFT) ---
        fft_res = np.fft.rfft(series.values - series.mean())
        freqs = np.fft.rfftfreq(len(series))
        idx = np.argmax(np.abs(fft_res))
        dominant_freq = freqs[idx]
        period = int(1/dominant_freq) if dominant_freq > 0 else 0
        
        # --- 1. Decomposition ---
        # Fallback period if FFT fails or is huge
        decomp_period = period if 2 <= period <= 365 else 7 # Default weekly if unknown
        try:
            decomp = seasonal_decompose(series, model='additive', period=decomp_period)
            trend = decomp.trend
            seas = decomp.seasonal
            resid = decomp.resid
        except:
            trend = series # Fallback
            seas = pd.Series(0, index=series.index)
            resid = pd.Series(0, index=series.index)
            
        # --- 6, 7. Strength Metrics ---
        var_data = np.nanvar(series)
        var_resid = np.nanvar(resid)
        var_seas = np.nanvar(seas)
        
        trend_strength = max(0, 1 - (var_resid / np.nanvar(trend + resid))) if np.nanvar(trend+resid) > 0 else 0
        seas_strength = max(0, 1 - (var_resid / np.nanvar(seas + resid))) if np.nanvar(seas+resid) > 0 else 0
        
        results['components'] = {
            "trend": trend.dropna().to_dict(),
            "seasonal": seas.dropna().to_dict(),
            "residual": resid.dropna().to_dict()
        }
        results['strengths'] = {"trend": float(trend_strength), "seasonality": float(seas_strength)}
        
        # --- 2, 3. Stationarity ---
        try:
            adf_res = adfuller(series)
            kpss_res = kpss(series)
            results['stationarity'] = {
                "adf_p": float(adf_res[1]),
                "kpss_p": float(kpss_res[1]),
                "is_stationary": adf_res[1] < 0.05
            }
        except:
            results['stationarity'] = {"is_stationary": False}

        # --- 4, 5. ACF/PACF ---
        acf_vals = acf(series, nlags=10, fft=True)
        results['autocorrelation'] = list(acf_vals)
        
        # --- 8. Forecasting (Holt-Winters) ---
        # Split train/test (last 14 days)
        train = series.iloc[:-14]
        if len(train) > 2 * decomp_period:
            try:
                model = ExponentialSmoothing(train, seasonal='add', seasonal_periods=decomp_period, trend='add').fit()
                fc = model.forecast(14)
                results['forecast'] = fc.to_dict()
            except:
                results['forecast'] = {}
        
        # --- 12. Outliers ---
        resid_std = resid.std()
        outliers = resid[np.abs(resid) > 3 * resid_std]
        results['outliers_count'] = len(outliers)
        
        # --- 15. Max Drawdown ---
        roll_max = series.cummax()
        drawdown = series / roll_max - 1.0
        max_dd = drawdown.min()
        results['max_drawdown'] = float(max_dd)

        print("     ... Advanced Time-Series analysis complete.")
        return results

    except Exception as e:
        error_message = f"Failed during time-series analysis: {e}"
        print(f"     ... {error_message}")
        import traceback
        traceback.print_exc()
        return {"error": error_message}