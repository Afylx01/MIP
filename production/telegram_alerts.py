#!/usr/bin/env python3
"""
production/telegram_alerts.py
Production Master Task 3: Telegram Formatter & Dispatcher for MIP Momentum Scanner

Formats an executive, institutional HTML Telegram alert containing:
  1. Header: Strategy Name, Screener Date, Market Regime (NORMAL vs DEFENSIVE).
  2. Top 20 Momentum Scrips Table (Rank, Symbol, Close Price, 52wH Distance, 200 EMA Ratio, Volar Score).
  3. Actionable Position Sizing: Target whole shares & capital allocation for:
       - Tier 1: ₹10 Lakhs Mandate (₹50,000 per slot)
       - Tier 2: ₹1 Crore Mandate (₹5,00,000 per slot)
  4. Dispatch via `/usr/local/bin/telegram-notify --html`.
  5. Supports `--dry-run` for local preview without network dispatch.

Usage:
  python3 production/telegram_alerts.py [--screener-csv PATH] [--dry-run]
"""

import sys
import os
import subprocess
import argparse
import datetime
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd
import numpy as np

BASE_DIR = Path("/storage/emulated/0/Documents/Project MIP")
DEFAULT_SCREENER_CSV = BASE_DIR / "deliverables/phase_8/data_csv/screener_output_live.csv"
BENCHMARK_CSV = BASE_DIR / "deliverables/phase_7/data_csv/nifty_500_benchmark_proxy.csv"
TELEGRAM_NOTIFY_BIN = Path("/usr/local/bin/telegram-notify")


def get_market_regime(as_of_date: str) -> Dict:
    """Reads NIFTY 500 benchmark and compares close to 20 EMA."""
    if not BENCHMARK_CSV.exists():
        return {"label": "NORMAL (Default)", "close": 0.0, "ema_20": 0.0, "is_normal": True}
    df = pd.read_csv(BENCHMARK_CSV)
    df["date"] = df["date"].astype(str)
    row = df[df["date"] == as_of_date]
    if row.empty:
        prior = df[df["date"] <= as_of_date]
        if prior.empty:
            return {"label": "NORMAL (Default)", "close": 0.0, "ema_20": 0.0, "is_normal": True}
        row = prior.iloc[[-1]]

    c = float(row["close"].values[0])
    e20 = float(row["ema_20"].values[0])
    is_normal = (c >= e20)
    label = "🟢 NORMAL / RISK-ON (Entries Active)" if is_normal else "🔴 DEFENSIVE / RISK-OFF (Entries Paused / Exits to Cash)"
    return {"label": label, "close": c, "ema_20": e20, "is_normal": is_normal}


