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
from typing import Optional, List, Dict
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


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Standalone JdK Relative Rotation Graph Analyzer")
    parser.add_argument("--as-of-date", type=str, default="2026-08-28", help="Analysis date (YYYY-MM-DD)")
    args = parser.parse_args()

    as_of_date = args.as_of_date
    android_path = Path("/storage/emulated/0/Documents/Project MIP")
    if "PROJECT_MIP_DIR" in os.environ and Path(os.environ["PROJECT_MIP_DIR"]).exists():
        base_dir = Path(os.environ["PROJECT_MIP_DIR"])
    elif android_path.exists():
        base_dir = android_path
    else:
        cur = Path(__file__).resolve()
        base_dir = cur.parent.parent.parent

    uni_path = base_dir / "data/universe/nifty500_pit_universe.parquet"
    bench_path = base_dir / "deliverables/phase_7/data_csv/nifty_500_benchmark_proxy.csv"

    print("\n" + "=" * 70)
    print(f"🌀  JdK RELATIVE ROTATION GRAPH (RRG) ANALYZER — AS OF {as_of_date}")
    print("=" * 70)

    # Load benchmark
    b_df = pd.read_csv(bench_path)
    b_df["date"] = b_df["date"].astype(str)
    bench_map = dict(zip(b_df["date"], b_df["close"]))

    # Load universe bars for past 200 days
    dt = pd.to_datetime(as_of_date)
    start_str = (dt - pd.Timedelta(days=200)).strftime("%Y-%m-%d")
    bars = pd.read_parquet(uni_path, filters=[("date", ">=", start_str), ("date", "<=", as_of_date)])
    active = set(bars[bars["date"] == as_of_date]["symbol"].unique())
    bars = bars[bars["symbol"].isin(active)].copy()
    bars = bars.sort_values(by=["symbol", "date"]).reset_index(drop=True)
    bars["benchmark_close"] = bars["date"].map(bench_map).fillna(1.0)

    plugin = RRGFilterPlugin(enabled=False)
    bars = plugin.evaluate(bars, as_of_date=as_of_date)
    snap = bars[bars["date"] == as_of_date].copy()

    total = len(snap)
    print(f"Universe Scanned: {total:,} active scrips\n")

    print(f"{'QUADRANT':<12}{'COUNT':<8}{'PCT':<8}{'STATUS'}")
    print("-" * 55)
    for q, bias in [
        ("LEADING", "🟢 Outperforming Benchmark (Ratio >= 100, Mom >= 100)"),
        ("IMPROVING", "🟢 Accelerating into Leadership (Ratio < 100, Mom >= 100)"),
        ("WEAKENING", "🟡 Decelerating (Ratio >= 100, Mom < 100)"),
        ("LAGGING", "🔴 Underperforming Benchmark (Ratio < 100, Mom < 100)"),
    ]:
        cnt = (snap["rrg_quadrant"] == q).sum()
        pct = (cnt / total) * 100.0 if total > 0 else 0.0
        print(f"{q:<12}{cnt:>5d}   {pct:>5.1f}%   {bias}")
    print("-" * 55)

    # Top Leading
    lead = snap[snap["rrg_quadrant"] == "LEADING"].sort_values(by="rrg_rs_ratio", ascending=False).head(10)
    print("\nTOP 10 LEADING SCRIPS BY RS-RATIO:")
    print(f"{'SYMBOL':<12}{'PRICE':<10}{'RS-RATIO':<12}{'RS-MOMENTUM'}")
    print("-" * 50)
    for _, r in lead.iterrows():
        print(f"{r['symbol']:<12}₹{r['close']:<9.1f}{r['rrg_rs_ratio']:<12.1f}{r['rrg_rs_momentum']:.1f}")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()

