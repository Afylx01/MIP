#!/usr/bin/env python3
"""
deliverables/halt1b_p_a2/scripts/gate4_unit_test.py
Phase 5.5.A-2 — Gate 4: Adjuster Unit Test on Real Bhavcopy Data (Zero Network)

Tests 5 real corporate action events from 2016-2020:
1. INFY: 2018-09-04 Bonus 1:1 (ratio=1.0)
2. TCS: 2018-05-31 Bonus 1:1 (ratio=1.0)
3. RELIANCE: 2017-09-07 Bonus 1:1 (ratio=1.0)
4. WIPRO: 2019-03-06 Bonus 1:3 (ratio=0.3333)
5. MOLDTKPAC: 2016-02-17 Split 10 to 5 (ratio=2.0)

For each event:
- Prints 5 bars before and 5 bars after ex_date (both raw and adjusted).
- Asserts raw series has a step drop at ex_date consistent with ratio.
- Asserts adjusted series has no single-day move > 30% on ex_date.
"""

import sys
import datetime
import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR = Path("/sdcard/Documents/Project MIP")
DELIVERABLES_DIR = BASE_DIR / "deliverables/halt1b_p_a2"
RAW_DIR = DELIVERABLES_DIR / "raw"
DATA_CSV_DIR = DELIVERABLES_DIR / "data_csv"
SAMPLES_DIR = DELIVERABLES_DIR / "samples"
VERIF_DATA_DIR = BASE_DIR / "data/verification/halt1b_p_a2"

# Import adjuster
sys.path.insert(0, str(BASE_DIR))
from scripts.adjust_prices import adjust_ohlc

CALENDAR_PATH = VERIF_DATA_DIR / "ca_calendar_raw.parquet"
RAW_BARS_PATH = SAMPLES_DIR / "test_events_raw_bars.csv"

TEST_EVENTS = [
    {
        "symbol": "INFY",
        "ex_date": "2018-09-04",
        "action_type": "bonus",
        "ratio": 1.0,
        "expected_drop": -0.50
    },
    {
        "symbol": "TCS",
        "ex_date": "2018-05-31",
        "action_type": "bonus",
        "ratio": 1.0,
        "expected_drop": -0.50
    },
    {
        "symbol": "RELIANCE",
        "ex_date": "2017-09-07",
        "action_type": "bonus",
        "ratio": 1.0,
        "expected_drop": -0.50
    },
    {
        "symbol": "WIPRO",
        "ex_date": "2019-03-06",
        "action_type": "bonus",
        "ratio": 1.0/3.0,
        "expected_drop": -0.25
    },
    {
        "symbol": "MOLDTKPAC",
        "ex_date": "2016-02-17",
        "action_type": "split",
        "ratio": 2.0,
        "expected_drop": -0.50
    }
]

