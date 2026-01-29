
import numpy as np
import pandas as pd
import pd_money  # noqa: F401

def test_xirr_simple():
    # Simple case: Invest 100, get 110 after 1 year. Return should be 10%.
    dates = pd.to_datetime(["2020-01-01", "2021-01-01"])
    s = pd.Series([-100.0, 110.0], index=dates)
    
    # 2020 was leap year (366 days).
    # XIRR uses 365.0 as denominator usually, or Actual/365.
    # Our impl uses (date - start).days / 365.0
    # days = 366. years = 366/365 = 1.0027...
    # 100 = 110 / (1+r)^1.0027
    # (1+r)^1.0027 = 1.1
    # 1+r = 1.1^(1/1.0027) = 1.1^0.997...
    # r approx 0.099...
    
    xirr = s.money.xirr()
    assert np.isclose(xirr, 0.10, atol=0.01)

def test_xirr_irregular():
    # Invest 1000 on Jan 1.
    # Invest 1000 on July 1.
    # Withdraw 2100 on Jan 1 next year.
    dates = pd.to_datetime(["2022-01-01", "2022-07-01", "2023-01-01"])
    s = pd.Series([-1000.0, -1000.0, 2100.0], index=dates)
    
    xirr = s.money.xirr()
    # Approx 6-7%?
    assert xirr > 0.05
    assert xirr < 0.15

def test_xirr_no_convergence():
    # Impossible case? Or just zero?
    # Invest 100, get 0.
    dates = pd.to_datetime(["2020-01-01", "2021-01-01"])
    s = pd.Series([-100.0, 0.0], index=dates)
    # Rate should be -1.0 (-100%).
    xirr = s.money.xirr()
    if xirr is not None:
         assert np.isclose(xirr, -1.0, atol=0.01)
