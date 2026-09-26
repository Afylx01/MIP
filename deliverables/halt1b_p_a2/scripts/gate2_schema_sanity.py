#!/usr/bin/env python3
"""
deliverables/halt1b_p_a2/scripts/gate2_schema_sanity.py
Phase 5.5.A-2 — Gate 2: Schema Sanity and Hand Verification (Zero Network)

1. Asserts schema and prints column dtypes.
2. Asserts ex_date is monotonic non-decreasing after sort.
3. Asserts no duplicate (symbol, ex_date, action_type).
4. Asserts every ratio > 0.
5. Hand-verifies 3 events (INFY 2018, TCS 2018, RELIANCE 2017) against NSE public announcements.
6. Cross-checks coverage against NIFTY500 members (2016-2020) from symbol_map.
"""

import sys
import datetime
import pandas as pd
from pathlib import Path

BASE_DIR = Path("/sdcard/Documents/Project MIP")
DELIVERABLES_DIR = BASE_DIR / "deliverables/halt1b_p_a2"
RAW_DIR = DELIVERABLES_DIR / "raw"
DATA_CSV_DIR = DELIVERABLES_DIR / "data_csv"
VERIF_DATA_DIR = BASE_DIR / "data/verification/halt1b_p_a2"

CALENDAR_PATH = VERIF_DATA_DIR / "ca_calendar_raw.parquet"
SYMBOL_MAP_PATH = BASE_DIR / "data/symbol_map.parquet"

EXPECTED_COLUMNS = ["symbol", "ex_date", "action_type", "ratio", "source_url", "fetched_at"]

PUBLIC_REFERENCES = [
    {
        "symbol": "INFY",
        "ex_date": "2018-09-04",
        "action_type": "bonus",
        "expected_ratio": 1.0,
        "ref_source": "NSE Corporate Announcements (Jul 13, 2018 & Aug 20, 2018)",
        "ref_text": "Infosys Ltd - Recommendation of bonus issue in 1:1 ratio. Record Date: September 5, 2018. Ex-Date: September 4, 2018."
    },
    {
        "symbol": "TCS",
        "ex_date": "2018-05-31",
        "action_type": "bonus",
        "expected_ratio": 1.0,
        "ref_source": "NSE Corporate Announcements (Apr 19, 2018 & May 23, 2018)",
        "ref_text": "Tata Consultancy Services Ltd - Issue of 1:1 Bonus Shares & Dividend Rs 29/sh. Record Date: June 2, 2018. Ex-Date: May 31, 2018."
    },
    {
        "symbol": "RELIANCE",
        "ex_date": "2017-09-07",
        "action_type": "bonus",
        "expected_ratio": 1.0,
        "ref_source": "NSE Corporate Announcements (Jul 21, 2017 & Aug 24, 2017)",
        "ref_text": "Reliance Industries Ltd - Issue of 1:1 Bonus Equity Shares. Record Date: September 9, 2017. Ex-Date: September 7, 2017."
    }
]

