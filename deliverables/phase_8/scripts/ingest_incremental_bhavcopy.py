#!/usr/bin/env python3
"""
deliverables/phase_8/scripts/ingest_incremental_bhavcopy.py
Phase 8 Task 1: Incremental Bhavcopy Ingestion Engine

Provides institutional-grade incremental ingestion of daily Bhavcopies into the
master parquet price store (data/adjusted_bhavcopy_max_2007_2026.parquet).

Invariants Enforced:
  1. Unique (symbol, date) primary key constraint (0 duplicates).
  2. Strict monotonic date ordering per symbol.
  3. Zero null or negative prices across Open, High, Low, Close.
  4. Safe atomic writes with temporary file replacement.

Usage:
  python3 ingest_incremental_bhavcopy.py --verify-only
  python3 ingest_incremental_bhavcopy.py --self-test
  python3 ingest_incremental_bhavcopy.py --new-csv path/to/bhavcopy.csv [--dry-run]
"""

import sys
import os
import argparse
import datetime
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np

BASE_DIR = Path("/storage/emulated/0/Documents/Project MIP")
DATA_DIR = BASE_DIR / "data"
DELIV_DIR = BASE_DIR / "deliverables/phase_8"
RAW_DIR = DELIV_DIR / "raw"
DATA_CSV_DIR = DELIV_DIR / "data_csv"

DEFAULT_MASTER_PARQUET = DATA_DIR / "adjusted_bhavcopy_max_2007_2026.parquet"
LOG_FILE = RAW_DIR / "ingest_incremental_bhavcopy.log"

REQUIRED_COLUMNS = ["symbol", "date", "open", "high", "low", "close", "volume"]


