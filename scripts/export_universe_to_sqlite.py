#!/usr/bin/env python3
"""
Parquet-to-SQLite Universe Export Bridge for Pydroid 3
Directive: DIR-PROD-PYDROID3-PORT-01 (Standing Gate HALT-16)

Reads the master PIT universe parquet (2,146,531 rows) and exports
to an optimized, indexed SQLite 3 database in Project_MIP_Pydroid3.
"""

import os
import sys
import time
import shutil
import sqlite3
import pandas as pd
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
PARQUET_PATH = BASE_DIR / "data" / "universe" / "nifty500_pit_universe.parquet"
SECTOR_MAP_PATH = BASE_DIR / "data" / "universe" / "symbol_sector_map.json"
CALENDAR_PATH = BASE_DIR / "data" / "trading_calendar.txt"
ENV_PATH = BASE_DIR / ".env"

# Target Directory
DEFAULT_TARGET = Path("/storage/emulated/0/Documents/Project_MIP_Pydroid3")
if not DEFAULT_TARGET.parent.exists():
    DEFAULT_TARGET = Path("/sdcard/Documents/Project_MIP_Pydroid3")


def export_universe(target_dir: Path = DEFAULT_TARGET):
    start_time = time.time()
    print("=" * 70)
    print(" PROJECT MIP -> PYDROID 3 SQLITE EXPORT BRIDGE")
    print(f" Source Parquet: {PARQUET_PATH}")
    print(f" Target Directory: {target_dir}")
    print("=" * 70)

    if not PARQUET_PATH.exists():
        raise FileNotFoundError(f"Source parquet not found: {PARQUET_PATH}")

    # Ensure target directory structure exists
    data_dir = target_dir / "data"
    pydroid_core_dir = target_dir / "pydroid_core"
    tests_dir = target_dir / "tests"
    reports_dir = target_dir / "reports"

    for d in [data_dir, pydroid_core_dir, tests_dir, reports_dir]:
        d.mkdir(parents=True, exist_ok=True)
    print(f"✓ Target directories initialized under {target_dir}")

    # Copy metadata files
    if SECTOR_MAP_PATH.exists():
        shutil.copy2(SECTOR_MAP_PATH, data_dir / "symbol_sector_map.json")
        print(f"✓ Copied symbol_sector_map.json -> {data_dir / 'symbol_sector_map.json'}")
    else:
        print(f"⚠ Warning: {SECTOR_MAP_PATH} not found!")

    if CALENDAR_PATH.exists():
        shutil.copy2(CALENDAR_PATH, data_dir / "trading_calendar.txt")
        print(f"✓ Copied trading_calendar.txt -> {data_dir / 'trading_calendar.txt'}")
    else:
        print(f"⚠ Warning: {CALENDAR_PATH} not found!")

    # Copy .env and create .env.example
    env_example_content = (
        "# Project MIP Pydroid 3 Configuration\n"
        "TELEGRAM_BOT_TOKEN=your_bot_token_here\n"
        "TELEGRAM_CHAT_ID=your_chat_id_here\n"
    )
    with open(target_dir / ".env.example", "w", encoding="utf-8") as f:
        f.write(env_example_content)
    print(f"✓ Created {target_dir / '.env.example'}")

    if ENV_PATH.exists():
        shutil.copy2(ENV_PATH, target_dir / ".env")
        print(f"✓ Copied live .env -> {target_dir / '.env'}")

    # Load Parquet
    print("\nReading master Parquet into memory...")
    t0 = time.time()
    df = pd.read_parquet(PARQUET_PATH)
    read_duration = time.time() - t0
    total_rows = len(df)
    print(f"✓ Ingested {total_rows:,} rows in {read_duration:.2f}s")
    print(f"  Columns: {list(df.columns)}")
    print(f"  Unique Symbols: {df['symbol'].nunique():,}")
    print(f"  Date Range: {df['date'].min()} to {df['date'].max()}")

    # Prepare SQLite database
    db_path = data_dir / "universe.db"
    if db_path.exists():
        print(f"Removing existing database: {db_path}")
        db_path.unlink()

    print(f"\nConnecting to SQLite: {db_path} ...")
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Performance pragmas for bulk load
    cursor.execute("PRAGMA synchronous = OFF;")
    cursor.execute("PRAGMA journal_mode = MEMORY;")
    cursor.execute("PRAGMA cache_size = 100000;")
    cursor.execute("PRAGMA temp_store = MEMORY;")

    print("Creating table schema...")
    cursor.execute("""
        CREATE TABLE prices (
            date TEXT NOT NULL,
            symbol TEXT NOT NULL,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume REAL,
            is_delisted INTEGER DEFAULT 0
        );
    """)

    # Ensure types
    df['date'] = df['date'].astype(str)
    df['symbol'] = df['symbol'].astype(str)
    df['open'] = df['open'].astype(float)
    df['high'] = df['high'].astype(float)
    df['low'] = df['low'].astype(float)
    df['close'] = df['close'].astype(float)
    df['volume'] = df['volume'].astype(float)
    df['is_delisted'] = df['is_delisted'].astype(int)

    # Insert rows in chunks
    chunk_size = 100000
    insert_sql = """
        INSERT INTO prices (date, symbol, open, high, low, close, volume, is_delisted)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
    """

    print(f"Inserting {total_rows:,} rows in chunks of {chunk_size:,}...")
    t_insert = time.time()
    tuples_data = [
        tuple(x) for x in df[['date', 'symbol', 'open', 'high', 'low', 'close', 'volume', 'is_delisted']].to_numpy()
    ]
    
    for i in range(0, total_rows, chunk_size):
        chunk = tuples_data[i:i + chunk_size]
        cursor.executemany(insert_sql, chunk)
        conn.commit()
        pct = min(100.0, (i + len(chunk)) / total_rows * 100.0)
        sys.stdout.write(f"\r  Progress: {pct:5.1f}% ({min(i + chunk_size, total_rows):,}/{total_rows:,})")
        sys.stdout.flush()

    insert_duration = time.time() - t_insert
    print(f"\n✓ Insert completed in {insert_duration:.2f}s ({(total_rows / insert_duration):,.0f} rows/s)")

    # Build Indices
    print("\nBuilding compound indices...")
    t_idx = time.time()
    
    print("  Creating idx_prices_date ON prices (date)...")
    cursor.execute("CREATE INDEX idx_prices_date ON prices (date);")
    
    print("  Creating idx_prices_sym_date ON prices (symbol, date)...")
    cursor.execute("CREATE INDEX idx_prices_sym_date ON prices (symbol, date);")
    
    print("  Creating idx_prices_sym ON prices (symbol)...")
    cursor.execute("CREATE INDEX idx_prices_sym ON prices (symbol);")

    print("  Running ANALYZE for query optimizer statistics...")
    cursor.execute("ANALYZE;")
    conn.commit()
    idx_duration = time.time() - t_idx
    print(f"✓ Indices created and analyzed in {idx_duration:.2f}s")

    # Verification Queries
    print("\nRunning Verification Audit Queries...")
    cursor.execute("SELECT COUNT(*) FROM prices;")
    db_row_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT symbol) FROM prices;")
    db_sym_count = cursor.fetchone()[0]

    cursor.execute("SELECT MIN(date), MAX(date) FROM prices;")
    db_min_date, db_max_date = cursor.fetchone()

    cursor.execute("SELECT COUNT(*) FROM prices WHERE close <= 0 OR open <= 0 OR high <= 0 OR low <= 0;")
    non_positive_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM prices WHERE date IS NULL OR symbol IS NULL OR close IS NULL;")
    null_count = cursor.fetchone()[0]

    db_size_bytes = db_path.stat().st_size
    db_size_mb = db_size_bytes / (1024 * 1024)

    conn.close()

    print("=" * 70)
    print(" VERIFICATION AUDIT RESULTS:")
    print(f"  Database Path:       {db_path}")
    print(f"  Database File Size:  {db_size_mb:.2f} MB ({db_size_bytes:,} bytes)")
    print(f"  Total Row Count:     {db_row_count:,} (Parquet: {total_rows:,})")
    print(f"  Distinct Symbols:    {db_sym_count:,} (Parquet: {df['symbol'].nunique():,})")
    print(f"  Date Bounds:         {db_min_date} to {db_max_date}")
    print(f"  Non-Positive Prices: {non_positive_count}")
    print(f"  Null Values:         {null_count}")
    print("=" * 70)

    # Invariant assertions
    assert db_row_count == total_rows, f"Row count mismatch! DB: {db_row_count}, Parquet: {total_rows}"
    assert db_sym_count == df['symbol'].nunique(), f"Symbol count mismatch!"
    assert db_min_date == df['date'].min(), f"Min date mismatch!"
    assert db_max_date == df['date'].max(), f"Max date mismatch!"
    assert non_positive_count == 0, f"Found {non_positive_count} non-positive prices!"
    assert null_count == 0, f"Found {null_count} null fields!"

    elapsed = time.time() - start_time
    print(f"\n[SUCCESS] Parquet to SQLite export completed in {elapsed:.2f}s with 100% integrity match!")
    return db_path


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_TARGET
    export_universe(target)
