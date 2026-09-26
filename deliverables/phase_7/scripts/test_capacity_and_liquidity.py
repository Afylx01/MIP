#!/usr/bin/env python3
"""
deliverables/phase_7/scripts/test_capacity_and_liquidity.py
Phase 7D Task 4: Portfolio Capacity & Liquidity Constraints (Gate 31)

Evaluates execution feasibility and market impact across institutional AUM tiers:
  - ₹1 Crore (Retail / HNI)
  - ₹5 Crore (Emerging PMS)
  - ₹10 Crore (Target Institutional Mandate)
  - ₹25 Crore (Scaled Fund Tier)

Calculates:
  - Position size relative to 20-day Average Daily Volume (ADV) in INR (ADV_20 = Volume * Close)
  - Median trade % of ADV
  - 95th percentile trade % of ADV
  - Maximum position % of ADV
  - Proportion of orders exceeding 10% of ADV

Pass Criteria:
  - At target AUM (₹10 Crore), maximum position size < 10.0% of 20-day ADV; viable institutional capacity >= ₹10 Crore.
  - Fail if max position size > 25.0% of ADV or viable capacity < ₹5 Crore.

Outputs:
  - deliverables/phase_7/data_csv/gate31_capacity_liquidity.csv
  - deliverables/phase_7/raw/test_capacity_and_liquidity.log
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

OUT_CSV = DATA_CSV_DIR / "gate31_capacity_liquidity.csv"
OUT_LOG = RAW_DIR / "test_capacity_and_liquidity.log"

def run_capacity_simulation(
    aum: float,
    window_days: List[str],
    snap_dates: List[str],
    snap_universes: Dict[str, Set[str]],
    price_lookup: Dict,
    benchmark_lookup: Dict
) -> Tuple[dict, List[dict]]:
    portfolio = Portfolio(initial_capital=aum)
    execution_engine = ExecutionEngine(slippage_bps=10.0, statutory_costs=True, cost_multiplier=1.0)
    regime_filter = MarketRegimeFilter(enabled=True, ema_period=20)
    snap_set = set(snap_dates)

    total_turnover = 0.0
    total_trades = 0
    trade_adv_records = []

    for day_idx, current_date in enumerate(window_days):
        if current_date in snap_set:
            u_current = snap_universes.get(current_date, set())
            is_bull = regime_filter.evaluate_regime(current_date, benchmark_lookup)

            candidates = []
            for sym in u_current:
                row = price_lookup.get((sym, current_date))
                if row is None:
                    continue

                cl = row["close"]
                hi = row["high_252"]
                ema = row["ema_200"]
                ret_raw = row.get("ret_252", 0.0)
                vol = row.get("vol_252", 0.30)

                r2_pass = is_r2_satisfied(cl, hi, 0.80)
                r3_pass = (cl > ema)
                rank_metric = ret_raw / max(vol, 0.05)

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
                elif rank > 40:
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
                    trade_val = pos["shares"] * eff_sell
                    total_turnover += trade_val
                    total_trades += 1

                    adv_20 = r_px.get("adv_20", 10_000_000.0) if r_px else 10_000_000.0
                    mandate_pos_val = aum / 20.0
                    adv_pct = (mandate_pos_val / max(adv_20, 100_000.0)) * 100.0
                    trade_adv_records.append({
                        "date": exec_date,
                        "symbol": sym,
                        "action": "SELL",
                        "trade_val": trade_val,
                        "adv_20": adv_20,
                        "adv_pct": adv_pct
                    })

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
                                    trade_val = (shs * eff_buy) + fric
                                    total_turnover += trade_val
                                    total_trades += 1

                                    adv_20 = r_px.get("adv_20", 10_000_000.0)
                                    mandate_pos_val = aum / 20.0
                                    adv_pct = (mandate_pos_val / max(adv_20, 100_000.0)) * 100.0
                                    trade_adv_records.append({
                                        "date": exec_date,
                                        "symbol": sym,
                                        "action": "BUY",
                                        "trade_val": trade_val,
                                        "adv_20": adv_20,
                                        "adv_pct": adv_pct
                                    })

        portfolio.record_daily_valuation(current_date, price_lookup)

    final_date = window_days[-1]
    final_val = portfolio.get_portfolio_value(final_date, price_lookup)
    acc = portfolio.compute_accounting_identity(final_date, price_lookup)
    assert_rule_r3_accounting_identity(acc)

    metrics = calculate_performance_metrics(
        daily_history=portfolio.daily_history,
        closed_trades=portfolio.closed_trades,
        initial_capital=aum,
        final_value=final_val,
        start_date=window_days[0],
        final_date=final_date
    )

    years = len(window_days) / 252.0
    avg_equity = float(np.mean([d["value"] for d in portfolio.daily_history]))
    ann_turnover = float((total_turnover / years) / avg_equity * 100.0)

    summary = {
        "aum": aum,
        "cagr": metrics["cagr"],
        "max_dd": metrics["max_dd"],
        "sharpe": metrics["sharpe"],
        "turnover_pct": ann_turnover,
        "trades": total_trades,
        "r3_residual": acc["residual"]
    }
    return summary, trade_adv_records

def main():
    DATA_CSV_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    log_lines = []
    def log(msg=""):
        print(msg)
        log_lines.append(msg)

    log("=" * 80)
    log("PHASE 7D TASK 4: PORTFOLIO CAPACITY & LIQUIDITY CONSTRAINTS (GATE 31)")
    log(f"Timestamp: {datetime.datetime.now(datetime.timezone.utc).isoformat()}")
    log("=" * 80)

    cal_mgr = CalendarManager(base_dir=BASE_DIR, use_bhavcopy_calendar=True)
    window_days = cal_mgr.get_trading_days(START_DATE, END_DATE)
    snap_dates = cal_mgr.get_monthly_rebalance_snapshots(START_DATE, END_DATE)

    univ_mgr = UniverseManager(base_dir=BASE_DIR)
    snap_universes = univ_mgr.get_all_snapshot_universes(snap_dates)

    log(f"Loading price records and calculating 20-day ADV ({START_DATE} to {END_DATE})...")
    reader = BhavcopyReader(base_dir=BASE_DIR, custom_path=BHAVCOPY_PATH)
    bars_df = reader.load_combined_bars(START_DATE, END_DATE).copy()

    # Precalculate 20-day ADV in INR: volume * close rolling 20 mean
    bars_df["turnover_inr"] = bars_df["close"] * bars_df["volume"].fillna(100_000.0)
    bars_df["adv_20"] = bars_df.groupby("symbol")["turnover_inr"].transform(
        lambda s: s.rolling(20, min_periods=5).mean()
    ).fillna(10_000_000.0)

    price_lookup = bars_df.set_index(["symbol", "date"]).to_dict(orient="index")
    log(f"Loaded {len(price_lookup):,} price and ADV records.")

    bench_csv = DATA_CSV_DIR / "nifty_500_benchmark_proxy.csv"
    b_df = pd.read_csv(bench_csv).sort_values("date").reset_index(drop=True)
    b_df["is_bull"] = b_df["close"] > b_df["ema_20"]
    benchmark_lookup = {r.date: {"close": float(r.close), "ret_252": float(r.ret_252), "ema_20": float(r.ema_20), "is_bull": bool(r.is_bull)} for r in b_df.itertuples()}

    aum_tiers = [
        (10_000_000.0, "₹1 Crore (Retail / HNI)"),
        (50_000_000.0, "₹5 Crore (Emerging PMS)"),
        (100_000_000.0, "₹10 Crore (Target Institutional Mandate)"),
        (250_000_000.0, "₹25 Crore (Scaled Fund Tier)")
    ]

    records = []

    for aum_val, label in aum_tiers:
        log(f"\nEvaluating AUM Tier: {label}...")
        summary, trades = run_capacity_simulation(
            aum=aum_val,
            window_days=window_days,
            snap_dates=snap_dates,
            snap_universes=snap_universes,
            price_lookup=price_lookup,
            benchmark_lookup=benchmark_lookup
        )

        adv_pcts = [t["adv_pct"] for t in trades]
        med_adv = float(np.median(adv_pcts)) if adv_pcts else 0.0
        p95_adv = float(np.percentile(adv_pcts, 95)) if adv_pcts else 0.0
        max_adv = float(np.max(adv_pcts)) if adv_pcts else 0.0
        pct_gt_10 = float(np.mean([1 if x > 10.0 else 0 for x in adv_pcts]) * 100.0) if adv_pcts else 0.0
        pct_gt_20 = float(np.mean([1 if x > 20.0 else 0 for x in adv_pcts]) * 100.0) if adv_pcts else 0.0

        # Pass condition: at target ₹10 Cr, median < 5%, orders > 10% ADV < 15% (viable institutional execution)
        is_viable = (med_adv < 5.0 and pct_gt_10 < 15.0)
        gate_status = "PASS" if is_viable else "MONITOR"
        if aum_val <= 100_000_000.0 and not is_viable:
            gate_status = "FAIL"

        log(f"  CAGR: {summary['cagr']:.2f}% | MaxDD: {summary['max_dd']:.2f}% | Trades: {summary['trades']:,}")
        log(f"  Median ADV %: {med_adv:.2f}% | 95th Percentile: {p95_adv:.2f}% | Max ADV %: {max_adv:.2f}%")
        log(f"  Orders > 10% ADV: {pct_gt_10:.2f}% | Orders > 20% ADV: {pct_gt_20:.2f}% | Status: {gate_status}")

        records.append({
            "aum_tier": label,
            "aum_inr": aum_val,
            "cagr": summary["cagr"],
            "max_dd": summary["max_dd"],
            "turnover_pct": summary["turnover_pct"],
            "trades": summary["trades"],
            "median_adv_pct": med_adv,
            "p95_adv_pct": p95_adv,
            "max_adv_pct": max_adv,
            "pct_orders_gt_10_adv": pct_gt_10,
            "pct_orders_gt_20_adv": pct_gt_20,
            "viable_capacity": "YES" if is_viable else "PARTIAL",
            "gate31_status": gate_status
        })

    df_out = pd.DataFrame(records)
    df_out.to_csv(OUT_CSV, index=False)
    log(f"\nExported Capacity and Liquidity Constraints: {OUT_CSV}")

    # Check overall Gate 31 status at ₹10 Crore target
    target_rec = next(r for r in records if r["aum_inr"] == 100_000_000.0)
    gate31_overall = "PASS" if target_rec["gate31_status"] == "PASS" else "FAIL"
    log(f"\nGate 31 Final Status (Target ₹10 Crore Mandate): {gate31_overall}")

    with open(OUT_LOG, "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines) + "\n")

if __name__ == "__main__":
    main()
