#!/usr/bin/env python3
"""
deliverables/phase_5_6/scripts/generate_evidence_index.py
Phase 5.6 — EVIDENCE_INDEX.tsv and SHA256SUMS Generator
"""

import hashlib
from pathlib import Path

BASE_DIR = Path("/storage/emulated/0/Documents/Project MIP")
DELIV_DIR = BASE_DIR / "deliverables/phase_5_6"

def get_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def what_it_proves(rel_path: str) -> str:
    p = rel_path
    if "DIGEST.md" in p:
        return "Phase 5.6 executive summary digest detailing modern era extension, step transition across 2020-09-14, and joint Bhavcopy coverage audit"
    if "task_list.md" in p:
        return "Phase 5.6 roadmap tracking progress across modern index event and Bhavcopy ingestion gates"
    if "SHA256SUMS.txt" in p:
        return "Cryptographic SHA-256 manifest of all Phase 5.6 deliverables"
    if "data_csv/modern_snapshot_coverage.csv" in p:
        return "Gate 5.6-A point-in-time constituent coverage across 71 modern monthly snapshots proving median coverage >= 85.0%"
    if "raw/gate_5_6a_continuity.txt" in p:
        return "Gate 5.6-A raw execution log: step-transition continuity, [500, 501] constituent bounds, and coverage audit"
    if "scripts/build_modern_datasets.py" in p:
        return "Phase 5.6 builder script generating modern events and extracting modern adjusted Bhavcopy bars"
    if "scripts/gate_5_6a_continuity_coverage.py" in p:
        return "Gate 5.6-A verification script auditing modern continuity and snapshot price coverage"
    if "scripts/generate_evidence_index.py" in p:
        return "Script generating Phase 5.6 EVIDENCE_INDEX.tsv manifest"
    if "data/index_events_modern.parquet" in p:
        return "Modern era index events dataset (2020-09 to 2026-08, 459 events)"
    if "data/adjusted_bhavcopy_bars_modern.parquet" in p:
        return "Modern adjusted Bhavcopy daily price bars (2020-09-15 to 2026-08-31, 952,666 bars)"
    if "data/corrections.parquet" in p:
        return "Approved corrections table dynamically applied during replay (all 16 status = 'approved')"
    if "data/index_events.parquet" in p:
        return "Append-only historical index events source dataset unaltered (9,121 rows, SHA256 7a15cfae...)"
    if "data/symbol_map.parquet" in p:
        return "Symbol map providing active scrip resolution including all modern constituents (1,614 scrips)"
    return "Artifact supporting Phase 5.6 execution"

def main():
    rows = []
    files = []

    # Deliverables directory files
    for f in sorted(DELIV_DIR.glob("**/*")):
        if f.is_file() and f.name not in ["EVIDENCE_INDEX.tsv", "SHA256SUMS.txt"]:
            files.append(f)

    # Core modern and historical data dependencies
    for f in [
        BASE_DIR / "data/index_events_modern.parquet",
        BASE_DIR / "data/adjusted_bhavcopy_bars_modern.parquet",
        BASE_DIR / "data/corrections.parquet",
        BASE_DIR / "data/index_events.parquet",
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
