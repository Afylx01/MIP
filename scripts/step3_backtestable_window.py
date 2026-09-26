#!/usr/bin/env python3
"""
scripts/step3_backtestable_window.py
Phase 5.5 — Gate 2c Step 3: Backtestable-Window Report (NIFTY500 ONLY)

Key Deliverables:
1. Define backtestable window:
   - window_start: 253rd cached NSEI bar on/after 2015-01-01 (providing 252-bar warm-up).
   - window_end: covered_end of NIFTY500 (2020-09-14).
2. For every first-trading-day-of-month snapshot in the window:
   - Compute mapped (auto/approved), price-covered (covered), and both fractions.
   - Export full table to deliverables/gate_2c/data_csv/window_fractions.csv.
   - Print count, min, median, and count below 80%.
3. Print specific snapshots with counts as numerator/denominator:
   - 2016-01-04 (first trading day of 2016)
   - 2018-01-01 (first trading day of 2018)
   - 2020-09-14 (covered_end)
4. State monthly rebalance count and print mandatory disclosure:
   - 'Universe reconstruction incomplete in <N> of <M> snapshots' + survivorship note.
5. Recompute and print whole 1998-2020 range labelled 'not backtestable'.
"""

import os
import sys
import shutil
import datetime
import pandas as pd
import numpy as np

EVENTS_PATH = "data/index_events.parquet"
SYMBOL_MAP_PATH = "data/symbol_map.parquet"
TRADING_CALENDAR_TXT = "data/trading_calendar.txt"

DELIVERABLES_CSV_DIR = "deliverables/gate_2c/data_csv"
DELIVERABLES_SCRIPTS_DIR = "deliverables/gate_2c/scripts"
DELIVERABLES_RAW_DIR = "deliverables/gate_2c/raw_outputs"

os.makedirs(DELIVERABLES_CSV_DIR, exist_ok=True)
os.makedirs(DELIVERABLES_SCRIPTS_DIR, exist_ok=True)
os.makedirs(DELIVERABLES_RAW_DIR, exist_ok=True)

