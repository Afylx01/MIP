#!/usr/bin/env python3
"""
deliverables/halt1b_p_a3/scripts/gate3_coverage.py
Phase 5.5.A-3 — Gate 3: Joint Coverage Re-Measurement

Recomputes joint universe coverage across all 57 monthly snapshots (2016-01-04 to 2020-09-01):
  Joint Coverage = |Mapped ∩ Price-Covered ∩ Not-Flagged| / |Snapshot Constituents|

Compares reconstructed Phase A-3 coverage against Gate 2c baseline (median 24.56%).
Evaluates median against §1 thresholds (PASS >= 85.0%, INDICATIVE 60.0-84.9%, REJECT < 60.0%).
Exports comparison table to deliverables/halt1b_p_a3/data_csv/monthly_coverage_comparison.csv.
Logs output to deliverables/halt1b_p_a3/raw/gate3_coverage.txt.
"""

import sys
import datetime
import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR = Path("/sdcard/Documents/Project MIP")
DELIVERABLES_DIR = BASE_DIR / "deliverables/halt1b_p_a3"
RAW_DIR = DELIVERABLES_DIR / "raw"
DATA_CSV_DIR = DELIVERABLES_DIR / "data_csv"
VERIF_DATA_DIR = BASE_DIR / "data/verification/halt1b_p_a3"

EVENTS_PATH = BASE_DIR / "data/index_events.parquet"
SYMBOL_MAP_PATH = BASE_DIR / "data/symbol_map.parquet"
ADJ_BARS_PATH = VERIF_DATA_DIR / "adjusted_bhavcopy_bars.parquet"
GATE2C_WINDOW_CSV = BASE_DIR / "deliverables/gate_2c/data_csv/window_fractions.csv"

def is_scrip_unflagged(info: dict, snap_date: datetime.date) -> bool:
    flags_str = info.get("flags", "") or ""
    if not flags_str:
        return True
        
    flag_tokens = [t.strip() for t in flags_str.split(";") if t.strip()]
    for token in flag_tokens:
        # S1: listing_after_first_seen
        if token == "listing_after_first_seen":
            # Active only if snap_date < eq_listing_date
            listing_str = str(info.get("eq_listing_date", "")).strip()
            if listing_str and listing_str != "nan":
                try:
                    listing_dt = pd.to_datetime(listing_str).date()
                    if snap_date < listing_dt:
                        return False
                except Exception:
                    return False
            else:
                return False
        # S2: duplicate_name_collision
        elif "duplicate_name_collision" in token:
            return False
        # S3: unsourced
        elif "unsourced" in token:
            return False
        # S4: concurrent_alias_collision
        elif "concurrent_alias_collision" in token:
            return False
        # S5: predecessor_marker
        elif "predecessor_marker" in token:
            return False
        # S6: first_token_mismatch or name_mismatch
        elif "first_token_mismatch" in token or "name_mismatch" in token:
            return False
            
    return True

