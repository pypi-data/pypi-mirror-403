"""Growth metrics for financial data."""

from __future__ import annotations

import numpy as np
import pandas as pd


def cagr_series(
    series: pd.Series,
    period_years: float | None = None,
) -> float:
    """Calculate Compound Annual Growth Rate (CAGR).

    Formula: (End / Start) ^ (1 / n) - 1

    Args:
        series: Time-series data.
        period_years: Time period in years. If None, inferred from DatetimeIndex.

    Returns:
        float: The CAGR value.
    """
    s = pd.to_numeric(series, errors="coerce").dropna()
    
    if len(s) < 2:
        return np.nan
        
    start_val = s.iloc[0]
    end_val = s.iloc[-1]
    
    if period_years is None:
        if isinstance(series.index, pd.DatetimeIndex):
            start_date = s.index[0]
            end_date = s.index[-1]
            diff = end_date - start_date
            period_years = diff.days / 365.25
        else:
            raise ValueError("period_years is required if index is not DatetimeIndex")
            
    if period_years <= 0:
        return np.nan
        
    if start_val == 0:
        return np.inf if end_val > 0 else -np.inf if end_val < 0 else 0.0
    
    # Handle negative start value? CAGR is undefined/complex for negative start.
    # We'll return NaN or allow numpy to handle it (likely NaN for fractional power).
    if start_val < 0:
        return np.nan
        
    return (end_val / start_val) ** (1 / period_years) - 1.0
