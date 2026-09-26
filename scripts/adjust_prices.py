"""
scripts/adjust_prices.py
Corporate Action Price and Volume Adjuster for Project MIP.

Implements cumulative backward adjustment across stock splits and bonus issues.
Contract:
- adjust_ohlc(raw_df, ca_calendar_df) -> adjusted_df
- Input raw_df: columns symbol, date, open, high, low, close, volume
- Input ca_calendar_df: columns symbol, ex_date, action_type, ratio
- Output: same shape as raw_df, adjusted OHLC and volume
- Method: cumulative backward adjustment (date < ex_date multiplied by factor)
- No rounding. No filling. No forward-fill. NaN stays NaN.
- Pure function. No I/O. No global state. No prints.
"""

import pandas as pd
import numpy as np

def adjust_ohlc(raw_df: pd.DataFrame, ca_calendar_df: pd.DataFrame) -> pd.DataFrame:
    """
    Pure function performing cumulative backward adjustment of OHLCV bars.
    
    Parameters
    ----------
    raw_df : pd.DataFrame
        DataFrame with columns: symbol, date, open, high, low, close, volume.
    ca_calendar_df : pd.DataFrame
        DataFrame with columns: symbol, ex_date, action_type, ratio.
        
    Returns
    -------
    pd.DataFrame
        Copy of raw_df with adjusted open, high, low, close, and volume.
    """
    if raw_df is None or raw_df.empty:
        return raw_df.copy() if raw_df is not None else pd.DataFrame()
        
    required_raw = ["symbol", "date", "open", "high", "low", "close", "volume"]
    missing_raw = [c for c in required_raw if c not in raw_df.columns]
    if missing_raw:
        raise ValueError(f"raw_df missing required columns: {missing_raw}")
        
    required_ca = ["symbol", "ex_date", "action_type", "ratio"]
    missing_ca = [c for c in required_ca if c not in ca_calendar_df.columns]
    if missing_ca:
        raise ValueError(f"ca_calendar_df missing required columns: {missing_ca}")

    # Work on a copy preserving index
    adj_df = raw_df.copy()
    
    if ca_calendar_df.empty:
        return adj_df
        
    # Convert dates to ISO strings for uniform, safe comparison
    raw_dates_str = pd.to_datetime(adj_df["date"]).dt.strftime("%Y-%m-%d").values
    raw_symbols = adj_df["symbol"].astype(str).values
    
    # Filter valid actions
    valid_ca = ca_calendar_df[
        (ca_calendar_df["action_type"].isin(["bonus", "split"])) &
        (ca_calendar_df["ratio"] > 0)
    ].copy()
    
    if valid_ca.empty:
        return adj_df
        
    valid_ca["ex_date_str"] = pd.to_datetime(valid_ca["ex_date"]).dt.strftime("%Y-%m-%d")
    
    # Initialize adjustment factors (1.0 for each row)
    price_factors = np.ones(len(adj_df), dtype=np.float64)
    
    # Group actions by symbol
    for sym, group in valid_ca.groupby("symbol"):
        sym_mask = (raw_symbols == str(sym))
        if not np.any(sym_mask):
            continue
            
        sym_dates = raw_dates_str[sym_mask]
        sym_factors = np.ones(len(sym_dates), dtype=np.float64)
        
        # Sort events by ex_date ascending
        sorted_events = group.sort_values(by="ex_date_str")
        
        for _, row in sorted_events.iterrows():
            action = row["action_type"]
            ratio = float(row["ratio"])
            ex_dt = row["ex_date_str"]
            
            if action == "bonus":
                # Bonus ratio A:B -> factor = 1 / (1 + ratio)
                f = 1.0 / (1.0 + ratio)
            elif action == "split":
                # Split ratio old/new -> factor = 1 / ratio
                f = 1.0 / ratio
            else:
                continue
                
            # All bars strictly prior to ex_date are adjusted
            prior_mask = (sym_dates < ex_dt)
            sym_factors[prior_mask] *= f
            
        price_factors[sym_mask] = sym_factors
        
    # Apply price and volume adjustments
    # Note: NaN values remain NaN because float * NaN = NaN
    adj_df["open"] = adj_df["open"].astype(np.float64) * price_factors
    adj_df["high"] = adj_df["high"].astype(np.float64) * price_factors
    adj_df["low"] = adj_df["low"].astype(np.float64) * price_factors
    adj_df["close"] = adj_df["close"].astype(np.float64) * price_factors
    
    # Volume is adjusted inversely (multiplied by 1/price_factor)
    volume_factors = np.where(price_factors > 0, 1.0 / price_factors, 1.0)
    adj_df["volume"] = adj_df["volume"].astype(np.float64) * volume_factors
    
    return adj_df
