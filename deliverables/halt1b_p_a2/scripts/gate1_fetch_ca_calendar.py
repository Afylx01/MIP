#!/usr/bin/env python3
"""
deliverables/halt1b_p_a2/scripts/gate1_fetch_ca_calendar.py
Phase 5.5.A-2 — Gate 1: Fetch CA Calendar & Gate 4 Reference Bhavcopies

1. Fetches historical Corporate Actions (2016-01-01 to 2020-09-14) from NSE API.
2. Saves raw API JSON payloads to deliverables/halt1b_p_a2/samples/ca_raw_<YYYY>.json.
3. Parses splits and bonuses with exact ratio extraction.
4. Generates data/verification/halt1b_p_a2/ca_calendar_raw.parquet and CSV export.
5. Downloads daily Bhavcopy zip archives for the 5 Gate 4 event windows into samples/bhav/.
6. Extracts raw OHLCV bars for the test symbols into samples/test_events_raw_bars.csv.
"""

import os
import sys
import re
import json
import time
import zipfile
import datetime
import subprocess
import pandas as pd
from pathlib import Path

BASE_DIR = Path("/sdcard/Documents/Project MIP")
DELIVERABLES_DIR = BASE_DIR / "deliverables/halt1b_p_a2"
RAW_DIR = DELIVERABLES_DIR / "raw"
DATA_CSV_DIR = DELIVERABLES_DIR / "data_csv"
SAMPLES_DIR = DELIVERABLES_DIR / "samples"
BHAV_DIR = SAMPLES_DIR / "bhav"
VERIF_DATA_DIR = BASE_DIR / "data/verification/halt1b_p_a2"

for d in [RAW_DIR, DATA_CSV_DIR, SAMPLES_DIR, BHAV_DIR, VERIF_DATA_DIR]:
    d.mkdir(parents=True, exist_ok=True)

USER_AGENT = "MIP-research/0.1"

# Date slices for CA API
CA_SLICES = [
    ("2016", "01-01-2016", "31-12-2016"),
    ("2017", "01-01-2017", "31-12-2017"),
    ("2018", "01-01-2018", "31-12-2018"),
    ("2019", "01-01-2019", "31-12-2019"),
    ("2020", "01-01-2020", "14-09-2020"),
]