def format_telegram_html(
    screener_df: pd.DataFrame,
    as_of_date: str,
    regime: Dict,
    top_n: int = 20
) -> str:
    """Formats institutional HTML message for Telegram."""
    qual = screener_df[screener_df["is_qualified"] == True].sort_values(by="rank").head(top_n).copy()

    html = []
    html.append("📊 <b>PROJECT MIP — PRODUCTION MOMENTUM ALERT</b>")
    html.append(f"📅 <b>Signal Date</b>: {as_of_date} (Friday EOD)")
    html.append(f"⚡ <b>Market Regime</b>: {regime['label']}")
    html.append(f"📈 <i>NIFTY 500: ₹{regime['close']:,.2f} | 20 EMA: ₹{regime['ema_20']:,.2f}</i>\n")

    html.append(f"🏆 <b>TOP {len(qual)} MOMENTUM CANDIDATES</b>")
    html.append("<pre>")
    html.append(f"{'#':<3}{'SYMBOL':<11}{'PRICE':<9}{'52wH%':<8}{'VOLAR':<6}")
    html.append("-" * 37)

    for _, r in qual.iterrows():
        rk = int(r["rank"])
        sym = str(r["symbol"])[:10]
        px = f"₹{float(r['close']):.1f}"
        dist = f"{float(r['distance_52wh_pct']):.1f}%"
        volar = f"{float(r['volar_score']):.2f}"
        html.append(f"{rk:<3}{sym:<11}{px:<9}{dist:<8}{volar:<6}")

    html.append("</pre>\n")

    # Position Sizing Recommendations
    html.append("🎯 <b>TARGET POSITION SIZING (TOP 20 EQUAL-WEIGHT)</b>")
    html.append("<b>Tier 1: ₹10 Lakhs Portfolio (₹50,000 / Slot)</b>")
    html.append("<pre>")
    html.append(f"{'SYMBOL':<11}{'SHARES':<8}{'EST. OUTLAY'}")
    html.append("-" * 28)
    for _, r in qual.head(10).iterrows():
        sym = str(r["symbol"])[:10]
        px = float(r["close"])
        shs = int(50_000 // px) if px > 0 else 0
        outlay = f"₹{shs * px:,.0f}"
        html.append(f"{sym:<11}{shs:<8}{outlay}")
    html.append("... [See tearsheet for full 20 slots]")
    html.append("</pre>\n")

    html.append("<b>Tier 2: ₹1 Crore Portfolio (₹5,00,000 / Slot)</b>")
    html.append("<pre>")
    html.append(f"{'SYMBOL':<11}{'SHARES':<8}{'EST. OUTLAY'}")
    html.append("-" * 28)
    for _, r in qual.head(10).iterrows():
        sym = str(r["symbol"])[:10]
        px = float(r["close"])
        shs = int(500_000 // px) if px > 0 else 0
        outlay = f"₹{shs * px:,.0f}"
        html.append(f"{sym:<11}{shs:<8}{outlay}")
    html.append("... [See tearsheet for full 20 slots]")
    html.append("</pre>\n")

    html.append("🛡️ <b>Execution Rules Reminder</b>:")
    html.append("• 100% Exit Buffer: Retain existing holdings up to Rank 40.")
    html.append("• Zero Look-Ahead: Signals Friday Close -> Monday Open execution.")
    html.append("• Trend Invariant: Exit immediately on 200 EMA break.")

    return "\n".join(html)


def dispatch_telegram_alert(
    screener_csv: Path,
    as_of_date: Optional[str] = None,
    dry_run: bool = False
) -> str:
    """Loads screener, formats HTML alert, and dispatches via telegram-notify."""
    if not screener_csv.exists():
        raise FileNotFoundError(f"Screener CSV not found: {screener_csv}")

    df = pd.read_csv(screener_csv)
    date_str = as_of_date or str(df["date"].iloc[0] if "date" in df.columns else datetime.date.today())
    regime = get_market_regime(date_str)

    msg = format_telegram_html(df, as_of_date=date_str, regime=regime)

    if dry_run:
        print("\n==================== TELEGRAM ALERT PREVIEW (DRY-RUN) ====================")
        print(msg)
        print("==========================================================================\n")
        return msg

    print("Dispatching Telegram alert via telegram-notify...")
    cmd = [
        str(TELEGRAM_NOTIFY_BIN),
        "--html",
        "-m", msg
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0:
        print("✅ Telegram alert dispatched successfully!")
    else:
        print(f"⚠️ Telegram dispatch failed: {res.stderr}")
    return msg


def main():
    parser = argparse.ArgumentParser(description="MIP Telegram Momentum Alert Dispatcher")
    parser.add_argument("--screener-csv", type=str, default=str(DEFAULT_SCREENER_CSV), help="Path to live screener CSV")
    parser.add_argument("--as-of-date", type=str, default="2026-08-28", help="Screener as-of date")
    parser.add_argument("--dry-run", action="store_true", help="Print message to terminal without sending")

    args = parser.parse_args()
    dispatch_telegram_alert(
        screener_csv=Path(args.screener_csv),
        as_of_date=args.as_of_date,
        dry_run=args.dry_run
    )


if __name__ == "__main__":
    main()
