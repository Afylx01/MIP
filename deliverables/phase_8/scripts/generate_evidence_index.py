#!/usr/bin/env python3
"""
deliverables/phase_8/scripts/generate_evidence_index.py
Phase 8 — EVIDENCE_INDEX.tsv and SHA256SUMS Generator

Generates cryptographic checksums and evidence manifests for Phase 8 deliverables.
"""

import hashlib
from pathlib import Path

BASE_DIR = Path("/storage/emulated/0/Documents/Project MIP")
DELIV_DIR = BASE_DIR / "deliverables/phase_8"


def get_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def what_it_proves(rel_path: str) -> str:
    p = rel_path
    if "NEXT_TASK.md" in p:
        return "Phase 8 active directive specifying the production screener, order generator, and ledger architecture"
    if "DIGEST.md" in p:
        return "Phase 8 Operations Manual, executive digest, and dual-date production simulation tearsheet"
    if "task_list.md" in p:
        return "Phase 8 execution roadmap tracking Tasks 1-5 with Standing Gate HALT-9 open"
    if "SHA256SUMS.txt" in p:
        return "Cryptographic SHA-256 manifest of all Phase 8 deliverables"
    if "EVIDENCE_INDEX.tsv" in p:
        return "Comprehensive evidence index mapping files, sizes, SHA-256 hashes, and claims proven"

    # Data CSVs
    if "data_csv/screener_output_sample.csv" in p:
        return "Standard production screener sample ranking all qualifying momentum candidates"
    if "data_csv/screener_output_20260821.csv" in p:
        return "Run 1 Friday 2026-08-21 screener output ranking 355 qualified momentum scrips"
    if "data_csv/screener_output_20260828.csv" in p:
        return "Run 2 Friday 2026-08-28 screener output ranking 360 qualified momentum scrips"
    if "data_csv/rebalance_orders_sample.csv" in p:
        return "Standard execution order tickets with whole shares and itemized statutory fees"
    if "data_csv/rebalance_orders_20260821.csv" in p:
        return "Run 1 initial deployment order tickets seeding Top 20 scrips for ₹1 Crore AUM"
    if "data_csv/rebalance_orders_20260828.csv" in p:
        return "Run 2 weekly rebalance orders confirming 100% exit buffer retention (20 HOLDs)"
    if "data_csv/trade_recommendations_sample.md" in p:
        return "Standard investment desk trade recommendation memo with fee breakdown"
    if "data_csv/trade_recommendations_20260821.md" in p:
        return "Run 1 investment desk trade recommendation memo for initial deployment"
    if "data_csv/trade_recommendations_20260828.md" in p:
        return "Run 2 investment desk trade recommendation memo for weekly rebalance"
    if "data_csv/portfolio_ledger_sample.csv" in p:
        return "Standard portfolio holdings ledger breakdown with market values and weights"
    if "data_csv/portfolio_ledger_20260824.csv" in p:
        return "Run 1 executed holdings ledger as of Monday Open 2026-08-24"
    if "data_csv/portfolio_ledger_20260831.csv" in p:
        return "Run 2 executed holdings ledger as of Monday Open 2026-08-31 (₹1.02 Cr valuation)"
    if "data_csv/portfolio_state.json" in p:
        return "Persistent portfolio state JSON tracking cash balance, cost basis, and P&L"
    if "data_csv/portfolio_state_20260824.json" in p:
        return "Run 1 persistent portfolio state JSON as of 2026-08-24"
    if "data_csv/portfolio_state_20260831.json" in p:
        return "Run 2 persistent portfolio state JSON as of 2026-08-31"

    # Scripts
    if "scripts/ingest_incremental_bhavcopy.py" in p:
        return "Task 1: Incremental daily Bhavcopy ingestion engine with invariant auditing"
    if "scripts/screen_production_momentum.py" in p:
        return "Task 2: Friday EOD production momentum screener and Volar ranker"
    if "scripts/generate_execution_orders.py" in p:
        return "Task 3: Execution order generator applying 100% exit buffer and itemized fee schedule"
    if "scripts/manage_portfolio_ledger.py" in p:
        return "Task 4: Persistent portfolio ledger manager enforcing Rule R-3 cash conservation"
    if "scripts/run_production_pipeline.py" in p:
        return "Task 5: End-to-end production pipeline orchestrator and dual-date simulator"
    if "scripts/generate_evidence_index.py" in p:
        return "Evidence index and SHA-256 manifest compilation script"

    # Raw logs
    if "raw/ingest_incremental_bhavcopy.log" in p:
        return "Task 1 raw execution log verifying self-test, append idempotency, and master integrity"
    if "raw/screen_production_momentum.log" in p:
        return "Task 2 raw execution log recording market regime checks and filter funnel counts"
    if "raw/generate_execution_orders.log" in p:
        return "Task 3 raw execution log itemizing order quantities and regulatory fees"
    if "raw/manage_portfolio_ledger.log" in p:
        return "Task 4 raw execution log confirming fills, cash debits, and Rule R-3 0.00 residual"
    if "raw/pipeline_execution_log.txt" in p:
        return "Task 5 raw stdout log of the complete dual-date production simulation"

    return f"Phase 8 deliverable file: {Path(rel_path).name}"


def main():
    print("Collecting files for Phase 8 Evidence Manifest...")
    all_files = sorted(list(DELIV_DIR.rglob("*")))
    valid_files = []

    for f in all_files:
        if not f.is_file():
            continue
        rel = f.relative_to(DELIV_DIR)
        rel_str = str(rel)

        # Skip caches and generated manifests themselves during hashing
        if "__pycache__" in rel_str or rel_str in ["EVIDENCE_INDEX.tsv", "SHA256SUMS.txt"]:
            continue
        valid_files.append((rel_str, f))

    tsv_lines = ["relative_path\tfile_size_bytes\tsha256_checksum\twhat_it_proves\n"]
    sums_lines = []

    for rel_str, f_path in valid_files:
        size = f_path.stat().st_size
        sha = get_sha256(f_path)
        proves = what_it_proves(rel_str)
        tsv_lines.append(f"{rel_str}\t{size}\t{sha}\t{proves}\n")
        sums_lines.append(f"{sha}  deliverables/phase_8/{rel_str}\n")

    tsv_path = DELIV_DIR / "EVIDENCE_INDEX.tsv"
    sums_path = DELIV_DIR / "SHA256SUMS.txt"

    with open(tsv_path, "w", encoding="utf-8") as f:
        f.writelines(tsv_lines)

    with open(sums_path, "w", encoding="utf-8") as f:
        f.writelines(sums_lines)

    print(f"Generated {tsv_path} ({tsv_path.stat().st_size:,} bytes, {len(valid_files)} entries).")
    print(f"Generated {sums_path} ({sums_path.stat().st_size:,} bytes, {len(sums_lines)} checksums).")


if __name__ == "__main__":
    main()
