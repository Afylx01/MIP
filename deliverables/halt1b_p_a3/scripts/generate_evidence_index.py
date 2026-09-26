#!/usr/bin/env python3
"""
deliverables/halt1b_p_a3/scripts/generate_evidence_index.py
Generates EVIDENCE_INDEX.tsv for Phase 5.5.A-3.
Calculates exact file size and sha256 for all artifacts under deliverables/halt1b_p_a3/
and data/verification/halt1b_p_a3/.
"""

import hashlib
from pathlib import Path

BASE_DIR = Path("/sdcard/Documents/Project MIP")
DELIV_DIR = BASE_DIR / "deliverables/halt1b_p_a3"
VERIF_DIR = BASE_DIR / "data/verification/halt1b_p_a3"

def get_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def what_it_proves(rel_path: str) -> str:
    p = rel_path
    if "DIGEST.md" in p:
        return "Phase 5.5.A-3 executive summary digest with gate claims, metrics, and evidence pointers"
    if "data_csv/required_symbols_dates.csv" in p:
        return "Gate 0 manifest of 435 mapped target symbols required across all 57 snapshots"
    if "data_csv/snapshot_prerequisite_audit.csv" in p:
        return "Gate 0 audit of constituent counts and mapping percentages across 57 snapshots"
    if "data_csv/window_trading_dates.csv" in p:
        return "Gate 0 calendar of 1,154 trading dates covering 2016-01-01 to 2020-09-14"
    if "data_csv/gate1_download_summary.csv" in p:
        return "Gate 1 summary table of 1,154 downloaded daily Bhavcopies with record counts and sizes"
    if "data_csv/gate2_spot_check_summary.csv" in p:
        return "Gate 2 spot-check summary verifying price continuity across 5 reference corporate action events"
    if "data_csv/monthly_coverage_comparison.csv" in p:
        return "Gate 3 comparative table showing Gate 2c baseline vs Phase A-3 reconstructed coverage for 57 snapshots"
    if "raw/gate0_prerequisites.txt" in p:
        return "Gate 0 raw stdout: prerequisite universe audit and snapshot derivation"
    if "raw/gate1_fetch.txt" in p:
        return "Gate 1 raw stdout: concurrent Bhavcopy download and raw price bar extraction"
    if "raw/gate2_adjustment.txt" in p:
        return "Gate 2 raw stdout: corporate action adjustment execution and invariance assertions"
    if "raw/gate3_coverage.txt" in p:
        return "Gate 3 raw stdout: joint coverage re-measurement across all 57 snapshots and acceptance ruling"
    if "raw_bhavcopy_bars.parquet" in p:
        return "Gate 1 ingested raw unadjusted OHLCV price series extracted from official daily Bhavcopies"
    if "adjusted_bhavcopy_bars.parquet" in p:
        return "Gate 2 corporate-action adjusted OHLCV price series across 2016-2020 window"
    if "scripts/gate0_prerequisites.py" in p:
        return "Gate 0 script auditing 57 monthly snapshots and isolating required symbols and dates"
    if "scripts/gate1_fetch_bhavcopies.py" in p:
        return "Gate 1 script concurrently sourcing daily Bhavcopies from nsearchives and extracting series EQ/BE"
    if "scripts/gate2_adjustment.py" in p:
        return "Gate 2 script applying adjust_ohlc pure function across full reconstructed price dataset"
    if "scripts/gate3_coverage.py" in p:
        return "Gate 3 script re-measuring joint coverage metrics and evaluating §1 thresholds"
    if "scripts/generate_evidence_index.py" in p:
        return "Script compiling Phase 5.5.A-3 EVIDENCE_INDEX.tsv manifest"
    if "task_list.md" in p:
        return "Phase 5.5 roadmap task list tracking progress across gates"
    if "samples/bhav/" in p:
        return f"Daily official NSE Bhavcopy zip archive downloaded during Gate 1 ({Path(p).name})"
    return "Artifact supporting Phase 5.5.A-3 execution"

def main():
    rows = []
    files = []
    for f in sorted(DELIV_DIR.glob("**/*")):
        if f.is_file() and f.name != "EVIDENCE_INDEX.tsv":
            files.append(f)
    for f in sorted(VERIF_DIR.glob("**/*")):
        if f.is_file():
            files.append(f)
            
    for f in files:
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

if __name__ == "__main__":
    main()
