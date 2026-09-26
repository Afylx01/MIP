#!/usr/bin/env python3
"""
production/plugins/rrg_filter.py
Relative Rotation Graph (RRG) Plugin for Project MIP.

Implements the Julius de Kempenaer (JdK) Relative Rotation Graph model:
  - RS = Stock_Price / Benchmark_Price
  - RS-Ratio = 100.0 * (RS / SMA_50(RS))
  - RS-Momentum = 100.0 * (RS-Ratio / SMA_10(RS-Ratio))
  - Quadrant Classification:
      - LEADING:    RS-Ratio >= 100 and RS-Momentum >= 100
      - WEAKENING:  RS-Ratio >= 100 and RS-Momentum < 100
      - LAGGING:    RS-Ratio < 100 and RS-Momentum < 100
      - IMPROVING:  RS-Ratio < 100 and RS-Momentum >= 100
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Ensure plugin base is importable
PROD_DIR = Path(__file__).resolve().parent.parent
if str(PROD_DIR) not in sys.path:
    sys.path.insert(0, str(PROD_DIR))

from plugins.base_plugin import FilterPlugin


class RRGFilterPlugin(FilterPlugin):
    """JdK Relative Rotation Graph Filter & Quadrant Classifier."""

    def __init__(
        self,
        enabled: bool = False,
        ratio_period: int = 50,
        momentum_period: int = 10,
        allowed_quadrants: Optional[list] = None
    ):
        super().__init__(name="rrg", enabled=enabled)
        self.ratio_period = ratio_period
        self.momentum_period = momentum_period
        self.allowed_quadrants = allowed_quadrants or ["LEADING", "IMPROVING"]

    def evaluate(self, universe_df: pd.DataFrame, as_of_date: str) -> pd.DataFrame:
        """
        Calculates RS-Ratio, RS-Momentum, Quadrant, and adds 'passed_rrg' column.
        Expects universe_df to have columns: ['symbol', 'date', 'close', 'benchmark_close'].
        """
        df = universe_df.copy()

        if "benchmark_close" not in df.columns:
            # Fall back to flat ratio if benchmark not provided
            df["benchmark_close"] = 1.0

        # Calculate RS Ratio
        df["rrg_raw_rs"] = df["close"] / df["benchmark_close"].replace(0.0, np.nan)

        # RS-Ratio (normalized relative to moving average)
        df["rrg_rs_sma"] = df.groupby("symbol")["rrg_raw_rs"].transform(
            lambda s: s.rolling(self.ratio_period, min_periods=10).mean()
        )
        df["rrg_rs_ratio"] = 100.0 * (df["rrg_raw_rs"] / df["rrg_rs_sma"].replace(0.0, np.nan)).fillna(100.0)

        # RS-Momentum (normalized relative to RS-Ratio moving average)
        df["rrg_ratio_sma"] = df.groupby("symbol")["rrg_rs_ratio"].transform(
            lambda s: s.rolling(self.momentum_period, min_periods=3).mean()
        )
        df["rrg_rs_momentum"] = 100.0 * (df["rrg_rs_ratio"] / df["rrg_ratio_sma"].replace(0.0, np.nan)).fillna(100.0)

        # Classify Quadrant
        def classify_quadrant(row):
            ratio = row["rrg_rs_ratio"]
            mom = row["rrg_rs_momentum"]
            if ratio >= 100.0 and mom >= 100.0:
                return "LEADING"
            elif ratio >= 100.0 and mom < 100.0:
                return "WEAKENING"
            elif ratio < 100.0 and mom < 100.0:
                return "LAGGING"
            else:
                return "IMPROVING"

        df["rrg_quadrant"] = df.apply(classify_quadrant, axis=1)

        # Determine pass/fail
        if self.enabled:
            df["passed_rrg"] = df["rrg_quadrant"].isin(self.allowed_quadrants)
        else:
            # When disabled, all rows pass but diagnostic columns are retained
            df["passed_rrg"] = True

        return df
