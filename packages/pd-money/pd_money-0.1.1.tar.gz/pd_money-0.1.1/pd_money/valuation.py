"""Valuation utilities for financial data."""

from __future__ import annotations

import numpy as np
import pandas as pd


def npv_series(series: pd.Series, rate: float) -> float:
    """Calculate the Net Present Value (NPV) for irregular cash flows.
    
    Formula: sum(CF_i / (1 + rate)^t_i)
    where t_i is the time in years from the first cash flow.
    
    Args:
        series: Cash flows with DatetimeIndex.
        rate: Annual discount rate (e.g. 0.08 for 8%).
        
    Returns:
        float: The Net Present Value.
    """
    s = pd.to_numeric(series, errors="coerce").dropna()
    
    if not isinstance(s.index, pd.DatetimeIndex):
        raise ValueError("Series index must be a DatetimeIndex for NPV")
        
    if len(s) == 0:
        return 0.0
        
    dates = s.index
    values = s.values
    
    # Calculate fraction of years from the first date
    start_date = dates[0]
    years = (dates - start_date).days / 365.0
    
    # Discount values: NPV = sum( CF / (1+r)^t )
    factors = (1.0 + rate) ** years
    npv = np.sum(values / factors)
    
    return float(npv)
