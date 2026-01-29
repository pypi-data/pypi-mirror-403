import numpy as np
import pandas as pd

import pd_money  # noqa: F401


def test_clean_basic():
    s = pd.Series(["$1,000.00", "(500.00)", "-", " \u20ac50 "])
    out = s.money.clean()
    assert out.tolist() == [1000.0, -500.0, 0.0, 50.0]


def test_clean_percent():
    s = pd.Series(["10%", "5"])
    out = s.money.clean(percent=True)
    assert np.allclose(out.to_numpy(), np.array([0.10, 5.0]))


def test_clean_eu_locale():
    s = pd.Series(["1.234,56"])
    out = s.money.clean(locale="eu")
    assert out.iloc[0] == 1234.56
