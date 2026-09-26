#!/usr/bin/env python3
"""
deliverables/phase_6/scripts/generate_evidence_index.py
Phase 6 — EVIDENCE_INDEX.tsv and SHA256SUMS Generator
"""

import hashlib
from pathlib import Path

BASE_DIR = Path("/storage/emulated/0/Documents/Project MIP")
DELIV_DIR = BASE_DIR / "deliverables/phase_6"
PACKAGE_DIR = BASE_DIR / "indian_backtest"

def get_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def what_it_proves(rel_path: str) -> str:
    p = rel_path
    if "DIGEST.md" in p:
        return "Phase 6 executive digest detailing podcast momentum backtester performance, comparative metrics, drawdown reduction, and Standing Rule R-3 / R-6 verification"
    if "task_list.md" in p:
        return "Phase 6 roadmap tracking progress across modular package architecture, multi-cycle backtest runs, and standing gate HALT-6"
    if "SHA256SUMS.txt" in p:
        return "Cryptographic SHA-256 manifest of all Phase 6 deliverables"
    if "data_csv/comparative_strategy_metrics.csv" in p:
        return "Comparative strategy performance metrics across Run 1 (Baseline), Run 2 (E1 RS), Run 3 (Full Strategy with E4 Regime Filter + Friction), and Benchmark"
    if "data_csv/drawdown_regime_analysis.csv" in p:
        return "Drawdown regime analysis proving the effectiveness of the 200 EMA cash filter during major market drawdowns"
    if "raw/run1_baseline_pass1.txt" in p:
        return "Run 1 (Baseline Momentum) Pass 1 raw execution log and trade records"
    if "raw/run1_baseline_pass2.txt" in p:
        return "Run 1 (Baseline Momentum) Pass 2 raw execution log verifying byte-identical reproducibility (Rule R-6)"
    if "raw/run2_e1_rs_pass1.txt" in p:
        return "Run 2 (Momentum + E1 RS) Pass 1 raw execution log and trade records"
    if "raw/run2_e1_rs_pass2.txt" in p:
        return "Run 2 (Momentum + E1 RS) Pass 2 raw execution log verifying byte-identical reproducibility (Rule R-6)"
    if "raw/run3_full_strategy_pass1.txt" in p:
        return "Run 3 (Full Strategy: E1 RS + E4 Regime Cash Filter + Friction) Pass 1 raw execution log and trade records"
    if "raw/run3_full_strategy_pass2.txt" in p:
        return "Run 3 (Full Strategy: E1 RS + E4 Regime Cash Filter + Friction) Pass 2 raw execution log verifying byte-identical reproducibility (Rule R-6)"
    if "raw/rule_r3_r6_summary.txt" in p:
        return "Summary log proving Standing Rule R-3 accounting identity (residual == 0.00) and Standing Rule R-6 byte-identical reproducibility across all runs"
    if "scripts/podcast_backtest_runner.py" in p:
        return "Phase 6 multi-cycle backtest execution runner script"
    if "scripts/generate_evidence_index.py" in p:
        return "Script generating Phase 6 EVIDENCE_INDEX.tsv and SHA256SUMS manifests"
    if "indian_backtest" in p:
        return f"Modular production package source component: {Path(p).name}"
    return "Artifact supporting Phase 6 execution"

def main():
    rows = []
    files = []

    # Deliverables directory files
    for f in sorted(DELIV_DIR.glob("**/*")):
        if f.is_file() and f.name not in ["EVIDENCE_INDEX.tsv", "SHA256SUMS.txt"]:
            files.append(f)

    # Modular package files
    for f in sorted(PACKAGE_DIR.glob("**/*")):
        if f.is_file() and not f.name.endswith(".pyc") and "__pycache__" not in str(f):
            files.append(f)

    # Core data dependencies
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
