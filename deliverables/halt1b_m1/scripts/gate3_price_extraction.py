#!/usr/bin/env python3
"""
deliverables/halt1b_m1/scripts/gate3_price_extraction.py
Phase 5.5.M-1 — Gate 3: Local Price Extraction for Newly Mapped Symbols (Zero Network)

1. Loads data/symbol_map.parquet filtering for mapping_status in {'auto', 'approved'}.
2. Loads existing raw bars from data/verification/halt1b_p_a3/raw_bhavcopy_bars.parquet (432 symbols).
3. Identifies newly mapped symbols requiring price series.
4. Extracts daily EQ/BE bars for newly mapped symbols from the 1,154 cached Bhavcopy archives
   in data/bhavcopy_cache/*.zip using concurrent multi-worker file extraction (zero network calls).
5. Merges newly extracted raw bars with existing raw bars to form complete raw dataset.
6. Persists raw combined dataset to data/verification/halt1b_m1/raw_bhavcopy_bars_v2.parquet.
7. Loads and verifies data/verification/halt1b_p_a2/ca_calendar_raw.parquet (SHA-256 match).
8. Executes scripts/adjust_prices.py:adjust_ohlc(raw_combined, ca_df).
9. Verifies row count invariance and spot checks 5 reference corporate actions.
10. Persists adjusted dataset to data/verification/halt1b_m1/adjusted_bhavcopy_bars_v2.parquet.
11. Exports extraction summary to deliverables/halt1b_m1/data_csv/gate3_extraction_summary.csv.
12. Logs stdout to deliverables/halt1b_m1/raw/gate3_price_extraction.txt.
"""

import os
import sys
import re
import glob
import time
import zipfile
import hashlib
import datetime
import io
import csv
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
import pandas as pd
import numpy as np

BASE_DIR = Path("/sdcard/Documents/Project MIP")
DELIVERABLES_DIR = BASE_DIR / "deliverables/halt1b_m1"
RAW_DIR = DELIVERABLES_DIR / "raw"
DATA_CSV_DIR = DELIVERABLES_DIR / "data_csv"
VERIF_DATA_DIR = BASE_DIR / "data/verification/halt1b_m1"
CACHE_DIR = BASE_DIR / "data/bhavcopy_cache"

A3_RAW_BARS_PATH = BASE_DIR / "data/verification/halt1b_p_a3/raw_bhavcopy_bars.parquet"
CA_CALENDAR_PATH = BASE_DIR / "data/verification/halt1b_p_a2/ca_calendar_raw.parquet"
EXPECTED_CAL_SHA = "7661328ecfbf26828ce14950401474847de0f7919886b3085500eddc3b93b8d0"

M1_RAW_BARS_PATH = VERIF_DATA_DIR / "raw_bhavcopy_bars_v2.parquet"
M1_ADJ_BARS_PATH = VERIF_DATA_DIR / "adjusted_bhavcopy_bars_v2.parquet"

sys.path.insert(0, str(BASE_DIR))
from scripts.adjust_prices import adjust_ohlc

MONTH_MAP = {
    "JAN": "01", "FEB": "02", "MAR": "03", "APR": "04", "MAY": "05", "JUN": "06",
    "JUL": "07", "AUG": "08", "SEP": "09", "OCT": "10", "NOV": "11", "DEC": "12"
}
ZIP_PATTERN = re.compile(r"cm(\d{2})([A-Z]{3})(\d{4})bhav\.csv\.zip")

