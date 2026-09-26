#!/usr/bin/env python3
"""
deliverables/data_comparison/scripts/run_comparative_backtest.py
Task 5 — Comparative Strategy Backtest Re-Run: Official Bhavcopy vs Yahoo Finance

Executes the identical production momentum strategy (indian_backtest) across 2016–2026 under:
  - Run A: Official NSE Consolidated Bhavcopy (data/adjusted_bhavcopy_max_2007_2026.parquet)
  - Run B: Yahoo Finance OHLCV Dataset (data/yfinance_ohlcv_2007_2026.parquet)

Strategy Specification (Frozen Podcast Engine):
  - Point-in-time NIFTY 500 constituents
  - Rule R2 (Close >= 0.80 * High_252) & Rule R3 (Close > EMA_200)
  - Extension E1: 12-Month Relative Strength Ranking vs NIFTY 500 benchmark
  - Target Portfolio: N = 20 equal-weighted positions
  - Maintenance: Exit rank > 40 or Close < EMA_200
  - Extension E4: 200 EMA Market Regime Cash Filter (halt entries if benchmark < 200 EMA)
  - Execution Rule R8: Next-Day Open with 10 bps slippage + statutory charges

Outputs:
  - deliverables/data_comparison/data_csv/comparative_backtest_delta.csv
  - deliverables/data_comparison/raw/comparative_backtest_log.txt
"""

import sys
import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple
import pandas as pd
import numpy as np

BASE_DIR = Path("/storage/emulated/0/Documents/Project MIP")
DELIV_DIR = BASE_DIR / "deliverables/data_comparison"
DATA_CSV_DIR = DELIV_DIR / "data_csv"
RAW_DIR = DELIV_DIR / "raw"
DATA_DIR = BASE_DIR / "data"

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from indian_backtest.data.bhavcopy_reader import BhavcopyReader
from indian_backtest.data.universe_manager import UniverseManager
from indian_backtest.data.calendar_manager import CalendarManager
from indian_backtest.engine.portfolio import Portfolio
from indian_backtest.engine.rebalancer import Rebalancer
from indian_backtest.engine.execution import ExecutionEngine
from indian_backtest.engine.regime_filter import MarketRegimeFilter
from indian_backtest.analytics.metrics import calculate_performance_metrics
from indian_backtest.analytics.tearsheet import format_strategy_tearsheet
from indian_backtest.analytics.auditor_assert import assert_rule_r3_accounting_identity

BHAVCOPY_PATH = DATA_DIR / "adjusted_bhavcopy_max_2007_2026.parquet"
YFINANCE_PATH = DATA_DIR / "yfinance_ohlcv_2007_2026.parquet"
OUT_CSV = DATA_CSV_DIR / "comparative_backtest_delta.csv"
OUT_LOG = RAW_DIR / "comparative_backtest_log.txt"

START_DATE = "2016-01-04"
END_DATE = "2026-08-31"
INITIAL_CAPITAL = 10_000_000.0
N_PORTFOLIO = 20
EXIT_RANK = 40
SLIPPAGE_BPS = 0.0010  # 10 bps
STATUTORY_COSTS = True

def run_simulation(
    dataset_name: str,
    price_lookup: Dict[Tuple[str, str], dict],
    benchmark_lookup: Dict[str, dict],
    window_days: List[str],
    snap_universes: Dict[str, Set[str]],
    snap_dates: List[str]
) -> dict:
    portfolio = Portfolio(initial_capital=INITIAL_CAPITAL)
    rebalancer = Rebalancer(portfolio_size=N_PORTFOLIO, exit_rank_multiplier=2, use_relative_strength=True)
    execution_engine = ExecutionEngine(slippage_bps=10.0, statutory_costs=STATUTORY_COSTS)
    regime_filter = MarketRegimeFilter(enabled=True)

    snap_date_set = set(snap_dates)

    for day_idx, current_date in enumerate(window_days):
        # 1. Monthly rebalance check
        if current_date in snap_date_set:
            u_current = snap_universes.get(current_date, set())
            is_first_day = (day_idx == 0)

            # Market Regime Filter check (Extension E4)
            is_bullish_regime = regime_filter.evaluate_regime(current_date, benchmark_lookup)

            # Candidate signal evaluation & ranking
            pass_candidates, rank_map = rebalancer.evaluate_candidates(
                universe_symbols=u_current,
                current_date=current_date,
                price_lookup=price_lookup,
                benchmark_lookup=benchmark_lookup,
                is_first_day=is_first_day
            )

            # Maintenance & exits
            exits, retained = rebalancer.determine_exits(
                current_holdings=portfolio.holdings,
                universe_symbols=u_current,
                current_date=current_date,
                price_lookup=price_lookup,
                rank_map=rank_map
            )

            # Rule R8: Next-Day Open Execution
            next_day_idx = day_idx + 1
            if next_day_idx < len(window_days):
                exec_date = window_days[next_day_idx]

                # Process Exits at Next-Day Open
                for sym, reason in exits:
                    pos = portfolio.holdings[sym]
                    exec_row = price_lookup.get((sym, exec_date))
                    open_px = exec_row["open"] if (exec_row and exec_row["open"] > 0) else pos["buy_price"]
                    effective_sell_px, sell_friction = execution_engine.calculate_sell_execution(open_px, pos["shares"])
                    portfolio.close_position(sym, effective_sell_px, exec_date, reason, sell_friction)

                # Process Entries for Open Slots
                open_slots = N_PORTFOLIO - len(retained)
                if open_slots > 0 and portfolio.cash > 0 and is_bullish_regime:
                    entrants = [c["symbol"] for c in pass_candidates if c["symbol"] not in retained][:open_slots]
                    if entrants:
                        cash_per_stock = portfolio.cash / len(entrants)
                        for sym in entrants:
                            exec_row = price_lookup.get((sym, exec_date))
                            if exec_row and exec_row["open"] > 0:
                                open_px = exec_row["open"]
                                shs, eff_buy_px, buy_friction = execution_engine.calculate_buy_execution(open_px, cash_per_stock)
                                if shs > 0:
                                    sym_rank = rank_map.get(sym, 1)
                                    portfolio.open_position(sym, shs, eff_buy_px, exec_date, sym_rank, buy_friction)

        # 2. Daily valuation
        portfolio.record_daily_valuation(current_date, price_lookup)

    final_date = window_days[-1]
    final_val = portfolio.get_portfolio_value(final_date, price_lookup)
    acc_identity = portfolio.compute_accounting_identity(final_date, price_lookup)
    assert_rule_r3_accounting_identity(acc_identity)

    perf_metrics = calculate_performance_metrics(
        daily_history=portfolio.daily_history,
        closed_trades=portfolio.closed_trades,
        initial_capital=INITIAL_CAPITAL,
        final_value=final_val,
        start_date=window_days[0],
        final_date=final_date
    )
    return {
        "dataset_name": dataset_name,
        "portfolio": portfolio,
        "acc_identity": acc_identity,
        "metrics": perf_metrics
    }

