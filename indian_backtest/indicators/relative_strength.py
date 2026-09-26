"""
indian_backtest.indicators.relative_strength
===========================================
Podcast Extension E1: Relative Strength (RS) ratio of stock vs NIFTY 500 benchmark over 12 months (252 trading days).
Ranks surviving candidates by their relative outperformance vs the broader market index.
"""

from typing import Dict, Optional
import numpy as np
import pandas as pd

def calculate_relative_strength(
    stock_return_252: float,
    benchmark_return_252: float
) -> float:
    """
    Computes 12-month Relative Strength (RS) ratio:
        RS = (1.0 + R_stock) / (1.0 + R_benchmark)
    If benchmark return <= -1.0 (edge case), uses difference: R_stock - R_benchmark.
    """
    denom = 1.0 + benchmark_return_252
    if denom > 0.01:
        return (1.0 + stock_return_252) / denom
    return stock_return_252 - benchmark_return_252
