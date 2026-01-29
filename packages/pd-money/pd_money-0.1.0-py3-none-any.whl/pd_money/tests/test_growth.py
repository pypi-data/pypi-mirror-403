
import numpy as np
import pandas as pd
import pd_money  # noqa: F401

def test_cagr_simple():
    s = pd.Series([100, 121])
    # 2 periods if we assume years? No, explicitly provide years.
    # 100 -> 121 is 21% growth.
    # If 2 years: (1.21)^(1/2) - 1 = 1.1 - 1 = 0.1
    cagr = s.money.cagr(period_years=2)
    assert np.isclose(cagr, 0.10)

def test_cagr_datetime():
    dates = pd.to_datetime(["2020-01-01", "2021-01-01", "2022-01-01"])
    s = pd.Series([100, 110, 121], index=dates)
    # Approx 2 years.
    # 2020 is leap (366). 2021 is 365. Total 731 days.
    # Years = 731 / 365.25 = 2.0013689
    # (121/100)^(1/2.0013689) - 1
    cagr = s.money.cagr()
    
    years = (dates[-1] - dates[0]).days / 365.25
    expected = (121/100) ** (1/years) - 1
    assert np.isclose(cagr, expected)

def test_cagr_negative_start():
    s = pd.Series([-100, 100])
    cagr = s.money.cagr(period_years=1)
    assert np.isnan(cagr)

def test_cagr_zero_period():
    s = pd.Series([100, 110])
    cagr = s.money.cagr(period_years=0)
    assert np.isnan(cagr)
