#!/usr/bin/env python3
"""
deliverables/data_comparison/scripts/generate_evidence_index.py
Data Comparison — EVIDENCE_INDEX.tsv and SHA256SUMS Generator
"""

import hashlib
from pathlib import Path

BASE_DIR = Path("/storage/emulated/0/Documents/Project MIP")
DELIV_DIR = BASE_DIR / "deliverables/data_comparison"

def get_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def what_it_proves(rel_path: str) -> str:
    p = rel_path
    if "DATA_COMPARISON_RULING.md" in p:
        return "Final Auditor ruling certifying Bhavcopy consolidation, rejecting YFinance for backtesting, and clearing HALT-7"
    if "DIGEST.md" in p:
        return "Executive digest and definitive audit verdict on Yahoo Finance data trustability vs official NSE Bhavcopy"
    if "task_list.md" in p:
        return "Roadmap tracking data comparison gates with Standing Gate HALT-7 open"
    if "SHA256SUMS.txt" in p:
        return "Cryptographic SHA-256 manifest of all data comparison deliverables"
    if "data_csv/coverage_comparison.csv" in p:
        return "Survivorship bias audit quantifying missing/delisted scrips in Yahoo Finance vs point-in-time universe"
    if "data_csv/price_tracking_error.csv" in p:
        return "Price discrepancy audit computing MAPE, Max Diff, and % of bars diverging > 1.0%"
    if "data_csv/corporate_action_fidelity.csv" in p:
        return "Corporate action fidelity audit verifying 1-day returns across 10 known bonus/split dates"
    if "data_csv/comparative_backtest_delta.csv" in p:
        return "Comparative momentum strategy backtest results quantifying performance divergence (Bhavcopy vs YFinance)"
    if "raw/consolidation_log.txt" in p:
        return "Raw log of maximum Bhavcopy consolidation (2007-2026, 2.14M bars, 1,039 symbols, 0 duplicates)"
    if "raw/yfinance_download_log.txt" in p:
        return "Raw log of multi-threaded batched Yahoo Finance download"
    if "raw/comparative_audit_log.txt" in p:
        return "Raw log of comparative mathematical fidelity audit"
    if "raw/comparative_backtest_log.txt" in p:
        return "Raw log and tearsheets of comparative backtest re-run"
    if "scripts/consolidate_max_bhavcopy.py" in p:
        return "Maximum Bhavcopy consolidation builder script"
    if "scripts/fetch_yfinance_ohlcv.py" in p:
        return "Batched multi-threaded YFinance downloader script"
    if "scripts/audit_yfinance_vs_bhavcopy.py" in p:
        return "Comparative fidelity and corporate action audit script"
    if "scripts/run_comparative_backtest.py" in p:
        return "Comparative momentum strategy backtest runner script"
    if "scripts/generate_evidence_index.py" in p:
        return "Manifest and checksum generator script"
    if "data/adjusted_bhavcopy_max_2007_2026.parquet" in p:
        return "Consolidated maximum Bhavcopy ground-truth dataset (2007-2026, 2,137,630 bars, 1,039 symbols)"
    if "data/yfinance_ohlcv_2007_2026.parquet" in p:
        return "Consolidated Yahoo Finance OHLCV dataset (2007-2026, with raw OHLC, Adj Close, Dividends, Splits)"
    if "data/symbol_map.parquet" in p:
        return "Symbol map providing active scrip resolution including all modern constituents (1,614 scrips)"
    return "Artifact supporting Data Comparison execution"

def main():
    rows = []
    files = []

    # Deliverables directory files
    for f in sorted(DELIV_DIR.glob("**/*")):
        if f.is_file() and f.name not in ["EVIDENCE_INDEX.tsv", "SHA256SUMS.txt"]:
            files.append(f)

    # Core data dependencies
    for f in [
        BASE_DIR / "data/adjusted_bhavcopy_max_2007_2026.parquet",
        BASE_DIR / "data/yfinance_ohlcv_2007_2026.parquet",
        BASE_DIR / "data/symbol_map.parquet"
    ]:
        if f.exists() and f.is_file():
            files.append(f)

    for f in sorted(files, key=lambda x: str(x.relative_to(BASE_DIR))):
        rel_p = str(f.relative_to(BASE_DIR))
        size = f.stat().st_size
        sha = get_sha256(f)
        desc = what_it_proves(rel_p)
        rows.append(f"{rel_p}\t{size}\t{sha}\t{desc}")

    out_tsv = DELIV_DIR / "EVIDENCE_INDEX.tsv"
    with open(out_tsv, "w", encoding="utf-8") as out:
        out.write("path\tbytes\tsha256\twhat_it_proves\n")
        for r in rows:
            out.write(r + "\n")

    print(f"Generated {out_tsv} ({out_tsv.stat().st_size:,} bytes, {len(rows)} entries).")

    # Generate SHA256SUMS.txt for deliverables
    sha_lines = []
    for f in sorted(DELIV_DIR.glob("**/*")):
        if f.is_file() and f.name != "SHA256SUMS.txt":
            rel_p = str(f.relative_to(DELIV_DIR))
            sha = get_sha256(f)
            sha_lines.append(f"{sha}  {rel_p}")
    sha_file = DELIV_DIR / "SHA256SUMS.txt"
    with open(sha_file, "w", encoding="utf-8") as sf:
        sf.write("\n".join(sha_lines) + "\n")
    print(f"Generated {sha_file} ({sha_file.stat().st_size:,} bytes, {len(sha_lines)} checksums).")

if __name__ == "__main__":
    main()
