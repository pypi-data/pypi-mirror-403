"""FX conversion utilities."""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd


def _coerce_rate_series(
    rates: object,
    date_col: Optional[str] = None,
    rate_col: Optional[str] = None,
) -> pd.Series:
    if isinstance(rates, pd.Series):
        return rates
    if isinstance(rates, dict):
        return pd.Series(rates)
    if isinstance(rates, pd.DataFrame):
        columns = list(rates.columns)
        if date_col is None or rate_col is None:
            if "date" in columns and "rate" in columns:
                date_col = "date"
                rate_col = "rate"
            elif len(columns) >= 2:
                date_col = columns[0]
                rate_col = columns[1]
            else:
                raise ValueError("rates DataFrame must have at least two columns")
        return pd.Series(rates[rate_col].to_numpy(), index=rates[date_col])
    raise TypeError("rates must be a number, dict, Series, or DataFrame")


def _normalize_dates(
    dates: pd.Series,
    rates_index: pd.Index,
) -> tuple[pd.Series, pd.Index]:
    if pd.api.types.is_datetime64_any_dtype(dates) and not isinstance(rates_index, pd.DatetimeIndex):
        try:
            rates_index = pd.to_datetime(rates_index)
        except (ValueError, TypeError):
            pass

    if isinstance(rates_index, pd.DatetimeIndex):
        rates_index = rates_index.normalize()
        if pd.api.types.is_datetime64_any_dtype(dates):
            dates_key = dates.dt.normalize()
        else:
            try:
                dates_key = pd.to_datetime(dates).dt.normalize()
            except (ValueError, TypeError):
                rates_index = rates_index.astype(str)
                dates_key = dates.astype(str)
    else:
        rates_index = rates_index.astype(str)
        dates_key = dates.astype(str)

    return dates_key, rates_index


def convert_series(
    series: pd.Series,
    to: str,
    rates: object,
    dates: Optional[pd.Series] = None,
    date_col: Optional[object] = None,
    rate_col: Optional[str] = None,
) -> pd.Series:
    """Convert a Series of amounts using FX rates.

    Args:
        series: Input amounts.
        to: Target currency code (informational).
        rates: Scalar rate or mapping (dict/Series/DataFrame).
        dates: Series of dates for time-based mapping.
        date_col: Alias for dates; must be a Series/array when using the Series accessor.
        rate_col: Column name for rates when rates is a DataFrame.
    """

    if dates is None and date_col is not None:
        if isinstance(date_col, (pd.Series, np.ndarray, list)):
            dates = pd.Series(date_col, index=series.index)
        else:
            raise ValueError("date_col must be a Series/array when using a Series accessor")

    if dates is None:
        if isinstance(rates, (int, float, np.number)):
            return series.astype(float) * float(rates)
        raise ValueError("When rates is a mapping you must pass dates or date_col as a Series")

    rate_series = _coerce_rate_series(rates, rate_col=rate_col)
    dates_series = pd.Series(dates, index=series.index)
    dates_key, rates_index = _normalize_dates(dates_series, rate_series.index)
    rate_series = rate_series.copy()
    rate_series.index = rates_index

    mapped = dates_key.map(rate_series)
    return series.astype(float) * mapped
