#!/usr/bin/env python3
"""
production/sector_rotation.py
Production Sector Rotation Engine for Project MIP.

Computes comprehensive Sector Rotation analytics across the 12 primary NSE sectors:
  1. Sector Performance (Equal-weighted 1M [21d], 3M [63d], 1Y [252d] returns).
  2. Relative Strength Alpha vs NIFTY 500 (Alpha_1M and Alpha_3M).
  3. Sector Internal Breadth (% > 200 EMA and % within 20% of 52w High).
  4. Sector RRG Quadrant (Mean RS-Ratio and RS-Momentum -> LEADING, IMPROVING, WEAKENING, LAGGING).
  5. Top 20 Momentum Candidate Density (count and percentage share).
  6. Composite Sector Rank Score:
       Score = 0.5 * Alpha_1M + 0.5 * Alpha_3M + 0.2 * (Sector_Breadth_200 - 50.0)

Exports snapshot to deliverables/phase_8/data_csv/sector_rotation_live.json
and mirrors to /sdcard/Documents/deliverables/sector_rotation_live.json
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

BASE_DIR = Path("/storage/emulated/0/Documents/Project MIP")
DATA_DIR = BASE_DIR / "data"
UNIVERSE_PARQUET = DATA_DIR / "universe/nifty500_pit_universe.parquet"
BENCHMARK_CSV = BASE_DIR / "deliverables/phase_7/data_csv/nifty_500_benchmark_proxy.csv"
DEFAULT_OUTPUT_JSON = BASE_DIR / "deliverables/phase_8/data_csv/sector_rotation_live.json"
MIRROR_OUTPUT_JSON = Path("/sdcard/Documents/deliverables/sector_rotation_live.json")

PROD_DIR = BASE_DIR / "production"
if str(PROD_DIR) not in sys.path:
    sys.path.insert(0, str(PROD_DIR))

from sector_map import PRIMARY_SECTORS, SECTOR_NAMES, get_sector, get_sector_map
from plugins.rrg_filter import RRGFilterPlugin


class SectorRotationEngine:
    """Quantitative Sector Rotation and Relative Strength Engine."""

    def __init__(
        self,
        universe_parquet: Path = UNIVERSE_PARQUET,
        benchmark_csv: Path = BENCHMARK_CSV,
    ):
        self.universe_parquet = Path(universe_parquet)
        self.benchmark_csv = Path(benchmark_csv)
        self.sector_map = get_sector_map()

    def log(self, msg: str):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [SectorEngine] {msg}")

    def load_benchmark(self) -> pd.DataFrame:
        """Loads continuous benchmark proxy."""
        if not self.benchmark_csv.exists():
            raise FileNotFoundError(f"Benchmark CSV not found at {self.benchmark_csv}")
        df = pd.read_csv(self.benchmark_csv)
        df["date"] = df["date"].astype(str)
        return df

    def get_benchmark_returns(self, as_of_date: str) -> Dict[str, float]:
        """Calculates benchmark 21-day, 63-day, and 252-day returns."""
        b_df = self.load_benchmark()
        row = b_df[b_df["date"] == as_of_date]
        if row.empty:
            prior = b_df[b_df["date"] <= as_of_date]
            if prior.empty:
                raise ValueError(f"No benchmark data on or before {as_of_date}")
            target_idx = prior.index[-1]
        else:
            target_idx = row.index[0]

        c_now = float(b_df.loc[target_idx, "close"])

        # 21 bars prior
        idx_21 = max(0, target_idx - 21)
        c_21 = float(b_df.loc[idx_21, "close"])
        ret_21 = (c_now / c_21 - 1.0) if c_21 > 0 else 0.0

        # 63 bars prior
        idx_63 = max(0, target_idx - 63)
        c_63 = float(b_df.loc[idx_63, "close"])
        ret_63 = (c_now / c_63 - 1.0) if c_63 > 0 else 0.0

        # 252 bars prior
        idx_252 = max(0, target_idx - 252)
        c_252 = float(b_df.loc[idx_252, "close"])
        ret_252 = (c_now / c_252 - 1.0) if c_252 > 0 else 0.0

        return {
            "date": b_df.loc[target_idx, "date"],
            "close": c_now,
            "ret_1m": ret_21 * 100.0,
            "ret_3m": ret_63 * 100.0,
            "ret_1y": ret_252 * 100.0,
        }

    def compute_rotation(
        self,
        as_of_date: str,
        snapshot_df: Optional[pd.DataFrame] = None,
        top20_symbols: Optional[List[str]] = None,
        lookback_days: int = 550,
    ) -> Dict:
        """
        Computes all sector rotation metrics for the 12 primary sectors.
        If snapshot_df is provided with pre-calculated returns and indicators, uses it.
        Otherwise loads universe bars and calculates indicators.
        """
        self.log(f"Computing Sector Rotation as of {as_of_date}...")

        # Benchmark returns
        bench = self.get_benchmark_returns(as_of_date)
        b_ret_1m = bench["ret_1m"]
        b_ret_3m = bench["ret_3m"]
        b_ret_1y = bench["ret_1y"]

        # Check if snapshot_df has all required fields
        req_cols = {"close", "ema_200", "high_252", "ret_21", "ret_63", "ret_252", "rrg_rs_ratio", "rrg_rs_momentum"}
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

            self.log("Calculating indicators and period returns (21d, 63d, 252d)...")
            bars["ema_200"] = bars.groupby("symbol")["close"].transform(
                lambda s: s.ewm(span=200, adjust=True, min_periods=50).mean()
            )
            bars["high_252"] = bars.groupby("symbol")["high"].transform(
                lambda s: s.rolling(252, min_periods=50).max()
            )
            bars["ret_21"] = bars.groupby("symbol")["close"].transform(
                lambda s: s / s.shift(21) - 1.0
            )
            bars["ret_63"] = bars.groupby("symbol")["close"].transform(
                lambda s: s / s.shift(63) - 1.0
            )
            bars["ret_252"] = bars.groupby("symbol")["close"].transform(
                lambda s: s / s.shift(252) - 1.0
            )

            # RRG Indicators
            b_df = self.load_benchmark()
            bench_map = dict(zip(b_df["date"], b_df["close"]))
            bars["benchmark_close"] = bars["date"].map(bench_map).fillna(1.0)
            rrg_plugin = RRGFilterPlugin(enabled=False)
            bars = rrg_plugin.evaluate(bars, as_of_date=as_of_date)

            snap = bars[bars["date"] == as_of_date].copy()

        # Ensure sector column exists
        if "sector" not in snap.columns:
            snap["sector"] = snap["symbol"].map(lambda sym: self.sector_map.get(str(sym).upper().strip(), get_sector(str(sym))))

        # Fill missing extremes
        snap["high_252"] = snap["high_252"].fillna(snap["close"])
        snap["ema_200"] = snap["ema_200"].fillna(snap["close"])

        # Determine top 20 candidate set
        top20_set = set(top20_symbols) if top20_symbols is not None else set()

        # Compute metrics per sector
        sector_results = []
        for sec in PRIMARY_SECTORS:
            sec_df = snap[snap["sector"] == sec]
            n_sec = len(sec_df)

            if n_sec == 0:
                continue

            # Performance
            ret_1m = float(sec_df["ret_21"].dropna().mean() * 100.0) if not sec_df["ret_21"].dropna().empty else 0.0
            ret_3m = float(sec_df["ret_63"].dropna().mean() * 100.0) if not sec_df["ret_63"].dropna().empty else 0.0
            ret_1y = float(sec_df["ret_252"].dropna().mean() * 100.0) if not sec_df["ret_252"].dropna().empty else 0.0

            # Alpha vs NIFTY 500
            alpha_1m = ret_1m - b_ret_1m
            alpha_3m = ret_3m - b_ret_3m

            # Breadth
            breadth_200 = float((sec_df["close"] > sec_df["ema_200"]).mean() * 100.0)
            breadth_52w = float((sec_df["close"] >= 0.80 * sec_df["high_252"]).mean() * 100.0)

            # RRG Quadrant
            rrg_ratio = float(sec_df["rrg_rs_ratio"].dropna().mean()) if "rrg_rs_ratio" in sec_df.columns and not sec_df["rrg_rs_ratio"].dropna().empty else 100.0
            rrg_mom = float(sec_df["rrg_rs_momentum"].dropna().mean()) if "rrg_rs_momentum" in sec_df.columns and not sec_df["rrg_rs_momentum"].dropna().empty else 100.0

            if rrg_ratio >= 100.0 and rrg_mom >= 100.0:
                rrg_quad = "LEADING"
            elif rrg_ratio >= 100.0 and rrg_mom < 100.0:
                rrg_quad = "WEAKENING"
            elif rrg_ratio < 100.0 and rrg_mom < 100.0:
                rrg_quad = "LAGGING"
            else:
                rrg_quad = "IMPROVING"

            # Top 20 Candidates in this sector
            cands = [s for s in sec_df["symbol"].tolist() if s in top20_set]
            cand_cnt = len(cands)
            cand_share = round((cand_cnt / 20.0) * 100.0, 1)

            # Composite Score: 0.5*Alpha_1M + 0.5*Alpha_3M + 0.2*(Sector_Breadth_200 - 50.0)
            score = 0.5 * alpha_1m + 0.5 * alpha_3m + 0.2 * (breadth_200 - 50.0)

            sector_results.append({
                "sector": sec,
                "name": SECTOR_NAMES.get(sec, sec),
                "symbol_count": n_sec,
                "ret_1m": round(ret_1m, 2),
                "ret_3m": round(ret_3m, 2),
                "ret_1y": round(ret_1y, 2),
                "alpha_1m": round(alpha_1m, 2),
                "alpha_3m": round(alpha_3m, 2),
                "breadth_200": round(breadth_200, 1),
                "breadth_52w": round(breadth_52w, 1),
                "rrg_rs_ratio": round(rrg_ratio, 2),
                "rrg_rs_momentum": round(rrg_mom, 2),
                "rrg_quadrant": rrg_quad,
                "candidate_count": cand_cnt,
                "candidate_share": cand_share,
                "candidates": cands,
                "composite_score": round(score, 2),
            })

        # Rank sectors descending by composite_score
        sector_results.sort(key=lambda x: x["composite_score"], reverse=True)
        for rank_idx, s in enumerate(sector_results, start=1):
            s["rank"] = rank_idx

        # Inflowing (Top 3) and Lagging (Bottom 3)
        top_inflowing = [s["sector"] for s in sector_results[:3]]
        lagging = [s["sector"] for s in sector_results[-3:]]

        rotation_data = {
            "as_of_date": as_of_date,
            "universe_size": len(snap),
            "benchmark": {
                "name": "NIFTY 500",
                "close": round(bench["close"], 2),
                "ret_1m": round(bench["ret_1m"], 2),
                "ret_3m": round(bench["ret_3m"], 2),
                "ret_1y": round(bench["ret_1y"], 2),
            },
            "top_inflowing_sectors": top_inflowing,
            "top_lagging_sectors": lagging,
            "sectors": {s["sector"]: s for s in sector_results},
            "ranked_sectors": sector_results,
            "timestamp": datetime.datetime.now().isoformat(),
        }

        return rotation_data

    def export_json(
        self,
        rotation_data: Dict,
        output_path: Optional[Path] = None,
    ) -> Path:
        """Exports sector rotation dictionary to JSON and mirrors to shared deliverables."""
        dest_json = Path(output_path) if output_path else DEFAULT_OUTPUT_JSON
        dest_json.parent.mkdir(parents=True, exist_ok=True)

        with open(dest_json, "w", encoding="utf-8") as f:
            json.dump(rotation_data, f, indent=2)
        self.log(f"Exported live sector rotation snapshot to {dest_json}")

        try:
            MIRROR_OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(dest_json, MIRROR_OUTPUT_JSON)
            self.log(f"Mirrored sector rotation snapshot to {MIRROR_OUTPUT_JSON}")
        except Exception as e:
            self.log(f"Note: Could not mirror to {MIRROR_OUTPUT_JSON}: {e}")

        return dest_json

    def print_summary(self, rotation_data: Dict):
        """Prints formatted sector rotation tearsheet to console."""
        r = rotation_data
        b = r["benchmark"]
        print("\n" + "=" * 78)
        print(f"SECTOR ROTATION & RELATIVE STRENGTH TEARSHEET — AS OF {r['as_of_date']}")
        print("=" * 78)
        print(f"Benchmark: NIFTY 500 (Close: ₹{b['close']:,.2f} | 1M: {b['ret_1m']:+.2f}% | 3M: {b['ret_3m']:+.2f}%)")
        print(f"Top 3 Inflowing Leadership: {', '.join(r['top_inflowing_sectors'])}")
        print(f"Lagging Sectors:            {', '.join(r['top_lagging_sectors'])}")
        print("-" * 78)
        print(f"{'#':<3}{'SECTOR':<13}{'1M-RET':<9}{'1M-ALPHA':<10}{'3M-ALPHA':<10}{'BREADTH':<9}{'RRG':<6}{'SCORE':<8}{'PICKS'}")
        print("-" * 78)
        quad_code = {"LEADING": "LEAD", "IMPROVING": "IMPR", "WEAKENING": "WEAK", "LAGGING": "LAGG"}
        for s in r["ranked_sectors"]:
            rk = s["rank"]
            sec = s["sector"]
            r1m = f"{s['ret_1m']:+.1f}%"
            a1m = f"{s['alpha_1m']:+.1f}%"
            a3m = f"{s['alpha_3m']:+.1f}%"
            br200 = f"{s['breadth_200']:.1f}%"
            rrg = quad_code.get(s["rrg_quadrant"], s["rrg_quadrant"][:4])
            score = f"{s['composite_score']:+.2f}"
            picks = f"{s['candidate_count']} ({s['candidate_share']:.0f}%)" if s['candidate_count'] > 0 else "-"
            print(f"{rk:<3}{sec:<13}{r1m:<9}{a1m:<10}{a3m:<10}{br200:<9}{rrg:<6}{score:<8}{picks}")
        print("=" * 78 + "\n")


def main():
    parser = argparse.ArgumentParser(description="MIP Sector Rotation Engine")
    parser.add_argument("--as-of-date", type=str, default="2026-08-28", help="Target EOD date (YYYY-MM-DD)")
    parser.add_argument("--output", type=str, default=str(DEFAULT_OUTPUT_JSON), help="Output JSON path")

    args = parser.parse_args()
    engine = SectorRotationEngine()
    data = engine.compute_rotation(as_of_date=args.as_of_date)
    engine.export_json(data, output_path=Path(args.output))
    engine.print_summary(data)


if __name__ == "__main__":
    main()
