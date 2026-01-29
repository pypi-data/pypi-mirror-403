"""Date and calendar utilities for financial data."""

from __future__ import annotations

import pandas as pd


def fiscal_year_series(
    series: pd.Series,
    start_month: int = 1,
) -> pd.Series:
    """Convert dates to Fiscal Year strings (e.g., 'FY2023 Q4').

    Assumes the Fiscal Year is named after the calendar year it ends in.
    Example: If start_month=10 (Oct), then Oct 2023 is FY2024.

    Args:
        series: Series of dates.
        start_month: Month the fiscal year starts (1-12).

    Returns:
        Series: Strings formatted as "FY{Year} Q{Quarter}".
    """
    if not 1 <= start_month <= 12:
        raise ValueError("start_month must be between 1 and 12")

    dates = pd.to_datetime(series, errors="coerce")
    
    # Calculate effective month relative to fiscal start
    # If start=10. Oct(10) -> Month 1.
    # (Month - Start) % 12 + 1
    # 10 - 10 = 0 -> 1
    # 11 - 10 = 1 -> 2
    # 1 - 10 = -9 % 12 = 3 -> 4
    effective_months = (dates.dt.month - start_month) % 12 + 1
    
    quarters = (effective_months - 1) // 3 + 1
    
    # Calculate Fiscal Year
    # If start_month == 1: FY = Calendar Year
    # If start_month > 1:
    #   If month >= start_month: FY = Year + 1
    #   Else: FY = Year
    
    years = dates.dt.year
    if start_month > 1:
        years = years + (dates.dt.month >= start_month).astype(int)
        
    # Format
    # Vectorized string formatting is tricky in pandas without apply, but we can try map
    # Or simple string concatenation
    
    # Using format with Apply is safer for NaNs
    def _fmt(y, q):
        if pd.isna(y) or pd.isna(q):
            return None
        return f"FY{int(y)} Q{int(q)}"
        
    df_temp = pd.DataFrame({"y": years, "q": quarters})
    return df_temp.apply(lambda row: _fmt(row["y"], row["q"]), axis=1).astype("string")
