#!/usr/bin/env python3
"""
deliverables/phase_7/scripts/test_trade_statistics.py
Phase 7C Task 4: Trade Statistics & Expectancy Analysis (Gate 22)

Analyzes itemized closed round-trip trades from the baseline momentum model (2016–2026):
  - Win Rate (%), Loss Rate (%)
  - Average Gain (%), Average Loss (%)
  - Win/Loss Payoff Ratio
  - Profit Factor (Gross Profits / |Gross Losses|)
  - Expectancy per trade: E = (P_win * W) - (P_loss * L)
  - Gain-to-Pain Ratio and Average Holding Period (days)

Pass Criteria:
  - Win Rate > 40.0%
  - Profit Factor > 1.50

Outputs:
  - deliverables/phase_7/data_csv/gate22_trade_statistics.csv
  - deliverables/phase_7/data_csv/gate22_closed_trades_itemized.csv
  - deliverables/phase_7/raw/test_trade_statistics.log
"""

import sys
import os
import datetime
from pathlib import Path
from typing import Dict, List, Tuple
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

OUT_CSV = DATA_CSV_DIR / "gate22_trade_statistics.csv"
OUT_TRADES_CSV = DATA_CSV_DIR / "gate22_closed_trades_itemized.csv"
OUT_LOG = RAW_DIR / "test_trade_statistics.log"

