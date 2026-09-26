#!/usr/bin/env python3
"""
production/scanner.py
Production Master Task 3: Core Momentum Scanner with Pluggable RRG Hook

Evaluates the verified institutional 5-tier strategy rules on the standardized
survivorship-free universe:
  1. Filter 1 (Retracement): Close >= 0.80 * 252d High (within 20% of 52w high).
  2. Filter 2 (Trend): Close > 200 EMA.
  3. Filter 3 (Relative Strength): Stock / NIFTY 500 ratio > 200 EMA of ratio.
  4. Ranking Metric: Volar Score = Return_252 / max(vol_252, 0.05).
  5. Market Regime: NIFTY 500 Close vs 20-day EMA (Normal vs Defensive).
  6. Pluggable Extension: Evaluates active plugins (e.g. JdK RRG Filter).

Outputs:
  - deliverables/phase_8/data_csv/screener_output_live.csv
"""

import sys
import os
import argparse
import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np

BASE_DIR = Path("/storage/emulated/0/Documents/Project MIP")
DATA_DIR = BASE_DIR / "data"
PROD_DIR = BASE_DIR / "production"
PLUGINS_DIR = PROD_DIR / "plugins"

if str(PROD_DIR) not in sys.path:
    sys.path.insert(0, str(PROD_DIR))

from plugins.rrg_filter import RRGFilterPlugin
from breadth import MarketBreadthEngine

UNIVERSE_PARQUET = DATA_DIR / "universe/nifty500_pit_universe.parquet"
BENCHMARK_CSV = BASE_DIR / "deliverables/phase_7/data_csv/nifty_500_benchmark_proxy.csv"
DEFAULT_OUTPUT_CSV = BASE_DIR / "deliverables/phase_8/data_csv/screener_output_live.csv"


