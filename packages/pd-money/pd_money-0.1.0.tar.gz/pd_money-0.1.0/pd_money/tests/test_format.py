
import pandas as pd
import pd_money  # noqa: F401

def test_format_basic_us():
    s = pd.Series([1000.0, -500.5, 0.0, None])
    out = s.money.format()
    expected = pd.Series(["$1,000.00", "-$500.50", "$0.00", None]).astype("string")
    pd.testing.assert_series_equal(out, expected)

def test_format_accounting():
    s = pd.Series([1000.0, -500.5])
    out = s.money.format(accounting=True)
    expected = pd.Series(["$1,000.00", "($500.50)"]).astype("string")
    pd.testing.assert_series_equal(out, expected)

def test_format_eu_locale():
    s = pd.Series([1234.56, -0.1])
    out = s.money.format(locale="eu", symbol="€")
    expected = pd.Series(["€1.234,56", "-€0,10"]).astype("string")
    pd.testing.assert_series_equal(out, expected)
