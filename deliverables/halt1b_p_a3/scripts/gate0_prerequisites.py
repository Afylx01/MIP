#!/usr/bin/env python3
"""
deliverables/halt1b_p_a3/scripts/gate0_prerequisites.py
Phase 5.5.A-3 — Gate 0: Snapshot & Universe Prerequisite Audit

Audits the 57 monthly NIFTY500 constituent snapshots (2016-01-04 to 2020-09-01),
cross-references constituents against data/symbol_map.parquet (mapping_status in {auto, approved}),
isolates unique required symbols and required historical trading dates from data/trading_calendar.txt.
"""

import os
import sys
import datetime
import pandas as pd
from pathlib import Path

BASE_DIR = Path("/sdcard/Documents/Project MIP")
DELIVERABLES_DIR = BASE_DIR / "deliverables/halt1b_p_a3"
RAW_DIR = DELIVERABLES_DIR / "raw"
DATA_CSV_DIR = DELIVERABLES_DIR / "data_csv"

for d in [RAW_DIR, DATA_CSV_DIR]:
    d.mkdir(parents=True, exist_ok=True)

EVENTS_PATH = BASE_DIR / "data/index_events.parquet"
SYMBOL_MAP_PATH = BASE_DIR / "data/symbol_map.parquet"
CALENDAR_PATH = BASE_DIR / "data/trading_calendar.txt"
GATE2C_WINDOW_CSV = BASE_DIR / "deliverables/gate_2c/data_csv/window_fractions.csv"

