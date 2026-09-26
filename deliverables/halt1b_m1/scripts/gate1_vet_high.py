#!/usr/bin/env python3
"""
deliverables/halt1b_m1/scripts/gate1_vet_high.py
Phase 5.5.M-1 — Gate 1: High-Confidence Tier Vetting & Application

1. Inspects data/symbol_map_review_high.csv for candidates matching pending NIFTY500 scrips.
2. Verifies:
   - ISIN presence in data/raw_reference/EQUITY_L.csv
   - Name similarity >= 0.90
   - No cross-entity name mismatch flags
3. Sets review_action = 'approved' and populates approval_note citing verified evidence.
4. Executes scripts/apply_symbol_map_review.py to update data/symbol_map.parquet and log changes.
5. Saves stdout to deliverables/halt1b_m1/raw/gate1_apply_high.txt.
"""

import sys
import os
import subprocess
import datetime
import pandas as pd
from pathlib import Path

BASE_DIR = Path("/sdcard/Documents/Project MIP")
DELIV_DIR = BASE_DIR / "deliverables/halt1b_m1"
RAW_DIR = DELIV_DIR / "raw"
DATA_CSV_DIR = DELIV_DIR / "data_csv"

PENDING_CSV = DELIV_DIR / "data_csv/nifty500_pending_scrips_ranked.csv"
REVIEW_HIGH_CSV = BASE_DIR / "data/symbol_map_review_high.csv"
EQUITY_L_CSV = BASE_DIR / "data/raw_reference/EQUITY_L.csv"

def main():
    print("=" * 80)
    print("PHASE 5.5.M-1 — GATE 1: HIGH-CONFIDENCE TIER VETTING & APPLICATION")
    print(f"Timestamp: {datetime.datetime.now(datetime.timezone.utc).isoformat()}")
    print("=" * 80)

    # 1. Load pending scrips and EQUITY_L reference
    pending_df = pd.read_csv(PENDING_CSV)
    pending_scrips = set(pending_df["scrip_name"])
    print(f"Loaded {len(pending_scrips)} pending NIFTY500 constituent scrips.")

    eq = pd.read_csv(EQUITY_L_CSV)
    eq.columns = [c.strip() for c in eq.columns]
    eq_isins = set(eq["ISIN NUMBER"].str.strip())
    print(f"Loaded {len(eq_isins):,} active ISINs from EQUITY_L.")

    # 2. Load review_high.csv
    review_high = pd.read_csv(REVIEW_HIGH_CSV, dtype=str).fillna("")
    print(f"Loaded review_high: {len(review_high)} candidate rows.")

    approved_count = 0
    approved_details = []

    for idx, row in review_high.iterrows():
        scrip = row["scrip_name"].strip()
        if scrip not in pending_scrips:
            continue

        isin = row["isin"].strip()
        sim_val = float(row["name_similarity"]) if row["name_similarity"] else 0.0
        flags = row["flags"].strip()
        sym = row["symbol"].strip()

        # Vetting criteria:
        # - ISIN verified in EQUITY_L
        # - name_similarity >= 0.90
        # - No name_mismatch flag
        # - Exclude known ticker anomalies like Tata Motors -> TMCV
        if isin in eq_isins and sim_val >= 0.90 and "name_mismatch" not in flags:
            if scrip == "Tata Motors Ltd." and sym != "TATAMOTORS":
                continue

            review_high.at[idx, "review_action"] = "approved"
            note = f"Verified exact ISIN {isin} in EQUITY_L; name similarity {sim_val:.2f}; official NSE constituent."
            review_high.at[idx, "approval_note"] = note
            approved_count += 1
            approved_details.append({
                "scrip_name": scrip,
                "symbol": sym,
                "isin": isin,
                "similarity": sim_val,
                "flags": flags,
                "approval_note": note
            })

    print(f"\nVetted and marked {approved_count} high-confidence scrips as 'approved'.")

    # Save updated review_high.csv
    review_high.to_csv(REVIEW_HIGH_CSV, index=False)
    print(f"Saved updated review file: {REVIEW_HIGH_CSV}")

    # Export vetted summary CSV
    vetted_csv = DATA_CSV_DIR / "gate1_vetted_high_summary.csv"
    pd.DataFrame(approved_details).to_csv(vetted_csv, index=False)
    print(f"Exported vetted summary: {vetted_csv} ({approved_count} rows)")

    # 3. Execute apply_symbol_map_review.py
    print("\n--- Executing scripts/apply_symbol_map_review.py ---")
    cmd = ["/usr/bin/python3", "scripts/apply_symbol_map_review.py", str(REVIEW_HIGH_CSV)]
    res = subprocess.run(cmd, cwd=str(BASE_DIR), capture_output=True, text=True)

    print(res.stdout)
    if res.stderr:
        print("STDERR:", res.stderr, file=sys.stderr)

    assert res.returncode == 0, f"apply_symbol_map_review.py failed with code {res.returncode}"

    print("=" * 80)
    print(f"GATE 1 EXIT: SUCCESS — {approved_count} HIGH-CONFIDENCE SCRIPS APPROVED AND APPLIED")
    print("=" * 80)

if __name__ == "__main__":
    main()
