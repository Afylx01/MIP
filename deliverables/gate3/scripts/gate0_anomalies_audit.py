#!/usr/bin/env python3
"""
deliverables/gate3/scripts/gate0_anomalies_audit.py
Phase 5.5 Gate 3 — Gate 0: Anomalies & Quarantined Rows Ingestion

1. Ingests data/index_events.parquet and IndexInclExcl.xls.
2. Ingests deliverables/gate_2c/data_csv/quarantine_gate1.csv.
3. Replays raw NIFTY500 constituent history from 1998-08-01 seed batch through 2020-09-14.
4. Isolates:
   - 15 orphan OUT events (stocks excluded without prior recorded inclusion).
   - 1 duplicate IN event.
   - Quarantined grp_2017_09_05 suspect datetime rows.
5. Exports:
   - deliverables/gate3/data_csv/unresolved_anomalies.csv
   - deliverables/gate3/raw/gate0_anomalies_audit.txt
"""

import os
import sys
import datetime
import xlrd
import pandas as pd
from pathlib import Path

BASE_DIR = Path("/sdcard/Documents/Project MIP")
DELIVERABLES_DIR = BASE_DIR / "deliverables/gate3"
RAW_DIR = DELIVERABLES_DIR / "raw"
DATA_CSV_DIR = DELIVERABLES_DIR / "data_csv"

INDEX_EVENTS_PARQUET = BASE_DIR / "data/index_events.parquet"
QUARANTINE_CSV = BASE_DIR / "deliverables/gate_2c/data_csv/quarantine_gate1.csv"
XLS_FILE = BASE_DIR / "IndexInclExcl.xls"

for d in [RAW_DIR, DATA_CSV_DIR]:
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

        if d_typ == 3:  # XL_CELL_DATE
            dt_tuple = xlrd.xldate_as_tuple(d_val, wb.datemode)
            dt = datetime.date(*dt_tuple[:3])
            date_type = "datetime"
        elif d_typ == 1:  # string
            parts = [int(p) for p in str(d_val).strip().split("-")]
            dt = datetime.date(parts[2], parts[1], parts[0])
            date_type = "string"
        elif d_typ == 2:  # number
            dt_tuple = xlrd.xldate_as_tuple(d_val, wb.datemode)
            dt = datetime.date(*dt_tuple[:3])
            date_type = "datetime"
        else:
            dt = None
            date_type = "unknown"

        rows.append({
            "index": "NIFTY500",
            "source_label": "Nifty 500",
            "row": r + 1,
            "effective_date": dt,
            "scrip_name": scrip,
            "action": act,
            "date_type": date_type
        })
    return rows

