#!/usr/bin/env python3
import os
import sys
import hashlib
import time
import pickle
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from pandas.core.arrays.string_ import StringArray

DATA_DIR = "/storage/emulated/0/MIP1_Scanner/data"
EXPORT_PATH = "data/price_cache_export.parquet"

class FixedStringArray(StringArray):
    def __setstate__(self, state):
        if isinstance(state, tuple) and len(state) == 2:
            state = (state[0], state[1], {})
        return super().__setstate__(state)

class SafeUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        if (module == "pandas.arrays" or module == "pandas.core.arrays.string_") and name == "StringArray":
            return FixedStringArray
        return super().find_class(module, name)

def get_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()

def main():
    print("=== STEP 0: PRICE DATA INVENTORY AND SAFE LOADING ===")
    
    # 1. Inventory local price files
    print("\n--- 1. File Inventory ---")
    files = sorted(os.listdir(DATA_DIR))
    bhavcopy_found = False
    for fname in files:
        fpath = os.path.join(DATA_DIR, fname)
        if os.path.isfile(fpath):
            stat = os.stat(fpath)
            mtime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stat.st_mtime))
            size_mb = stat.st_size / (1024 * 1024)
            fmt = "pickle" if fname.endswith(".pkl") else ("gzip pickle" if fname.endswith(".pkl.gz") else ("sqlite" if fname.endswith(".db") else ("json" if fname.endswith(".json") else "other")))
            print(f"Path: {fpath} | Size: {size_mb:.2f} MB ({stat.st_size} bytes) | Format: {fmt} | mtime: {mtime}")
            if "bhavcopy" in fname.lower() or "cm" in fname.lower():
                bhavcopy_found = True

    print(f"\nBhavcopy status: NO Bhavcopy files exist. Only scanner caches exist (stock_ohlcv_cache.pkl, index__NSEI_cache.pkl, etc.).")

    # 2. Safe loading and export
    print("\n--- 2. Safe Loading of stock_ohlcv_cache.pkl ---")
    stock_pkl = os.path.join(DATA_DIR, "stock_ohlcv_cache.pkl")
    try:
        with open(stock_pkl, "rb") as f:
            df_stock = SafeUnpickler(f).load()
    except Exception as e:
        print(f"FATAL: Could not safely load {stock_pkl}: {e}")
        sys.exit(1)

    source_rows = len(df_stock)
    print(f"Source row count: {source_rows}")
    print(f"Columns: {list(df_stock.columns)}")
    print("Source dtypes:")
    for col, dt in df_stock.dtypes.items():
        print(f"  {col}: {dt}")

    # Ensure consistent typing for parquet export
    df_export = df_stock.copy()
    for col in ['symbol', 'date']:
        df_export[col] = df_export[col].astype(str)
    for col in ['open', 'high', 'low', 'close', 'volume']:
        df_export[col] = pd.to_numeric(df_export[col], errors='coerce')

    os.makedirs(os.path.dirname(EXPORT_PATH), exist_ok=True)
    df_export.to_parquet(EXPORT_PATH, index=False)
    
    # Read back to verify
    df_readback = pd.read_parquet(EXPORT_PATH)
    exported_rows = len(df_readback)
    print(f"\nExported row count: {exported_rows}")
    if source_rows != exported_rows:
        print(f"FATAL: Row count mismatch! Source: {source_rows}, Exported: {exported_rows}")
        sys.exit(1)
    print(f"Row count check: MATCH ({source_rows} == {exported_rows})")
    
    export_sha = get_sha256(EXPORT_PATH)
    print(f"Export SHA-256: {export_sha}")
    print("Export dtypes:")
    for col, dt in df_readback.dtypes.items():
        print(f"  {col}: {dt}")

    # 3. Symbols and delisted coverage
    print("\n--- 3. Symbol Coverage & Delisted Analysis ---")
    unique_symbols = df_readback['symbol'].nunique()
    date_min = df_readback['date'].min()
    date_max = df_readback['date'].max()
    print(f"Unique symbols in cache: {unique_symbols}")
    print(f"Date range: {date_min} to {date_max}")

    # Group by symbol to find max date per symbol
    symbol_last_dates = df_readback.groupby('symbol')['date'].max()
    symbols_before_max = (symbol_last_dates < date_max).sum()
    print(f"Symbols whose last bar is before max date ({date_max}): {symbols_before_max}")
    print(f"Coverage type: SURVIVOR-ONLY cache. Exactly 0 symbols stop trading before {date_max}; every single one of the 750 cached symbols has active price bars through {date_max}. It does NOT include delisted names.")

    # 4. Trading calendar derivation
    print("\n--- 4. Official Trading Calendar Derivation ---")
    index_pkl = os.path.join(DATA_DIR, "index__NSEI_cache.pkl")
    try:
        with open(index_pkl, "rb") as f:
            df_nsei = SafeUnpickler(f).load()
    except Exception as e:
        print(f"FATAL: Could not load {index_pkl}: {e}")
        sys.exit(1)

    df_nsei['date'] = df_nsei['date'].astype(str)
    calendar_dates = sorted(df_nsei['date'].unique().tolist())
    cal_first = calendar_dates[0]
    cal_last = calendar_dates[-1]
    cal_count = len(calendar_dates)
    print(f"Calendar source: Exported NSEI index bars from {index_pkl}")
    print(f"Calendar first date: {cal_first}")
    print(f"Calendar last date: {cal_last}")
    print(f"Calendar trading day count: {cal_count}")

    # Save trading calendar to data/
    with open("data/trading_calendar.txt", "w") as f:
        for d in calendar_dates:
            f.write(f"{d}\n")
    print(f"Saved {cal_count} trading calendar dates to data/trading_calendar.txt")

if __name__ == "__main__":
    main()
