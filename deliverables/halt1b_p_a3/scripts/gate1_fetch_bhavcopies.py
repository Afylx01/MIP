#!/usr/bin/env python3
"""
deliverables/halt1b_p_a3/scripts/gate1_fetch_bhavcopies.py
Phase 5.5.A-3 — Gate 1: Bhavcopy Acquisition & Raw Price Ingestion

1. Sources historical daily Bhavcopy archives (2016-01-01 to 2020-09-14, 1,154 trading dates)
   from official exchange archives (nsearchives.nseindia.com).
2. Uses honest User-Agent (MIP-research/0.1), concurrent session pool with retries and exponential backoff.
3. Reuses pre-existing Bhavcopies from deliverables/halt1b_p_a2/samples/bhav/ if present.
4. Verifies zip integrity (PK\x03\x04) and CSV headers.
5. Filters series EQ and BE for the 435 required target symbols.
6. Persists raw price dataset to data/verification/halt1b_p_a3/raw_bhavcopy_bars.parquet.
7. Exports summary CSV to deliverables/halt1b_p_a3/data_csv/gate1_download_summary.csv.
"""

import os
import sys
import io
import time
import zipfile
import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
import requests

BASE_DIR = Path("/sdcard/Documents/Project MIP")
DELIVERABLES_DIR = BASE_DIR / "deliverables/halt1b_p_a3"
RAW_DIR = DELIVERABLES_DIR / "raw"
DATA_CSV_DIR = DELIVERABLES_DIR / "data_csv"
SAMPLES_DIR = DELIVERABLES_DIR / "samples"
BHAV_DIR = SAMPLES_DIR / "bhav"
VERIF_DATA_DIR = BASE_DIR / "data/verification/halt1b_p_a3"

A2_BHAV_DIR = BASE_DIR / "deliverables/halt1b_p_a2/samples/bhav"

for d in [RAW_DIR, DATA_CSV_DIR, SAMPLES_DIR, BHAV_DIR, VERIF_DATA_DIR]:
    d.mkdir(parents=True, exist_ok=True)

USER_AGENT = "MIP-research/0.1"

MONTH_MAP = {
    "01": "JAN", "02": "FEB", "03": "MAR", "04": "APR", "05": "MAY", "06": "JUN",
    "07": "JUL", "08": "AUG", "09": "SEP", "10": "OCT", "11": "NOV", "12": "DEC"
}

def make_url(dt_str: str) -> tuple[str, str]:
    # e.g. 2016-01-04 -> dd=04, mon=JAN, yyyy=2016
    yyyy, mm, dd = dt_str.split("-")
    mon = MONTH_MAP[mm]
    fname = f"cm{dd}{mon}{yyyy}bhav.csv.zip"
    url = f"https://nsearchives.nseindia.com/content/historical/EQUITIES/{yyyy}/{mon}/{fname}"
    return url, fname

