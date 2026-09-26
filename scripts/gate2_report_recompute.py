#!/usr/bin/env python3
"""
Step 6 — Recompute Gate 2 Report (NIFTY500 Only)
- Recomputes Gate 2 report for NIFTY500 ONLY.
- Other six indices show: "event log only, not reconstructable" instead of resolved fractions.
- Snapshots with zero members print N/A, never 0.0%.
- Reports before vs after rebuild:
    - counts by status (auto, proposed, unresolved) and by flag
    - blocked IN and OUT events
    - name-level resolved fractions for 2010-01-01, 2014-01-01, 2018-01-01 and covered_end snapshots
    - all monthly snapshots (count, min, median, count below 80%)
    - second, separate metric: price-covered fraction (members whose mapped symbol has coverage_pct >= 90%)
- Includes survivorship disclosure line:
    "Survivorship note: <n> of <total> NIFTY500 members at <snapshot> are unresolved or lack price data."
"""

import os
import sys
import datetime
import pandas as pd

EVENTS_PATH = "data/index_events.parquet"
V1_MAP_PATH = "data/symbol_map_v1.parquet"
CURRENT_MAP_PATH = "data/symbol_map.parquet"

PRIMARY_INDICES = [
    "NIFTY500",
    "NIFTY50",
    "NIFTYNEXT50",
    "NIFTY100",
    "NIFTY200",
    "NIFTYMIDCAP100",
    "NIFTYSMALLCAP100",
]

GATE_B_DATES = ["2010-01-01", "2014-01-01", "2018-01-01"]

def evaluate_map(map_path, events_df):
    df_map = pd.read_parquet(map_path)
    status_map = dict(zip(df_map["scrip_name"], df_map["status"]))
    cov_map = dict(zip(df_map["scrip_name"], df_map.get("coverage_pct", pd.Series([0.0]*len(df_map)))))
    sym_map = dict(zip(df_map["scrip_name"], df_map["symbol"]))

    status_counts = df_map["status"].value_counts().to_dict()
    
    # Flags counts
    flag_counts = {}
    if "flags" in df_map.columns:
        for fl_str in df_map["flags"].dropna():
            if fl_str:
                for f in fl_str.split(";"):
                    k = f.split("(")[0]
                    flag_counts[k] = flag_counts.get(k, 0) + 1

    return {
        "df_map": df_map,
        "status_map": status_map,
        "cov_map": cov_map,
        "sym_map": sym_map,
        "status_counts": status_counts,
        "flag_counts": flag_counts,
    }

