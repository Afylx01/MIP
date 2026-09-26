#!/usr/bin/env python3
"""
deliverables/gate_ab/scripts/generate_evidence_index.py
Phase 5.5 Gates A & B — EVIDENCE_INDEX.tsv Generator
"""

import hashlib
from pathlib import Path

BASE_DIR = Path("/storage/emulated/0/Documents/Project MIP")
DELIV_DIR = BASE_DIR / "deliverables/gate_ab"

def get_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def what_it_proves(rel_path: str) -> str:
    p = rel_path
    if "DIGEST.md" in p:
        return "Phase 5.5 Gates A & B executive summary digest with gate claims, continuity metrics, and evidence pointers"
    if "data_csv/gate_a_coverage_map.csv" in p:
        return "Gate A point-in-time coverage metrics across all 57 monthly snapshots proving resolved >= 80% and median joint coverage >= 85%"
    if "data_csv/gate_b_snapshot_summary.csv" in p:
        return "Gate B monthly constituent count summary proving all 57 snapshots strictly within [500, 501] (bounds [490, 515])"
    if "data_csv/snapshot_constituents_57.csv" in p:
        return "Gate B complete constituent manifest (28,554 rows) detailing symbol mapping and joint coverage for all 57 snapshots"
    if "raw/gate0_prerequisites.txt" in p:
        return "Gate 0 raw stdout: transition of corrections to approved, append-only assertion, and universe audit"
    if "raw/gate1_coverage_map.txt" in p:
        return "Gate 1 raw stdout: Gate A coverage map execution, R-5 resolution validation, and joint coverage PASS proof"
    if "raw/gate2_snapshot_sanity.txt" in p:
        return "Gate 2 raw stdout: Gate B chronological replay proving 0 orphan OUTs, 0 duplicate INs, and [500, 501] constituent count"
    if "scripts/gate0_prerequisites.py" in p:
        return "Gate 0 script validating prerequisites and transitioning corrections to approved status"
    if "scripts/gate1_coverage_map.py" in p:
        return "Gate 1 script executing point-in-time coverage re-measurement across all 57 snapshots"
    if "scripts/gate2_snapshot_sanity.py" in p:
        return "Gate 2 script executing chronological replay and exporting complete constituent manifests"
    if "scripts/generate_evidence_index.py" in p:
        return "Script generating Phase 5.5 Gates A & B EVIDENCE_INDEX.tsv manifest"
    if "task_list.md" in p:
        return "Phase 5.5 Gates A & B roadmap task list tracking progress across gates (HALT-3 open)"
    if "data/corrections.parquet" in p:
        return "Approved corrections table dynamically applied during replay (all 16 status = 'approved')"
    if "data/corrections_backup_proposed.parquet" in p:
        return "Point-in-time backup of corrections table prior to approval transition"
    return "Artifact supporting Phase 5.5 Gates A & B execution"

def main():
    rows = []
    files = []

    # Deliv dir files
    for f in sorted(DELIV_DIR.glob("**/*")):
        if f.is_file() and f.name != "EVIDENCE_INDEX.tsv":
            files.append(f)

    # Root corrections files
    for f in [BASE_DIR / "data/corrections.parquet", BASE_DIR / "data/corrections_backup_proposed.parquet"]:
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
