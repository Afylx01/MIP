#!/usr/bin/env python3
"""
production/breadth.py
Production Market Breadth Engine for Project MIP.

Computes comprehensive market breadth indicators across the point-in-time universe:
  1. Trend Participation Breadth:
     - pct_above_200_ema (% > 200 EMA)
     - pct_above_50_ema (% > 50 EMA)
     - pct_above_20_ema (% > 20 EMA)
  2. High Proximity Breadth (Candidate Pool Viability):
     - pct_within_20pct_52wh (% within 20% of 52w High)
     - pct_within_5pct_52wh (% within 5% of 52w High)
  3. Net New Highs:
     - new_52w_highs (Close >= 0.99 * High_252)
     - new_52w_lows (Close <= 1.01 * Low_252)
     - net_highs_lows (new_52w_highs - new_52w_lows)
  4. Breadth Regime Classification:
     - 🟢 STRONG EXPANSION: pct_above_200_ema >= 60.0% AND pct_above_50_ema >= 55.0%
     - 🟡 SELECTIVE / NEUTRAL: 40.0% <= pct_above_200_ema < 60.0%
     - 🔴 CONTRACTION / DEFENSIVE: pct_above_200_ema < 40.0% OR (pct_above_200_ema < 50.0% AND net_highs_lows < 0)
  5. RRG Universe Distribution:
     - LEADING, IMPROVING, WEAKENING, LAGGING counts and percentages

Exports live snapshot to deliverables/phase_8/data_csv/market_breadth_live.json
"""

import sys
import os
import json
import shutil
import argparse
import datetime
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd
import numpy as np

def get_base_dir() -> Path:
    """Dynamically resolves Project MIP root across Windows and Linux."""
    if "PROJECT_MIP_DIR" in os.environ and Path(os.environ["PROJECT_MIP_DIR"]).exists():
        return Path(os.environ["PROJECT_MIP_DIR"])
    android_path = Path("/storage/emulated/0/Documents/Project MIP")
    if android_path.exists():
        return android_path
    cur = Path(__file__).resolve()
    for p in [cur] + list(cur.parents):
        if (p / "run_mip.py").exists() or (p / "data/universe").exists():
            return p
    return cur.parent.parent if cur.parent.name in ["production", "scripts"] else cur.parent


def get_deliverables_mirror_dir(base_dir: Path) -> Path:
    """Resolves deliverables mirror directory safely across environments."""
    sdcard_mirror = Path("/sdcard/Documents/deliverables")
    if sdcard_mirror.exists() and sdcard_mirror.is_dir():
        return sdcard_mirror
    local_mirror = base_dir / "deliverables"
    local_mirror.mkdir(parents=True, exist_ok=True)
    return local_mirror


BASE_DIR = get_base_dir()
DATA_DIR = BASE_DIR / "data"
UNIVERSE_PARQUET = DATA_DIR / "universe/nifty500_pit_universe.parquet"
BENCHMARK_CSV = BASE_DIR / "deliverables/phase_7/data_csv/nifty_500_benchmark_proxy.csv"
DEFAULT_OUTPUT_JSON = BASE_DIR / "deliverables/phase_8/data_csv/market_breadth_live.json"
MIRROR_OUTPUT_JSON = get_deliverables_mirror_dir(BASE_DIR) / "market_breadth_live.json"


PROD_DIR = BASE_DIR / "production"
if str(PROD_DIR) not in sys.path:
    sys.path.insert(0, str(PROD_DIR))

from plugins.rrg_filter import RRGFilterPlugin


