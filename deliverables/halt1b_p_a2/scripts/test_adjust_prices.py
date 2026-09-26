#!/usr/bin/env python3
"""
scripts/test_adjust_prices.py
Smoke test for corporate action price adjuster (Branch B requirement).

Constructs a 5-bar raw series and a 1-event calendar and asserts the adjusted
series is continuous across the event.
"""

import sys
import numpy as np
import pandas as pd
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.adjust_prices import adjust_ohlc

def test_bonus_continuity_5_bar():
    # 5-bar synthetic price series:
    # Day 0: Pre-bonus (close = 2000)
    # Day 1: Pre-bonus (close = 2020)
    # Day 2: Ex-date for 1:1 bonus (ratio=1.0) -> stock trades at ~half price (close = 1010)
    # Day 3: Post-bonus (close = 1025)
    # Day 4: Post-bonus (close = 1035)
    raw_data = {
        "symbol": ["TEST"] * 5,
        "date": ["2020-01-01", "2020-01-02", "2020-01-03", "2020-01-06", "2020-01-07"],
        "open": [1990.0, 2010.0, 1005.0, 1015.0, 1025.0],
        "high": [2010.0, 2030.0, 1015.0, 1030.0, 1040.0],
        "low": [1980.0, 2000.0, 1000.0, 1010.0, 1020.0],
        "close": [2000.0, 2020.0, 1010.0, 1025.0, 1035.0],
        "volume": [10000.0, 12000.0, 24000.0, 22000.0, 21000.0]
    }
    raw_df = pd.DataFrame(raw_data)
    
    ca_data = {
        "symbol": ["TEST"],
        "ex_date": ["2020-01-03"],
        "action_type": ["bonus"],
        "ratio": [1.0]
    }
    ca_df = pd.DataFrame(ca_data)
    
    # 1. Assert raw series has artificial ~50% drop
    raw_return_at_event = (raw_df["close"].iloc[2] / raw_df["close"].iloc[1]) - 1.0
    print(f"Raw 1-day return across ex-date: {raw_return_at_event:.2%}")
    assert raw_return_at_event < -0.45, "Raw series should show ~50% step drop!"
    
    # 2. Adjust OHLC
    adj_df = adjust_ohlc(raw_df, ca_df)
    
    # 3. Assert shape and columns preserved
    assert adj_df.shape == raw_df.shape, "Adjusted DataFrame shape mismatch!"
    assert list(adj_df.columns) == list(raw_df.columns), "Columns altered!"
    
    # 4. Assert adjusted return across ex-date is continuous
    # Pre-bonus close 2020 should adjust to 2020 * 0.5 = 1010
    assert abs(adj_df["close"].iloc[1] - 1010.0) < 1e-6, f"Expected 1010.0, got {adj_df['close'].iloc[1]}"
    assert abs(adj_df["close"].iloc[2] - 1010.0) < 1e-6, f"Expected 1010.0, got {adj_df['close'].iloc[2]}"
    
    adj_return_at_event = (adj_df["close"].iloc[2] / adj_df["close"].iloc[1]) - 1.0
    print(f"Adjusted 1-day return across ex-date: {adj_return_at_event:.2%}")
    assert abs(adj_return_at_event) < 0.001, f"Adjusted series should be continuous! Got {adj_return_at_event}"
    
    # 5. Assert volume adjusted inversely
    # Pre-bonus volume 12000 should become 12000 * 2.0 = 24000
    assert abs(adj_df["volume"].iloc[1] - 24000.0) < 1e-6, f"Expected 24000 volume, got {adj_df['volume'].iloc[1]}"
    
    # 6. Assert input raw_df was not mutated (pure function)
    assert raw_df["close"].iloc[1] == 2020.0, "Input raw_df was mutated!"
    
    print("Smoke test PASSED: 5-bar series with 1-event bonus is continuous.")

def test_split_and_nan_preservation():
    raw_df = pd.DataFrame({
        "symbol": ["SPLIT_TEST"] * 3,
        "date": ["2020-01-01", "2020-01-02", "2020-01-03"],
        "open": [100.0, np.nan, 20.0],
        "high": [105.0, 105.0, 21.0],
        "low": [95.0, 95.0, 19.0],
        "close": [100.0, 100.0, 20.0],
        "volume": [1000.0, 1000.0, 5000.0]
    })
    ca_df = pd.DataFrame({
        "symbol": ["SPLIT_TEST"],
        "ex_date": ["2020-01-03"],
        "action_type": ["split"],
        "ratio": [5.0] # 10 to 2 split -> ratio = 5.0
    })
    adj = adjust_ohlc(raw_df, ca_df)
    # Pre-split close 100 should adjust to 100 / 5 = 20.0
    assert abs(adj["close"].iloc[1] - 20.0) < 1e-6
    # NaN must stay NaN
    assert np.isnan(adj["open"].iloc[1]), "NaN was not preserved!"
    print("Smoke test PASSED: Split and NaN preservation verified.")

if __name__ == "__main__":
    test_bonus_continuity_5_bar()
    test_split_and_nan_preservation()
    print("\nALL ADJUSTER SMOKE TESTS PASSED.")
