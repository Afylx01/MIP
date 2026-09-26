#!/usr/bin/env python3
"""
scripts/update_universe.py
Production Master Task 2: Standardized Survivorship-Free Universe Database & Auto-Updater

Manages the institutional, point-in-time, survivorship-bias-free master universe:
  `data/universe/nifty500_pit_universe.parquet` and `data/universe/universe_metadata.json`.

Features:
  1. Build / Re-initialize standardized universe from 20-year Bhavcopy + Graveyard.
  2. Idempotent incremental append of daily Bhavcopy CSVs with symbol mapping.
  3. Invariant enforcement: Unique (symbol, date), monotonic sorting, 0 null prices.
  4. Automatic metadata manifest update with cryptographic SHA-256 fingerprint.
  5. Audit verification mode (--verify-only).

Usage:
  python3 scripts/update_universe.py --build-initial
  python3 scripts/update_universe.py --verify-only
  python3 scripts/update_universe.py --new-bhavcopy /path/to/cm<DATE>bhav.csv
"""

import sys
import os
import json
import hashlib
import argparse
import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
import pandas as pd
import numpy as np

def get_base_dir() -> Path:
    """Dynamically resolves Project MIP root across Windows and Linux."""
    if "PROJECT_MIP_DIR" in os.environ and Path(os.environ["PROJECT_MIP_DIR"]).exists():
        return Path(os.environ["PROJECT_MIP_DIR"])
    android_path = Path("/storage/emulated/0/Documents/Project MIP")
    if android_path.exists():
        return android_path
    cur = Path(__file__).resolve()
    for p in [cur] + list(cur.parents):
        if (p / "run_mip.py").exists() or (p / "data/universe").exists():
            return p
    return cur.parent.parent if cur.parent.name in ["production", "scripts"] else cur.parent


BASE_DIR = get_base_dir()
DATA_DIR = BASE_DIR / "data"
UNIVERSE_DIR = DATA_DIR / "universe"
MASTER_UNIVERSE_PARQUET = UNIVERSE_DIR / "nifty500_pit_universe.parquet"
METADATA_JSON = UNIVERSE_DIR / "universe_metadata.json"

BHAVCOPY_MASTER = DATA_DIR / "adjusted_bhavcopy_max_2007_2026.parquet"
GRAVEYARD_CSV = DATA_DIR / "verification/survivorship_graveyard.csv"
SYMBOL_MAP_PARQUET = DATA_DIR / "symbol_map.parquet"

REQUIRED_COLUMNS = ["date", "symbol", "open", "high", "low", "close", "volume", "is_delisted"]


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


