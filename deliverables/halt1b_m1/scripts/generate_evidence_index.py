#!/usr/bin/env python3
"""
deliverables/halt1b_m1/scripts/generate_evidence_index.py
Generates EVIDENCE_INDEX.tsv for Phase 5.5.M-1.
Calculates exact file size and sha256 for all artifacts under deliverables/halt1b_m1/
and data/verification/halt1b_m1/.
"""

import hashlib
from pathlib import Path

BASE_DIR = Path("/sdcard/Documents/Project MIP")
DELIV_DIR = BASE_DIR / "deliverables/halt1b_m1"
VERIF_DIR = BASE_DIR / "data/verification/halt1b_m1"

def get_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def what_it_proves(rel_path: str) -> str:
    p = rel_path
    if "DIGEST.md" in p:
        return "Phase 5.5.M-1 executive summary digest with gate claims, coverage metrics, and evidence pointers"
    if "data_csv/nifty500_pending_scrips_ranked.csv" in p:
        return "Gate 0 ranking of 299 pending NIFTY500 constituent scrips by snapshot occurrence frequency"
    if "data_csv/gate1_vetted_high_summary.csv" in p:
        return "Gate 1 summary of 70 high-confidence candidate scrips vetted against EQUITY_L and approved"
    if "data_csv/gate2_curated_review.csv" in p:
        return "Gate 2 review batch of 122 curated corporate rename and medium-tier constituent mappings"
    if "data_csv/approved_scrips_summary.csv" in p:
        return "Gate 2 comprehensive audit of 192 approved scrips across Gates 1 and 2"
    if "data_csv/gate3_extraction_summary.csv" in p:
        return "Gate 3 local Bhavcopy price extraction and corporate action adjustment summary metrics"
    if "data_csv/monthly_coverage_comparison_v2.csv" in p:
        return "Gate 4 comparative monthly coverage across 57 snapshots proving 86.25% median joint coverage (PASS)"
    if "raw/gate0_triage.txt" in p:
        return "Gate 0 raw stdout: pending constituent triage and frequency ranking"
    if "raw/gate1_apply_high.txt" in p:
        return "Gate 1 raw stdout: application of 70 high-confidence scrip approvals via apply_symbol_map_review.py"
    if "raw/gate2_apply_medium.txt" in p:
        return "Gate 2 raw stdout: application of 122 curated scrip approvals via apply_symbol_map_review.py"
    if "raw/gate3_price_extraction.txt" in p:
        return "Gate 3 raw stdout: multi-threaded local price extraction across 1,154 Bhavcopies and CA adjustment"
    if "raw/gate4_coverage.txt" in p:
        return "Gate 4 raw stdout: joint coverage re-measurement across 57 snapshots achieving PASS verdict"
    if "raw_bhavcopy_bars_v2.parquet" in p:
        return "Gate 3 expanded raw unadjusted OHLCV price series (753,046 bars across 711 symbols)"
    if "adjusted_bhavcopy_bars_v2.parquet" in p:
        return "Gate 3 corporate action adjusted OHLCV price series (753,046 bars across 711 symbols)"
    if "scripts/gate0_triage.py" in p:
        return "Gate 0 script triaging and ranking pending constituent scrips"
    if "scripts/gate1_vet_high.py" in p:
        return "Gate 1 script vetting high-confidence candidate mappings against EQUITY_L"
    if "scripts/gate2_curate_mappings.py" in p:
        return "Gate 2 script curating corporate rename and medium-tier constituent mappings"
    if "scripts/gate3_price_extraction.py" in p:
        return "Gate 3 script extracting series EQ/BE bars from local Bhavcopy cache and executing CA adjustment"
    if "scripts/gate4_coverage_remeasurement.py" in p:
        return "Gate 4 script re-measuring joint coverage metrics and validating >=85.0% PASS threshold"
    if "scripts/generate_evidence_index.py" in p:
        return "Script compiling Phase 5.5.M-1 EVIDENCE_INDEX.tsv manifest"
    if "task_list.md" in p:
        return "Phase 5.5.M-1 roadmap task list tracking progress across gates (HALT-1b-M-1 open)"
    return "Artifact supporting Phase 5.5.M-1 execution"

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
