#!/usr/bin/env python3
"""
deliverables/phase_7/scripts/test_parameter_plateau.py
Phase 7B Task 3: Multi-Dimensional Parameter Plateau Sensitivity Grid (Gate 14)

Evaluates 54 parameter combinations across 2016-2026:
  - Retracement Factor: [0.85, 0.80, 0.75] (15%, 20%, 25% filter from 52-week High)
  - EMA Trend Filter: [150, 200, 250] days
  - Ranking Lookback: [126, 189, 252] days (6m, 9m, 12m)
  - Portfolio Size: [15, 20] stocks (exit buffer = 2x size)

Pass Criteria:
  - >= 70.0% of combinations beat Benchmark CAGR by >= +3.0 percentage points.

Outputs:
  - deliverables/phase_7/data_csv/gate14_parameter_plateau_grid.csv
  - deliverables/phase_7/raw/test_parameter_plateau.log
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

OUT_CSV = DATA_CSV_DIR / "gate14_parameter_plateau_grid.csv"
OUT_LOG = RAW_DIR / "test_parameter_plateau.log"

def build_multi_indicator_lookup(bhavcopy_path: Path, start_date: str, end_date: str):
    df = pd.read_parquet(bhavcopy_path)
    df = df[(df["date"] >= start_date) & (df["date"] <= end_date)].copy()
    df = df.sort_values(["symbol", "date"]).reset_index(drop=True)

    # 52-week High
    df["high_252"] = df.groupby("symbol")["close"].transform(lambda s: s.rolling(252, min_periods=1).max())

    # EMAs: 150, 200, 250
    for span in [150, 200, 250]:
        df[f"ema_{span}"] = df.groupby("symbol")["close"].transform(lambda s: s.ewm(span=span, adjust=True, min_periods=1).mean())

    # Lookback Returns: 126, 189, 252
    def calc_ret_k(k):
        def _fn(s):
            n = len(s)
            vals = s.to_numpy()
            prev = vals[np.maximum(0, np.arange(n) - k)]
            with np.errstate(divide="ignore", invalid="ignore"):
                ret = np.where(np.arange(n) > 0, vals / prev - 1.0, 0.0)
            return pd.Series(ret, index=s.index)
        return _fn

    for k in [126, 189, 252]:
        df[f"ret_{k}"] = df.groupby("symbol")["close"].transform(calc_ret_k(k))

    df["day1_ret"] = (df["close"] / df["open"] - 1.0).fillna(0.0)

    price_lookup = df.set_index(["symbol", "date"]).to_dict(orient="index")
    return price_lookup

def run_grid_simulation(
    r2_factor: float,
    ema_period: int,
    lookback_days: int,
    portfolio_size: int,
    exit_multiplier: int,
    window_days: List[str],
    snap_dates: List[str],
    snap_universes: Dict[str, Set[str]],
    price_lookup: Dict,
    benchmark_lookup: Dict
) -> dict:
    portfolio = Portfolio(initial_capital=INITIAL_CAPITAL)
    execution_engine = ExecutionEngine(slippage_bps=10.0, statutory_costs=True, cost_multiplier=1.0)
    regime_filter = MarketRegimeFilter(enabled=True, ema_period=20)
    snap_set = set(snap_dates)
    exit_rank = portfolio_size * exit_multiplier
    ema_col = f"ema_{ema_period}"
    ret_col = f"ret_{lookback_days}"

    for day_idx, current_date in enumerate(window_days):
        if current_date in snap_set:
            u_current = snap_universes.get(current_date, set())
            is_first_day = (day_idx == 0)

            # Benchmark return for RS
            b_ret = 0.0
            if current_date in benchmark_lookup:
                b_ret = benchmark_lookup[current_date].get(f"ret_{lookback_days}", benchmark_lookup[current_date].get("ret_252", 0.0))

            # Candidate evaluation
            candidates = []
            for sym in u_current:
                row = price_lookup.get((sym, current_date))
                if row is None:
                    continue
                cl = row["close"]
                hi = row["high_252"]
                ema = row[ema_col]
                raw_ret = row["day1_ret"] if is_first_day else row[ret_col]

                r2_pass = is_r2_satisfied(cl, hi, r2_factor)
                r3_pass = (cl >= ema) if is_first_day else (cl > ema)
                rank_metric = calculate_relative_strength(raw_ret, b_ret)

                candidates.append({
                    "symbol": sym,
                    "close": cl,
                    "rank_metric": rank_metric,
                    "r2_pass": r2_pass,
                    "r3_pass": r3_pass
                })

            candidates.sort(key=lambda x: (-x["rank_metric"], x["symbol"]))
            rank_map = {c["symbol"]: i + 1 for i, c in enumerate(candidates)}
            pass_candidates = [c for c in candidates if c["r2_pass"] and c["r3_pass"]]

            # Determine exits
            exits = []
            retained = []
            for sym, pos in list(portfolio.holdings.items()):
                row = price_lookup.get((sym, current_date))
                sym_rank = rank_map.get(sym, 9999)

                if sym not in u_current or row is None:
                    exits.append((sym, "universe_exit"))
                elif not is_r2_satisfied(row["close"], row["high_252"], r2_factor):
                    exits.append((sym, "r2_exit"))
                elif row["close"] <= row[ema_col]:
                    exits.append((sym, "r3_exit"))
                elif sym_rank > exit_rank:
                    exits.append((sym, "rank_exit"))
                else:
                    retained.append(sym)

            # Next trading day execution
            next_idx = day_idx + 1
            if next_idx < len(window_days):
                exec_date = window_days[next_idx]

                # Exits
                for sym, reason in exits:
                    pos = portfolio.holdings[sym]
                    r_px = price_lookup.get((sym, exec_date))
                    open_px = r_px["open"] if (r_px and r_px["open"] > 0) else pos["buy_price"]
                    eff_sell, fric = execution_engine.calculate_sell_execution(open_px, pos["shares"])
                    portfolio.close_position(sym, eff_sell, exec_date, reason, fric)

                # Entries
                is_bull = regime_filter.evaluate_regime(current_date, benchmark_lookup)
                open_slots = portfolio_size - len(portfolio.holdings)
                if is_bull and open_slots > 0 and portfolio.cash > 0:
                    entrants = [c["symbol"] for c in pass_candidates if c["symbol"] not in portfolio.holdings][:open_slots]
                    if entrants:
                        slot_capital = portfolio.cash / len(entrants)
                        for sym in entrants:
                            r_px = price_lookup.get((sym, exec_date))
                            if r_px and r_px["open"] > 0:
                                shs, eff_buy, fric = execution_engine.calculate_buy_execution(r_px["open"], slot_capital)
                                if shs > 0:
                                    s_rank = rank_map.get(sym, 1)
                                    portfolio.open_position(sym, shs, eff_buy, exec_date, s_rank, fric)

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
        "total_trades": len(portfolio.closed_trades)
    }

def main():
    DATA_CSV_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    log_lines = []
    def log(msg=""):
        print(msg)
        log_lines.append(msg)

    log("=" * 80)
    log("PHASE 7B TASK 3: MULTI-DIMENSIONAL PARAMETER PLATEAU SENSITIVITY GRID (GATE 14)")
    log(f"Timestamp: {datetime.datetime.now(datetime.timezone.utc).isoformat()}")
    log("=" * 80)

    cal_mgr = CalendarManager(base_dir=BASE_DIR, use_bhavcopy_calendar=True)
    u_mgr = UniverseManager(base_dir=BASE_DIR)
    window_days = cal_mgr.get_trading_days(START_DATE, END_DATE)
    snaps = cal_mgr.get_monthly_rebalance_snapshots(START_DATE, END_DATE)
    snap_universes = u_mgr.get_all_snapshot_universes(snaps)

    log(f"Loading Bhavcopy and precomputing multi-dimensional indicators...")
    price_lookup = build_multi_indicator_lookup(BHAVCOPY_PATH, START_DATE, END_DATE)

    reader = BhavcopyReader(base_dir=BASE_DIR, custom_path=BHAVCOPY_PATH)
    idx_df = reader.load_benchmark_index()
    # Compute benchmark lookback returns
    for k in [126, 189, 252]:
        def calc_ret_k(k):
            def _fn(s):
                n = len(s)
                vals = s.to_numpy()
                prev = vals[np.maximum(0, np.arange(n) - k)]
                with np.errstate(divide="ignore", invalid="ignore"):
                    ret = np.where(np.arange(n) > 0, vals / prev - 1.0, 0.0)
                return pd.Series(ret, index=s.index)
            return _fn
        idx_df[f"ret_{k}"] = calc_ret_k(k)(idx_df["close"])

    benchmark_lookup = idx_df.set_index("date").to_dict(orient="index")

    b_start = benchmark_lookup[window_days[0]]["close"]
    b_end = benchmark_lookup[window_days[-1]]["close"]
    yrs = (pd.to_datetime(window_days[-1]) - pd.to_datetime(window_days[0])).days / 365.25
    b_cagr = (((b_end / b_start) ** (1.0 / yrs)) - 1.0) * 100.0

    log(f"Benchmark Period: {window_days[0]} to {window_days[-1]} ({len(window_days)} trading days)")
    log(f"Benchmark CAGR:   {b_cagr:.2f}%")
    log(f"Pass Threshold:   Strategy CAGR >= Benchmark + 3.0 pp ({b_cagr + 3.0:.2f}%)")
    log("-" * 80)

    # 54 combinations: 3 x 3 x 3 x 2
    r2_factors = [0.85, 0.80, 0.75]
    ema_periods = [150, 200, 250]
    lookback_days_list = [126, 189, 252]
    portfolio_sizes = [15, 20]

    grid_rows = []
    combo_id = 0

    for r2 in r2_factors:
        for ema in ema_periods:
            for lb in lookback_days_list:
                for sz in portfolio_sizes:
                    combo_id += 1
                    res = run_grid_simulation(
                        r2_factor=r2,
                        ema_period=ema,
                        lookback_days=lb,
                        portfolio_size=sz,
                        exit_multiplier=2,
                        window_days=window_days,
                        snap_dates=snaps,
                        snap_universes=snap_universes,
                        price_lookup=price_lookup,
                        benchmark_lookup=benchmark_lookup
                    )
                    m = res["metrics"]
                    acc = res["acc_identity"]
                    s_cagr = m["cagr"]
                    excess = s_cagr - b_cagr
                    beat_thresh = "PASS" if excess >= 3.0 else "FAIL"

                    record = {
                        "combination_id": combo_id,
                        "r2_factor": r2,
                        "retracement_pct": round((1.0 - r2) * 100.0, 1),
                        "ema_trend_days": ema,
                        "lookback_days": lb,
                        "portfolio_size": sz,
                        "exit_rank_buffer": sz * 2,
                        "strategy_cagr_pct": round(s_cagr, 2),
                        "benchmark_cagr_pct": round(b_cagr, 2),
                        "excess_cagr_pp": round(excess, 2),
                        "max_drawdown_pct": round(m["max_dd"], 2),
                        "sharpe_ratio": round(m["sharpe"], 2),
                        "trades_count": res["total_trades"],
                        "beat_threshold": beat_thresh,
                        "rule_r3_residual": acc["residual"]
                    }
                    grid_rows.append(record)
                    log(f"[{combo_id:02d}/54] R2={r2:.2f} EMA={ema} LB={lb} SZ={sz} | Strat: {s_cagr:>5.2f}% | Excess: {excess:>+5.2f} pp | MaxDD: {m['max_dd']:>5.2f}% | {beat_thresh}")

    res_df = pd.DataFrame(grid_rows)
    total_combos = len(res_df)
    pass_count = (res_df["beat_threshold"] == "PASS").sum()
    pass_pct = (pass_count / total_combos * 100.0) if total_combos > 0 else 0.0

    min_excess = res_df["excess_cagr_pp"].min()
    max_excess = res_df["excess_cagr_pp"].max()
    median_excess = res_df["excess_cagr_pp"].median()
    mean_excess = res_df["excess_cagr_pp"].mean()

    log("\n" + "=" * 80)
    log("GATE 14 COMPLIANCE EVALUATION")
    log("=" * 80)
    log(f"  Total Combinations Evaluated: {total_combos}")
    log(f"  Combinations Meeting Threshold: {pass_count} / {total_combos} ({pass_pct:.1f}%) (Pass Threshold: >= 70.0%)")
    log(f"  CAGR Range:                   {res_df['strategy_cagr_pct'].min():.2f}% to {res_df['strategy_cagr_pct'].max():.2f}%")
    log(f"  Excess Alpha Range:           {min_excess:+.2f} pp to {max_excess:+.2f} pp")
    log(f"  Median Excess Alpha:          {median_excess:+.2f} pp")
    log(f"  Mean Excess Alpha:            {mean_excess:+.2f} pp")

    gate14_pass = (pass_pct >= 70.0)
    log(f"  Gate 14 Status:               {'PASS' if gate14_pass else 'FAIL'}")

    res_df.to_csv(OUT_CSV, index=False)
    log(f"\nExported Parameter Plateau Grid: {OUT_CSV}")

    with open(OUT_LOG, "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines) + "\n")

if __name__ == "__main__":
    main()
