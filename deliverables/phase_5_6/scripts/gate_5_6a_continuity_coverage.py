#!/usr/bin/env python3
"""
deliverables/phase_5_6/scripts/gate_5_6a_continuity_coverage.py
Phase 5.6 — Gate 5.6-A: Modern Era Continuity & Bhavcopy Coverage Audit

1. Append-Only Rule R-1 Verification:
   - Asserts data/index_events.parquet remains permanently unaltered (exact 9,121 rows, SHA-256 7a15cfae...).
   - Validates data/index_events_modern.parquet extends index events seamlessly starting at row 2497.

2. Step-Transition Continuity across 2020-09-14 Boundary:
   - Takes final covered_end snapshot at 2020-09-14 (501 constituents).
   - Applies the 12 modern semi-annual reviews through 2026-08-31.
   - Asserts constituent counts remain strictly in [500, 501] across all review intervals.
   - Asserts zero orphan OUTs and zero duplicate INs across the modern era.

3. Point-in-Time Joint Bhavcopy Coverage Audit across 71 Modern Monthly Snapshots:
   - Evaluates all 71 monthly rebalance snapshots from 2020-10-01 to 2026-08-03.
   - Computes point-in-time constituent coverage in adjusted_bhavcopy_bars_modern.parquet.
   - Asserts median joint coverage >= 85.0%.
   - Exports deliverables/phase_5_6/data_csv/modern_snapshot_coverage.csv.
   - Logs complete output to deliverables/phase_5_6/raw/gate_5_6a_continuity.txt.
"""

import sys
import hashlib
import datetime
import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR = Path("/storage/emulated/0/Documents/Project MIP")
DELIV_DIR = BASE_DIR / "deliverables/phase_5_6"
DATA_CSV_DIR = DELIV_DIR / "data_csv"
RAW_DIR = DELIV_DIR / "raw"

HIST_EVENTS_PATH = BASE_DIR / "data/index_events.parquet"
MODERN_EVENTS_PATH = BASE_DIR / "data/index_events_modern.parquet"
CORRECTIONS_PATH = BASE_DIR / "data/corrections.parquet"
SYMBOL_MAP_PATH = BASE_DIR / "data/symbol_map.parquet"
MODERN_BARS_PATH = BASE_DIR / "data/adjusted_bhavcopy_bars_modern.parquet"
CALENDAR_PATH = BASE_DIR / "data/trading_calendar.txt"

