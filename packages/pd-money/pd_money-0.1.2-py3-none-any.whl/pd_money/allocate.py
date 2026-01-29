"""Allocation utilities for splitting amounts."""

from __future__ import annotations

import numpy as np
import pandas as pd


def allocate_series(
    series: pd.Series,
    weights: list[float] | np.ndarray,
    decimals: int = 2,
) -> pd.DataFrame:
    """Split a Series of amounts into components based on weights.

    Ensures the sum of components equals the original amount exactly,
    distributing rounding errors (pennies) to the largest fractional parts.

    Args:
        series: Series of amounts to split.
        weights: List of weights (e.g. [0.3, 0.7]).
        decimals: Precision to round components to.

    Returns:
        DataFrame with one column per weight.
    """
    values = pd.to_numeric(series, errors="coerce").fillna(0.0).to_numpy()
    weights_arr = np.array(weights, dtype=float)
    
    if weights_arr.sum() == 0:
        raise ValueError("Weights cannot sum to zero")
        
    weights_norm = weights_arr / weights_arr.sum()
    
    # Shapes:
    # values: (n_rows, 1)
    # weights_norm: (1, n_cols)
    values_2d = values[:, np.newaxis]
    weights_row = weights_norm[np.newaxis, :]
    
    # Ideal splits
    raw_splits = values_2d * weights_row
    
    factor = 10.0 ** decimals
    penny = 1.0 / factor
    
    # Initial floor
    # Use round(floor(x * factor)) / factor to avoid float precision issues before floor?
    # Standard: floor(x * factor) / factor
    # We add a tiny epsilon to handle float nines (e.g. 19.9999999 -> 20)
    splits_floored = np.floor(raw_splits * factor + 1e-9) / factor
    
    # Calculate remainder per row
    current_sums = splits_floored.sum(axis=1)
    remainders = values - current_sums
    
    # How many pennies to distribute?
    # Round to nearest integer count of pennies
    pennies_needed = np.round(remainders * factor).astype(int)
    
    # Distribute pennies based on largest fractional part ("Largest Remainder Method")
    # Fractional part = Raw - Floored
    fractional_parts = raw_splits - splits_floored
    
    # We want to find the indices of the top N largest fractional parts for each row.
    # N = pennies_needed[row]
    
    # Create a rank matrix where 0 is the largest fractional part, 1 is second, etc.
    # argsort(argsort(-x)) gives the rank (0-based)
    ranks = np.argsort(np.argsort(-fractional_parts, axis=1), axis=1)
    
    # Mask: True if rank < pennies_needed
    # We need to broadcast pennies_needed (n_rows,) to (n_rows, n_cols)
    pennies_needed_2d = pennies_needed[:, np.newaxis]
    mask = ranks < pennies_needed_2d
    
    # Add pennies where mask is True
    final_splits = splits_floored + np.where(mask, penny, 0.0)
    
    return pd.DataFrame(final_splits, index=series.index)