class ProductionScanner:
    """Institutional momentum screener with pluggable filter hooks."""

    def __init__(
        self,
        universe_parquet: Path = UNIVERSE_PARQUET,
        benchmark_csv: Path = BENCHMARK_CSV,
        enable_rrg: bool = False
    ):
        self.universe_parquet = Path(universe_parquet)
        self.benchmark_csv = Path(benchmark_csv)
        self.plugins = [
            RRGFilterPlugin(enabled=enable_rrg)
        ]
        self.breadth_engine = MarketBreadthEngine(
            universe_parquet=self.universe_parquet,
            benchmark_csv=self.benchmark_csv
        )

    def log(self, msg: str):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {msg}")

    def load_benchmark(self) -> pd.DataFrame:
        """Loads continuous benchmark proxy."""
        if not self.benchmark_csv.exists():
            raise FileNotFoundError(f"Benchmark CSV not found at {self.benchmark_csv}")
        df = pd.read_csv(self.benchmark_csv)
        df["date"] = df["date"].astype(str)
        return df

    def evaluate_regime(self, as_of_date: str) -> Dict:
        """Checks NIFTY 500 close against 20 EMA."""
        b_df = self.load_benchmark()
        row = b_df[b_df["date"] == as_of_date]
        if row.empty:
            prior = b_df[b_df["date"] <= as_of_date]
            if prior.empty:
                raise ValueError(f"No benchmark data on or before {as_of_date}")
            row = prior.iloc[[-1]]

        c = float(row["close"].values[0])
        e20 = float(row["ema_20"].values[0])
        is_normal = (c >= e20)
        label = "NORMAL (Risk-On: Entries Active)" if is_normal else "DEFENSIVE (Risk-Off: Entries Paused / Cash Active)"
        return {
            "date": row["date"].values[0],
            "close": c,
            "ema_20": e20,
            "is_normal": is_normal,
            "label": label
        }

    def run_scan(
        self,
        as_of_date: str,
        output_csv: Optional[Path] = None,
        lookback_days: int = 550
    ) -> pd.DataFrame:
        """Runs the momentum screen and ranks qualifying stocks."""
        dest_csv = Path(output_csv) if output_csv else DEFAULT_OUTPUT_CSV
        dest_csv.parent.mkdir(parents=True, exist_ok=True)

        self.log("==================================================================")
        self.log(f"RUNNING PRODUCTION MOMENTUM SCANNER AS OF {as_of_date}")
        self.log("==================================================================")

        # 1. Market Regime
        regime = self.evaluate_regime(as_of_date)
        self.log(f"Market Regime: NIFTY 500 Close = ₹{regime['close']:.2f} | 20 EMA = ₹{regime['ema_20']:.2f}")
        self.log(f"Status:        {regime['label']}")

        # 2. Benchmark Mapping
        b_df = self.load_benchmark()
        bench_map = dict(zip(b_df["date"], b_df["close"]))

        # 3. Load Universe Bars
        target_dt = datetime.datetime.strptime(as_of_date, "%Y-%m-%d")
        start_str = (target_dt - datetime.timedelta(days=lookback_days)).strftime("%Y-%m-%d")

        self.log(f"Loading bars from {start_str} to {as_of_date}...")
        bars = pd.read_parquet(
            self.universe_parquet,
            filters=[("date", ">=", start_str), ("date", "<=", as_of_date)]
        )
        self.log(f"Loaded {len(bars):,} bars across {bars['symbol'].nunique():,} symbols.")

        # Filter to symbols trading on as_of_date
        active_today = set(bars[bars["date"] == as_of_date]["symbol"].unique())
        bars = bars[bars["symbol"].isin(active_today)].copy()
        bars = bars.sort_values(by=["symbol", "date"]).reset_index(drop=True)

        # 4. Technical Indicators
        self.log("Computing technical indicators (52w High/Low, EMAs 200/50/20, Volar, RS Ratio)...")
        bars["high_252"] = bars.groupby("symbol")["high"].transform(
            lambda s: s.rolling(252, min_periods=50).max()
        )
        bars["low_252"] = bars.groupby("symbol")["low"].transform(
            lambda s: s.rolling(252, min_periods=50).min()
        )
        bars["ema_200"] = bars.groupby("symbol")["close"].transform(
            lambda s: s.ewm(span=200, adjust=True, min_periods=50).mean()
        )
        bars["ema_50"] = bars.groupby("symbol")["close"].transform(
            lambda s: s.ewm(span=50, adjust=True, min_periods=20).mean()
        )
        bars["ema_20"] = bars.groupby("symbol")["close"].transform(
            lambda s: s.ewm(span=20, adjust=True, min_periods=10).mean()
        )
        bars["ret_252"] = bars.groupby("symbol")["close"].transform(
            lambda s: s / s.shift(252) - 1.0
        )
        bars["ret_1d"] = bars.groupby("symbol")["close"].pct_change().fillna(0.0)
        bars["vol_252"] = bars.groupby("symbol")["ret_1d"].transform(
            lambda s: s.rolling(252, min_periods=20).std() * np.sqrt(252)
        ).fillna(0.30).replace(0.0, 0.30)

        # Relative Strength Ratio vs NIFTY 500
        bars["benchmark_close"] = bars["date"].map(bench_map).fillna(1.0)
        bars["rs_ratio"] = bars["close"] / bars["benchmark_close"]
        bars["rs_ema_200"] = bars.groupby("symbol")["rs_ratio"].transform(
            lambda s: s.ewm(span=200, adjust=True, min_periods=50).mean()
        )
        bars["rs_pass"] = bars["rs_ratio"] > bars["rs_ema_200"]

        # 5. Evaluate Plugins (including RRG)
        for plugin in self.plugins:
            self.log(f"Applying plugin: {plugin.name} (enabled={plugin.enabled})...")
            bars = plugin.evaluate(bars, as_of_date=as_of_date)

        # 6. Extract Target Date Snapshot
        snapshot = bars[bars["date"] == as_of_date].copy()
        snapshot["high_252"] = snapshot["high_252"].fillna(snapshot["close"])
        snapshot["low_252"] = snapshot["low_252"].fillna(snapshot["close"])
        snapshot["distance_52wh_pct"] = (snapshot["close"] / snapshot["high_252"] - 1.0) * 100.0
        snapshot["ema_200_ratio"] = snapshot["close"] / snapshot["ema_200"]

        # 6b. Market Breadth & RRG Analytics
        breadth_data = self.breadth_engine.compute_breadth(as_of_date=as_of_date, snapshot_df=snapshot)
        self.breadth_engine.export_json(breadth_data)
        self.breadth_engine.print_summary(breadth_data)

        # Core 3 Filters
        snapshot["filter1_pass"] = snapshot["close"] >= (0.80 * snapshot["high_252"])
        snapshot["filter2_pass"] = snapshot["close"] > snapshot["ema_200"]
        snapshot["filter3_pass"] = snapshot["rs_pass"].fillna(False)

        # Check plugin passes
        plugin_passed = pd.Series(True, index=snapshot.index)
        for plugin in self.plugins:
            col_name = f"passed_{plugin.name}"
            if col_name in snapshot.columns:
                plugin_passed = plugin_passed & snapshot[col_name]

        snapshot["is_qualified"] = (
            snapshot["filter1_pass"] &
            snapshot["filter2_pass"] &
            snapshot["filter3_pass"] &
            snapshot["ret_252"].notnull() &
            plugin_passed
        )

        # Volar Score = Return_252 / Vol_252
        snapshot["volar_score"] = snapshot["ret_252"] / snapshot["vol_252"].clip(lower=0.05)

        # Separate qualified and non-qualified
        qual = snapshot[snapshot["is_qualified"] == True].copy()
        qual = qual.sort_values(by=["volar_score", "symbol"], ascending=[False, True]).reset_index(drop=True)
        qual["rank"] = np.arange(1, len(qual) + 1)

        non_qual = snapshot[snapshot["is_qualified"] == False].copy()
        non_qual = non_qual.sort_values(by=["volar_score", "symbol"], ascending=[False, True]).reset_index(drop=True)
        non_qual["rank"] = np.arange(len(qual) + 1, len(snapshot) + 1)

        full_df = pd.concat([qual, non_qual], ignore_index=True)

        cols = [
            "rank", "symbol", "close", "high_252", "distance_52wh_pct",
            "ema_200", "ema_200_ratio", "ret_252", "vol_252", "volar_score",
            "volume", "is_delisted", "filter1_pass", "filter2_pass", "filter3_pass",
            "is_qualified"
        ]
        if "rrg_quadrant" in full_df.columns:
            cols.extend(["rrg_rs_ratio", "rrg_rs_momentum", "rrg_quadrant", "passed_rrg"])

        export_df = full_df[[c for c in cols if c in full_df.columns]].copy()

        # Format numbers
        export_df["close"] = export_df["close"].round(2)
        export_df["high_252"] = export_df["high_252"].round(2)
        export_df["distance_52wh_pct"] = export_df["distance_52wh_pct"].round(2)
        export_df["ema_200"] = export_df["ema_200"].round(2)
        export_df["ema_200_ratio"] = export_df["ema_200_ratio"].round(4)
        export_df["ret_252"] = (export_df["ret_252"] * 100.0).round(2)
        export_df["vol_252"] = (export_df["vol_252"] * 100.0).round(2)
        export_df["volar_score"] = export_df["volar_score"].round(4)

        if "rrg_rs_ratio" in export_df.columns:
            export_df["rrg_rs_ratio"] = export_df["rrg_rs_ratio"].round(2)
            export_df["rrg_rs_momentum"] = export_df["rrg_rs_momentum"].round(2)

        export_df.to_csv(dest_csv, index=False)
        self.log(f"Exported live screener results ({len(export_df)} scrips) to {dest_csv}")

        # Summary
        n_act = len(snapshot)
        n_qual = len(qual)
        self.log("------------------------------------------------------------------")
        self.log(f"SCREENING SUMMARY: Active: {n_act:,} | Qualified Candidates: {n_qual:,} ({n_qual/n_act*100:.1f}%)")
        self.log("------------------------------------------------------------------")

        top20_raw = qual.head(20).copy()
        top20 = pd.DataFrame({
            "rank": top20_raw["rank"],
            "symbol": top20_raw["symbol"],
            "close": "₹" + top20_raw["close"].round(2).astype(str),
            "distance_52wh_pct": top20_raw["distance_52wh_pct"].round(2).astype(str) + "%",
            "volar_score": top20_raw["volar_score"].round(4),
            "rrg_quadrant": top20_raw["rrg_quadrant"] if "rrg_quadrant" in top20_raw.columns else "N/A",
            "rrg_rs_ratio": top20_raw["rrg_rs_ratio"].round(2) if "rrg_rs_ratio" in top20_raw.columns else 100.0,
        })
        self.log("\n" + top20.to_string(index=False))
        self.log("==================================================================\n")

        return export_df


def main():
    parser = argparse.ArgumentParser(description="Production Momentum Scanner")
    parser.add_argument("--as-of-date", type=str, default="2026-08-28", help="Target EOD date (YYYY-MM-DD)")
    parser.add_argument("--output", type=str, default=str(DEFAULT_OUTPUT_CSV), help="Output CSV path")
    parser.add_argument("--enable-rrg", action="store_true", help="Enable Relative Rotation Graph (RRG) filter")

    args = parser.parse_args()
    scanner = ProductionScanner(enable_rrg=args.enable_rrg)
    scanner.run_scan(as_of_date=args.as_of_date, output_csv=Path(args.output))


if __name__ == "__main__":
    main()
