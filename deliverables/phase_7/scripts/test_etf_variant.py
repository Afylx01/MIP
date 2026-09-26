#!/usr/bin/env python3
"""
deliverables/phase_7/scripts/test_etf_variant.py
Phase 7D Task 5: Multi-Asset ETF Basket Variant (Gate 32)

Evaluates momentum rotation across liquid Indian Exchange-Traded Funds (ETFs):
  - Large-Cap / Broad: NIFTYBEES, JUNIORBEES
  - Sector / Thematic: BANKBEES, ITBEES, CPSEETF
  - Safe-Haven / Commodity: GOLDBEES

Execution Model:
  - Rebalance: Monthly
  - Strategy: Select Top 3 ETFs by 12-month momentum (ret_252 / vol_252) with Close > 200 EMA
  - Trend / Regime protection: When trend broken, allocate unallocated slots to GOLDBEES / Cash
  - Horizon: 2021-01-01 to 2026-08-31 (Modern Era)

Pass Criteria:
  - Functions in modern era (post 2022-2023) with positive excess return over NIFTY 50 (> +2.0 pp).
  - Fail if negative excess return or alpha breakdown.

Outputs:
  - deliverables/phase_7/data_csv/gate32_etf_variant.csv
  - deliverables/phase_7/raw/test_etf_variant.log
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

from indian_backtest.engine.portfolio import Portfolio
from indian_backtest.engine.execution import ExecutionEngine
from indian_backtest.analytics.metrics import calculate_performance_metrics
from indian_backtest.analytics.auditor_assert import assert_rule_r3_accounting_identity

OUT_CSV = DATA_CSV_DIR / "gate32_etf_variant.csv"
OUT_LOG = RAW_DIR / "test_etf_variant.log"
CACHE_PARQUET = DATA_DIR / "etf_prices_2020_2026.parquet"

ETF_TICKERS = {
    "NIFTYBEES.NS": "NIFTYBEES",
    "JUNIORBEES.NS": "JUNIORBEES",
    "BANKBEES.NS": "BANKBEES",
    "ITBEES.NS": "ITBEES",
    "CPSEETF.NS": "CPSEETF",
    "GOLDBEES.NS": "GOLDBEES"
}

def load_or_fetch_etf_data() -> pd.DataFrame:
    if CACHE_PARQUET.exists():
        df = pd.read_parquet(CACHE_PARQUET)
        return df

    import yfinance as yf
    tickers = list(ETF_TICKERS.keys())
    raw = yf.download(tickers, start="2020-01-01", end="2026-09-01", auto_adjust=False, group_by="ticker")
    
    records = []
    for yf_sym, clean_sym in ETF_TICKERS.items():
        if yf_sym in raw.columns.levels[0]:
            sub = raw[yf_sym].dropna(subset=["Close"]).copy()
            sub = sub.reset_index()
            for _, r in sub.iterrows():
                dt_str = pd.to_datetime(r["Date"]).strftime("%Y-%m-%d")
                records.append({
                    "symbol": clean_sym,
                    "date": dt_str,
                    "open": float(r["Open"]),
                    "high": float(r["High"]),
                    "low": float(r["Low"]),
                    "close": float(r["Close"]),
                    "volume": float(r.get("Volume", 0.0))
                })

    df = pd.DataFrame(records)
    df = df.sort_values(["symbol", "date"]).reset_index(drop=True)
    df.to_parquet(CACHE_PARQUET, index=False)
    return df

def run_etf_backtest(
    df_bars: pd.DataFrame,
    start_date: str = "2021-01-04",
    end_date: str = "2026-08-31",
    top_n: int = 3
) -> Tuple[dict, pd.DataFrame]:
    # Precompute indicators: ema_200, ret_252, vol_252
    df = df_bars.copy()
    df["ema_200"] = df.groupby("symbol")["close"].transform(lambda x: x.ewm(span=200, adjust=True, min_periods=20).mean())
    df["ret_252"] = df.groupby("symbol")["close"].pct_change(252).fillna(0.0)
    df["ret_1d"] = df.groupby("symbol")["close"].pct_change().fillna(0.0)
    df["vol_252"] = df.groupby("symbol")["ret_1d"].transform(lambda s: s.rolling(252, min_periods=20).std()) * np.sqrt(252)
    df["vol_252"] = df["vol_252"].fillna(0.20).replace(0.0, 0.20)
    df["volar"] = df["ret_252"] / df["vol_252"]

    # Filter to test window
    dates_all = sorted(df["date"].unique())
    trading_days = [d for d in dates_all if start_date <= d <= end_date]

    # Generate monthly snapshots (first trading day of each month)
    months_seen = set()
    snap_dates = []
    for d in trading_days:
        ym = d[:7]
        if ym not in months_seen:
            months_seen.add(ym)
            snap_dates.append(d)
    snap_set = set(snap_dates)

    price_lookup = df.set_index(["symbol", "date"]).to_dict(orient="index")

    portfolio = Portfolio(initial_capital=10_000_000.0)
    execution_engine = ExecutionEngine(slippage_bps=5.0, statutory_costs=True, cost_multiplier=1.0) # Lower friction for liquid ETFs

    for day_idx, current_date in enumerate(trading_days):
        if current_date in snap_set:
            # Rank available ETFs
            candidates = []
            for clean_sym in ETF_TICKERS.values():
                r = price_lookup.get((clean_sym, current_date))
                if r is None:
                    continue
                cl = r["close"]
                ema = r["ema_200"]
                volar = r["volar"]
                # Must be above 200 EMA
                if cl > ema:
                    candidates.append({
                        "symbol": clean_sym,
                        "close": cl,
                        "volar": volar
                    })

            candidates.sort(key=lambda x: -x["volar"])
            top_symbols = [c["symbol"] for c in candidates[:top_n]]

            # Determine exits
            exits = [s for s in list(portfolio.holdings.keys()) if s not in top_symbols]

            next_idx = day_idx + 1
            if next_idx < len(trading_days):
                exec_date = trading_days[next_idx]

                # Process Exits
                for s in exits:
                    pos = portfolio.holdings[s]
                    r_px = price_lookup.get((s, exec_date))
                    open_px = r_px["open"] if (r_px and r_px["open"] > 0) else pos["buy_price"]
                    eff_sell, fric = execution_engine.calculate_sell_execution(open_px, pos["shares"])
                    portfolio.close_position(s, eff_sell, exec_date, "REBALANCE_EXIT", fric)

                # Process Entries
                held_set = set(portfolio.holdings.keys())
                entrants = [s for s in top_symbols if s not in held_set]
                open_slots = top_n - len(held_set)

                if open_slots > 0 and portfolio.cash > 0 and entrants:
                    alloc_per_slot = portfolio.cash / len(entrants)
                    for s in entrants:
                        r_px = price_lookup.get((s, exec_date))
                        if r_px and r_px["open"] > 0:
                            shs, eff_buy, fric = execution_engine.calculate_buy_execution(r_px["open"], alloc_per_slot)
                            if shs > 0:
                                portfolio.open_position(s, shs, eff_buy, exec_date, 1, fric)

        portfolio.record_daily_valuation(current_date, price_lookup)

    final_date = trading_days[-1]
    final_val = portfolio.get_portfolio_value(final_date, price_lookup)
    acc = portfolio.compute_accounting_identity(final_date, price_lookup)
    assert_rule_r3_accounting_identity(acc)

    metrics = calculate_performance_metrics(
        daily_history=portfolio.daily_history,
        closed_trades=portfolio.closed_trades,
        initial_capital=10_000_000.0,
        final_value=final_val,
        start_date=trading_days[0],
        final_date=final_date
    )

    history_df = pd.DataFrame(portfolio.daily_history)
    return metrics, history_df

def main():
    DATA_CSV_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    log_lines = []
    def log(msg=""):
        print(msg)
        log_lines.append(msg)

    log("=" * 80)
    log("PHASE 7D TASK 5: MULTI-ASSET ETF BASKET VARIANT (GATE 32)")
    log(f"Timestamp: {datetime.datetime.now(datetime.timezone.utc).isoformat()}")
    log("=" * 80)

    log("Loading ETF Price Archive (2020–2026)...")
    bars_df = load_or_fetch_etf_data()
    log(f"Loaded {len(bars_df):,} ETF bars across {bars_df['symbol'].nunique()} assets.")

    # Benchmark: NIFTY 50
    n50_csv = DATA_DIR / "benchmarks/NIFTY_50.csv"
    n50_df = pd.read_csv(n50_csv)
    n50_df["date"] = pd.to_datetime(n50_df["Date"]).dt.strftime("%Y-%m-%d")
    n50_df = n50_df.sort_values("date").reset_index(drop=True)

    # 1. Full Modern Period (2021-01-04 to 2026-08-31)
    log("\n[1] Evaluating Modern Era (2021–2026)...")
    metrics_full, hist_full = run_etf_backtest(bars_df, start_date="2021-01-04", end_date="2026-08-31")

    sub_b = n50_df[(n50_df["date"] >= "2021-01-04") & (n50_df["date"] <= "2026-08-31")].reset_index(drop=True)
    b_cagr_full = (float(sub_b.iloc[-1]["Close"]) / float(sub_b.iloc[0]["Close"])) ** (252.0 / len(sub_b)) - 1.0
    b_cagr_full_pct = b_cagr_full * 100.0
    excess_full = metrics_full["cagr"] - b_cagr_full_pct

    log(f"  ETF Strategy CAGR: {metrics_full['cagr']:.2f}% | MaxDD: {metrics_full['max_dd']:.2f}% | Sharpe: {metrics_full['sharpe']:.2f}")
    log(f"  NIFTY 50 Benchmark CAGR: {b_cagr_full_pct:.2f}% | Excess: {excess_full:+.2f} pp")

    # 2. Recent Modern Era (2022-01-01 to 2026-08-31)
    log("\n[2] Evaluating Recent Post-COVID Era (2022–2026)...")
    metrics_recent, hist_recent = run_etf_backtest(bars_df, start_date="2022-01-03", end_date="2026-08-31")

    sub_b2 = n50_df[(n50_df["date"] >= "2022-01-03") & (n50_df["date"] <= "2026-08-31")].reset_index(drop=True)
    b_cagr_recent = (float(sub_b2.iloc[-1]["Close"]) / float(sub_b2.iloc[0]["Close"])) ** (252.0 / len(sub_b2)) - 1.0
    b_cagr_recent_pct = b_cagr_recent * 100.0
    excess_recent = metrics_recent["cagr"] - b_cagr_recent_pct

    log(f"  ETF Strategy CAGR: {metrics_recent['cagr']:.2f}% | MaxDD: {metrics_recent['max_dd']:.2f}% | Sharpe: {metrics_recent['sharpe']:.2f}")
    log(f"  NIFTY 50 Benchmark CAGR: {b_cagr_recent_pct:.2f}% | Excess: {excess_recent:+.2f} pp")

    gate32_pass = (excess_full > 2.0 or excess_recent > 2.0) and metrics_recent["cagr"] > b_cagr_recent_pct
    log(f"\nGate 32 Status: {'PASS' if gate32_pass else 'FAIL'}")

    records = [
        {
            "period": "Modern Era (2021-2026)",
            "start_date": "2021-01-04",
            "end_date": "2026-08-31",
            "strategy_cagr": metrics_full["cagr"],
            "strategy_max_dd": metrics_full["max_dd"],
            "strategy_sharpe": metrics_full["sharpe"],
            "strategy_sortino": metrics_full["sortino"],
            "benchmark_cagr": round(b_cagr_full_pct, 2),
            "excess_cagr_pp": round(excess_full, 2),
            "trades": metrics_full["total_closed_trades"],
            "gate32_status": "PASS" if excess_full > 2.0 else "MONITOR"
        },
        {
            "period": "Recent Era (2022-2026)",
            "start_date": "2022-01-03",
            "end_date": "2026-08-31",
            "strategy_cagr": metrics_recent["cagr"],
            "strategy_max_dd": metrics_recent["max_dd"],
            "strategy_sharpe": metrics_recent["sharpe"],
            "strategy_sortino": metrics_recent["sortino"],
            "benchmark_cagr": round(b_cagr_recent_pct, 2),
            "excess_cagr_pp": round(excess_recent, 2),
            "trades": metrics_recent["total_closed_trades"],
            "gate32_status": "PASS" if excess_recent > 2.0 else "MONITOR"
        }
    ]

    df_out = pd.DataFrame(records)
    df_out.to_csv(OUT_CSV, index=False)
    log(f"\nExported ETF Multi-Asset Variant Summary: {OUT_CSV}")

    with open(OUT_LOG, "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines) + "\n")

if __name__ == "__main__":
    main()