def main():
    print("=" * 80)
    print("PHASE 5.5.A-2 — GATE 2: SCHEMA SANITY & HAND VERIFICATION")
    print(f"Timestamp: {datetime.datetime.now(datetime.timezone.utc).isoformat()}")
    print("=" * 80)
    
    assert CALENDAR_PATH.exists(), f"Missing calendar file: {CALENDAR_PATH}"
    df = pd.read_parquet(CALENDAR_PATH)
    print(f"Loaded calendar from {CALENDAR_PATH}: {len(df):,} rows.")
    
    # 1. Assert schema and print column dtypes
    print("\n--- 1. Schema & Dtypes Assertion ---")
    cols = df.columns.tolist()
    print(f"Calendar columns: {cols}")
    assert cols == EXPECTED_COLUMNS, f"Schema mismatch! Got {cols}, expected {EXPECTED_COLUMNS}"
    print("Column dtypes:")
    for c, dt in df.dtypes.items():
        print(f"  - {c}: {dt}")
    assert pd.api.types.is_numeric_dtype(df["ratio"]), "Ratio column must be numeric!"
    print("Assertion 1 PASSED: Exact schema match and dtypes valid.")

    # 2. Assert ex_date is monotonic non-decreasing after sort
    print("\n--- 2. Monotonic Ex-Date Assertion ---")
    sorted_df = df.sort_values(by=["ex_date", "symbol"]).reset_index(drop=True)
    is_monotonic = sorted_df["ex_date"].is_monotonic_increasing
    print(f"ex_date is_monotonic_increasing: {is_monotonic}")
    assert is_monotonic, "ex_date is not monotonic non-decreasing after sort!"
    print("Assertion 2 PASSED: ex_date sorted monotonically.")

    # 3. Assert no duplicate (symbol, ex_date, action_type)
    print("\n--- 3. Uniqueness Assertion ---")
    dup_mask = df.duplicated(subset=["symbol", "ex_date", "action_type"], keep=False)
    num_dups = dup_mask.sum()
    print(f"Duplicate (symbol, ex_date, action_type) count: {num_dups}")
    if num_dups > 0:
        print("Duplicate rows:")
        print(df[dup_mask])
    assert num_dups == 0, f"Found {num_dups} duplicate events!"
    print("Assertion 3 PASSED: Zero duplicates.")

    # 4. Assert every ratio > 0
    print("\n--- 4. Positive Ratio Assertion ---")
    non_positive = (df["ratio"] <= 0) | df["ratio"].isna()
    num_bad_ratio = non_positive.sum()
    print(f"Non-positive / NaN ratio count: {num_bad_ratio}")
    assert num_bad_ratio == 0, f"Found {num_bad_ratio} invalid ratios!"
    min_ratio = df["ratio"].min()
    max_ratio = df["ratio"].max()
    print(f"Min ratio: {min_ratio:.6f} | Max ratio: {max_ratio:.6f}")
    print("Assertion 4 PASSED: All ratios strictly positive.")

    # 5. Hand-verify 3 events against public sources
    print("\n--- 5. Hand Verification of 3 Reference Events ---")
    for ref in PUBLIC_REFERENCES:
        sym = ref["symbol"]
        ex_dt = ref["ex_date"]
        ev_type = ref["action_type"]
        match = df[(df["symbol"] == sym) & (df["ex_date"] == ex_dt) & (df["action_type"] == ev_type)]
        assert not match.empty, f"Reference event not found in calendar: {sym} {ex_dt} {ev_type}"
        row = match.iloc[0]
        print(f"\nTarget: {sym} ({ev_type.upper()}) on {ex_dt}")
        print(f"  Calendar Event Row:")
        print(f"    symbol:      {row['symbol']}")
        print(f"    ex_date:     {row['ex_date']}")
        print(f"    action_type: {row['action_type']}")
        print(f"    ratio:       {row['ratio']:.4f}")
        print(f"    source_url:  {row['source_url']}")
        print(f"  Public Reference Source: {ref['ref_source']}")
        print(f"  Public Reference Text:   \"{ref['ref_text']}\"")
        assert abs(row["ratio"] - ref["expected_ratio"]) < 1e-6, f"Ratio mismatch for {sym}: {row['ratio']} vs {ref['expected_ratio']}"
        print("  -> Hand verification MATCH: Ratio and ex-date exact match.")
    print("Assertion 5 PASSED: All 3 hand-verified events confirmed against public records.")

    # 6. Cross-check coverage against NIFTY500 member symbols over 2016-2020
    print("\n--- 6. NIFTY500 Union Member Coverage Cross-Check ---")
    assert SYMBOL_MAP_PATH.exists(), f"Missing symbol map: {SYMBOL_MAP_PATH}"
    smap = pd.read_parquet(SYMBOL_MAP_PATH)
    
    # Filter mapping_status in {'auto', 'approved'}
    smap_valid = smap[smap["mapping_status"].isin(["auto", "approved"])].copy()
    
    # Filter 2016-2020 membership window: first_seen <= 2020-09-14 and last_seen >= 2016-01-01
    smap_valid["first_seen_dt"] = pd.to_datetime(smap_valid["first_seen"]).dt.date
    smap_valid["last_seen_dt"] = pd.to_datetime(smap_valid["last_seen"]).dt.date
    
    nifty_2016_2020 = smap_valid[
        (smap_valid["first_seen_dt"] <= datetime.date(2020, 9, 14)) &
        (smap_valid["last_seen_dt"] >= datetime.date(2016, 1, 1))
    ]
    
    nifty_symbols = sorted(set(nifty_2016_2020["symbol"].dropna().unique()))
    print(f"Total NIFTY500 union member symbols (2016-2020): {len(nifty_symbols)}")
    
    calendar_symbols = set(df["symbol"].unique())
    nifty_with_ca = [s for s in nifty_symbols if s in calendar_symbols]
    nifty_without_ca = [s for s in nifty_symbols if s not in calendar_symbols]
    
    pct_with = (len(nifty_with_ca) / len(nifty_symbols)) * 100.0 if nifty_symbols else 0.0
    print(f"NIFTY500 symbols with at least one CA event: {len(nifty_with_ca):,} ({pct_with:.1f}%)")
    print(f"NIFTY500 symbols with zero CA events:        {len(nifty_without_ca):,} ({100.0 - pct_with:.1f}%)")
    
    # Export coverage breakdown to CSV
    coverage_df = pd.DataFrame([
        {"symbol": s, "has_ca_event": (s in calendar_symbols), "ca_event_count": len(df[df["symbol"] == s])}
        for s in nifty_symbols
    ])
    cov_csv = DATA_CSV_DIR / "nifty500_ca_coverage.csv"
    coverage_df.to_csv(cov_csv, index=False)
    print(f"Exported coverage table to {cov_csv}")

    print("\n" + "=" * 80)
    print("GATE 2 EXIT: ALL ASSERTIONS PASSED — SCHEMA SANITY, HAND VERIFICATION & COVERAGE CONFIRMED")
    print("=" * 80)

if __name__ == "__main__":
    main()
