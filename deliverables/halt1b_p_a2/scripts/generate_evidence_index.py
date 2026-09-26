#!/usr/bin/env python3
"""
deliverables/halt1b_p_a2/scripts/generate_evidence_index.py
Generates EVIDENCE_INDEX.tsv for Phase 5.5.A-2.
Calculates exact file size and sha256 for all artifacts under deliverables/halt1b_p_a2/
and data/verification/halt1b_p_a2/.
"""

import hashlib
from pathlib import Path

BASE_DIR = Path("/sdcard/Documents/Project MIP")
DELIV_DIR = BASE_DIR / "deliverables/halt1b_p_a2"
VERIF_DIR = BASE_DIR / "data/verification/halt1b_p_a2"

def get_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def what_it_proves(rel_path: str) -> str:
    p = rel_path
    if "ca_calendar_raw.parquet" in p:
        return "Persisted binary Parquet CA calendar with exact required schema (214 records, 2016-2020)"
    if "data_csv/ca_calendar.csv" in p:
        return "Full CSV export of CA calendar containing all 214 splits and bonuses across 2016-2020"
    if "data_csv/gate4_test_bars.csv" in p:
        return "Raw and adjusted OHLCV bars across 11-day windows for 5 unit-tested corporate actions"
    if "data_csv/gate4_unit_test_summary.csv" in p:
        return "Summary table proving raw step drop and adjusted continuity (<30% move) for 5 events"
    if "data_csv/nifty500_ca_coverage.csv" in p:
        return "Cross-check coverage table for 456 NIFTY500 union members (79 with CA, 377 without)"
    if "raw/ca_calendar_parsed_debug.csv" in p:
        return "Debug export of all parsed corporate actions including original NSE subject strings"
    if "raw/gate0_discovery.txt" in p:
        return "Gate 0 raw stdout: 9 candidate endpoint probes, HTTP status, reachability, and exit decision"
    if "raw/gate1_fetch.txt" in p:
        return "Gate 1 raw stdout: 5 slice fetches (9,473 raw records) and 55 Bhavcopy zip downloads"
    if "raw/gate2_sanity.txt" in p:
        return "Gate 2 raw stdout: schema assertion, monotonic sort, zero dups, and 3 hand-verified events"
    if "raw/gate3_smoke_test.txt" in p:
        return "Gate 3 raw stdout: smoke test execution on 5-bar series verifying zero return jump across event"
    if "raw/gate4_unit_test.txt" in p:
        return "Gate 4 raw stdout: unit test execution on 5 real events proving step drop and continuity"
    if "samples/ca_raw_2016.json" in p:
        return "Raw NSE JSON response for corporate actions in 2016 (2,106 records)"
    if "samples/ca_raw_2017.json" in p:
        return "Raw NSE JSON response for corporate actions in 2017 (2,025 records)"
    if "samples/ca_raw_2018.json" in p:
        return "Raw NSE JSON response for corporate actions in 2018 (2,012 records)"
    if "samples/ca_raw_2019.json" in p:
        return "Raw NSE JSON response for corporate actions in 2019 (2,148 records)"
    if "samples/ca_raw_2020.json" in p:
        return "Raw NSE JSON response for corporate actions in 2020 through Sep 14 (1,182 records)"
    if "samples/test_events_raw_bars.csv" in p:
        return "Extracted raw Bhavcopy bars (275 bars total, 55 per symbol) for the 5 Gate 4 test events"
    if "samples/bhav/" in p:
        return f"Daily official NSE Bhavcopy zip archive downloaded during Gate 1 ({Path(p).name})"
    if "scripts/adjust_prices.py" in p:
        return "Pure function adjust_ohlc implementing cumulative backward adjustment of OHLC and volume"
    if "scripts/gate0_ca_discovery.py" in p:
        return "Script probing candidate NSE corporate action endpoints with honest UA and rate limiting"
    if "scripts/gate1_fetch_ca_calendar.py" in p:
        return "Script fetching 2016-2020 CA records, parsing splits/bonuses, and downloading test Bhavcopies"
    if "scripts/gate2_schema_sanity.py" in p:
        return "Script executing schema sanity assertions, hand verification, and NIFTY500 coverage check"
    if "scripts/gate4_unit_test.py" in p:
        return "Script running adjuster unit test on real Bhavcopies across 5 historical events"
    if "scripts/test_adjust_prices.py" in p:
        return "Smoke test script for adjust_prices asserting continuity on synthetic 5-bar series"
    if "task_list.md" in p:
        return "Phase 5.5 roadmap task list tracking progress across gates"
    return "Artifact supporting Phase 5.5.A-2 execution"

def main():
    rows = []
    # Collect files
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
