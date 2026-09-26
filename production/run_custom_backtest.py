#!/usr/bin/env python3
"""
production/run_custom_backtest.py
Interactive Custom Strategy Backtester for Project MIP.

Allows operators to interactively parameterize and run quantitative backtests:
  1. Start Date [Default: 2016-01-01]
  2. End Date [Default: 2026-08-31]
  3. Portfolio Size (Top N) [Default: 20]
  4. Ranking Metric [1: Volar Score (Default), 2: Raw 252d Return]
  5. Exit Buffer Rank [Default: 40]
  6. Market Regime Filter (Pause entries if NIFTY 500 < 20 EMA) [Y/n, Default: Y]
  7. Friction Tier [1: 1x Real Institutional Costs, 2: 2x Stress, 3: 3x Extreme]
  8. Initial Capital in INR [Default: 10,000,000 (₹1 Crore)]

Outputs:
  - Instant institutional terminal tearsheet
  - reports/custom_backtest_results.csv (Summary statistics)
  - reports/custom_backtest_trades.csv (Trade execution logs)
  - reports/custom_backtest_equity.csv (Daily equity curve)
"""

import sys
import os
import argparse
import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
import pandas as pd
import numpy as np

def get_base_dir() -> Path:
    """Dynamically resolves Project MIP root across Windows and Linux."""
    if "PROJECT_MIP_DIR" in os.environ and Path(os.environ["PROJECT_MIP_DIR"]).exists():
        return Path(os.environ["PROJECT_MIP_DIR"])
    android_path = Path("/storage/emulated/0/Documents/Project MIP")
    if android_path.exists():
        return android_path
    cur = Path(__file__).resolve()
    for p in [cur] + list(cur.parents):
        if (p / "run_mip.py").exists() or (p / "data/universe").exists():
            return p
    return cur.parent.parent if cur.parent.name in ["production", "scripts"] else cur.parent


BASE_DIR = get_base_dir()
DATA_DIR = BASE_DIR / "data"
UNIVERSE_PARQUET = DATA_DIR / "universe/nifty500_pit_universe.parquet"
BENCHMARK_CSV = BASE_DIR / "deliverables/phase_7/data_csv/nifty_500_benchmark_proxy.csv"
REPORTS_DIR = BASE_DIR / "reports"

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from indian_backtest.data.calendar_manager import CalendarManager
from indian_backtest.data.universe_manager import UniverseManager
from indian_backtest.engine.portfolio import Portfolio
from indian_backtest.engine.execution import ExecutionEngine
from indian_backtest.indicators.price_extremes import is_r2_satisfied
from indian_backtest.analytics.metrics import calculate_performance_metrics
from indian_backtest.analytics.auditor_assert import assert_rule_r3_accounting_identity


def log(msg: str):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [CustomBacktester] {msg}")


def prompt_user_input() -> dict:
    """Interactively prompts operator for backtest parameters with formatted defaults."""
    print("\n" + "=" * 76)
    print("🧪  PROJECT MIP — INTERACTIVE CUSTOM STRATEGY BACKTESTER")
    print("Configure your quantitative simulation parameters below (Press ENTER for Default):")
    print("=" * 76 + "\n")

    # 1. Start Date
    start_in = input("1. Start Date [YYYY-MM-DD, Default: 2016-01-01]: ").strip()
    start_date = start_in if start_in else "2016-01-01"

    # 2. End Date
    end_in = input("2. End Date   [YYYY-MM-DD, Default: 2026-08-31]: ").strip()
    end_date = end_in if end_in else "2026-08-31"

    # 3. Portfolio Size Top N
    top_in = input("3. Portfolio Size (Top N holdings) [Default: 20]: ").strip()
    top_n = int(top_in) if top_in else 20

    # 4. Ranking Metric
    metric_in = input("4. Ranking Metric [1: Volar Score (Default), 2: Raw 252d Return]: ").strip()
    use_volar = (metric_in != "2")

    # 5. Exit Buffer Rank
    buf_in = input(f"5. Exit Buffer Rank Cutoff [Default: 40, recommended 2x Top-N]: ").strip()
    exit_buffer = int(buf_in) if buf_in else (top_n * 2)

    # 6. Market Regime Filter
    reg_in = input("6. Market Regime Filter (Pause entries if NIFTY 500 < 20 EMA) [Y/n, Default: Y]: ").strip().lower()
    regime_active = (reg_in not in ["n", "no", "false", "0"])

    # 7. Friction Tier
    fric_in = input("7. Friction Tier [1: 1x Real Costs (Default), 2: 2x Stress, 3: 3x Extreme]: ").strip()
    friction_mult = float(fric_in) if fric_in in ["1", "2", "3"] else 1.0

    # 8. Initial Capital
    cap_in = input("8. Initial Capital in INR [Default: 10000000 (₹1 Crore)]: ").strip()
    capital = float(cap_in) if cap_in else 10_000_000.0

    return {
        "start_date": start_date,
        "end_date": end_date,
        "top_n": top_n,
        "use_volar": use_volar,
        "exit_buffer": exit_buffer,
        "regime_active": regime_active,
        "friction_mult": friction_mult,
        "capital": capital,
    }


