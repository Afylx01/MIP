"""
indian_backtest.indicators.price_extremes
========================================
52-week (252-trading-day) price extreme channels and Rule R2 threshold calculations.
"""

import pandas as pd

def calculate_high_252(series: pd.Series) -> pd.Series:
    """
    Computes 252-trading-day rolling maximum of close price.
    """
    return series.rolling(window=252, min_periods=1).max()

def is_r2_satisfied(close: float, high_252: float, threshold_factor: float = 0.80) -> bool:
    """
    Rule R2: Close must be within 20% of its 52-week high (close >= 0.80 * high_252).
    """
    if high_252 <= 0:
        return False
    return close >= threshold_factor * high_252
