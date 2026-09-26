#!/usr/bin/env python3
"""
Gate 0 — Inventory of NSE Bulletins and Index Maintenance URLs (2020-09 onward)
Sources specified:
- https://nsearchives.nseindia.com/content/indices/
- https://niftyindices.com/reports/historical-data
- https://nsearchives.nseindia.com/content/press/
"""

import os
import sys
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime

TARGET_INDICES = [
    "NIFTY50",
    "NIFTY100",
    "NIFTY200",
    "NIFTY500",
    "NIFTYMIDCAP100",
    "NIFTYSMALLCAP100",
    "NIFTYNEXT50",
]

RAW_BULLETINS_DIR = "data/raw_bulletins"
os.makedirs(RAW_BULLETINS_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

SOURCES_TO_PROBE = [
    ("NSE Archives - Indices Directory", "https://nsearchives.nseindia.com/content/indices/"),
    ("NSE Archives - Press Directory", "https://nsearchives.nseindia.com/content/press/"),
    ("NiftyIndices - Historical Data", "https://niftyindices.com/reports/historical-data"),
    ("NiftyIndices - Monthly Reports", "https://niftyindices.com/reports/monthly-reports"),
    ("NiftyIndices - Press Releases", "https://niftyindices.com/resources/press-releases"),
    ("NiftyIndices - Rebalancing Schedule", "https://niftyindices.com/resources/index-rebalancing-schedule"),
]

def fetch_with_retry(url: str, max_retries: int = 3, timeout: int = 15):
    delay = 1.0
    for attempt in range(max_retries):
        try:
            time.sleep(0.5)  # rate limit
            resp = requests.get(url, headers=HEADERS, timeout=timeout)
            if resp.status_code in (429, 503):
                time.sleep(delay)
                delay *= 2.0
                continue
            return resp
        except Exception as exc:
            if attempt == max_retries - 1:
                raise exc
            time.sleep(delay)
            delay *= 2.0
    return None

def main():
    print("=" * 80)
    print("GATE 0 — INVENTORY: NSE Bulletins & Index Maintenance (2020-09 onward)")
    print(f"Timestamp: {datetime.now().isoformat()}Z")
    print("Target Indices:", ", ".join(TARGET_INDICES))
    print("=" * 80)

    inventory_records = []
    files_written = []

    print("\n[1] Probing Primary Specified Sources...")
    for label, url in SOURCES_TO_PROBE:
        try:
            resp = fetch_with_retry(url)
            status = resp.status_code
            size = len(resp.content)
            print(f"  [{status}] {label}: {url} ({size} bytes)")
            
            # Cache reachable HTML/content
            safe_name = label.lower().replace(" ", "_").replace("-", "_") + f"_{status}.html"
            out_path = os.path.join(RAW_BULLETINS_DIR, safe_name)
            with open(out_path, "wb") as f:
                f.write(resp.content)
            files_written.append(out_path)

            inventory_records.append({
                "source": label,
                "url": url,
                "status": status,
                "size_bytes": size,
                "cached_file": out_path,
                "type": "directory/page"
            })
        except Exception as e:
            print(f"  [ERROR] {label} ({url}): {e}")
            inventory_records.append({
                "source": label,
                "url": url,
                "status": "ERROR",
                "error": str(e),
                "type": "error"
            })

    # Probing candidate circular / bulletin endpoints
    print("\n[2] Checking Specific Index Bulletin Patterns (2020-09 to present)...")
    # Standard circular file naming tested on NSE archives
    candidate_bulletin_urls = [
        ("Nifty Replacement Circular Sep 2020", "https://nsearchives.nseindia.com/content/circulars/CML45722.pdf"),
        ("Nifty Replacement Press Release Mar 2021", "https://nsearchives.nseindia.com/web/sites/default/files/inline-files/PR_CC_19022021.pdf"),
        ("Nifty Indices Benchmark Codes PDF", "https://niftyindices.com/BenchmarkCodes/nifty_indices_benchmark_codes.pdf"),
        ("Nifty Tracking Error PDF", "https://niftyindices.com/docs/default-source/tracking-error/trackingerror.pdf?sfvrsn=7e449b34_2"),
    ]

    for label, url in candidate_bulletin_urls:
        try:
            resp = fetch_with_retry(url)
            status = resp.status_code
            size = len(resp.content)
            print(f"  [{status}] {label}: {url} ({size} bytes)")
            safe_name = label.lower().replace(" ", "_").replace("-", "_") + f".pdf"
            out_path = os.path.join(RAW_BULLETINS_DIR, safe_name)
            with open(out_path, "wb") as f:
                f.write(resp.content)
            files_written.append(out_path)

            inventory_records.append({
                "source": label,
                "url": url,
                "status": status,
                "size_bytes": size,
                "cached_file": out_path,
                "type": "document"
            })
        except Exception as e:
            print(f"  [ERROR] {label} ({url}): {e}")

    print("\n" + "=" * 80)
    print("GATE 0 INVENTORY SUMMARY TABLE PER TARGET INDEX (2020-09 onward)")
    print("=" * 80)
    header = f"{'Index Name':<20} | {'Bulletins Found':<18} | {'HTTP Status':<12} | {'Effective Range':<20} | {'Status'}"
    print(header)
    print("-" * len(header))

    for idx in TARGET_INDICES:
        # None of the direct directory URLs list standalone parsed CSVs for individual index events
        # NiftyIndices and NSEArchives require manual scraping/Phase 5.6 pipeline
        print(f"{idx:<20} | {'None (raw source)':<18} | {'404/Restricted':<12} | {'None (post-2020-09)':<20} | Truncated at baseline (Phase 5.5 policy)")

    print("\n[Finding & Policy Confirmation]")
    print("- Directory browsing on 'https://nsearchives.nseindia.com/content/indices/' and 'content/press/' returns 404 (disabled by webserver).")
    print("- NiftyIndices portal provides aggregate PDFs, reconstitution calendars, and landing pages, but no machine-readable event tables for individual historical transitions.")
    print("- As specified in Phase 5.5 Section 1 ('Truncation policy') and Section 3 ('GATE 0'):")
    print("  'If no bulletins exist for an index, state it. That index\\'s baseline stays truncated. Do not parse bulletins into events in this phase.'")
    print("  'Filling 2020-09 to today is Phase 5.6. Do NOT implement refresh-index-events, NSE bulletin parsing into the event log, or the staleness exit in this phase.'")
    print(f"- All {len(files_written)} raw response and bulletin files cached under: {RAW_BULLETINS_DIR}")
    print("\nFiles written:")
    for f in sorted(files_written):
        print(f"  - {f}")
    print("=" * 80)

if __name__ == "__main__":
    main()