def main():
    DATA_CSV_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    log_lines = []
    def log(msg=""):
        print(msg)
        log_lines.append(msg)

    log("=" * 80)
    log("PHASE 7C TASK 4: TRADE STATISTICS & EXPECTANCY ANALYSIS (GATE 22)")
    log(f"Timestamp: {datetime.datetime.now(datetime.timezone.utc).isoformat()}")
    log("=" * 80)

    cal_mgr = CalendarManager(base_dir=BASE_DIR, use_bhavcopy_calendar=True)
    u_mgr = UniverseManager(base_dir=BASE_DIR)
    window_days = cal_mgr.get_trading_days(START_DATE, END_DATE)
    snaps = cal_mgr.get_monthly_rebalance_snapshots(START_DATE, END_DATE)
    snap_universes = u_mgr.get_all_snapshot_universes(snaps)

    log(f"Loading Bhavcopy and benchmark data across {START_DATE} to {END_DATE}...")
    reader = BhavcopyReader(base_dir=BASE_DIR, custom_path=BHAVCOPY_PATH)
    price_lookup = reader.get_price_lookup(START_DATE, END_DATE)
    idx_df = reader.load_benchmark_index()
    benchmark_lookup = idx_df.set_index("date").to_dict(orient="index")

    log("Executing baseline simulation to extract itemized closed trades...")
    res = run_simulation_instance(
        slippage_bps=10.0,
        cost_multiplier=1.0,
        window_days=window_days,
        snap_dates=snaps,
        snap_universes=snap_universes,
        price_lookup=price_lookup,
        benchmark_lookup=benchmark_lookup,
        record_full_deliverables=True
    )

    closed = res["portfolio"].closed_trades
    n_trades = len(closed)

    itemized_records = []
    for t in closed:
        cost_basis = (t["shares"] * t["buy_price"]) + t.get("entry_friction", 0.0)
        pnl = t["pnl"]
        pnl_pct = (pnl / cost_basis * 100.0) if cost_basis > 0 else 0.0
        h_days = (pd.to_datetime(t["sell_date"]) - pd.to_datetime(t["buy_date"])).days
        itemized_records.append({
            "symbol": t["symbol"],
            "buy_date": t["buy_date"],
            "buy_price": round(t["buy_price"], 2),
            "sell_date": t["sell_date"],
            "sell_price": round(t["sell_price"], 2),
            "shares": t["shares"],
            "cost_basis": round(cost_basis, 2),
            "net_pnl": round(pnl, 2),
            "return_pct": round(pnl_pct, 2),
            "holding_days": h_days,
            "exit_reason": t["exit_reason"],
            "total_friction": round(t.get("total_friction", 0.0), 2)
        })

    df_trades = pd.DataFrame(itemized_records)
    df_trades.to_csv(OUT_TRADES_CSV, index=False)
    log(f"Exported {len(df_trades)} itemized round-trip closed trades to: {OUT_TRADES_CSV}")

    wins = df_trades[df_trades["net_pnl"] > 0]
    losses = df_trades[df_trades["net_pnl"] < 0]
    evens = df_trades[df_trades["net_pnl"] == 0]

    n_wins = len(wins)
    n_losses = len(losses)
    n_evens = len(evens)

    win_rate = (n_wins / n_trades * 100.0) if n_trades > 0 else 0.0
    loss_rate = (n_losses / n_trades * 100.0) if n_trades > 0 else 0.0

    gross_profit = float(wins["net_pnl"].sum())
    gross_loss = abs(float(losses["net_pnl"].sum()))
    net_pnl = float(df_trades["net_pnl"].sum())

    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else 999.0
    avg_win_inr = float(wins["net_pnl"].mean()) if n_wins > 0 else 0.0
    avg_loss_inr = abs(float(losses["net_pnl"].mean())) if n_losses > 0 else 0.0

    avg_win_pct = float(wins["return_pct"].mean()) if n_wins > 0 else 0.0
    avg_loss_pct = abs(float(losses["return_pct"].mean())) if n_losses > 0 else 0.0

    payoff_ratio = (avg_win_pct / avg_loss_pct) if avg_loss_pct > 0 else 0.0

    # Trade Expectancy Formula: E = (P_win * Avg_Win_Pct) - (P_loss * Avg_Loss_Pct)
    p_win_dec = win_rate / 100.0
    p_loss_dec = loss_rate / 100.0
    expectancy_pct = (p_win_dec * avg_win_pct) - (p_loss_dec * avg_loss_pct)
    expectancy_inr = net_pnl / n_trades if n_trades > 0 else 0.0

    gain_to_pain = (net_pnl / gross_loss) if gross_loss > 0 else 999.0
    avg_holding_days = float(df_trades["holding_days"].mean())
    median_holding_days = float(df_trades["holding_days"].median())

    max_win_pct = float(df_trades["return_pct"].max())
    max_loss_pct = float(df_trades["return_pct"].min())
    best_symbol = df_trades.sort_values("return_pct", ascending=False).iloc[0]["symbol"]
    worst_symbol = df_trades.sort_values("return_pct").iloc[0]["symbol"]

    log("\n" + "=" * 80)
    log("GATE 22 COMPLIANCE EVALUATION & TRADE STATISTICS")
    log("=" * 80)
    log(f"  Total Round-Trip Trades:      {n_trades}")
    log(f"  Winning Trades:               {n_wins} ({win_rate:.2f}%) (Pass Threshold: > 40.0%)")
    log(f"  Losing Trades:                {n_losses} ({loss_rate:.2f}%)")
    log(f"  Gross Profits:                INR {gross_profit:,.2f}")
    log(f"  Gross Losses:                 INR {gross_loss:,.2f}")
    log(f"  Net Realized PnL:             INR {net_pnl:,.2f}")
    log(f"  Profit Factor:                {profit_factor:.2f} (Pass Threshold: > 1.50)")
    log(f"  Average Win:                  +{avg_win_pct:.2f}% (INR {avg_win_inr:,.2f})")
    log(f"  Average Loss:                 -{avg_loss_pct:.2f}% (INR {avg_loss_inr:,.2f})")
    log(f"  Win/Loss Payoff Ratio:        {payoff_ratio:.2f}x (Asymmetric right-tail payoff)")
    log(f"  Mathematical Expectancy:      +{expectancy_pct:.2f}% per trade (+INR {expectancy_inr:,.2f})")
    log(f"  Gain-to-Pain Ratio:           {gain_to_pain:.2f}")
    log(f"  Average Holding Period:       {avg_holding_days:.1f} days (Median: {median_holding_days:.0f} days)")
    log(f"  Maximum Winning Trade:        +{max_win_pct:.2f}% ({best_symbol})")
    log(f"  Maximum Losing Trade:         {max_loss_pct:.2f}% ({worst_symbol})")

    gate22_pass = (win_rate > 40.0 and profit_factor > 1.50)
    log(f"\n  Gate 22 Status:               {'PASS' if gate22_pass else 'FAIL'}")

    summary_records = [
        {"metric": "Total Closed Trades", "value": n_trades, "threshold": "Informational", "status": "INFO"},
        {"metric": "Winning Trades Count", "value": n_wins, "threshold": "Informational", "status": "INFO"},
        {"metric": "Losing Trades Count", "value": n_losses, "threshold": "Informational", "status": "INFO"},
        {"metric": "Win Rate (%)", "value": round(win_rate, 2), "threshold": "> 40.0%", "status": "PASS" if win_rate > 40.0 else "FAIL"},
        {"metric": "Loss Rate (%)", "value": round(loss_rate, 2), "threshold": "Informational", "status": "INFO"},
        {"metric": "Profit Factor", "value": round(profit_factor, 2), "threshold": "> 1.50", "status": "PASS" if profit_factor > 1.50 else "FAIL"},
        {"metric": "Gross Realized Profits (INR)", "value": round(gross_profit, 2), "threshold": "Informational", "status": "INFO"},
        {"metric": "Gross Realized Losses (INR)", "value": round(gross_loss, 2), "threshold": "Informational", "status": "INFO"},
        {"metric": "Net Realized PnL (INR)", "value": round(net_pnl, 2), "threshold": "> 0.00", "status": "PASS" if net_pnl > 0 else "FAIL"},
        {"metric": "Average Win Return (%)", "value": round(avg_win_pct, 2), "threshold": "Informational", "status": "INFO"},
        {"metric": "Average Loss Return (%)", "value": round(avg_loss_pct, 2), "threshold": "Informational", "status": "INFO"},
        {"metric": "Win/Loss Payoff Ratio", "value": round(payoff_ratio, 2), "threshold": "> 1.00", "status": "PASS" if payoff_ratio > 1.0 else "FAIL"},
        {"metric": "Expectancy Return per Trade (%)", "value": round(expectancy_pct, 2), "threshold": "> 0.00%", "status": "PASS" if expectancy_pct > 0 else "FAIL"},
        {"metric": "Expectancy PnL per Trade (INR)", "value": round(expectancy_inr, 2), "threshold": "> 0.00", "status": "PASS" if expectancy_inr > 0 else "FAIL"},
        {"metric": "Gain-to-Pain Ratio", "value": round(gain_to_pain, 2), "threshold": "> 0.50", "status": "PASS" if gain_to_pain > 0.50 else "FAIL"},
        {"metric": "Average Holding Period (Days)", "value": round(avg_holding_days, 1), "threshold": "Informational", "status": "INFO"},
        {"metric": "Median Holding Period (Days)", "value": round(median_holding_days, 1), "threshold": "Informational", "status": "INFO"},
        {"metric": "Max Winning Trade Return (%)", "value": round(max_win_pct, 2), "threshold": "Informational", "status": "INFO"},
        {"metric": "Max Losing Trade Return (%)", "value": round(max_loss_pct, 2), "threshold": "Informational", "status": "INFO"},
        {"metric": "Gate 22 Compliance Status", "value": "PASS" if gate22_pass else "FAIL", "threshold": "Win Rate > 40% & PF > 1.50", "status": "PASS" if gate22_pass else "FAIL"}
    ]

    pd.DataFrame(summary_records).to_csv(OUT_CSV, index=False)
    log(f"Exported Gate 22 Summary Table: {OUT_CSV}")

    with open(OUT_LOG, "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines) + "\n")

if __name__ == "__main__":
    main()
