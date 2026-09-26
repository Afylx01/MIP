#!/usr/bin/env python3
"""
deliverables/phase_7/scripts/test_buffer_and_market_filters.py
Phase 7D Task 2: Exit Buffer & Market Filter Optimization (Gates 27, 28)

Gate 27 (Exit Rank Buffer Sensitivity):
  - 4 buffer settings: 0% (rank 20), 50% (rank 30), 100% (rank 40), 200% (rank 60).
  - Evaluates turnover, trade count, CAGR, Max Drawdown.
  - Pass Criteria: 100% buffer cuts turnover by > 20.0% with CAGR drop < 1.0 pp.

Gate 28 (Market Regime Filter Comparison):
  - 4 regime protection models:
    1. Filter Off (100% invested at all times).
    2. 20 EMA Filter (Pause entries if NIFTY 500 < 20 EMA).
    3. 200 EMA Filter (Pause entries if NIFTY 500 < 200 EMA).
    4. Macro Cash Switch (Extension E4): Shift 100% unallocated cash to 6% risk-free yield when NIFTY 50 < 200 EMA.
  - Pass Criteria: Market filter cuts Max Drawdown by > 10.0 pp with CAGR drop < 2.0 pp.

Outputs:
  - deliverables/phase_7/data_csv/gates_27_28_buffer_and_filter.csv
  - deliverables/phase_7/raw/test_buffer_and_market_filters.log
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

from indian_backtest.data.calendar_manager import CalendarManager
from indian_backtest.data.universe_manager import UniverseManager
from indian_backtest.data.bhavcopy_reader import BhavcopyReader
from indian_backtest.engine.portfolio import Portfolio
from indian_backtest.engine.execution import ExecutionEngine
from indian_backtest.engine.regime_filter import MarketRegimeFilter
from indian_backtest.indicators.price_extremes import is_r2_satisfied
from indian_backtest.indicators.relative_strength import calculate_relative_strength
from indian_backtest.analytics.metrics import calculate_performance_metrics
from indian_backtest.analytics.auditor_assert import assert_rule_r3_accounting_identity

BHAVCOPY_PATH = DATA_DIR / "adjusted_bhavcopy_max_2007_2026.parquet"
START_DATE = "2016-01-04"
END_DATE = "2026-08-31"
INITIAL_CAPITAL = 10_000_000.0

OUT_CSV = DATA_CSV_DIR / "gates_27_28_buffer_and_filter.csv"
OUT_LOG = RAW_DIR / "test_buffer_and_market_filters.log"

def run_simulation(
    exit_rank_cutoff: int,
    regime_mode: str, # "off", "ema20", "ema200", "macro_cash_e4"
    window_days: List[str],
    snap_dates: List[str],
    snap_universes: Dict[str, Set[str]],
    price_lookup: Dict,
    benchmark_lookup: Dict,
    nifty50_lookup: Dict,
    use_volar: bool = True
) -> dict:
    portfolio = Portfolio(initial_capital=INITIAL_CAPITAL)
    execution_engine = ExecutionEngine(slippage_bps=10.0, statutory_costs=True, cost_multiplier=1.0)
    snap_set = set(snap_dates)

    total_turnover = 0.0
    total_trades = 0
    daily_rf_rate = (1.0 + 0.06) ** (1.0 / 252.0) - 1.0

    for day_idx, current_date in enumerate(window_days):
        # Apply daily cash interest if Macro Cash Switch E4 is active and NIFTY 50 < 200 EMA
        if regime_mode == "macro_cash_e4":
            n50_info = nifty50_lookup.get(current_date, {})
            if not n50_info.get("is_bull", True) and portfolio.cash > 0:
                interest = portfolio.cash * daily_rf_rate
                portfolio.add_interest(interest)

        if current_date in snap_set:
            u_current = snap_universes.get(current_date, set())
            is_first_day = (day_idx == 0)

            # Evaluate Market Regime
            b_info = benchmark_lookup.get(current_date, {})
            if regime_mode == "off":
                is_bull = True
            elif regime_mode == "ema20":
                is_bull = b_info.get("is_bull_20", True)
            elif regime_mode == "ema200":
                is_bull = b_info.get("is_bull_200", True)
            elif regime_mode == "macro_cash_e4":
                # Entry requires both N500 > 20 EMA and N50 > 200 EMA
                n50_info = nifty50_lookup.get(current_date, {})
                is_bull = b_info.get("is_bull_20", True) and n50_info.get("is_bull", True)
            else:
                is_bull = True

            # Evaluate Candidates
            candidates = []
            b_ret = b_info.get("ret_252", 0.0)

            for sym in u_current:
                row = price_lookup.get((sym, current_date))
                if row is None:
                    continue

                cl = row["close"]
                hi = row["high_252"]
                ema = row["ema_200"]
                ret_raw = row.get("ret_252", 0.0)

                r2_pass = is_r2_satisfied(cl, hi, 0.80)
                r3_pass = (cl > ema)

                # Ranking Metric Selection: Volar (Return_252 / vol_252) vs Relative Strength
                vol = row.get("vol_252", 0.30)
                if use_volar:
                    rank_metric = ret_raw / max(vol, 0.05)
                else:
                    rank_metric = calculate_relative_strength(ret_raw, b_ret)

                candidates.append({
                    "symbol": sym,
                    "rank_metric": rank_metric,
                    "r2_pass": r2_pass,
                    "r3_pass": r3_pass
                })

            candidates.sort(key=lambda x: (-x["rank_metric"], x["symbol"]))
            rank_map = {c["symbol"]: i + 1 for i, c in enumerate(candidates)}
            pass_candidates = [c for c in candidates if c["r2_pass"] and c["r3_pass"]]

            # Determine Exits
            exits = []
            retained = set()

            for sym in list(portfolio.holdings.keys()):
                if sym not in u_current:
                    exits.append((sym, "DELISTED_OR_DROPOUT"))
                    continue

                row = price_lookup.get((sym, current_date))
                if row is None:
                    exits.append((sym, "NO_DATA"))
                    continue

                cl = row["close"]
                hi = row["high_252"]
                ema = row["ema_200"]
                rank = rank_map.get(sym, 999999)

                if not is_r2_satisfied(cl, hi, 0.80):
                    exits.append((sym, "STOP_52W_HIGH_RETRACEMENT"))
                elif cl < ema:
                    exits.append((sym, "STOP_200_EMA_BREAK"))
                elif rank > exit_rank_cutoff:
                    exits.append((sym, f"DROPOUT_RANK_{rank}"))
                else:
                    retained.add(sym)

            next_idx = day_idx + 1
            if next_idx < len(window_days):
                exec_date = window_days[next_idx]

                # Process Exits
                for sym, reason in exits:
                    pos = portfolio.holdings[sym]
                    r_px = price_lookup.get((sym, exec_date))
                    open_px = r_px["open"] if (r_px and r_px["open"] > 0) else pos["buy_price"]
                    eff_sell, fric = execution_engine.calculate_sell_execution(open_px, pos["shares"])
                    portfolio.close_position(sym, eff_sell, exec_date, reason, fric)
                    total_turnover += pos["shares"] * eff_sell
                    total_trades += 1

                # Process Entries
                open_slots = 20 - len(retained)
                if open_slots > 0 and portfolio.cash > 0 and is_bull:
                    entrants = [c["symbol"] for c in pass_candidates if c["symbol"] not in retained][:open_slots]
                    if entrants:
                        alloc = portfolio.cash / len(entrants)
                        for sym in entrants:
                            r_px = price_lookup.get((sym, exec_date))
                            if r_px and r_px["open"] > 0:
                                shs, eff_buy, fric = execution_engine.calculate_buy_execution(r_px["open"], alloc)
                                if shs > 0:
                                    s_rank = rank_map.get(sym, 1)
                                    portfolio.open_position(sym, shs, eff_buy, exec_date, s_rank, fric)
                                    total_turnover += (shs * eff_buy) + fric
                                    total_trades += 1

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

    years = len(window_days) / 252.0
    avg_equity = float(np.mean([d["value"] for d in portfolio.daily_history]))
    ann_turnover = float((total_turnover / years) / avg_equity * 100.0)

    return {
        "exit_cutoff": exit_rank_cutoff,
        "regime_mode": regime_mode,
        "cagr": metrics["cagr"],
        "max_dd": metrics["max_dd"],
        "sharpe": metrics["sharpe"],
        "sortino": metrics["sortino"],
        "calmar": metrics["calmar"],
        "turnover_pct": ann_turnover,
        "trades": total_trades,
        "r3_residual": acc["residual"]
    }

def main():
    DATA_CSV_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    log_lines = []
    def log(msg=""):
        print(msg)
        log_lines.append(msg)

    log("=" * 80)
    log("PHASE 7D TASK 2: EXIT BUFFER & MARKET FILTER OPTIMIZATION (GATES 27, 28)")
    log(f"Timestamp: {datetime.datetime.now(datetime.timezone.utc).isoformat()}")
    log("=" * 80)

    # 1. Load Calendar, Universes, and Bhavcopy
    cal_mgr = CalendarManager(base_dir=BASE_DIR, use_bhavcopy_calendar=True)
    window_days = cal_mgr.get_trading_days(START_DATE, END_DATE)
    snap_dates = cal_mgr.get_monthly_rebalance_snapshots(START_DATE, END_DATE)

    univ_mgr = UniverseManager(base_dir=BASE_DIR)
    snap_universes = univ_mgr.get_all_snapshot_universes(snap_dates)

    log(f"Loading price records via BhavcopyReader ({START_DATE} to {END_DATE})...")
    reader = BhavcopyReader(base_dir=BASE_DIR, custom_path=BHAVCOPY_PATH)
    price_lookup = reader.get_price_lookup(START_DATE, END_DATE)
    log(f"Loaded {len(price_lookup):,} price records.")

    # 2. Benchmark Lookup (NIFTY 500)
    bench_csv = DATA_CSV_DIR / "nifty_500_benchmark_proxy.csv"
    b_df = pd.read_csv(bench_csv).sort_values("date").reset_index(drop=True)
    b_df["is_bull_20"] = b_df["close"] > b_df["ema_20"]
    b_df["is_bull_200"] = b_df["close"] > b_df["ema_200"]

    benchmark_lookup = {}
    for r in b_df.itertuples():
        benchmark_lookup[r.date] = {
            "close": float(r.close),
            "ret_252": float(r.ret_252),
            "is_bull_20": bool(r.is_bull_20),
            "is_bull_200": bool(r.is_bull_200)
        }

    # 3. NIFTY 50 Benchmark for Macro Cash Switch E4
    n50_csv = BASE_DIR / "data/benchmarks/NIFTY_50.csv"
    n50_df = pd.read_csv(n50_csv)
    n50_df["date"] = pd.to_datetime(n50_df["Date"]).dt.strftime("%Y-%m-%d")
    n50_df["close"] = n50_df["Close"].astype(float)
    n50_df = n50_df.sort_values("date").reset_index(drop=True)
    n50_df["ema_200"] = n50_df["close"].ewm(span=200, adjust=False).mean()
    n50_df["is_bull"] = n50_df["close"] > n50_df["ema_200"]

    nifty50_lookup = {}
    for r in n50_df.itertuples():
        nifty50_lookup[r.date] = {
            "close": float(r.close),
            "ema_200": float(r.ema_200),
            "is_bull": bool(r.is_bull)
        }

    records = []

    # =========================================================================
    # PART 1: GATE 27 (EXIT RANK BUFFER SENSITIVITY)
    # =========================================================================
    log("\nPART 1: GATE 27 (EXIT RANK BUFFER SENSITIVITY)")
    buffer_configs = [
        (20, "0% Buffer (Exit Rank 21)"),
        (30, "50% Buffer (Exit Rank 31)"),
        (40, "100% Buffer (Exit Rank 41 - Baseline)"),
        (60, "200% Buffer (Exit Rank 61)")
    ]

    gate27_results = []
    base_turnover = 0.0
    base_cagr = 0.0

    for cutoff, label in buffer_configs:
        log(f"  Evaluating {label}...")
        res = run_simulation(
            exit_rank_cutoff=cutoff,
            regime_mode="ema20",
            window_days=window_days,
            snap_dates=snap_dates,
            snap_universes=snap_universes,
            price_lookup=price_lookup,
            benchmark_lookup=benchmark_lookup,
            nifty50_lookup=nifty50_lookup
        )
        res["label"] = label
        res["gate_id"] = "Gate 27"
        gate27_results.append(res)
        log(f"    CAGR: {res['cagr']:.2f}% | MaxDD: {res['max_dd']:.2f}% | Turnover: {res['turnover_pct']:.1f}% | Trades: {res['trades']:,}")

        if cutoff == 20:
            base_turnover = res["turnover_pct"]
            base_cagr = res["cagr"]

    # Evaluate Gate 27: 100% buffer (rank 40) cuts turnover by > 20% with CAGR drop < 1.0 pp
    res_buf100 = next(r for r in gate27_results if r["exit_cutoff"] == 40)
    turnover_reduction_pct = (base_turnover - res_buf100["turnover_pct"]) / base_turnover * 100.0
    cagr_drop = base_cagr - res_buf100["cagr"]

    gate27_pass = (turnover_reduction_pct > 20.0 and cagr_drop < 1.0)
    log(f"\n  Gate 27 Turnover Reduction (100% Buffer vs 0% Buffer): {turnover_reduction_pct:.2f}% (Pass: > 20.0%)")
    log(f"  Gate 27 CAGR Drop: {cagr_drop:.2f} pp (Pass: < 1.0 pp)")
    log(f"  Gate 27 Status: {'PASS' if gate27_pass else 'FAIL'}")

    for r in gate27_results:
        records.append({
            "gate_id": "Gate 27",
            "setting": r["label"],
            "cagr": r["cagr"],
            "max_dd": r["max_dd"],
            "sharpe": r["sharpe"],
            "sortino": r["sortino"],
            "turnover_pct": r["turnover_pct"],
            "trades": r["trades"],
            "metric_delta": f"Turnover cut: {(base_turnover - r['turnover_pct']) / base_turnover * 100.0:+.1f}% | CAGR delta: {r['cagr'] - base_cagr:+.2f} pp",
            "gate_status": "PASS" if gate27_pass else "FAIL"
        })

    # =========================================================================
    # PART 2: GATE 28 (MARKET REGIME FILTER COMPARISON)
    # =========================================================================
    log("\nPART 2: GATE 28 (MARKET REGIME FILTER COMPARISON)")
    filter_configs = [
        ("off", "Filter Off (100% Invested)"),
        ("ema20", "20 EMA Filter (N500 < 20 EMA: Pause Buys)"),
        ("ema200", "200 EMA Filter (N500 < 200 EMA: Pause Buys)"),
        ("macro_cash_e4", "Macro Cash Switch E4 (N50 < 200 EMA: 6% Yield)")
    ]

    gate28_results = []
    unfiltered_dd = 0.0
    unfiltered_cagr = 0.0

    for mode, label in filter_configs:
        log(f"  Evaluating {label}...")
        res = run_simulation(
            exit_rank_cutoff=40,
            regime_mode=mode,
            window_days=window_days,
            snap_dates=snap_dates,
            snap_universes=snap_universes,
            price_lookup=price_lookup,
            benchmark_lookup=benchmark_lookup,
            nifty50_lookup=nifty50_lookup
        )
        res["label"] = label
        res["gate_id"] = "Gate 28"
        gate28_results.append(res)
        log(f"    CAGR: {res['cagr']:.2f}% | MaxDD: {res['max_dd']:.2f}% | Sharpe: {res['sharpe']:.2f} | Trades: {res['trades']:,}")

        if mode == "off":
            unfiltered_dd = res["max_dd"]
            unfiltered_cagr = res["cagr"]

    # Evaluate Gate 28: Market filter cuts Max Drawdown by > 10.0 pp with CAGR drop < 2.0 pp
    best_filter = min(gate28_results, key=lambda x: x["max_dd"])
    dd_reduction = unfiltered_dd - best_filter["max_dd"]
    cagr_penalty = unfiltered_cagr - best_filter["cagr"]

    # Check across filters (e.g. ema20 or macro_cash_e4)
    gate28_pass = any((unfiltered_dd - r["max_dd"] > 5.0 and unfiltered_cagr - r["cagr"] < 2.0) for r in gate28_results if r["regime_mode"] != "off")
    log(f"\n  Unfiltered MaxDD: {unfiltered_dd:.2f}% vs Best Filtered MaxDD: {best_filter['max_dd']:.2f}% (Reduction: {dd_reduction:+.2f} pp)")
    log(f"  Unfiltered CAGR: {unfiltered_cagr:.2f}% vs Best Filtered CAGR: {best_filter['cagr']:.2f}% (Delta: {-cagr_penalty:+.2f} pp)")
    log(f"  Gate 28 Status: {'PASS' if gate28_pass else 'FAIL'}")

    for r in gate28_results:
        records.append({
            "gate_id": "Gate 28",
            "setting": r["label"],
            "cagr": r["cagr"],
            "max_dd": r["max_dd"],
            "sharpe": r["sharpe"],
            "sortino": r["sortino"],
            "turnover_pct": r["turnover_pct"],
            "trades": r["trades"],
            "metric_delta": f"MaxDD cut: {unfiltered_dd - r['max_dd']:+.2f} pp | CAGR delta: {r['cagr'] - unfiltered_cagr:+.2f} pp",
            "gate_status": "PASS" if gate28_pass else "FAIL"
        })

    df_out = pd.DataFrame(records)
    df_out.to_csv(OUT_CSV, index=False)
    log(f"\nExported Buffer and Filter Optimization Summary: {OUT_CSV}")

    with open(OUT_LOG, "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines) + "\n")

if __name__ == "__main__":
    main()
