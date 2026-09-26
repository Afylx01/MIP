#!/usr/bin/env python3
"""
deliverables/gate3/scripts/gate3_simulated_replay.py
Phase 5.5 Gate 3 — Gate 3: Simulated Replay & Continuity Assertion

1. Stacks data/corrections.parquet (treating status == 'proposed' as active for simulation only)
   on top of data/index_events.parquet (and raw IndexInclExcl.xls).
2. Verifies assertions:
   - Orphan OUT count drops from 15 to 0.
   - Duplicate IN count drops from 1 to 0.
   - NIFTY500 constituent count on all 57 monthly snapshots stays within [490, 515].
3. Exports:
   - deliverables/gate3/data_csv/simulation_rebalance_counts.csv
   - deliverables/gate3/raw/gate3_simulated_replay.txt
"""

import sys
import datetime
import xlrd
import pandas as pd
from pathlib import Path

BASE_DIR = Path("/sdcard/Documents/Project MIP")
DELIVERABLES_DIR = BASE_DIR / "deliverables/gate3"
DATA_CSV_DIR = DELIVERABLES_DIR / "data_csv"
RAW_DIR = DELIVERABLES_DIR / "raw"

INDEX_EVENTS_PARQUET = BASE_DIR / "data/index_events.parquet"
CORRECTIONS_PARQUET = BASE_DIR / "data/corrections.parquet"
XLS_FILE = BASE_DIR / "IndexInclExcl.xls"
QUARANTINE_CSV = BASE_DIR / "deliverables/gate_2c/data_csv/quarantine_gate1.csv"
TRADING_CALENDAR_TXT = BASE_DIR / "data/trading_calendar.txt"

for d in [DATA_CSV_DIR, RAW_DIR]:
    d.mkdir(parents=True, exist_ok=True)

def parse_excel_nifty500():
    wb = xlrd.open_workbook(str(XLS_FILE))
    sheet = wb.sheet_by_name("Nifty 500")
    rows = []
    for r in range(1, sheet.nrows):
        d_val = sheet.cell_value(r, 1)
        d_typ = sheet.cell_type(r, 1)
        scrip = str(sheet.cell_value(r, 2)).strip()
        act_str = str(sheet.cell_value(r, 3)).strip().lower()
        act = "IN" if "inclusion" in act_str else ("OUT" if "exclusion" in act_str else "OTHER")

        if d_typ == 3:
            dt_tuple = xlrd.xldate_as_tuple(d_val, wb.datemode)
            dt = datetime.date(*dt_tuple[:3])
        elif d_typ == 1:
            parts = [int(p) for p in str(d_val).strip().split("-")]
            dt = datetime.date(parts[2], parts[1], parts[0])
        elif d_typ == 2:
            dt_tuple = xlrd.xldate_as_tuple(d_val, wb.datemode)
            dt = datetime.date(*dt_tuple[:3])
        else:
            dt = None

        rows.append({
            "row": r + 1,
            "effective_date": dt,
            "scrip_name": scrip,
            "action": act
        })
    return rows