def fetch_single_bhavcopy(dt_str: str, target_symbols: set) -> dict:
    url, fname = make_url(dt_str)
    dest_path = BHAV_DIR / fname
    a2_path = A2_BHAV_DIR / fname
    
    zip_bytes = None
    source_type = "network"

    # Check if already cached in A-3
    if dest_path.exists() and dest_path.stat().st_size > 5000:
        try:
            with open(dest_path, "rb") as f:
                content = f.read()
            if content.startswith(b"PK\x03\x04"):
                zip_bytes = content
                source_type = "cache_a3"
        except Exception:
            pass

    # Check if available from A-2
    if zip_bytes is None and a2_path.exists() and a2_path.stat().st_size > 5000:
        try:
            with open(a2_path, "rb") as f:
                content = f.read()
            if content.startswith(b"PK\x03\x04"):
                zip_bytes = content
                source_type = "cache_a2"
                with open(dest_path, "wb") as f_out:
                    f_out.write(content)
        except Exception:
            pass

    # Download from network if not cached
    if zip_bytes is None:
        retries = 0
        max_retries = 3
        backoff = 1.0
        while retries <= max_retries:
            try:
                s = requests.Session()
                s.headers.update({
                    "User-Agent": USER_AGENT,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
                })
                resp = s.get(url, timeout=20)
                if resp.status_code == 200 and len(resp.content) > 5000 and resp.content.startswith(b"PK\x03\x04"):
                    zip_bytes = resp.content
                    with open(dest_path, "wb") as f_out:
                        f_out.write(zip_bytes)
                    source_type = "download"
                    break
                elif resp.status_code == 404:
                    # Market holiday or unlisted date
                    return {
                        "trading_date": dt_str,
                        "status": "HTTP_404",
                        "records_extracted": 0,
                        "size_bytes": len(resp.content),
                        "source": "network_404",
                        "bars": []
                    }
                elif resp.status_code in [429, 503]:
                    time.sleep(backoff)
                    backoff *= 2.0
                    retries += 1
                else:
                    retries += 1
                    time.sleep(0.5)
            except Exception as e:
                retries += 1
                time.sleep(backoff)
                backoff *= 1.5

        if zip_bytes is None:
            return {
                "trading_date": dt_str,
                "status": "FAILED",
                "records_extracted": 0,
                "size_bytes": 0,
                "source": "failed",
                "bars": []
            }

    # Extract target symbols from zip
    extracted_bars = []
    try:
        with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
            csv_names = [n for n in zf.namelist() if n.endswith(".csv")]
            if not csv_names:
                return {
                    "trading_date": dt_str,
                    "status": "CORRUPT_NO_CSV",
                    "records_extracted": 0,
                    "size_bytes": len(zip_bytes),
                    "source": source_type,
                    "bars": []
                }
            with zf.open(csv_names[0]) as csv_file:
                df = pd.read_csv(csv_file)
                df.columns = [c.strip().upper() for c in df.columns]
                
                # Check required headers
                req_headers = ["SYMBOL", "SERIES", "OPEN", "HIGH", "LOW", "CLOSE", "TOTTRDQTY"]
                for h in req_headers:
                    if h not in df.columns:
                        raise ValueError(f"Missing required header {h} in {fname}")
                
                # Filter series EQ and BE
                df_eq = df[df["SERIES"].isin(["EQ", "BE"])].copy()
                df_eq["SYMBOL"] = df_eq["SYMBOL"].str.strip().str.upper()
                
                # Filter target symbols
                sub = df_eq[df_eq["SYMBOL"].isin(target_symbols)]
                
                for _, r in sub.iterrows():
                    extracted_bars.append({
                        "symbol": r["SYMBOL"],
                        "date": dt_str,
                        "open": float(r["OPEN"]),
                        "high": float(r["HIGH"]),
                        "low": float(r["LOW"]),
                        "close": float(r["CLOSE"]),
                        "volume": float(r["TOTTRDQTY"]),
                        "series": r["SERIES"].strip()
                    })
                    
        return {
            "trading_date": dt_str,
            "status": "SUCCESS",
            "records_extracted": len(extracted_bars),
            "size_bytes": len(zip_bytes),
            "source": source_type,
            "bars": extracted_bars
        }
    except Exception as e:
        return {
            "trading_date": dt_str,
            "status": f"PARSE_ERROR_{str(e)[:30]}",
            "records_extracted": 0,
            "size_bytes": len(zip_bytes),
            "source": source_type,
            "bars": []
        }

