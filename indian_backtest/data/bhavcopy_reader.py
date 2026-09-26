"""
indian_backtest.data.bhavcopy_reader
===================================
High-performance adjusted Bhavcopy and price bar data loader for NSE equities and benchmark indices.
Supports both historical Phase 5.5 Bhavcopy bars and modern era Phase 5.6 bars.
"""

import pickle
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
import numpy as np
import pandas as pd
from pandas.core.arrays.string_ import StringArray

class FixedStringArray(StringArray):
    def __setstate__(self, state):
        if isinstance(state, tuple) and len(state) == 2:
            state = (state[0], state[1], {})
        return super().__setstate__(state)

class SafeUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        if (module == "pandas.arrays" or module == "pandas.core.arrays.string_") and name == "StringArray":
            return FixedStringArray
        return super().find_class(module, name)

class BhavcopyReader:
    def __init__(self, base_dir: Optional[Path] = None, custom_path: Optional[Path] = None):
        self.base_dir = base_dir or Path("/storage/emulated/0/Documents/Project MIP")
        self.custom_path = custom_path
        self.bars_max_path = self.base_dir / "data/adjusted_bhavcopy_max_2007_2026.parquet"
        self.bars_v2_path = self.base_dir / "data/verification/halt1b_m1/adjusted_bhavcopy_bars_v2.parquet"
        self.bars_modern_path = self.base_dir / "data/adjusted_bhavcopy_bars_modern.parquet"
        self.price_export_path = self.base_dir / "data/price_cache_export.parquet"
        self.nsei_cache_path = Path("/sdcard/MIP1_Scanner/data/index__NSEI_cache.pkl")

        self._cached_bars_df: Optional[pd.DataFrame] = None
        self._cached_price_lookup: Optional[Dict[Tuple[str, str], dict]] = None
        self._cached_index_df: Optional[pd.DataFrame] = None

    def load_combined_bars(self, start_date: str = "2016-01-04", end_date: str = "2026-08-31") -> pd.DataFrame:
        """
        Loads continuous daily adjusted price bars across historical (2016-2020) and modern (2020-2026) eras.
        """
        if self._cached_bars_df is not None:
            return self._cached_bars_df

        if self.custom_path and Path(self.custom_path).exists():
            df = pd.read_parquet(self.custom_path)
            df = df[(df["date"] >= start_date) & (df["date"] <= end_date)].copy()
        elif self.bars_max_path.exists():
            df = pd.read_parquet(self.bars_max_path)
            df = df[(df["date"] >= start_date) & (df["date"] <= end_date)].copy()
        elif self.price_export_path.exists():
            df = pd.read_parquet(self.price_export_path)
            df = df[(df["date"] >= start_date) & (df["date"] <= end_date)].copy()
        elif self.bars_v2_path.exists() and self.bars_modern_path.exists():
            df_hist = pd.read_parquet(self.bars_v2_path)
            df_mod = pd.read_parquet(self.bars_modern_path)
            df = pd.concat([df_hist, df_mod], ignore_index=True)
            df = df[(df["date"] >= start_date) & (df["date"] <= end_date)].copy()
        else:
            raise FileNotFoundError("Required Bhavcopy parquet datasets not found on disk!")

        df = df.sort_values(["symbol", "date"]).reset_index(drop=True)

        # Precompute indicators: high_252, ema_200, ret_252
        df["high_252"] = df.groupby("symbol")["close"].transform(lambda s: s.rolling(252, min_periods=1).max())
        df["ema_200"] = df.groupby("symbol")["close"].transform(lambda s: s.ewm(span=200, adjust=True, min_periods=1).mean())

        def calc_ret(s):
            n = len(s)
            vals = s.to_numpy()
            prev = vals[np.maximum(0, np.arange(n) - 252)]
            with np.errstate(divide="ignore", invalid="ignore"):
                ret = np.where(np.arange(n) > 0, vals / prev - 1.0, 0.0)
            return pd.Series(ret, index=s.index)

        df["ret_252"] = df.groupby("symbol")["close"].transform(calc_ret)
        df["day1_ret"] = (df["close"] / df["open"] - 1.0).fillna(0.0)
        df["ret_1d"] = df.groupby("symbol")["close"].pct_change().fillna(0.0)
        df["vol_252"] = df.groupby("symbol")["ret_1d"].transform(lambda s: s.rolling(252, min_periods=20).std()) * np.sqrt(252)
        df["vol_252"] = df["vol_252"].fillna(0.30).replace(0.0, 0.30)

        self._cached_bars_df = df
        return df

    def get_price_lookup(self, start_date: str = "2016-01-04", end_date: str = "2026-08-31") -> Dict[Tuple[str, str], dict]:
        """
        Returns fast dictionary lookup (symbol, date) -> bar attributes.
        """
        if self._cached_price_lookup is not None:
            return self._cached_price_lookup

        df = self.load_combined_bars(start_date, end_date)
        self._cached_price_lookup = df.set_index(["symbol", "date"]).to_dict(orient="index")
        return self._cached_price_lookup

    def load_benchmark_index(self) -> pd.DataFrame:
        """
        Loads NIFTY 500 / NSEI benchmark index closing series and computes its 200 EMA.
        """
        if self._cached_index_df is not None:
            return self._cached_index_df

        proxy_path = self.base_dir / "deliverables/phase_7/data_csv/nifty_500_benchmark_proxy.csv"
        if proxy_path.exists():
            df = pd.read_csv(proxy_path)
            self._cached_index_df = df
            return df

        if self.nsei_cache_path.exists():
            with open(self.nsei_cache_path, "rb") as f:
                df = SafeUnpickler(f).load()
        else:
            # Fallback: compute equal-weight market average from bars
            bars = self.load_combined_bars()
            df = bars.groupby("date")["close"].mean().reset_index()

        df = df.sort_values("date").reset_index(drop=True)
        df["ema_20"] = df["close"].ewm(span=20, adjust=False).mean()
        df["ema_200"] = df["close"].ewm(span=200, adjust=True, min_periods=1).mean()
        df["high_252"] = df["close"].rolling(252, min_periods=1).max()
        df["ret_252"] = df["close"].pct_change(252).fillna(0.0)

        self._cached_index_df = df
        return df