def main():
    print("=" * 80)
    print("PHASE 5.5 GATE 3 — GATE 3: SIMULATED REPLAY & CONTINUITY ASSERTION")
    print(f"Timestamp: {datetime.datetime.now(datetime.timezone.utc).isoformat()}")
    print("=" * 80)

    # 1. Load Data
    print("\n--- 1. Loading Index Events and Proposed Corrections ---")
    assert INDEX_EVENTS_PARQUET.exists(), f"Missing {INDEX_EVENTS_PARQUET}"
    events_df = pd.read_parquet(INDEX_EVENTS_PARQUET)
    n500_events = events_df[events_df["index"] == "NIFTY500"].sort_values(["effective_date", "row"]).reset_index(drop=True)
    print(f"Loaded NIFTY500 events from parquet: {len(n500_events):,} events")

    assert CORRECTIONS_PARQUET.exists(), f"Missing {CORRECTIONS_PARQUET}"
    corr_df = pd.read_parquet(CORRECTIONS_PARQUET)
    print(f"Loaded proposed corrections: {len(corr_df)} rules (all status = '{corr_df['status'].iloc[0]}')")

    # Load quarantined row numbers for Nifty 500
    quarantine_df = pd.read_csv(QUARANTINE_CSV)
    n500_quarantine_rows = set(quarantine_df[quarantine_df["sheet"] == "Nifty 500"]["row"].tolist())
    print(f"Loaded quarantined row numbers from Gate 1 manifest: {n500_quarantine_rows}")

    # Build rename lookups
    renames = corr_df[corr_df["action"] == "RENAME"]
    # target_scrip_name -> predecessor_scrip_name
    rev_rename_map = {r["target_scrip_name"]: r["scrip_name"] for _, r in renames.iterrows()}
    # predecessor_scrip_name -> target_scrip_name
    fwd_rename_map = {r["scrip_name"]: (r["target_scrip_name"], r["effective_date"]) for _, r in renames.iterrows()}

    print(f"Constructed {len(rev_rename_map)} rename linkages.")

    # 2. Simulation Replay on Raw Workbook Events (Unfiltered 2,495 rows)
    print("\n--- 2. Simulated Replay on Raw Workbook Events (IndexInclExcl.xls) ---")
    raw_xls_rows = parse_excel_nifty500()
    sorted_raw = sorted(raw_xls_rows, key=lambda x: (x["effective_date"] if x["effective_date"] else datetime.date(1900, 1, 1), x["row"]))

    active_raw = set()
    raw_orphans = []
    raw_duplicates = []

    for r in sorted_raw:
        # Enforce quarantine removal of redundant duplicate rows 2136 and 2162
        if r["row"] in n500_quarantine_rows:
            continue

        dt_str = r["effective_date"].strftime("%Y-%m-%d") if r["effective_date"] else "UNKNOWN"
        scrip = r["scrip_name"]
        act = r["action"]

        if act == "IN":
            if scrip in active_raw:
                raw_duplicates.append((dt_str, scrip, r["row"]))
            else:
                active_raw.add(scrip)
        elif act == "OUT":
            if scrip in active_raw:
                active_raw.remove(scrip)
            elif scrip in rev_rename_map and rev_rename_map[scrip] in active_raw:
                # Rename linkage successfully applied!
                active_raw.remove(rev_rename_map[scrip])
            else:
                raw_orphans.append((dt_str, scrip, r["row"]))

    print(f"Results of Replay on Raw Workbook + Corrections:")
    print(f"  Orphan OUT count:   {len(raw_orphans)} (was 15)")
    print(f"  Duplicate IN count: {len(raw_duplicates)} (was 1)")
    assert len(raw_orphans) == 0, f"Failed assertion: Remaining raw orphans: {raw_orphans}"
    assert len(raw_duplicates) == 0, f"Failed assertion: Remaining raw duplicates: {raw_duplicates}"
    print("  -> Assertion 1 PASSED: Orphan OUTs dropped from 15 to EXACTLY 0.")
    print("  -> Assertion 2 PASSED: Duplicate INs dropped from 1 to EXACTLY 0.")

    # 3. Simulation Replay on index_events.parquet + Corrections
    print("\n--- 3. Simulated Replay on data/index_events.parquet + Corrections ---")
    active_pq = set()
    pq_orphans = []
    pq_duplicates = []

    for _, r in n500_events.iterrows():
        dt_str = str(r["effective_date"])[:10]
        scrip = r["scrip_name"]
        act = r["action"]

        if act == "IN":
            if scrip in active_pq:
                pq_duplicates.append((dt_str, scrip, r["row"]))
            else:
                active_pq.add(scrip)
        elif act == "OUT":
            if scrip in active_pq:
                active_pq.remove(scrip)
            elif scrip in rev_rename_map and rev_rename_map[scrip] in active_pq:
                active_pq.remove(rev_rename_map[scrip])
            else:
                pq_orphans.append((dt_str, scrip, r["row"]))

    print(f"Results of Replay on index_events.parquet + Corrections:")
    print(f"  Orphan OUT count:   {len(pq_orphans)}")
    print(f"  Duplicate IN count: {len(pq_duplicates)}")
    assert len(pq_orphans) == 0, f"Failed assertion: Remaining pq orphans: {pq_orphans}"
    assert len(pq_duplicates) == 0, f"Failed assertion: Remaining pq duplicates: {pq_duplicates}"
    print("  -> Assertion 3 PASSED: Zero orphans and zero duplicates on index_events.parquet.")

    # 4. Snapshot Constituent Count Invariance across 57 Monthly Snapshots
    print("\n--- 4. Evaluating Snapshot Constituent Counts across 57 Monthly Snapshots ---")
    with open(TRADING_CALENDAR_TXT) as f:
        cal_dates = sorted([line.strip() for line in f if line.strip()])

    by_ym = {}
    for d in cal_dates:
        if "2016-01-01" <= d <= "2020-09-14":
            ym = d[:7]
            by_ym.setdefault(ym, []).append(d)
    snapshot_dates = [days[0] for ym, days in sorted(by_ym.items())]
    print(f"Loaded {len(snapshot_dates)} monthly snapshot dates ({snapshot_dates[0]} to {snapshot_dates[-1]}).")

    snapshot_records = []
    for idx, snap_dt_str in enumerate(snapshot_dates, 1):
        snap_dt = pd.to_datetime(snap_dt_str).date()
        sub = n500_events[pd.to_datetime(n500_events["effective_date"]).dt.date <= snap_dt]
        
        # Uncorrected replay count
        uncorr_active = set()
        for _, r in sub.iterrows():
            if r["action"] == "IN":
                uncorr_active.add(r["scrip_name"])
            elif r["action"] == "OUT":
                uncorr_active.discard(r["scrip_name"])
        uncorr_count = len(uncorr_active)

        # Corrected replay count
        corr_active = set()
        for _, r in sub.iterrows():
            scrip = r["scrip_name"]
            act = r["action"]
            if act == "IN":
                corr_active.add(scrip)
            elif act == "OUT":
                if scrip in corr_active:
                    corr_active.remove(scrip)
                elif scrip in rev_rename_map and rev_rename_map[scrip] in corr_active:
                    corr_active.remove(rev_rename_map[scrip])
        corr_count = len(corr_active)

        snapshot_records.append({
            "snapshot_idx": idx,
            "snapshot_date": snap_dt_str,
            "uncorrected_constituent_count": uncorr_count,
            "corrected_constituent_count": corr_count,
            "is_valid_range_490_515": (490 <= corr_count <= 515),
            "delta": corr_count - uncorr_count
        })

    snap_df = pd.DataFrame(snapshot_records)
    out_csv = DATA_CSV_DIR / "simulation_rebalance_counts.csv"
    snap_df.to_csv(out_csv, index=False)
    print(f"Exported simulation rebalance counts: {out_csv} ({len(snap_df)} snapshots)")

    min_c = snap_df["corrected_constituent_count"].min()
    med_c = snap_df["corrected_constituent_count"].median()
    max_c = snap_df["corrected_constituent_count"].max()
    all_valid = snap_df["is_valid_range_490_515"].all()

    print(f"\nCorrected Constituent Count Distribution:")
    print(f"  Min:    {min_c}")
    print(f"  Median: {med_c:.1f}")
    print(f"  Max:    {max_c}")
    print(f"  All within [490, 515]: {all_valid}")
    assert all_valid, "Failed assertion: Constituent counts violated [490, 515] boundary!"
    print("  -> Assertion 4 PASSED: All 57 snapshots strictly within statutory range [490, 515].")

    print("\nSample Milestone Snapshots:")
    milestones = ["2016-01-04", "2018-01-01", "2020-09-01"]
    for ms in milestones:
        sub_m = snap_df[snap_df["snapshot_date"] == ms]
        if not sub_m.empty:
            r = sub_m.iloc[0]
            print(f"  Snapshot {r['snapshot_date']} (Snap #{int(r['snapshot_idx'])}): uncorrected = {r['uncorrected_constituent_count']}, corrected = {r['corrected_constituent_count']} (delta = {r['delta']})")

    print("\n" + "=" * 80)
    print("GATE 3 SIMULATED REPLAY COMPLETE: ALL CONTINUITY ASSERTIONS PASSED")
    print("=" * 80)

if __name__ == "__main__":
    main()
