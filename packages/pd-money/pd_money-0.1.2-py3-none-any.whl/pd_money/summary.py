"""Summary profiling for financial data."""

from __future__ import annotations

import pandas as pd
from pd_money.growth import cagr_series
from pd_money.performance import drawdown_series


def profile_series(series: pd.Series) -> pd.Series:
    """Generate a financial summary profile of the Series.

    Includes:
    - Count, Nulls
    - Min, Max, Sum, Mean
    - Zeros (count)
    - Negatives (count)
    - CAGR (if applicable)
    - Max Drawdown

    Returns:
        Series: Summary statistics.
    """
    s = pd.to_numeric(series, errors="coerce")
    
    desc = s.describe()
    
    stats = {
        "count": desc["count"],
        "mean": desc["mean"],
        "sum": s.sum(),
        "min": desc["min"],
        "max": desc["max"],
        "zeros": (s == 0).sum(),
        "negatives": (s < 0).sum(),
        "nulls": s.isna().sum(),
    }
    
    # CAGR
    try:
        cagr_val = cagr_series(series)
        stats["cagr"] = cagr_val
    except (ValueError, TypeError):
        stats["cagr"] = None

    # Max Drawdown
    dd = drawdown_series(series)
    stats["max_drawdown"] = dd.min()
    
    return pd.Series(stats)
