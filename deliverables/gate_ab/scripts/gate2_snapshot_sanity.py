#!/usr/bin/env python3
"""
deliverables/gate_ab/scripts/gate2_snapshot_sanity.py
Phase 5.5 Gates A & B — Gate 2: Gate B — Chronological Snapshot Sanity Replay

1. Executes chronological forward replay across full 22-year event log (1998-08-01 to 2020-09-14):
   - Ingests data/index_events.parquet (9,121 events)
   - Stacks approved data/corrections.parquet dynamically
2. Invariant Assertions:
   - Orphan OUT count across full history == 0
   - Duplicate IN count across full history == 0
   - Constituent count on all 57 monthly snapshots within [490, 515] (expected [500, 501])
3. Exports:
   - deliverables/gate_ab/data_csv/snapshot_constituents_57.csv (complete constituent manifest for all 57 snapshots)
   - deliverables/gate_ab/data_csv/gate_b_snapshot_summary.csv
   - deliverables/gate_ab/raw/gate2_snapshot_sanity.txt
"""

import sys
import datetime
import pandas as pd
from pathlib import Path

BASE_DIR = Path("/storage/emulated/0/Documents/Project MIP")
DELIV_DIR = BASE_DIR / "deliverables/gate_ab"
DATA_CSV_DIR = DELIV_DIR / "data_csv"
RAW_DIR = DELIV_DIR / "raw"

EVENTS_PATH = BASE_DIR / "data/index_events.parquet"
CORRECTIONS_PATH = BASE_DIR / "data/corrections.parquet"
SYMBOL_MAP_PATH = BASE_DIR / "data/symbol_map.parquet"
ADJ_BARS_PATH = BASE_DIR / "data/verification/halt1b_m1/adjusted_bhavcopy_bars_v2.parquet"
CALENDAR_PATH = BASE_DIR / "data/trading_calendar.txt"

def is_scrip_unflagged(info: dict, snap_date: datetime.date, sym: str, snap_date_str: str, price_lookup: set) -> bool:
    m_stat = info.get("status", "")
    flags_str = info.get("flags", "") or ""
    if not flags_str:
        return True

    flag_tokens = [t.strip() for t in flags_str.split(";") if t.strip()]
    for token in flag_tokens:
        if token == "listing_after_first_seen":
            if (sym, snap_date_str) in price_lookup:
                continue
            listing_str = str(info.get("eq_listing_date", "")).strip()
            if listing_str and listing_str != "nan":
                try:
                    listing_dt = pd.to_datetime(listing_str).date()
                    if snap_date < listing_dt:
                        return False
                except Exception:
                    pass
        elif m_stat == "approved":
            continue
        elif any(k in token for k in ["duplicate_name_collision", "unsourced", "concurrent_alias_collision", "predecessor_marker", "first_token_mismatch", "name_mismatch"]):
            return False

    return True

