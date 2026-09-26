#!/usr/bin/env python3
"""
deliverables/halt1b_m1/scripts/gate0_triage.py
Phase 5.5.M-1 — Gate 0: NIFTY500 Pending Scrip Triage & Impact Ranking

1. Replays NIFTY500 index events across all 57 monthly snapshots.
2. Identifies all 734 unique constituent scrips and computes their snapshot frequency.
3. Cross-references against data/symbol_map.parquet to isolate the 299 unapproved scrips.
4. Categorizes unapproved scrips across review tiers (high, medium, unresolved, low).
5. Ranks pending scrips by occurrence frequency and exports:
   - deliverables/halt1b_m1/data_csv/nifty500_pending_scrips_ranked.csv
   - deliverables/halt1b_m1/raw/gate0_triage.txt
"""

import sys
import datetime
import pandas as pd
from pathlib import Path

BASE_DIR = Path("/sdcard/Documents/Project MIP")
DELIV_DIR = BASE_DIR / "deliverables/halt1b_m1"
DATA_CSV_DIR = DELIV_DIR / "data_csv"
RAW_DIR = DELIV_DIR / "raw"

EVENTS_PATH = BASE_DIR / "data/index_events.parquet"
SYMBOL_MAP_PATH = BASE_DIR / "data/symbol_map.parquet"
SNAPSHOTS_CSV = BASE_DIR / "deliverables/halt1b_p_a3/data_csv/monthly_coverage_comparison.csv"
REVIEW_HIGH_CSV = BASE_DIR / "data/symbol_map_review_high.csv"
REVIEW_MED_CSV = BASE_DIR / "data/symbol_map_review_medium.csv"
REVIEW_UNRES_CSV = BASE_DIR / "data/symbol_map_unresolved.csv"
REVIEW_LOW_CSV = BASE_DIR / "data/symbol_map_review_low.csv"
EQUITY_L_CSV = BASE_DIR / "data/raw_reference/EQUITY_L.csv"

