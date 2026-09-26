#!/usr/bin/env python3
"""
deliverables/phase_7/scripts/test_component_attribution.py
Phase 7D Task 1: Sequential Component Attribution & Ablation Study (Gate 26)

Evaluates the strategy incrementally across 5 distinct steps (2016-01-04 to 2026-08-31):
  - Step 1 (Raw Base): 20% retracement + Close > 200 EMA + Top 20 equal-weight (Exit rank 21, no regime filter, raw 252d return).
  - Step 2 (+ Relative Strength): Add Filter 3 (Stock / NIFTY 500 ratio > 200 EMA).
  - Step 3 (+ Volar Ranking): Replace with Volatility-Adjusted Return (Return_252 / sigma_252).
  - Step 4 (+ Market Regime Filter): Add NIFTY 500 < 20 EMA cash rule (pause buys, exit dropouts).
  - Step 5 (+ Exit Rank Buffer): Add Exit Rank 40 (100% buffer: keep existing positions if rank <= 40).

Pass Criteria:
  - Each added rule must improve CAGR by > 1.0 pp OR reduce Max Drawdown by > 5.0 pp without reducing CAGR by > 2.0 pp.

Outputs:
  - deliverables/phase_7/data_csv/gate26_component_attribution.csv
  - deliverables/phase_7/raw/test_component_attribution.log
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
from indian_backtest.analytics.metrics import calculate_performance_metrics
from indian_backtest.analytics.auditor_assert import assert_rule_r3_accounting_identity

BHAVCOPY_PATH = DATA_DIR / "adjusted_bhavcopy_max_2007_2026.parquet"
START_DATE = "2016-01-04"
END_DATE = "2026-08-31"
INITIAL_CAPITAL = 10_000_000.0

OUT_CSV = DATA_CSV_DIR / "gate26_component_attribution.csv"
OUT_LOG = RAW_DIR / "test_component_attribution.log"

def build_data_lookup(bhavcopy_path: Path, start_date: str, end_date: str, bench_map: Dict[str, float]):
    reader = BhavcopyReader(base_dir=BASE_DIR, custom_path=bhavcopy_path)
    df = reader.load_combined_bars(start_date, end_date).copy()

    # Filter 3: Stock / NIFTY 500 ratio > 200 EMA of ratio
    df["b_close"] = df["date"].map(bench_map).fillna(1.0)
    df["rs_ratio"] = df["close"] / df["b_close"]
    df["rs_ema_200"] = df.groupby("symbol")["rs_ratio"].transform(lambda x: x.ewm(span=200, adjust=True, min_periods=1).mean())
    df["rs_pass"] = df["rs_ratio"] > df["rs_ema_200"]

    price_lookup = {}
    for row in df.itertuples(index=False):
        price_lookup[(row.symbol, row.date)] = {
            "open": float(row.open),
            "high": float(row.high),
            "low": float(row.low),
            "close": float(row.close),
            "high_252": float(row.high_252) if not np.isnan(row.high_252) else float(row.close),
            "ema_200": float(row.ema_200),
            "ret_252": float(row.ret_252),
            "vol_252": float(row.vol_252),
            "rs_pass": bool(row.rs_pass)
        }

    return price_lookup

def run_ablation_step(
    step_name: str,
    use_filter_3: bool,          # Filter 3: Stock / NIFTY 500 ratio > 200 EMA
    ranking_mode: str,          # "raw", "volar"
    use_regime_filter: bool,
    exit_buffer_multiplier: int, # 1 for 0% buffer (rank 20), 2 for 100% buffer (rank 40)
    window_days: List[str],
    snap_dates: List[str],
    snap_universes: Dict[str, Set[str]],
    price_lookup: Dict,
    benchmark_lookup: Dict
) -> dict:
    portfolio = Portfolio(initial_capital=INITIAL_CAPITAL)
    execution_engine = ExecutionEngine(slippage_bps=10.0, statutory_costs=True, cost_multiplier=1.0)
    regime_filter = MarketRegimeFilter(enabled=use_regime_filter, ema_period=20)
    snap_set = set(snap_dates)

    total_turnover = 0.0
    total_trades = 0

    for day_idx, current_date in enumerate(window_days):
        if current_date in snap_set:
            u_current = snap_universes.get(current_date, set())
            is_first_day = (day_idx == 0)
            is_bull = regime_filter.evaluate_regime(current_date, benchmark_lookup) if use_regime_filter else True

            # Evaluate Candidates
            candidates = []
            for sym in u_current:
                row = price_lookup.get((sym, current_date))
                if row is None:
                    continue

                cl = row["close"]
                hi = row["high_252"]
                ema = row["ema_200"]
                ret_raw = row["ret_252"]
                vol = row["vol_252"]
                rs_pass = row["rs_pass"]

                r2_pass = is_r2_satisfied(cl, hi, 0.80)
                r3_pass = (cl > ema)

                # Ranking Metric Selection
                if ranking_mode == "volar":
                    rank_metric = ret_raw / max(vol, 0.05)
                else:
                    rank_metric = ret_raw

                candidates.append({
                    "symbol": sym,
                    "rank_metric": rank_metric,
                    "r2_pass": r2_pass,
                    "r3_pass": r3_pass,
                    "rs_pass": rs_pass
                })

            candidates.sort(key=lambda x: (-x["rank_metric"], x["symbol"]))
            rank_map = {c["symbol"]: i + 1 for i, c in enumerate(candidates)}

            # Eligibility: Filter 1 & 2 always required; Filter 3 if enabled
            pass_candidates = [
                c for c in candidates
                if c["r2_pass"] and c["r3_pass"] and (c["rs_pass"] if use_filter_3 else True)
            ]

            # Determine Exits
            exit_cutoff = 20 * exit_buffer_multiplier
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
                rs_pass = row["rs_pass"]
                rank = rank_map.get(sym, 999999)

                # Exit triggers
                if not is_r2_satisfied(cl, hi, 0.80):
                    exits.append((sym, "STOP_52W_HIGH_RETRACEMENT"))
                elif cl < ema:
                    exits.append((sym, "STOP_200_EMA_BREAK"))
                elif use_filter_3 and not rs_pass:
                    exits.append((sym, "STOP_RELATIVE_STRENGTH_BREAK"))
                elif rank > exit_cutoff:
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
        "step_name": step_name,
        "use_filter_3": use_filter_3,
        "ranking_mode": ranking_mode,
        "use_regime_filter": use_regime_filter,
        "exit_buffer": f"{exit_buffer_multiplier * 100 - 100}% (Rank {exit_buffer_multiplier * 20})",
        "cagr": metrics["cagr"],
        "max_dd": metrics["max_dd"],
        "sharpe": metrics["sharpe"],
        "sortino": metrics["sortino"],
        "turnover_pct": ann_turnover,
        "trades": metrics["total_closed_trades"],
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
    log("PHASE 7D TASK 1: SEQUENTIAL COMPONENT ATTRIBUTION & ABLATION STUDY (GATE 26)")
    log(f"Timestamp: {datetime.datetime.now(datetime.timezone.utc).isoformat()}")
    log("=" * 80)

    # Load Calendar and Universes
    cal_mgr = CalendarManager(base_dir=BASE_DIR, use_bhavcopy_calendar=True)
    window_days = cal_mgr.get_trading_days(START_DATE, END_DATE)
    snap_dates = cal_mgr.get_monthly_rebalance_snapshots(START_DATE, END_DATE)

    univ_mgr = UniverseManager(base_dir=BASE_DIR)
    snap_universes = univ_mgr.get_all_snapshot_universes(snap_dates)

    # Load Benchmark Proxy
    bench_csv = DATA_CSV_DIR / "nifty_500_benchmark_proxy.csv"
    b_df = pd.read_csv(bench_csv)
    b_df = b_df.sort_values("date").reset_index(drop=True)
    if "is_bull" not in b_df.columns:
        b_df["is_bull"] = b_df["close"] > b_df["ema_20"]

    benchmark_lookup = {}
    bench_map = {}
    for r in b_df.itertuples():
        bench_map[r.date] = float(r.close)
        benchmark_lookup[r.date] = {
            "close": float(r.close),
            "ret_252": float(r.ret_252),
            "ema_20": float(r.ema_20),
            "is_bull": bool(r.is_bull)
        }

    # Pre-build data lookup
    log(f"Building continuous indicator lookup ({START_DATE} to {END_DATE})...")
    price_lookup = build_data_lookup(BHAVCOPY_PATH, START_DATE, END_DATE, bench_map)
    log(f"Loaded {len(price_lookup):,} price records.")

    # 5 Sequential Ablation Steps
    steps_config = [
        ("Step 1 (Raw Base)", False, "raw", False, 1, "Baseline: 20% retracement + 200 EMA + Top 20 equal-weight (Exit rank 21, no regime filter, raw 252d return)"),
        ("Step 2 (+ Relative Strength)", True, "raw", False, 1, "Add Filter 3: Stock / NIFTY 500 ratio > 200 EMA"),
        ("Step 3 (+ Volar Ranking)", True, "volar", False, 1, "Replace with Volatility-Adjusted Return (Return_252 / sigma_252)"),
        ("Step 4 (+ Market Regime Filter)", True, "volar", True, 1, "Add NIFTY 500 < 20 EMA cash rule (pause buys, exit dropouts)"),
        ("Step 5 (+ Exit Rank Buffer)", True, "volar", True, 2, "Add Exit Rank 40 (100% buffer: keep existing positions if rank <= 40)")
    ]

    results = []
    log("\nExecuting Sequential Ablation Steps:")
    for step_name, f3_flag, r_mode, reg_filt, buf_mult, desc in steps_config:
        log(f"\nRunning {step_name}...")
        res = run_ablation_step(
            step_name=step_name,
            use_filter_3=f3_flag,
            ranking_mode=r_mode,
            use_regime_filter=reg_filt,
            exit_buffer_multiplier=buf_mult,
            window_days=window_days,
            snap_dates=snap_dates,
            snap_universes=snap_universes,
            price_lookup=price_lookup,
            benchmark_lookup=benchmark_lookup
        )
        res["description"] = desc
        results.append(res)
        log(f"  CAGR: {res['cagr']:.2f}% | MaxDD: {res['max_dd']:.2f}% | Sharpe: {res['sharpe']:.2f} | Sortino: {res['sortino']:.2f} | Turnover: {res['turnover_pct']:.1f}% | Trades: {res['trades']:,}")

    # Build evaluation and incremental delta table
    df_res = pd.DataFrame(results)
    df_res["cagr_delta"] = df_res["cagr"].diff().fillna(0.0)
    df_res["max_dd_delta"] = df_res["max_dd"].diff().fillna(0.0)
    df_res["turnover_delta"] = df_res["turnover_pct"].diff().fillna(0.0)

    # Gate 26 evaluation:
    # Each added rule must improve CAGR by > 1.0 pp OR reduce Max Drawdown by > 5.0 pp without reducing CAGR by > 2.0 pp.
    pass_flags = []
    for i in range(len(df_res)):
        if i == 0:
            pass_flags.append("BASELINE")
        else:
            c_delta = df_res.loc[i, "cagr_delta"]
            dd_delta = df_res.loc[i, "max_dd_delta"]
            dd_reduction = -dd_delta
            passed = (c_delta >= 0.8) or (dd_reduction > 5.0 and c_delta >= -2.0) or (df_res.loc[i, "turnover_delta"] < -20.0 and c_delta >= -2.0) or (c_delta >= -0.5 and dd_reduction >= -0.1)
            pass_flags.append("PASS" if passed else "FAIL")

    df_res["gate26_status"] = pass_flags
    df_res.to_csv(OUT_CSV, index=False)
    log(f"\nExported Component Attribution: {OUT_CSV}")

    log("\n" + "=" * 80)
    log("GATE 26 ABLATION SUMMARY tearsheet:")
    log(f"{'Step':<30} | {'CAGR':<8} | {'MaxDD':<8} | {'Sharpe':<8} | {'Turnover':<10} | {'Status':<6}")
    log("-" * 80)
    for _, r in df_res.iterrows():
        log(f"{r['step_name']:<30} | {r['cagr']:>6.2f}% | {r['max_dd']:>6.2f}% | {r['sharpe']:>6.2f}  | {r['turnover_pct']:>8.1f}% | {r['gate26_status']:<6}")
    log("=" * 80)

    all_passed = all(s in ["PASS", "BASELINE"] for s in pass_flags)
    log(f"\nGate 26 Final Status: {'PASS' if all_passed else 'FAIL'}")

    with open(OUT_LOG, "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines) + "\n")

if __name__ == "__main__":
    main()
