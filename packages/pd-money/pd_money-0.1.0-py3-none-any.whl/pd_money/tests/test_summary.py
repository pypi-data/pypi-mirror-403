
import numpy as np
import pandas as pd
import pd_money  # noqa: F401

def test_profile_basic():
    # 100, 200, -50, 0, NaN
    s = pd.Series([100, 200, -50, 0, np.nan])
    prof = s.money.profile()
    
    assert prof["count"] == 4
    assert prof["sum"] == 250
    assert prof["zeros"] == 1
    assert prof["negatives"] == 1
    assert prof["nulls"] == 1
    assert prof["min"] == -50
    assert prof["max"] == 200
    
    # CAGR requires DatetimeIndex or implicit numeric index?
    # cagr_series checks index. RangeIndex (0,1,2,3,4) is not Datetime.
    # So CAGR should be None/NaN if logic catches exception or returns nan.
    # The summary code catches ValueError/TypeError and sets to None.
    # cagr_series raises ValueError if no period provided and not datetime index.
    # So stats["cagr"] should be None.
    assert pd.isna(prof["cagr"])

    # Max Drawdown
    # Sequence: 100, 200 (Peak), -50 (Peak=200, dd=( -50/200 - 1 ) = -1.25), 0, nan
    # Min of drawdown is -1.25
    assert np.isclose(prof["max_drawdown"], -1.25)
    
def test_profile_with_dates():
    dates = pd.to_datetime(["2020-01-01", "2021-01-01"])
    s = pd.Series([100, 121], index=dates)
    prof = s.money.profile()
    
    # 1 year (leap year 2020). 100 -> 121 is 21%.
    assert np.isclose(prof["cagr"], 0.21, atol=0.01)