def main():
    print("=" * 80)
    print("PHASE 5.5.A-2 — GATE 4: ADJUSTER UNIT TEST ON REAL BHAVCOPY DATA")
    print(f"Timestamp: {datetime.datetime.now(datetime.timezone.utc).isoformat()}")
    print("=" * 80)
    
    assert CALENDAR_PATH.exists(), f"Missing calendar file: {CALENDAR_PATH}"
    assert RAW_BARS_PATH.exists(), f"Missing raw bars file: {RAW_BARS_PATH}"
    
    ca_df = pd.read_parquet(CALENDAR_PATH)
    all_raw_bars = pd.read_csv(RAW_BARS_PATH)
    
    print(f"Loaded calendar: {len(ca_df):,} events.")
    print(f"Loaded raw bars: {len(all_raw_bars):,} bars across symbols: {all_raw_bars['symbol'].unique().tolist()}")
    
    combined_export = []
    summary_results = []
    
    for ev in TEST_EVENTS:
        sym = ev["symbol"]
        ex_dt = ev["ex_date"]
        ev_type = ev["action_type"]
        ratio = ev["ratio"]
        expected_drop = ev["expected_drop"]
        
        print("\n" + "=" * 70)
        print(f"TEST EVENT: {sym} | {ev_type.upper()} | Ratio: {ratio:.4f} | Ex-Date: {ex_dt}")
        print("=" * 70)
        
        # Filter raw bars for symbol
        sym_raw = all_raw_bars[all_raw_bars["symbol"] == sym].copy()
        sym_raw = sym_raw.sort_values(by="date").reset_index(drop=True)
        
        assert not sym_raw.empty, f"No bars found for {sym}!"
        assert ex_dt in sym_raw["date"].values, f"Ex-date {ex_dt} not found in bars for {sym}!"
        
        ex_idx = sym_raw[sym_raw["date"] == ex_dt].index[0]
        start_idx = max(0, ex_idx - 5)
        end_idx = min(len(sym_raw), ex_idx + 6)
        
        event_raw_slice = sym_raw.iloc[start_idx:end_idx].copy().reset_index(drop=True)
        
        # Adjust using pure function
        event_adj_slice = adjust_ohlc(event_raw_slice, ca_df)
        
        # Find index of ex_date in slice
        slice_ex_idx = event_raw_slice[event_raw_slice["date"] == ex_dt].index[0]
        assert slice_ex_idx > 0, "No bar prior to ex_date in slice!"
        
        # Pre-event bar (T-1) and event bar (T)
        raw_pre_close = event_raw_slice.loc[slice_ex_idx - 1, "close"]
        raw_ex_close = event_raw_slice.loc[slice_ex_idx, "close"]
        raw_return = (raw_ex_close / raw_pre_close) - 1.0
        
        adj_pre_close = event_adj_slice.loc[slice_ex_idx - 1, "close"]
        adj_ex_close = event_adj_slice.loc[slice_ex_idx, "close"]
        adj_return = (adj_ex_close / adj_pre_close) - 1.0
        
        print(f"\n--- Raw Bars (5 Before, Ex-Date, 5 After) for {sym} ---")
        for i, r in event_raw_slice.iterrows():
            marker = " <-- EX-DATE" if r["date"] == ex_dt else (" (T-1)" if i == slice_ex_idx - 1 else "")
            print(f"  {r['date']} | O: {r['open']:8.2f} | H: {r['high']:8.2f} | L: {r['low']:8.2f} | C: {r['close']:8.2f} | V: {r['volume']:10,d}{marker}")
            
        print(f"\n--- Adjusted Bars (5 Before, Ex-Date, 5 After) for {sym} ---")
        for i, r in event_adj_slice.iterrows():
            marker = " <-- EX-DATE" if r["date"] == ex_dt else (" (T-1)" if i == slice_ex_idx - 1 else "")
            print(f"  {r['date']} | O: {r['open']:8.2f} | H: {r['high']:8.2f} | L: {r['low']:8.2f} | C: {r['close']:8.2f} | V: {r['volume']:10.0f}{marker}")

        print(f"\nReturn Analysis across Ex-Date ({sym}):")
        print(f"  Raw T-1 Close:      {raw_pre_close:.2f}")
        print(f"  Raw Ex-Date Close:   {raw_ex_close:.2f}")
        print(f"  Raw 1-Day Return:   {raw_return:+.2%} (Expected step: ~{expected_drop:+.0%})")
        print(f"  Adjusted T-1 Close: {adj_pre_close:.2f}")
        print(f"  Adjusted Ex Close:  {adj_ex_close:.2f}")
        print(f"  Adjusted Return:    {adj_return:+.2%}")
        
        # Assertions
        # 1. Raw step consistent with ratio
        step_diff = abs(raw_return - expected_drop)
        print(f"  Raw step discrepancy from expected drop: {step_diff:.4f}")
        assert step_diff < 0.12, f"Raw step for {sym} ({raw_return:.2%}) not consistent with expected {expected_drop:.2%}!"
        print(f"  -> Assertion 1 PASSED: Raw step matches event ratio.")
        
        # 2. Adjusted series has no move > 30% on ex_date
        assert abs(adj_return) <= 0.30, f"Adjusted series move for {sym} ({adj_return:.2%}) exceeds 30% limit!"
        print(f"  -> Assertion 2 PASSED: Adjusted return ({adj_return:+.2%}) <= 30% limit.")
        
        summary_results.append({
            "symbol": sym,
            "ex_date": ex_dt,
            "action_type": ev_type,
            "ratio": ratio,
            "raw_t_minus_1_close": raw_pre_close,
            "raw_ex_close": raw_ex_close,
            "raw_return_pct": f"{raw_return * 100:.2f}%",
            "adj_t_minus_1_close": adj_pre_close,
            "adj_ex_close": adj_ex_close,
            "adj_return_pct": f"{adj_return * 100:.2f}%",
            "status": "PASS"
        })
        
        # Combine bars for CSV export
        for i in range(len(event_raw_slice)):
            combined_export.append({
                "symbol": sym,
                "date": event_raw_slice.loc[i, "date"],
                "is_ex_date": (event_raw_slice.loc[i, "date"] == ex_dt),
                "raw_open": event_raw_slice.loc[i, "open"],
                "raw_high": event_raw_slice.loc[i, "high"],
                "raw_low": event_raw_slice.loc[i, "low"],
                "raw_close": event_raw_slice.loc[i, "close"],
                "raw_volume": event_raw_slice.loc[i, "volume"],
                "adj_open": event_adj_slice.loc[i, "open"],
                "adj_high": event_adj_slice.loc[i, "high"],
                "adj_low": event_adj_slice.loc[i, "low"],
                "adj_close": event_adj_slice.loc[i, "close"],
                "adj_volume": event_adj_slice.loc[i, "volume"],
            })

    # Summary table
    sum_df = pd.DataFrame(summary_results)
    print("\n" + "=" * 80)
    print("GATE 4 UNIT TEST SUMMARY (ALL 5 EVENTS)")
    print("=" * 80)
    print(sum_df.to_string(index=False))
    
    # Export CSVs
    sum_csv = DATA_CSV_DIR / "gate4_unit_test_summary.csv"
    sum_df.to_csv(sum_csv, index=False)
    
    bars_csv = DATA_CSV_DIR / "gate4_test_bars.csv"
    pd.DataFrame(combined_export).to_csv(bars_csv, index=False)
    
    print(f"\nExported summary table to: {sum_csv}")
    print(f"Exported combined bars to:  {bars_csv}")
    
    print("\n" + "=" * 80)
    print("GATE 4 EXIT: ALL 5 EVENTS VERIFIED — ASSERTIONS PASSED (STEP DROP VERIFIED & ADJUSTED MOVE < 30%)")
    print("=" * 80)

if __name__ == "__main__":
    main()
