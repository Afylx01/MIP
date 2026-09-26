#!/usr/bin/env python3
"""
deliverables/gate3/scripts/generate_evidence_index.py
Generates EVIDENCE_INDEX.tsv for Phase 5.5 Gate 3.
Calculates exact file size and sha256 for all artifacts under deliverables/gate3/
and root data/corrections*.
"""

import hashlib
from pathlib import Path

BASE_DIR = Path("/sdcard/Documents/Project MIP")
DELIV_DIR = BASE_DIR / "deliverables/gate3"

def get_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def what_it_proves(rel_path: str) -> str:
    p = rel_path
    if "DIGEST.md" in p:
        return "Phase 5.5 Gate 3 executive summary digest with gate claims, continuity metrics, and evidence pointers"
    if "data_csv/unresolved_anomalies.csv" in p:
        return "Gate 0 audit isolating all 15 orphan OUTs and 1 duplicate IN from raw Excel replay"
    if "data_csv/forensic_reconciliation.csv" in p:
        return "Gate 1 forensic reconciliation linking every orphan/duplicate anomaly to verified corporate actions & circulars"
    if "data_csv/proposed_corrections.csv" in p:
        return "Gate 2 compiled table of 16 proposed corrections in human-readable CSV format"
    if "data_csv/simulation_rebalance_counts.csv" in p:
        return "Gate 3 constituent count distribution across 57 snapshots verifying compliance with [490, 515]"
    if "raw/gate0_anomalies_audit.txt" in p:
        return "Gate 0 raw stdout: anomaly ingestion, raw Excel replay, and quarantine identification"
    if "raw/gate2_build_corrections.txt" in p:
        return "Gate 2 raw stdout: compilation of data/corrections.parquet with Rule R-11 proposed status validation"
    if "raw/gate3_simulated_replay.txt" in p:
        return "Gate 3 raw stdout: simulated replay proving 0 orphan OUTs, 0 duplicate INs, and count range [500, 501]"
    if "data/corrections.parquet" in p:
        return "Gate 2 append-only corrections proposal table in Parquet (all status = 'proposed')"
    if "data/corrections_report.md" in p:
        return "Gate 2 comprehensive narrative report detailing root causes and verification evidence for all 16 rules"
    if "scripts/gate0_anomalies_audit.py" in p:
        return "Gate 0 script isolating anomalies and replaying raw workbook events"
    if "scripts/gate1_forensic_reconciliation.py" in p:
        return "Gate 1 script documenting verifiable corporate action evidence for each anomaly"
    if "scripts/gate2_build_corrections.py" in p:
        return "Gate 2 script compiling data/corrections.parquet and generating report"
    if "scripts/gate3_simulated_replay.py" in p:
        return "Gate 3 script executing simulated replay and asserting continuity invariants"
    if "scripts/generate_evidence_index.py" in p:
        return "Script compiling Phase 5.5 Gate 3 EVIDENCE_INDEX.tsv manifest"
    if "task_list.md" in p:
        return "Phase 5.5 roadmap task list tracking progress across gates (HALT-2 open)"
    return "Artifact supporting Phase 5.5 Gate 3 execution"

def main():
    rows = []
    files = []
    
    # 1. Deliv dir files
    for f in sorted(DELIV_DIR.glob("**/*")):
        if f.is_file() and f.name != "EVIDENCE_INDEX.tsv":
            files.append(f)
            
    # 2. Root corrections files
    for f in [BASE_DIR / "data/corrections.parquet", BASE_DIR / "data/corrections_report.md"]:
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

if __name__ == "__main__":
    main()