def main():
    print("=" * 80)
    print("PHASE 5.5.A-3 — GATE 1: BHAVCOPY ACQUISITION & RAW PRICE INGESTION")
    start_time = datetime.datetime.now(datetime.timezone.utc)
    print(f"Timestamp: {start_time.isoformat()}")
    print("=" * 80)

    # 1. Load Required Target Symbols
    req_symbols_csv = DATA_CSV_DIR / "required_symbols_dates.csv"
    assert req_symbols_csv.exists(), f"Missing required symbols file: {req_symbols_csv}"
    req_df = pd.read_csv(req_symbols_csv)
    target_symbols = set(req_df["symbol"].dropna().str.strip().str.upper().unique())
    print(f"Loaded {len(target_symbols)} required target symbols from Gate 0.")

    # 2. Load Trading Dates
    dates_csv = DATA_CSV_DIR / "window_trading_dates.csv"
    assert dates_csv.exists(), f"Missing trading dates file: {dates_csv}"
    dates_df = pd.read_csv(dates_csv)
    trading_dates = sorted(dates_df["trading_date"].tolist())
    total_dates = len(trading_dates)
    print(f"Loaded {total_dates} trading dates from Gate 0 ({trading_dates[0]} to {trading_dates[-1]}).")

    # 3. Concurrent Fetch & Extraction
    print(f"\nStarting concurrent acquisition with ThreadPoolExecutor (max_workers=6)...")
    t0 = time.time()
    
    all_bars = []
    summary_records = []
    
    completed_count = 0
    success_count = 0
    cached_count = 0
    net_count = 0
    holiday_count = 0
    failed_count = 0

    with ThreadPoolExecutor(max_workers=6) as executor:
        future_to_date = {executor.submit(fetch_single_bhavcopy, dt, target_symbols): dt for dt in trading_dates}
        
        for future in as_completed(future_to_date):
            res = future.result()
            completed_count += 1
            st = res["status"]
            
            if st == "SUCCESS":
                success_count += 1
                if "cache" in res["source"]:
                    cached_count += 1
                else:
                    net_count += 1
                all_bars.extend(res["bars"])
            elif "404" in st:
                holiday_count += 1
            else:
                failed_count += 1
                
            summary_records.append({
                "trading_date": res["trading_date"],
                "status": res["status"],
                "records_extracted": res["records_extracted"],
                "size_bytes": res["size_bytes"],
                "source": res["source"]
            })
            
            if completed_count % 100 == 0 or completed_count == total_dates:
                pct = completed_count / total_dates * 100.0
                elapsed = time.time() - t0
                print(f"  [{completed_count:4d}/{total_dates:4d} ({pct:5.1f}%)] "
                      f"Success: {success_count} (Cache: {cached_count}, Net: {net_count}) | "
                      f"Holidays: {holiday_count} | Failed: {failed_count} | "
                      f"Bars Extracted: {len(all_bars):,} | Time: {elapsed:.1f}s")

    elapsed_total = time.time() - t0
    print(f"\nAcquisition Completed in {elapsed_total:.1f}s ({elapsed_total/60:.2f} mins).")

    # 4. Summary Table Export
    sum_df = pd.DataFrame(summary_records).sort_values("trading_date").reset_index(drop=True)
    sum_csv = DATA_CSV_DIR / "gate1_download_summary.csv"
    sum_df.to_csv(sum_csv, index=False)
    print(f"Exported download summary table: {sum_csv} ({len(sum_df)} dates, {sum_csv.stat().st_size:,} bytes)")

    # 5. Persist Raw Bars Dataset
    print(f"\n--- 5. Persisting Raw Bhavcopy Bars Dataset ---")
    raw_df = pd.DataFrame(all_bars)
    raw_df = raw_df.sort_values(by=["symbol", "date"]).reset_index(drop=True)
    
    out_parquet = VERIF_DATA_DIR / "raw_bhavcopy_bars.parquet"
    # Select clean schema columns matching adjuster contract
    clean_cols = ["symbol", "date", "open", "high", "low", "close", "volume"]
    raw_df_clean = raw_df[clean_cols].copy()
    raw_df_clean.to_parquet(out_parquet, index=False)
    
    print(f"Persisted Parquet: {out_parquet}")
    print(f"  Total Raw Bars:       {len(raw_df_clean):,}")
    print(f"  Distinct Symbols:     {raw_df_clean['symbol'].nunique():,}")
    print(f"  Distinct Dates:       {raw_df_clean['date'].nunique():,}")
    print(f"  Date Range:           {raw_df_clean['date'].min()} to {raw_df_clean['date'].max()}")
    print(f"  Parquet File Size:    {out_parquet.stat().st_size:,} bytes ({out_parquet.stat().st_size / 1024 / 1024:.2f} MB)")

    # Assertions
    assert len(raw_df_clean) > 300000, f"Expected >300,000 bars, got {len(raw_df_clean):,}"
    assert raw_df_clean["symbol"].nunique() >= 400, f"Expected >=400 symbols, got {raw_df_clean['symbol'].nunique()}"
    assert raw_df_clean["date"].nunique() >= 1100, f"Expected >=1,100 dates, got {raw_df_clean['date'].nunique()}"

    print("\n" + "=" * 80)
    print("GATE 1 EXIT: SUCCESS — RAW BHAVCOPY BARS INGESTED AND PERSISTED")
    print("=" * 80)

if __name__ == "__main__":
    main()
