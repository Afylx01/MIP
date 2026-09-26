#!/usr/bin/env python3
"""
deliverables/gate_cd/scripts/generate_evidence_index.py
Phase 5.5 Gates C & D — EVIDENCE_INDEX.tsv Generator
"""

import hashlib
from pathlib import Path

BASE_DIR = Path("/storage/emulated/0/Documents/Project MIP")
DELIV_DIR = BASE_DIR / "deliverables/gate_cd"

def get_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def what_it_proves(rel_path: str) -> str:
    p = rel_path
    if "DIGEST.md" in p:
        return "Phase 5.5 Gates C & D executive summary digest with continuity metrics, backtest comparisons, and evidence pointers"
    if "task_list.md" in p:
        return "Phase 5.5 Gates C & D roadmap tracking progress across gates (HALT-4 open)"
    if "data_csv/gate_c_continuity_summary.csv" in p:
        return "Gate C continuity audit metrics across all 7 broad market indices proving NIFTY500 0 orphans/duplicates"
    if "data_csv/reconstructed_turnover.csv" in p:
        return "Gate D point-in-time universe reconstruction turnover metrics comparing 2016-01-04 start to 2020-09-14 end"
    if "data_csv/price_gaps.csv" in p:
        return "Gate D price coverage audit proving zero snapshots have >20 symbols with >30% missing Bhavcopy bars"
    if "data_csv/backtest_comparison_metrics.csv" in p:
        return "Gate D comparative backtest performance metrics comparing survivor Run (a) to point-in-time Run (b)"
    if "data_csv/holdings_attribution.csv" in p:
        return "Gate D symbol-level holdings attribution detailing PnL divergence driven by universe differences"
    if "raw/gate_c_continuity.txt" in p:
        return "Gate C raw stdout: multi-index continuity audit across 7 broad market indices"
    if "raw/gate_d_reconstruct.txt" in p:
        return "Gate D raw stdout: universe reconstruction and Bhavcopy price gap audit"
    if "raw/gate_d_backtest_run_a.txt" in p:
        return "Gate D raw stdout: Run (a) baseline backtest execution report, trade log, and R-3 identity verification"
    if "raw/gate_d_backtest_run_b.txt" in p:
        return "Gate D raw stdout: Run (b) dynamic backtest execution report, trade log, and R-3 identity verification"
    if "scripts/gate_c_continuity.py" in p:
        return "Gate C script auditing index event continuity across all 7 broad market indices"
    if "scripts/gate_d_reconstruct.py" in p:
        return "Gate D script reconstructing universe membership and auditing Bhavcopy price gaps"
    if "scripts/gate_d_backtest_runner.py" in p:
        return "Gate D script executing comparative baseline backtests under frozen strategy rules"
    if "scripts/generate_evidence_index.py" in p:
        return "Script generating Phase 5.5 Gates C & D EVIDENCE_INDEX.tsv manifest"
    if "data/corrections.parquet" in p:
        return "Approved corrections table dynamically applied during replay (all 16 status = 'approved')"
    if "data/index_events.parquet" in p:
        return "Append-only index events source dataset unaltered (9,121 rows)"
    if "data/symbol_map.parquet" in p:
        return "Symbol map providing active scrip resolution (763 active scrips)"
    return "Artifact supporting Phase 5.5 Gates C & D execution"

def main():
    rows = []
    files = []

    # Deliv dir files
    for f in sorted(DELIV_DIR.glob("**/*")):
        if f.is_file() and f.name != "EVIDENCE_INDEX.tsv":
            files.append(f)

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

if __name__ == "__main__":
    main()