def main():
    print("=" * 80)
    print("GATE 2 REPORT RECOMPUTATION (NIFTY500 ONLY) — BEFORE VS AFTER REBUILD")
    print("=" * 80)

    events_df = pd.read_parquet(EVENTS_PATH)
    nifty500_events = events_df[events_df["index"] == "NIFTY500"].sort_values(["effective_date", "row"])

    v1_res = evaluate_map(V1_MAP_PATH, events_df)
    v2_res = evaluate_map(CURRENT_MAP_PATH, events_df)

    print("\n--- 1. OVERALL STATUS COUNTS (BEFORE VS AFTER) ---")
    print(f"{'Status':<15} | {'Before (v1)':<15} | {'After (v2b)':<15}")
    print("-" * 50)
    for s in ["auto", "proposed", "unresolved"]:
        c1 = v1_res["status_counts"].get(s, 0)
        c2 = v2_res["status_counts"].get(s, 0)
        print(f"{s:<15} | {c1:<15} | {c2:<15}")

    print("\n--- 2. FLAG COUNTS IN REBUILT MAP (v2b) ---")
    for f, c in sorted(v2_res["flag_counts"].items(), key=lambda x: -x[1]):
        print(f"  {f:<35}: {c}")

    print("\n--- 3. PER-INDEX SUMMARY ---")
    for idx_name in PRIMARY_INDICES:
        print(f"\n==================== INDEX: {idx_name} ====================")
        idx_events = events_df[events_df["index"] == idx_name].sort_values(["effective_date", "row"])
        unique_scrips = idx_events["scrip_name"].unique()
        n_unique = len(unique_scrips)
        print(f"Total Unique Scrips: {n_unique} | Total Events: {len(idx_events)}")

        if idx_name != "NIFTY500":
            print("  Status: event log only, not reconstructable (lacks 1998-08-01 seed batch)")
            continue

        # NIFTY500 reconstruction
        for label, r_data in [("BEFORE REBUILD (v1)", v1_res), ("AFTER REBUILD (v2b)", v2_res)]:
            print(f"\n  >>> {label} <<<")
            scrip_status = r_data["status_map"]
            scrip_cov = r_data["cov_map"]
            scrip_sym = r_data["sym_map"]

            # Blocked events: unapproved/unresolved scrips block all events
            # Note: in Gate 2, only 'auto' and 'approved' are resolved. 'proposed' and 'unresolved' are blocked.
            blocked_scrips = {s for s in unique_scrips if scrip_status.get(s) not in ("auto", "approved")}
            blocked_in = len(idx_events[(idx_events["scrip_name"].isin(blocked_scrips)) & (idx_events["action"] == "IN")])
            blocked_out = len(idx_events[(idx_events["scrip_name"].isin(blocked_scrips)) & (idx_events["action"] == "OUT")])
            print(f"  Blocked Events: IN = {blocked_in}, OUT = {blocked_out}")

            # Replay membership
            covered_end_dt = idx_events["effective_date"].max()
            covered_end_str = covered_end_dt.strftime("%Y-%m-%d")
            dates_to_check = GATE_B_DATES + [covered_end_str]

            print(f"  Reconstructed Snapshot Fractions:")
            for snap_str in dates_to_check:
                snap_dt = pd.to_datetime(snap_str).date()
                sub = idx_events[idx_events["effective_date"] <= snap_dt]
                members = set()
                for _, er in sub.iterrows():
                    if er["action"] == "IN":
                        members.add(er["scrip_name"])
                    elif er["action"] == "OUT":
                        members.discard(er["scrip_name"])

                tot = len(members)
                if tot == 0:
                    print(f"    Snapshot {snap_str}: N/A (0 members)")
                    continue

                res_count = sum(1 for m in members if scrip_status.get(m) in ("auto", "approved"))
                res_frac = res_count / tot * 100.0

                cov_count = sum(1 for m in members if scrip_status.get(m) in ("auto", "approved") and scrip_cov.get(m, 0.0) >= 90.0)
                cov_frac = cov_count / tot * 100.0

                unres_or_lack_price = tot - cov_count

                print(f"    Snapshot {snap_str}:")
                print(f"      - Name-Level Resolved Fraction : {res_count:3d} / {tot:3d} ({res_frac:.1f}%)")
                print(f"      - Price-Covered Fraction (>=90%): {cov_count:3d} / {tot:3d} ({cov_frac:.1f}%)")
                print(f"      - Survivorship note: {unres_or_lack_price} of {tot} NIFTY500 members at {snap_str} are unresolved or lack price data.")

            # Monthly snapshots
            earliest_dt = idx_events["effective_date"].min()
            m_dates = pd.date_range(start=earliest_dt, end=covered_end_dt, freq="MS")
            name_fracs = []
            price_fracs = []
            below_80_name = []
            below_80_price = []

            for m_ts in m_dates:
                m_dt = m_ts.date()
                sub = idx_events[idx_events["effective_date"] <= m_dt]
                members = set()
                for _, er in sub.iterrows():
                    if er["action"] == "IN":
                        members.add(er["scrip_name"])
                    elif er["action"] == "OUT":
                        members.discard(er["scrip_name"])
                tot = len(members)
                if tot == 0:
                    continue

                res_count = sum(1 for m in members if scrip_status.get(m) in ("auto", "approved"))
                n_frac = res_count / tot
                name_fracs.append(n_frac)
                if n_frac < 0.80:
                    below_80_name.append((m_dt.strftime("%Y-%m-%d"), n_frac))

                cov_count = sum(1 for m in members if scrip_status.get(m) in ("auto", "approved") and scrip_cov.get(m, 0.0) >= 90.0)
                p_frac = cov_count / tot
                price_fracs.append(p_frac)
                if p_frac < 0.80:
                    below_80_price.append((m_dt.strftime("%Y-%m-%d"), p_frac))

            sn = pd.Series(name_fracs)
            sp = pd.Series(price_fracs)
            print(f"\n  Monthly Rebalance Snapshots (Total = {len(name_fracs)}):")
            print(f"    Name-Level Resolved : Min = {sn.min()*100:.1f}%, Median = {sn.median()*100:.1f}%, <80% = {len(below_80_name)}")
            print(f"    Price-Covered (>=90%): Min = {sp.min()*100:.1f}%, Median = {sp.median()*100:.1f}%, <80% = {len(below_80_price)}")

if __name__ == "__main__":
    main()
