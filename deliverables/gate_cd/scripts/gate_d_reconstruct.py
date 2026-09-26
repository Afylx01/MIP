#!/usr/bin/env python3
"""
deliverables/gate_cd/scripts/gate_d_reconstruct.py
Phase 5.5 Gates C & D — Gate D: Universe Reconstruction & Price Gap Audit

1. Point-in-Time Universe Reconstruction:
   - Rebuilds NIFTY500 membership as-of 2016-01-04 (window start) and 2020-09-14 (covered_end).
   - Computes start constituent count, end constituent count, start symbols not in end set (removed),
     and end symbols not in start set (added).
   - Exports turnover metrics to deliverables/gate_cd/data_csv/reconstructed_turnover.csv.

2. Price Gap Audit across 57 Monthly Snapshots:
   - Evaluates all dynamic constituents used in Run (b) across all 57 monthly snapshots.
   - Verifies Bhavcopy price bar coverage in data/verification/halt1b_m1/adjusted_bhavcopy_bars_v2.parquet.
   - Audits missing bars percentage per symbol over each monthly period [T_i, T_{i+1}).
   - Invariant: Zero snapshots have > 20 symbols with > 30% missing bars.
   - Exports price gaps to deliverables/gate_cd/data_csv/price_gaps.csv.
   - Logs full output to deliverables/gate_cd/raw/gate_d_reconstruct.txt.
"""

import sys
import datetime
import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR = Path("/storage/emulated/0/Documents/Project MIP")
DELIV_DIR = BASE_DIR / "deliverables/gate_cd"
DATA_CSV_DIR = DELIV_DIR / "data_csv"
RAW_DIR = DELIV_DIR / "raw"

EVENTS_PATH = BASE_DIR / "data/index_events.parquet"
CORRECTIONS_PATH = BASE_DIR / "data/corrections.parquet"
SYMBOL_MAP_PATH = BASE_DIR / "data/symbol_map.parquet"
SNAPSHOTS_PATH = BASE_DIR / "deliverables/gate_ab/data_csv/snapshot_constituents_57.csv"
BARS_PATH = BASE_DIR / "data/verification/halt1b_m1/adjusted_bhavcopy_bars_v2.parquet"
CALENDAR_PATH = BASE_DIR / "data/trading_calendar.txt"

