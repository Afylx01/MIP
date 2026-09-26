#!/usr/bin/env python3
"""
deliverables/phase_7/scripts/test_is_oos_split.py
Phase 7B Task 1: In-Sample (IS) vs Out-of-Sample (OOS) Split Analysis (Gate 11)

Partitions the 20-year consolidated Bhavcopy history into:
  1. In-Sample (IS): 2007-01-02 to 2015-12-31 (9.0 years, covering 2008 GFC & 2011-2013 consolidation)
  2. Out-of-Sample (OOS): 2016-01-04 to 2026-08-31 (10.66 years, modern expansion era)

Outputs:
  - deliverables/phase_7/data_csv/gate11_is_oos_results.csv
  - deliverables/phase_7/raw/test_is_oos_split.log
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

from indian_backtest.data.bhavcopy_reader import BhavcopyReader
from indian_backtest.data.calendar_manager import CalendarManager
from indian_backtest.data.universe_manager import UniverseManager
from deliverables.phase_7.scripts.test_cost_sensitivity import run_simulation_instance

BHAVCOPY_PATH = DATA_DIR / "adjusted_bhavcopy_max_2007_2026.parquet"
OUT_CSV = DATA_CSV_DIR / "gate11_is_oos_results.csv"
OUT_LOG = RAW_DIR / "test_is_oos_split.log"

IS_START = "2007-01-02"
IS_END = "2015-12-31"
OOS_START = "2016-01-04"
OOS_END = "2026-08-31"

def evaluate_subperiod(start_dt: str, end_dt: str, period_name: str, cal_mgr, u_mgr, benchmark_lookup, log):
    log(f"\n--- Evaluating {period_name} ({start_dt} to {end_dt}) ---")
    reader = BhavcopyReader(base_dir=BASE_DIR, custom_path=BHAVCOPY_PATH)
    lookup = reader.get_price_lookup(start_dt, end_dt)
    
    window_days = cal_mgr.get_trading_days(start_dt, end_dt)
    snap_dates = cal_mgr.get_monthly_rebalance_snapshots(start_dt, end_dt)
    snap_universes = u_mgr.get_all_snapshot_universes(snap_dates)

    log(f"  Trading Days:       {len(window_days):,}")
    log(f"  Monthly Snapshots:  {len(snap_dates):,}")

    res = run_simulation_instance(
        slippage_bps=10.0,
        cost_multiplier=1.0,
        window_days=window_days,
        snap_dates=snap_dates,
        snap_universes=snap_universes,
        price_lookup=lookup,
        benchmark_lookup=benchmark_lookup,
        record_full_deliverables=False
    )

    m = res["metrics"]
    acc = res["acc_identity"]

    b_start = benchmark_lookup[window_days[0]]["close"]
    b_end = benchmark_lookup[window_days[-1]]["close"]
    yrs = (pd.to_datetime(window_days[-1]) - pd.to_datetime(window_days[0])).days / 365.25
    b_cagr = ((b_end / b_start) ** (1.0 / yrs) - 1.0) * 100.0 if yrs > 0 else 0.0
    excess_cagr = m["cagr"] - b_cagr

    log(f"  Strategy CAGR:      {m['cagr']:.2f}%")
    log(f"  Benchmark CAGR:     {b_cagr:.2f}%")
    log(f"  Excess CAGR:        {excess_cagr:+.2f} percentage points")
    log(f"  Max Drawdown:       {m['max_dd']:.2f}%")
    log(f"  Sharpe Ratio:       {m['sharpe']:.2f}")
    log(f"  Sortino Ratio:      {m['sortino']:.2f}")
    log(f"  Calmar Ratio:       {m['calmar']:.2f}")
    log(f"  Win Rate (%):       {m['win_rate_pct']:.2f}%")
    log(f"  Profit Factor:      {m['profit_factor']:.2f}")
    log(f"  Closed Trades:      {m['total_closed_trades']}")
    log(f"  Rule R-3 Residual:  {acc['residual']:.10f}")

    return {
        "period": period_name,
        "start_date": start_dt,
        "end_date": end_dt,
        "duration_years": round(yrs, 2),
        "trading_days": len(window_days),
        "snapshots": len(snap_dates),
        "strategy_cagr": round(m["cagr"], 2),
        "benchmark_cagr": round(b_cagr, 2),
        "excess_cagr": round(excess_cagr, 2),
        "max_drawdown": round(m["max_dd"], 2),
        "sharpe_ratio": round(m["sharpe"], 2),
        "sortino_ratio": round(m["sortino"], 2),
        "calmar_ratio": round(m["calmar"], 2),
        "win_rate_pct": round(m["win_rate_pct"], 2),
        "profit_factor": round(m["profit_factor"], 2),
        "total_trades": m["total_closed_trades"],
        "residual": acc["residual"]
    }

def main():
    DATA_CSV_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    log_lines = []
    def log(msg=""):
        print(msg)
        log_lines.append(msg)

    log("=" * 80)
    log("PHASE 7B TASK 1: IN-SAMPLE VS OUT-OF-SAMPLE SPLIT ANALYSIS (GATE 11)")
    log(f"Timestamp: {datetime.datetime.now(datetime.timezone.utc).isoformat()}")
    log("=" * 80)

    cal_mgr = CalendarManager(base_dir=BASE_DIR, use_bhavcopy_calendar=True)
    u_mgr = UniverseManager(base_dir=BASE_DIR)

    reader = BhavcopyReader(base_dir=BASE_DIR, custom_path=BHAVCOPY_PATH)
    idx_df = reader.load_benchmark_index()
    benchmark_lookup = idx_df.set_index("date").to_dict(orient="index")

    # 1. In-Sample
    res_is = evaluate_subperiod(IS_START, IS_END, "In-Sample (IS)", cal_mgr, u_mgr, benchmark_lookup, log)

    # 2. Out-of-Sample
    res_oos = evaluate_subperiod(OOS_START, OOS_END, "Out-of-Sample (OOS)", cal_mgr, u_mgr, benchmark_lookup, log)

    # 3. Audit Gate 11 Pass Criteria
    log("\n" + "=" * 80)
    log("GATE 11 COMPLIANCE EVALUATION")
    log("=" * 80)
    oos_excess = res_oos["excess_cagr"]
    oos_sharpe = res_oos["sharpe_ratio"]

    # Pass Criteria: OOS CAGR > Benchmark + 3.0 pp AND OOS Sharpe > 0.80
    gate11_pass = (oos_excess >= 3.0 and oos_sharpe >= 0.80)
    log(f"  OOS Excess Return:  {oos_excess:+.2f} pp (Threshold: >= +3.00 pp) -> {'PASS' if oos_excess >= 3.0 else 'FAIL'}")
    log(f"  OOS Sharpe Ratio:   {oos_sharpe:.2f} (Threshold: >= 0.80) -> {'PASS' if oos_sharpe >= 0.80 else 'FAIL'}")
    log(f"  Gate 11 Status:     {'PASS' if gate11_pass else 'FAIL'}")

    res_df = pd.DataFrame([res_is, res_oos])
    res_df.to_csv(OUT_CSV, index=False)
    log(f"\nExported In-Sample vs Out-of-Sample Results: {OUT_CSV}")

    with open(OUT_LOG, "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines) + "\n")

if __name__ == "__main__":
    main()
