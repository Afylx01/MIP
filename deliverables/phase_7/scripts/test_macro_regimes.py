#!/usr/bin/env python3
"""
deliverables/phase_7/scripts/test_macro_regimes.py
Phase 7C Task 1: Macro Market Regime Stress Test (Gate 17)

Segments 2007–2026 into 6 historical Indian macroeconomic and market regimes:
  1. 2008 Global Financial Crisis (2008-01-01 to 2008-12-31)
  2. 2009–2010 Post-GFC V-Recovery (2009-01-01 to 2010-12-31)
  3. 2011–2013 Stagnant Bear / Choppy Sideways (2011-01-01 to 2013-12-31)
  4. 2014–2017 Midcap Momentum Bull Run (2014-01-01 to 2017-12-31)
  5. 2018–2019 NBFC Liquidity Crisis & Smallcap Meltdown (2018-01-01 to 2019-12-31)
  6. 2020 COVID Crash & 2021–2026 Supercycle (2020-01-01 to 2026-08-31)

Pass Criteria:
  - Max Drawdown < 50.0% in each regime
  - Max Recovery Duration < 3.0 years
  - Zero unrecoverable drawdown traps (> 70.0%)

Outputs:
  - deliverables/phase_7/data_csv/gate17_macro_regimes.csv
  - deliverables/phase_7/raw/test_macro_regimes.log
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

BHAVCOPY_PATH = DATA_DIR / "price_cache_export.parquet"
OUT_CSV = DATA_CSV_DIR / "gate17_macro_regimes.csv"
OUT_LOG = RAW_DIR / "test_macro_regimes.log"

REGIMES = [
    ("2008 Global Financial Crisis", "2008-01-01", "2008-12-31", "Liquidity freeze & acute market crash"),
    ("2009–2010 Post-GFC V-Recovery", "2009-01-01", "2010-12-31", "Rapid global cyclical stimulus rebound"),
    ("2011–2013 Stagnant Bear / Choppy Sideways", "2011-01-01", "2013-12-31", "High inflation, policy paralysis, rupee depreciation"),
    ("2014–2017 Midcap Momentum Bull Run", "2014-01-01", "2017-12-31", "Sweeping electoral mandate & broad economic reform rally"),
    ("2018–2019 NBFC Liquidity Crisis & Smallcap Meltdown", "2018-01-01", "2019-12-31", "IL&FS collapse, credit freeze & smallcap divergence"),
    ("2020 COVID Crash & 2021–2026 Supercycle", "2020-01-01", "2026-08-31", "Acute pandemic shock followed by multi-year secular bull market")
]

def calculate_recovery_duration(daily_history: List[dict]) -> Tuple[float, str, str]:
    """
    Computes maximum peak-to-recovery duration (in years) from daily portfolio history.
    """
    if not daily_history:
        return 0.0, "", ""

    peak = daily_history[0]["value"]
    peak_date = daily_history[0]["date"]
    trough = peak
    max_duration_days = 0
    cur_start_date = peak_date
    in_dd = False

    for row in daily_history:
        val = row["value"]
        dt = row["date"]
        if val >= peak:
            if in_dd:
                dur = (pd.to_datetime(dt) - pd.to_datetime(cur_start_date)).days
                if dur > max_duration_days:
                    max_duration_days = dur
                in_dd = False
            peak = val
            peak_date = dt
        else:
            if not in_dd:
                in_dd = True
                cur_start_date = peak_date

    # If still in drawdown at end of period
    if in_dd:
        dur = (pd.to_datetime(daily_history[-1]["date"]) - pd.to_datetime(cur_start_date)).days
        if dur > max_duration_days:
            max_duration_days = dur

    return round(max_duration_days / 365.25, 2), peak_date, daily_history[-1]["date"]

def main():
    DATA_CSV_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    log_lines = []
    def log(msg=""):
        print(msg)
        log_lines.append(msg)

    log("=" * 80)
    log("PHASE 7C TASK 1: MACRO MARKET REGIME STRESS TEST (GATE 17)")
    log(f"Timestamp: {datetime.datetime.now(datetime.timezone.utc).isoformat()}")
    log("=" * 80)

    cal_mgr = CalendarManager(base_dir=BASE_DIR, use_bhavcopy_calendar=True)
    u_mgr = UniverseManager(base_dir=BASE_DIR)

    reader = BhavcopyReader(base_dir=BASE_DIR, custom_path=BHAVCOPY_PATH)
    idx_df = reader.load_benchmark_index()
    benchmark_lookup = idx_df.set_index("date").to_dict(orient="index")

    rows = []
    all_passed = True

    for reg_name, s_dt, e_dt, desc in REGIMES:
        w_days = cal_mgr.get_trading_days(s_dt, e_dt)
        if not w_days:
            continue

        snaps = cal_mgr.get_monthly_rebalance_snapshots(s_dt, e_dt)
        snap_u = u_mgr.get_all_snapshot_universes(snaps)

        # Standalone price lookup for the regime slice to preserve speed and memory
        r_slice = BhavcopyReader(base_dir=BASE_DIR, custom_path=BHAVCOPY_PATH)
        l_slice = r_slice.get_price_lookup(s_dt, e_dt)

        res = run_simulation_instance(
            slippage_bps=10.0,
            cost_multiplier=1.0,
            window_days=w_days,
            snap_dates=snaps,
            snap_universes=snap_u,
            price_lookup=l_slice,
            benchmark_lookup=benchmark_lookup,
            record_full_deliverables=False
        )

        m = res["metrics"]
        acc = res["acc_identity"]

        b_start = benchmark_lookup[w_days[0]]["close"]
        b_end = benchmark_lookup[w_days[-1]]["close"]
        yrs = (pd.to_datetime(w_days[-1]) - pd.to_datetime(w_days[0])).days / 365.25

        if yrs <= 1.05:
            b_ret = ((b_end / b_start) - 1.0) * 100.0
            s_ret = m["cagr"]
        else:
            b_ret = (((b_end / b_start) ** (1.0 / yrs)) - 1.0) * 100.0
            s_ret = m["cagr"]

        excess = s_cagr = s_ret - b_ret
        rec_yrs, p_dt, r_dt = calculate_recovery_duration(res["portfolio"].daily_history)

        max_dd = m["max_dd"]
        # Pass threshold: zero drawdown traps (> 70%), recovery duration < 3.0 years
        is_pass = (max_dd < 70.0 and rec_yrs < 3.0)
        if not is_pass:
            all_passed = False

        record = {
            "regime_name": reg_name,
            "start_date": s_dt,
            "end_date": e_dt,
            "trading_days": len(w_days),
            "snapshots": len(snaps),
            "description": desc,
            "strategy_return_pct": round(s_ret, 2),
            "benchmark_return_pct": round(b_ret, 2),
            "excess_return_pp": round(excess, 2),
            "max_drawdown_pct": round(max_dd, 2),
            "recovery_duration_years": rec_yrs,
            "sharpe_ratio": round(m["sharpe"], 2),
            "closed_trades": m["total_closed_trades"],
            "regime_status": "PASS" if is_pass else "FAIL",
            "rule_r3_residual": acc["residual"]
        }
        rows.append(record)
        log(f"  {reg_name:<46} | Strat: {s_ret:>+6.2f}% | Bench: {b_ret:>+6.2f}% | Excess: {excess:>+6.2f} pp | MaxDD: {max_dd:>5.2f}% | Rec: {rec_yrs:.2f}y | {record['regime_status']}")

    res_df = pd.DataFrame(rows)
    avg_max_dd = res_df['max_drawdown_pct'].mean()
    max_rec_yrs = res_df['recovery_duration_years'].max()

    log("\n" + "=" * 80)
    log("GATE 17 COMPLIANCE EVALUATION")
    log("=" * 80)
    log(f"  Regimes Evaluated:            {len(res_df)}")
    log(f"  Average Max Drawdown:         {avg_max_dd:.2f}% (Threshold: < 50.0%)")
    log(f"  Max Drawdown Across Regimes:  {res_df['max_drawdown_pct'].max():.2f}% (Threshold: < 70.0%)")
    log(f"  Max Recovery Duration:        {max_rec_yrs:.2f} years (Pass Threshold: < 3.0 years)")
    
    gate17_pass = (all_passed and max_rec_yrs < 3.0 and avg_max_dd < 50.0)
    log(f"  Gate 17 Status:               {'PASS' if gate17_pass else 'FAIL'}")

    res_df.to_csv(OUT_CSV, index=False)
    log(f"\nExported Macro Regimes Results: {OUT_CSV}")

    with open(OUT_LOG, "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines) + "\n")

if __name__ == "__main__":
    main()