def main():
    print("=" * 80)
    print("PHASE 5.5.A-3 — GATE 3: JOINT COVERAGE RE-MEASUREMENT")
    print(f"Timestamp: {datetime.datetime.now(datetime.timezone.utc).isoformat()}")
    print("=" * 80)

    # 1. Load Datasets
    print("\n--- 1. Loading Datasets ---")
    events_df = pd.read_parquet(EVENTS_PATH)
    nifty500_events = events_df[events_df["index"] == "NIFTY500"].sort_values(["effective_date", "action"]).reset_index(drop=True)
    print(f"Loaded index events: {len(nifty500_events):,} events")

    smap = pd.read_parquet(SYMBOL_MAP_PATH)
    map_dict = smap.set_index("scrip_name").to_dict(orient="index")
    print(f"Loaded symbol map: {len(smap):,} scrips")

    assert ADJ_BARS_PATH.exists(), f"Missing adjusted bars file: {ADJ_BARS_PATH}"
    adj_bars = pd.read_parquet(ADJ_BARS_PATH)
    print(f"Loaded adjusted bars: {len(adj_bars):,} bars across {adj_bars['symbol'].nunique()} symbols and {adj_bars['date'].nunique()} dates.")

    # Create quick price lookup set: (symbol, date)
    valid_bars = adj_bars[(adj_bars["close"] > 0) & (~adj_bars["close"].isna())]
    price_lookup = set(zip(valid_bars["symbol"], valid_bars["date"]))
    print(f"Constructed price lookup table: {len(price_lookup):,} valid (symbol, date) entries.")

    assert GATE2C_WINDOW_CSV.exists(), f"Missing Gate 2c baseline: {GATE2C_WINDOW_CSV}"
    g2c_df = pd.read_csv(GATE2C_WINDOW_CSV)
    print(f"Loaded Gate 2c baseline table: {len(g2c_df)} snapshots.")

    snapshot_dates = g2c_df["snapshot_date"].tolist()
    assert len(snapshot_dates) == 57, f"Expected 57 snapshots, got {len(snapshot_dates)}"

    # 2. Re-Measure Joint Coverage on All 57 Snapshots
    print("\n--- 2. Re-Measuring Coverage across 57 Monthly Snapshots ---")
    rows = []

    for idx, snap_date_str in enumerate(snapshot_dates):
        snap_date = datetime.datetime.strptime(snap_date_str, "%Y-%m-%d").date()
        sub = nifty500_events[nifty500_events["effective_date"] <= snap_date]
        active = set()
        for _, r in sub.iterrows():
            if r["action"] == "IN":
                active.add(r["scrip_name"])
            elif r["action"] == "OUT":
                active.discard(r["scrip_name"])

        tot = len(active)
        mapped = 0
        price_cov = 0
        unflagged = 0
        joint_cov = 0

        for scrip in active:
            info = map_dict.get(scrip, {})
            m_stat = info.get("mapping_status", "unresolved")
            sym = info.get("symbol", "").strip()

            is_m = (m_stat in ["auto", "approved"] and len(sym) > 0)
            is_p = is_m and ((sym, snap_date_str) in price_lookup)
            is_u = is_m and is_scrip_unflagged(info, snap_date)
            is_j = is_m and is_p and is_u

            if is_m:
                mapped += 1
            if is_p:
                price_cov += 1
            if is_u:
                unflagged += 1
            if is_j:
                joint_cov += 1

        # Baseline Gate 2c row
        g2c_row = g2c_df.iloc[idx]
        g2c_both_count = int(g2c_row["both_count"])
        g2c_both_frac = float(g2c_row["both_frac"])

        a3_joint_frac = round(joint_cov / tot * 100.0, 2) if tot > 0 else 0.0
        delta_pct = round(a3_joint_frac - g2c_both_frac, 2)

        rows.append({
            "snapshot_idx": idx + 1,
            "snapshot_date": snap_date_str,
            "total_constituents": tot,
            "g2c_both_count": g2c_both_count,
            "g2c_both_frac": g2c_both_frac,
            "a3_mapped_count": mapped,
            "a3_mapped_frac": round(mapped / tot * 100.0, 2) if tot else 0.0,
            "a3_price_covered_count": price_cov,
            "a3_price_covered_frac": round(price_cov / tot * 100.0, 2) if tot else 0.0,
            "a3_unflagged_count": unflagged,
            "a3_joint_count": joint_cov,
            "a3_joint_frac": a3_joint_frac,
            "delta_pct": delta_pct
        })

    comp_df = pd.DataFrame(rows)

    # 3. Export Comparison Table
    out_csv = DATA_CSV_DIR / "monthly_coverage_comparison.csv"
    comp_df.to_csv(out_csv, index=False)
    print(f"Exported monthly coverage comparison table: {out_csv} ({len(comp_df)} rows, {out_csv.stat().st_size:,} bytes)")

    # 4. Summary Statistics & Acceptance Evaluation
    print("\n" + "=" * 80)
    print("PHASE 5.5.A-3 SUMMARY STATISTICS & THRESHOLD EVALUATION")
    print("=" * 80)
    g2c_med = comp_df["g2c_both_frac"].median()
    a3_mapped_med = comp_df["a3_mapped_frac"].median()
    a3_price_med = comp_df["a3_price_covered_frac"].median()
    a3_joint_med = comp_df["a3_joint_frac"].median()
    a3_joint_min = comp_df["a3_joint_frac"].min()
    a3_joint_max = comp_df["a3_joint_frac"].max()

    print(f"Snapshots Analyzed:            {len(comp_df)}")
    print(f"Gate 2c Baseline Median Both:  {g2c_med:.2f}%")
    print(f"Phase A-3 Reconstructed:")
    print(f"  Mapped Fraction Median:      {a3_mapped_med:.2f}% (min: {comp_df['a3_mapped_frac'].min():.2f}%, max: {comp_df['a3_mapped_frac'].max():.2f}%)")
    print(f"  Price-Covered Median:        {a3_price_med:.2f}% (min: {comp_df['a3_price_covered_frac'].min():.2f}%, max: {comp_df['a3_price_covered_frac'].max():.2f}%)")
    print(f"  Joint Coverage Median:       {a3_joint_med:.2f}%")
    print(f"  Joint Coverage Min:          {a3_joint_min:.2f}% (Snapshot {comp_df.loc[comp_df['a3_joint_frac'].idxmin(), 'snapshot_date']})")
    print(f"  Joint Coverage Max:          {a3_joint_max:.2f}% (Snapshot {comp_df.loc[comp_df['a3_joint_frac'].idxmax(), 'snapshot_date']})")
    print(f"  Median Coverage Delta:       +{a3_joint_med - g2c_med:.2f} percentage points")

    # Threshold Check
    print("\nAcceptance Evaluation against §1 Thresholds:")
    print("  PASS:       Median Joint Coverage >= 85.0%")
    print("  INDICATIVE: Median Joint Coverage 60.0% - 84.9%")
    print("  REJECT:     Median Joint Coverage < 60.0%")

    if a3_joint_med >= 85.0:
        ruling = "PASS"
        note = "Survivorship bias successfully eliminated; median coverage exceeds 85.0% threshold."
    elif a3_joint_med >= 60.0:
        ruling = "INDICATIVE"
        note = "Survivorship bias substantially mitigated; median coverage between 60.0% and 84.9% (indicative determination per Q5=(b))."
    else:
        ruling = "REJECT"
        note = "Median coverage below 60.0% threshold."

    print(f"\nRULING: {ruling}")
    print(f"Note:   {note}")

    # Specific Milestone Snapshots
    print("\nMilestone Snapshots Comparison:")
    milestones = ["2016-01-04", "2018-01-01", "2020-09-01"]
    for m in milestones:
        sub_row = comp_df[comp_df["snapshot_date"] == m]
        if not sub_row.empty:
            r = sub_row.iloc[0]
            print(f"  Snapshot {m}:")
            print(f"    Constituents:       {r['total_constituents']}")
            print(f"    Gate 2c Baseline:   {r['g2c_both_count']}/{r['total_constituents']} ({r['g2c_both_frac']}%)")
            print(f"    Phase A-3 Joint:    {r['a3_joint_count']}/{r['total_constituents']} ({r['a3_joint_frac']}%)")
            print(f"    Improvement:        +{r['delta_pct']} percentage points")

    print("\n" + "=" * 80)
    print(f"GATE 3 EXIT: COVERAGE RE-MEASUREMENT COMPLETE — RULING: {ruling} (MEDIAN: {a3_joint_med:.2f}%)")
    print("=" * 80)

if __name__ == "__main__":
    main()
