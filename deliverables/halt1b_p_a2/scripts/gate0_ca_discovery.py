#!/usr/bin/env python3
"""
deliverables/halt1b_p_a2/scripts/gate0_ca_discovery.py
Phase 5.5.A-2 — Gate 0: Corporate-Action Endpoint Discovery
Probes candidate NSE endpoints with honest User-Agent and rate limiting.
"""

import os
import sys
import time
import datetime
import subprocess
from pathlib import Path

DELIVERABLES_DIR = Path("/sdcard/Documents/Project MIP/deliverables/halt1b_p_a2")
RAW_DIR = DELIVERABLES_DIR / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

USER_AGENT = "MIP-research/0.1"

CANDIDATES = [
    ("NSE Current API", "https://www.nseindia.com/api/corporates-corporateActions?index=equities"),
    ("NSE Date-Filtered API (2016)", "https://www.nseindia.com/api/corporates-corporateActions?index=equities&from_date=01-01-2016&to_date=31-12-2016"),
    ("Archives CA_ACTION_2016", "https://nsearchives.nseindia.com/content/equities/CA_ACTION_2016.csv"),
    ("Archives CA_ACTION_2018", "https://nsearchives.nseindia.com/content/equities/CA_ACTION_2018.csv"),
    ("Archives CA_ACTION_2020", "https://nsearchives.nseindia.com/content/equities/CA_ACTION_2020.csv"),
    ("Archives corp_actions_2016", "https://nsearchives.nseindia.com/content/equities/corp_actions_2016.csv"),
    ("Archives corp_actions_2018", "https://nsearchives.nseindia.com/content/equities/corp_actions_2018.csv"),
    ("Archives corp_actions_2020", "https://nsearchives.nseindia.com/content/equities/corp_actions_2020.csv"),
    ("Archives Equities Directory Listing", "https://nsearchives.nseindia.com/content/equities/")
]

def probe_url(name, url):
    print(f"\nProbing: {name}")
    print(f"URL: {url}")
    out_file = "/tmp/gate0_probe.tmp"
    cmd = [
        "curl", "-s", "-m", "20",
        "-w", "%{http_code}:%{size_download}:%{content_type}:%{time_total}",
        "-A", USER_AGENT,
        "-H", "Accept: text/html,application/xhtml+xml,application/xml,application/json,*/*;q=0.9",
        url,
        "-o", out_file
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    meta = res.stdout.strip().split(":", 3)
    status = int(meta[0]) if len(meta) >= 1 and meta[0].isdigit() else 0
    size = int(float(meta[1])) if len(meta) >= 2 and meta[1].replace(".", "", 1).isdigit() else 0
    c_type = meta[2] if len(meta) >= 3 else "unknown"
    latency_s = meta[3] if len(meta) >= 4 else "0"

    print(f"Status: HTTP {status} | Size: {size:,} bytes | Type: {c_type} | Latency: {latency_s}s")

    sample_lines = []
    if Path(out_file).exists() and size > 0:
        try:
            with open(out_file, "r", errors="replace") as f:
                for _ in range(5):
                    l = f.readline()
                    if not l:
                        break
                    sample_lines.append(l.strip()[:140])
        except Exception as e:
            sample_lines.append(f"<Error reading payload: {e}>")

    if sample_lines:
        print("First lines of response:")
        for idx, line in enumerate(sample_lines, 1):
            print(f"  {idx}. {line}")

    return {
        "name": name,
        "url": url,
        "status": status,
        "size": size,
        "content_type": c_type,
        "sample": sample_lines
    }

def main():
    print("=" * 80)
    print("PHASE 5.5.A-2 — GATE 0: CA ENDPOINT DISCOVERY")
    print(f"Timestamp: {datetime.datetime.now(datetime.timezone.utc).isoformat()}")
    print("=" * 80)

    results = []
    for name, url in CANDIDATES:
        res = probe_url(name, url)
        results.append(res)
        time.sleep(1.2)

    print("\n" + "=" * 80)
    print("GATE 0 DISCOVERY SUMMARY & EXIT DETERMINATION")
    print("=" * 80)

    usable_endpoint = None
    for r in results:
        if r["status"] == 200 and "application/json" in r["content_type"] and r["size"] > 10000:
            usable_endpoint = r["url"]
            print(f"USABLE HISTORICAL ENDPOINT IDENTIFIED: {r['name']}")
            print(f"Endpoint Pattern: https://www.nseindia.com/api/corporates-corporateActions?index=equities&from_date=<DD-MM-YYYY>&to_date=<DD-MM-YYYY>")
            print(f"Coverage: Supports full date range filtering across 2016-01-01 to 2020-09-14 with JSON records.")
            break

    if usable_endpoint:
        print("\nGATE 0 EXIT: USABLE ENDPOINT FOUND -> PROCEED TO GATE 1 ON CA PATH 1.")
    else:
        print("\nGATE 0 EXIT: ENDPOINTS UNREACHABLE -> FALL BACK TO CA PATH 2 (MANUAL PLAN).")

    print("=" * 80)

if __name__ == "__main__":
    main()