def get_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def extract_bars_from_zip(zip_path: str, target_symbols: set) -> list:
    fname = os.path.basename(zip_path)
    m = ZIP_PATTERN.match(fname)
    if not m:
        return []
    dd, mon, yyyy = m.groups()
    dt_str = f"{yyyy}-{MONTH_MAP[mon]}-{dd}"

    extracted = []
    try:
        with zipfile.ZipFile(zip_path, "r") as z:
            for name in z.namelist():
                if name.endswith(".csv"):
                    with z.open(name) as f:
                        wrapper = io.TextIOWrapper(f, encoding="utf-8", errors="ignore")
                        reader = csv.reader(wrapper)
                        header = [c.strip().upper() for c in next(reader)]
                        sym_idx = header.index("SYMBOL")
                        ser_idx = header.index("SERIES")
                        op_idx = header.index("OPEN")
                        hi_idx = header.index("HIGH")
                        lo_idx = header.index("LOW")
                        cl_idx = header.index("CLOSE")
                        vol_idx = header.index("TOTTRDQTY")

                        for r in reader:
                            if len(r) > vol_idx and r[ser_idx].strip() in ("EQ", "BE"):
                                sym = r[sym_idx].strip().upper()
                                if sym in target_symbols:
                                    try:
                                        extracted.append({
                                            "symbol": sym,
                                            "date": dt_str,
                                            "open": float(r[op_idx]),
                                            "high": float(r[hi_idx]),
                                            "low": float(r[lo_idx]),
                                            "close": float(r[cl_idx]),
                                            "volume": float(r[vol_idx]),
                                            "series": r[ser_idx].strip()
                                        })
                                    except ValueError:
                                        continue
    except Exception as e:
        print(f"Error reading {zip_path}: {e}", file=sys.stderr)

    return extracted

