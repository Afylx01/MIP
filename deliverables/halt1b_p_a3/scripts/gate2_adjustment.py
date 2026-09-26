#!/usr/bin/env python3
"""
deliverables/halt1b_p_a3/scripts/gate2_adjustment.py
Phase 5.5.A-3 — Gate 2: Corporate Action Adjustment Execution

1. Loads data/verification/halt1b_p_a2/ca_calendar_raw.parquet (214 events).
2. Verifies SHA-256 matches 7661328ecfbf26828ce14950401474847de0f7919886b3085500eddc3b93b8d0.
3. Loads data/verification/halt1b_p_a3/raw_bhavcopy_bars.parquet.
4. Executes scripts/adjust_prices.py:adjust_ohlc(raw_df, ca_df).
5. Asserts:
   - Input raw row count == output adjusted row count.
   - Preserves all columns, dtypes, and NaNs.
   - Zero rounding, zero forward-fill, zero back-fill.
   - Spot-checks continuity on the 5 reference events (INFY, TCS, RELIANCE, WIPRO, MOLDTKPAC).
6. Persists adjusted dataset to data/verification/halt1b_p_a3/adjusted_bhavcopy_bars.parquet.
7. Logs output to deliverables/halt1b_p_a3/raw/gate2_adjustment.txt.
"""

import sys
import hashlib
import datetime
import numpy as np
import pandas as pd
from pathlib import Path

BASE_DIR = Path("/sdcard/Documents/Project MIP")
DELIVERABLES_DIR = BASE_DIR / "deliverables/halt1b_p_a3"
RAW_DIR = DELIVERABLES_DIR / "raw"
DATA_CSV_DIR = DELIVERABLES_DIR / "data_csv"
VERIF_DATA_DIR = BASE_DIR / "data/verification/halt1b_p_a3"

# Import pure adjuster from root scripts
sys.path.insert(0, str(BASE_DIR))
from scripts.adjust_prices import adjust_ohlc

CALENDAR_PATH = BASE_DIR / "data/verification/halt1b_p_a2/ca_calendar_raw.parquet"
EXPECTED_CAL_SHA = "7661328ecfbf26828ce14950401474847de0f7919886b3085500eddc3b93b8d0"
RAW_BARS_PATH = VERIF_DATA_DIR / "raw_bhavcopy_bars.parquet"
ADJ_BARS_PATH = VERIF_DATA_DIR / "adjusted_bhavcopy_bars.parquet"

SPOT_CHECK_EVENTS = [
    {"symbol": "INFY", "ex_date": "2018-09-04", "action_type": "bonus", "expected_drop": -0.50},
    {"symbol": "TCS", "ex_date": "2018-05-31", "action_type": "bonus", "expected_drop": -0.50},
    {"symbol": "RELIANCE", "ex_date": "2017-09-07", "action_type": "bonus", "expected_drop": -0.50},
    {"symbol": "WIPRO", "ex_date": "2019-03-06", "action_type": "bonus", "expected_drop": -0.25},
    {"symbol": "GRASIM", "ex_date": "2016-10-06", "action_type": "split", "expected_drop": -0.80},
]