def run_custom_backtest(
    start_date: str = "2016-01-01",
    end_date: str = "2026-08-31",
    top_n: int = 20,
    use_volar: bool = True,
    exit_buffer: int = 40,
    regime_active: bool = True,
    friction_mult: float = 1.0,
    capital: float = 10_000_000.0,
) -> dict:
    """Executes institutional momentum backtest with specified configuration."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    log("=" * 76)
    log("INITIALIZING CUSTOM MOMENTUM SIMULATION")
    log(f"  Period:        {start_date} to {end_date}")
    log(f"  Portfolio:     Top {top_n} slots | Exit Buffer: Rank {exit_buffer}")
    log(f"  Ranking:       {'Volar Score (Ret_252 / Vol_252)' if use_volar else 'Raw 252-day Return'}")
    log(f"  Market Filter: {'Active (NIFTY 500 >= 20 EMA)' if regime_active else 'Disabled (Always 100% Invested)'}")
    log(f"  Friction:      {friction_mult:.1f}x Institutional Tariff (STT, Stamp, GST, 10bps Slippage)")
    log(f"  Capital:       ₹{capital:,.2f}")
    log("=" * 76)

    # 1. Trading Calendar and Snapshot Dates
    cal_mgr = CalendarManager(base_dir=BASE_DIR, use_bhavcopy_calendar=True)
    all_trading_days = cal_mgr.get_trading_days(start_date, end_date)
    if not all_trading_days:
        raise ValueError(f"No trading days found between {start_date} and {end_date}")

    snap_dates = cal_mgr.get_monthly_rebalance_snapshots(start_date, end_date)
    snap_set = set(snap_dates)
    log(f"Identified {len(all_trading_days):,} trading sessions and {len(snap_dates):,} rebalance cycles.")

    # 2. Point-in-Time Universe
    univ_mgr = UniverseManager(base_dir=BASE_DIR)
    snap_universes = univ_mgr.get_all_snapshot_universes(snap_dates)

    # 3. Load Benchmark Proxy
    log("Ingesting continuous NIFTY 500 benchmark series...")
    b_df = pd.read_csv(BENCHMARK_CSV)
    b_df["date"] = b_df["date"].astype(str)
    b_df["is_bull_20"] = b_df["close"] >= b_df["ema_20"]
    bench_lookup = {}
    for r in b_df.itertuples():
        bench_lookup[r.date] = {
            "close": float(r.close),
            "ret_252": float(r.ret_252) if hasattr(r, "ret_252") else 0.0,
            "is_bull_20": bool(r.is_bull_20),
        }

    # Benchmark CAGR over period
    b_start_rows = b_df[b_df["date"] >= start_date]
    b_start_px = float(b_start_rows.iloc[0]["close"]) if not b_start_rows.empty else 1.0
    b_end_rows = b_df[b_df["date"] <= end_date]
    b_end_px = float(b_end_rows.iloc[-1]["close"]) if not b_end_rows.empty else 1.0
    sim_years = (pd.to_datetime(end_date) - pd.to_datetime(start_date)).days / 365.25
    bench_cagr = ((b_end_px / b_start_px) ** (1.0 / sim_years) - 1.0) * 100.0 if sim_years > 0 else 0.0

    # 4. Load Universe Bars (With Warmup)
    warmup_start = (pd.to_datetime(start_date) - datetime.timedelta(days=400)).strftime("%Y-%m-%d")
    log(f"Loading universe parquet bars from {warmup_start} to {end_date}...")
    bars = pd.read_parquet(
        UNIVERSE_PARQUET,
        filters=[("date", ">=", warmup_start), ("date", "<=", end_date)],
        columns=["date", "symbol", "open", "high", "low", "close", "volume"]
    )
    bars = bars.sort_values(by=["symbol", "date"]).reset_index(drop=True)
    log(f"Loaded {len(bars):,} bars across {bars['symbol'].nunique():,} symbols.")

    # 5. Technical Indicators
    log("Computing technical indicators (52w High, 200 EMA, Returns, Volatility)...")
    bars["high_252"] = bars.groupby("symbol")["high"].transform(
        lambda s: s.rolling(252, min_periods=50).max()
    )
    bars["ema_200"] = bars.groupby("symbol")["close"].transform(
        lambda s: s.ewm(span=200, adjust=True, min_periods=50).mean()
    )
    bars["ret_252"] = bars.groupby("symbol")["close"].transform(
        lambda s: s / s.shift(252) - 1.0
    )
    bars["ret_1d"] = bars.groupby("symbol")["close"].pct_change().fillna(0.0)
    bars["vol_252"] = bars.groupby("symbol")["ret_1d"].transform(
        lambda s: s.rolling(252, min_periods=20).std() * np.sqrt(252)
    ).fillna(0.30).replace(0.0, 0.30)

    # Filter bars to simulation window
    sim_bars = bars[(bars["date"] >= start_date) & (bars["date"] <= end_date)].copy()

    # Fast Price Lookup dictionary
    log("Building high-speed memory price cache...")
    sym_arr = sim_bars["symbol"].to_numpy()
    dt_arr = sim_bars["date"].to_numpy()
    op_arr = sim_bars["open"].to_numpy()
    cl_arr = sim_bars["close"].to_numpy()
    hi_arr = sim_bars["high_252"].to_numpy()
    em_arr = sim_bars["ema_200"].to_numpy()
    rt_arr = sim_bars["ret_252"].to_numpy()
    vl_arr = sim_bars["vol_252"].to_numpy()

    price_lookup: Dict[Tuple[str, str], dict] = {}
    for i in range(len(sym_arr)):
        price_lookup[(sym_arr[i], dt_arr[i])] = {
            "open": op_arr[i],
            "close": cl_arr[i],
            "high_252": hi_arr[i],
            "ema_200": em_arr[i],
            "ret_252": rt_arr[i],
            "vol_252": vl_arr[i],
        }

    # 6. Execution Simulation Loop
    log("Simulating strategy execution...")
    portfolio = Portfolio(initial_capital=capital)
    execution_engine = ExecutionEngine(
        slippage_bps=10.0 * friction_mult,
        statutory_costs=True,
        cost_multiplier=friction_mult
    )

    total_turnover = 0.0
    total_trades = 0

    for day_idx, current_date in enumerate(all_trading_days):
        if current_date in snap_set:
            u_current = snap_universes.get(current_date, set())
            b_info = bench_lookup.get(current_date, {})
            is_bull = b_info.get("is_bull_20", True) if regime_active else True

            # Evaluate Candidates
            candidates = []
            for sym in u_current:
                row = price_lookup.get((sym, current_date))
                if row is None or np.isnan(row["close"]):
                    continue

                cl = row["close"]
                hi = row["high_252"] if not np.isnan(row["high_252"]) else cl
                ema = row["ema_200"] if not np.isnan(row["ema_200"]) else cl
                ret_raw = row["ret_252"] if not np.isnan(row["ret_252"]) else 0.0
                vol = row["vol_252"] if not np.isnan(row["vol_252"]) else 0.30

                r2_pass = is_r2_satisfied(cl, hi, 0.80)
                r3_pass = (cl > ema)

                if use_volar:
                    rank_score = ret_raw / max(vol, 0.05)
                else:
                    rank_score = ret_raw

                candidates.append({
                    "symbol": sym,
                    "rank_score": rank_score,
                    "r2_pass": r2_pass,
                    "r3_pass": r3_pass
                })

            candidates.sort(key=lambda x: (-x["rank_score"], x["symbol"]))
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
                if row is None or np.isnan(row["close"]):
                    exits.append((sym, "NO_DATA"))
                    continue

                cl = row["close"]
                hi = row["high_252"] if not np.isnan(row["high_252"]) else cl
                ema = row["ema_200"] if not np.isnan(row["ema_200"]) else cl
                rank = rank_map.get(sym, 999999)

                if not is_r2_satisfied(cl, hi, 0.80):
                    exits.append((sym, "STOP_52W_HIGH_RETRACEMENT"))
                elif cl < ema:
                    exits.append((sym, "STOP_200_EMA_BREAK"))
                elif rank > exit_buffer:
                    exits.append((sym, f"DROPOUT_RANK_{rank}"))
                else:
                    retained.add(sym)

            next_idx = day_idx + 1
            if next_idx < len(all_trading_days):
                exec_date = all_trading_days[next_idx]

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
                open_slots = top_n - len(retained)
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

    final_date = all_trading_days[-1]
    final_val = portfolio.get_portfolio_value(final_date, price_lookup)
    acc = portfolio.compute_accounting_identity(final_date, price_lookup)
    assert_rule_r3_accounting_identity(acc)

    metrics = calculate_performance_metrics(
        daily_history=portfolio.daily_history,
        closed_trades=portfolio.closed_trades,
        initial_capital=capital,
        final_value=final_val,
        start_date=all_trading_days[0],
        final_date=final_date
    )

    alpha = metrics["cagr"] - bench_cagr
    total_friction = sum(t.get("total_friction", 0.0) for t in portfolio.closed_trades)

    # Drawdown Duration and Recovery
    eq_df = pd.DataFrame(portfolio.daily_history)
    eq_df["peak"] = eq_df["value"].cummax()
    eq_df["dd"] = (eq_df["value"] - eq_df["peak"]) / eq_df["peak"]

    # Maximum drawdown duration
    dd_days = 0
    max_dd_days = 0
    for dd in eq_df["dd"]:
        if dd < 0:
            dd_days += 1
            if dd_days > max_dd_days:
                max_dd_days = dd_days
        else:
            dd_days = 0

    results = {
        "parameters": {
            "start_date": start_date,
            "end_date": end_date,
            "top_n": top_n,
            "ranking_metric": "Volar Score" if use_volar else "Raw Return",
            "exit_buffer_rank": exit_buffer,
            "regime_filter": "20 EMA Bull" if regime_active else "Off",
            "friction_mult": friction_mult,
            "initial_capital": capital,
        },
        "performance": {
            "strategy_cagr": metrics["cagr"],
            "benchmark_cagr": round(bench_cagr, 2),
            "alpha": round(alpha, 2),
            "sharpe_ratio": metrics["sharpe"],
            "sortino_ratio": metrics["sortino"],
            "calmar_ratio": metrics["calmar"],
            "max_drawdown": metrics["max_dd"],
            "max_underwater_days": max_dd_days,
            "total_trades": len(portfolio.closed_trades),
            "win_rate_pct": metrics["win_rate_pct"],
            "profit_factor": metrics["profit_factor"],
            "avg_holding_days": metrics["avg_holding_days"],
            "final_value": round(final_val, 2),
            "net_profit": round(final_val - capital, 2),
            "total_friction_paid": round(total_friction, 2),
        }
    }

    # Export CSV files
    out_results_csv = REPORTS_DIR / "custom_backtest_results.csv"
    out_trades_csv = REPORTS_DIR / "custom_backtest_trades.csv"
    out_equity_csv = REPORTS_DIR / "custom_backtest_equity.csv"

    # Export Summary Results
    res_flat = {**results["parameters"], **results["performance"]}
    pd.DataFrame([res_flat]).to_csv(out_results_csv, index=False)

    # Export Trades
    if portfolio.closed_trades:
        pd.DataFrame(portfolio.closed_trades).to_csv(out_trades_csv, index=False)

    # Export Equity Curve
    eq_df.to_csv(out_equity_csv, index=False)

    log(f"Exported performance summary to {out_results_csv}")
    log(f"Exported closed trade logs to {out_trades_csv}")
    log(f"Exported daily equity series to {out_equity_csv}")

    # Display Tearsheet
    print_tearsheet(results)

    return results


def print_tearsheet(results: dict):
    """Prints institutional terminal tearsheet."""
    p = results["parameters"]
    m = results["performance"]

    print("\n" + "=" * 78)
    print("🏆  PROJECT MIP — CUSTOM STRATEGY PERFORMANCE TEARSHEET")
    print("=" * 78)
    print(f"Period:            {p['start_date']} to {p['end_date']} | Capital: ₹{p['initial_capital']:,.0f}")
    print(f"Configuration:     Top {p['top_n']} Holdings | Exit Buffer: Rank {p['exit_buffer_rank']} | Metric: {p['ranking_metric']}")
    print(f"Market Filter:     {p['regime_filter']} | Friction: {p['friction_mult']}x Tariff")
    print("-" * 78)
    print("CAPITAL & RETURNS DYNAMICS:")
    print(f"  • Final Portfolio Value:     ₹{m['final_value']:>14,.2f}")
    print(f"  • Net Profit:                ₹{m['net_profit']:>14,.2f}")
    print(f"  • Strategy CAGR:              {m['strategy_cagr']:>13.2f}%")
    print(f"  • NIFTY 500 Benchmark CAGR:   {m['benchmark_cagr']:>13.2f}%")
    print(f"  • Net Annual Alpha:           {m['alpha']:>+13.2f}%")
    print("-" * 78)
    print("RISK-ADJUSTED PERFORMANCE:")
    print(f"  • Annualized Sharpe Ratio:    {m['sharpe_ratio']:>13.2f}")
    print(f"  • Annualized Sortino Ratio:   {m['sortino_ratio']:>13.2f}")
    print(f"  • Calmar Ratio (CAGR / DD):   {m['calmar_ratio']:>13.2f}")
    print(f"  • Maximum Drawdown:           {m['max_drawdown']:>13.2f}%")
    print(f"  • Max Underwater Duration:    {m['max_underwater_days']:>10d} trading days")
    print("-" * 78)
    print("TRADE & FRICTION STATISTICS:")
    print(f"  • Total Closed Trades:        {m['total_trades']:>10d}")
    print(f"  • Win Rate:                   {m['win_rate_pct']:>13.2f}%")
    print(f"  • Profit Factor:              {m['profit_factor']:>13.2f}")
    print(f"  • Avg Holding Duration:       {m['avg_holding_days']:>13.1f} days")
    print(f"  • Total Friction Paid:       ₹{m['total_friction_paid']:>14,.2f}")
    print("=" * 78 + "\n")


def main():
    parser = argparse.ArgumentParser(description="MIP Custom Strategy Backtester")
    parser.add_argument("--batch", action="store_true", help="Run with CLI arguments instead of interactive prompt")
    parser.add_argument("--start-date", type=str, default="2016-01-01")
    parser.add_argument("--end-date", type=str, default="2026-08-31")
    parser.add_argument("--top-n", type=int, default=20)
    parser.add_argument("--metric", type=str, choices=["volar", "return"], default="volar")
    parser.add_argument("--exit-buffer", type=int, default=40)
    parser.add_argument("--regime-filter", action="store_true", default=True)
    parser.add_argument("--friction-tier", type=float, default=1.0)
    parser.add_argument("--capital", type=float, default=10_000_000.0)

    args = parser.parse_args()

    if args.batch or not sys.stdin.isatty():
        run_custom_backtest(
            start_date=args.start_date,
            end_date=args.end_date,
            top_n=args.top_n,
            use_volar=(args.metric == "volar"),
            exit_buffer=args.exit_buffer,
            regime_active=args.regime_filter,
            friction_mult=args.friction_tier,
            capital=args.capital,
        )
    else:
        cfg = prompt_user_input()
        run_custom_backtest(
            start_date=cfg["start_date"],
            end_date=cfg["end_date"],
            top_n=cfg["top_n"],
            use_volar=cfg["use_volar"],
            exit_buffer=cfg["exit_buffer"],
            regime_active=cfg["regime_active"],
            friction_mult=cfg["friction_mult"],
            capital=cfg["capital"],
        )


if __name__ == "__main__":
    main()
