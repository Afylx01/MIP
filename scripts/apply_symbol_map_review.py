#!/usr/bin/env python3
"""
scripts/apply_symbol_map_review.py <review_csv_path>
Hardened Review Application Tool for Gate 2b:
- Reads 'review_action' only; ignores 'status'.
- Refuses whole file if any review_action is unrecognized. Refuses to accept 'auto'.
- Refuses to approve a row with empty symbol or ISIN.
- Refuses to approve a row that has ANY flag unless approval_note is non-empty.
- If override is given, override symbol/ISIN must exist in EQUITY_L or override_evidence must be non-empty;
  then resolution_method = 'user_override'.
- Verifies each CSV row's (scrip_name, symbol, isin) matches the map row; refuses on mismatch.
- If zero changes result, exits without rewriting the parquet and says so.
- Before write: backs up map and appends every change to data/symbol_map_changes.parquet
  (timestamp, scrip_name, old_status, new_status, note). Prints applied counts per tier.
"""

import sys
import os
import shutil
import datetime
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

SYMBOL_MAP_PATH = "data/symbol_map.parquet"
CHANGES_PATH = "data/symbol_map_changes.parquet"
EQUITY_L_PATH = "data/raw_reference/EQUITY_L.csv"

VALID_ACTIONS = {"proposed", "approved", "rejected"}

