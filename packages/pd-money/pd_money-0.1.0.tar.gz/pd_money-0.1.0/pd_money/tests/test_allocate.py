
import numpy as np
import pandas as pd
import pd_money  # noqa: F401

def test_allocate_equal_weights():
    s = pd.Series([100.00])
    # 100 / 3 = 33.333... -> 33.34, 33.33, 33.33
    weights = [1, 1, 1]
    df = s.money.allocate(weights)
    
    assert df.shape == (1, 3)
    row0 = df.iloc[0].values
    assert np.isclose(row0.sum(), 100.0)
    
    # Check that we have one 33.34 and two 33.33
    counts = {}
    for x in row0:
        val = round(x, 2)
        counts[val] = counts.get(val, 0) + 1
        
    assert counts[33.34] == 1
    assert counts[33.33] == 2

def test_allocate_proportional():
    s = pd.Series([10.00])
    weights = [7, 3] # 70%, 30% -> 7.00, 3.00
    df = s.money.allocate(weights)
    
    row0 = df.iloc[0].values
    assert np.isclose(row0[0], 7.0)
    assert np.isclose(row0[1], 3.0)

def test_allocate_rounding():
    # 10.00 allocated 1:1:1 -> 3.333... -> 3.34, 3.33, 3.33
    s = pd.Series([10.00])
    df = s.money.allocate([1, 1, 1])
    row0 = df.iloc[0].values
    assert np.isclose(row0.sum(), 10.0)
    # 3.34, 3.33, 3.33
    vals = sorted(np.round(row0, 2))
    assert vals == [3.33, 3.33, 3.34]
