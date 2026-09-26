#!/usr/bin/env python3
"""
deliverables/data_comparison/scripts/fetch_yfinance_ohlcv.py
Task 3 — High-Performance Batched YFinance Ingestion Engine

Downloads historical daily OHLCV bars (2007-01-01 to 2026-08-31) for all point-in-time
constituents across the NIFTY 500 universe from Yahoo Finance.

Features:
  - Multi-threaded batching (50 symbols per chunk)
  - Resumable batch checkpointing (preserves network progress)
  - Captures raw OHLCV, Adj Close, Dividends, and Stock Splits (auto_adjust=False)
  - Audits survivorship bias / missing / delisted tickers (e.g. DHFL, RANBAXY, etc.)
  - Exports data/yfinance_ohlcv_2007_2026.parquet
  - Exports deliverables/data_comparison/data_csv/coverage_comparison.csv
  - Logs deliverables/data_comparison/raw/yfinance_download_log.txt
"""

import sys
import time
import hashlib
import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple
import pandas as pd
import numpy as np
import yfinance as yf

BASE_DIR = Path("/storage/emulated/0/Documents/Project MIP")
DELIV_DIR = BASE_DIR / "deliverables/data_comparison"
DATA_CSV_DIR = DELIV_DIR / "data_csv"
RAW_DIR = DELIV_DIR / "raw"
DATA_DIR = BASE_DIR / "data"

BATCH_DIR = DATA_DIR / "yfinance_batches"
OUT_PARQUET = DATA_DIR / "yfinance_ohlcv_2007_2026.parquet"
COVERAGE_CSV = DATA_CSV_DIR / "coverage_comparison.csv"
LOG_FILE = RAW_DIR / "yfinance_download_log.txt"

BHAVCOPY_MAX_PATH = DATA_DIR / "adjusted_bhavcopy_max_2007_2026.parquet"
SYMBOL_MAP_PATH = DATA_DIR / "symbol_map.parquet"

START_DATE = "2007-01-01"
END_DATE = "2026-09-01"
BATCH_SIZE = 50

AUDIT_CANARIES = [
    "PCJEWELLER", "DHFL", "RCOM", "UNITECH", "RANBAXY", "SUZLON", "JPASSOCIAT",
    "INFY", "TCS", "RELIANCE", "WIPRO"
]

