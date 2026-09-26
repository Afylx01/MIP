#!/usr/bin/env python3
"""
deliverables/phase_7/scripts/test_walk_forward.py
Phase 7B Task 2: Walk-Forward Rolling Analysis (Gate 12)

Executes 14 rolling Out-of-Sample (OOS) testing windows (5-year rolling training / 1-year forward testing):
  - 2012 through 2026 forward test windows
  - Computes annual strategy return, benchmark return, and excess alpha for each test year

Outputs:
  - deliverables/phase_7/data_csv/gate12_walk_forward_matrix.csv
  - deliverables/phase_7/raw/test_walk_forward.log
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
OUT_CSV = DATA_CSV_DIR / "gate12_walk_forward_matrix.csv"
OUT_LOG = RAW_DIR / "test_walk_forward.log"

WINDOWS = [
    ("2007–2011", "2012", "2012-01-01", "2012-12-31"),
    ("2008–2012", "2013", "2013-01-01", "2013-12-31"),
    ("2009–2013", "2014", "2014-01-01", "2014-12-31"),
    ("2010–2014", "2015", "2015-01-01", "2015-12-31"),
    ("2011–2015", "2016", "2016-01-01", "2016-12-31"),
    ("2012–2016", "2017", "2017-01-01", "2017-12-31"),
    ("2013–2017", "2018", "2018-01-01", "2018-12-31"),
    ("2014–2018", "2019", "2019-01-01", "2019-12-31"),
    ("2015–2019", "2020", "2020-01-01", "2020-12-31"),
    ("2016–2020", "2021", "2021-01-01", "2021-12-31"),
    ("2017–2021", "2022", "2022-01-01", "2022-12-31"),
    ("2018–2022", "2023", "2023-01-01", "2023-12-31"),
    ("2019–2023", "2024", "2024-01-01", "2024-12-31"),
    ("2020–2024", "2025–2026", "2025-01-01", "2026-08-31")
]

def main():
    DATA_CSV_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    log_lines = []
    def log(msg=""):
        print(msg)
        log_lines.append(msg)

    log("=" * 80)
    log("PHASE 7B TASK 2: WALK-FORWARD ROLLING ANALYSIS (GATE 12)")
    log(f"Timestamp: {datetime.datetime.now(datetime.timezone.utc).isoformat()}")
    log("=" * 80)

    cal_mgr = CalendarManager(base_dir=BASE_DIR, use_bhavcopy_calendar=True)
    u_mgr = UniverseManager(base_dir=BASE_DIR)

    reader = BhavcopyReader(base_dir=BASE_DIR, custom_path=BHAVCOPY_PATH)
    idx_df = reader.load_benchmark_index()
    benchmark_lookup = idx_df.set_index("date").to_dict(orient="index")

    matrix_rows = []

    for train_lbl, test_lbl, s_dt, e_dt in WINDOWS:
        w_days = cal_mgr.get_trading_days(s_dt, e_dt)
        if not w_days:
            continue

        snaps = cal_mgr.get_monthly_rebalance_snapshots(s_dt, e_dt)
        snap_u = u_mgr.get_all_snapshot_universes(snaps)

        # Standalone price lookup for the test window to preserve speed & memory
        r_yr = BhavcopyReader(base_dir=BASE_DIR, custom_path=BHAVCOPY_PATH)
        l_yr = r_yr.get_price_lookup(s_dt, e_dt)

        res = run_simulation_instance(
            slippage_bps=10.0,
            cost_multiplier=1.0,
            window_days=w_days,
            snap_dates=snaps,
            snap_universes=snap_u,
            price_lookup=l_yr,
            benchmark_lookup=benchmark_lookup,
            record_full_deliverables=False
        )

        m = res["metrics"]
        acc = res["acc_identity"]

        b_start = benchmark_lookup[w_days[0]]["close"]
        b_end = benchmark_lookup[w_days[-1]]["close"]
        yrs = (pd.to_datetime(w_days[-1]) - pd.to_datetime(w_days[0])).days / 365.25

        # Single-year arithmetic return vs annualized CAGR
        if yrs <= 1.05:
            b_ret = ((b_end / b_start) - 1.0) * 100.0
            s_ret = m["cagr"]  # In 1-year windows, cagr is annual return
        else:
            b_ret = (((b_end / b_start) ** (1.0 / yrs)) - 1.0) * 100.0
            s_ret = m["cagr"]

        excess = s_ret - b_ret
        is_win = (excess > 0.0)

        record = {
            "train_window": train_lbl,
            "test_window": test_lbl,
            "start_date": s_dt,
            "end_date": e_dt,
            "trading_days": len(w_days),
            "snapshots": len(snaps),
            "strategy_return_pct": round(s_ret, 2),
            "benchmark_return_pct": round(b_ret, 2),
            "excess_return_pp": round(excess, 2),
            "max_drawdown_pct": round(m["max_dd"], 2),
            "sharpe_ratio": round(m["sharpe"], 2),
            "trades_count": m["total_closed_trades"],
            "win_vs_benchmark": "WIN" if is_win else "LOSS",
            "rule_r3_residual": acc["residual"]
        }
        matrix_rows.append(record)
        log(f"  Test {test_lbl:<10} | Strat: {s_ret:>+6.2f}% | Bench: {b_ret:>+6.2f}% | Excess: {excess:>+6.2f} pp | MaxDD: {m['max_dd']:>5.2f}% | {record['win_vs_benchmark']}")

    res_df = pd.DataFrame(matrix_rows)
    total_windows = len(res_df)
    win_count = (res_df["win_vs_benchmark"] == "WIN").sum()
    pct_win = (win_count / total_windows * 100.0) if total_windows > 0 else 0.0
    median_excess = res_df["excess_return_pp"].median()
    avg_excess = res_df["excess_return_pp"].mean()

    log("\n" + "=" * 80)
    log("GATE 12 COMPLIANCE EVALUATION")
    log("=" * 80)
    log(f"  Total Rolling Windows:    {total_windows}")
    log(f"  Winning OOS Windows:      {win_count} / {total_windows} ({pct_win:.1f}%) (Pass Threshold: >= 70.0%)")
    log(f"  Median Excess Return:     {median_excess:+.2f} percentage points (Pass Threshold: > +3.00 pp)")
    log(f"  Mean Excess Return:       {avg_excess:+.2f} percentage points")

    gate12_pass = (pct_win >= 70.0 and median_excess > 3.0)
    log(f"  Gate 12 Status:           {'PASS' if gate12_pass else 'FAIL'}")

    res_df.to_csv(OUT_CSV, index=False)
    log(f"\nExported Walk-Forward Results: {OUT_CSV}")

    with open(OUT_LOG, "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines) + "\n")

if __name__ == "__main__":
    main()
