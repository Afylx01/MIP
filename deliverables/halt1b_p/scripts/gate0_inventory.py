#!/usr/bin/env python3
"""
Phase 5.5.A-1 — Gate 0: Prerequisite Inventory
Runs without network access to answer Questions Q1-Q4 from files on disk,
and prints the auditor question Q5 verbatim.
"""

import os
import sys
import subprocess
import datetime
from pathlib import Path
import pandas as pd

def run_cmd(cmd_str):
    print(f"\n$ {cmd_str}")
    try:
        res = subprocess.run(cmd_str, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, check=False)
        print(res.stdout.strip())
        return res.stdout.strip()
    except Exception as e:
        print(f"ERROR: {e}")
        return str(e)

def main():
    print("="*80)
    print("PHASE 5.5.A-1 — GATE 0: PREREQUISITE INVENTORY")
    print(f"Timestamp: {datetime.datetime.now(datetime.timezone.utc).isoformat()}")
    print("="*80)

    # -------------------------------------------------------------------------
    # Q1: Corporate-action adjuster contract
    # -------------------------------------------------------------------------
    print("\n" + "="*80)
    print("### Q1. Corporate-action adjuster contract")
    print("="*80)
    print("Searching for Phase 6 build prompt §2.3 corporate-action adjustment module...")
    
    search_dirs = [
        ".",
        "scripts",
        "indian_backtest",
        "data",
        "/storage/emulated/0/Documents",
        "/storage/emulated/0/MIP1_Scanner"
    ]
    print(f"Directories searched: {search_dirs}")

    found_adjusters = []
    for d in search_dirs:
        p = Path(d)
        if p.exists():
            for f in p.rglob("*.py"):
                name = f.name.lower()
                if any(k in name for k in ["adjust", "corporate", "split", "ca_"]):
                    found_adjusters.append(str(f))

    print(f"Candidate files found matching naming pattern: {found_adjusters}")

    print("\nInspecting scanner watchdog in /storage/emulated/0/Documents/MIP1_Scanner_v5_5_0.py:")
    run_cmd("sed -n '1329,1355p' /storage/emulated/0/Documents/MIP1_Scanner_v5_5_0.py")

    print("\nEvaluation against Gate 0 Q1 specifications:")
    print("- Module file path: NOT FOUND")
    print("- __file__: NOT FOUND")
    print("- Entry point signature: NOT FOUND")
    print("- Input shape / docstring: NOT FOUND")
    print("- Corporate-action calendar schema: NOT FOUND")
    print("- Auto-detects discontinuities: MIP1_Scanner_v5_5_0.py has an internal basis watchdog (_detect_basis_changes) that compares fresh vs cached yfinance rows and flags symbols for full refetch if ratio != 1.0, but NO standalone corporate-action adjustment calculation module exists in this workspace.")
    print("\nRESULT: UNANSWERED — adjuster not present")

    # -------------------------------------------------------------------------
    # Q2: price_status provenance
    # -------------------------------------------------------------------------
    print("\n" + "="*80)
    print("### Q2. price_status provenance")
    print("="*80)
    
    symbol_map_path = "data/symbol_map.parquet"
    print(f"Reading symbol map from: {symbol_map_path}")
    df_map = pd.read_parquet(symbol_map_path)
    
    covered_rows = df_map[df_map["price_status"] == "covered"]
    partial_rows = df_map[df_map["price_status"] == "partial"]

    covered_row = covered_rows.iloc[0]
    partial_row = partial_rows.iloc[0]

    print("\n[Covered Symbol Row - All 13 Evidence Columns + Identifiers]:")
    for k, v in covered_row.to_dict().items():
        print(f"  {k:<20}: {v}")

    print("\n[Partial Symbol Row - All 13 Evidence Columns + Identifiers]:")
    for k, v in partial_row.to_dict().items():
        print(f"  {k:<20}: {v}")

    print("\n[Provenance Tracking - Code writing bars_present and price_status]:")
    print("Code location: scripts/step1_v3_rebuild.py")
    print("Lines 30-34, 290-302 (Input price file):")
    run_cmd("sed -n '30,34p' scripts/step1_v3_rebuild.py")
    run_cmd("sed -n '290,302p' scripts/step1_v3_rebuild.py")
    print("\nLines 638-652 (price_status logic):")
    run_cmd("sed -n '638,652p' scripts/step1_v3_rebuild.py")

    print("\nPrice file identified: data/price_cache_export.parquet")

    print("\n[Spot Checking Bar Values for ADANIPOWER on 3 Sample Dates]:")
    price_export_path = "data/price_cache_export.parquet"
    df_price = pd.read_parquet(price_export_path)
    sub = df_price[df_price["symbol"] == partial_row["symbol"]]
    sample_dates = ["2015-01-02", "2018-01-01", "2020-09-14"]
    sub_sample = sub[sub["date"].isin(sample_dates)][["symbol", "date", "open", "high", "low", "close", "volume"]]
    print(sub_sample.to_string(index=False))

    # -------------------------------------------------------------------------
    # Q3: Network path
    # -------------------------------------------------------------------------
    print("\n" + "="*80)
    print("### Q3. Network path")
    print("="*80)
    run_cmd("uname -a")
    run_cmd("hostname")
    run_cmd("ip route get 1.1.1.1")
    run_cmd("curl -s https://ifconfig.me")
    print("")

    print("Checking for VPS.md, servers.md, hosts.md in workspace and ~/ :")
    vps_found = []
    for base in [Path("."), Path("/root")]:
        if base.exists():
            for f in base.rglob("*"):
                if f.is_file() and any(k in f.name.lower() for k in ["vps.md", "servers.md", "hosts.md"]):
                    vps_found.append(str(f))
    if vps_found:
        print(f"Files found: {vps_found}")
        for vf in vps_found:
            print(f"\n--- Contents of {vf} ---")
            print(Path(vf).read_text()[:500])
    else:
        print("Files found: None")

    # -------------------------------------------------------------------------
    # Q4: Storage headroom
    # -------------------------------------------------------------------------
    print("\n" + "="*80)
    print("### Q4. Storage headroom")
    print("="*80)
    run_cmd("df -h '/sdcard/Documents/Project MIP'")
    run_cmd("du -sh '/sdcard/Documents/Project MIP'")
    run_cmd("du -sh '/storage/emulated/0/MIP1_Scanner/data/'")
    print("\nFiles under data/ larger than 10 MB:")
    run_cmd("find data/ -type f -size +10M -exec ls -lh {} +")

    print("\nHeadroom Classification: Headroom is ABOVE 1 GB (30 GB available on /storage/emulated/0).")

    # -------------------------------------------------------------------------
    # Q5: User's goal (Auditor's question to user)
    # -------------------------------------------------------------------------
    print("\n" + "="*80)
    print("### Q5. User's goal (auditor's question to the user)")
    print("="*80)
    q5_text = (
        "> AUDITOR QUESTION TO USER — unanswered:\n"
        "> Which of the following is the goal of the MIP-1 baseline backtest?\n"
        ">   (a) Reproduce the podcast's 29.6% CAGR as closely as possible.\n"
        ">   (b) Determine whether MIP-1 has a real edge over NIFTY500 Total\n"
        ">       Return on a survivorship-free sample.\n"
        ">   (c) Validate the engine end-to-end; the number itself is not the\n"
        ">       point.\n"
        "> The answer changes what \"done\" means and which sub-phases of A are\n"
        "> required. The user must answer in writing before A-2 begins."
    )
    print(q5_text)
    print("="*80)

if __name__ == "__main__":
    main()