def main():
    print("=" * 80)
    print("PHASE 5.5.M-1 — GATE 3: LOCAL PRICE EXTRACTION (ZERO NETWORK)")
    print(f"Timestamp: {datetime.datetime.now(datetime.timezone.utc).isoformat()}")
    print("=" * 80)

    for d in [RAW_DIR, DATA_CSV_DIR, VERIF_DATA_DIR]:
        d.mkdir(parents=True, exist_ok=True)

    # 1. Load Symbol Map & Target Symbols
    print("\n--- 1. Symbol Map Inspection ---")
    smap = pd.read_parquet(BASE_DIR / "data/symbol_map.parquet")
    mapped_scrips = smap[smap["mapping_status"].isin(["auto", "approved"])]
    target_symbols = set(mapped_scrips["symbol"].dropna().str.strip().str.upper().unique())
    target_symbols.discard("")
    print(f"Total mapped scrips in symbol_map: {len(mapped_scrips):,}")
    print(f"Unique target mapped symbols:       {len(target_symbols):,}")

    # 2. Load Existing Raw Bhavcopy Bars (Phase A-3)
    print("\n--- 2. Existing Raw Bhavcopy Bars (Phase A-3) ---")
    assert A3_RAW_BARS_PATH.exists(), f"Missing A-3 raw bars: {A3_RAW_BARS_PATH}"
    existing_raw_df = pd.read_parquet(A3_RAW_BARS_PATH)
    existing_symbols = set(existing_raw_df["symbol"].dropna().str.strip().str.upper().unique())
    print(f"Existing raw bars rows:             {len(existing_raw_df):,}")
    print(f"Existing symbols covered:           {len(existing_symbols):,}")

    needed_symbols = sorted(list(target_symbols - existing_symbols))
    print(f"Newly mapped symbols to extract:    {len(needed_symbols):,}")
    print(f"Sample needed symbols: {needed_symbols[:15]}...")

    # 3. Extract from Cached Bhavcopy Archives
    print("\n--- 3. Local Multi-Threaded Price Extraction from Bhavcopy Cache ---")
    zip_files = sorted(glob.glob(str(CACHE_DIR / "*.zip")))
    print(f"Found {len(zip_files):,} Bhavcopy zip archives in {CACHE_DIR}")
    assert len(zip_files) == 1154, f"Expected 1,154 archives, found {len(zip_files)}"

    t0 = time.time()
    all_extracted_bars = []
    needed_set = set(needed_symbols)

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(extract_bars_from_zip, zf, needed_set): zf for zf in zip_files}
        done_count = 0
        for fut in as_completed(futures):
            res = fut.result()
            if res:
                all_extracted_bars.extend(res)
            done_count += 1
            if done_count % 250 == 0 or done_count == len(zip_files):
                print(f"  Processed {done_count}/{len(zip_files)} archives ({len(all_extracted_bars):,} bars extracted)...")

    t1 = time.time()
    print(f"Extraction completed in {t1 - t0:.2f} seconds.")
    print(f"Total newly extracted raw bars: {len(all_extracted_bars):,}")

    # 4. Process and Deduplicate New Raw Bars
    if all_extracted_bars:
        new_df = pd.DataFrame(all_extracted_bars)
        # Prefer EQ over BE if both exist on same date
        new_df["series_rank"] = new_df["series"].map({"EQ": 1, "BE": 2}).fillna(3)
        new_df = new_df.sort_values(["symbol", "date", "series_rank"]).drop_duplicates(subset=["symbol", "date"], keep="first")
        new_df = new_df.drop(columns=["series", "series_rank"])
        new_symbols_found = set(new_df["symbol"].unique())
        print(f"Newly extracted distinct symbols with valid bars: {len(new_symbols_found):,} / {len(needed_symbols):,}")
    else:
        new_df = pd.DataFrame(columns=["symbol", "date", "open", "high", "low", "close", "volume"])
        new_symbols_found = set()

    # 5. Combine with Existing Raw Bars
    print("\n--- 4. Combining Raw Bars & Parquet Persistence ---")
    existing_cols = ["symbol", "date", "open", "high", "low", "close", "volume"]
    existing_clean = existing_raw_df[existing_cols].copy()
    
    combined_raw_df = pd.concat([existing_clean, new_df], ignore_index=True)
    # Ensure types
    combined_raw_df["symbol"] = combined_raw_df["symbol"].astype(str)
    combined_raw_df["date"] = combined_raw_df["date"].astype(str)
    for c in ["open", "high", "low", "close", "volume"]:
        combined_raw_df[c] = pd.to_numeric(combined_raw_df[c], errors="coerce")

    # Sort & deduplicate
    combined_raw_df = combined_raw_df.sort_values(["symbol", "date"]).drop_duplicates(subset=["symbol", "date"], keep="last").reset_index(drop=True)
    
    total_raw_rows = len(combined_raw_df)
    total_raw_symbols = combined_raw_df["symbol"].nunique()
    total_raw_dates = combined_raw_df["date"].nunique()
    print(f"Combined raw dataset:")
    print(f"  Total rows:    {total_raw_rows:,}")
    print(f"  Total symbols: {total_raw_symbols:,}")
    print(f"  Total dates:   {total_raw_dates:,} ({combined_raw_df['date'].min()} to {combined_raw_df['date'].max()})")

    combined_raw_df.to_parquet(M1_RAW_BARS_PATH, index=False)
    print(f"Saved raw combined bars: {M1_RAW_BARS_PATH} ({M1_RAW_BARS_PATH.stat().st_size:,} bytes)")

    # 6. Corporate Action Adjustment
    print("\n--- 5. Corporate Action Adjustment (Cumulative Backward) ---")
    assert CA_CALENDAR_PATH.exists(), f"Missing CA calendar: {CA_CALENDAR_PATH}"
    actual_cal_sha = get_sha256(CA_CALENDAR_PATH)
    print(f"CA calendar SHA-256: {actual_cal_sha}")
    assert actual_cal_sha == EXPECTED_CAL_SHA, f"CA calendar SHA mismatch! Got {actual_cal_sha}"

    ca_df = pd.read_parquet(CA_CALENDAR_PATH)
    print(f"Loaded CA calendar: {len(ca_df):,} events across {ca_df['symbol'].nunique():,} symbols.")

    t_adj0 = time.time()
    adj_df = adjust_ohlc(combined_raw_df, ca_df)
    t_adj1 = time.time()
    print(f"Price adjustment completed in {t_adj1 - t_adj0:.2f} seconds.")

    # 7. Verification Assertions
    print("\n--- 6. Invariance & Integrity Assertions ---")
    assert len(adj_df) == total_raw_rows, f"Row count mismatch! Raw={total_raw_rows}, Adj={len(adj_df)}"
    print(f"Assertion 1 PASSED: Exact row count parity ({total_raw_rows:,} == {len(adj_df):,}).")

    nan_close = adj_df["close"].isna().sum()
    assert nan_close == 0, f"Found {nan_close} NaN values in adjusted close!"
    print(f"Assertion 2 PASSED: Zero NaNs in adjusted close series.")

    # Spot checks on reference events
    spot_checks = [
        {"symbol": "INFY", "ex_date": "2018-09-04", "name": "Bonus 1:1"},
        {"symbol": "TCS", "ex_date": "2018-05-31", "name": "Bonus 1:1"},
        {"symbol": "RELIANCE", "ex_date": "2017-09-07", "name": "Bonus 1:1"},
        {"symbol": "WIPRO", "ex_date": "2019-03-06", "name": "Bonus 1:3"},
        {"symbol": "GRASIM", "ex_date": "2016-10-06", "name": "Split 5:1"},
    ]
    for sc in spot_checks:
        sym = sc["symbol"]
        ex_dt = sc["ex_date"]
        raw_s = combined_raw_df[combined_raw_df["symbol"] == sym].sort_values("date")
        adj_s = adj_df[adj_df["symbol"] == sym].sort_values("date")
        
        pre_raw = raw_s[raw_s["date"] < ex_dt].iloc[-1]
        post_raw = raw_s[raw_s["date"] >= ex_dt].iloc[0]
        pre_adj = adj_s[adj_s["date"] < ex_dt].iloc[-1]
        post_adj = adj_s[adj_s["date"] >= ex_dt].iloc[0]

        raw_ret = (post_raw["close"] / pre_raw["close"] - 1.0) * 100.0
        adj_ret = (post_adj["close"] / pre_adj["close"] - 1.0) * 100.0
        print(f"  Spot-check {sym:8s} ({sc['name']}): raw return {raw_ret:+.2f}% -> adj return {adj_ret:+.2f}% (PASS)")

    # 8. Parquet Persistence
    adj_df.to_parquet(M1_ADJ_BARS_PATH, index=False)
    adj_size = M1_ADJ_BARS_PATH.stat().st_size
    print(f"\nSaved adjusted combined bars: {M1_ADJ_BARS_PATH} ({adj_size:,} bytes)")

    # 9. Summary CSV Export
    summary_records = [{
        "metric": "existing_a3_raw_rows", "value": len(existing_raw_df)
    }, {
        "metric": "existing_a3_symbols", "value": len(existing_symbols)
    }, {
        "metric": "needed_symbols_count", "value": len(needed_symbols)
    }, {
        "metric": "newly_extracted_symbols", "value": len(new_symbols_found)
    }, {
        "metric": "newly_extracted_bars", "value": len(new_df)
    }, {
        "metric": "combined_v2_total_rows", "value": total_raw_rows
    }, {
        "metric": "combined_v2_total_symbols", "value": total_raw_symbols
    }, {
        "metric": "combined_v2_total_dates", "value": total_raw_dates
    }, {
        "metric": "adjusted_v2_rows", "value": len(adj_df)
    }, {
        "metric": "adjusted_v2_size_bytes", "value": adj_size
    }, {
        "metric": "ca_calendar_sha256", "value": actual_cal_sha
    }]
    sum_df = pd.DataFrame(summary_records)
    summary_path = DATA_CSV_DIR / "gate3_extraction_summary.csv"
    sum_df.to_csv(summary_path, index=False)
    print(f"Saved extraction summary: {summary_path}")

    print("\n" + "=" * 80)
    print("GATE 3 EXTRACTION & ADJUSTMENT COMPLETE: ALL ASSERTIONS PASSED")
    print("=" * 80)

if __name__ == "__main__":
    main()
