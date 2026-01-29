"""Performance metrics for financial data."""

from __future__ import annotations

import pandas as pd


def drawdown_series(series: pd.Series) -> pd.Series:
    """Calculate the drawdown from the running maximum.
    
    Formula: (Price / RunningMax) - 1
    
    Args:
        series: Time-series of prices or values.
        
    Returns:
        Series: Drawdown values (0.0 to -1.0 usually).
    """
    s = pd.to_numeric(series, errors="coerce")
    running_max = s.cummax()
    drawdown = (s / running_max) - 1
    return drawdown


def volatility_series(series: pd.Series, periods: int | None = None) -> float:
    """Calculate annualized volatility.
    
    Args:
        series: Time-series of values.
        periods: Number of periods per year. If None, inferred from index.
            (Daily=252, Monthly=12, Quarterly=4, Weekly=52).
            
    Returns:
        float: Annualized volatility (std dev * sqrt(periods)).
    """
    import numpy as np
    
    s = pd.to_numeric(series, errors="coerce")
    
    # Calculate returns (percentage change)
    returns = s.pct_change().dropna()
    
    if periods is None:
        if isinstance(s.index, pd.DatetimeIndex):
            # Infer frequency
            inferred_freq = pd.infer_freq(s.index)
            if inferred_freq:
                if "D" in inferred_freq or "B" in inferred_freq:
                    periods = 252
                elif "W" in inferred_freq:
                    periods = 52
                elif "M" in inferred_freq:
                    periods = 12
                elif "Q" in inferred_freq:
                    periods = 4
                elif "Y" in inferred_freq:
                    periods = 1
                else:
                    # Fallback for daily if high frequency or unknown
                    periods = 252
            else:
                 # Check average delta days
                 delta = (s.index[-1] - s.index[0]).days / len(s)
                 if delta < 1.5: # ~ Daily
                     periods = 252
                 elif delta < 8: # ~ Weekly
                     periods = 52
                 elif delta < 32: # ~ Monthly
                     periods = 12
                 else:
                     periods = 1 # Assume annual
        else:
             periods = 252 # Default to daily trading days
             
    vol = returns.std() * np.sqrt(periods)
    return vol


def beta_series(series: pd.Series, benchmark: pd.Series) -> float | None:
    """Calculate Beta relative to a benchmark.
    
    Beta = Cov(Asset_Returns, Benchmark_Returns) / Var(Benchmark_Returns)
    
    Args:
        series: Asset prices/values.
        benchmark: Benchmark prices/values (e.g. S&P 500).
        
    Returns:
        float: Beta value. Returns None if alignment fails or insufficient data.
    """
    s = pd.to_numeric(series, errors="coerce")
    b = pd.to_numeric(benchmark, errors="coerce")
    
    # Calculate returns
    s_ret = s.pct_change().dropna()
    b_ret = b.pct_change().dropna()
    
    # Align data (inner join on index)
    # We use a DataFrame to ensure alignment
    df = pd.concat([s_ret, b_ret], axis=1, join="inner")
    
    if len(df) < 2:
        return None
        
    s_aligned = df.iloc[:, 0]
    b_aligned = df.iloc[:, 1]
    
    # Covariance
    cov = s_aligned.cov(b_aligned)
    
    # Variance of benchmark
    var = b_aligned.var()
    
    if var == 0:
        return None
        
    return cov / var
