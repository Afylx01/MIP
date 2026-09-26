"""
indian_backtest.indicators.moving_averages
=========================================
Exponential and simple moving average calculations.
"""

import numpy as np
import pandas as pd

def calculate_ema_200(series: pd.Series) -> pd.Series:
    """
    Computes 200-day Exponential Moving Average (EMA).
    """
    return series.ewm(span=200, adjust=True, min_periods=1).mean()

def calculate_sma(series: pd.Series, period: int = 50) -> pd.Series:
    """
    Computes Simple Moving Average (SMA).
    """
    return series.rolling(window=period, min_periods=1).mean()
