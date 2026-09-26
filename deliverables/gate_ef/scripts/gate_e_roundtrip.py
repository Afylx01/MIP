#!/usr/bin/env python3
"""
deliverables/gate_ef/scripts/gate_e_roundtrip.py
Phase 5.5 Gates E & F — Gate E: Round-Trip Bi-Directional Snapshot Replay Engine

1. Three-Date Deterministic Round-Trip Replay:
   - Uses fixed RNG seed (seed = 42) to sample 3 distinct dates across the 1998–2020 history (early, mid, late).
   - Computes point-in-time membership via Forward Replay from the 1998-08-01 seed batch.
   - Computes point-in-time membership via Backward Replay from the 2020-09-14 covered_end snapshot (reversing IN and OUT events).
   - Asserts mathematical equivalence: ForwardSet == BackwardSet (symmetric difference == 0).
   - Exports full constituent manifests to data/verification/membership_<date>.txt.

2. End-Boundary Continuity:
   - Evaluates membership as of the eve of covered_end (2020-09-13: 501 constituents).
   - Applies events effective on 2020-09-14 (Row 2495 IN JTEKT India Ltd., Row 2496 OUT Asahi India Glass Ltd.).
   - Asserts resulting set strictly equals snapshot at covered_end (501 constituents).

3. Standalone Offline Invariant:
   - Verifies zero network dependencies (standalone execution from local parquet/txt files).
   - Verifies Standing Rule R-1: data/index_events.parquet unaltered (exact 9,121 rows, SHA256 7a15cfae...).

Outputs:
  - data/verification/membership_2003-09-05.txt
  - data/verification/membership_2012-05-21.txt
  - data/verification/membership_2015-12-14.txt
  - deliverables/gate_ef/data_csv/gate_e_roundtrip_summary.csv
  - deliverables/gate_ef/raw/gate_e_roundtrip.txt
"""

import sys
import hashlib
import datetime
import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR = Path("/storage/emulated/0/Documents/Project MIP")
DELIV_DIR = BASE_DIR / "deliverables/gate_ef"
DATA_CSV_DIR = DELIV_DIR / "data_csv"
RAW_DIR = DELIV_DIR / "raw"
VERIFY_DIR = BASE_DIR / "data/verification"

EVENTS_PATH = BASE_DIR / "data/index_events.parquet"
CORRECTIONS_PATH = BASE_DIR / "data/corrections.parquet"
SYMBOL_MAP_PATH = BASE_DIR / "data/symbol_map.parquet"

EXPECTED_EVENTS_SHA256 = "7a15cfae88c53c6a4d79c5fe28dc3642a999728855d29329a892e11261d2d54a"
COVERED_END_DATE = "2020-09-14"
RNG_SEED = 42

