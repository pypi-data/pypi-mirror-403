"""Cleaning utilities for financial data."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Optional

import pandas as pd

CURRENCY_SYMBOLS = "[\\$\\u20ac\\u00a3\\u00a5]"


def _validate_locale(locale: str) -> str:
    locale = locale.lower()
    if locale not in {"us", "eu"}:
        raise ValueError("locale must be 'us' or 'eu'")
    return locale


def _to_decimal(series: pd.Series, percent_mask: Optional[pd.Series]) -> pd.Series:
    def _convert(value: object) -> Optional[Decimal]:
        if value is None or value is pd.NA:
            return None
        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError):
            return None

    converted = series.map(_convert)
    if percent_mask is not None:
        converted = converted.where(~percent_mask, converted.map(lambda v: v / Decimal("100") if v is not None else None))
    return converted


def clean_series(
    series: pd.Series,
    percent: bool = False,
    as_decimal: bool = False,
    locale: str = "us",
    errors: str = "coerce",
) -> pd.Series:
    """Clean a financial series into numeric values.

    Args:
        series: Input Pandas Series.
        percent: Treat trailing % as percent values (divide by 100).
        as_decimal: Return Decimal values instead of float64.
        locale: "us" for comma thousands/dot decimals, "eu" for dot thousands/comma decimals.
        errors: Passed to pandas.to_numeric when as_decimal is False.
    """

    locale = _validate_locale(locale)

    s = series.astype("string")
    s = s.str.replace("\u00a0", "", regex=False)
    s = s.str.strip()
    s = s.str.replace(r"^[\u2013\u2014-]$", "0", regex=True)
    s = s.str.replace(r"^\((.*)\)$", r"-\1", regex=True)
    s = s.str.replace(CURRENCY_SYMBOLS, "", regex=True)
    s = s.str.replace(" ", "", regex=False)

    if locale == "eu":
        s = s.str.replace(".", "", regex=False)
        s = s.str.replace(",", ".", regex=False)
    else:
        s = s.str.replace(",", "", regex=False)

    percent_mask = None
    if percent:
        percent_mask = s.str.contains("%", regex=False, na=False)
        s = s.str.replace("%", "", regex=False)

    s = s.replace("", pd.NA)

    if as_decimal:
        return _to_decimal(s, percent_mask)

    cleaned = pd.to_numeric(s, errors=errors)
    if percent_mask is not None:
        cleaned = cleaned.astype(float)
        cleaned = cleaned.where(~percent_mask, cleaned / 100.0)
    return cleaned