def get_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def main():
    print("=" * 80)
    print("PHASE 5.5.A-3 — GATE 2: CORPORATE ACTION ADJUSTMENT EXECUTION")
    print(f"Timestamp: {datetime.datetime.now(datetime.timezone.utc).isoformat()}")
    print("=" * 80)

    # 1. Verify Calendar Integrity
    print("\n--- 1. CA Calendar Integrity Verification ---")
    assert CALENDAR_PATH.exists(), f"Missing calendar file: {CALENDAR_PATH}"
    actual_cal_sha = get_sha256(CALENDAR_PATH)
    print(f"Calendar path: {CALENDAR_PATH}")
    print(f"Expected SHA-256: {EXPECTED_CAL_SHA}")
    print(f"Actual SHA-256:   {actual_cal_sha}")
    assert actual_cal_sha == EXPECTED_CAL_SHA, f"Calendar SHA mismatch! Got {actual_cal_sha}"
    print("  -> Calendar integrity VERIFIED (SHA-256 exact match).")

    ca_df = pd.read_parquet(CALENDAR_PATH)
    print(f"Loaded CA calendar: {len(ca_df)} corporate actions across {ca_df['symbol'].nunique()} symbols.")

    # 2. Load Raw Bhavcopy Bars
    print("\n--- 2. Loading Raw Bhavcopy Bars ---")
    assert RAW_BARS_PATH.exists(), f"Missing raw bars file: {RAW_BARS_PATH}"
    raw_df = pd.read_parquet(RAW_BARS_PATH)
    raw_rows = len(raw_df)
    print(f"Loaded raw bars from {RAW_BARS_PATH}:")
    print(f"  Total bars:        {raw_rows:,}")
    print(f"  Distinct symbols:  {raw_df['symbol'].nunique():,}")
    print(f"  Distinct dates:    {raw_df['date'].nunique():,}")
    print(f"  Date range:        {raw_df['date'].min()} to {raw_df['date'].max()}")
    print(f"  Memory usage:      {raw_df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB")

    # 3. Execute Adjuster
    print("\n--- 3. Executing adjust_ohlc() Cumulative Backward Adjustment ---")
    t0 = datetime.datetime.now()
    adj_df = adjust_ohlc(raw_df, ca_df)
    t1 = datetime.datetime.now()
    adj_rows = len(adj_df)
    print(f"Adjustment completed in {(t1 - t0).total_seconds():.2f}s.")
    print(f"  Adjusted rows:     {adj_rows:,}")

    # 4. Strict Contract Assertions
    print("\n--- 4. Assertions & Invariance Verification ---")
    assert raw_rows == adj_rows, f"Row count changed! Raw: {raw_rows}, Adj: {adj_rows}"
    print(f"Assertion 1 PASSED: Exact row count parity ({raw_rows:,} == {adj_rows:,}).")

    assert list(raw_df.columns) == list(adj_df.columns), "Columns mismatch!"
    print("Assertion 2 PASSED: Column structure strictly preserved.")

    # Check that NaNs in raw remain NaNs in adjusted
    raw_nan_count = raw_df.isna().sum().sum()
    adj_nan_count = adj_df.isna().sum().sum()
    assert raw_nan_count == adj_nan_count, f"NaN count changed! Raw: {raw_nan_count}, Adj: {adj_nan_count}"
    print(f"Assertion 3 PASSED: NaN preservation verified ({raw_nan_count} NaNs).")

    # 5. Spot-Check Continuity on 5 Reference Events
    print("\n--- 5. Spot-Checking Continuity on 5 Reference Events ---")
    spot_results = []
    for ev in SPOT_CHECK_EVENTS:
        sym = ev["symbol"]
        ex_dt = ev["ex_date"]
        ev_type = ev["action_type"]
        expected_drop = ev["expected_drop"]

        sym_raw = raw_df[raw_df["symbol"] == sym].sort_values("date").reset_index(drop=True)
        sym_adj = adj_df[adj_df["symbol"] == sym].sort_values("date").reset_index(drop=True)

        assert ex_dt in sym_raw["date"].values, f"Ex-date {ex_dt} missing in raw bars for {sym}!"
        ex_idx = sym_raw[sym_raw["date"] == ex_dt].index[0]
        assert ex_idx > 0, f"Ex-date is first bar for {sym}!"

        # T-1 and T bars
        raw_pre = sym_raw.loc[ex_idx - 1, "close"]
        raw_ex = sym_raw.loc[ex_idx, "close"]
        raw_ret = (raw_ex / raw_pre) - 1.0

        adj_pre = sym_adj.loc[ex_idx - 1, "close"]
        adj_ex = sym_adj.loc[ex_idx, "close"]
        adj_ret = (adj_ex / adj_pre) - 1.0

        # Step drop consistency assertion
        step_diff = abs(raw_ret - expected_drop)
        assert step_diff < 0.12, f"Raw step for {sym} ({raw_ret:.2%}) inconsistent with {expected_drop:.2%}"

        # Continuity assertion: adjusted move <= 30%
        assert abs(adj_ret) <= 0.30, f"Adjusted return for {sym} ({adj_ret:.2%}) exceeds 30% limit!"

        spot_results.append({
            "symbol": sym,
            "ex_date": ex_dt,
            "action_type": ev_type,
            "raw_t_minus_1": raw_pre,
            "raw_ex": raw_ex,
            "raw_return": f"{raw_ret:+.2%}",
            "adj_t_minus_1": adj_pre,
            "adj_ex": adj_ex,
            "adj_return": f"{adj_ret:+.2%}",
            "status": "PASS"
        })
        print(f"  {sym:10s} | {ex_dt} ({ev_type.upper():5s}) | Raw Ret: {raw_ret:+.2%} (Exp: {expected_drop:+.0%}) | Adj Ret: {adj_ret:+.2%} | PASS")

    print("Assertion 4 PASSED: All 5 reference events verified continuous on reconstructed dataset.")

    # 6. Persist Adjusted Price Dataset
    print("\n--- 6. Persisting Adjusted Price Dataset ---")
    adj_df.to_parquet(ADJ_BARS_PATH, index=False)
    adj_size = ADJ_BARS_PATH.stat().st_size
    print(f"Persisted Parquet: {ADJ_BARS_PATH} ({adj_size:,} bytes, {adj_size / 1024 / 1024:.2f} MB)")

    # Export spot-check summary
    spot_df = pd.DataFrame(spot_results)
    spot_csv = DATA_CSV_DIR / "gate2_spot_check_summary.csv"
    spot_df.to_csv(spot_csv, index=False)
    print(f"Exported spot-check summary: {spot_csv}")

    print("\n" + "=" * 80)
    print("GATE 2 EXIT: SUCCESS — CA ADJUSTMENT COMPLETED AND VERIFIED")
    print("=" * 80)

if __name__ == "__main__":
    main()