def main():
    DATA_CSV_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    log_lines = []
    def log(msg=""):
        print(msg)
        log_lines.append(msg)

    log("=" * 80)
    log("TASK 5: COMPARATIVE MOMENTUM BACKTEST (BHAVCOPY VS YFINANCE)")
    log(f"Timestamp: {datetime.datetime.now(datetime.timezone.utc).isoformat()}")
    log("=" * 80)

    # 1. Trading Calendar & Point-in-Time Universe
    cal_mgr = CalendarManager(base_dir=BASE_DIR)
    window_days = cal_mgr.get_trading_days(START_DATE, END_DATE)
    snap_dates = cal_mgr.get_monthly_rebalance_snapshots(START_DATE, END_DATE)

    u_mgr = UniverseManager(base_dir=BASE_DIR)
    snap_universes = u_mgr.get_all_snapshot_universes(snap_dates)

    log(f"Trading Days:         {len(window_days):,} days ({START_DATE} to {END_DATE})")
    log(f"Rebalance Snapshots:  {len(snap_dates):,} monthly snapshots")

    # Benchmark Index Series
    reader_base = BhavcopyReader(base_dir=BASE_DIR)
    idx_df = reader_base.load_benchmark_index()
    benchmark_lookup = idx_df.set_index("date").to_dict(orient="index")

    # 2. RUN A: Official Consolidated Bhavcopy
    log("\n--- Executing RUN A: Official NSE Consolidated Bhavcopy ---")
    reader_bhav = BhavcopyReader(base_dir=BASE_DIR, custom_path=BHAVCOPY_PATH)
    lookup_bhav = reader_bhav.get_price_lookup(START_DATE, END_DATE)
    res_a = run_simulation(
        dataset_name="Official NSE Bhavcopy",
        price_lookup=lookup_bhav,
        benchmark_lookup=benchmark_lookup,
        window_days=window_days,
        snap_universes=snap_universes,
        snap_dates=snap_dates
    )
    tearsheet_a = format_strategy_tearsheet(
        "Run A: Official NSE Bhavcopy",
        res_a["metrics"],
        res_a["acc_identity"],
        sample_trades=res_a["portfolio"].closed_trades,
        held_positions=res_a["portfolio"].holdings
    )
    log(tearsheet_a)

    # 3. RUN B: Yahoo Finance OHLCV
    log("\n--- Executing RUN B: Yahoo Finance OHLCV ---")
    reader_yf = BhavcopyReader(base_dir=BASE_DIR, custom_path=YFINANCE_PATH)
    lookup_yf = reader_yf.get_price_lookup(START_DATE, END_DATE)
    res_b = run_simulation(
        dataset_name="Yahoo Finance OHLCV",
        price_lookup=lookup_yf,
        benchmark_lookup=benchmark_lookup,
        window_days=window_days,
        snap_universes=snap_universes,
        snap_dates=snap_dates
    )
    tearsheet_b = format_strategy_tearsheet(
        "Run B: Yahoo Finance OHLCV",
        res_b["metrics"],
        res_b["acc_identity"],
        sample_trades=res_b["portfolio"].closed_trades,
        held_positions=res_b["portfolio"].holdings
    )
    log(tearsheet_b)

    # 4. Compare Performance Deltas
    log("\n--- Performance Divergence & Delta Analysis ---")
    ma = res_a["metrics"]
    mb = res_b["metrics"]

    cagr_a = ma["cagr"]
    cagr_b = mb["cagr"]
    delta_cagr = cagr_b - cagr_a

    maxdd_a = ma["max_dd"]
    maxdd_b = mb["max_dd"]
    delta_maxdd = maxdd_b - maxdd_a

    trades_a = ma["total_closed_trades"]
    trades_b = mb["total_closed_trades"]
    delta_trades = trades_b - trades_a

    delta_rows = [
        {"metric": "Data Source", "run_a_bhavcopy": "Official NSE Bhavcopy", "run_b_yfinance": "Yahoo Finance (yfinance)", "delta": "N/A", "interpretation": "Ground truth vs Public web source"},
        {"metric": "Initial Capital (INR)", "run_a_bhavcopy": f"{INITIAL_CAPITAL:,.2f}", "run_b_yfinance": f"{INITIAL_CAPITAL:,.2f}", "delta": "0.00", "interpretation": "Identical initial conditions"},
        {"metric": "Final Portfolio Value (INR)", "run_a_bhavcopy": f"{res_a['acc_identity']['final_value']:,.2f}", "run_b_yfinance": f"{res_b['acc_identity']['final_value']:,.2f}", "delta": f"{res_b['acc_identity']['final_value'] - res_a['acc_identity']['final_value']:,.2f}", "interpretation": "Wealth accumulation delta"},
        {"metric": "Net Profit (INR)", "run_a_bhavcopy": f"{res_a['acc_identity']['net_profit']:,.2f}", "run_b_yfinance": f"{res_b['acc_identity']['net_profit']:,.2f}", "delta": f"{res_b['acc_identity']['net_profit'] - res_a['acc_identity']['net_profit']:,.2f}", "interpretation": "Absolute profit delta"},
        {"metric": "CAGR (%)", "run_a_bhavcopy": f"{cagr_a:.2f}%", "run_b_yfinance": f"{cagr_b:.2f}%", "delta": f"{delta_cagr:+.2f} pp", "interpretation": "Survivorship / dividend distortion in CAGR"},
        {"metric": "Max Drawdown (%)", "run_a_bhavcopy": f"{maxdd_a:.2f}%", "run_b_yfinance": f"{maxdd_b:.2f}%", "delta": f"{delta_maxdd:+.2f} pp", "interpretation": "Downside risk discrepancy"},
        {"metric": "Sharpe Ratio", "run_a_bhavcopy": f"{ma['sharpe']:.2f}", "run_b_yfinance": f"{mb['sharpe']:.2f}", "delta": f"{mb['sharpe'] - ma['sharpe']:+.2f}", "interpretation": "Risk-adjusted return delta"},
        {"metric": "Sortino Ratio", "run_a_bhavcopy": f"{ma['sortino']:.2f}", "run_b_yfinance": f"{mb['sortino']:.2f}", "delta": f"{mb['sortino'] - ma['sortino']:+.2f}", "interpretation": "Downside volatility ratio delta"},
        {"metric": "Total Closed Trades", "run_a_bhavcopy": f"{trades_a}", "run_b_yfinance": f"{trades_b}", "delta": f"{delta_trades:+d}", "interpretation": "Trade count divergence due to missing scrips"},
        {"metric": "Win Rate (%)", "run_a_bhavcopy": f"{ma['win_rate_pct']:.2f}%", "run_b_yfinance": f"{mb['win_rate_pct']:.2f}%", "delta": f"{mb['win_rate_pct'] - ma['win_rate_pct']:+.2f} pp", "interpretation": "Trade outcome accuracy"},
        {"metric": "Profit Factor", "run_a_bhavcopy": f"{ma['profit_factor']:.2f}", "run_b_yfinance": f"{mb['profit_factor']:.2f}", "delta": f"{mb['profit_factor'] - ma['profit_factor']:+.2f}", "interpretation": "Gross profit / loss ratio"},
        {"metric": "Avg Holding Period (Days)", "run_a_bhavcopy": f"{ma['avg_holding_days']:.1f}", "run_b_yfinance": f"{mb['avg_holding_days']:.1f}", "delta": f"{mb['avg_holding_days'] - ma['avg_holding_days']:+.1f}", "interpretation": "Holding duration alignment"},
        {"metric": "Rule R-3 Residual", "run_a_bhavcopy": f"{res_a['acc_identity']['residual']:.10f}", "run_b_yfinance": f"{res_b['acc_identity']['residual']:.10f}", "delta": "0.00", "interpretation": "Strict accounting identity satisfied"}
    ]

    delta_df = pd.DataFrame(delta_rows)
    delta_df.to_csv(OUT_CSV, index=False)
    log(f"\nExported comparative backtest delta table: {OUT_CSV}")

    log("\n" + "=" * 80)
    log("TASK 5 COMPLETE: COMPARATIVE BACKTEST FINISHED (PASS)")
    log("=" * 80)

    with open(OUT_LOG, "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines) + "\n")

if __name__ == "__main__":
    main()
