
import numpy as np
import pandas as pd
import pd_money  # noqa: F401

def test_drawdown_basic():
    # 100 -> 120 (Peak) -> 60 (-50%) -> 120 (0%) -> 150 (Peak)
    s = pd.Series([100, 120, 60, 120, 150])
    dd = s.money.drawdown()
    
    expected = pd.Series([0.0, 0.0, -0.5, 0.0, 0.0])
    pd.testing.assert_series_equal(dd, expected)

def test_drawdown_all_down():
    s = pd.Series([100, 90, 80])
    dd = s.money.drawdown()
    # 100 (Peak=100) -> 0
    # 90 (Peak=100) -> -0.1
    # 80 (Peak=100) -> -0.2
    expected = pd.Series([0.0, -0.1, -0.2])
    pd.testing.assert_series_equal(dd, expected)

def test_volatility_daily():
    # 2 days of returns: 1% and -1%.
    # dates: day1, day2, day3.
    # Prices: 100, 101, 99.99
    dates = pd.to_datetime(["2020-01-01", "2020-01-02", "2020-01-03"])
    s = pd.Series([100.0, 101.0, 99.99], index=dates)
    
    # Returns: 
    # 101/100 - 1 = 0.01
    # 99.99/101 - 1 = -0.01
    # Std dev of [0.01, -0.01] is approx 0.01414
    # Annualized = 0.01414 * sqrt(252) ~= 0.224
    
    vol = s.money.volatility()
    assert vol > 0.2
    assert vol < 0.25

def test_volatility_manual():
    # Simple case: constant returns should have 0 volatility
    s = pd.Series([100, 110, 121]) # 10% returns exactly
    vol = s.money.volatility(periods=1)
    assert np.isclose(vol, 0.0)

def test_beta_perfect_correlation():
    # Asset moves exactly 2x the benchmark
    # Bench: 100, 101, 102 (+1%, +0.99%)
    # Asset: 100, 102, 104 (+2%, +1.96% approx)
    # Actually let's use exact returns to be sure
    dates = pd.to_datetime(["2020-01-01", "2020-01-02", "2020-01-03"])
    bench = pd.Series([100.0, 101.0, 102.0], index=dates)
    
    # Asset returns = 2 * Benchmark returns
    # r_b1 = 0.01. r_a1 = 0.02 -> Price 102.
    # r_b2 = (102/101 - 1) = 0.0099. r_a2 = 2 * 0.0099 = 0.0198.
    # Price 3 = 102 * (1+0.0198) = 104.0196
    
    asset_vals = [100.0, 102.0]
    r_b2 = 102.0/101.0 - 1
    asset_vals.append(asset_vals[-1] * (1 + 2*r_b2))
    asset = pd.Series(asset_vals, index=dates)
    
    beta = asset.money.beta(benchmark=bench)
    assert np.isclose(beta, 2.0)

def test_beta_uncorrelated():
    # Asset flat, Benchmark moves
    dates = pd.to_datetime(["2020-01-01", "2020-01-02", "2020-01-03"])
    bench = pd.Series([100.0, 110.0, 100.0], index=dates)
    asset = pd.Series([100.0, 100.0, 100.0], index=dates)
    
    beta = asset.money.beta(benchmark=bench)
    # Covariance should be 0
    assert np.isclose(beta, 0.0)