def main():
    lines = []
    def log(msg=""):
        print(msg)
        lines.append(msg)

    log("=" * 80)
    log("PHASE 5.5 GATES C & D — GATE D: UNIVERSE RECONSTRUCTION & PRICE GAP AUDIT")
    log(f"Timestamp: {datetime.datetime.now(datetime.timezone.utc).isoformat()}")
    log("=" * 80)

    for d in [DATA_CSV_DIR, RAW_DIR]:
        d.mkdir(parents=True, exist_ok=True)

    # 1. Point-in-Time Universe Reconstruction (2016-01-04 vs 2020-09-14)
    log("\n--- 1. Point-in-Time NIFTY500 Universe Reconstruction ---")
    events_df = pd.read_parquet(EVENTS_PATH)
    n500 = events_df[events_df["index"] == "NIFTY500"].sort_values(["effective_date", "row"]).reset_index(drop=True)

    corr_df = pd.read_parquet(CORRECTIONS_PATH)
    renames = corr_df[corr_df["action"] == "RENAME"]
    rev_rename_map = {r["target_scrip_name"]: r["scrip_name"] for _, r in renames.iterrows()}

    smap = pd.read_parquet(SYMBOL_MAP_PATH).set_index("scrip_name")

    def get_members(as_of_dt_str: str) -> set:
        as_of_dt = pd.to_datetime(as_of_dt_str).date()
        sub = n500[pd.to_datetime(n500["effective_date"]).dt.date <= as_of_dt]
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

    start_date = "2016-01-04"
    end_date = "2020-09-14"

    start_members = get_members(start_date)
    end_members = get_members(end_date)

    start_count = len(start_members)
    end_count = len(end_members)

    removed_scrips = sorted(start_members - end_members)
    added_scrips = sorted(end_members - start_members)
    common_scrips = sorted(start_members & end_members)

    log(f"As-of Window Start ({start_date}): {start_count} constituents")
    log(f"As-of Covered End  ({end_date}):   {end_count} constituents")
    log(f"Start constituents removed by end:  {len(removed_scrips)}")
    log(f"End constituents added since start: {len(added_scrips)}")
    log(f"Retained / Common constituents:     {len(common_scrips)}")

    # Check symbol mapping turnover
    start_symbols = {smap.loc[s, "symbol"] for s in start_members if s in smap.index and pd.notna(smap.loc[s, "symbol"]) and smap.loc[s, "symbol"]}
    end_symbols = {smap.loc[s, "symbol"] for s in end_members if s in smap.index and pd.notna(smap.loc[s, "symbol"]) and smap.loc[s, "symbol"]}

    symbols_removed = sorted(start_symbols - end_symbols)
    symbols_added = sorted(end_symbols - start_symbols)
    symbols_common = sorted(start_symbols & end_symbols)

    log(f"\nMapped Symbol Set Level:")
    log(f"  Start Unique Mapped Symbols: {len(start_symbols)}")
    log(f"  End Unique Mapped Symbols:   {len(end_symbols)}")
    log(f"  Symbols Removed:             {len(symbols_removed)}")
    log(f"  Symbols Added:               {len(symbols_added)}")
    log(f"  Symbols Common:              {len(symbols_common)}")

    turnover_pct = (len(removed_scrips) + len(added_scrips)) / (start_count + end_count) * 100.0
    log(f"Gross Constituent Turnover: {turnover_pct:.2f}% across the 4.7-year clamped window")

    # Export turnover summary
    turnover_summary = pd.DataFrame([{
        "start_date": start_date,
        "end_date": end_date,
        "start_constituent_count": start_count,
        "end_constituent_count": end_count,
        "removed_constituent_count": len(removed_scrips),
        "added_constituent_count": len(added_scrips),
        "common_constituent_count": len(common_scrips),
        "start_mapped_symbols": len(start_symbols),
        "end_mapped_symbols": len(end_symbols),
        "symbols_removed": len(symbols_removed),
        "symbols_added": len(symbols_added),
        "symbols_common": len(symbols_common),
        "gross_turnover_pct": round(turnover_pct, 2)
    }])
    turnover_csv = DATA_CSV_DIR / "reconstructed_turnover.csv"
    turnover_summary.to_csv(turnover_csv, index=False)
    log(f"Exported turnover summary to: {turnover_csv.relative_to(BASE_DIR)}")

    # 2. Bhavcopy Price Coverage & Gap Audit across 57 Monthly Snapshots
    log("\n--- 2. Bhavcopy Price Coverage & Price Gap Audit across 57 Snapshots ---")
    snaps_df = pd.read_csv(SNAPSHOTS_PATH)
    bars_df = pd.read_parquet(BARS_PATH)

    with open(CALENDAR_PATH) as f:
        cal_dates = sorted([line.strip() for line in f if line.strip()])
    cal_window = [d for d in cal_dates if start_date <= d <= end_date]

    snap_dates = sorted(snaps_df["snapshot_date"].unique())
    log(f"Auditing price coverage across {len(snap_dates)} snapshots ({snap_dates[0]} to {snap_dates[-1]})...")
    log(f"Total calendar trading days in clamped window: {len(cal_window)}")

    bars_by_sym = bars_df.groupby("symbol")["date"].apply(set).to_dict()

    gap_records = []
    snapshot_gap_summary = []

    for i, s_dt in enumerate(snap_dates):
        next_s_dt = snap_dates[i + 1] if i + 1 < len(snap_dates) else "2020-09-15"
        period_days = [d for d in cal_window if s_dt <= d < next_s_dt]
        sub_snap = snaps_df[snaps_df["snapshot_date"] == s_dt]

        # Constituents used in Run (b) (joint covered)
        sub_b = sub_snap[sub_snap["is_joint_covered"] == True]

        missing_gt_30_count = 0
        symbols_evaluated = len(sub_b)

        for _, r in sub_b.iterrows():
            sym = r["symbol"]
            scrip = r["scrip_name"]
            b_dates = bars_by_sym.get(sym, set())
            present_days = sum(1 for d in period_days if d in b_dates)
            expected_days = len(period_days)
            missing_pct = (1.0 - present_days / expected_days) if expected_days > 0 else 0.0

            if missing_pct > 0.30:
                missing_gt_30_count += 1
                gap_records.append({
                    "snapshot_idx": i + 1,
                    "snapshot_date": s_dt,
                    "period_end": next_s_dt,
                    "scrip_name": scrip,
                    "symbol": sym,
                    "period_trading_days": expected_days,
                    "present_trading_days": present_days,
                    "missing_trading_days": expected_days - present_days,
                    "missing_pct": round(missing_pct * 100.0, 2)
                })

        snapshot_gap_summary.append({
            "snapshot_idx": i + 1,
            "snapshot_date": s_dt,
            "period_trading_days": len(period_days),
            "run_b_constituents": symbols_evaluated,
            "symbols_missing_gt_30pct": missing_gt_30_count,
            "is_valid": (missing_gt_30_count <= 20)
        })

    gap_df = pd.DataFrame(gap_records) if gap_records else pd.DataFrame(columns=[
        "snapshot_idx", "snapshot_date", "period_end", "scrip_name", "symbol",
        "period_trading_days", "present_trading_days", "missing_trading_days", "missing_pct"
    ])
    gap_csv = DATA_CSV_DIR / "price_gaps.csv"
    gap_df.to_csv(gap_csv, index=False)
    log(f"Exported price gap records: {gap_csv.relative_to(BASE_DIR)} ({len(gap_df)} records, {gap_csv.stat().st_size:,} bytes)")

    snap_sum_df = pd.DataFrame(snapshot_gap_summary)
    max_missing_in_any_snap = snap_sum_df["symbols_missing_gt_30pct"].max()
    snaps_violating_threshold = int((snap_sum_df["symbols_missing_gt_30pct"] > 20).sum())

    log(f"\nPrice Coverage Audit Findings:")
    log(f"  Total Evaluated Run (b) Holdings Periods: {len(snap_dates)} snapshots")
    log(f"  Total Identified Price Gap Instances (>30% missing bars): {len(gap_df)}")
    log(f"  Max Symbols with >30% Missing Bars in Any Single Snapshot: {max_missing_in_any_snap} (threshold: <= 20)")
    log(f"  Snapshots with >20 Symbols with >30% Missing Bars: {snaps_violating_threshold} (expected: 0)")

    if not gap_df.empty:
        log("\nDetailed Manifest of Price Gap Instances (>30% missing bars):")
        for _, gr in gap_df.iterrows():
            log(f"  Snapshot #{int(gr['snapshot_idx'])} ({gr['snapshot_date']}): {gr['symbol']} ({gr['scrip_name']}) — present {int(gr['present_trading_days'])}/{int(gr['period_trading_days'])} days ({gr['missing_pct']}% missing)")

    # Assertions
    log("\n--- Acceptance Assertions ---")
    assert start_count == 500, f"Start count must be 500! Found: {start_count}"
    assert end_count == 501, f"End count must be 501! Found: {end_count}"
    assert snaps_violating_threshold == 0, f"Assertion FAILED: Found {snaps_violating_threshold} snapshots with >20 symbols missing >30% bars!"
    log(f"Assertion 1 PASSED: Start count {start_count} == 500, End count {end_count} == 501.")
    log(f"Assertion 2 PASSED: Zero snapshots have > 20 symbols with > 30% missing bars (max observed: {max_missing_in_any_snap} <= 20).")

    log("\n" + "=" * 80)
    log("GATE D STEP 2 COMPLETE: UNIVERSE RECONSTRUCTION & PRICE GAP AUDIT (PASS)")
    log("=" * 80)

    raw_path = RAW_DIR / "gate_d_reconstruct.txt"
    with open(raw_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    log(f"Saved raw log to: {raw_path.relative_to(BASE_DIR)}")

if __name__ == "__main__":
    main()
