import numpy as np
import pandas as pd

import pd_money  # noqa: F401


def test_from_unit_millions():
    s = pd.Series([1.5])
    out = s.money.from_unit("m")
    assert out.iloc[0] == 1_500_000.0


def test_to_unit_millions():
    s = pd.Series([1_500_000])
    out = s.money.to_unit("m", decimals=1)
    assert out.iloc[0] == "1.5M"


def test_convert_static_rate():
    s = pd.Series([10.0, 20.0])
    out = s.money.convert(to="USD", rates=1.1)
    assert np.allclose(out.to_numpy(), np.array([11.0, 22.0]))


def test_convert_with_dates():
    s = pd.Series([10.0, 20.0])
    dates = pd.Series(["2023-01-01", "2023-01-02"])
    rates = {"2023-01-01": 1.1, "2023-01-02": 1.2}
    out = s.money.convert(to="USD", rates=rates, dates=dates)
    assert np.allclose(out.to_numpy(), np.array([11.0, 24.0]))


def test_lint_report_flags():
    s = pd.Series(["$1.00", "\u20ac2.00", "#DIV/0!"])
    report = s.money.lint()
    assert any("Excel error" in line for line in report)
    assert any("Mixed currency" in line for line in report)
