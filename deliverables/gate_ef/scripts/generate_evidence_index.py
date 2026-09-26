#!/usr/bin/env python3
"""
deliverables/gate_ef/scripts/generate_evidence_index.py
Phase 5.5 Gates E & F — EVIDENCE_INDEX.tsv and SHA256SUMS Generator
"""

import hashlib
from pathlib import Path

BASE_DIR = Path("/storage/emulated/0/Documents/Project MIP")
DELIV_DIR = BASE_DIR / "deliverables/gate_ef"
VERIFY_DIR = BASE_DIR / "data/verification"

def get_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def what_it_proves(rel_path: str) -> str:
    p = rel_path
    if "DIGEST.md" in p:
        return "Phase 5.5 Gates E & F executive summary digest detailing round-trip replay, boundary continuity, byte-identical reproducibility, and date clamping"
    if "task_list.md" in p:
        return "Phase 5.5 roadmap tracking progress through Gate E and Gate F with HALT-5 held open"
    if "SHA256SUMS.txt" in p:
        return "Cryptographic SHA-256 manifest of all Gate E & F deliverables"
    if "data_csv/gate_e_roundtrip_summary.csv" in p:
        return "Gate E summary metrics proving forward and backward replay equivalence across sampled dates and end boundary continuity"
    if "data_csv/gate_f_clamping_summary.csv" in p:
        return "Gate F summary metrics demonstrating automatic out-of-bounds date clamping, warning emission, and run-date invariance"
    if "raw/gate_e_roundtrip.txt" in p:
        return "Gate E raw execution log: forward/backward replay equivalence, symmetric difference 0, and end-boundary event transitions"
    if "raw/gate_f_pass1.txt" in p or "raw/gate_f_run_pass1.txt" in p:
        return "Gate F raw execution log: Pass 1 point-in-time dynamic backtest metrics, trade log, and Rule R-3 identity verification"
    if "raw/gate_f_pass2.txt" in p or "raw/gate_f_run_pass2.txt" in p:
        return "Gate F raw execution log: Pass 2 point-in-time dynamic backtest metrics, trade log, and Rule R-3 identity verification"
    if "raw/gate_f_truncation.txt" in p:
        return "Gate F raw execution log: boundary clamping tests, warning emission verification, and run-date invariance"
    if "scripts/gate_e_roundtrip.py" in p:
        return "Gate E script implementing bi-directional snapshot replay and end-boundary continuity verification"
    if "scripts/gate_f_reproducibility.py" in p:
        return "Gate F script executing dual-pass reproducibility, out-of-bounds date clamping, and run-date invariance"
    if "scripts/generate_evidence_index.py" in p:
        return "Script generating Phase 5.5 Gates E & F EVIDENCE_INDEX.tsv manifest"
    if "membership_2003-09-05.txt" in p:
        return "Gate E membership manifest as of 2003-09-05 (early history) verified identical under forward and backward replay"
    if "membership_2012-05-21.txt" in p:
        return "Gate E membership manifest as of 2012-05-21 (mid history) verified identical under forward and backward replay"
    if "membership_2015-12-14.txt" in p:
        return "Gate E membership manifest as of 2015-12-14 (late history) verified identical under forward and backward replay"
    if "data/corrections.parquet" in p:
        return "Approved corrections table dynamically applied during replay (all 16 status = 'approved')"
    if "data/index_events.parquet" in p:
        return "Append-only index events source dataset unaltered (9,121 rows, SHA256 7a15cfae...)"
    if "data/symbol_map.parquet" in p:
        return "Symbol map providing active scrip resolution (763 active scrips)"
    return "Artifact supporting Phase 5.5 Gates E & F execution"

def main():
    rows = []
    files = []

    # Deliverables directory files
    for f in sorted(DELIV_DIR.glob("**/*")):
        if f.is_file() and f.name not in ["EVIDENCE_INDEX.tsv", "SHA256SUMS.txt"]:
            files.append(f)

    # Exported verification manifests
    for manifest in ["membership_2003-09-05.txt", "membership_2012-05-21.txt", "membership_2015-12-14.txt"]:
        mf_path = VERIFY_DIR / manifest
        if mf_path.exists():
            files.append(mf_path)

    # Core data dependencies
    for f in [BASE_DIR / "data/corrections.parquet", BASE_DIR / "data/index_events.parquet", BASE_DIR / "data/symbol_map.parquet"]:
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