class MarketBreadthEngine:
    """Quantitative Market Breadth & RRG Distribution Engine."""

    def __init__(
        self,
        universe_parquet: Path = UNIVERSE_PARQUET,
        benchmark_csv: Path = BENCHMARK_CSV
    ):
        self.universe_parquet = Path(universe_parquet)
        self.benchmark_csv = Path(benchmark_csv)

    def log(self, msg: str):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [BreadthEngine] {msg}")

    def load_benchmark(self) -> pd.DataFrame:
        """Loads continuous benchmark proxy."""
        if not self.benchmark_csv.exists():
            raise FileNotFoundError(f"Benchmark CSV not found at {self.benchmark_csv}")
        df = pd.read_csv(self.benchmark_csv)
        df["date"] = df["date"].astype(str)
        return df

    def compute_breadth(
        self,
        as_of_date: str,
        snapshot_df: Optional[pd.DataFrame] = None,
        lookback_days: int = 550
    ) -> Dict:
        """
        Computes all market breadth metrics and RRG distributions.
        If snapshot_df is provided with pre-calculated indicators, uses it.
        Otherwise loads bars from universe parquet and calculates indicators.
        """
        self.log(f"Computing Market Breadth as of {as_of_date}...")

        # If pre-calculated snapshot with all indicators is provided, use it
        req_cols = {"close", "ema_200", "ema_50", "ema_20", "high_252", "low_252"}
        if snapshot_df is not None and req_cols.issubset(set(snapshot_df.columns)):
            snap = snapshot_df[snapshot_df["date"] == as_of_date].copy() if "date" in snapshot_df.columns else snapshot_df.copy()
        else:
            # Load universe bars and calculate indicators
            target_dt = datetime.datetime.strptime(as_of_date, "%Y-%m-%d")
            start_str = (target_dt - datetime.timedelta(days=lookback_days)).strftime("%Y-%m-%d")

            self.log(f"Loading universe bars from {start_str} to {as_of_date}...")
            bars = pd.read_parquet(
                self.universe_parquet,
                filters=[("date", ">=", start_str), ("date", "<=", as_of_date)]
            )

            # Filter to symbols active on target date
            active_today = set(bars[bars["date"] == as_of_date]["symbol"].unique())
            bars = bars[bars["symbol"].isin(active_today)].copy()
            bars = bars.sort_values(by=["symbol", "date"]).reset_index(drop=True)

            self.log("Calculating EMAs (20, 50, 200) and 52-week High/Low...")
            bars["ema_200"] = bars.groupby("symbol")["close"].transform(
                lambda s: s.ewm(span=200, adjust=True, min_periods=50).mean()
            )
            bars["ema_50"] = bars.groupby("symbol")["close"].transform(
                lambda s: s.ewm(span=50, adjust=True, min_periods=20).mean()
            )
            bars["ema_20"] = bars.groupby("symbol")["close"].transform(
                lambda s: s.ewm(span=20, adjust=True, min_periods=10).mean()
            )
            bars["high_252"] = bars.groupby("symbol")["high"].transform(
                lambda s: s.rolling(252, min_periods=50).max()
            )
            bars["low_252"] = bars.groupby("symbol")["low"].transform(
                lambda s: s.rolling(252, min_periods=50).min()
            )

            # RRG Indicators
            b_df = self.load_benchmark()
            bench_map = dict(zip(b_df["date"], b_df["close"]))
            bars["benchmark_close"] = bars["date"].map(bench_map).fillna(1.0)
            rrg_plugin = RRGFilterPlugin(enabled=False)
            bars = rrg_plugin.evaluate(bars, as_of_date=as_of_date)

            snap = bars[bars["date"] == as_of_date].copy()

        # Fill any missing extremes with current close
        snap["high_252"] = snap["high_252"].fillna(snap["close"])
        snap["low_252"] = snap["low_252"].fillna(snap["close"])
        snap["ema_200"] = snap["ema_200"].fillna(snap["close"])
        snap["ema_50"] = snap["ema_50"].fillna(snap["close"])
        snap["ema_20"] = snap["ema_20"].fillna(snap["close"])

        total_scanned = len(snap)
        if total_scanned == 0:
            raise ValueError(f"No active universe symbols found on {as_of_date}")

        # 1. Trend Participation Breadth
        above_200 = int((snap["close"] > snap["ema_200"]).sum())
        above_50 = int((snap["close"] > snap["ema_50"]).sum())
        above_20 = int((snap["close"] > snap["ema_20"]).sum())

        pct_above_200 = round((above_200 / total_scanned) * 100.0, 2)
        pct_above_50 = round((above_50 / total_scanned) * 100.0, 2)
        pct_above_20 = round((above_20 / total_scanned) * 100.0, 2)

        # 2. High Proximity Breadth
        within_20pct = int((snap["close"] >= 0.80 * snap["high_252"]).sum())
        within_5pct = int((snap["close"] >= 0.95 * snap["high_252"]).sum())

        pct_within_20 = round((within_20pct / total_scanned) * 100.0, 2)
        pct_within_5 = round((within_5pct / total_scanned) * 100.0, 2)

        # 3. Net New Highs / Lows
        new_highs = int((snap["close"] >= 0.99 * snap["high_252"]).sum())
        new_lows = int((snap["close"] <= 1.01 * snap["low_252"]).sum())
        net_highs_lows = new_highs - new_lows

        # 4. Market Breadth Regime Classification
        # 🟢 STRONG EXPANSION: pct_above_200_ema >= 60.0% AND pct_above_50_ema >= 55.0%
        # 🟡 SELECTIVE / NEUTRAL: 40.0% <= pct_above_200_ema < 60.0%
        # 🔴 CONTRACTION / DEFENSIVE: pct_above_200_ema < 40.0% OR (pct_above_200_ema < 50.0% AND net_highs_lows < 0)
        if pct_above_200 < 40.0 or (pct_above_200 < 50.0 and net_highs_lows < 0):
            regime_key = "CONTRACTION"
            regime_label = "🔴 CONTRACTION / DEFENSIVE"
            regime_emoji = "🔴"
            regime_desc = "Breadth deterioration; defensive cash posture advised"
        elif pct_above_200 >= 60.0 and pct_above_50 >= 55.0:
            regime_key = "EXPANSION"
            regime_label = "🟢 STRONG EXPANSION"
            regime_emoji = "🟢"
            regime_desc = "Broad-based momentum expansion across market segments"
        else:
            regime_key = "NEUTRAL"
            regime_label = "🟡 SELECTIVE / NEUTRAL"
            regime_emoji = "🟡"
            regime_desc = "Selective leadership; strict risk-adjusted criteria required"

        # 5. RRG Universe Distribution
        rrg_dist = {}
        if "rrg_quadrant" in snap.columns:
            for quad, bias in [
                ("LEADING", "🟢 OUTPERFORM"),
                ("IMPROVING", "🟢 ACCELERATING"),
                ("WEAKENING", "🟡 DECELERATING"),
                ("LAGGING", "🔴 UNDERPERFORM")
            ]:
                cnt = int((snap["rrg_quadrant"] == quad).sum())
                pct = round((cnt / total_scanned) * 100.0, 2)
                rrg_dist[quad] = {
                    "count": cnt,
                    "pct": pct,
                    "bias": bias
                }

        breadth_data = {
            "as_of_date": as_of_date,
            "universe_size": total_scanned,
            "trend_participation": {
                "pct_above_200_ema": pct_above_200,
                "pct_above_50_ema": pct_above_50,
                "pct_above_20_ema": pct_above_20,
                "count_above_200_ema": above_200,
                "count_above_50_ema": above_50,
                "count_above_20_ema": above_20
            },
            "high_proximity": {
                "pct_within_20pct_52wh": pct_within_20,
                "pct_within_5pct_52wh": pct_within_5,
                "count_within_20pct_52wh": within_20pct,
                "count_within_5pct_52wh": within_5pct
            },
            "net_new_highs": {
                "new_52w_highs": new_highs,
                "new_52w_lows": new_lows,
                "net_highs_lows": net_highs_lows
            },
            "regime": {
                "key": regime_key,
                "classification": regime_key,
                "label": regime_label,
                "emoji": regime_emoji,
                "description": regime_desc
            },
            "rrg_distribution": rrg_dist,
            # Convenient top-level shortcuts
            "pct_above_200_ema": pct_above_200,
            "pct_above_50_ema": pct_above_50,
            "pct_above_20_ema": pct_above_20,
            "pct_within_20pct_52wh": pct_within_20,
            "pct_within_5pct_52wh": pct_within_5,
            "new_52w_highs": new_highs,
            "new_52w_lows": new_lows,
            "net_highs_lows": net_highs_lows,
            "breadth_regime": regime_label,
            "timestamp": datetime.datetime.now().isoformat()
        }

        return breadth_data

    def export_json(
        self,
        breadth_data: Dict,
        output_path: Optional[Path] = None
    ) -> Path:
        """Exports breadth dictionary to JSON and mirrors to shared deliverables."""
        dest_json = Path(output_path) if output_path else DEFAULT_OUTPUT_JSON
        dest_json.parent.mkdir(parents=True, exist_ok=True)

        with open(dest_json, "w", encoding="utf-8") as f:
            json.dump(breadth_data, f, indent=2)
        self.log(f"Exported live breadth snapshot to {dest_json}")

        try:
            MIRROR_OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(dest_json, MIRROR_OUTPUT_JSON)
            self.log(f"Mirrored breadth snapshot to {MIRROR_OUTPUT_JSON}")
        except Exception as e:
            self.log(f"Note: Could not mirror to {MIRROR_OUTPUT_JSON}: {e}")

        return dest_json

    def print_summary(self, breadth_data: Dict):
        """Prints formatted market breadth tearsheet to console."""
        b = breadth_data
        tp = b["trend_participation"]
        hp = b["high_proximity"]
        nh = b["net_new_highs"]
        reg = b["regime"]
        rrg = b.get("rrg_distribution", {})

        print("\n" + "=" * 65)
        print(f"MARKET BREADTH & RRG TEARSHEET — AS OF {b['as_of_date']}")
        print("=" * 65)
        print(f"Universe Size:           {b['universe_size']:,} scrips")
        print(f"Breadth Regime:          {reg['label']}")
        print(f"Assessment:              {reg['description']}")
        print("-" * 65)
        print("TREND PARTICIPATION BREADTH:")
        print(f"  • % Above 200 EMA:     {tp['pct_above_200_ema']:>6.2f}%  ({tp['count_above_200_ema']}/{b['universe_size']})")
        print(f"  • % Above 50 EMA:      {tp['pct_above_50_ema']:>6.2f}%  ({tp['count_above_50_ema']}/{b['universe_size']})")
        print(f"  • % Above 20 EMA:      {tp['pct_above_20_ema']:>6.2f}%  ({tp['count_above_20_ema']}/{b['universe_size']})")
        print("-" * 65)
        print("HIGH PROXIMITY & LEADERSHIP:")
        print(f"  • % Within 20% 52wH:   {hp['pct_within_20pct_52wh']:>6.2f}%  ({hp['count_within_20pct_52wh']}/{b['universe_size']})")
        print(f"  • % Within 5% 52wH:    {hp['pct_within_5pct_52wh']:>6.2f}%  ({hp['count_within_5pct_52wh']}/{b['universe_size']})")
        print(f"  • New 52-Week Highs:   {nh['new_52w_highs']:>6d}")
        print(f"  • New 52-Week Lows:    {nh['new_52w_lows']:>6d}")
        print(f"  • Net Highs - Lows:    {nh['net_highs_lows']:>+6d}")
        if rrg:
            print("-" * 65)
            print("RELATIVE ROTATION GRAPH (RRG) DISTRIBUTION:")
            for q, d in rrg.items():
                print(f"  • {q:<10}:        {d['count']:>4d}  ({d['pct']:>5.1f}%)  {d['bias']}")
        print("=" * 65 + "\n")


def main():
    parser = argparse.ArgumentParser(description="MIP Market Breadth Engine")
    parser.add_argument("--as-of-date", type=str, default="2026-08-28", help="Target EOD date (YYYY-MM-DD)")
    parser.add_argument("--output", type=str, default=str(DEFAULT_OUTPUT_JSON), help="Output JSON path")

    args = parser.parse_args()
    engine = MarketBreadthEngine()
    breadth = engine.compute_breadth(as_of_date=args.as_of_date)
    engine.export_json(breadth, output_path=Path(args.output))
    engine.print_summary(breadth)


if __name__ == "__main__":
    main()