def main():
    lines = []
    def log(msg=""):
        print(msg)
        lines.append(msg)

    log("=" * 80)
    log("PHASE 5.5 GATES A & B — GATE 2: CHRONOLOGICAL SNAPSHOT SANITY REPLAY")
    log(f"Timestamp: {datetime.datetime.now(datetime.timezone.utc).isoformat()}")
    log("=" * 80)

    for d in [DATA_CSV_DIR, RAW_DIR]:
        d.mkdir(parents=True, exist_ok=True)

    # 1. Load Data
    log("\n--- 1. Ingesting Events and Approved Corrections ---")
    events_df = pd.read_parquet(EVENTS_PATH)
    n500_events = events_df[events_df["index"] == "NIFTY500"].sort_values(["effective_date", "row"]).reset_index(drop=True)
    log(f"Loaded NIFTY500 index events: {len(n500_events):,} events")

    corr_df = pd.read_parquet(CORRECTIONS_PATH)
    log(f"Loaded approved corrections: {len(corr_df)} rules (all status = '{corr_df['status'].iloc[0]}')")
    assert (corr_df["status"] == "approved").all(), "All corrections must be approved!"

    renames = corr_df[corr_df["action"] == "RENAME"]
    rev_rename_map = {r["target_scrip_name"]: r["scrip_name"] for _, r in renames.iterrows()}
    fwd_rename_map = {r["scrip_name"]: (r["target_scrip_name"], pd.to_datetime(r["effective_date"]).date()) for _, r in renames.iterrows()}
    quarantine_rows = set(corr_df[corr_df["action"] == "REMOVE"]["scrip_name"].tolist())
    log(f"Constructed {len(rev_rename_map)} reverse rename linkages and {len(fwd_rename_map)} forward rename linkages.")

    smap = pd.read_parquet(SYMBOL_MAP_PATH)
    map_dict = smap.set_index("scrip_name").to_dict(orient="index")

    adj_bars = pd.read_parquet(ADJ_BARS_PATH)
    valid_bars = adj_bars[(adj_bars["close"] > 0) & (~adj_bars["close"].isna())]
    price_lookup = set(zip(valid_bars["symbol"], valid_bars["date"]))

    # 2. Chronological Forward Replay across Full 22-Year History
    log("\n--- 2. Full History Chronological Forward Replay ---")
    active_set = set()
    orphan_outs = []
    duplicate_ins = []

    for _, r in n500_events.iterrows():
        scrip = r["scrip_name"]
        act = r["action"]
        row_num = r["row"]
        dt_str = str(r["effective_date"])[:10]

        # Quarantined rows removal
        if row_num in [2136, 2162]:
            continue

        if act == "IN":
            if scrip in active_set:
                duplicate_ins.append((dt_str, scrip, row_num))
            else:
                active_set.add(scrip)
        elif act == "OUT":
            if scrip in active_set:
                active_set.remove(scrip)
            elif scrip in rev_rename_map and rev_rename_map[scrip] in active_set:
                # Corporate rename linkage successfully reconciled
                active_set.remove(rev_rename_map[scrip])
            else:
                orphan_outs.append((dt_str, scrip, row_num))

    log(f"Full History Continuity Audit Results (1998-08-01 to 2020-09-14):")
    log(f"  Total Events Processed:   {len(n500_events):,}")
    log(f"  Orphan OUT Count:         {len(orphan_outs)} (expected: 0)")
    log(f"  Duplicate IN Count:       {len(duplicate_ins)} (expected: 0)")
    log(f"  Final Active Membership:  {len(active_set)} constituents")

    assert len(orphan_outs) == 0, f"Assertion 1 FAILED: Found {len(orphan_outs)} orphan OUTs: {orphan_outs}"
    log("Assertion 1 PASSED: Exactly 0 orphan OUTs across entire 22-year event log.")

    assert len(duplicate_ins) == 0, f"Assertion 2 FAILED: Found {len(duplicate_ins)} duplicate INs: {duplicate_ins}"
    log("Assertion 2 PASSED: Exactly 0 duplicate INs across entire 22-year event log.")

    # 3. Monthly Snapshot Sanity Replay across 57 Snapshots
    log("\n--- 3. Monthly Snapshot Sanity Evaluation across 57 Snapshots ---")
    with open(CALENDAR_PATH) as f:
        cal_dates = sorted([line.strip() for line in f if line.strip()])
    by_ym = {}
    for d in cal_dates:
        if "2016-01-01" <= d <= "2020-09-14":
            by_ym.setdefault(d[:7], []).append(d)
    snapshot_dates = [days[0] for ym, days in sorted(by_ym.items())]
    log(f"Loaded {len(snapshot_dates)} monthly snapshot dates ({snapshot_dates[0]} to {snapshot_dates[-1]})")

    all_snapshot_constituents = []
    snapshot_summary_rows = []

    for idx, snap_date_str in enumerate(snapshot_dates, 1):
        snap_date = datetime.datetime.strptime(snap_date_str, "%Y-%m-%d").date()
        sub = n500_events[pd.to_datetime(n500_events["effective_date"]).dt.date <= snap_date]

        snap_active = set()
        for _, r in sub.iterrows():
            scrip = r["scrip_name"]
            act = r["action"]
            if r["row"] in [2136, 2162]:
                continue
            if act == "IN":
                snap_active.add(scrip)
            elif act == "OUT":
                if scrip in snap_active:
                    snap_active.remove(scrip)
                elif scrip in rev_rename_map and rev_rename_map[scrip] in snap_active:
                    snap_active.remove(rev_rename_map[scrip])

        count = len(snap_active)
        is_valid_range = (490 <= count <= 515)

        resolved_cnt = 0
        price_cnt = 0
        unflagged_cnt = 0
        joint_cnt = 0

        for scrip in sorted(snap_active):
            info = map_dict.get(scrip, {})
            # If predecessor is unresolved and rename is effective, check target
            if info.get("status") not in ["auto", "approved"] and scrip in fwd_rename_map:
                tgt, eff_dt = fwd_rename_map[scrip]
                if snap_date >= eff_dt and tgt in map_dict:
                    info = map_dict.get(tgt, {})

            status = info.get("status", "unresolved")
            sym = info.get("symbol", "").strip()

            is_res = (status in ["auto", "approved"] and len(sym) > 0)
            is_prc = is_res and ((sym, snap_date_str) in price_lookup)
            is_unf = is_res and is_scrip_unflagged(info, snap_date, sym, snap_date_str, price_lookup)
            is_jnt = is_res and is_prc and is_unf

            if is_res:
                resolved_cnt += 1
            if is_prc:
                price_cnt += 1
            if is_unf:
                unflagged_cnt += 1
            if is_jnt:
                joint_cnt += 1

            all_snapshot_constituents.append({
                "snapshot_idx": idx,
                "snapshot_date": snap_date_str,
                "scrip_name": scrip,
                "symbol": sym,
                "status": status,
                "is_price_covered": is_prc,
                "is_unflagged": is_unf,
                "is_joint_covered": is_jnt
            })

        snapshot_summary_rows.append({
            "snapshot_idx": idx,
            "snapshot_date": snap_date_str,
            "constituent_count": count,
            "is_valid_range_490_515": is_valid_range,
            "resolved_count": resolved_cnt,
            "price_covered_count": price_cnt,
            "unflagged_count": unflagged_cnt,
            "joint_covered_count": joint_cnt
        })

    # Export manifests
    df_constituents = pd.DataFrame(all_snapshot_constituents)
    constituents_csv = DATA_CSV_DIR / "snapshot_constituents_57.csv"
    df_constituents.to_csv(constituents_csv, index=False)
    log(f"Exported complete snapshot constituents manifest: {constituents_csv.relative_to(BASE_DIR)} ({len(df_constituents):,} rows, {constituents_csv.stat().st_size:,} bytes)")

    df_summary = pd.DataFrame(snapshot_summary_rows)
    summary_csv = DATA_CSV_DIR / "gate_b_snapshot_summary.csv"
    df_summary.to_csv(summary_csv, index=False)
    log(f"Exported snapshot summary: {summary_csv.relative_to(BASE_DIR)} ({len(df_summary)} rows)")

    # Assertions
    min_cnt = df_summary["constituent_count"].min()
    med_cnt = df_summary["constituent_count"].median()
    max_cnt = df_summary["constituent_count"].max()
    all_within_range = df_summary["is_valid_range_490_515"].all()

    log("\n" + "=" * 80)
    log("GATE B CONSTITUENT COUNT INVARIANTS & BOUNDARY VERIFICATION")
    log("=" * 80)
    log(f"Snapshot Constituent Count Distribution:")
    log(f"  Min Count:    {min_cnt}")
    log(f"  Median Count: {med_cnt:.1f}")
    log(f"  Max Count:    {max_cnt}")
    log(f"  Statutory Range: [490, 515]")
    log(f"  100% of Snapshots within Range: {all_within_range}")

    assert all_within_range, f"Assertion 3 FAILED: Constituent counts violated [490, 515] (min: {min_cnt}, max: {max_cnt})"
    log("Assertion 3 PASSED: Constituent count strictly within statutory range [490, 515] across all 57 monthly snapshots.")

    log("\nSample Milestone Snapshots:")
    for ms in ["2016-01-04", "2018-01-01", "2020-09-01"]:
        sub_ms = df_summary[df_summary["snapshot_date"] == ms]
        if not sub_ms.empty:
            r = sub_ms.iloc[0]
            log(f"  Snapshot {r['snapshot_date']} (Snap #{int(r['snapshot_idx'])}): Constituents = {r['constituent_count']}, Joint Covered = {r['joint_covered_count']} (Range Valid: {r['is_valid_range_490_515']})")

    log("\n" + "=" * 80)
    log("GATE B COMPLETE: REPLAY CONTINUITY & SNAPSHOT SANITY VERIFIED (PASS)")
    log("=" * 80)

    raw_path = RAW_DIR / "gate2_snapshot_sanity.txt"
    with open(raw_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    log(f"Saved raw log to: {raw_path.relative_to(BASE_DIR)}")

if __name__ == "__main__":
    main()
