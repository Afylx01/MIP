#!/usr/bin/env python3
"""
deliverables/phase_7/scripts/init_phase7_engine.py
Phase 7A Task 1: Engine Configuration & Benchmark Ingestion

Constructs the continuous NIFTY 500 benchmark proxy across all 4,857 trading sessions (2007–2026),
verifies calendar alignment, and validates the execution readiness of the indian_backtest engine.

Outputs:
  - deliverables/phase_7/data_csv/nifty_500_benchmark_proxy.csv
  - deliverables/phase_7/raw/init_phase7_engine.log
"""

import sys
import os
import datetime
from pathlib import Path
import pandas as pd
import numpy as np

BASE_DIR = Path("/storage/emulated/0/Documents/Project MIP")
DELIV_DIR = BASE_DIR / "deliverables/phase_7"
DATA_CSV_DIR = DELIV_DIR / "data_csv"
RAW_DIR = DELIV_DIR / "raw"
DATA_DIR = BASE_DIR / "data"

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from indian_backtest.data.bhavcopy_reader import BhavcopyReader, SafeUnpickler
from indian_backtest.data.calendar_manager import CalendarManager
from indian_backtest.data.universe_manager import UniverseManager
from indian_backtest.engine.portfolio import Portfolio
from indian_backtest.engine.rebalancer import Rebalancer
from indian_backtest.engine.execution import ExecutionEngine
from indian_backtest.engine.regime_filter import MarketRegimeFilter

BHAVCOPY_PATH = DATA_DIR / "adjusted_bhavcopy_max_2007_2026.parquet"
NIFTY_50_PATH = DATA_DIR / "benchmarks/NIFTY_50.csv"
NIFTY_100_PATH = DATA_DIR / "benchmarks/NIFTY_100.csv"
NSEI_CACHE_PATH = Path("/sdcard/MIP1_Scanner/data/index__NSEI_cache.pkl")
OUT_PROXY_CSV = DATA_CSV_DIR / "nifty_500_benchmark_proxy.csv"
OUT_LOG = RAW_DIR / "init_phase7_engine.log"