def main():
    print("=" * 80)
    print("APPLY SYMBOL MAP REVIEW TOOL (HARDENED)")
    print("=" * 80)

    if len(sys.argv) < 2:
        print("Usage: python3 scripts/apply_symbol_map_review.py <review_csv_path>")
        sys.exit(1)

    csv_path = sys.argv[1]
    if not os.path.exists(csv_path):
        print(f"REFUSAL: Review file '{csv_path}' not found!")
        sys.exit(1)

    print(f"Reading review file: {csv_path}")
    review_df = pd.read_csv(csv_path, dtype=str).fillna("")

    if "review_action" not in review_df.columns:
        print("REFUSAL: Required column 'review_action' missing from review CSV!")
        sys.exit(1)

    # 1. Refusal check: review_action validation
    for idx, row in review_df.iterrows():
        action = row["review_action"].strip().lower()
        if action == "auto":
            print(f"REFUSAL: Row {idx + 2} specifies review_action='auto'. Cannot manually assign 'auto' status via review!")
            sys.exit(2)
        if action not in VALID_ACTIONS:
            print(f"REFUSAL: Row {idx + 2} has unrecognized review_action='{action}'. Must be one of {sorted(list(VALID_ACTIONS))}!")
            sys.exit(2)

    # Load EQUITY_L for override validation
    eq_df = pd.read_csv(EQUITY_L_PATH)
    eq_df.columns = [c.strip() for c in eq_df.columns]
    eq_symbols = set(eq_df["SYMBOL"].str.strip().dropna())
    eq_isins = set(eq_df["ISIN NUMBER"].str.strip().dropna())

    # Load existing symbol map
    if not os.path.exists(SYMBOL_MAP_PATH):
        print(f"REFUSAL: Symbol map '{SYMBOL_MAP_PATH}' not found!")
        sys.exit(1)

    map_df = pd.read_parquet(SYMBOL_MAP_PATH)
    map_dict = {r["scrip_name"]: dict(r) for _, r in map_df.iterrows()}

    # 2. Key matching & Row approval validation
    pending_updates = []
    
    for idx, row in review_df.iterrows():
        scrip = row["scrip_name"].strip()
        action = row["review_action"].strip().lower()
        csv_sym = row.get("symbol", "").strip()
        csv_isin = row.get("isin", "").strip()

        if scrip not in map_dict:
            print(f"REFUSAL: Scrip '{scrip}' in review CSV row {idx + 2} not found in symbol map!")
            sys.exit(3)

        target = map_dict[scrip]
        
        # Verify key match (scrip_name, symbol, isin)
        map_sym = str(target.get("symbol", "") or "").strip()
        map_isin = str(target.get("isin", "") or "").strip()
        
        if (csv_sym != map_sym) or (csv_isin != map_isin):
            print(f"REFUSAL: Key mismatch on row {idx + 2} for '{scrip}'!")
            print(f"  CSV key: (symbol='{csv_sym}', isin='{csv_isin}')")
            print(f"  Map key: (symbol='{map_sym}', isin='{map_isin}')")
            sys.exit(3)

        override_sym = row.get("override_symbol", "").strip()
        override_isin = row.get("override_isin", "").strip()
        override_ev = row.get("override_evidence", "").strip()
        note = row.get("approval_note", "").strip()

        # Check approval constraints
        if action == "approved":
            effective_sym = override_sym if override_sym else map_sym
            effective_isin = override_isin if override_isin else map_isin

            # Refuse empty symbol or ISIN
            if not effective_sym or not effective_isin:
                print(f"REFUSAL: Cannot approve row {idx + 2} ('{scrip}') with empty symbol or ISIN!")
                sys.exit(4)

            # Refuse flagged row without approval_note
            flags = str(target.get("flags", "") or "").strip()
            if flags and not note:
                print(f"REFUSAL: Cannot approve flagged row {idx + 2} ('{scrip}') without an approval_note!")
                print(f"  Active flags: {flags}")
                sys.exit(4)

            # Check override validity
            if override_sym or override_isin:
                in_equity_l = (override_sym in eq_symbols) and (override_isin in eq_isins)
                if not in_equity_l and not override_ev:
                    print(f"REFUSAL: Override symbol/ISIN on row {idx + 2} ('{scrip}') not in EQUITY_L and 'override_evidence' is empty!")
                    sys.exit(4)

        if action in ("approved", "rejected"):
            if action != target["status"] or override_sym or override_isin:
                pending_updates.append({
                    "scrip_name": scrip,
                    "new_action": action,
                    "override_sym": override_sym,
                    "override_isin": override_isin,
                    "override_ev": override_ev,
                    "note": note,
                    "tier": target.get("confidence", "low"),
                    "old_status": target["status"],
                })

    # 3. Check for zero changes
    if not pending_updates:
        print("\nNotice: Review CSV produced ZERO status or mapping changes.")
        print("Exiting without rewriting symbol map parquet file.")
        sys.exit(0)

    # 4. Backup before writing
    ts_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"data/symbol_map_backup_{ts_str}.parquet"
    shutil.copyfile(SYMBOL_MAP_PATH, backup_path)
    print(f"\nCreated backup at: {backup_path}")

    # 5. Apply changes
    changes_records = []
    now_iso = datetime.datetime.now().isoformat()
    tier_counts = {"high": 0, "medium": 0, "low": 0}

    for u in pending_updates:
        scrip = u["scrip_name"]
        target = map_dict[scrip]
        old_status = target["status"]
        new_status = u["new_action"]

        if u["override_sym"]:
            target["symbol"] = u["override_sym"]
            target["resolution_method"] = "user_override"
        if u["override_isin"]:
            target["isin"] = u["override_isin"]
            target["resolution_method"] = "user_override"

        target["status"] = new_status
        target["mapping_status"] = new_status
        tier_counts[u["tier"]] = tier_counts.get(u["tier"], 0) + 1

        changes_records.append({
            "timestamp": now_iso,
            "scrip_name": scrip,
            "old_status": old_status,
            "new_status": new_status,
            "note": u["note"],
        })

    # Write updated map
    updated_rows = list(map_dict.values())
    updated_df = pd.DataFrame(updated_rows)
    pq.write_table(pa.Table.from_pandas(updated_df), SYMBOL_MAP_PATH)
    print(f"Updated {SYMBOL_MAP_PATH} successfully.")

    # Append to changes log
    changes_df = pd.DataFrame(changes_records)
    if os.path.exists(CHANGES_PATH):
        old_changes = pd.read_parquet(CHANGES_PATH)
        changes_df = pd.concat([old_changes, changes_df], ignore_index=True)
    pq.write_table(pa.Table.from_pandas(changes_df), CHANGES_PATH)
    print(f"Appended {len(pending_updates)} change record(s) to {CHANGES_PATH}.")

    print("\n--- Changes Applied by Tier ---")
    for t, count in tier_counts.items():
        print(f"  {t.upper()}: {count}")

if __name__ == "__main__":
    main()
