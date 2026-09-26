#!/usr/bin/env python3
"""
deliverables/phase_7/scripts/test_rebalance_date_sensitivity.py
Phase 7B Task 4: Rebalance-Date & Calendar Day Sensitivity (Gate 15)

Evaluates 5 distinct monthly trading days for rebalancing across 2016-2026:
  1. 1st Trading Day of Month (Baseline)
  2. 5th Trading Day of Month
  3. 10th Trading Day of Month
  4. 15th Trading Day of Month
  5. Last Trading Day of Month

Pass Criteria:
  - Average excess CAGR across all 5 dates > 3.0 percentage points
  - Standard deviation of excess returns across dates < 4.0 percentage points

Outputs:
  - deliverables/phase_7/data_csv/gate15_rebalance_date_sensitivity.csv
  - deliverables/phase_7/raw/test_rebalance_date_sensitivity.log
"""

import sys
import os
import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple
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
START_DATE = "2016-01-04"
END_DATE = "2026-08-31"

OUT_CSV = DATA_CSV_DIR / "gate15_rebalance_date_sensitivity.csv"
OUT_LOG = RAW_DIR / "test_rebalance_date_sensitivity.log"

SCHEDULES = [
    ("1st Trading Day (Baseline)", "1st"),
    ("5th Trading Day", "5th"),
    ("10th Trading Day", "10th"),
    ("15th Trading Day", "15th"),
    ("Last Trading Day", "last"),
]

def get_monthly_snapshots(window_days: List[str], rule: str) -> List[str]:
    months: Dict[str, List[str]] = {}
    for d in window_days:
        ym = d[:7]
        if ym not in months:
            months[ym] = []
        months[ym].append(d)

    snaps = []
    for ym, days in sorted(months.items()):
        if rule == "1st":
            snaps.append(days[0])
        elif rule == "5th":
            idx = min(4, len(days) - 1)
            snaps.append(days[idx])
        elif rule == "10th":
            idx = min(9, len(days) - 1)
            snaps.append(days[idx])
        elif rule == "15th":
            idx = min(14, len(days) - 1)
            snaps.append(days[idx])
        elif rule == "last":
            snaps.append(days[-1])
    return snaps

def main():
    DATA_CSV_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    log_lines = []
    def log(msg=""):
        print(msg)
        log_lines.append(msg)

    log("=" * 80)
    log("PHASE 7B TASK 4: REBALANCE-DATE SENSITIVITY EVALUATION (GATE 15)")
    log(f"Timestamp: {datetime.datetime.now(datetime.timezone.utc).isoformat()}")
    log("=" * 80)

    cal_mgr = CalendarManager(base_dir=BASE_DIR, use_bhavcopy_calendar=True)
    u_mgr = UniverseManager(base_dir=BASE_DIR)
    window_days = cal_mgr.get_trading_days(START_DATE, END_DATE)

    log(f"Loading Bhavcopy and benchmark data across {START_DATE} to {END_DATE}...")
    reader = BhavcopyReader(base_dir=BASE_DIR, custom_path=BHAVCOPY_PATH)
    price_lookup = reader.get_price_lookup(START_DATE, END_DATE)
    idx_df = reader.load_benchmark_index()
    benchmark_lookup = idx_df.set_index("date").to_dict(orient="index")

    b_start = benchmark_lookup[window_days[0]]["close"]
    b_end = benchmark_lookup[window_days[-1]]["close"]
    yrs = (pd.to_datetime(window_days[-1]) - pd.to_datetime(window_days[0])).days / 365.25
    b_cagr = (((b_end / b_start) ** (1.0 / yrs)) - 1.0) * 100.0

    log(f"Benchmark Period: {window_days[0]} to {window_days[-1]} ({len(window_days)} trading days)")
    log(f"Benchmark CAGR:   {b_cagr:.2f}%")
    log("-" * 80)

    rows = []
    for label, rule in SCHEDULES:
        snaps = get_monthly_snapshots(window_days, rule)
        snap_universes = u_mgr.get_all_snapshot_universes(snaps)

        res = run_simulation_instance(
            slippage_bps=10.0,
            cost_multiplier=1.0,
            window_days=window_days,
            snap_dates=snaps,
            snap_universes=snap_universes,
            price_lookup=price_lookup,
            benchmark_lookup=benchmark_lookup,
            record_full_deliverables=False
        )

        m = res["metrics"]
        acc = res["acc_identity"]
        s_cagr = m["cagr"]
        excess = s_cagr - b_cagr

        record = {
            "schedule_label": label,
            "rebalance_rule": rule,
            "total_snapshots": len(snaps),
            "strategy_cagr_pct": round(s_cagr, 2),
            "benchmark_cagr_pct": round(b_cagr, 2),
            "excess_cagr_pp": round(excess, 2),
            "max_drawdown_pct": round(m["max_dd"], 2),
            "sharpe_ratio": round(m["sharpe"], 2),
            "trades_count": m["total_closed_trades"],
            "rule_r3_residual": acc["residual"]
        }
        rows.append(record)
        log(f"  {label:<28} | Strat: {s_cagr:>5.2f}% | Bench: {b_cagr:>5.2f}% | Excess: {excess:>+5.2f} pp | MaxDD: {m['max_dd']:>5.2f}% | Sharpe: {m['sharpe']:.2f}")

    res_df = pd.DataFrame(rows)
    avg_excess = res_df["excess_cagr_pp"].mean()
    std_excess = res_df["excess_cagr_pp"].std()
    min_excess = res_df["excess_cagr_pp"].min()
    max_excess = res_df["excess_cagr_pp"].max()

    log("\n" + "=" * 80)
    log("GATE 15 COMPLIANCE EVALUATION")
    log("=" * 80)
    log(f"  Schedules Evaluated:          {len(res_df)}")
    log(f"  Average Excess CAGR:          {avg_excess:+.2f} pp (Pass Threshold: > +3.00 pp)")
    log(f"  Std Dev of Excess Returns:    {std_excess:.2f} pp (Pass Threshold: < 4.00 pp)")
    log(f"  Excess Return Range:          {min_excess:+.2f} pp to {max_excess:+.2f} pp")

    gate15_pass = (avg_excess > 3.0 and std_excess < 4.0)
    log(f"  Gate 15 Status:               {'PASS' if gate15_pass else 'FAIL'}")

    res_df.to_csv(OUT_CSV, index=False)
    log(f"\nExported Rebalance-Date Sensitivity Results: {OUT_CSV}")

    with open(OUT_LOG, "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines) + "\n")

if __name__ == "__main__":
    main()