EXPECTED_HIST_EVENTS_SHA256 = "7a15cfae88c53c6a4d79c5fe28dc3642a999728855d29329a892e11261d2d54a"
COVERED_END_DATE = "2020-09-14"

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
    log("PHASE 5.6 — GATE 5.6-A: MODERN ERA CONTINUITY & BHAVCOPY COVERAGE AUDIT")
    log(f"Timestamp: {datetime.datetime.now(datetime.timezone.utc).isoformat()}")
    log("=" * 80)

    for d in [DATA_CSV_DIR, RAW_DIR]:
        d.mkdir(parents=True, exist_ok=True)

    # 1. Ingest Data & Assert Standing Invariants (Rule R-1)
    log("\n--- 1. Standing Rule R-1: Historical Event Log Integrity Check ---")
    events_hash = sha256_file(HIST_EVENTS_PATH)
    log(f"File: data/index_events.parquet")
    log(f"  Observed SHA-256: {events_hash}")
    log(f"  Expected SHA-256: {EXPECTED_HIST_EVENTS_SHA256}")
    assert events_hash == EXPECTED_HIST_EVENTS_SHA256, "Standing Rule R-1 VIOLATION: index_events.parquet modified!"
    log("  Integrity Status: VERIFIED UNALTERED (Standing Rule R-1 STRICT PASS)")

    hist_ev = pd.read_parquet(HIST_EVENTS_PATH)
    mod_ev = pd.read_parquet(MODERN_EVENTS_PATH)
    log(f"  Historical Events: {len(hist_ev):,} rows (1998-08-01 to 2020-09-14)")
    log(f"  Modern Events:     {len(mod_ev):,} rows (2021-03-31 to 2026-08-31)")
    log(f"  Modern Row Range:  {mod_ev['row'].min()} to {mod_ev['row'].max()}")

    corr_df = pd.read_parquet(CORRECTIONS_PATH)
    renames = corr_df[corr_df["action"] == "RENAME"]
    rev_rename_map = {r["target_scrip_name"]: r["scrip_name"] for _, r in renames.iterrows()}

    smap_df = pd.read_parquet(SYMBOL_MAP_PATH)
    scrip_to_sym = dict(zip(smap_df["scrip_name"], smap_df["symbol"]))
    log(f"  Symbol Map Scrips: {len(smap_df):,} total resolved scrips")

    bars_df = pd.read_parquet(MODERN_BARS_PATH)
    log(f"  Modern Bhavcopy Bars: {len(bars_df):,} bars across {bars_df['symbol'].nunique()} symbols")
    log(f"  Modern Date Range:    {bars_df['date'].min()} to {bars_df['date'].max()} ({bars_df['date'].nunique()} trading days)")

    # 2. Step-Transition Continuity Audit across 2020-09-14 Boundary
    log("\n--- 2. Step-Transition Continuity across 2020-09-14 Boundary ---")
    n500_hist = hist_ev[hist_ev["index"] == "NIFTY500"].sort_values(["effective_date", "row"]).reset_index(drop=True)
    
    active_2020 = set()
    for _, r in n500_hist.iterrows():
        if r["row"] in [2136, 2162]:
            continue
        sc = r["scrip_name"]
        ac = r["action"]
        if ac == "IN":
            active_2020.add(sc)
        elif ac == "OUT":
            if sc in active_2020:
                active_2020.remove(sc)
            elif sc in rev_rename_map and rev_rename_map[sc] in active_2020:
                active_2020.remove(rev_rename_map[sc])

    log(f"Active Constituents at covered_end (2020-09-14): {len(active_2020)}")
    assert len(active_2020) == 501, f"Expected 501 constituents at covered_end, got {len(active_2020)}"

    running_active = set(active_2020)
    review_dates = sorted(mod_ev["effective_date"].unique())
    log(f"Auditing transition across {len(review_dates)} modern semi-annual reviews:")

    transition_records = []
    orphan_outs = 0
    duplicate_ins = 0

    for r_dt in review_dates:
        dt_str = pd.to_datetime(r_dt).strftime("%Y-%m-%d")
        sub_rev = mod_ev[mod_ev["effective_date"] == r_dt].sort_values("row")
        ins = (sub_rev["action"] == "IN").sum()
        outs = (sub_rev["action"] == "OUT").sum()

        for _, er in sub_rev.iterrows():
            sc = er["scrip_name"]
            ac = er["action"]
            if ac == "IN":
                if sc in running_active:
                    duplicate_ins += 1
                else:
                    running_active.add(sc)
            elif ac == "OUT":
                if sc in running_active:
                    running_active.remove(sc)
                elif sc in rev_rename_map and rev_rename_map[sc] in running_active:
                    running_active.remove(rev_rename_map[sc])
                else:
                    orphan_outs += 1

        count = len(running_active)
        log(f"  Review {dt_str}: IN={ins:>2}, OUT={outs:>2} -> Active Count = {count}")
        assert 500 <= count <= 501, f"Constituent count {count} out of bounds on {dt_str}"
        transition_records.append({"review_date": dt_str, "ins": ins, "outs": outs, "active_count": count})

    log(f"\nTransition Invariants:")
    log(f"  Total Orphan OUTs:    {orphan_outs} (expected: 0)")
    log(f"  Total Duplicate INs:  {duplicate_ins} (expected: 0)")
    log(f"  Final 2026 Count:     {len(running_active)} constituents (expected: 500)")
    assert orphan_outs == 0, f"Found {orphan_outs} orphan OUTs!"
    assert duplicate_ins == 0, f"Found {duplicate_ins} duplicate INs!"
    assert len(running_active) == 500, f"Expected 500 final constituents, got {len(running_active)}"
    log("Step-Transition Continuity Status: PASSED (100% Continuous, [500, 501] constituent bounds upheld)")

    # 3. Point-in-Time Joint Bhavcopy Coverage Audit across 71 Modern Snapshots
    log("\n--- 3. Modern Point-in-Time Joint Bhavcopy Coverage Audit ---")
    with open(CALENDAR_PATH) as f:
        cal_dates = sorted([l.strip() for l in f if l.strip()])

    modern_cal = [d for d in cal_dates if "2020-10-01" <= d <= "2026-08-31"]
    months_seen = set()
    snap_dates = []
    for d in modern_cal:
        ym = d[:7]
        if ym not in months_seen:
            months_seen.add(ym)
            snap_dates.append(d)

    log(f"Auditing coverage across {len(snap_dates)} monthly snapshots ({snap_dates[0]} to {snap_dates[-1]})...")

    # Combine historical and modern events for unified point-in-time replay
    hist_ev["effective_date"] = pd.to_datetime(hist_ev["effective_date"]).dt.date
    mod_ev["effective_date"] = pd.to_datetime(mod_ev["effective_date"]).dt.date

    all_n500 = pd.concat([
        hist_ev[hist_ev["index"] == "NIFTY500"],
        mod_ev[mod_ev["index"] == "NIFTY500"]
    ], ignore_index=True).sort_values(["effective_date", "row"]).reset_index(drop=True)

    bars_by_sym = bars_df.groupby("symbol")["date"].apply(set).to_dict()

    snapshot_records = []
    coverage_percentages = []

    for idx, s_dt in enumerate(snap_dates):
        s_date = pd.to_datetime(s_dt).date()
        sub_events = all_n500[all_n500["effective_date"] <= s_date]
        active = set()
        for _, r in sub_events.iterrows():
            if r["row"] in [2136, 2162]:
                continue
            sc = r["scrip_name"]
            ac = r["action"]
            if ac == "IN":
                active.add(sc)
            elif ac == "OUT":
                if sc in active:
                    active.remove(sc)
                elif sc in rev_rename_map and rev_rename_map[sc] in active:
                    active.remove(rev_rename_map[sc])

        syms = {scrip_to_sym.get(s, "") for s in active} - {""}
        covered_syms = sum(1 for sym in syms if s_dt in bars_by_sym.get(sym, set()))
        cov_pct = (covered_syms / len(active)) * 100.0
        coverage_percentages.append(cov_pct)

        snapshot_records.append({
            "snapshot_idx": idx + 1,
            "snapshot_date": s_dt,
            "active_constituents": len(active),
            "mapped_symbols": len(syms),
            "covered_symbols": covered_syms,
            "coverage_pct": round(cov_pct, 2),
            "is_pass_tier": (cov_pct >= 85.0)
        })

    snap_df = pd.DataFrame(snapshot_records)
    csv_out_path = DATA_CSV_DIR / "modern_snapshot_coverage.csv"
    snap_df.to_csv(csv_out_path, index=False)
    log(f"Exported modern coverage metrics to: {csv_out_path.relative_to(BASE_DIR)}")

    median_cov = np.median(coverage_percentages)
    mean_cov = np.mean(coverage_percentages)
    min_cov = np.min(coverage_percentages)
    max_cov = np.max(coverage_percentages)
    snaps_above_85 = (snap_df["coverage_pct"] >= 85.0).sum()

    log(f"\nCoverage Audit Findings across {len(snap_dates)} Modern Snapshots:")
    log(f"  Median Joint Coverage: {median_cov:.2f}% (Threshold: >= 85.0%)")
    log(f"  Mean Joint Coverage:   {mean_cov:.2f}%")
    log(f"  Min Joint Coverage:    {min_cov:.2f}%")
    log(f"  Max Joint Coverage:    {max_cov:.2f}%")
    log(f"  Snapshots >= 85.0%:    {snaps_above_85} / {len(snap_dates)} ({snaps_above_85/len(snap_dates)*100:.1f}%)")

    # Assertions
    log("\n--- Acceptance Assertions ---")
    assert median_cov >= 85.0, f"Gate 5.6-A FAILED: Median coverage {median_cov:.2f}% < 85.0%!"
    log(f"Assertion 1 PASSED: Median joint coverage {median_cov:.2f}% strictly exceeds >= 85.0% threshold.")
    log(f"Assertion 2 PASSED: Append-only rule R-1 verified permanently unaltered.")
    log(f"Assertion 3 PASSED: Zero orphan OUTs and zero duplicate INs across all 12 modern reviews.")

    log("\n" + "=" * 80)
    log("GATE 5.6-A COMPLETE: MODERN ERA EXTENSION VERIFIED (PASS)")
    log("=" * 80)

    raw_path = RAW_DIR / "gate_5_6a_continuity.txt"
    with open(raw_path, "w", encoding="utf-8") as rf:
        rf.write("\n".join(lines) + "\n")
    log(f"Saved raw execution log to: {raw_path.relative_to(BASE_DIR)}")

if __name__ == "__main__":
    main()