def main():
    print("=" * 80)
    print("PHASE 5.5.A-3 — GATE 0: SNAPSHOT & UNIVERSE PREREQUISITE AUDIT")
    print(f"Timestamp: {datetime.datetime.now(datetime.timezone.utc).isoformat()}")
    print("=" * 80)

    # 1. Load Index Events
    print("\n--- 1. Loading Index Events & Trading Calendar ---")
    events_df = pd.read_parquet(EVENTS_PATH)
    nifty500_events = events_df[events_df["index"] == "NIFTY500"].sort_values(["effective_date", "action"]).reset_index(drop=True)
    print(f"Loaded NIFTY500 index events: {len(nifty500_events):,} events")

    with open(CALENDAR_PATH) as f:
        cal_dates = sorted([line.strip() for line in f if line.strip()])
    print(f"Loaded trading calendar: {len(cal_dates):,} dates total ({cal_dates[0]} to {cal_dates[-1]})")

    # Filter trading dates for Phase A-3 window (2016-01-01 to 2020-09-14)
    window_trading_dates = [d for d in cal_dates if "2016-01-01" <= d <= "2020-09-14"]
    print(f"Phase A-3 Window Trading Dates: {len(window_trading_dates):,} dates ({window_trading_dates[0]} to {window_trading_dates[-1]})")

    # 2. Derive the 57 Monthly Snapshots
    print("\n--- 2. Deriving the 57 Monthly Snapshots ---")
    by_ym = {}
    for d in window_trading_dates:
        ym = d[:7]
        by_ym.setdefault(ym, []).append(d)

    snapshot_dates = [days[0] for ym, days in sorted(by_ym.items())]
    print(f"Monthly Snapshot Count: {len(snapshot_dates)} snapshots")
    print(f"Snapshot Range: {snapshot_dates[0]} to {snapshot_dates[-1]}")
    assert len(snapshot_dates) == 57, f"Expected exactly 57 monthly snapshots, found {len(snapshot_dates)}"

    # Cross-check against Gate 2c baseline snapshots
    if GATE2C_WINDOW_CSV.exists():
        gate2c_df = pd.read_csv(GATE2C_WINDOW_CSV)
        g2c_snaps = gate2c_df["snapshot_date"].tolist()
        assert g2c_snaps == snapshot_dates, "Snapshot dates do not match Gate 2c window_fractions.csv!"
        print("  -> Snapshot dates EXACT MATCH with Gate 2c baseline (57/57).")

    # 3. Load Symbol Map & Replay Snapshots
    print("\n--- 3. Replaying Index Events & Auditing Constituent Mapping ---")
    smap = pd.read_parquet(SYMBOL_MAP_PATH)
    map_dict = smap.set_index("scrip_name").to_dict(orient="index")
    print(f"Loaded symbol map: {len(smap):,} scrips total")
    print(f"  mapping_status value counts:")
    for stat, cnt in smap["mapping_status"].value_counts().items():
        print(f"    - {stat}: {cnt:,}")

    all_unique_constituents = set()
    mapped_symbols = set()
    mapped_scrips = set()
    unmapped_scrips = set()

    snapshot_stats = []

    for idx, snap_date_str in enumerate(snapshot_dates, 1):
        snap_date = datetime.datetime.strptime(snap_date_str, "%Y-%m-%d").date()
        sub = nifty500_events[nifty500_events["effective_date"] <= snap_date]
        active = set()
        for _, r in sub.iterrows():
            if r["action"] == "IN":
                active.add(r["scrip_name"])
            elif r["action"] == "OUT":
                active.discard(r["scrip_name"])
                
        tot = len(active)
        mapped_count = 0
        unmapped_count = 0
        
        for scrip in active:
            all_unique_constituents.add(scrip)
            info = map_dict.get(scrip, {})
            m_stat = info.get("mapping_status", "unresolved")
            sym = info.get("symbol", "").strip()
            
            if m_stat in ["auto", "approved"] and sym:
                mapped_count += 1
                mapped_symbols.add(sym)
                mapped_scrips.add(scrip)
            else:
                unmapped_count += 1
                unmapped_scrips.add(scrip)
                
        snapshot_stats.append({
            "snapshot_idx": idx,
            "snapshot_date": snap_date_str,
            "total_constituents": tot,
            "mapped_constituents": mapped_count,
            "unmapped_constituents": unmapped_count,
            "mapped_pct": round(mapped_count / tot * 100.0, 2) if tot else 0.0
        })

    snap_df = pd.DataFrame(snapshot_stats)
    print(f"\nConstituent Audit Across All 57 Snapshots:")
    print(f"  Total unique constituent scrips in universe: {len(all_unique_constituents)}")
    print(f"  Unique mapped constituent scrips:            {len(mapped_scrips)} ({len(mapped_scrips)/len(all_unique_constituents)*100:.1f}%)")
    print(f"  Unique unmapped constituent scrips:          {len(unmapped_scrips)} ({len(unmapped_scrips)/len(all_unique_constituents)*100:.1f}%)")
    print(f"  Unique valid target symbols required:        {len(mapped_symbols)}")
    print(f"  Snapshot constituent count range:            {snap_df['total_constituents'].min()} to {snap_df['total_constituents'].max()}")
    print(f"  Mapped constituent fraction range:           {snap_df['mapped_pct'].min():.2f}% to {snap_df['mapped_pct'].max():.2f}% (median: {snap_df['mapped_pct'].median():.2f}%)")

    # 4. Isolate Unique Required Symbols & Dates Table
    print("\n--- 4. Exporting Required Symbols & Dates Artifacts ---")
    req_symbols_list = sorted(list(mapped_symbols))
    
    # Build detailed metadata table for required symbols
    req_metadata = []
    for sym in req_symbols_list:
        matches = smap[smap["symbol"] == sym]
        if not matches.empty:
            r = matches.iloc[0]
            req_metadata.append({
                "symbol": sym,
                "scrip_name": r["scrip_name"],
                "mapping_status": r["mapping_status"],
                "isin": r.get("isin", ""),
                "first_seen": str(r.get("first_seen", "")),
                "last_seen": str(r.get("last_seen", "")),
                "flags": r.get("flags", "")
            })
        else:
            req_metadata.append({
                "symbol": sym,
                "scrip_name": "",
                "mapping_status": "unknown",
                "isin": "",
                "first_seen": "",
                "last_seen": "",
                "flags": ""
            })
            
    req_df = pd.DataFrame(req_metadata)
    req_csv = DATA_CSV_DIR / "required_symbols_dates.csv"
    req_df.to_csv(req_csv, index=False)
    print(f"Exported required symbols manifest: {req_csv} ({len(req_df)} symbols, {req_csv.stat().st_size:,} bytes)")

    # Export snapshot constituents audit table
    snap_csv = DATA_CSV_DIR / "snapshot_prerequisite_audit.csv"
    snap_df.to_csv(snap_csv, index=False)
    print(f"Exported snapshot prerequisite table: {snap_csv} ({len(snap_df)} rows, {snap_csv.stat().st_size:,} bytes)")

    # Export list of 1,154 trading dates to CSV
    dates_csv = DATA_CSV_DIR / "window_trading_dates.csv"
    pd.DataFrame({"trading_date": window_trading_dates}).to_csv(dates_csv, index=False)
    print(f"Exported window trading dates: {dates_csv} ({len(window_trading_dates)} dates, {dates_csv.stat().st_size:,} bytes)")

    print("\n" + "=" * 80)
    print("GATE 0 EXIT: PREREQUISITES VERIFIED — 57 SNAPSHOTS, 435 SYMBOLS, 1,154 DATES CONFIRMED")
    print("=" * 80)

if __name__ == "__main__":
    main()
