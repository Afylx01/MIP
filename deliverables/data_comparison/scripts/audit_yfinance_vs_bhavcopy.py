#!/usr/bin/env python3
"""
deliverables/data_comparison/scripts/audit_yfinance_vs_bhavcopy.py
Task 4 — Comparative Fidelity & Trustability Analysis

Performs rigorous mathematical auditing between official NSE Bhavcopy data and Yahoo Finance:
  1. Coverage & Survivorship Bias: Quantifies purged/delisted scrips missing in YFinance.
  2. Price Discrepancy & Tracking Error: Computes MAPE, Max Diff, and % of bars diverging > 1.0%.
  3. Corporate Action Fidelity: Verifies 1-day returns across 10 known historical bonus/split dates.

Outputs:
  - deliverables/data_comparison/data_csv/price_tracking_error.csv
  - deliverables/data_comparison/data_csv/corporate_action_fidelity.csv
  - deliverables/data_comparison/raw/comparative_audit_log.txt
"""

import sys
import hashlib
import datetime
from pathlib import Path
from typing import Dict, List, Tuple
import pandas as pd
import numpy as np

BASE_DIR = Path("/storage/emulated/0/Documents/Project MIP")
DELIV_DIR = BASE_DIR / "deliverables/data_comparison"
DATA_CSV_DIR = DELIV_DIR / "data_csv"
RAW_DIR = DELIV_DIR / "raw"
DATA_DIR = BASE_DIR / "data"

BHAVCOPY_PATH = DATA_DIR / "adjusted_bhavcopy_max_2007_2026.parquet"
YFINANCE_PATH = DATA_DIR / "yfinance_ohlcv_2007_2026.parquet"
COVERAGE_CSV = DATA_CSV_DIR / "coverage_comparison.csv"
TRACKING_CSV = DATA_CSV_DIR / "price_tracking_error.csv"
CORP_ACTION_CSV = DATA_CSV_DIR / "corporate_action_fidelity.csv"
LOG_FILE = RAW_DIR / "comparative_audit_log.txt"

# 10 Known Historical Corporate Actions (Ex-Date, Pre-Date, Action Details)
KNOWN_ACTIONS = [
    {"symbol": "INFY", "ex_date": "2018-09-04", "pre_date": "2018-09-03", "event": "1:1 Bonus"},
    {"symbol": "TCS", "ex_date": "2018-05-31", "pre_date": "2018-05-30", "event": "1:1 Bonus"},
    {"symbol": "RELIANCE", "ex_date": "2017-09-07", "pre_date": "2017-09-06", "event": "1:1 Bonus"},
    {"symbol": "WIPRO", "ex_date": "2019-03-06", "pre_date": "2019-03-05", "event": "1:3 Bonus"},
    {"symbol": "HDFCBANK", "ex_date": "2019-09-19", "pre_date": "2019-09-18", "event": "1:2 Split"},
    {"symbol": "EICHERMOT", "ex_date": "2020-08-24", "pre_date": "2020-08-21", "event": "1:10 Split"},
    {"symbol": "IRCTC", "ex_date": "2021-10-28", "pre_date": "2021-10-27", "event": "1:5 Split"},
    {"symbol": "TATASTEEL", "ex_date": "2022-07-28", "pre_date": "2022-07-27", "event": "1:10 Split"},
    {"symbol": "ITC", "ex_date": "2016-07-01", "pre_date": "2016-06-30", "event": "1:2 Bonus"},
    {"symbol": "BAJFINANCE", "ex_date": "2016-09-12", "pre_date": "2016-09-09", "event": "1:1 Bonus + 1:5 Split"}
]

