"""Pandas Series accessor for financial data utilities."""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd

from pd_money.allocate import allocate_series
from pd_money.clean import CURRENCY_SYMBOLS, clean_series
from pd_money.convert import convert_series
from pd_money.format import format_series
from pd_money.dates import fiscal_year_series
from pd_money.growth import cagr_series
from pd_money.performance import beta_series, drawdown_series, volatility_series
from pd_money.summary import profile_series
from pd_money.valuation import npv_series
from pd_money.xirr import xirr_series

UNIT_FACTORS = {
    "k": 1_000.0,
    "m": 1_000_000.0,
    "mm": 1_000_000.0,
    "b": 1_000_000_000.0,
}

UNIT_SYMBOLS = {
    "k": "K",
    "m": "M",
    "mm": "M",
    "b": "B",
}


def _unit_factor(unit: str) -> float:
    if unit is None:
        raise ValueError("unit is required")
    key = unit.lower()
    if key not in UNIT_FACTORS:
        raise ValueError("unit must be one of: k, m, mm, b")
    return UNIT_FACTORS[key]


def _unit_symbol(unit: str) -> str:
    key = unit.lower()
    return UNIT_SYMBOLS[key]


def lint_series(series: pd.Series, decimals: int = 2) -> list[str]:
    report: list[str] = []
    s = series
    s_str = s.astype("string")

    nulls = int(s.isna().sum())
    if nulls == 0:
        report.append("[PASS] No nulls found.")
    else:
        report.append(f"[WARN] {nulls} nulls found.")

    error_mask = s_str.str.contains(r"#DIV/0!|#REF!|#N/A", regex=True, na=False)
    error_count = int(error_mask.sum())
    if error_count:
        report.append(f"[FAIL] {error_count} rows contain Excel error strings.")
    else:
        report.append("[PASS] No Excel error strings found.")

    symbols = s_str.str.findall(CURRENCY_SYMBOLS)
    unique_symbols: set[str] = set()
    for items in symbols.dropna():
        for symbol in items:
            unique_symbols.add(symbol)

    if len(unique_symbols) > 1:
        report.append(
            "[WARN] Mixed currency symbols detected: "
            + ", ".join(sorted(unique_symbols))
        )
    else:
        report.append("[PASS] No mixed currency symbols detected.")

    s_num = pd.to_numeric(s, errors="coerce")
    scale = 10 ** decimals
    scaled = s_num * scale
    precision_mask = s_num.notna() & ~np.isclose(
        scaled, np.round(scaled), atol=1e-9
    )
    precision_count = int(precision_mask.sum())
    if precision_count:
        report.append(
            f"[WARN] {precision_count} rows exceed {decimals} decimal places."
        )
    else:
        report.append(f"[PASS] No precision issues beyond {decimals} decimals.")

    return report


@pd.api.extensions.register_series_accessor("money")
class MoneyAccessor:
    """Series accessor for cleaning and transforming financial data."""

    def __init__(self, pandas_obj: pd.Series) -> None:
        self._obj = pandas_obj

    def clean(
        self,
        percent: bool = False,
        as_decimal: bool = False,
        locale: str = "us",
        errors: str = "coerce",
    ) -> pd.Series:
        return clean_series(
            self._obj,
            percent=percent,
            as_decimal=as_decimal,
            locale=locale,
            errors=errors,
        )

    def from_unit(self, unit: str) -> pd.Series:
        factor = _unit_factor(unit)
        values = pd.to_numeric(self._obj, errors="coerce")
        return values * factor

    def to_unit(
        self,
        unit: str,
        decimals: int = 1,
        suffix: bool = True,
    ) -> pd.Series:
        factor = _unit_factor(unit)
        values = pd.to_numeric(self._obj, errors="coerce")
        scaled = (values / factor).round(decimals)

        if not suffix:
            return scaled

        symbol = _unit_symbol(unit)

        def _format(value: float) -> Optional[str]:
            if pd.isna(value):
                return None
            return f"{value:.{decimals}f}{symbol}"

        return scaled.map(_format)

    def to_units(
        self,
        unit: str,
        decimals: int = 1,
        suffix: bool = True,
    ) -> pd.Series:
        return self.to_unit(unit, decimals=decimals, suffix=suffix)

    def convert(
        self,
        to: str,
        rates: object,
        dates: Optional[pd.Series] = None,
        date_col: Optional[object] = None,
        rate_col: Optional[str] = None,
    ) -> pd.Series:
        """Convert amounts using FX rates.

        Args:
            to: Target currency code.
            rates: Exchange rates (dict, Series, or DataFrame).
            dates: Series of dates matching the rows (required for time-series rates).
            date_col: Alias for dates. Must be a Series (e.g. df['Date']), not a string name.
            rate_col: Column name to use if rates is a DataFrame.
        """
        return convert_series(
            self._obj,
            to=to,
            rates=rates,
            dates=dates,
            date_col=date_col,
            rate_col=rate_col,
        )

    def lint(self, decimals: int = 2) -> list[str]:
        return lint_series(self._obj, decimals=decimals)

    def format(
        self,
        symbol: str = "$",
        digits: int = 2,
        accounting: bool = False,
        locale: str = "us",
    ) -> pd.Series:
        """Format a numeric series into financial strings.

        Args:
            symbol: Currency symbol (default '$').
            digits: Number of decimal places.
            accounting: If True, use (100.00) for negative numbers.
            locale: "us" (1,000.00) or "eu" (1.000,00).
        """
        return format_series(
            self._obj,
            symbol=symbol,
            digits=digits,
            accounting=accounting,
            locale=locale,
        )

    def allocate(
        self,
        weights: list[float] | np.ndarray,
        decimals: int = 2,
    ) -> pd.DataFrame:
        """Split amounts into components based on weights (penny-perfect)."""
        return allocate_series(self._obj, weights=weights, decimals=decimals)

    def cagr(self, period_years: Optional[float] = None) -> float:
        """Calculate Compound Annual Growth Rate."""
        return cagr_series(self._obj, period_years=period_years)

    def drawdown(self) -> pd.Series:
        """Calculate the drawdown series from the running maximum."""
        return drawdown_series(self._obj)

    def volatility(self, periods: Optional[int] = None) -> float:
        """Calculate annualized volatility."""
        return volatility_series(self._obj, periods=periods)

    def beta(self, benchmark: pd.Series) -> Optional[float]:
        """Calculate Beta relative to a benchmark."""
        return beta_series(self._obj, benchmark=benchmark)

    def fiscal_year(self, start_month: int = 1) -> pd.Series:
        """Convert dates to Fiscal Year strings (e.g. FY2023 Q4)."""
        return fiscal_year_series(self._obj, start_month=start_month)

    def profile(self) -> pd.Series:
        """Generate a financial summary profile."""
        return profile_series(self._obj)

    def npv(self, rate: float) -> float:
        """Calculate Net Present Value (NPV) for cash flows."""
        return npv_series(self._obj, rate=rate)

    def xirr(self, guess: float = 0.1) -> Optional[float]:
        """Calculate Internal Rate of Return (XIRR) for cash flows."""
        return xirr_series(self._obj, guess=guess)