def main():
    print("=" * 80)
    print("PHASE 5.5.M-1 — GATE 0: NIFTY500 PENDING SCRIP TRIAGE & IMPACT RANKING")
    print(f"Timestamp: {datetime.datetime.now(datetime.timezone.utc).isoformat()}")
    print("=" * 80)

    # 1. Load Snapshots & Index Events
    print("\n--- 1. Loading Snapshots & Index Events ---")
    snap_df = pd.read_csv(SNAPSHOTS_CSV)
    snapshot_dates = snap_df["snapshot_date"].tolist()
    print(f"Loaded {len(snapshot_dates)} monthly snapshots ({snapshot_dates[0]} to {snapshot_dates[-1]}).")

    events_df = pd.read_parquet(EVENTS_PATH)
    nifty500_events = events_df[events_df["index"] == "NIFTY500"].sort_values(["effective_date", "action"]).reset_index(drop=True)
    print(f"Loaded NIFTY500 index events: {len(nifty500_events):,} events.")

    # Convert events to lightweight tuples for blazing-fast replay
    event_records = [
        (r.effective_date, r.action, r.scrip_name)
        for r in nifty500_events.itertuples(index=False)
    ]

    # 2. Replay Snapshots to Precompute Active Set & Scrip Frequency
    print("\n--- 2. Replaying Snapshots & Computing Scrip Frequency ---")
    snapshot_active_sets = {}
    scrip_counts = {}

    for snap_date_str in snapshot_dates:
        snap_date = datetime.datetime.strptime(snap_date_str, "%Y-%m-%d").date()
        active = set()
        for eff_dt, action, scrip in event_records:
            if eff_dt <= snap_date:
                if action == "IN":
                    active.add(scrip)
                elif action == "OUT":
                    active.discard(scrip)
            else:
                break
        snapshot_active_sets[snap_date_str] = active
        for s in active:
            scrip_counts[s] = scrip_counts.get(s, 0) + 1

    total_universe_scrips = len(scrip_counts)
    print(f"Total unique constituent scrips in 57 snapshots: {total_universe_scrips}")

    # 3. Load Symbol Map & Review Tiers
    print("\n--- 3. Cross-Referencing with Symbol Map & Review Tiers ---")
    smap = pd.read_parquet(SYMBOL_MAP_PATH)
    smap_dict = smap.set_index("scrip_name").to_dict(orient="index")

    # Load review tiers for lookup
    high_scrips = set(pd.read_csv(REVIEW_HIGH_CSV)["scrip_name"]) if REVIEW_HIGH_CSV.exists() else set()
    med_scrips = set(pd.read_csv(REVIEW_MED_CSV)["scrip_name"]) if REVIEW_MED_CSV.exists() else set()
    unres_scrips = set(pd.read_csv(REVIEW_UNRES_CSV)["scrip_name"]) if REVIEW_UNRES_CSV.exists() else set()
    low_scrips = set(pd.read_csv(REVIEW_LOW_CSV)["scrip_name"]) if REVIEW_LOW_CSV.exists() else set()

    mapped_scrips = []
    pending_scrips = []

    for scrip, freq in sorted(scrip_counts.items(), key=lambda x: -x[1]):
        info = smap_dict.get(scrip, {})
        m_stat = info.get("mapping_status", "unresolved")
        sym = info.get("symbol", "").strip()
        isin = info.get("isin", "").strip()
        flags = info.get("flags", "")
        conf = info.get("confidence", "unresolved")

        # Determine review source tier
        source_tier = "unknown"
        if scrip in high_scrips:
            source_tier = "review_high"
        elif scrip in med_scrips:
            source_tier = "review_medium"
        elif scrip in unres_scrips:
            source_tier = "unresolved"
        elif scrip in low_scrips:
            source_tier = "review_low"

        row = {
            "scrip_name": scrip,
            "snapshot_frequency": freq,
            "pct_snapshots": round(freq / len(snapshot_dates) * 100.0, 2),
            "mapping_status": m_stat,
            "symbol": sym,
            "isin": isin,
            "confidence": conf,
            "flags": flags,
            "source_tier": source_tier
        }

        if m_stat in ["auto", "approved"]:
            mapped_scrips.append(row)
        else:
            pending_scrips.append(row)

    print(f"Constituent breakdown:")
    print(f"  Currently Mapped (auto/approved):     {len(mapped_scrips)} ({len(mapped_scrips)/total_universe_scrips:.1%})")
    print(f"  Pending Review (proposed/unresolved): {len(pending_scrips)} ({len(pending_scrips)/total_universe_scrips:.1%})")
    assert len(pending_scrips) == 299, f"Expected exactly 299 pending scrips, got {len(pending_scrips)}"

    # 4. Analyze Pending Review Tiers
    pending_df = pd.DataFrame(pending_scrips)
    tier_counts = pending_df["source_tier"].value_counts()
    print("\nPending Scrips by Source Tier:")
    for t, cnt in tier_counts.items():
        print(f"  {t:<20}: {cnt:3d} scrips ({(cnt/len(pending_df))*100:.1f}%)")

    # 5. Export Ranked CSV
    out_csv = DATA_CSV_DIR / "nifty500_pending_scrips_ranked.csv"
    pending_df.to_csv(out_csv, index=False)
    print(f"\nExported ranked pending scrips table: {out_csv} ({len(pending_df)} rows, {out_csv.stat().st_size:,} bytes)")

    # 6. Cumulative Coverage Potential Analysis
    print("\n--- 4. Potential Coverage Analysis by Tier ---")
    g0_audit = pd.read_csv(BASE_DIR / "deliverables/halt1b_p_a3/data_csv/snapshot_prerequisite_audit.csv")
    current_mapped_median = g0_audit["mapped_pct"].median()
    print(f"Current Base Mapped Fraction Median: {current_mapped_median:.2f}%")

    high_in_pending = set(pending_df[pending_df["source_tier"] == "review_high"]["scrip_name"])
    med_in_pending = set(pending_df[pending_df["source_tier"] == "review_medium"]["scrip_name"])
    unres_in_pending = set(pending_df[pending_df["source_tier"] == "unresolved"]["scrip_name"])
    low_in_pending = set(pending_df[pending_df["source_tier"] == "review_low"]["scrip_name"])

    for label, included_tiers in [
        ("Base Only", set()),
        ("+ Review High (84 scrips)", high_in_pending),
        ("+ Review High + Medium (156 scrips)", high_in_pending | med_in_pending),
        ("+ All Pending (High + Med + Unres + Low) (299 scrips)", set(pending_df["scrip_name"]))
    ]:
        sim_fracs = []
        for snap_date_str, active in snapshot_active_sets.items():
            mapped_count = sum(1 for s in active if (smap_dict.get(s, {}).get("mapping_status") in ["auto", "approved"]) or (s in included_tiers))
            sim_fracs.append(mapped_count / len(active) * 100.0)
        sim_s = pd.Series(sim_fracs)
        print(f"  Simulation [{label:<45}]: Median Mapped = {sim_s.median():.2f}% (min: {sim_s.min():.2f}%, max: {sim_s.max():.2f}%)")

    print("\n" + "=" * 80)
    print("GATE 0 EXIT: PENDING SCRIPS TRIAGED — 299 SCRIPS ISOLATED AND RANKED")
    print("=" * 80)

if __name__ == "__main__":
    main()