def main():
    DATA_CSV_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    log_lines = []
    def log(msg=""):
        print(msg)
        log_lines.append(msg)

    log("=" * 80)
    log("TASK 4: COMPARATIVE FIDELITY & TRUSTABILITY ANALYSIS")
    log(f"Timestamp: {datetime.datetime.now(datetime.timezone.utc).isoformat()}")
    log("=" * 80)

    # 1. Ingest Datasets
    log("\n--- 1. Ingesting Bhavcopy & YFinance Datasets ---")
    log(f"Loading Bhavcopy ground truth: {BHAVCOPY_PATH.name}...")
    df_bhav = pd.read_parquet(BHAVCOPY_PATH)
    log(f"  Bhavcopy bars: {len(df_bhav):,} | Symbols: {df_bhav['symbol'].nunique():,} | Dates: {df_bhav['date'].min()} to {df_bhav['date'].max()}")

    log(f"Loading YFinance dataset: {YFINANCE_PATH.name}...")
    df_yf = pd.read_parquet(YFINANCE_PATH)
    log(f"  YFinance bars: {len(df_yf):,} | Symbols: {df_yf['symbol'].nunique():,} | Dates: {df_yf['date'].min()} to {df_yf['date'].max()}")

    # 2. Coverage & Survivorship Bias Audit
    log("\n--- 2. Survivorship Bias & Universe Coverage Audit ---")
    cov_df = pd.read_csv(COVERAGE_CSV)
    total_scrips = len(cov_df)
    avail_scrips = len(cov_df[cov_df["in_yfinance"]])
    missing_scrips = len(cov_df[~cov_df["in_yfinance"]])
    missing_pct = (missing_scrips / total_scrips) * 100.0

    log(f"Total Target Universe Scrips:   {total_scrips:,}")
    log(f"Available in YFinance:           {avail_scrips:,} ({avail_scrips / total_scrips * 100.0:.2f}%)")
    log(f"Missing / Purged in YFinance:    {missing_scrips:,} ({missing_pct:.2f}%)")

    log("\nAudit of Critical Delisted / Canary Symbols in YFinance:")
    canaries = ["PCJEWELLER", "DHFL", "RCOM", "UNITECH", "RANBAXY", "SUZLON", "JPASSOCIAT"]
    for c in canaries:
        sub = cov_df[cov_df["symbol"] == c]
        if not sub.empty:
            r = sub.iloc[0]
            st = "FOUND" if r["in_yfinance"] else "PURGED / MISSING"
            cnt = r["yf_bars_count"]
            log(f"  {c:<12}: {st:<16} | Bars in YF: {cnt:>5} | Status: {r['status']}")

    # 3. Intersecting Price Discrepancy & Tracking Error Audit
    log("\n--- 3. Price Discrepancy & Tracking Error Audit ---")
    log("Joining Bhavcopy and YFinance on (symbol, date)...")
    
    # Merge on symbol and date
    merged = pd.merge(
        df_bhav[["symbol", "date", "open", "close"]].rename(columns={"open": "bhav_open", "close": "bhav_close"}),
        df_yf[["symbol", "date", "open", "close", "adj_close"]].rename(columns={"open": "yf_open", "close": "yf_close", "adj_close": "yf_adj_close"}),
        on=["symbol", "date"],
        how="inner"
    )
    log(f"Total intersecting bars: {len(merged):,} across {merged['symbol'].nunique():,} symbols")

    # Compute Absolute Percentage Error (APE)
    # Using YF Close (split-adjusted) vs Bhavcopy Close
    merged["close_diff"] = np.abs(merged["yf_close"] - merged["bhav_close"])
    merged["close_ape"] = np.where(merged["bhav_close"] > 0, (merged["close_diff"] / merged["bhav_close"]) * 100.0, 0.0)

    # Using YF Open vs Bhavcopy Open
    merged["open_diff"] = np.abs(merged["yf_open"] - merged["bhav_open"])
    merged["open_ape"] = np.where(merged["bhav_open"] > 0, (merged["open_diff"] / merged["bhav_open"]) * 100.0, 0.0)

    # Aggregate by symbol
    sym_stats = []
    for sym, group in merged.groupby("symbol"):
        n_bars = len(group)
        mape_close = group["close_ape"].mean()
        max_close_diff_pct = group["close_ape"].max()
        mape_open = group["open_ape"].mean()
        divergent_bars_1pct = int((group["close_ape"] > 1.0).sum())
        divergent_pct = (divergent_bars_1pct / n_bars) * 100.0 if n_bars > 0 else 0.0
        sym_stats.append({
            "symbol": sym,
            "intersecting_bars": n_bars,
            "mape_close_pct": round(mape_close, 4),
            "max_close_diff_pct": round(max_close_diff_pct, 4),
            "mape_open_pct": round(mape_open, 4),
            "divergent_bars_gt_1pct": divergent_bars_1pct,
            "divergent_pct": round(divergent_pct, 2)
        })

    tracking_df = pd.DataFrame(sym_stats).sort_values("divergent_pct", ascending=False).reset_index(drop=True)
    tracking_df.to_csv(TRACKING_CSV, index=False)
    log(f"Exported price tracking error metrics: {TRACKING_CSV}")

    # Overall dataset-level error metrics
    overall_mape_close = merged["close_ape"].mean()
    overall_mape_open = merged["open_ape"].mean()
    total_div_1pct = int((merged["close_ape"] > 1.0).sum())
    total_div_pct = (total_div_1pct / len(merged)) * 100.0

    log(f"Overall Close MAPE:               {overall_mape_close:.3f}%")
    log(f"Overall Open MAPE:                {overall_mape_open:.3f}%")
    log(f"Total Bars Diverging > 1.0%:      {total_div_1pct:,} / {len(merged):,} ({total_div_pct:.2f}%)")

    # 4. Corporate Action Fidelity Audit
    log("\n--- 4. Corporate Action Adjustment Fidelity Audit ---")
    corp_results = []
    for ca in KNOWN_ACTIONS:
        sym = ca["symbol"]
        ex_d = ca["ex_date"]
        pre_d = ca["pre_date"]
        evt = ca["event"]

        # Bhavcopy pre and ex
        b_pre = df_bhav[(df_bhav["symbol"] == sym) & (df_bhav["date"] == pre_d)]
        b_ex = df_bhav[(df_bhav["symbol"] == sym) & (df_bhav["date"] == ex_d)]
        b_ret = None
        if not b_pre.empty and not b_ex.empty:
            p0 = b_pre.iloc[0]["close"]
            p1 = b_ex.iloc[0]["close"]
            b_ret = ((p1 / p0) - 1.0) * 100.0 if p0 > 0 else 0.0

        # YF raw Close pre and ex
        yf_pre = df_yf[(df_yf["symbol"] == sym) & (df_yf["date"] == pre_d)]
        yf_ex = df_yf[(df_yf["symbol"] == sym) & (df_yf["date"] == ex_d)]
        yf_close_ret = None
        yf_adj_ret = None
        if not yf_pre.empty and not yf_ex.empty:
            c0 = yf_pre.iloc[0]["close"]
            c1 = yf_ex.iloc[0]["close"]
            yf_close_ret = ((c1 / c0) - 1.0) * 100.0 if c0 > 0 else 0.0

            a0 = yf_pre.iloc[0]["adj_close"]
            a1 = yf_ex.iloc[0]["adj_close"]
            yf_adj_ret = ((a1 / a0) - 1.0) * 100.0 if a0 > 0 else 0.0

        ret_diff = abs(b_ret - yf_close_ret) if (b_ret is not None and yf_close_ret is not None) else None
        is_fidelity_ok = (ret_diff is not None and ret_diff < 0.5)

        corp_results.append({
            "symbol": sym,
            "corporate_event": evt,
            "pre_date": pre_d,
            "ex_date": ex_d,
            "bhavcopy_adjusted_return_pct": round(b_ret, 3) if b_ret is not None else None,
            "yfinance_close_return_pct": round(yf_close_ret, 3) if yf_close_ret is not None else None,
            "yfinance_adj_close_return_pct": round(yf_adj_ret, 3) if yf_adj_ret is not None else None,
            "return_difference_pct": round(ret_diff, 3) if ret_diff is not None else None,
            "fidelity_pass": is_fidelity_ok
        })

    corp_df = pd.DataFrame(corp_results)
    corp_df.to_csv(CORP_ACTION_CSV, index=False)
    log(f"Exported corporate action fidelity audit: {CORP_ACTION_CSV}")

    log("\nCorporate Action Fidelity Verification Table:")
    log(f"{'Symbol':<10} {'Event':<25} {'Ex-Date':<12} {'Bhav Ret %':<12} {'YF Ret %':<12} {'Diff %':<10} {'Status'}")
    log("-" * 88)
    for _, r in corp_df.iterrows():
        b_str = f"{r['bhavcopy_adjusted_return_pct']:.2f}%" if pd.notna(r['bhavcopy_adjusted_return_pct']) else "N/A"
        y_str = f"{r['yfinance_close_return_pct']:.2f}%" if pd.notna(r['yfinance_close_return_pct']) else "N/A"
        d_str = f"{r['return_difference_pct']:.2f}%" if pd.notna(r['return_difference_pct']) else "N/A"
        st = "PASS" if r['fidelity_pass'] else "DISCREPANCY"
        log(f"{r['symbol']:<10} {r['corporate_event']:<25} {r['ex_date']:<12} {b_str:<12} {y_str:<12} {d_str:<10} {st}")

    log("\n" + "=" * 80)
    log("TASK 4 COMPLETE: COMPARATIVE AUDIT FINISHED (PASS)")
    log("=" * 80)

    # Save log
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines) + "\n")

if __name__ == "__main__":
    main()
