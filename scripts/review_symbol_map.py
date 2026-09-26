#!/usr/bin/env python3
"""
scripts/review_symbol_map.py
Hardened Review Tool for Gate 2b:
- Includes ONLY status = 'proposed' rows in review CSVs.
- Writes status = 'unresolved' rows to a separate data/symbol_map_unresolved.csv (cannot be approved).
- Groups proposed rows by confidence tier (high / medium / low) and writes data/symbol_map_review_<tier>.csv.
- Includes ALL evidence columns from Step 3c plus editable columns:
    review_action (default: 'proposed', values: 'proposed|approved|rejected'),
    override_symbol, override_isin, override_evidence, approval_note
- The 'status' column in the CSV is read-only.
- Never auto-approves.
"""

import os
import sys
import pandas as pd

SYMBOL_MAP_PATH = "data/symbol_map.parquet"
OUTPUT_DIR = "data"

def main():
    print("=" * 80)
    print("STEP 4 — REVIEW TOOLING: GENERATING REVIEW CSVS")
    print("=" * 80)

    if not os.path.exists(SYMBOL_MAP_PATH):
        raise FileNotFoundError(f"{SYMBOL_MAP_PATH} not found!")

    df = pd.read_parquet(SYMBOL_MAP_PATH)
    print(f"Total symbol map rows: {len(df)}")
    print("Current status counts:")
    for s, c in df["status"].value_counts().items():
        print(f"  {s:<15}: {c}")

    # 1. Unresolved rows go to separate CSV for reference
    unresolved = df[df["status"] == "unresolved"].copy()
    unresolved_path = os.path.join(OUTPUT_DIR, "symbol_map_unresolved.csv")
    unresolved.to_csv(unresolved_path, index=False)
    print(f"\nUnresolved rows count: {len(unresolved)}")
    print(f"Written unresolved reference CSV to: {unresolved_path}")

    # 2. Proposed rows go to tier review CSVs
    proposed = df[df["status"] == "proposed"].copy()
    print(f"\nProposed rows requiring review: {len(proposed)}")

    # Editable review columns
    editable_cols = ["review_action", "override_symbol", "override_isin", "override_evidence", "approval_note"]

    tiers = ["high", "medium", "low"]
    for tier in tiers:
        sub = proposed[proposed["confidence"] == tier].copy()
        out_csv = os.path.join(OUTPUT_DIR, f"symbol_map_review_{tier}.csv")
        
        # Add editable columns
        sub["review_action"] = "proposed"
        sub["override_symbol"] = ""
        sub["override_isin"] = ""
        sub["override_evidence"] = ""
        sub["approval_note"] = ""

        # Reorder columns: scrip_name, status (read-only), review_action, candidate info, evidence columns, override fields
        col_order = [
            "scrip_name", "status", "review_action", "symbol", "isin", "confidence", "resolution_method",
            "flags", "coverage_pct", "bars_present", "bars_expected", "price_first_bar", "price_last_bar",
            "eq_name", "eq_series", "eq_listing_date", "isin_in_equity_l", "name_similarity", "first_token_match",
            "evidence_source", "override_symbol", "override_isin", "override_evidence", "approval_note"
        ]
        sub = sub[col_order]
        sub.to_csv(out_csv, index=False)
        print(f"\n[Tier: {tier.upper()}] — Count: {len(sub)}")
        print(f"  Written to: {out_csv}")
        print("  First 5 entries:")
        for _, r in sub.head(5).iterrows():
            print(f"    - Scrip: '{r['scrip_name']:<35}' | Sym: '{r['symbol']:<10}' | Flags: {r['flags'][:40]}")

    print("\n" + "=" * 80)
    print("REVIEW CSV FILES GENERATED:")
    print("  - data/symbol_map_unresolved.csv (reference only, cannot be approved)")
    print("  - data/symbol_map_review_high.csv")
    print("  - data/symbol_map_review_medium.csv")
    print("  - data/symbol_map_review_low.csv")
    print("Note: The 'status' column is read-only. Reviewers must edit 'review_action' and provide 'approval_note' if flagged.")
    print("=" * 80)

if __name__ == "__main__":
    main()