class IncrementalBhavcopyIngestor:
    """Manages appending and validating daily EOD bars in master parquet format."""

    def __init__(self, master_parquet_path: Path = DEFAULT_MASTER_PARQUET):
        self.master_parquet_path = Path(master_parquet_path)
        RAW_DIR.mkdir(parents=True, exist_ok=True)
        DATA_CSV_DIR.mkdir(parents=True, exist_ok=True)

    def log(self, msg: str, to_console: bool = True):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted = f"[{timestamp}] {msg}"
        if to_console:
            print(formatted)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(formatted + "\n")

    def load_master(self) -> pd.DataFrame:
        """Loads current master parquet file."""
        if not self.master_parquet_path.exists():
            raise FileNotFoundError(f"Master parquet not found at {self.master_parquet_path}")
        df = pd.read_parquet(self.master_parquet_path)
        return df

    def validate_bars(self, df: pd.DataFrame, is_incoming: bool = False) -> Tuple[bool, str]:
        """Validates schema, datatypes, and non-null positive constraints."""
        missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
        if missing:
            return False, f"Missing required columns: {missing}"

        # Null checks
        null_counts = df[REQUIRED_COLUMNS].isnull().sum()
        if null_counts.any():
            bad_cols = null_counts[null_counts > 0].to_dict()
            return False, f"Null values detected: {bad_cols}"

        # Positive price checks
        price_cols = ["open", "high", "low", "close"]
        for p in price_cols:
            if (df[p] <= 0).any():
                bad_count = (df[p] <= 0).sum()
                return False, f"Found {bad_count} non-positive values in column '{p}'"

        # High >= Low check on incoming new bars
        if is_incoming:
            if (df["high"] < df["low"]).any():
                bad_hl = (df["high"] < df["low"]).sum()
                return False, f"Found {bad_hl} rows where High < Low in incoming bars"

        # Unique key check within input dataframe
        dup_count = df.duplicated(subset=["symbol", "date"]).sum()
        if dup_count > 0:
            return False, f"Found {dup_count} duplicate (symbol, date) keys in incoming bars"

        return True, "Valid"

    def parse_nse_bhavcopy_csv(self, csv_path: Path) -> pd.DataFrame:
        """Parses standard NSE CM Bhavcopy CSV format."""
        raw = pd.read_csv(csv_path)
        raw.columns = [c.strip().upper() for c in raw.columns]

        # Handle SERIES filtering if available
        if "SERIES" in raw.columns:
            raw = raw[raw["SERIES"].isin(["EQ", "BE", "BZ"])].copy()

        col_map = {
            "SYMBOL": "symbol",
            "TIMESTAMP": "date",
            "DATE": "date",
            "TRADEDATE": "date",
            "OPEN": "open",
            "OPEN_PRICE": "open",
            "HIGH": "high",
            "HIGH_PRICE": "high",
            "LOW": "low",
            "LOW_PRICE": "low",
            "CLOSE": "close",
            "CLOSE_PRICE": "close",
            "TOTTRDQTY": "volume",
            "TTL_TRD_QNTY": "volume",
            "VOLUME": "volume"
        }

        rename_dict = {}
        for src, dst in col_map.items():
            if src in raw.columns and dst not in rename_dict.values():
                rename_dict[src] = dst

        df = raw.rename(columns=rename_dict)
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")

        df = df[REQUIRED_COLUMNS].copy()
        df["symbol"] = df["symbol"].astype(str).str.strip().str.upper()
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        return df

    def ingest_bars(
        self,
        new_bars_df: pd.DataFrame,
        output_path: Optional[Path] = None,
        dry_run: bool = False
    ) -> Dict:
        """
        Merges new daily bars into master parquet store.
        Applies deduplication, monotonic sorting, and atomic write.
        """
        dest_path = Path(output_path) if output_path else self.master_parquet_path

        is_valid, err_msg = self.validate_bars(new_bars_df, is_incoming=True)
        if not is_valid:
            raise ValueError(f"Incoming bars failed validation: {err_msg}")

        self.log(f"Loading master dataset from {self.master_parquet_path}...")
        master_df = self.load_master()
        initial_rows = len(master_df)
        incoming_rows = len(new_bars_df)
        self.log(f"Master rows: {initial_rows:,} | Incoming rows: {incoming_rows:,}")

        # Combine datasets
        combined = pd.concat([master_df, new_bars_df], ignore_index=True)

        # Deduplicate keeping latest
        combined = combined.drop_duplicates(subset=["symbol", "date"], keep="last")

        # Sort monotonically
        combined = combined.sort_values(by=["symbol", "date"]).reset_index(drop=True)
        final_rows = len(combined)
        net_new_rows = final_rows - initial_rows

        self.log(f"Merged total rows: {final_rows:,} (Net new: {net_new_rows:,})")

        # Re-verify combined integrity
        is_comb_valid, comb_err = self.validate_bars(combined, is_incoming=False)
        if not is_comb_valid:
            raise ValueError(f"Combined dataset integrity violation: {comb_err}")

        if dry_run:
            self.log("[DRY-RUN] Verification successful. Master file NOT modified.")
        else:
            self.log(f"Writing updated dataset atomically to {dest_path}...")
            temp_file = dest_path.with_suffix(".tmp.parquet")
            combined.to_parquet(temp_file, index=False, engine="pyarrow")
            temp_file.replace(dest_path)
            self.log(f"Successfully updated master parquet at {dest_path}.")

        summary = {
            "initial_rows": initial_rows,
            "incoming_rows": incoming_rows,
            "final_rows": final_rows,
            "net_new_rows": net_new_rows,
            "unique_symbols": int(combined["symbol"].nunique()),
            "min_date": str(combined["date"].min()),
            "max_date": str(combined["date"].max()),
            "dry_run": dry_run
        }
        return summary

    def verify_master_integrity(self) -> Dict:
        """Runs strict invariant audit on master parquet."""
        self.log(f"Auditing master parquet integrity: {self.master_parquet_path}...")
        df = self.load_master()
        total_rows = len(df)
        symbols = df["symbol"].nunique()
        min_date = df["date"].min()
        max_date = df["date"].max()

        # Invariant 1: Columns
        missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]

        # Invariant 2: Nulls
        null_counts = df[REQUIRED_COLUMNS].isnull().sum().to_dict()
        total_nulls = sum(null_counts.values())

        # Invariant 3: Duplicates
        duplicates = int(df.duplicated(subset=["symbol", "date"]).sum())

        # Invariant 4: Monotonicity
        monotonic = True
        for sym, group in df.groupby("symbol"):
            if not group["date"].is_monotonic_increasing:
                monotonic = False
                break

        status = (
            len(missing_cols) == 0 and
            total_nulls == 0 and
            duplicates == 0 and
            monotonic
        )

        results = {
            "status": "PASS" if status else "FAIL",
            "total_rows": total_rows,
            "unique_symbols": symbols,
            "min_date": str(min_date),
            "max_date": str(max_date),
            "missing_cols": missing_cols,
            "total_nulls": total_nulls,
            "duplicate_keys": duplicates,
            "monotonic_ordering": monotonic
        }

        self.log("==================================================================")
        self.log(f"MASTER PARQUET INTEGRITY AUDIT: {results['status']}")
        self.log(f"Total Bars:       {total_rows:,}")
        self.log(f"Unique Symbols:   {symbols:,}")
        self.log(f"Date Range:       {min_date} to {max_date}")
        self.log(f"Duplicates:       {duplicates}")
        self.log(f"Total Nulls:      {total_nulls}")
        self.log(f"Monotonic Dates:  {monotonic}")
        self.log("==================================================================")
        return results

    def run_self_test(self) -> bool:
        """Executes automated self-test on temporary copy to verify ingestion invariants."""
        self.log("Running self-test for incremental ingestion engine...")
        master_df = self.load_master()
        sample_slice = master_df.tail(100).copy()

        with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tmp:
            tmp_path = Path(tmp.name)

        try:
            # Create test base
            base_slice = master_df.iloc[:-50].copy()
            base_slice.to_parquet(tmp_path, index=False)

            test_ingestor = IncrementalBhavcopyIngestor(master_parquet_path=tmp_path)

            # Test appending the last 50 rows
            new_bars = master_df.iloc[-50:].copy()
            summary = test_ingestor.ingest_bars(new_bars, output_path=tmp_path, dry_run=False)

            assert summary["final_rows"] == len(master_df), "Row count mismatch after append!"
            assert summary["net_new_rows"] == 50, "Net new count mismatch!"

            # Test idempotent duplicate append
            summary_dup = test_ingestor.ingest_bars(new_bars, output_path=tmp_path, dry_run=False)
            assert summary_dup["net_new_rows"] == 0, "Idempotency violated: duplicates added!"

            # Test audit on temp file
            audit = test_ingestor.verify_master_integrity()
            assert audit["status"] == "PASS", "Integrity audit failed on self-test dataset!"

            self.log("✅ Self-test PASSED: Append, deduplication, idempotency, and invariants confirmed.")
            return True
        finally:
            if tmp_path.exists():
                tmp_path.unlink()