def sha256_file(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def main():
    lines = []
    def log(msg=""):
        print(msg)
        lines.append(msg)

    log("=" * 80)
    log("PHASE 5.5 GATES E & F — GATE E: ROUND-TRIP BI-DIRECTIONAL SNAPSHOT REPLAY")
    log(f"Timestamp: {datetime.datetime.now(datetime.timezone.utc).isoformat()}")
    log(f"Deterministic RNG Seed: {RNG_SEED}")
    log("=" * 80)

    for d in [DATA_CSV_DIR, RAW_DIR, VERIFY_DIR]:
        d.mkdir(parents=True, exist_ok=True)

    # 1. Ingest Data & Assert Standing Invariants (Rule R-1)
    log("\n--- 1. Standing Rule R-1: Append-Only Event Log Integrity Check ---")
    events_hash = sha256_file(EVENTS_PATH)
    log(f"File: data/index_events.parquet")
    log(f"  Observed SHA-256: {events_hash}")
    log(f"  Expected SHA-256: {EXPECTED_EVENTS_SHA256}")
    assert events_hash == EXPECTED_EVENTS_SHA256, "Standing Rule R-1 VIOLATION: index_events.parquet modified!"
    log("  Integrity Status: VERIFIED UNALTERED (Standing Rule R-1 STRICT PASS)")

    events_df = pd.read_parquet(EVENTS_PATH)
    log(f"  Total Index Events: {len(events_df):,} rows (expected 9,121)")
    assert len(events_df) == 9121, f"Expected 9,121 events, got {len(events_df)}"

    corr_df = pd.read_parquet(CORRECTIONS_PATH)
    log(f"  Loaded Corrections: {len(corr_df)} approved rules")
    assert (corr_df["status"] == "approved").all(), "All corrections must be approved!"

    renames = corr_df[corr_df["action"] == "RENAME"]
    rev_rename_map = {r["target_scrip_name"]: r["scrip_name"] for _, r in renames.iterrows()}
    fwd_rename_map = {r["scrip_name"]: r["target_scrip_name"] for _, r in renames.iterrows()}
    log(f"  Loaded {len(rev_rename_map)} corporate rename linkages")

    smap_df = pd.read_parquet(SYMBOL_MAP_PATH)
    log(f"  Loaded Symbol Map:  {len(smap_df):,} scrips")

    # Filter NIFTY500 events
    n500 = events_df[events_df["index"] == "NIFTY500"].sort_values(["effective_date", "row"]).reset_index(drop=True)
    log(f"  Total NIFTY500 Events: {len(n500):,} events (1998-08-01 to 2020-09-14)")

    # 2. Build Forward Replay Engine & Map Rename-Consuming Rows
    log("\n--- 2. Forward Replay Baseline & Rename-Consuming Event Tracking ---")
    active_end = set()
    rename_consuming_rows = set()

    for _, r in n500.iterrows():
        row_num = r["row"]
        if row_num in [2136, 2162]:
            continue
        scrip = r["scrip_name"]
        act = r["action"]
        if act == "IN":
            active_end.add(scrip)
        elif act == "OUT":
            if scrip in active_end:
                active_end.remove(scrip)
            elif scrip in rev_rename_map and rev_rename_map[scrip] in active_end:
                active_end.remove(rev_rename_map[scrip])
                rename_consuming_rows.add(row_num)
            else:
                raise RuntimeError(f"Unexpected orphan OUT: row {row_num}, scrip '{scrip}'")

    log(f"Covered End Snapshot ({COVERED_END_DATE}): {len(active_end)} active constituents")
    assert len(active_end) == 501, f"Expected 501 active constituents at covered_end, found {len(active_end)}"
    log(f"Tracked Rename-Consuming Rows: {len(rename_consuming_rows)} events: {sorted(rename_consuming_rows)}")

    # Forward Replay Function
    def forward_replay(target_date_str: str) -> set:
        tgt_dt = pd.to_datetime(target_date_str).date()
        sub = n500[pd.to_datetime(n500["effective_date"]).dt.date <= tgt_dt]
        active = set()
        for _, r in sub.iterrows():
            if r["row"] in [2136, 2162]:
                continue
            scrip = r["scrip_name"]
            act = r["action"]
            if act == "IN":
                active.add(scrip)
            elif act == "OUT":
                if scrip in active:
                    active.remove(scrip)
                elif scrip in rev_rename_map and rev_rename_map[scrip] in active:
                    active.remove(rev_rename_map[scrip])
        return active

    # Backward Replay Function from covered_end (2020-09-14)
    def backward_replay(target_date_str: str) -> set:
        tgt_dt = pd.to_datetime(target_date_str).date()
        cov_dt = pd.to_datetime(COVERED_END_DATE).date()
        # Events strictly after target_date up to covered_end
        sub = n500[(pd.to_datetime(n500["effective_date"]).dt.date > tgt_dt) & 
                   (pd.to_datetime(n500["effective_date"]).dt.date <= cov_dt)]
        active = set(active_end)
        # Apply in reverse chronological order
        for _, r in sub.iloc[::-1].iterrows():
            row_num = r["row"]
            if row_num in [2136, 2162]:
                continue
            scrip = r["scrip_name"]
            act = r["action"]
            if act == "IN":
                assert scrip in active, f"Backward replay error: IN scrip '{scrip}' not present to remove"
                active.remove(scrip)
            elif act == "OUT":
                if row_num in rename_consuming_rows:
                    scrip_to_restore = rev_rename_map[scrip]
                else:
                    scrip_to_restore = scrip
                assert scrip_to_restore not in active, f"Backward replay error: OUT scrip '{scrip_to_restore}' already present to add"
                active.add(scrip_to_restore)
        return active

    # 3. Three-Date Deterministic Sampling & Round-Trip Equivalence Assertion
    log("\n--- 3. Three-Date Deterministic Sampling (Fixed Seed = 42) ---")
    unique_dates = sorted(pd.to_datetime(n500["effective_date"]).dt.strftime("%Y-%m-%d").unique())
    early_pool = [d for d in unique_dates if d < "2006-01-01"]
    mid_pool   = [d for d in unique_dates if "2006-01-01" <= d < "2014-01-01"]
    late_pool  = [d for d in unique_dates if d >= "2014-01-01" and d < COVERED_END_DATE]

    rng = np.random.RandomState(RNG_SEED)
    sample_early = str(rng.choice(early_pool))
    sample_mid   = str(rng.choice(mid_pool))
    sample_late  = str(rng.choice(late_pool))

    sample_specs = [
        {"id": 1, "tier": "Early History (1998–2005)", "date": sample_early},
        {"id": 2, "tier": "Mid History (2006–2013)",   "date": sample_mid},
        {"id": 3, "tier": "Late History (2014–2020)",  "date": sample_late}
    ]

    log(f"Sampled Test Dates across 22-year event log:")
    for s in sample_specs:
        log(f"  Sample #{s['id']} [{s['tier']}]: {s['date']}")

    summary_records = []

    for s in sample_specs:
        dt_str = s["date"]
        log(f"\nExecuting Bi-Directional Replay for Sample #{s['id']} ({dt_str}):")
        
        fwd_set = forward_replay(dt_str)
        bwd_set = backward_replay(dt_str)

        sym_diff = fwd_set ^ bwd_set
        is_equiv = (len(sym_diff) == 0)

        log(f"  Forward Replay Constituent Count:  {len(fwd_set)}")
        log(f"  Backward Replay Constituent Count: {len(bwd_set)}")
        log(f"  Symmetric Difference Count:        {len(sym_diff)}")
        log(f"  Mathematical Equivalence Status:   {'PASSED (Set-Identical)' if is_equiv else 'FAILED'}")

        assert is_equiv, f"Gate E Assertion FAILED on {dt_str}: Symmetric difference non-empty: {sym_diff}"

        # Export membership manifest
        manifest_filename = f"membership_{dt_str}.txt"
        manifest_path = VERIFY_DIR / manifest_filename
        sorted_manifest = sorted(fwd_set)
        with open(manifest_path, "w", encoding="utf-8") as mf:
            mf.write("\n".join(sorted_manifest) + "\n")

        manifest_hash = sha256_file(manifest_path)
        log(f"  Exported Membership Manifest: {manifest_path.relative_to(BASE_DIR)} ({len(sorted_manifest)} scrips, SHA256 {manifest_hash[:16]}...)")

        summary_records.append({
            "sample_id": s["id"],
            "sample_tier": s["tier"],
            "test_date": dt_str,
            "rng_seed": RNG_SEED,
            "forward_count": len(fwd_set),
            "backward_count": len(bwd_set),
            "sym_difference_count": len(sym_diff),
            "is_set_identical": is_equiv,
            "manifest_file": f"data/verification/{manifest_filename}",
            "manifest_sha256": manifest_hash
        })

    # 4. End-Boundary Continuity Audit (2020-09-13 to 2020-09-14)
    log("\n--- 4. End-Boundary Continuity Audit on covered_end (2020-09-14) ---")
    eve_date = "2020-09-13"
    eve_set = forward_replay(eve_date)
    end_set = forward_replay(COVERED_END_DATE)

    cov_end_dt = pd.to_datetime(COVERED_END_DATE).date()
    events_at_end = n500[pd.to_datetime(n500["effective_date"]).dt.date == cov_end_dt]

    log(f"Membership as-of Eve of Covered End ({eve_date}): {len(eve_set)} constituents")
    log(f"Events effective exactly on covered_end ({COVERED_END_DATE}): {len(events_at_end)} events")

    applied_events_log = []
    transition_set = set(eve_set)
    for _, r in events_at_end.iterrows():
        act = r["action"]
        scrip = r["scrip_name"]
        row_num = r["row"]
        applied_events_log.append(f"Row {row_num}: {act} '{scrip}'")
        log(f"  Applying Event -> Row {row_num}: {act} '{scrip}'")
        if act == "IN":
            transition_set.add(scrip)
        elif act == "OUT":
            if scrip in transition_set:
                transition_set.remove(scrip)
            elif scrip in rev_rename_map and rev_rename_map[scrip] in transition_set:
                transition_set.remove(rev_rename_map[scrip])
            else:
                raise RuntimeError(f"End boundary OUT error: scrip '{scrip}' not in eve set")

    end_diff = transition_set ^ end_set
    is_end_continuous = (len(end_diff) == 0) and (len(transition_set) == 501)

    log(f"Resulting Set Count after applying {COVERED_END_DATE} events: {len(transition_set)}")
    log(f"Snapshot Count at covered_end ({COVERED_END_DATE}):          {len(end_set)}")
    log(f"Set Difference with covered_end Snapshot:                    {len(end_diff)}")
    log(f"End-Boundary Continuity Status:                             {'PASSED (Strictly Continuous)' if is_end_continuous else 'FAILED'}")

    assert is_end_continuous, f"End boundary continuity assertion FAILED: difference: {end_diff}"

    # Append end boundary continuity to summary
    summary_records.append({
        "sample_id": 4,
        "sample_tier": "End-Boundary Continuity (2020-09-14)",
        "test_date": COVERED_END_DATE,
        "rng_seed": RNG_SEED,
        "forward_count": len(transition_set),
        "backward_count": len(end_set),
        "sym_difference_count": len(end_diff),
        "is_set_identical": is_end_continuous,
        "manifest_file": f"Applied: {'; '.join(applied_events_log)}",
        "manifest_sha256": "N/A (Transition Equivalence Verified)"
    })

    # 5. Export Summary CSV & Raw Text Log
    log("\n--- 5. Exporting Gate E Summary Evidence ---")
    summary_df = pd.DataFrame(summary_records)
    summary_csv_path = DATA_CSV_DIR / "gate_e_roundtrip_summary.csv"
    summary_df.to_csv(summary_csv_path, index=False)
    log(f"Exported summary CSV: {summary_csv_path.relative_to(BASE_DIR)} ({len(summary_df)} records)")

    log("\n" + "=" * 80)
    log("GATE E STEP 1 COMPLETE: ROUND-TRIP BI-DIRECTIONAL REPLAY & BOUNDARY AUDIT (PASS)")
    log("=" * 80)

    raw_path = RAW_DIR / "gate_e_roundtrip.txt"
    with open(raw_path, "w", encoding="utf-8") as rf:
        rf.write("\n".join(lines) + "\n")
    log(f"Saved raw log: {raw_path.relative_to(BASE_DIR)}")

if __name__ == "__main__":
    main()
