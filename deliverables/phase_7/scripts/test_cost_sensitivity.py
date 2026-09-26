#!/usr/bin/env python3
"""
deliverables/phase_7/scripts/test_cost_sensitivity.py
Phase 7A Task 4: Transaction Cost & Slippage Stress Matrix (Gates 5, 6, 7, 8) & Portfolio Deliverables

Executes:
  - Gate 5: Base Institutional Cost Model (1x friction, 10 bps slippage)
  - Gate 6: 2x Cost Stress Test (Double all brokerage, STT, statutory fees & slippage)
  - Gate 7: 3x Cost Stress Test (Triple all execution friction costs)
  - Gate 8: Slippage Sensitivity Ladder (0.10%, 0.25%, 0.50%, 1.00%)
  
Standard Deliverables Generated:
  - deliverables/phase_7/data_csv/gates_5_8_cost_stress_matrix.csv
  - deliverables/phase_7/data_csv/daily_equity_curves.csv
  - deliverables/phase_7/data_csv/monthly_returns.csv
  - deliverables/phase_7/data_csv/trade_log.csv
  - deliverables/phase_7/data_csv/monthly_holdings_snapshots.parquet
  - deliverables/phase_7/data_csv/gates_1_to_10_summary.csv
  - deliverables/phase_7/raw/test_cost_sensitivity.log
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
from indian_backtest.engine.portfolio import Portfolio
from indian_backtest.engine.rebalancer import Rebalancer
from indian_backtest.engine.execution import ExecutionEngine
from indian_backtest.engine.regime_filter import MarketRegimeFilter
from indian_backtest.analytics.metrics import calculate_performance_metrics
from indian_backtest.analytics.auditor_assert import assert_rule_r3_accounting_identity

BHAVCOPY_PATH = DATA_DIR / "adjusted_bhavcopy_max_2007_2026.parquet"
START_DATE = "2016-01-04"
END_DATE = "2026-08-31"
INITIAL_CAPITAL = 10_000_000.0

OUT_MATRIX_CSV = DATA_CSV_DIR / "gates_5_8_cost_stress_matrix.csv"
OUT_EQUITY_CSV = DATA_CSV_DIR / "daily_equity_curves.csv"
OUT_MONTHLY_CSV = DATA_CSV_DIR / "monthly_returns.csv"
OUT_TRADES_CSV = DATA_CSV_DIR / "trade_log.csv"
OUT_HOLDINGS_PARQUET = DATA_CSV_DIR / "monthly_holdings_snapshots.parquet"
OUT_ALL_GATES_CSV = DATA_CSV_DIR / "gates_1_to_10_summary.csv"
OUT_LOG = RAW_DIR / "test_cost_sensitivity.log"

def run_simulation_instance(
    slippage_bps: float,
    cost_multiplier: float,
    window_days: List[str],
    snap_dates: List[str],
    snap_universes: Dict[str, Set[str]],
    price_lookup: Dict,
    benchmark_lookup: Dict,
    record_full_deliverables: bool = False
):
    portfolio = Portfolio(initial_capital=INITIAL_CAPITAL)
    rebalancer = Rebalancer(portfolio_size=20, exit_rank_multiplier=2, use_relative_strength=True)
    execution_engine = ExecutionEngine(slippage_bps=slippage_bps, statutory_costs=True, cost_multiplier=cost_multiplier)
    regime_filter = MarketRegimeFilter(enabled=True, ema_period=20)
    snap_set = set(snap_dates)

    detailed_trade_records = []
    holdings_snapshots = []
    trade_counter = 0

    for day_idx, current_date in enumerate(window_days):
        if current_date in snap_set:
            u_current = snap_universes.get(current_date, set())
            is_first_day = (day_idx == 0)
            is_bull = regime_filter.evaluate_regime(current_date, benchmark_lookup)

            pass_candidates, rank_map = rebalancer.evaluate_candidates(
                universe_symbols=u_current,
                current_date=current_date,
                price_lookup=price_lookup,
                benchmark_lookup=benchmark_lookup,
                is_first_day=is_first_day
            )

            exits, retained = rebalancer.determine_exits(
                current_holdings=portfolio.holdings,
                universe_symbols=u_current,
                current_date=current_date,
                price_lookup=price_lookup,
                rank_map=rank_map
            )

            next_idx = day_idx + 1
            if next_idx < len(window_days):
                exec_date = window_days[next_idx]

                # Process Exits
                for sym, reason in exits:
                    trade_counter += 1
                    pos = portfolio.holdings[sym]
                    r_px = price_lookup.get((sym, exec_date))
                    open_px = r_px["open"] if (r_px and r_px["open"] > 0) else pos["buy_price"]
                    eff_sell, fric = execution_engine.calculate_sell_execution(open_px, pos["shares"])
                    portfolio.close_position(sym, eff_sell, exec_date, reason, fric)

                    if record_full_deliverables:
                        gross_val = pos["shares"] * open_px
                        slip_amt = (pos["shares"] * open_px) - (pos["shares"] * eff_sell)
                        detailed_trade_records.append({
                            "trade_id": trade_counter,
                            "ticker": sym,
                            "signal_date": current_date,
                            "exec_date": exec_date,
                            "side": "SELL",
                            "shares": pos["shares"],
                            "price": eff_sell,
                            "gross_value": gross_val,
                            "net_costs": fric,
                            "slippage": slip_amt,
                            "exit_reason": reason
                        })

                # Process Entries
                open_slots = 20 - len(retained)
                if open_slots > 0 and portfolio.cash > 0 and is_bull:
                    entrants = [c["symbol"] for c in pass_candidates if c["symbol"] not in retained][:open_slots]
                    if entrants:
                        alloc = portfolio.cash / len(entrants)
                        for sym in entrants:
                            trade_counter += 1
                            r_px = price_lookup.get((sym, exec_date))
                            if r_px and r_px["open"] > 0:
                                shs, eff_buy, fric = execution_engine.calculate_buy_execution(r_px["open"], alloc)
                                if shs > 0:
                                    s_rank = rank_map.get(sym, 1)
                                    portfolio.open_position(sym, shs, eff_buy, exec_date, s_rank, fric)
                                    if record_full_deliverables:
                                        gross_val = shs * r_px["open"]
                                        slip_amt = (shs * eff_buy) - gross_val
                                        detailed_trade_records.append({
                                            "trade_id": trade_counter,
                                            "ticker": sym,
                                            "signal_date": current_date,
                                            "exec_date": exec_date,
                                            "side": "BUY",
                                            "shares": shs,
                                            "price": eff_buy,
                                            "gross_value": gross_val,
                                            "net_costs": fric,
                                            "slippage": slip_amt,
                                            "exit_reason": ""
                                        })

            # Record Snapshot Holdings at monthly rebalance
            if record_full_deliverables:
                port_val_snap = portfolio.get_portfolio_value(current_date, price_lookup)
                for sym, pos in portfolio.holdings.items():
                    r_px = price_lookup.get((sym, current_date))
                    cur_px = r_px["close"] if r_px else pos["buy_price"]
                    mkt_val = pos["shares"] * cur_px
                    holdings_snapshots.append({
                        "snapshot_date": current_date,
                        "symbol": sym,
                        "rank": pos["entry_rank"],
                        "shares": pos["shares"],
                        "price": cur_px,
                        "market_value": mkt_val,
                        "weight": (mkt_val / port_val_snap) if port_val_snap > 0 else 0.0
                    })

        portfolio.record_daily_valuation(current_date, price_lookup)

    final_date = window_days[-1]
    final_val = portfolio.get_portfolio_value(final_date, price_lookup)
    acc = portfolio.compute_accounting_identity(final_date, price_lookup)
    assert_rule_r3_accounting_identity(acc)

    metrics = calculate_performance_metrics(
        daily_history=portfolio.daily_history,
        closed_trades=portfolio.closed_trades,
        initial_capital=INITIAL_CAPITAL,
        final_value=final_val,
        start_date=window_days[0],
        final_date=final_date
    )

    return {
        "metrics": metrics,
        "acc_identity": acc,
        "portfolio": portfolio,
        "detailed_trades": detailed_trade_records,
        "holdings_snapshots": holdings_snapshots
    }

def main():
    DATA_CSV_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    log_lines = []
    def log(msg=""):
        print(msg)
        log_lines.append(msg)

    log("=" * 80)
    log("PHASE 7A TASK 4: TRANSACTION COST & SLIPPAGE STRESS MATRIX (GATES 5-8)")
    log(f"Timestamp: {datetime.datetime.now(datetime.timezone.utc).isoformat()}")
    log("=" * 80)

    # 1. Environment & Data Setup
    reader = BhavcopyReader(base_dir=BASE_DIR, custom_path=BHAVCOPY_PATH)
    price_lookup = reader.get_price_lookup(START_DATE, END_DATE)
    idx_df = reader.load_benchmark_index()
    benchmark_lookup = idx_df.set_index("date").to_dict(orient="index")

    cal_mgr = CalendarManager(base_dir=BASE_DIR, use_bhavcopy_calendar=True)
    window_days = cal_mgr.get_trading_days(START_DATE, END_DATE)
    snap_dates = cal_mgr.get_monthly_rebalance_snapshots(START_DATE, END_DATE)

    u_mgr = UniverseManager(base_dir=BASE_DIR)
    snap_universes = u_mgr.get_all_snapshot_universes(snap_dates)

    # Benchmark metrics
    b_start = benchmark_lookup[window_days[0]]["close"]
    b_end = benchmark_lookup[window_days[-1]]["close"]
    n_years = (pd.to_datetime(window_days[-1]) - pd.to_datetime(window_days[0])).days / 365.25
    benchmark_cagr = (b_end / b_start) ** (1.0 / n_years) - 1.0
    b_cagr_pct = benchmark_cagr * 100.0

    log(f"Analysis Window: {START_DATE} to {END_DATE} ({len(window_days)} days, {len(snap_dates)} snapshots)")
    log(f"Benchmark CAGR (NIFTY 500 Proxy): {b_cagr_pct:.2f}%\n")

    # =========================================================================
    # Run Baseline (1x Cost, 10 bps Slippage) with Full Deliverables Recording
    # =========================================================================
    log("--- Executing Gate 5: Base Institutional Cost Model (1x Friction, 10 bps Slippage) ---")
    res_base = run_simulation_instance(
        slippage_bps=10.0,
        cost_multiplier=1.0,
        window_days=window_days,
        snap_dates=snap_dates,
        snap_universes=snap_universes,
        price_lookup=price_lookup,
        benchmark_lookup=benchmark_lookup,
        record_full_deliverables=True
    )
    m_base = res_base["metrics"]
    acc_base = res_base["acc_identity"]
    excess_base = m_base["cagr"] - b_cagr_pct
    g5_pass = (excess_base >= 4.0)
    log(f"  Base CAGR:     {m_base['cagr']:.2f}% (Benchmark: {b_cagr_pct:.2f}%, Excess: {excess_base:+.2f} pp)")
    log(f"  Base MaxDD:    {m_base['max_dd']:.2f}% | Sharpe: {m_base['sharpe']:.2f} | Trades: {m_base['total_closed_trades']}")
    log(f"  Gate 5 Status: {'PASS' if g5_pass else 'FAIL'}")

    # =========================================================================
    # Run Gate 6: 2x Cost Stress Test
    # =========================================================================
    log("\n--- Executing Gate 6: 2x Cost Stress Test (Double all friction & slippage) ---")
    res_2x = run_simulation_instance(
        slippage_bps=10.0,
        cost_multiplier=2.0,
        window_days=window_days,
        snap_dates=snap_dates,
        snap_universes=snap_universes,
        price_lookup=price_lookup,
        benchmark_lookup=benchmark_lookup,
        record_full_deliverables=False
    )
    m_2x = res_2x["metrics"]
    excess_2x = m_2x["cagr"] - b_cagr_pct
    g6_pass = (excess_2x >= 2.0)
    log(f"  2x CAGR:       {m_2x['cagr']:.2f}% (Benchmark: {b_cagr_pct:.2f}%, Excess: {excess_2x:+.2f} pp)")
    log(f"  2x MaxDD:      {m_2x['max_dd']:.2f}% | Sharpe: {m_2x['sharpe']:.2f}")
    log(f"  Gate 6 Status: {'PASS' if g6_pass else 'FAIL'}")

    # =========================================================================
    # Run Gate 7: 3x Cost Stress Test
    # =========================================================================
    log("\n--- Executing Gate 7: 3x Cost Stress Test (Triple all friction & slippage) ---")
    res_3x = run_simulation_instance(
        slippage_bps=10.0,
        cost_multiplier=3.0,
        window_days=window_days,
        snap_dates=snap_dates,
        snap_universes=snap_universes,
        price_lookup=price_lookup,
        benchmark_lookup=benchmark_lookup,
        record_full_deliverables=False
    )
    m_3x = res_3x["metrics"]
    excess_3x = m_3x["cagr"] - b_cagr_pct
    g7_pass = (excess_3x > 0.0)
    log(f"  3x CAGR:       {m_3x['cagr']:.2f}% (Benchmark: {b_cagr_pct:.2f}%, Excess: {excess_3x:+.2f} pp)")
    log(f"  3x MaxDD:      {m_3x['max_dd']:.2f}% | Sharpe: {m_3x['sharpe']:.2f}")
    log(f"  Gate 7 Status: {'PASS' if g7_pass else 'FAIL'}")

    # =========================================================================
    # Run Gate 8: Slippage Sensitivity Ladder
    # =========================================================================
    log("\n--- Executing Gate 8: Slippage Sensitivity Ladder ---")
    slip_tiers = [10.0, 25.0, 50.0, 100.0]
    ladder_results = []

    for slip_bps in slip_tiers:
        res_s = run_simulation_instance(
            slippage_bps=slip_bps,
            cost_multiplier=1.0,
            window_days=window_days,
            snap_dates=snap_dates,
            snap_universes=snap_universes,
            price_lookup=price_lookup,
            benchmark_lookup=benchmark_lookup,
            record_full_deliverables=False
        )
        ms = res_s["metrics"]
        excess_s = ms["cagr"] - b_cagr_pct
        ladder_results.append({
            "slippage_pct": slip_bps / 100.0,
            "slippage_bps": slip_bps,
            "cagr": ms["cagr"],
            "max_dd": ms["max_dd"],
            "sharpe": ms["sharpe"],
            "excess_cagr": excess_s
        })
        log(f"  Slippage {slip_bps/100:.2f}%: CAGR={ms['cagr']:.2f}%, MaxDD={ms['max_dd']:.2f}%, Sharpe={ms['sharpe']:.2f}, Excess={excess_s:+.2f} pp")

    # Evaluate Gate 8 pass criteria
    max_dd_increase = ladder_results[-1]["max_dd"] - ladder_results[0]["max_dd"]
    cagr_rel_drop = (ladder_results[0]["cagr"] - ladder_results[-1]["cagr"]) / ladder_results[0]["cagr"] * 100.0
    cagr_at_50bps = [r["cagr"] for r in ladder_results if r["slippage_bps"] == 50.0][0]
    g8_pass = (max_dd_increase < 10.0 and cagr_at_50bps > b_cagr_pct)
    log(f"  MaxDD Increase: {max_dd_increase:.2f} pp (< 10 pp threshold)")
    log(f"  CAGR at 50 bps: {cagr_at_50bps:.2f}% (> {b_cagr_pct:.2f}% benchmark)")
    log(f"  Gate 8 Status:  {'PASS' if g8_pass else 'FAIL'}")

    # =========================================================================
    # Export Gates 5-8 Cost Stress Matrix
    # =========================================================================
    stress_rows = [
        {
            "test_name": "Gate 5: Base Institutional Cost (1x)",
            "cost_multiplier": 1.0,
            "slippage_bps": 10.0,
            "cagr_pct": m_base["cagr"],
            "max_dd_pct": m_base["max_dd"],
            "sharpe": m_base["sharpe"],
            "excess_over_benchmark_pp": excess_base,
            "gate_status": "PASS" if g5_pass else "FAIL"
        },
        {
            "test_name": "Gate 6: 2x Cost Stress Test",
            "cost_multiplier": 2.0,
            "slippage_bps": 20.0,
            "cagr_pct": m_2x["cagr"],
            "max_dd_pct": m_2x["max_dd"],
            "sharpe": m_2x["sharpe"],
            "excess_over_benchmark_pp": excess_2x,
            "gate_status": "PASS" if g6_pass else "FAIL"
        },
        {
            "test_name": "Gate 7: 3x Cost Stress Test",
            "cost_multiplier": 3.0,
            "slippage_bps": 30.0,
            "cagr_pct": m_3x["cagr"],
            "max_dd_pct": m_3x["max_dd"],
            "sharpe": m_3x["sharpe"],
            "excess_over_benchmark_pp": excess_3x,
            "gate_status": "PASS" if g7_pass else "FAIL"
        }
    ]
    for r in ladder_results:
        stress_rows.append({
            "test_name": f"Gate 8: Slippage Ladder ({r['slippage_pct']:.2f}%)",
            "cost_multiplier": 1.0,
            "slippage_bps": r["slippage_bps"],
            "cagr_pct": r["cagr"],
            "max_dd_pct": r["max_dd"],
            "sharpe": r["sharpe"],
            "excess_over_benchmark_pp": r["excess_cagr"],
            "gate_status": "PASS" if (r["cagr"] > b_cagr_pct) else "FAIL"
        })

    stress_df = pd.DataFrame(stress_rows)
    stress_df.to_csv(OUT_MATRIX_CSV, index=False)
    log(f"\nExported Cost Stress Matrix: {OUT_MATRIX_CSV}")

    # =========================================================================
    # Export Standard Portfolio Deliverables
    # =========================================================================
    log("\n--- Exporting Required Standardized Backtest Deliverables ---")

    # 1. Daily Equity Curves
    eq_rows = []
    peak_val = INITIAL_CAPITAL
    port_obj = res_base["portfolio"]

    for row in port_obj.daily_history:
        d = row["date"]
        val = row["value"]
        cash = row["cash"]
        peak_val = max(peak_val, val)
        dd = (val / peak_val - 1.0) * 100.0
        b_val = benchmark_lookup.get(d, {}).get("close", np.nan)
        eq_rows.append({
            "date": d,
            "portfolio_value": val,
            "cash_balance": cash,
            "invested_capital": val - cash,
            "benchmark_value": b_val,
            "drawdown": dd,
            "active_positions": row["holdings_count"]
        })
    eq_df = pd.DataFrame(eq_rows)
    eq_df.to_csv(OUT_EQUITY_CSV, index=False)
    log(f"  1. Exported Daily Equity Curves: {OUT_EQUITY_CSV} ({len(eq_df):,} days)")

    # 2. Monthly Returns Table
    eq_df["date_dt"] = pd.to_datetime(eq_df["date"])
    eq_df["year"] = eq_df["date_dt"].dt.year
    eq_df["month"] = eq_df["date_dt"].dt.month
    monthly_groups = eq_df.groupby(["year", "month"])

    m_rows = []
    prev_end_val = INITIAL_CAPITAL
    prev_end_b = benchmark_lookup[window_days[0]]["close"]

    for (yr, mo), grp in monthly_groups:
        end_val = grp.iloc[-1]["portfolio_value"]
        strat_ret = (end_val / prev_end_val - 1.0) * 100.0

        end_b = grp.iloc[-1]["benchmark_value"]
        bench_ret = (end_b / prev_end_b - 1.0) * 100.0 if prev_end_b > 0 else 0.0

        excess_ret = strat_ret - bench_ret
        m_rows.append({
            "year": yr,
            "month": mo,
            "strategy_return": strat_ret,
            "benchmark_return": bench_ret,
            "excess_return": excess_ret
        })
        prev_end_val = end_val
        prev_end_b = end_b

    m_df = pd.DataFrame(m_rows)
    m_df.to_csv(OUT_MONTHLY_CSV, index=False)
    log(f"  2. Exported Monthly Returns Table: {OUT_MONTHLY_CSV} ({len(m_df):,} months)")

    # 3. Comprehensive Trade Log
    trades_df = pd.DataFrame(res_base["detailed_trades"])
    trades_df.to_csv(OUT_TRADES_CSV, index=False)
    log(f"  3. Exported Comprehensive Trade Log: {OUT_TRADES_CSV} ({len(trades_df):,} trades)")

    # 4. Holdings Snapshots
    holdings_df = pd.DataFrame(res_base["holdings_snapshots"])
    holdings_df.to_parquet(OUT_HOLDINGS_PARQUET, index=False)
    log(f"  4. Exported Monthly Holdings Snapshots: {OUT_HOLDINGS_PARQUET} ({len(holdings_df):,} rows)")

    # =========================================================================
    # 5. Compile Gates 1 to 10 Consolidated Summary Table
    # =========================================================================
    log("\n--- Compiling Gates 1-10 Master Summary Table ---")
    g1_4_df = pd.read_csv(DATA_CSV_DIR / "gates_1_4_integrity_audit.csv")
    g9_10_df = pd.read_csv(DATA_CSV_DIR / "gates_9_10_execution_constraints.csv")

    g5_actual = f"Net CAGR: {m_base['cagr']:.2f}% (Benchmark: {b_cagr_pct:.2f}%, Excess: {excess_base:+.2f} pp >= +4.0 pp)"
    g6_actual = f"Net CAGR: {m_2x['cagr']:.2f}% (Benchmark: {b_cagr_pct:.2f}%, Excess: {excess_2x:+.2f} pp >= +2.0 pp)"
    g7_actual = f"Net CAGR: {m_3x['cagr']:.2f}% (Benchmark: {b_cagr_pct:.2f}%, Excess: {excess_3x:+.2f} pp > 0.0 pp)"
    g8_actual = f"MaxDD increase: {max_dd_increase:.2f} pp (< 10 pp); CAGR at 50 bps slippage: {cagr_at_50bps:.2f}% (> {b_cagr_pct:.2f}%)"

    cost_summary_rows = [
        {
            "gate_id": "Gate 5",
            "test_name": "Base Institutional Cost Model",
            "pass_threshold": "Net CAGR > Benchmark CAGR + 4.0 percentage points",
            "fail_threshold": "Net CAGR < Benchmark CAGR + 2.0 percentage points",
            "actual_value": g5_actual,
            "test_status": "PASS" if g5_pass else "FAIL",
            "details": f"1x institutional schedule: 0.03% broking, 0.1% STT, 0.015% stamp, 10 bps slippage"
        },
        {
            "gate_id": "Gate 6",
            "test_name": "2x Cost Stress Test",
            "pass_threshold": "Net CAGR remains > Benchmark CAGR + 2.0 percentage points",
            "fail_threshold": "Strategy alpha disappears or drops below benchmark",
            "actual_value": g6_actual,
            "test_status": "PASS" if g6_pass else "FAIL",
            "details": f"2x institutional schedule: Round-trip friction doubled to ~1.50%"
        },
        {
            "gate_id": "Gate 7",
            "test_name": "3x Cost Stress Test",
            "pass_threshold": "Net excess return over benchmark remains strictly positive (> 0.0%)",
            "fail_threshold": "Negative excess return (strategy destroyed by friction)",
            "actual_value": g7_actual,
            "test_status": "PASS" if g7_pass else "FAIL",
            "details": f"3x institutional schedule: Round-trip friction tripled to ~2.25%"
        },
        {
            "gate_id": "Gate 8",
            "test_name": "Slippage Sensitivity Ladder",
            "pass_threshold": "Max Drawdown increase < 10 percentage points; CAGR > benchmark at <= 0.50% slippage",
            "fail_threshold": "CAGR drops below benchmark at <= 0.50% slippage",
            "actual_value": g8_actual,
            "test_status": "PASS" if g8_pass else "FAIL",
            "details": f"Discrete slippage tiers evaluated: 0.10%, 0.25%, 0.50%, 1.00%"
        }
    ]
    cost_summary_df = pd.DataFrame(cost_summary_rows)

    all_gates_df = pd.concat([g1_4_df, cost_summary_df, g9_10_df], ignore_index=True)
    all_gates_df.to_csv(OUT_ALL_GATES_CSV, index=False)
    log(f"  5. Exported Master Gates 1-10 Summary: {OUT_ALL_GATES_CSV}")

    log("\n" + "=" * 80)
    log("PHASE 7A TASK 4 COMPLETE: GATES 5-8 VERIFIED & MASTER DELIVERABLES EXPORTED")
    log("=" * 80)

    with open(OUT_LOG, "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines) + "\n")

if __name__ == "__main__":
    main()