def main():
    print("=" * 80)
    print("PHASE 5.5 GATE 3 — GATE 0: ANOMALIES & QUARANTINED ROWS INGESTION")
    print(f"Timestamp: {datetime.datetime.now(datetime.timezone.utc).isoformat()}")
    print("=" * 80)

    # 1. Ingest Index Events Parquet
    print("\n--- 1. Ingesting data/index_events.parquet ---")
    assert INDEX_EVENTS_PARQUET.exists(), f"Missing {INDEX_EVENTS_PARQUET}"
    events_df = pd.read_parquet(INDEX_EVENTS_PARQUET)
    n500_events = events_df[events_df["index"] == "NIFTY500"].sort_values(["effective_date", "row"]).reset_index(drop=True)
    print(f"Total raw index events in parquet: {len(events_df):,}")
    print(f"Total NIFTY500 events in parquet:   {len(n500_events):,}")

    # 2. Ingest Quarantined Rows
    print("\n--- 2. Ingesting Quarantine Manifest ---")
    assert QUARANTINE_CSV.exists(), f"Missing {QUARANTINE_CSV}"
    quarantine_df = pd.read_csv(QUARANTINE_CSV)
    print(f"Total quarantined rows from Gate 1: {len(quarantine_df)}")
    n500_quarantine = quarantine_df[quarantine_df["sheet"] == "Nifty 500"]
    print(f"Quarantined rows in Nifty 500 sheet: {len(n500_quarantine)}")
    for _, q in n500_quarantine.iterrows():
        print(f"  Row {q['row']}: {q['effective_date']} | {q['scrip_name']} | {q['action']} | {q['quarantine_reason']}")

    # 3. Raw Workbook Replay (to isolate all 15 orphan OUTs and 1 duplicate IN)
    print("\n--- 3. Replaying Unfiltered Workbook Events (IndexInclExcl.xls) ---")
    raw_xls_rows = parse_excel_nifty500()
    print(f"Parsed {len(raw_xls_rows)} raw events directly from 'Nifty 500' worksheet.")

    # Chronological sort by effective_date, then row
    sorted_rows = sorted(raw_xls_rows, key=lambda x: (x["effective_date"] if x["effective_date"] else datetime.date(1900, 1, 1), x["row"]))

    active = set()
    orphan_outs = []
    duplicate_ins = []
    anomalies = []

    for r in sorted_rows:
        scrip = r["scrip_name"]
        act = r["action"]
        dt = r["effective_date"]
        dt_str = dt.strftime("%Y-%m-%d") if dt else "UNKNOWN"

        if act == "IN":
            if scrip in active:
                item = {
                    "index": "NIFTY500",
                    "row": r["row"],
                    "effective_date": dt_str,
                    "scrip_name": scrip,
                    "action": act,
                    "anomaly_type": "duplicate_in",
                    "source": "raw_xls_embedded_block"
                }
                duplicate_ins.append(item)
                anomalies.append(item)
            else:
                active.add(scrip)
        elif act == "OUT":
            if scrip not in active:
                item = {
                    "index": "NIFTY500",
                    "row": r["row"],
                    "effective_date": dt_str,
                    "scrip_name": scrip,
                    "action": act,
                    "anomaly_type": "orphan_out",
                    "source": "raw_xls_corporate_rename" if r["row"] != 2136 else "raw_xls_embedded_duplicate"
                }
                orphan_outs.append(item)
                anomalies.append(item)
            else:
                active.remove(scrip)

    print(f"\n--- Anomaly Detection Results ---")
    print(f"Total Orphan OUT Events Detected: {len(orphan_outs)}")
    assert len(orphan_outs) == 15, f"Expected exactly 15 orphan OUTs, found {len(orphan_outs)}"
    for idx, o in enumerate(orphan_outs, 1):
        print(f"  [{idx:2d}/15] Row {o['row']:4d} | {o['effective_date']} | OUT | {o['scrip_name']}")

    print(f"\nTotal Duplicate IN Events Detected: {len(duplicate_ins)}")
    assert len(duplicate_ins) == 1, f"Expected exactly 1 duplicate IN, found {len(duplicate_ins)}"
    for idx, d in enumerate(duplicate_ins, 1):
        print(f"  [{idx:2d}/1]  Row {d['row']:4d} | {d['effective_date']} | IN  | {d['scrip_name']}")

    # 4. Quarantined Rows Context
    print(f"\n--- Quarantined grp_2017_09_05 Detail ---")
    print("Quarantined Rows in grp_2017_09_05 across all index sheets:")
    for _, q in quarantine_df[quarantine_df["group_id"] == "grp_2017_09_05"].iterrows():
        print(f"  Sheet: {q['sheet']:30s} | Row {q['row']:4d} | {q['effective_date']} | {q['action']:3s} | {q['scrip_name']}")

    # 5. Export Unresolved Anomalies CSV
    anom_df = pd.DataFrame(anomalies)
    out_csv = DATA_CSV_DIR / "unresolved_anomalies.csv"
    anom_df.to_csv(out_csv, index=False)
    print(f"\nExported unresolved anomalies table: {out_csv} ({len(anom_df)} rows)")

    print("\n" + "=" * 80)
    print("GATE 0 AUDIT COMPLETE: EXACTLY 15 ORPHAN OUTS & 1 DUPLICATE IN CONFIRMED")
    print("=" * 80)

if __name__ == "__main__":
    main()