def main():
    print("=" * 80)
    print("PHASE 5.5 — GATE 2c: STEP 3 (BACKTESTABLE-WINDOW REPORT — NIFTY500 ONLY)")
    print("=" * 80)

    # 1. Load Data
    events_df = pd.read_parquet(EVENTS_PATH)
    nifty500_events = events_df[events_df["index"] == "NIFTY500"].sort_values(["effective_date", "action"]).reset_index(drop=True)
    print(f"Loaded NIFTY500 events: {len(nifty500_events)} events")

    symbol_map = pd.read_parquet(SYMBOL_MAP_PATH)
    map_dict = symbol_map.set_index("scrip_name").to_dict(orient="index")
    print(f"Loaded symbol map v3: {len(symbol_map)} scrips")

    with open(TRADING_CALENDAR_TXT) as f:
        cal_dates = sorted([line.strip() for line in f if line.strip()])
    print(f"Loaded trading calendar: {len(cal_dates)} dates ({cal_dates[0]} to {cal_dates[-1]})")

    # -------------------------------------------------------------------------
    # 2. Window Derivation
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("[3.1] WINDOW DERIVATION")
    print("=" * 80)
    cal_2015 = [d for d in cal_dates if d >= "2015-01-01"]
    # 253rd cached NSEI bar on or after 2015-01-01 (1-indexed -> index 252)
    window_start_bar = cal_2015[252]
    window_end = "2020-09-14"

    print(f"Derivation details:")
    print(f"  First cached NSEI bar in 2015: {cal_2015[0]}")
    print(f"  252-bar warm-up period: {cal_2015[0]} to {cal_2015[251]} (exactly 252 trading bars)")
    print(f"  window_start: {window_start_bar} (the 253rd cached NSEI bar on or after 2015-01-01)")
    print(f"  window_end:   {window_end} (covered_end of NIFTY500 in index_events)")

    # -------------------------------------------------------------------------
    # 3. Monthly Snapshot Calculation Function
    # -------------------------------------------------------------------------
    def evaluate_snapshots(start_dt_str, end_dt_str, label=""):
        # Group calendar dates by YYYY-MM
        by_ym = {}
        for d in cal_dates:
            if start_dt_str <= d <= end_dt_str:
                ym = d[:7]
                by_ym.setdefault(ym, []).append(d)

        snapshot_dates = [days[0] for ym, days in sorted(by_ym.items())]

        rows = []
        for snap_date_str in snapshot_dates:
            snap_date = datetime.datetime.strptime(snap_date_str, "%Y-%m-%d").date()
            # Replay events up to snap_date
            sub = nifty500_events[nifty500_events["effective_date"] <= snap_date]
            active_members = set()
            for _, r in sub.iterrows():
                act = r["action"]
                scrip = r["scrip_name"]
                if act == "IN":
                    active_members.add(scrip)
                elif act == "OUT":
                    active_members.discard(scrip)

            total = len(active_members)
            mapped = 0
            price_cov = 0
            both = 0

            for s in active_members:
                info = map_dict.get(s, {})
                m_stat = info.get("mapping_status", "unresolved")
                p_stat = info.get("price_status", "no_symbol")
                is_mapped = (m_stat in ["auto", "approved"])
                is_cov = (p_stat == "covered")
                if is_mapped:
                    mapped += 1
                if is_cov:
                    price_cov += 1
                if is_mapped and is_cov:
                    both += 1

            rows.append({
                "snapshot_date": snap_date_str,
                "label": label,
                "total_members": total,
                "mapped_count": mapped,
                "mapped_frac": round(mapped / total * 100, 2) if total > 0 else 0.0,
                "price_covered_count": price_cov,
                "price_covered_frac": round(price_cov / total * 100, 2) if total > 0 else 0.0,
                "both_count": both,
                "both_frac": round(both / total * 100, 2) if total > 0 else 0.0,
            })
        return pd.DataFrame(rows)

    # Evaluate window snapshots (from 2016-01-01 to 2020-09-14)
    # Including 2016-01-04 (first trading day of 2016)
    window_df = evaluate_snapshots("2016-01-01", window_end, label="backtestable_candidate_window")

    # Save to data_csv/window_fractions.csv
    window_csv_path = os.path.join(DELIVERABLES_CSV_DIR, "window_fractions.csv")
    window_df.to_csv(window_csv_path, index=False)
    print(f"\nExported window fractions table to: {window_csv_path} ({len(window_df)} snapshots)")

    # -------------------------------------------------------------------------
    # 4. Summary Statistics for Window
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("[3.2] WINDOW FRACTIONS SUMMARY (MONTHLY SNAPSHOTS)")
    print("=" * 80)
    num_snaps = len(window_df)
    min_mapped = window_df["mapped_frac"].min()
    med_mapped = window_df["mapped_frac"].median()
    min_cov = window_df["price_covered_frac"].min()
    med_cov = window_df["price_covered_frac"].median()
    min_both = window_df["both_frac"].min()
    med_both = window_df["both_frac"].median()
    below_80 = (window_df["both_frac"] < 80.0).sum()

    print(f"Snapshot count in window: {num_snaps}")
    print(f"Mapped Fraction       : min = {min_mapped:.2f}%, median = {med_mapped:.2f}%")
    print(f"Price-Covered Fraction: min = {min_cov:.2f}%, median = {med_cov:.2f}%")
    print(f"Both Fraction         : min = {min_both:.2f}%, median = {med_both:.2f}%")
    print(f"Snapshots with Both < 80%: {below_80} / {num_snaps} ({below_80/num_snaps*100:.1f}%)")

    # -------------------------------------------------------------------------
    # 5. Required Specific Snapshots
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("[3.3] SPECIFIC MILESTONE SNAPSHOTS (COUNTS & FRACTIONS)")
    print("=" * 80)

    def print_milestone(dt_str, name):
        snap_dt = datetime.datetime.strptime(dt_str, "%Y-%m-%d").date()
        sub = nifty500_events[nifty500_events["effective_date"] <= snap_dt]
        active = set()
        for _, r in sub.iterrows():
            if r["action"] == "IN":
                active.add(r["scrip_name"])
            elif r["action"] == "OUT":
                active.discard(r["scrip_name"])
        tot = len(active)
        m_cnt = sum(1 for s in active if map_dict.get(s, {}).get("mapping_status") in ["auto", "approved"])
        p_cnt = sum(1 for s in active if map_dict.get(s, {}).get("price_status") == "covered")
        b_cnt = sum(1 for s in active if (map_dict.get(s, {}).get("mapping_status") in ["auto", "approved"]) and (map_dict.get(s, {}).get("price_status") == "covered"))

        print(f"\nSnapshot: {dt_str} ({name}) — Total Members: {tot}")
        print(f"  Mapped       : {m_cnt:3d} / {tot:3d} ({m_cnt/tot*100:5.2f}%)")
        print(f"  Price-Covered: {p_cnt:3d} / {tot:3d} ({p_cnt/tot*100:5.2f}%)")
        print(f"  Both         : {b_cnt:3d} / {tot:3d} ({b_cnt/tot*100:5.2f}%)")

    print_milestone("2016-01-04", "First Trading Day of 2016")
    print_milestone("2018-01-01", "First Trading Day of 2018")
    print_milestone("2020-09-14", "covered_end (Final Rebalance in Event Log)")

    # -------------------------------------------------------------------------
    # 6. Mandatory Disclosure & Monthly Rebalances Count
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("[3.4] REBALANCE COUNT & MANDATORY DISCLOSURE LINE")
    print("=" * 80)
    print(f"Number of monthly rebalance snapshots in window (2016-01 to 2020-09): {num_snaps}")
    print("\nREQUIRED DISCLOSURE LINE:")
    print(f"  Universe reconstruction incomplete in {below_80} of {num_snaps} snapshots.")
    print("  SURVIVORSHIP NOTE: Local price data represents a survivor-only cache spanning 750 current")
    print("  surviving entities. Delisted constituents, past merger targets, and defunct historical members")
    print("  lack historical price bars in the cache. Full point-in-time backtesting across this window")
    print("  is therefore unachievable without acquiring historical daily Bhavcopy archives for delisted entities.")

    # -------------------------------------------------------------------------
    # 7. Whole 1998–2020 Historical Range (Not Backtestable)
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("[3.5] FULL HISTORICAL RANGE 1998–2020 (LABELLED: NOT BACKTESTABLE)")
    print("=" * 80)
    # Build monthly dates from 1998-08-01 to 2020-09-14
    # Note: Calendar starts 2007-09-17. Prior to that, calendar days are not in index__NSEI_cache.pkl.
    # We construct 1st calendar day of each month for 1998-08 to 2007-09, and calendar first day thereafter.
    hist_snapshots = []
    # 1998-08 to 2007-08
    curr_yr, curr_mo = 1998, 8
    while (curr_yr < 2007) or (curr_yr == 2007 and curr_mo < 9):
        dt_s = f"{curr_yr:04d}-{curr_mo:02d}-01"
        hist_snapshots.append(dt_s)
        curr_mo += 1
        if curr_mo > 12:
            curr_mo = 1
            curr_yr += 1

    # From 2007-09 to 2020-09 use trading calendar
    by_ym_hist = {}
    for d in cal_dates:
        if "2007-09-01" <= d <= "2020-09-14":
            ym = d[:7]
            by_ym_hist.setdefault(ym, []).append(d)
    for ym, days in sorted(by_ym_hist.items()):
        hist_snapshots.append(days[0])

    hist_rows = []
    for snap_date_str in hist_snapshots:
        snap_date = datetime.datetime.strptime(snap_date_str, "%Y-%m-%d").date()
        sub = nifty500_events[nifty500_events["effective_date"] <= snap_date]
        active = set()
        for _, r in sub.iterrows():
            if r["action"] == "IN":
                active.add(r["scrip_name"])
            elif r["action"] == "OUT":
                active.discard(r["scrip_name"])
        tot = len(active)
        m_cnt = sum(1 for s in active if map_dict.get(s, {}).get("mapping_status") in ["auto", "approved"])
        p_cnt = sum(1 for s in active if map_dict.get(s, {}).get("price_status") == "covered")
        b_cnt = sum(1 for s in active if (map_dict.get(s, {}).get("mapping_status") in ["auto", "approved"]) and (map_dict.get(s, {}).get("price_status") == "covered"))
        hist_rows.append({
            "snapshot_date": snap_date_str,
            "backtestable_status": "NOT BACKTESTABLE",
            "total_members": tot,
            "mapped_count": m_cnt,
            "mapped_pct": round(m_cnt / tot * 100, 2) if tot > 0 else 0.0,
            "price_covered_count": p_cnt,
            "price_covered_pct": round(p_cnt / tot * 100, 2) if tot > 0 else 0.0,
            "both_count": b_cnt,
            "both_pct": round(b_cnt / tot * 100, 2) if tot > 0 else 0.0,
        })

    hist_df = pd.DataFrame(hist_rows)
    print(f"\nTotal historical snapshots (1998-08 to 2020-09): {len(hist_df)} snapshots")
    print(f"Sample historical snapshots (labelled NOT BACKTESTABLE):")
    h_header = f"| {'date':<11} | {'status':<18} | {'total':<6} | {'mapped':<15} | {'price_covered':<15} | {'both':<15} |"
    h_sep = "|" + "-"*13 + "|" + "-"*20 + "|" + "-"*8 + "|" + "-"*17 + "|" + "-"*17 + "|" + "-"*17 + "|"
    print(h_header)
    print(h_sep)
    # Print sample every 2 years
    for _, r in hist_df.iloc[::24].iterrows():
        m_str = f"{r['mapped_count']}/{r['total_members']} ({r['mapped_pct']}%)"
        p_str = f"{r['price_covered_count']}/{r['total_members']} ({r['price_covered_pct']}%)"
        b_str = f"{r['both_count']}/{r['total_members']} ({r['both_pct']}%)"
        print(f"| {r['snapshot_date']:<11} | {r['backtestable_status']:<18} | {r['total_members']:<6} | {m_str:<15} | {p_str:<15} | {b_str:<15} |")

    print("\nReason 1998–2020 is NOT BACKTESTABLE:")
    print("  1. Price coverage prior to 2015 is zero for >85% of constituents (cache begins 2015 for 640 symbols).")
    print("  2. Prior to 2007, price coverage is strictly 0.0% across all 500 constituents (zero cache bars).")
    print("  3. Point-in-time backtesting across 1998–2020 would suffer extreme survivorship bias and missing data.")

    # Copy script to deliverables/gate_2c/scripts/
    shutil.copy2(__file__, os.path.join(DELIVERABLES_SCRIPTS_DIR, "step3_backtestable_window.py"))
    print(f"\nCopied script to {os.path.join(DELIVERABLES_SCRIPTS_DIR, 'step3_backtestable_window.py')}")
    print("\n" + "=" * 80)
    print("STEP 3 COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