def main():
    parser = argparse.ArgumentParser(description="Phase 8 Incremental Bhavcopy Ingestion Engine")
    parser.add_argument("--master-parquet", type=str, default=str(DEFAULT_MASTER_PARQUET), help="Path to master parquet")
    parser.add_argument("--new-csv", type=str, default=None, help="Path to new Bhavcopy CSV")
    parser.add_argument("--new-parquet", type=str, default=None, help="Path to new Bhavcopy Parquet")
    parser.add_argument("--verify-only", action="store_true", help="Audit master parquet integrity")
    parser.add_argument("--self-test", action="store_true", help="Run automated ingestion self-test")
    parser.add_argument("--dry-run", action="store_true", help="Validate without modifying master parquet")
    parser.add_argument("--output-parquet", type=str, default=None, help="Custom output destination")

    args = parser.parse_args()
    ingestor = IncrementalBhavcopyIngestor(master_parquet_path=Path(args.master_parquet))

    if args.self_test:
        success = ingestor.run_self_test()
        sys.exit(0 if success else 1)

    if args.verify_only:
        audit = ingestor.verify_master_integrity()
        sys.exit(0 if audit["status"] == "PASS" else 1)

    if args.new_csv:
        csv_path = Path(args.new_csv)
        if not csv_path.exists():
            print(f"Error: CSV file not found: {csv_path}")
            sys.exit(1)
        new_bars = ingestor.parse_nse_bhavcopy_csv(csv_path)
        out_path = Path(args.output_parquet) if args.output_parquet else None
        summary = ingestor.ingest_bars(new_bars, output_path=out_path, dry_run=args.dry_run)
        print("Ingestion Summary:", summary)
        sys.exit(0)

    if args.new_parquet:
        pq_path = Path(args.new_parquet)
        if not pq_path.exists():
            print(f"Error: Parquet file not found: {pq_path}")
            sys.exit(1)
        new_bars = pd.read_parquet(pq_path)
        out_path = Path(args.output_parquet) if args.output_parquet else None
        summary = ingestor.ingest_bars(new_bars, output_path=out_path, dry_run=args.dry_run)
        print("Ingestion Summary:", summary)
        sys.exit(0)

    # Default: run verification audit
    audit = ingestor.verify_master_integrity()
    sys.exit(0 if audit["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
