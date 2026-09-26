#!/usr/bin/env python3
"""
deliverables/data_comparison/scripts/consolidate_max_bhavcopy.py
Task 2 — Maximum Bhavcopy Consolidation (2007–2026)

Consolidates:
  1. data/verification/halt1b_m1/adjusted_bhavcopy_bars_v2.parquet (2016-01-04 to 2020-09-14)
  2. data/adjusted_bhavcopy_bars_modern.parquet (2020-09-15 to 2026-08-31)
  3. data/price_cache_export.parquet (2007-01-02 to 2026-08-31)

Priority Resolution:
  - Official corporate action adjusted bars from (1) and (2) take absolute precedence.
  - Historical bars from (3) backfill the 2007-01-02 to 2015-12-31 horizon and any missing keys.

Output:
  - data/adjusted_bhavcopy_max_2007_2026.parquet
  - deliverables/data_comparison/raw/consolidation_log.txt
"""

import sys
import hashlib
import datetime
from pathlib import Path
import pandas as pd
import numpy as np

BASE_DIR = Path("/storage/emulated/0/Documents/Project MIP")
DELIV_DIR = BASE_DIR / "deliverables/data_comparison"
RAW_DIR = DELIV_DIR / "raw"
DATA_DIR = BASE_DIR / "data"

V2_PATH = DATA_DIR / "verification/halt1b_m1/adjusted_bhavcopy_bars_v2.parquet"
MOD_PATH = DATA_DIR / "adjusted_bhavcopy_bars_modern.parquet"
CACHE_PATH = DATA_DIR / "price_cache_export.parquet"
OUT_PATH = DATA_DIR / "adjusted_bhavcopy_max_2007_2026.parquet"

REQUIRED_COLS = ["symbol", "date", "open", "high", "low", "close", "volume"]

def sha256_file(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    log_lines = []
    def log(msg=""):
        print(msg)
        log_lines.append(msg)

    log("=" * 80)
    log("TASK 2: MAXIMUM BHAVCOPY CONSOLIDATION (2007–2026)")
    log(f"Timestamp: {datetime.datetime.now(datetime.timezone.utc).isoformat()}")
    log("=" * 80)

    # 1. Ingest datasets
    log("\n--- 1. Ingesting Source Datasets ---")
    log(f"Loading official adjusted bars (v2): {V2_PATH.name}...")
    df_v2 = pd.read_parquet(V2_PATH)
    log(f"  v2 shape: {df_v2.shape}, dates: {df_v2['date'].min()} to {df_v2['date'].max()}, symbols: {df_v2['symbol'].nunique()}")

    log(f"Loading modern adjusted bars: {MOD_PATH.name}...")
    df_mod = pd.read_parquet(MOD_PATH)
    log(f"  mod shape: {df_mod.shape}, dates: {df_mod['date'].min()} to {df_mod['date'].max()}, symbols: {df_mod['symbol'].nunique()}")

    log(f"Loading dense price cache: {CACHE_PATH.name}...")
    df_cache = pd.read_parquet(CACHE_PATH)
    log(f"  cache shape: {df_cache.shape}, dates: {df_cache['date'].min()} to {df_cache['date'].max()}, symbols: {df_cache['symbol'].nunique()}")

    # 2. Harmonize schemas
    for name, df in [("v2", df_v2), ("mod", df_mod), ("cache", df_cache)]:
        for c in REQUIRED_COLS:
            if c not in df.columns:
                raise ValueError(f"Missing column '{c}' in {name}")

    # Standardize string and float formats
    def clean_df(df: pd.DataFrame) -> pd.DataFrame:
        df = df[REQUIRED_COLS].copy()
        df["symbol"] = df["symbol"].astype(str).str.strip()
        df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
        for num_col in ["open", "high", "low", "close", "volume"]:
            df[num_col] = pd.to_numeric(df[num_col], errors="coerce").fillna(0.0)
        return df

    df_v2 = clean_df(df_v2)
    df_mod = clean_df(df_mod)
    df_cache = clean_df(df_cache)

    # 3. Priority Consolidation
    log("\n--- 2. Executing Priority Merging & Deduplication ---")
    # Official priority set: v2 + mod
    df_official = pd.concat([df_v2, df_mod], ignore_index=True)
    df_official = df_official.drop_duplicates(subset=["symbol", "date"], keep="last")
    log(f"Combined official adjusted bars (2016-2026): {len(df_official):,} bars across {df_official['symbol'].nunique()} symbols")

    # Identify keys already in official set
    official_keys = set(zip(df_official["symbol"], df_official["date"]))
    cache_keys = list(zip(df_cache["symbol"], df_cache["date"]))

    mask_cache_new = [k not in official_keys for k in cache_keys]
    df_cache_new = df_cache[mask_cache_new].copy()
    log(f"Price cache backfill bars (prior to 2016 + non-overlapping): {len(df_cache_new):,} bars")

    # Combine all
    df_consolidated = pd.concat([df_official, df_cache_new], ignore_index=True)
    log(f"Total raw merged bars: {len(df_consolidated):,}")

    # 4. Assert Invariants
    log("\n--- 3. Verifying Quality Invariants ---")
    # Sort strictly by symbol and date
    df_consolidated = df_consolidated.sort_values(["symbol", "date"]).reset_index(drop=True)

    # Check duplicates
    dup_mask = df_consolidated.duplicated(subset=["symbol", "date"], keep=False)
    num_dups = int(dup_mask.sum())
    log(f"Duplicate (symbol, date) keys: {num_dups}")
    assert num_dups == 0, f"FATAL: Found {num_dups} duplicate keys in consolidated dataset!"

    # Date range assertion
    min_date = df_consolidated["date"].min()
    max_date = df_consolidated["date"].max()
    log(f"Consolidated Date Horizon: {min_date} to {max_date}")
    assert min_date <= "2007-01-05", f"Start date {min_date} does not cover January 2007!"
    assert max_date >= "2026-08-31", f"End date {max_date} does not cover August 2026!"

    total_symbols = df_consolidated["symbol"].nunique()
    total_trading_days = df_consolidated["date"].nunique()
    log(f"Total Unique Symbols:     {total_symbols:,}")
    log(f"Total Unique Trading Days: {total_trading_days:,} days")
    log(f"Total Price Bars:          {len(df_consolidated):,} bars")

    # 5. Persist to Parquet
    log("\n--- 4. Persisting Consolidated Dataset ---")
    df_consolidated.to_parquet(OUT_PATH, engine="pyarrow", index=False)
    out_size = OUT_PATH.stat().st_size
    out_sha = sha256_file(OUT_PATH)
    log(f"Exported: {OUT_PATH}")
    log(f"File Size: {out_size:,} bytes ({out_size / (1024*1024):.2f} MB)")
    log(f"SHA-256:   {out_sha}")

    log("\n" + "=" * 80)
    log("TASK 2 COMPLETE: MAXIMUM BHAVCOPY CONSOLIDATION SUCCESSFUL (PASS)")
    log("=" * 80)

    # Save log
    with open(RAW_DIR / "consolidation_log.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines) + "\n")

if __name__ == "__main__":
    main()
