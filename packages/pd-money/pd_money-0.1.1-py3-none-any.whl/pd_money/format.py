"""Formatting utilities for financial data."""

from __future__ import annotations

import pandas as pd


def format_series(
    series: pd.Series,
    symbol: str = "$",
    digits: int = 2,
    accounting: bool = False,
    locale: str = "us",
) -> pd.Series:
    """Format a numeric series into financial strings.

    Args:
        series: Input numeric Series.
        symbol: Currency symbol (default '$').
        digits: Number of decimal places.
        accounting: If True, use (100.00) for negative numbers.
        locale: "us" (1,000.00) or "eu" (1.000,00).
    """
    if locale not in ("us", "eu"):
        raise ValueError("locale must be 'us' or 'eu'")

    def _fmt(val: object) -> str | None:
        if pd.isna(val):
            return None
        
        try:
            fval = float(val) # type: ignore
        except (ValueError, TypeError):
            return str(val)

        is_neg = fval < 0
        abs_val = abs(fval)

        # Standard US formatting first: 1,234.56
        s = f"{abs_val:,.{digits}f}"

        if locale == "eu":
            # Swap , and .
            s = s.translate(str.maketrans(",.", ".,"))

        if is_neg:
            if accounting:
                return f"({symbol}{s})"
            else:
                return f"-{symbol}{s}"
        else:
            return f"{symbol}{s}"

    return series.apply(_fmt).astype("string")