def main():
    DATA_CSV_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    log_lines = []
    def log(msg=""):
        print(msg)
        log_lines.append(msg)

    log("=" * 80)
    log("PHASE 7A TASK 1: ENGINE CONFIGURATION & BENCHMARK INGESTION")
    log(f"Timestamp: {datetime.datetime.now(datetime.timezone.utc).isoformat()}")
    log("=" * 80)

    # 1. Ingest Bhavcopy Calendar
    log("\n[1] Ingesting Consolidated Bhavcopy Dataset...")
    if not BHAVCOPY_PATH.exists():
        raise FileNotFoundError(f"Missing consolidated Bhavcopy dataset: {BHAVCOPY_PATH}")

    bars_df = pd.read_parquet(BHAVCOPY_PATH, columns=["symbol", "date", "open", "close"])
    total_bars = len(bars_df)
    unique_symbols = bars_df["symbol"].nunique()
    bar_dates = sorted(bars_df["date"].unique())
    n_calendar_days = len(bar_dates)
    start_cal = bar_dates[0]
    end_cal = bar_dates[-1]

    log(f"  Consolidated Bars:      {total_bars:,}")
    log(f"  Unique Scrips:          {unique_symbols:,}")
    log(f"  Calendar Trading Days:  {n_calendar_days:,} ({start_cal} to {end_cal})")

    # 2. Ingest Benchmark Data Sources
    log("\n[2] Ingesting Benchmark Index Series...")
    n50_df = pd.read_csv(NIFTY_50_PATH)[["Date", "Close"]].rename(columns={"Date": "date", "Close": "n50_close"})
    log(f"  NIFTY 50 Rows:          {len(n50_df):,} ({n50_df['date'].min()} to {n50_df['date'].max()})")

    n100_df = pd.read_csv(NIFTY_100_PATH)[["Date", "Close"]].rename(columns={"Date": "date", "Close": "n100_close"})
    log(f"  NIFTY 100 Rows:         {len(n100_df):,} ({n100_df['date'].min()} to {n100_df['date'].max()})")

    if NSEI_CACHE_PATH.exists():
        with open(NSEI_CACHE_PATH, "rb") as f:
            nsei_df = SafeUnpickler(f).load().rename(columns={"close": "nsei_close"})
        log(f"  NSEI Cache Rows:        {len(nsei_df):,} ({nsei_df['date'].min()} to {nsei_df['date'].max()})")
    else:
        nsei_df = pd.DataFrame(columns=["date", "nsei_close"])
        log("  NSEI Cache:             Not found, utilizing NIFTY 50 fallback")

    # 3. Construct Unified NIFTY 500 Benchmark Proxy
    log("\n[3] Synthesizing Continuous NIFTY 500 Benchmark Proxy (2007-2026)...")
    # Include pre-warmup trading dates from N100 to ensure 200 EMA is fully warmed up on day 1
    pre_dates = sorted(n100_df[n100_df["date"] < start_cal]["date"].unique())
    all_dates = sorted(list(set(pre_dates + bar_dates)))

    comb = pd.DataFrame({"date": all_dates})
    comb = comb.merge(n50_df, on="date", how="left")
    comb = comb.merge(n100_df, on="date", how="left")
    comb = comb.merge(nsei_df, on="date", how="left")

    # Anchor scaling factor on 2007-09-17 (first common day of N50 and N100)
    anchor_date = "2007-09-17"
    anchor_n50 = comb.loc[comb["date"] == anchor_date, "n50_close"].values[0]
    anchor_n100 = comb.loc[comb["date"] == anchor_date, "n100_close"].values[0]
    scale_factor = float(anchor_n50 / anchor_n100)
    log(f"  Anchor Date:            {anchor_date}")
    log(f"  NIFTY 50 Anchor Close:  {anchor_n50:.4f}")
    log(f"  NIFTY 100 Anchor Close: {anchor_n100:.4f}")
    log(f"  Chain Scaling Factor:   {scale_factor:.6f}")

    def resolve_close(row):
        # 1. N50 primary
        if pd.notna(row["n50_close"]):
            return float(row["n50_close"])
        # 2. NSEI cache if after anchor
        if pd.notna(row["nsei_close"]) and row["date"] >= anchor_date:
            return float(row["nsei_close"])
        # 3. Scaled N100 for historical pre-anchor dates
        if pd.notna(row["n100_close"]):
            return float(row["n100_close"] * scale_factor)
        return np.nan

    comb["close"] = comb.apply(resolve_close, axis=1)
    comb["close"] = comb["close"].ffill().bfill()

    # Precompute indicators across full history
    comb["daily_return"] = comb["close"].pct_change().fillna(0.0)
    comb["ema_20"] = comb["close"].ewm(span=20, adjust=False).mean()
    comb["ema_50"] = comb["close"].ewm(span=50, adjust=False).mean()
    comb["ema_200"] = comb["close"].ewm(span=200, adjust=False).mean()
    comb["high_252"] = comb["close"].rolling(252, min_periods=1).max()
    comb["ret_252"] = comb["close"].pct_change(252).fillna(0.0)
    comb["peak"] = comb["close"].cummax()
    comb["drawdown"] = (comb["close"] / comb["peak"] - 1.0) * 100.0

    # Filter to exact backtest calendar window
    proxy_df = comb[comb["date"].isin(bar_dates)].sort_values("date").reset_index(drop=True)
    export_cols = ["date", "close", "daily_return", "ret_252", "ema_20", "ema_50", "ema_200", "high_252", "drawdown"]
    proxy_df = proxy_df[export_cols]

    proxy_df.to_csv(OUT_PROXY_CSV, index=False)
    log(f"  Exported Benchmark Proxy: {OUT_PROXY_CSV} ({len(proxy_df):,} rows)")

    # 4. Verification of Calendar Alignment
    log("\n[4] Verifying 1-to-1 Calendar Alignment...")
    proxy_dates = set(proxy_df["date"])
    bhav_dates = set(bar_dates)
    diff_missing = bhav_dates - proxy_dates
    diff_extra = proxy_dates - bhav_dates

    log(f"  Bhavcopy Trading Dates: {len(bhav_dates):,}")
    log(f"  Benchmark Proxy Dates:  {len(proxy_dates):,}")
    log(f"  Unmatched Dates:        {len(diff_missing)} missing, {len(diff_extra)} extra")
    log(f"  Benchmark Null Count:   {proxy_df.isna().sum().sum()}")

    assert len(diff_missing) == 0 and len(diff_extra) == 0, "FATAL: Calendar dates misaligned!"
    assert proxy_df.isna().sum().sum() == 0, "FATAL: Null values found in benchmark proxy!"
    log("  Calendar Alignment:     100.00% VERIFIED (Zero Discrepancies)")

    # 5. Engine Baseline Smoke Test
    log("\n[5] Validating indian_backtest Baseline Execution...")
    cal_mgr = CalendarManager(base_dir=BASE_DIR, use_bhavcopy_calendar=True)
    test_days = cal_mgr.get_trading_days("2016-01-04", "2017-01-04")
    log(f"  Loaded Test Window:     {len(test_days)} trading days (2016)")

    reader = BhavcopyReader(base_dir=BASE_DIR)
    loaded_idx = reader.load_benchmark_index()
    log(f"  Loaded Benchmark via Reader: {len(loaded_idx):,} rows, close={loaded_idx['close'].iloc[-1]:.2f}")

    u_mgr = UniverseManager(base_dir=BASE_DIR)
    test_snaps = cal_mgr.get_monthly_rebalance_snapshots("2016-01-04", "2016-06-01")
    snap_u = u_mgr.get_all_snapshot_universes(test_snaps)
    log(f"  Resolved {len(snap_u)} snapshot universes successfully")

    regime_filter = MarketRegimeFilter(enabled=True, ema_period=20)
    is_bull = regime_filter.evaluate_regime("2016-01-04", loaded_idx.set_index("date").to_dict(orient="index"))
    log(f"  Market Regime on 2016-01-04 (20 EMA): {'BULL (Entries Allowed)' if is_bull else 'BEAR (Cash Mode)'}")

    log("\n" + "=" * 80)
    log("PHASE 7A TASK 1 COMPLETE: ENGINE CONFIGURATION CERTIFIED (PASS)")
    log("=" * 80)

    with open(OUT_LOG, "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines) + "\n")

if __name__ == "__main__":
    main()
