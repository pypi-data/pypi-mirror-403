"""XIRR calculation for financial data."""

from __future__ import annotations

import numpy as np
import pandas as pd
from datetime import date

def xirr_series(series: pd.Series, guess: float = 0.1) -> float | None:
    """Calculate the Internal Rate of Return for irregular cash flows (XIRR).
    
    The series index must be a DatetimeIndex representing dates.
    The series values represent cash flows (negative for outgoing, positive for incoming).
    
    Args:
        series: Cash flows with DatetimeIndex.
        guess: Initial guess for the rate (default 0.10).
        
    Returns:
        float: XIRR (e.g. 0.12 for 12%). Returns None if did not converge.
    """
    s = pd.to_numeric(series, errors="coerce").dropna()
    
    if not isinstance(s.index, pd.DatetimeIndex):
        raise ValueError("Series index must be a DatetimeIndex for XIRR")
        
    dates = s.index
    values = s.values
    
    if len(values) < 2:
        return None
        
    # Check if we have at least one positive and one negative
    if not (np.any(values > 0) and np.any(values < 0)):
        return None

    # Calculate fraction of years from start date
    start_date = dates[0]
    years = (dates - start_date).days / 365.0
    
    # Newton-Raphson method
    rate = guess
    limit = 100
    tol = 1e-6
    
    for _ in range(limit):
        # NPV = sum(C_i / (1+r)^t_i)
        # We need to solve NPV(r) = 0
        
        # Avoid division by zero or negative base for fractional power if rate <= -1
        if rate <= -1.0:
            rate = -0.99
            
        factor = (1.0 + rate) ** years
        npv = np.sum(values / factor)
        
        # Derivative of NPV w.r.t rate
        # d/dr [C * (1+r)^-t] = C * -t * (1+r)^(-t-1)
        # derivative = sum(values * -years * (1+rate)^(-years-1))
        
        derivative = np.sum(values * -years * ((1.0 + rate) ** (-years - 1.0)))
        
        if abs(derivative) < 1e-9:
             return None # Failed to converge (flat gradient)
             
        new_rate = rate - (npv / derivative)
        
        if abs(new_rate - rate) < tol:
            return new_rate
            
        rate = new_rate
        
    return None
