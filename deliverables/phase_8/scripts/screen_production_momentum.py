#!/usr/bin/env python3
"""
deliverables/phase_8/scripts/screen_production_momentum.py
Phase 8 Task 2: Friday EOD Production Screener & Ranker

Executes the verified institutional 5-step momentum screening algorithm on any target Friday close:
  1. Filter 1 (52-week High Retracement): Close >= 0.80 * High_252 (within 20% of 52w high).
  2. Filter 2 (Long-term Trend): Close > 200 EMA.
  3. Filter 3 (Relative Strength): Stock / NIFTY 500 ratio > 200 EMA of ratio.
  4. Ranking Metric: Volar = Return_252 / sigma_252.
  5. Market Regime Filter: NIFTY 500 Close vs 20 EMA (Normal / Risk-On vs Defensive / Risk-Off).

Outputs:
  - deliverables/phase_8/data_csv/screener_output_sample.csv (or custom destination)
  - deliverables/phase_8/raw/screen_production_momentum.log
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
DELIV_DIR = BASE_DIR / "deliverables/phase_8"
DATA_CSV_DIR = DELIV_DIR / "data_csv"
RAW_DIR = DELIV_DIR / "raw"

DEFAULT_MASTER_PARQUET = DATA_DIR / "adjusted_bhavcopy_max_2007_2026.parquet"
DEFAULT_BENCHMARK_CSV = BASE_DIR / "deliverables/phase_7/data_csv/nifty_500_benchmark_proxy.csv"
DEFAULT_OUTPUT_CSV = DATA_CSV_DIR / "screener_output_sample.csv"
LOG_FILE = RAW_DIR / "screen_production_momentum.log"


class ProductionMomentumScreener:
    """Institutional momentum screener and ranker."""

    def __init__(
        self,
        master_parquet_path: Path = DEFAULT_MASTER_PARQUET,
        benchmark_csv_path: Path = DEFAULT_BENCHMARK_CSV
    ):
        self.master_parquet_path = Path(master_parquet_path)
        self.benchmark_csv_path = Path(benchmark_csv_path)
        RAW_DIR.mkdir(parents=True, exist_ok=True)
        DATA_CSV_DIR.mkdir(parents=True, exist_ok=True)

    def log(self, msg: str, to_console: bool = True):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted = f"[{timestamp}] {msg}"
        if to_console:
            print(formatted)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(formatted + "\n")

    def load_benchmark(self) -> pd.DataFrame:
        """Loads continuous benchmark proxy series."""
        if not self.benchmark_csv_path.exists():
            raise FileNotFoundError(f"Benchmark file not found at {self.benchmark_csv_path}")
        df = pd.read_csv(self.benchmark_csv_path)
        df["date"] = df["date"].astype(str)
        return df

    def evaluate_market_regime(self, as_of_date: str) -> Dict:
        """Checks NIFTY 500 close against its 20 EMA as of target date."""
        bench_df = self.load_benchmark()
        row = bench_df[bench_df["date"] == as_of_date]

        if row.empty:
            # Fall back to latest available on or before as_of_date
            prior = bench_df[bench_df["date"] <= as_of_date]
            if prior.empty:
                raise ValueError(f"No benchmark data available on or before {as_of_date}")
            row = prior.iloc[[-1]]

        idx_date = row["date"].values[0]
        idx_close = float(row["close"].values[0])
        idx_ema_20 = float(row["ema_20"].values[0])
        idx_ema_200 = float(row["ema_200"].values[0]) if "ema_200" in row.columns else idx_close

        is_normal = (idx_close >= idx_ema_20)
        regime_label = "NORMAL / RISK-ON (Entries Active)" if is_normal else "DEFENSIVE / RISK-OFF (Entries Paused / Cash Active)"

        regime_info = {
            "date": idx_date,
            "index_close": idx_close,
            "index_ema_20": idx_ema_20,
            "index_ema_200": idx_ema_200,
            "is_normal_regime": is_normal,
            "regime_label": regime_label
        }
        return regime_info

    def run_screen(
        self,
        as_of_date: str,
        output_csv: Optional[Path] = None,
        top_n: int = 40,
        lookback_days: int = 550
    ) -> pd.DataFrame:
        """
        Executes momentum screen as of target Friday EOD date.
        Returns full dataframe of qualifying stocks sorted by Volar rank.
        """
        dest_csv = Path(output_csv) if output_csv else DEFAULT_OUTPUT_CSV
        self.log(f"==================================================================")
        self.log(f"RUNNING PRODUCTION MOMENTUM SCREENER AS OF {as_of_date}")
        self.log(f"==================================================================")

        # 1. Market Regime Evaluation
        regime = self.evaluate_market_regime(as_of_date)
        self.log(f"Market Regime: NIFTY 500 = {regime['index_close']:.2f} | 20 EMA = {regime['index_ema_20']:.2f}")
        self.log(f"Status:        {regime['regime_label']}")

        # 2. Benchmark Series for RS Ratio
        bench_df = self.load_benchmark()
        bench_map = dict(zip(bench_df["date"], bench_df["close"]))

        # 3. Load Bhavcopy Price History
        target_dt = datetime.datetime.strptime(as_of_date, "%Y-%m-%d")
        start_dt = target_dt - datetime.timedelta(days=lookback_days)
        start_str = start_dt.strftime("%Y-%m-%d")

        self.log(f"Loading bars from {start_str} to {as_of_date}...")
        bars = pd.read_parquet(
            self.master_parquet_path,
            filters=[("date", ">=", start_str), ("date", "<=", as_of_date)]
        )
        self.log(f"Loaded {len(bars):,} bars across {bars['symbol'].nunique():,} symbols.")

        # Check which symbols traded on as_of_date
        active_today = set(bars[bars["date"] == as_of_date]["symbol"].unique())
        self.log(f"Active symbols trading on {as_of_date}: {len(active_today):,}")

        # Filter bars to active symbols
        bars = bars[bars["symbol"].isin(active_today)].copy()
        bars = bars.sort_values(by=["symbol", "date"]).reset_index(drop=True)

        # 4. Indicator Computation
        self.log("Computing technical indicators (52w High, 200 EMA, Volar, RS Ratio)...")

        # Rolling 252d High
        bars["high_252"] = bars.groupby("symbol")["high"].transform(
            lambda s: s.rolling(252, min_periods=50).max()
        )

        # 200-day EMA
        bars["ema_200"] = bars.groupby("symbol")["close"].transform(
            lambda s: s.ewm(span=200, adjust=True, min_periods=50).mean()
        )

        # 252-day Return
        bars["ret_252"] = bars.groupby("symbol")["close"].transform(
            lambda s: s / s.shift(252) - 1.0
        )

        # 252-day Volatility
        bars["ret_1d"] = bars.groupby("symbol")["close"].pct_change().fillna(0.0)
        bars["vol_252"] = bars.groupby("symbol")["ret_1d"].transform(
            lambda s: s.rolling(252, min_periods=20).std() * np.sqrt(252)
        ).fillna(0.30).replace(0.0, 0.30)

        # Relative Strength Ratio vs NIFTY 500
        bars["b_close"] = bars["date"].map(bench_map).fillna(1.0)
        bars["rs_ratio"] = bars["close"] / bars["b_close"]
        bars["rs_ema_200"] = bars.groupby("symbol")["rs_ratio"].transform(
            lambda s: s.ewm(span=200, adjust=True, min_periods=50).mean()
        )
        bars["rs_pass"] = bars["rs_ratio"] > bars["rs_ema_200"]

        # 5. Extract As-Of Snapshot
        snapshot = bars[bars["date"] == as_of_date].copy()

        # Fill missing high_252 with close if newly listed
        snapshot["high_252"] = snapshot["high_252"].fillna(snapshot["close"])
        snapshot["retracement_pct"] = (snapshot["close"] / snapshot["high_252"] - 1.0) * 100.0

        # Evaluate 3 Stock Filters
        snapshot["filter1_pass"] = snapshot["close"] >= (0.80 * snapshot["high_252"])
        snapshot["filter2_pass"] = snapshot["close"] > snapshot["ema_200"]
        snapshot["filter3_pass"] = snapshot["rs_pass"].fillna(False)

        # Must have valid 252d return
        snapshot["has_return"] = snapshot["ret_252"].notnull()

        # Overall Qualification
        snapshot["is_qualified"] = (
            snapshot["filter1_pass"] &
            snapshot["filter2_pass"] &
            snapshot["filter3_pass"] &
            snapshot["has_return"]
        )

        # Volar Score = ret_252 / max(vol_252, 0.05)
        snapshot["volar_score"] = snapshot["ret_252"] / snapshot["vol_252"].clip(lower=0.05)

        # Split qualified and non-qualified
        qualified = snapshot[snapshot["is_qualified"]].copy()
        qualified = qualified.sort_values(by=["volar_score", "symbol"], ascending=[False, True]).reset_index(drop=True)
        qualified["rank"] = np.arange(1, len(qualified) + 1)

        non_qualified = snapshot[~snapshot["is_qualified"]].copy()
        non_qualified = non_qualified.sort_values(by=["volar_score", "symbol"], ascending=[False, True]).reset_index(drop=True)
        non_qualified["rank"] = np.arange(len(qualified) + 1, len(snapshot) + 1)

        full_table = pd.concat([qualified, non_qualified], ignore_index=True)

        # Clean display columns
        output_cols = [
            "rank", "symbol", "close", "high_252", "retracement_pct",
            "ema_200", "ret_252", "vol_252", "volar_score",
            "rs_ratio", "rs_ema_200", "filter1_pass", "filter2_pass", "filter3_pass", "is_qualified"
        ]
        export_df = full_table[output_cols].copy()

        # Round numeric columns for clean presentation
        export_df["close"] = export_df["close"].round(2)
        export_df["high_252"] = export_df["high_252"].round(2)
        export_df["retracement_pct"] = export_df["retracement_pct"].round(2)
        export_df["ema_200"] = export_df["ema_200"].round(2)
        export_df["ret_252"] = (export_df["ret_252"] * 100.0).round(2)
        export_df["vol_252"] = (export_df["vol_252"] * 100.0).round(2)
        export_df["volar_score"] = export_df["volar_score"].round(4)
        export_df["rs_ratio"] = export_df["rs_ratio"].round(6)
        export_df["rs_ema_200"] = export_df["rs_ema_200"].round(6)

        # Save to CSV
        export_df.to_csv(dest_csv, index=False)
        self.log(f"Exported screener results ({len(export_df)} scrips) to {dest_csv}")

        # Summary statistics
        n_active = len(snapshot)
        n_f1 = snapshot["filter1_pass"].sum()
        n_f2 = snapshot["filter2_pass"].sum()
        n_f3 = snapshot["filter3_pass"].sum()
        n_qual = len(qualified)

        self.log("------------------------------------------------------------------")
        self.log(f"SCREENING FUNNEL SUMMARY:")
        self.log(f"Active Universe Trading:      {n_active:,}")
        self.log(f"Filter 1 (Within 20% 52wH):   {n_f1:,} ({n_f1/n_active*100:.1f}%)")
        self.log(f"Filter 2 (Above 200 EMA):     {n_f2:,} ({n_f2/n_active*100:.1f}%)")
        self.log(f"Filter 3 (RS > 200 EMA):      {n_f3:,} ({n_f3/n_active*100:.1f}%)")
        self.log(f"Total Qualified Candidates:   {n_qual:,} ({n_qual/n_active*100:.1f}%)")
        self.log("------------------------------------------------------------------")

        # Display Top 20 Table
        self.log(f"TOP {min(20, n_qual)} QUALIFIED MOMENTUM STOCKS:")
        top_disp = qualified.head(20)[[
            "rank", "symbol", "close", "high_252", "retracement_pct", "ret_252", "vol_252", "volar_score"
        ]].copy()
        top_disp["ret_252"] = (top_disp["ret_252"] * 100.0).round(1).astype(str) + "%"
        top_disp["vol_252"] = (top_disp["vol_252"] * 100.0).round(1).astype(str) + "%"
        top_disp["retracement_pct"] = top_disp["retracement_pct"].round(1).astype(str) + "%"
        top_disp["close"] = "₹" + top_disp["close"].round(2).astype(str)
        top_disp["high_252"] = "₹" + top_disp["high_252"].round(2).astype(str)
        top_disp["volar_score"] = top_disp["volar_score"].round(3)

        self.log("\n" + top_disp.to_string(index=False))
        self.log("==================================================================\n")

        return export_df


def main():
    parser = argparse.ArgumentParser(description="Friday EOD Production Screener & Ranker")
    parser.add_argument("--as-of-date", type=str, default="2026-08-21", help="Target EOD date (YYYY-MM-DD)")
    parser.add_argument("--master-parquet", type=str, default=str(DEFAULT_MASTER_PARQUET), help="Path to master parquet")
    parser.add_argument("--benchmark-csv", type=str, default=str(DEFAULT_BENCHMARK_CSV), help="Path to benchmark proxy CSV")
    parser.add_argument("--output", type=str, default=str(DEFAULT_OUTPUT_CSV), help="Destination CSV path")
    parser.add_argument("--top-n", type=int, default=40, help="Top N scrips")

    args = parser.parse_args()
    screener = ProductionMomentumScreener(
        master_parquet_path=Path(args.master_parquet),
        benchmark_csv_path=Path(args.benchmark_csv)
    )
    screener.run_screen(as_of_date=args.as_of_date, output_csv=Path(args.output), top_n=args.top_n)


if __name__ == "__main__":
    main()