def sha256_file(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def main():
    DATA_CSV_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    BATCH_DIR.mkdir(parents=True, exist_ok=True)

    log_lines = []
    def log(msg=""):
        print(msg)
        log_lines.append(msg)

    log("=" * 80)
    log("TASK 3: HIGH-PERFORMANCE BATCHED YFINANCE INGESTION ENGINE")
    log(f"Timestamp: {datetime.datetime.now(datetime.timezone.utc).isoformat()}")
    log("=" * 80)

    # 1. Compile target symbols
    log("\n--- 1. Compiling Target Universe ---")
    smap_df = pd.read_parquet(SYMBOL_MAP_PATH)
    smap_symbols = set(smap_df["symbol"].dropna().astype(str).str.strip().unique())
    smap_symbols.discard("")

    bhav_df = pd.read_parquet(BHAVCOPY_MAX_PATH, columns=["symbol"])
    bhav_symbols = set(bhav_df["symbol"].dropna().astype(str).str.strip().unique())

    # Union of all symbols + canaries
    all_target_symbols = sorted(list(smap_symbols | bhav_symbols | set(AUDIT_CANARIES)))
    log(f"Symbols from symbol_map:        {len(smap_symbols):,}")
    log(f"Symbols from max Bhavcopy:      {len(bhav_symbols):,}")
    log(f"Total Unique Target Symbols:    {len(all_target_symbols):,}")

    # Build symbol -> scrip mapping
    sym_to_scrip = {}
    for _, r in smap_df.iterrows():
        s = str(r["symbol"]).strip() if pd.notna(r["symbol"]) else ""
        sc = str(r["scrip_name"]).strip() if pd.notna(r["scrip_name"]) else ""
        if s and sc and s not in sym_to_scrip:
            sym_to_scrip[s] = sc

    # 2. Divide into batches
    batches = [all_target_symbols[i:i + BATCH_SIZE] for i in range(0, len(all_target_symbols), BATCH_SIZE)]
    log(f"Divided universe into {len(batches)} batches of up to {BATCH_SIZE} symbols each.")

    # 3. Process batches
    log("\n--- 2. Downloading Historical OHLCV via YFinance ---")
    batch_files = []
    symbol_coverage_records = []

    for b_idx, batch in enumerate(batches):
        batch_parquet = BATCH_DIR / f"batch_{b_idx:03d}.parquet"
        tickers = [f"{s}.NS" for s in batch]
        ticker_to_sym = {f"{s}.NS": s for s in batch}

        if batch_parquet.exists() and batch_parquet.stat().st_size > 0:
            log(f"  [Batch {b_idx + 1}/{len(batches)}] Loading cached: {batch_parquet.name} ({len(batch)} symbols)")
            b_df = pd.read_parquet(batch_parquet)
            batch_files.append(batch_parquet)
            
            # Record coverage from cached batch
            found_syms = set(b_df["symbol"].unique()) if not b_df.empty else set()
            for s in batch:
                sub_len = len(b_df[b_df["symbol"] == s]) if s in found_syms else 0
                status = "available" if sub_len > 0 else "delisted_or_not_found"
                symbol_coverage_records.append({
                    "symbol": s,
                    "scrip_name": sym_to_scrip.get(s, s),
                    "yfinance_ticker": f"{s}.NS",
                    "in_bhavcopy": (s in bhav_symbols),
                    "in_yfinance": (sub_len > 0),
                    "yf_bars_count": sub_len,
                    "status": status
                })
            continue

        log(f"  [Batch {b_idx + 1}/{len(batches)}] Downloading {len(tickers)} tickers from Yahoo Finance...")
        t0 = time.time()
        try:
            raw_download = yf.download(
                tickers=tickers,
                start=START_DATE,
                end=END_DATE,
                group_by="ticker",
                auto_adjust=False,
                actions=True,
                threads=True,
                progress=False
            )
        except Exception as e:
            log(f"    ERROR in batch download: {e}")
            raw_download = pd.DataFrame()

        elapsed = time.time() - t0

        records = []
        # MultiIndex parsing: if single ticker vs multiple tickers
        if not raw_download.empty:
            if isinstance(raw_download.columns, pd.MultiIndex):
                top_levels = set(raw_download.columns.levels[0])
                for t in tickers:
                    s = ticker_to_sym[t]
                    if t in top_levels:
                        sub = raw_download[t].dropna(how="all")
                        sub_len = len(sub)
                        if sub_len > 0:
                            for idx, r in sub.iterrows():
                                records.append({
                                    "symbol": s,
                                    "date": idx.strftime("%Y-%m-%d"),
                                    "open": float(r.get("Open", 0.0) or 0.0),
                                    "high": float(r.get("High", 0.0) or 0.0),
                                    "low": float(r.get("Low", 0.0) or 0.0),
                                    "close": float(r.get("Close", 0.0) or 0.0),
                                    "adj_close": float(r.get("Adj Close", 0.0) or 0.0),
                                    "volume": float(r.get("Volume", 0.0) or 0.0),
                                    "dividends": float(r.get("Dividends", 0.0) or 0.0),
                                    "stock_splits": float(r.get("Stock Splits", 0.0) or 0.0)
                                })
                        status = "available" if sub_len > 0 else "delisted_or_not_found"
                        symbol_coverage_records.append({
                            "symbol": s,
                            "scrip_name": sym_to_scrip.get(s, s),
                            "yfinance_ticker": t,
                            "in_bhavcopy": (s in bhav_symbols),
                            "in_yfinance": (sub_len > 0),
                            "yf_bars_count": sub_len,
                            "status": status
                        })
                    else:
                        symbol_coverage_records.append({
                            "symbol": s,
                            "scrip_name": sym_to_scrip.get(s, s),
                            "yfinance_ticker": t,
                            "in_bhavcopy": (s in bhav_symbols),
                            "in_yfinance": False,
                            "yf_bars_count": 0,
                            "status": "delisted_or_not_found"
                        })
            else:
                # Single ticker fallback
                t = tickers[0]
                s = ticker_to_sym[t]
                sub = raw_download.dropna(how="all")
                sub_len = len(sub)
                for idx, r in sub.iterrows():
                    records.append({
                        "symbol": s,
                        "date": idx.strftime("%Y-%m-%d"),
                        "open": float(r.get("Open", 0.0) or 0.0),
                        "high": float(r.get("High", 0.0) or 0.0),
                        "low": float(r.get("Low", 0.0) or 0.0),
                        "close": float(r.get("Close", 0.0) or 0.0),
                        "adj_close": float(r.get("Adj Close", 0.0) or 0.0),
                        "volume": float(r.get("Volume", 0.0) or 0.0),
                        "dividends": float(r.get("Dividends", 0.0) or 0.0),
                        "stock_splits": float(r.get("Stock Splits", 0.0) or 0.0)
                    })
                symbol_coverage_records.append({
                    "symbol": s,
                    "scrip_name": sym_to_scrip.get(s, s),
                    "yfinance_ticker": t,
                    "in_bhavcopy": (s in bhav_symbols),
                    "in_yfinance": (sub_len > 0),
                    "yf_bars_count": sub_len,
                    "status": "available" if sub_len > 0 else "delisted_or_not_found"
                })
        else:
            for s in batch:
                symbol_coverage_records.append({
                    "symbol": s,
                    "scrip_name": sym_to_scrip.get(s, s),
                    "yfinance_ticker": f"{s}.NS",
                    "in_bhavcopy": (s in bhav_symbols),
                    "in_yfinance": False,
                    "yf_bars_count": 0,
                    "status": "delisted_or_not_found"
                })

        b_df = pd.DataFrame(records)
        b_df.to_parquet(batch_parquet, engine="pyarrow", index=False)
        batch_files.append(batch_parquet)
        log(f"    Completed in {elapsed:.1f}s | Parsed {len(records):,} bars -> {batch_parquet.name}")
        time.sleep(0.5)

    # 4. Consolidate All Batches
    log("\n--- 3. Consolidating All YFinance Batches ---")
    dfs = [pd.read_parquet(bf) for bf in batch_files if bf.stat().st_size > 0]
    if dfs:
        yf_all = pd.concat(dfs, ignore_index=True)
    else:
        yf_all = pd.DataFrame()

    log(f"Total raw YFinance bars downloaded: {len(yf_all):,}")

    if not yf_all.empty:
        # Sort and deduplicate
        yf_all = yf_all.sort_values(["symbol", "date"]).drop_duplicates(subset=["symbol", "date"]).reset_index(drop=True)
        yf_all.to_parquet(OUT_PARQUET, engine="pyarrow", index=False)
        out_size = OUT_PARQUET.stat().st_size
        out_sha = sha256_file(OUT_PARQUET)
        log(f"Persisted consolidated YFinance dataset: {OUT_PARQUET}")
        log(f"  Shape:     {yf_all.shape}")
        log(f"  Size:      {out_size:,} bytes ({out_size / (1024*1024):.2f} MB)")
        log(f"  SHA-256:   {out_sha}")
        log(f"  Symbols:   {yf_all['symbol'].nunique():,}")
        log(f"  Dates:     {yf_all['date'].min()} to {yf_all['date'].max()}")

    # 5. Export Coverage Comparison CSV
    cov_df = pd.DataFrame(symbol_coverage_records).drop_duplicates(subset=["symbol"]).reset_index(drop=True)
    cov_df.to_csv(COVERAGE_CSV, index=False)
    log(f"\nExported coverage audit: {COVERAGE_CSV} ({len(cov_df)} symbols audited)")

    # 6. Audit Survivorship Bias Footprint
    log("\n--- 4. YFinance Survivorship Bias Audit ---")
    total_audited = len(cov_df)
    avail_count = len(cov_df[cov_df["in_yfinance"]])
    missing_count = len(cov_df[~cov_df["in_yfinance"]])
    survivorship_pct = (missing_count / total_audited) * 100.0

    log(f"Total Point-in-Time Universe Scrips: {total_audited:,}")
    log(f"Found in YFinance:                  {avail_count:,} ({avail_count/total_audited*100:.1f}%)")
    log(f"MISSING in YFinance (Purged/Dead):  {missing_count:,} ({survivorship_pct:.1f}%)")

    log("\nCanary Check (Historical / Delisted / High-Profile Stocks):")
    for can in AUDIT_CANARIES:
        row = cov_df[cov_df["symbol"] == can]
        if not row.empty:
            r = row.iloc[0]
            status_str = f"FOUND ({r['yf_bars_count']:,} bars)" if r["in_yfinance"] else "MISSING / PURGED"
            log(f"  {can:<12}: {status_str}")

    log("\n" + "=" * 80)
    log("TASK 3 COMPLETE: YFINANCE INGESTION & COVERAGE AUDIT FINISHED")
    log("=" * 80)

    # Save log
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines) + "\n")

if __name__ == "__main__":
    main()