def fetch_ca_slice(label, from_date, to_date):
    raw_path = SAMPLES_DIR / f"ca_raw_{label}.json"
    url = f"https://www.nseindia.com/api/corporates-corporateActions?index=equities&from_date={from_date}&to_date={to_date}"
    if raw_path.exists() and raw_path.stat().st_size > 1000:
        print(f"Loading cached CA slice {label} from {raw_path.name}...")
        with open(raw_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"  -> Loaded {len(data):,} raw records for {label}")
        return data, url

    print(f"Fetching CA slice {label} ({from_date} to {to_date})...")
    cmd = [
        "curl", "-s", "-m", "30",
        "-w", "%{http_code}:%{size_download}:%{time_total}",
        "-A", USER_AGENT,
        "-H", "Accept: application/json, text/plain, */*",
        url,
        "-o", str(raw_path)
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    parts = res.stdout.strip().split(":")
    status = int(parts[0]) if len(parts) >= 1 and parts[0].isdigit() else 0
    size = int(float(parts[1])) if len(parts) >= 2 and parts[1].replace(".", "", 1).isdigit() else 0
    latency = parts[2] if len(parts) >= 3 else "0"
    
    print(f"  -> HTTP {status} | Size: {size:,} bytes | Time: {latency}s")
    if status != 200 or size < 1000:
        raise RuntimeError(f"Failed to fetch CA slice {label}: status={status}, size={size}")
        
    with open(raw_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"  -> Loaded {len(data):,} raw records for {label}")
    return data, url

def parse_ca_record(rec, source_url, fetched_at):
    """
    Parses a single record from NSE corporate actions API.
    Returns dict if valid equity split or bonus, else None.
    """
    series = (rec.get("series") or "").strip()
    # Filter equity series only (EQ, BE, SM, etc.)
    if series and series not in ("EQ", "BE", "SM", "BZ"):
        return None
        
    symbol = (rec.get("symbol") or "").strip().upper()
    ex_date_str = (rec.get("exDate") or "").strip()
    subject = (rec.get("subject") or "").strip()
    
    if not symbol or not ex_date_str or ex_date_str == "-":
        return None
        
    # Parse ex_date: format is usually 'DD-Mon-YYYY' e.g. '04-Sep-2018'
    try:
        ex_dt = datetime.datetime.strptime(ex_date_str, "%d-%b-%Y").date()
    except Exception:
        return None
        
    # Check if within window 2016-01-01 -> 2020-09-14
    if ex_dt < datetime.date(2016, 1, 1) or ex_dt > datetime.date(2020, 9, 14):
        return None
        
    subj_upper = subject.upper()
    
    # 1. BONUS
    # Examples: "Bonus 1:1", "Bonus Issue 1:2", "Bonus 1:3", "Bonus 3:1"
    # Ignore bonus debentures e.g. "Bonus Debentures"
    if "BONUS" in subj_upper and "DEBENTURE" not in subj_upper:
        # Match pattern X:Y
        m = re.search(r'BONUS.*?(\d+)\s*:\s*(\d+)', subj_upper)
        if not m:
            m = re.search(r'(\d+)\s*:\s*(\d+).*?BONUS', subj_upper)
        if m:
            x = float(m.group(1))
            y = float(m.group(2))
            if y > 0:
                ratio = x / y
                return {
                    "symbol": symbol,
                    "ex_date": ex_dt.isoformat(),
                    "action_type": "bonus",
                    "ratio": ratio,
                    "source_url": source_url,
                    "fetched_at": fetched_at,
                    "subject_raw": subject
                }

    # 2. SPLIT / SUB-DIVISION
    # Examples:
    # "Face Value Split (Sub-Division) - From Rs 10/- Per Share To Rs 2/- Per Share"
    # "Sub-Division of Face Value from Rs.10/- each to Rs.2/- each"
    # "Split - Rs 10/- to Re 1/-"
    if ("SPLIT" in subj_upper or "SUB-DIVISION" in subj_upper or "SUB DIVISION" in subj_upper) and "CONSOLIDATION" not in subj_upper:
        # Match "from ... X ... to ... Y"
        m = re.search(r'(?:FROM|RS\.?)\s*(\d+(?:\.\d+)?)\s*(?:/-)?.*?(?:TO|EACH TO)\s*(?:RS\.?|RE\.?)\s*(\d+(?:\.\d+)?)\s*(?:/-)?', subj_upper)
        if not m:
            m = re.search(r'(\d+(?:\.\d+)?)\s*(?:/-)?\s*TO\s*(\d+(?:\.\d+)?)\s*(?:/-)?', subj_upper)
        if m:
            old_fv = float(m.group(1))
            new_fv = float(m.group(2))
            if new_fv > 0 and old_fv > new_fv:
                ratio = old_fv / new_fv
                return {
                    "symbol": symbol,
                    "ex_date": ex_dt.isoformat(),
                    "action_type": "split",
                    "ratio": ratio,
                    "source_url": source_url,
                    "fetched_at": fetched_at,
                    "subject_raw": subject
                }
                
    return None

def download_bhavcopy(dt):
    """
    Downloads Bhavcopy zip for a date from NSE archives.
    URL: https://nsearchives.nseindia.com/content/historical/EQUITIES/<YYYY>/<MMM>/cm<DD><MMM><YYYY>bhav.csv.zip
    """
    dd = dt.strftime("%d")
    mmm = dt.strftime("%b").upper()
    yyyy = dt.strftime("%Y")
    filename = f"cm{dd}{mmm}{yyyy}bhav.csv.zip"
    dest_path = BHAV_DIR / filename
    
    if dest_path.exists() and dest_path.stat().st_size > 5000:
        return dest_path, True
        
    url = f"https://nsearchives.nseindia.com/content/historical/EQUITIES/{yyyy}/{mmm}/{filename}"
    cmd = [
        "curl", "-s", "-m", "25",
        "-w", "%{http_code}:%{size_download}",
        "-A", USER_AGENT,
        "-H", "Accept: text/html,application/xhtml+xml,application/xml,application/zip,*/*;q=0.9",
        url,
        "-o", str(dest_path)
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    parts = res.stdout.strip().split(":")
    status = int(parts[0]) if len(parts) >= 1 and parts[0].isdigit() else 0
    size = int(parts[1]) if len(parts) >= 2 and parts[1].isdigit() else 0
    
    if status == 200 and size > 5000:
        print(f"  Downloaded Bhavcopy: {filename} ({size:,} bytes)")
        return dest_path, True
    else:
        # Clean up empty or 404 file
        if dest_path.exists():
            dest_path.unlink()
        return dest_path, False

def get_trading_days_around(target_date, days_before=5, days_after=5):
    """
    Returns candidate dates around target_date (skipping weekends).
    Offsets -9 to +9 calendar days covers 11-13 weekdays, sufficient for 5 bars before and 5 after.
    """
    dates = []
    for offset in range(-9, 10):
        d = target_date + datetime.timedelta(days=offset)
        if d.weekday() < 5: # Mon-Fri
            dates.append(d)
    return sorted(dates)

def main():
    print("=" * 80)
    print("PHASE 5.5.A-2 — GATE 1: FETCH CA CALENDAR & BHAVCOPIES")
    start_time = datetime.datetime.now(datetime.timezone.utc)
    print(f"Timestamp: {start_time.isoformat()}")
    print("=" * 80)
    
    fetched_at = start_time.strftime("%Y-%m-%d %H:%M:%S UTC")
    all_records = []
    
    for label, f_dt, t_dt in CA_SLICES:
        data, url = fetch_ca_slice(label, f_dt, t_dt)
        for rec in data:
            parsed = parse_ca_record(rec, url, fetched_at)
            if parsed:
                all_records.append(parsed)
        time.sleep(1.2)
        
    print(f"\nTotal parsed corporate action events (splits/bonuses): {len(all_records)}")
    
    df = pd.DataFrame(all_records)
    # Deduplicate exact (symbol, ex_date, action_type)
    df = df.drop_duplicates(subset=["symbol", "ex_date", "action_type"])
    df = df.sort_values(by=["ex_date", "symbol"]).reset_index(drop=True)
    
    # Save full parsed debug CSV
    debug_csv = RAW_DIR / "ca_calendar_parsed_debug.csv"
    df.to_csv(debug_csv, index=False)
    
    # Save required schema columns
    clean_cols = ["symbol", "ex_date", "action_type", "ratio", "source_url", "fetched_at"]
    df_clean = df[clean_cols]
    
    out_parquet = VERIF_DATA_DIR / "ca_calendar_raw.parquet"
    out_csv = DATA_CSV_DIR / "ca_calendar.csv"
    
    df_clean.to_parquet(out_parquet, index=False)
    df_clean.to_csv(out_csv, index=False)
    
    print("\nGate 1 Calendar Statistics:")
    print(f"  Total records: {len(df_clean):,}")
    print(f"  Distinct symbols: {df_clean['symbol'].nunique():,}")
    print(f"  Distinct dates: {df_clean['ex_date'].nunique():,}")
    print(f"  Date range: {df_clean['ex_date'].min()} to {df_clean['ex_date'].max()}")
    print(f"  Action breakdown: {df_clean['action_type'].value_counts().to_dict()}")
    print(f"  Persisted Parquet: {out_parquet} ({out_parquet.stat().st_size:,} bytes)")
    print(f"  Persisted CSV: {out_csv} ({out_csv.stat().st_size:,} bytes)")

    # -------------------------------------------------------------------------
    # PART 2: GATE 4 EVENT WINDOW BHAVCOPY DOWNLOADS (WHILE NETWORK IS OPEN)
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("GATE 1 PART 2: FETCHING REFERENCE BHAVCOPIES FOR GATE 4 UNIT TESTS")
    print("=" * 80)
    
    # The 5 events to test:
    # 1. INFY 2018 bonus (ex-date: 2018-09-04, 1:1 bonus, ratio=1.0)
    # 2. TCS 2018 bonus (ex-date: 2018-05-31, 1:1 bonus, ratio=1.0)
    # 3. RELIANCE 2017 bonus (ex-date: 2017-09-07, 1:1 bonus, ratio=1.0)
    # 4. WIPRO 2019 bonus (ex-date: 2019-03-06, 1:3 bonus, ratio=0.3333333333333333)
    # 5. MOLDTKPAC 2016 split (ex-date: 2016-02-17, split 10 to 5, ratio=2.0)
    test_events = [
        {
            "symbol": "INFY",
            "ex_date": datetime.date(2018, 9, 4),
            "action_type": "bonus",
            "ratio": 1.0,
            "dates": [
                datetime.date(2018, 8, 28), datetime.date(2018, 8, 29), datetime.date(2018, 8, 30),
                datetime.date(2018, 8, 31), datetime.date(2018, 9, 3), datetime.date(2018, 9, 4),
                datetime.date(2018, 9, 5), datetime.date(2018, 9, 6), datetime.date(2018, 9, 7),
                datetime.date(2018, 9, 10), datetime.date(2018, 9, 11)
            ]
        },
        {
            "symbol": "TCS",
            "ex_date": datetime.date(2018, 5, 31),
            "action_type": "bonus",
            "ratio": 1.0,
            "dates": [
                datetime.date(2018, 5, 24), datetime.date(2018, 5, 25), datetime.date(2018, 5, 28),
                datetime.date(2018, 5, 29), datetime.date(2018, 5, 30), datetime.date(2018, 5, 31),
                datetime.date(2018, 6, 1), datetime.date(2018, 6, 4), datetime.date(2018, 6, 5),
                datetime.date(2018, 6, 6), datetime.date(2018, 6, 7)
            ]
        },
        {
            "symbol": "RELIANCE",
            "ex_date": datetime.date(2017, 9, 7),
            "action_type": "bonus",
            "ratio": 1.0,
            "dates": [
                datetime.date(2017, 8, 31), datetime.date(2017, 9, 1), datetime.date(2017, 9, 4),
                datetime.date(2017, 9, 5), datetime.date(2017, 9, 6), datetime.date(2017, 9, 7),
                datetime.date(2017, 9, 8), datetime.date(2017, 9, 11), datetime.date(2017, 9, 12),
                datetime.date(2017, 9, 13), datetime.date(2017, 9, 14)
            ]
        },
        {
            "symbol": "WIPRO",
            "ex_date": datetime.date(2019, 3, 6),
            "action_type": "bonus",
            "ratio": 1.0/3.0,
            "dates": [
                datetime.date(2019, 2, 26), datetime.date(2019, 2, 27), datetime.date(2019, 2, 28),
                datetime.date(2019, 3, 1), datetime.date(2019, 3, 5), datetime.date(2019, 3, 6),
                datetime.date(2019, 3, 7), datetime.date(2019, 3, 8), datetime.date(2019, 3, 11),
                datetime.date(2019, 3, 12), datetime.date(2019, 3, 13)
            ]
        },
        {
            "symbol": "MOLDTKPAC",
            "ex_date": datetime.date(2016, 2, 17),
            "action_type": "split",
            "ratio": 2.0,
            "dates": [
                datetime.date(2016, 2, 10), datetime.date(2016, 2, 11), datetime.date(2016, 2, 12),
                datetime.date(2016, 2, 15), datetime.date(2016, 2, 16), datetime.date(2016, 2, 17),
                datetime.date(2016, 2, 18), datetime.date(2016, 2, 19), datetime.date(2016, 2, 22),
                datetime.date(2016, 2, 23), datetime.date(2016, 2, 24)
            ]
        },
    ]
    
    # Check that each test event is in our calendar
    for ev in test_events:
        match = df[(df["symbol"] == ev["symbol"]) & (df["ex_date"] == ev["ex_date"].isoformat())]
        if match.empty:
            print(f"WARNING: Test event {ev['symbol']} {ev['ex_date']} not found in calendar!")
        else:
            row = match.iloc[0]
            print(f"Confirmed test event: {row['symbol']} on {row['ex_date']} | {row['action_type']} | ratio={row['ratio']:.4f}")

    # Collect exact 55 trading dates across the 5 events
    dates_to_fetch = set()
    for ev in test_events:
        for d in ev["dates"]:
            dates_to_fetch.add(d)
            
    print(f"\nTotal candidate trading dates to check across 5 event windows: {len(dates_to_fetch)}")
    assert len(dates_to_fetch) <= 55, f"Candidate dates {len(dates_to_fetch)} exceeds 55 limit!"
    
    downloaded_files = []
    for d in sorted(dates_to_fetch):
        path, success = download_bhavcopy(d)
        if success:
            downloaded_files.append((d, path))
        time.sleep(0.5) # respect rate limit
        
    print(f"\nSuccessfully downloaded / verified {len(downloaded_files)} daily Bhavcopy archives.")
    assert len(downloaded_files) <= 60, f"Downloaded files {len(downloaded_files)} exceeds 60 limit!"
    
    # Extract bars for test symbols from downloaded Bhavcopies
    extracted_bars = []
    test_symbols = {ev["symbol"] for ev in test_events}
    
    for dt, zip_path in downloaded_files:
        try:
            with zipfile.ZipFile(zip_path, 'r') as z:
                csv_names = [n for n in z.namelist() if n.endswith('.csv')]
                if not csv_names:
                    continue
                with z.open(csv_names[0]) as f:
                    bhav_df = pd.read_csv(f)
                    # Clean columns
                    bhav_df.columns = [c.strip() for c in bhav_df.columns]
                    # Filter for EQ series and test symbols
                    sub = bhav_df[(bhav_df["SERIES"] == "EQ") & (bhav_df["SYMBOL"].isin(test_symbols))]
                    for _, r in sub.iterrows():
                        extracted_bars.append({
                            "symbol": r["SYMBOL"].strip(),
                            "date": dt.strftime("%Y-%m-%d"),
                            "open": float(r["OPEN"]),
                            "high": float(r["HIGH"]),
                            "low": float(r["LOW"]),
                            "close": float(r["CLOSE"]),
                            "volume": int(r["TOTTRDQTY"])
                        })
        except Exception as e:
            print(f"Error parsing Bhavcopy {zip_path.name}: {e}")
            
    bars_df = pd.DataFrame(extracted_bars)
    bars_df = bars_df.sort_values(by=["symbol", "date"]).reset_index(drop=True)
    raw_bars_csv = SAMPLES_DIR / "test_events_raw_bars.csv"
    bars_df.to_csv(raw_bars_csv, index=False)
    print(f"\nSaved raw bars for test events to {raw_bars_csv} ({len(bars_df)} bars)")
    print(bars_df.groupby("symbol")["date"].count().to_dict())

    print("\n" + "=" * 80)
    print("GATE 1 EXIT: SUCCESS — CA CALENDAR PERSISTED AND GATE 4 DATA CAPTURED")
    print("=" * 80)

if __name__ == "__main__":
    main()
