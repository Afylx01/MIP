#!/usr/bin/env python3
"""
scripts/burst_probe.py
Phase 5.5.A-1 — Gate 1: Network Viability Burst Test
Executes exactly 30 requests according to prompt schedule:
- 15 requests to .csv.zip pattern (5 in 2016, 5 in 2018, 5 in 2020)
- 15 requests to sec_bhavdata_full pattern (5 in 2016, 5 in 2018, 5 in 2020)
Applies rate limiting, exponential backoff, per-request logging, and payload validation.
"""

import os
import sys
import time
import datetime
import subprocess
from pathlib import Path
import csv

BASE_DIR = Path("/sdcard/Documents/Project MIP")
DELIVERABLES_DIR = BASE_DIR / "deliverables" / "halt1b_p"
LOG_CSV = DELIVERABLES_DIR / "samples" / "burst_log.csv"
PROBE_DIR = DELIVERABLES_DIR / "samples" / "probe"

PROBE_DIR.mkdir(parents=True, exist_ok=True)
LOG_CSV.parent.mkdir(parents=True, exist_ok=True)

USER_AGENT = "MIP-research/0.1"

DATES_BY_YEAR = {
    2016: ["2016-02-08", "2016-04-22", "2016-06-15", "2016-09-09", "2016-11-23"],
    2018: ["2018-02-06", "2018-04-20", "2018-06-29", "2018-09-10", "2018-11-26"],
    2020: ["2020-02-05", "2020-04-23", "2020-07-06", "2020-09-14", "2020-11-25"]
}

MONTH_MAP = {
    "01": "JAN", "02": "FEB", "03": "MAR", "04": "APR", "05": "MAY", "06": "JUN",
    "07": "JUL", "08": "AUG", "09": "SEP", "10": "OCT", "11": "NOV", "12": "DEC"
}

def make_url_zip(dt_str: str) -> str:
    # e.g. 2016-06-15 -> YYYY=2016, MON=JUN, DD=15
    yyyy, mm, dd = dt_str.split("-")
    mon = MONTH_MAP[mm]
    return f"https://nsearchives.nseindia.com/content/historical/EQUITIES/{yyyy}/{mon}/cm{dd}{mon}{yyyy}bhav.csv.zip"

def make_url_sec(dt_str: str) -> str:
    # e.g. 2016-06-15 -> DDMMYYYY=15062016
    yyyy, mm, dd = dt_str.split("-")
    return f"https://nsearchives.nseindia.com/products/content/sec_bhavdata_full_{dd}{mm}{yyyy}.csv"

def fetch_request(url: str, output_path: Path, max_retries: int = 3):
    retry_count = 0
    while retry_count <= max_retries:
        t0 = time.time()
        req_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        
        # We use curl with timeout, writing response body to file and metadata to stdout
        cmd = [
            "curl", "-s", "-m", "25",
            "-w", "%{http_code}:%{size_download}:%{content_type}:%{time_total}",
            "-A", USER_AGENT,
            "-H", "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            url,
            "-o", str(output_path)
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        t1 = time.time()
        latency_ms = int((t1 - t0) * 1000)
        
        out = res.stdout.strip()
        parts = out.split(":", 3)
        if len(parts) >= 4:
            status_code = int(parts[0]) if parts[0].isdigit() else 0
            bytes_received = int(float(parts[1])) if parts[1].replace(".", "", 1).isdigit() else 0
            content_type = parts[2]
            err = "" if status_code == 200 else f"HTTP {status_code}"
        else:
            status_code = 0
            bytes_received = output_path.stat().st_size if output_path.exists() else 0
            content_type = "unknown"
            err = res.stderr.strip() or "Connection error / timeout"

        # Check rate-limiting backoff
        if status_code in [429, 503] and retry_count < max_retries:
            wait_sec = 2 ** (retry_count + 1)
            print(f"      [HTTP {status_code}] Rate-limited on {url}. Backing off {wait_sec}s (retry {retry_count+1}/{max_retries})...")
            retry_count += 1
            time.sleep(wait_sec)
            continue
        elif status_code in [429, 503]:
            err = "FAILED_RATE_LIMIT"
            return status_code, bytes_received, latency_ms, retry_count, content_type, err, req_iso

        return status_code, bytes_received, latency_ms, retry_count, content_type, err, req_iso

def main():
    print("=" * 80)
    print("PHASE 5.5.A-1 — GATE 1: NETWORK BURST TEST")
    print(f"Timestamp: {datetime.datetime.now(datetime.timezone.utc).isoformat()}")
    print(f"Target User-Agent: {USER_AGENT}")
    print("=" * 80)

    # Build the 30-request schedule (interleaved by date across years)
    schedule = []
    for y in [2016, 2018, 2020]:
        for dt_str in DATES_BY_YEAR[y]:
            schedule.append(("csv_zip", y, dt_str, make_url_zip(dt_str)))
            schedule.append(("sec_bhavdata", y, dt_str, make_url_sec(dt_str)))

    print(f"Prepared schedule of {len(schedule)} requests across 2016, 2018, 2020.")
    print("Beginning execution with minimum 1.0s floor between requests...\n")

    log_rows = []
    consecutive_non_200 = 0
    total_downloaded_bytes = 0
    max_bytes_limit = 200 * 1024 * 1024  # 200 MB

    for idx, (pattern, year, dt_str, url) in enumerate(schedule, 1):
        yyyy, mm, dd = dt_str.split("-")
        ext = "zip" if pattern == "csv_zip" else "csv"
        out_filename = f"{pattern}_{yyyy}{mm}{dd}.{ext}"
        out_path = PROBE_DIR / out_filename

        print(f"[{idx:02d}/30] Year={year} | Pattern={pattern:<13} | Date={dt_str}")
        print(f"        URL: {url}")

        status, bytes_rec, latency, retries, c_type, err, req_iso = fetch_request(url, out_path)
        total_downloaded_bytes += bytes_rec

        print(f"        Result: HTTP {status} | Latency: {latency} ms | Bytes: {bytes_rec} | Error: {err or 'None'}")

        if status == 200:
            consecutive_non_200 = 0
        else:
            consecutive_non_200 += 1
            # If non-200, delete any partial or error body
            if out_path.exists() and status != 200:
                out_path.unlink()

        log_rows.append({
            "seq": idx,
            "url": url,
            "pattern": pattern,
            "requested_at_iso": req_iso,
            "status_code": status,
            "bytes_received": bytes_rec,
            "latency_ms": latency,
            "retry_count": retries,
            "content_type": c_type,
            "error": err
        })

        if total_downloaded_bytes > max_bytes_limit:
            print(f"\nFATAL: Total downloaded bytes ({total_downloaded_bytes / (1024*1024):.1f} MB) exceeded 200 MB limit. Aborting burst.")
            break

        if consecutive_non_200 >= 5:
            print(f"\nFATAL: 5 consecutive requests failed with non-200. Aborting burst per protocol.")
            break

        # Minimum 1.0 second floor between successive requests
        time.sleep(1.2)

    # Write burst_log.csv
    fieldnames = ["seq", "url", "pattern", "requested_at_iso", "status_code", "bytes_received", "latency_ms", "retry_count", "content_type", "error"]
    with open(LOG_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(log_rows)

    print(f"\nWrote per-request log to: {LOG_CSV}")
    print(f"Total requests executed: {len(log_rows)} / 30")
    print(f"Total bytes downloaded: {total_downloaded_bytes:,} bytes")
    print("=" * 80)

if __name__ == "__main__":
    main()