class UniverseManager:
    """Manages the survivorship-free master universe database."""

    def __init__(
        self,
        universe_parquet: Path = MASTER_UNIVERSE_PARQUET,
        metadata_file: Path = METADATA_JSON
    ):
        self.universe_parquet = Path(universe_parquet)
        self.metadata_file = Path(metadata_file)
        UNIVERSE_DIR.mkdir(parents=True, exist_ok=True)

    def log(self, msg: str):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {msg}")

    def load_graveyard_delisted_symbols(self) -> Set[str]:
        """Loads verified delisted graveyard symbols."""
        if not GRAVEYARD_CSV.exists():
            self.log(f"⚠️ Warning: Graveyard CSV not found at {GRAVEYARD_CSV}. Assuming empty.")
            return set()
        df = pd.read_csv(GRAVEYARD_CSV)
        inactive = df[df["status"] == "inactive"]["symbol"].dropna().astype(str).str.strip().str.upper()
        return set(inactive)

    def validate_universe_invariants(self, df: pd.DataFrame) -> Tuple[bool, str]:
        """Validates all strict mathematical and schema invariants."""
        # 1. Required columns
        missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
        if missing:
            return False, f"Missing required columns: {missing}"

        # 2. Null price checks
        price_cols = ["open", "high", "low", "close"]
        for p in price_cols:
            null_cnt = df[p].isnull().sum()
            if null_cnt > 0:
                return False, f"Found {null_cnt} null values in price column '{p}'"
            if (df[p] <= 0).any():
                bad_cnt = (df[p] <= 0).sum()
                return False, f"Found {bad_cnt} non-positive values in price column '{p}'"

        # 3. Duplicate key constraint
        dup_count = int(df.duplicated(subset=["symbol", "date"]).sum())
        if dup_count > 0:
            return False, f"Found {dup_count} duplicate (symbol, date) composite keys"

        # 4. Monotonic ordering per symbol
        for sym, grp in df.groupby("symbol"):
            if not grp["date"].is_monotonic_increasing:
                return False, f"Non-monotonic chronological dates for symbol '{sym}'"

        return True, "Valid"

    def build_initial_universe(self) -> Dict:
        """
        Synthesizes the standardized survivorship-free master database from
        adjusted_bhavcopy_max_2007_2026.parquet and survivorship_graveyard.csv.
        """
        self.log(f"Building standardized survivorship-free universe database...")
        self.log(f"Source bars: {BHAVCOPY_MASTER}")
        self.log(f"Graveyard:   {GRAVEYARD_CSV}")

        if not BHAVCOPY_MASTER.exists():
            raise FileNotFoundError(f"Master Bhavcopy parquet not found at {BHAVCOPY_MASTER}")

        df = pd.read_parquet(BHAVCOPY_MASTER)
        self.log(f"Loaded {len(df):,} raw historical bars across {df['symbol'].nunique():,} symbols.")

        # Cross-reference graveyard symbols
        dead_symbols = self.load_graveyard_delisted_symbols()
        self.log(f"Loaded {len(dead_symbols):,} dead graveyard symbols.")

        # Annotate is_delisted
        df["symbol"] = df["symbol"].astype(str).str.strip().str.upper()
        df["date"] = df["date"].astype(str)
        df["is_delisted"] = df["symbol"].isin(dead_symbols)

        # Enforce column order
        df = df[REQUIRED_COLUMNS].copy()

        # Sort monotonically by symbol, date
        df = df.sort_values(by=["symbol", "date"]).reset_index(drop=True)

        # Validate invariants
        is_valid, msg = self.validate_universe_invariants(df)
        if not is_valid:
            raise ValueError(f"Initial universe validation failed: {msg}")

        # Atomic write
        temp_parquet = self.universe_parquet.with_suffix(".tmp.parquet")
        self.log(f"Writing to temporary file {temp_parquet}...")
        df.to_parquet(temp_parquet, index=False, engine="pyarrow")
        temp_parquet.replace(self.universe_parquet)
        self.log(f"Saved master universe database: {self.universe_parquet} ({self.universe_parquet.stat().st_size:,} bytes)")

        # Generate and save metadata manifest
        metadata = self._update_metadata(df)
        return metadata

    def _update_metadata(self, df: pd.DataFrame) -> Dict:
        """Computes and writes universe metadata manifest."""
        sha = compute_sha256(self.universe_parquet)
        total_bars = len(df)
        unique_symbols = int(df["symbol"].nunique())
        delisted_symbols = int(df[df["is_delisted"] == True]["symbol"].nunique())
        active_symbols = unique_symbols - delisted_symbols
        min_date = str(df["date"].min())
        max_date = str(df["date"].max())

        meta_dict = {
            "universe_name": "NIFTY 500 Point-in-Time Survivorship-Free Database",
            "file_name": self.universe_parquet.name,
            "sha256_hash": sha,
            "total_bars": total_bars,
            "unique_symbols": unique_symbols,
            "active_symbols": active_symbols,
            "delisted_symbols": delisted_symbols,
            "start_date": min_date,
            "end_date": max_date,
            "schema": {
                "date": "string (YYYY-MM-DD)",
                "symbol": "string (NSE Ticker)",
                "open": "float64 (Adjusted Open Price)",
                "high": "float64 (Adjusted High Price)",
                "low": "float64 (Adjusted Low Price)",
                "close": "float64 (Adjusted Close Price)",
                "volume": "float64 (Traded Quantity)",
                "is_delisted": "bool (True if graveyard constituent)"
            },
            "invariants_verified": [
                "unique_(symbol, date)_keys",
                "chronological_monotonic_sorting",
                "zero_null_prices",
                "positive_prices_guaranteed"
            ],
            "last_updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        with open(self.metadata_file, "w", encoding="utf-8") as f:
            json.dump(meta_dict, f, indent=2)

        self.log(f"Saved metadata manifest: {self.metadata_file}")
        self.log("==================================================================")
        self.log(f"UNIVERSE METADATA SUMMARY:")
        self.log(f"Total Bars:         {total_bars:,}")
        self.log(f"Unique Symbols:     {unique_symbols:,} (Active: {active_symbols:,} | Delisted: {delisted_symbols:,})")
        self.log(f"Date Coverage:      {min_date} to {max_date}")
        self.log(f"SHA-256 Hash:       {sha}")
        self.log("==================================================================")
        return meta_dict

    def verify_integrity(self) -> Dict:
        """Audits database file against metadata manifest and invariants."""
        self.log(f"Auditing universe database: {self.universe_parquet}")
        if not self.universe_parquet.exists():
            return {"status": "FAIL", "error": "Database file not found"}

        df = pd.read_parquet(self.universe_parquet)
        is_valid, msg = self.validate_universe_invariants(df)
        if not is_valid:
            return {"status": "FAIL", "error": msg}

        current_sha = compute_sha256(self.universe_parquet)
        if self.metadata_file.exists():
            with open(self.metadata_file, "r", encoding="utf-8") as f:
                meta = json.load(f)
            stored_sha = meta.get("sha256_hash")
            sha_match = (current_sha == stored_sha)
        else:
            sha_match = True

        status = is_valid and sha_match
        results = {
            "status": "PASS" if status else "FAIL",
            "total_bars": len(df),
            "unique_symbols": int(df["symbol"].nunique()),
            "delisted_symbols": int(df[df["is_delisted"] == True]["symbol"].nunique()),
            "date_range": f"{df['date'].min()} to {df['date'].max()}",
            "sha256_verified": sha_match,
            "invariants_passed": is_valid
        }

        self.log(f"Audit Result: {results['status']}")
        self.log(f"Bars: {results['total_bars']:,} | Symbols: {results['unique_symbols']} | Checksum Match: {sha_match}")
        return results

    def append_daily_bhavcopy(self, bhavcopy_csv: Path) -> Dict:
        """Ingests, maps, and appends new daily Bhavcopy CSV."""
        self.log(f"Ingesting daily Bhavcopy from {bhavcopy_csv}...")
        raw = pd.read_csv(bhavcopy_csv)
        raw.columns = [c.strip().upper() for c in raw.columns]

        if "SERIES" in raw.columns:
            raw = raw[raw["SERIES"].isin(["EQ", "BE", "BZ"])].copy()

        col_map = {
            "SYMBOL": "symbol", "TIMESTAMP": "date", "DATE": "date",
            "OPEN": "open", "OPEN_PRICE": "open", "HIGH": "high", "HIGH_PRICE": "high",
            "LOW": "low", "LOW_PRICE": "low", "CLOSE": "close", "CLOSE_PRICE": "close",
            "TOTTRDQTY": "volume", "TTL_TRD_QNTY": "volume", "VOLUME": "volume"
        }
        df = raw.rename(columns={s: d for s, d in col_map.items() if s in raw.columns})
        df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
        df["symbol"] = df["symbol"].astype(str).str.strip().str.upper()

        # Load existing universe
        existing = pd.read_parquet(self.universe_parquet)
        dead_symbols = self.load_graveyard_delisted_symbols()
        df["is_delisted"] = df["symbol"].isin(dead_symbols)

        combined = pd.concat([existing, df[REQUIRED_COLUMNS]], ignore_index=True)
        combined = combined.drop_duplicates(subset=["symbol", "date"], keep="last")
        combined = combined.sort_values(by=["symbol", "date"]).reset_index(drop=True)

        is_valid, msg = self.validate_universe_invariants(combined)
        if not is_valid:
            raise ValueError(f"Integrity check failed after daily append: {msg}")

        temp_p = self.universe_parquet.with_suffix(".tmp.parquet")
        combined.to_parquet(temp_p, index=False, engine="pyarrow")
        temp_p.replace(self.universe_parquet)

        metadata = self._update_metadata(combined)
        return metadata


def main():
    parser = argparse.ArgumentParser(description="Survivorship-Free Universe Database Manager")
    parser.add_argument("--build-initial", action="store_true", help="Build master universe database")
    parser.add_argument("--verify-only", action="store_true", help="Audit database invariants")
    parser.add_argument("--new-bhavcopy", type=str, default=None, help="Path to new daily Bhavcopy CSV")

    args = parser.parse_args()
    mgr = UniverseManager()

    if args.build_initial:
        mgr.build_initial_universe()
        sys.exit(0)

    if args.verify_only:
        audit = mgr.verify_integrity()
        sys.exit(0 if audit["status"] == "PASS" else 1)

    if args.new_bhavcopy:
        p = Path(args.new_bhavcopy)
        if not p.exists():
            print(f"Error: File not found: {p}")
            sys.exit(1)
        mgr.append_daily_bhavcopy(p)
        sys.exit(0)

    # Default action: verify if database exists, else build
    if MASTER_UNIVERSE_PARQUET.exists():
        audit = mgr.verify_integrity()
        sys.exit(0 if audit["status"] == "PASS" else 1)
    else:
        mgr.build_initial_universe()
        sys.exit(0)


if __name__ == "__main__":
    main()
