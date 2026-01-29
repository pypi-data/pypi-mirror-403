
import numpy as np
import pandas as pd
import pd_money  # noqa: F401

def test_npv_basic():
    # Invest 100 today, get 110 in 1 year.
    # If discount rate is 10%, NPV should be 0.
    dates = pd.to_datetime(["2020-01-01", "2021-01-01"])
    s = pd.Series([-100.0, 110.0], index=dates)
    
    # Note: 2020 is leap (366 days). 366/365 = 1.0027 years.
    # So it won't be exactly 0 with a 10% rate if we use 365-day denominator.
    # But it should be very close.
    npv = s.money.npv(rate=0.10)
    assert abs(npv) < 1.0 

def test_npv_zero_rate():
    # At 0% rate, NPV is just the sum of cash flows.
    dates = pd.to_datetime(["2020-01-01", "2021-01-01", "2022-01-01"])
    s = pd.Series([-100.0, 50.0, 60.0], index=dates)
    npv = s.money.npv(rate=0.0)
    assert np.isclose(npv, 10.0)

def test_npv_known_value():
    # 100 today + 100 in 1 year at 5%
    # 100 + 100/1.05 = 100 + 95.238 = 195.238
    dates = pd.to_datetime(["2020-01-01", "2021-01-01"])
    s = pd.Series([100.0, 100.0], index=dates)
    npv = s.money.npv(rate=0.05)
    
    # Adjust for leap year (366 days)
    years = 366/365.0
    expected = 100.0 + 100.0 / (1.05 ** years)
    assert np.isclose(npv, expected)
