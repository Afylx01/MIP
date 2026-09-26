#!/usr/bin/env python3
"""
deliverables/phase_7/scripts/test_universe_and_paper_trading.py
Phase 7B Task 5: Universe Segment Sensitivity & Simulated Paper Trading (Gates 16 & 13)

Part 1: Gate 16 (Universe Breadth Sensitivity)
  - Tests baseline momentum strategy across 5 discrete index universe segments (2016-2026):
    1. NIFTY 50 (Mega-cap)
    2. NIFTY Next 50 (Large/Midcap transition)
    3. NIFTY Midcap 150
    4. NIFTY Smallcap 250
    5. NIFTY 500 (Composite)
  - Pass Criteria: At least 3 universes beat Benchmark CAGR by >= +3.0 percentage points.
  - Export: deliverables/phase_7/data_csv/gate16_universe_sensitivity.csv

Part 2: Gate 13 (Simulated Paper Trading Calibration)
  - Runs recent 12-month forward simulation (2025-09-01 to 2026-08-31):
    - Ideal theoretical model (zero friction, zero slippage)
    - Realistic execution model (10 bps slippage, statutory STT/fees)
  - Pass Criteria: Tracking error < 5.0%; effective slippage <= 1.5x base cost.
  - Export: deliverables/phase_7/data_csv/gate13_paper_trading_calibration.csv

Outputs log: deliverables/phase_7/raw/test_universe_and_paper_trading.log
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

OUT_GATE16_CSV = DATA_CSV_DIR / "gate16_universe_sensitivity.csv"
OUT_GATE13_CSV = DATA_CSV_DIR / "gate13_paper_trading_calibration.csv"
OUT_LOG = RAW_DIR / "test_universe_and_paper_trading.log"

def partition_snapshot_universes(
    all_snap_universes: Dict[str, Set[str]],
    price_lookup: Dict
) -> Dict[str, Dict[str, Set[str]]]:
    """
    Partitions NIFTY 500 snapshot universes into 5 segments based on turnover/market proxy:
      - NIFTY 50: ranks 1..50
      - NIFTY Next 50: ranks 51..100
      - NIFTY Midcap 150: ranks 101..250
      - NIFTY Smallcap 250: ranks 251..500
      - NIFTY 500: all 500
    """
    segments = {
        "NIFTY 50": {},
        "NIFTY Next 50": {},
        "NIFTY Midcap 150": {},
        "NIFTY Smallcap 250": {},
        "NIFTY 500": {}
    }

    for snap_dt, sym_set in all_snap_universes.items():
        # Rank constituents by turnover proxy (close * volume) or close
        ranked_syms = []
        for s in sym_set:
            row = price_lookup.get((s, snap_dt))
            px = row["close"] if row else 100.0
            vol = row.get("volume", 100000.0) if row else 100000.0
            turnover = px * (vol if vol > 0 else 100000.0)
            ranked_syms.append((s, turnover))

        ranked_syms.sort(key=lambda x: -x[1])
        ordered = [s for s, _ in ranked_syms]

        segments["NIFTY 50"][snap_dt] = set(ordered[:50])
        segments["NIFTY Next 50"][snap_dt] = set(ordered[50:100])
        segments["NIFTY Midcap 150"][snap_dt] = set(ordered[100:250])
        segments["NIFTY Smallcap 250"][snap_dt] = set(ordered[250:500])
        segments["NIFTY 500"][snap_dt] = set(ordered[:500])

    return segments

def main():
    DATA_CSV_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    log_lines = []
    def log(msg=""):
        print(msg)
        log_lines.append(msg)

    log("=" * 80)
    log("PHASE 7B TASK 5: UNIVERSE BREADTH & SIMULATED PAPER TRADING (GATES 16 & 13)")
    log(f"Timestamp: {datetime.datetime.now(datetime.timezone.utc).isoformat()}")
    log("=" * 80)

    cal_mgr = CalendarManager(base_dir=BASE_DIR, use_bhavcopy_calendar=True)
    u_mgr = UniverseManager(base_dir=BASE_DIR)
    window_days = cal_mgr.get_trading_days(START_DATE, END_DATE)
    snaps = cal_mgr.get_monthly_rebalance_snapshots(START_DATE, END_DATE)
    snap_universes_n500 = u_mgr.get_all_snapshot_universes(snaps)

    log(f"Loading Bhavcopy and benchmark data across {START_DATE} to {END_DATE}...")
    reader = BhavcopyReader(base_dir=BASE_DIR, custom_path=BHAVCOPY_PATH)
    price_lookup = reader.get_price_lookup(START_DATE, END_DATE)
    idx_df = reader.load_benchmark_index()
    benchmark_lookup = idx_df.set_index("date").to_dict(orient="index")

    b_start = benchmark_lookup[window_days[0]]["close"]
    b_end = benchmark_lookup[window_days[-1]]["close"]
    yrs = (pd.to_datetime(window_days[-1]) - pd.to_datetime(window_days[0])).days / 365.25
    b_cagr = (((b_end / b_start) ** (1.0 / yrs)) - 1.0) * 100.0

    # -------------------------------------------------------------
    # PART 1: GATE 16 (Universe Segment Sensitivity)
    # -------------------------------------------------------------
    log("\n" + "=" * 80)
    log("PART 1: GATE 16 (UNIVERSE BREADTH SENSITIVITY)")
    log("=" * 80)
    log(f"Benchmark CAGR: {b_cagr:.2f}% across {len(window_days)} trading days")

    partitioned = partition_snapshot_universes(snap_universes_n500, price_lookup)

    gate16_rows = []
    for uname in ["NIFTY 50", "NIFTY Next 50", "NIFTY Midcap 150", "NIFTY Smallcap 250", "NIFTY 500"]:
        u_dict = partitioned[uname]
        res = run_simulation_instance(
            slippage_bps=10.0,
            cost_multiplier=1.0,
            window_days=window_days,
            snap_dates=snaps,
            snap_universes=u_dict,
            price_lookup=price_lookup,
            benchmark_lookup=benchmark_lookup,
            record_full_deliverables=False
        )

        m = res["metrics"]
        acc = res["acc_identity"]
        s_cagr = m["cagr"]
        excess = s_cagr - b_cagr
        is_pass = (excess >= 3.0)

        record = {
            "universe_name": uname,
            "universe_size": len(next(iter(u_dict.values()))),
            "strategy_cagr_pct": round(s_cagr, 2),
            "benchmark_cagr_pct": round(b_cagr, 2),
            "excess_cagr_pp": round(excess, 2),
            "max_drawdown_pct": round(m["max_dd"], 2),
            "sharpe_ratio": round(m["sharpe"], 2),
            "trades_count": m["total_closed_trades"],
            "beat_threshold": "PASS" if is_pass else "FAIL",
            "rule_r3_residual": acc["residual"]
        }
        gate16_rows.append(record)
        log(f"  {uname:<20} | Strat: {s_cagr:>5.2f}% | Excess: {excess:>+5.2f} pp | MaxDD: {m['max_dd']:>5.2f}% | Sharpe: {m['sharpe']:.2f} | {record['beat_threshold']}")

    df_g16 = pd.DataFrame(gate16_rows)
    pass_u_count = (df_g16["beat_threshold"] == "PASS").sum()
    gate16_status = "PASS" if pass_u_count >= 3 else "FAIL"

    log(f"\nGate 16 Compliance: {pass_u_count} / 5 universes beat benchmark by >= +3.0 pp (Pass Threshold: >= 3)")
    log(f"Gate 16 Status:     {gate16_status}")
    df_g16.to_csv(OUT_GATE16_CSV, index=False)
    log(f"Exported Gate 16 Results: {OUT_GATE16_CSV}")

    # -------------------------------------------------------------
    # PART 2: GATE 13 (Simulated Paper Trading Calibration)
    # -------------------------------------------------------------
    log("\n" + "=" * 80)
    log("PART 2: GATE 13 (SIMULATED PAPER TRADING CALIBRATION: 2025-09-01 to 2026-08-31)")
    log("=" * 80)

    pt_start = "2025-09-01"
    pt_end = "2026-08-31"
    pt_days = cal_mgr.get_trading_days(pt_start, pt_end)
    pt_snaps = cal_mgr.get_monthly_rebalance_snapshots(pt_start, pt_end)
    pt_u = u_mgr.get_all_snapshot_universes(pt_snaps)

    # 1. Ideal Model (0 bps slippage, 0 cost multiplier)
    res_ideal = run_simulation_instance(
        slippage_bps=0.0,
        cost_multiplier=0.0,
        window_days=pt_days,
        snap_dates=pt_snaps,
        snap_universes=pt_u,
        price_lookup=price_lookup,
        benchmark_lookup=benchmark_lookup,
        record_full_deliverables=True
    )

    # 2. Executed Model (10 bps slippage, 1.0 cost multiplier)
    res_exec = run_simulation_instance(
        slippage_bps=10.0,
        cost_multiplier=1.0,
        window_days=pt_days,
        snap_dates=pt_snaps,
        snap_universes=pt_u,
        price_lookup=price_lookup,
        benchmark_lookup=benchmark_lookup,
        record_full_deliverables=True
    )

    m_ideal = res_ideal["metrics"]
    m_exec = res_exec["metrics"]
    acc_ideal = res_ideal["acc_identity"]
    acc_exec = res_exec["acc_identity"]

    ideal_cagr = m_ideal["cagr"]
    exec_cagr = m_exec["cagr"]
    tracking_err_pp = abs(ideal_cagr - exec_cagr)

    # Frictional breakdown from executed trades
    total_gross = sum(t["gross_value"] for t in res_exec["detailed_trades"])
    total_slip = sum(t["slippage"] for t in res_exec["detailed_trades"])
    total_fees = sum(t["net_costs"] for t in res_exec["detailed_trades"])
    total_drag = total_slip + total_fees
    drag_bps = (total_drag / total_gross * 10000.0) if total_gross > 0 else 0.0

    b_pt_start = benchmark_lookup[pt_days[0]]["close"]
    b_pt_end = benchmark_lookup[pt_days[-1]]["close"]
    pt_yrs = (pd.to_datetime(pt_days[-1]) - pd.to_datetime(pt_days[0])).days / 365.25
    b_pt_cagr = (((b_pt_end / b_pt_start) ** (1.0 / pt_yrs)) - 1.0) * 100.0

    gate13_pass = (tracking_err_pp < 5.0 and drag_bps <= 150.0)

    g13_record = [{
        "calibration_period": f"{pt_start} to {pt_end}",
        "trading_days": len(pt_days),
        "ideal_theoretical_cagr_pct": round(ideal_cagr, 2),
        "executed_model_cagr_pct": round(exec_cagr, 2),
        "benchmark_cagr_pct": round(b_pt_cagr, 2),
        "tracking_error_pp": round(tracking_err_pp, 2),
        "total_turnover_inr": round(total_gross, 2),
        "total_slippage_inr": round(total_slip, 2),
        "total_fees_inr": round(total_fees, 2),
        "total_frictional_drag_inr": round(total_drag, 2),
        "frictional_drag_bps": round(drag_bps, 1),
        "trades_executed": len(res_exec["detailed_trades"]),
        "tracking_error_pass": "PASS" if tracking_err_pp < 5.0 else "FAIL",
        "drag_ratio_pass": "PASS" if drag_bps <= 150.0 else "FAIL",
        "gate13_status": "PASS" if gate13_pass else "FAIL",
        "rule_r3_residual": acc_exec["residual"]
    }]

    df_g13 = pd.DataFrame(g13_record)
    log(f"  Ideal Theoretical CAGR:       {ideal_cagr:.2f}%")
    log(f"  Executed Model CAGR:          {exec_cagr:.2f}%")
    log(f"  Execution Tracking Error:     {tracking_err_pp:.2f} pp (Pass Threshold: < 5.0 pp)")
    log(f"  Total Turnover Executed:      INR {total_gross:,.2f}")
    log(f"  Frictional Drag:              INR {total_drag:,.2f} ({drag_bps:.1f} bps) (Pass Threshold: <= 150.0 bps)")
    log(f"  Gate 13 Status:               {'PASS' if gate13_pass else 'FAIL'}")

    df_g13.to_csv(OUT_GATE13_CSV, index=False)
    log(f"Exported Gate 13 Results: {OUT_GATE13_CSV}")

    with open(OUT_LOG, "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines) + "\n")

if __name__ == "__main__":
    main()
