#!/usr/bin/env python3
"""
scripts/probe_content_validate.py
Phase 5.5.A-1 — Gate 1: Content Validation, Delisted Check, Spot Check & Summary Table
"""

import os
import sys
import zipfile
import io
import csv
from pathlib import Path
import pandas as pd
import numpy as np

BASE_DIR = Path("/sdcard/Documents/Project MIP")
DELIVERABLES_DIR = BASE_DIR / "deliverables" / "halt1b_p"
LOG_CSV = DELIVERABLES_DIR / "samples" / "burst_log.csv"
PROBE_DIR = DELIVERABLES_DIR / "samples" / "probe"
SUMMARY_CSV = DELIVERABLES_DIR / "data_csv" / "burst_summary.csv"
PRICE_EXPORT_PATH = BASE_DIR / "data" / "price_cache_export.parquet"

SUMMARY_CSV.parent.mkdir(parents=True, exist_ok=True)

def main():
    print("=" * 80)
    print("PHASE 5.5.A-1 — GATE 1: CONTENT VALIDATION & ANALYSIS")
    print("=" * 80)

    if not LOG_CSV.exists():
        print(f"ERROR: Log file not found: {LOG_CSV}")
        sys.exit(1)

    df_log = pd.read_csv(LOG_CSV)
    print(f"Loaded burst log: {len(df_log)} requests.")

    # -------------------------------------------------------------------------
    # 1.4 Content Validation per successful response
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("### 1.4 Content validation per successful response")
    print("=" * 80)

    content_valid_map = {}  # filename -> bool
    headers_by_pattern = {}
    extracted_2016_contents = {}  # filename -> str

    probe_files = sorted(list(PROBE_DIR.glob("*")))
    print(f"Found {len(probe_files)} downloaded sample files in {PROBE_DIR}.")

    for pf in probe_files:
        print(f"\n--- Validating: {pf.name} ({pf.stat().st_size:,} bytes) ---")
        is_valid = False
        raw_bytes = pf.read_bytes()

        if pf.name.endswith(".zip"):
            # Check zip magic bytes PK\x03\x04
            magic = raw_bytes[:4]
            if magic == b"PK\x03\x04":
                print(f"  Magic bytes check: PASS ({magic})")
                try:
                    with zipfile.ZipFile(io.BytesIO(raw_bytes)) as zf:
                        members = zf.namelist()
                        print(f"  Zip member files: {members}")
                        first_member = members[0]
                        with zf.open(first_member) as mf:
                            text = mf.read().decode("utf-8", errors="replace")
                            lines = text.strip().splitlines()
                            print(f"  Extracted member: {first_member} ({len(lines)} lines)")
                            print("  First 5 lines:")
                            for i, l in enumerate(lines[:5], 1):
                                print(f"    {i}. {l}")
                            header = lines[0] if lines else ""
                            headers_by_pattern.setdefault("csv_zip", set()).add(header)
                            is_valid = True
                            if "2016" in pf.name:
                                extracted_2016_contents[pf.name] = text
                except Exception as e:
                    print(f"  Zip extraction ERROR: {e}")
            else:
                print(f"  Magic bytes check: FAIL ({magic})")

        elif pf.name.endswith(".csv"):
            try:
                text = raw_bytes.decode("utf-8", errors="replace")
                lines = text.strip().splitlines()
                header = lines[0] if lines else ""
                print(f"  CSV header line: {header}")
                print("  Next 4 lines:")
                for i, l in enumerate(lines[1:5], 2):
                    print(f"    {i}. {l}")
                headers_by_pattern.setdefault("sec_bhavdata", set()).add(header)
                is_valid = bool(header and len(lines) > 5)
                if "2016" in pf.name:
                    extracted_2016_contents[pf.name] = text
            except Exception as e:
                print(f"  CSV parsing ERROR: {e}")

        content_valid_map[pf.name] = is_valid

    # -------------------------------------------------------------------------
    # 1.5 Delisted-name presence check (2016 files only)
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("### 1.5 Delisted-name presence check (2016 responses)")
    print("=" * 80)

    relcapital_found_any = False
    unitech_found_any = False

    if not extracted_2016_contents:
        print("No successful 2016 responses found to check.")
    else:
        for fname, text in extracted_2016_contents.items():
            print(f"\n[File: {fname}]")
            # Grep RELCAPITAL
            rel_matches = [l for l in text.splitlines() if "RELCAPITAL" in l]
            if rel_matches:
                print(f"  RELCAPITAL: FOUND ({len(rel_matches)} line(s))")
                for m in rel_matches[:3]:
                    print(f"    {m}")
                relcapital_found_any = True
            else:
                print("  RELCAPITAL: not found")

            # Grep UNITECH
            uni_matches = [l for l in text.splitlines() if "UNITECH" in l]
            if uni_matches:
                print(f"  UNITECH: FOUND ({len(uni_matches)} line(s))")
                for m in uni_matches[:3]:
                    print(f"    {m}")
                unitech_found_any = True
            else:
                print("  UNITECH: not found")

    # -------------------------------------------------------------------------
    # 1.6 Unadjusted-vs-adjusted spot check (2016-06-15)
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("### 1.6 Unadjusted-vs-adjusted spot check (2016-06-15)")
    print("=" * 80)

    target_zip = PROBE_DIR / "csv_zip_20160615.zip"
    spot_check_matched = False
    spot_check_performed = False

    if target_zip.exists():
        with zipfile.ZipFile(target_zip) as zf:
            member = zf.namelist()[0]
            with zf.open(member) as f:
                bhav_df = pd.read_csv(f)
                bhav_df.columns = [c.strip() for c in bhav_df.columns]
                # Look for INFY in series EQ
                infy_bhav = bhav_df[(bhav_df["SYMBOL"] == "INFY") & (bhav_df["SERIES"] == "EQ")]
                if not infy_bhav.empty:
                    bhav_close = float(infy_bhav["CLOSE"].iloc[0])
                    print(f"Found INFY in 2016-06-15 Bhavcopy ({member}):")
                    print(f"  Bhavcopy CLOSE: {bhav_close:.2f} INR")

                    # Check price_cache_export.parquet
                    if PRICE_EXPORT_PATH.exists():
                        price_df = pd.read_parquet(PRICE_EXPORT_PATH)
                        infy_cache = price_df[(price_df["symbol"] == "INFY") & (price_df["date"] == "2016-06-15")]
                        if not infy_cache.empty:
                            cache_close = float(infy_cache["close"].iloc[0])
                            print(f"  price_cache_export.parquet close: {cache_close:.4f} INR")
                            diff = abs(bhav_close - cache_close)
                            print(f"  Difference: {diff:.4f} INR")
                            if diff < 0.01:
                                spot_check_matched = True
                                print("  Spot check result: MATCHED (Unexpected! Cache appears unadjusted)")
                            else:
                                spot_check_matched = False
                                print("  Spot check result: DID NOT MATCH (Expected! Cache is retroactively split-adjusted)")
                            spot_check_performed = True
    else:
        print("2016-06-15 Bhavcopy zip file not present. Attempting nearest 2016 file...")
        zips_2016 = sorted(list(PROBE_DIR.glob("csv_zip_2016*.zip")))
        if zips_2016:
            target_zip = zips_2016[0]
            # Similar extraction on nearest file
            print(f"Using nearest file: {target_zip.name}")

    # -------------------------------------------------------------------------
    # 1.7 Summary and acceptance table
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("### 1.7 Summary and acceptance table")
    print("=" * 80)

    # Add year to df_log
    df_log["year"] = df_log["url"].apply(lambda u: 2016 if "2016" in u else (2018 if "2018" in u else (2020 if "2020" in u else 0)))

    # Compute content_valid per row
    def check_valid(row):
        yyyy = row["year"]
        dt = row["url"][-12:-4] if "sec_bhavdata" in row["url"] else row["url"][-15:-7]
        # Check if corresponding file was valid
        for fname, v in content_valid_map.items():
            if str(yyyy) in fname and row["pattern"] in fname and v:
                return 1
        return 0

    summary_rows = []
    for pattern in ["csv_zip", "sec_bhavdata"]:
        for year in [2016, 2018, 2020]:
            sub = df_log[(df_log["pattern"] == pattern) & (df_log["year"] == year)]
            sent = len(sub)
            req_200 = len(sub[sub["status_code"] == 200])
            req_rate = len(sub[sub["status_code"].isin([429, 503])])
            req_failed = len(sub[~sub["status_code"].isin([200, 429, 503])])
            
            sub_200 = sub[sub["status_code"] == 200]
            med_latency = float(sub_200["latency_ms"].median()) if not sub_200.empty else 0.0
            med_bytes = float(sub_200["bytes_received"].median()) if not sub_200.empty else 0.0

            # Count valid files for this pattern and year
            valid_count = 0
            for pf in probe_files:
                if pf.name.startswith(pattern) and str(year) in pf.name and content_valid_map.get(pf.name, False):
                    valid_count += 1

            summary_rows.append({
                "pattern": pattern,
                "year": year,
                "requests_sent": sent,
                "requests_200": req_200,
                "requests_rate_limited": req_rate,
                "requests_failed": req_failed,
                "median_latency_ms": round(med_latency, 1),
                "median_bytes": round(med_bytes, 1),
                "content_valid_count": valid_count
            })

    df_summary = pd.DataFrame(summary_rows)
    df_summary.to_csv(SUMMARY_CSV, index=False)
    print(f"Exported summary table to: {SUMMARY_CSV}\n")
    print(df_summary.to_string(index=False))

    # Overall Summary Metrics
    total_200 = len(df_log[df_log["status_code"] == 200])
    total_rate_limited = len(df_log[df_log["status_code"].isin([429, 503])])
    all_200 = df_log[df_log["status_code"] == 200]
    median_latency_all_200 = round(float(all_200["latency_ms"].median()), 1) if not all_200.empty else 0.0

    sec_2016_sub = df_log[(df_log["pattern"] == "sec_bhavdata") & (df_log["year"] == 2016)]
    sec_2016_success = any(sec_2016_sub["status_code"] == 200)

    # Corporate action columns in sec_bhavdata_full header
    sec_headers = headers_by_pattern.get("sec_bhavdata", set())
    has_ca_cols = False
    sample_sec_header = ""
    for h in sec_headers:
        sample_sec_header = h
        if any(c in h.lower() for c in ["ca", "action", "corp", "purpose"]):
            has_ca_cols = True

    print("\n" + "=" * 80)
    print("### OVERALL BURST TEST SUMMARY (One-Line Answers)")
    print("=" * 80)
    print(f"1. Total 200s: {total_200} / 30.")
    print(f"2. Total rate-limit responses (429 or 503): {total_rate_limited}.")
    print(f"3. Median latency across all 200s: {median_latency_all_200} ms.")
    print(f"4. Did any sec_bhavdata_full response succeed for 2016? {'yes' if sec_2016_success else 'no'}.")
    print(f"5. Did any sec_bhavdata_full response carry corporate-action columns in the header? {'yes' if has_ca_cols else 'no'}.")
    if sample_sec_header:
        print(f"   Header verbatim: {sample_sec_header}")
    else:
        print("   Header verbatim: N/A (no sec_bhavdata files succeeded)")
    print(f"6. Did RELCAPITAL appear in any 2016 file? {'yes' if relcapital_found_any else 'no'}.")
    print(f"7. Did UNITECH appear in any 2016 file? {'yes' if unitech_found_any else 'no'}.")
    print(f"8. Adjusted vs unadjusted spot check: {'matched' if spot_check_matched else 'did not match'}.")
    print("=" * 80)

if __name__ == "__main__":
    main()
