#!/usr/bin/env python3
"""
production/auto_fetch_market_data.py
Automated Dynamic Market Data Fetcher & Corporate Action Adjuster for Project MIP.

Directive ID: DIR-PROD-LIVE-DATA-SYNC-01
Standing Gate: HALT-15

Capabilities:
  1. Inspects data/universe/nifty500_pit_universe.parquet and detects latest date (max_date).
  2. Identifies missing trading dates up to target date (excluding weekends and NSE holidays).
  3. Downloads official daily equity Bhavcopies directly from official NSE archives.
  4. Fetches live corporate actions (splits, bonuses, cash dividends) from NSE API.
  5. Backward-adjusts historical price and volume series using verified institutional math.
  6. Enforces all 4 master invariants:
       - Exactly 0 null prices.
       - Exactly 0 duplicate (symbol, date) composite keys.
       - Strictly monotonic chronological sorting.
       - Strictly positive prices.
  7. Atomically updates nifty500_pit_universe.parquet and universe_metadata.json with new SHA-256.

Usage:
  python3 production/auto_fetch_market_data.py [--target-date YYYY-MM-DD] [--dry-run]
"""

import sys
import os
import io
import re
import json
import zipfile
import hashlib
import argparse
import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
import requests
import pandas as pd
import numpy as np


def get_base_dir() -> Path:
    """Dynamically resolves Project MIP root across Windows and Linux."""
    if "PROJECT_MIP_DIR" in os.environ and Path(os.environ["PROJECT_MIP_DIR"]).exists():
        return Path(os.environ["PROJECT_MIP_DIR"])
    android_path = Path("/storage/emulated/0/Documents/Project MIP")
    if android_path.exists():
        return android_path
    cur = Path(__file__).resolve()
    for p in [cur] + list(cur.parents):
        if (p / "run_mip.py").exists() or (p / "data/universe").exists():
            return p
    return cur.parent.parent if cur.parent.name in ["production", "scripts"] else cur.parent


def get_deliverables_mirror_dir(base_dir: Path) -> Path:
    """Resolves deliverables mirror directory safely across environments."""
    sdcard_mirror = Path("/sdcard/Documents/deliverables")
    if sdcard_mirror.exists() and sdcard_mirror.is_dir():
        return sdcard_mirror
    local_mirror = base_dir / "deliverables"
    local_mirror.mkdir(parents=True, exist_ok=True)
    return local_mirror


BASE_DIR = get_base_dir()
DATA_DIR = BASE_DIR / "data"
UNIVERSE_DIR = DATA_DIR / "universe"
UNIVERSE_PARQUET = UNIVERSE_DIR / "nifty500_pit_universe.parquet"
METADATA_JSON = UNIVERSE_DIR / "universe_metadata.json"
CALENDAR_FILE = DATA_DIR / "trading_calendar.txt"
GRAVEYARD_CSV = DATA_DIR / "verification/survivorship_graveyard.csv"
SECTOR_MAP_JSON = UNIVERSE_DIR / "symbol_sector_map.json"

REQUIRED_COLUMNS = ["date", "symbol", "open", "high", "low", "close", "volume", "is_delisted"]

NSE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nseindia.com/",
}


def compute_sha256(path: Path) -> str:
    """Computes SHA-256 cryptographic digest of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


class MarketDataSyncEngine:
    """Automated market data synchronization and corporate action adjustment engine."""

    def __init__(
        self,
        universe_parquet: Path = UNIVERSE_PARQUET,
        metadata_file: Path = METADATA_JSON,
        calendar_file: Path = CALENDAR_FILE,
    ):
        self.universe_parquet = Path(universe_parquet)
        self.metadata_file = Path(metadata_file)
        self.calendar_file = Path(calendar_file)
        self.session = requests.Session()
        self.session.headers.update(NSE_HEADERS)

    def log(self, msg: str):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [MarketDataSync] {msg}")

    def get_universe_max_date(self) -> str:
        """Reads latest date present in master universe parquet."""
        if not self.universe_parquet.exists():
            raise FileNotFoundError(f"Universe database not found at {self.universe_parquet}")
        df = pd.read_parquet(self.universe_parquet, columns=["date"])
        return str(df["date"].max())

    def get_known_holidays(self) -> Set[str]:
        """Loads non-trading dates from calendar file."""
        if not self.calendar_file.exists():
            return set()
        with open(self.calendar_file, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
        return set(lines)

    def get_missing_trading_dates(
        self,
        max_date: Optional[str] = None,
        target_date: Optional[str] = None
    ) -> List[str]:
        """
        Identifies missing trading dates between (max_date + 1) and target_date.
        Excludes weekends (Sat/Sun).
        """
        cur_max = max_date or self.get_universe_max_date()
        target = target_date or datetime.date.today().strftime("%Y-%m-%d")

        dt_max = datetime.date.fromisoformat(cur_max)
        dt_target = datetime.date.fromisoformat(target)

        if dt_target <= dt_max:
            return []

        known_calendar = self.get_known_holidays()

        missing = []
        cur = dt_max + datetime.timedelta(days=1)
        while cur <= dt_target:
            # 0=Mon, ..., 4=Fri, 5=Sat, 6=Sun
            if cur.weekday() < 5:
                dt_str = cur.strftime("%Y-%m-%d")
                # If calendar file covers future dates, check against it; otherwise check weekdays
                if not known_calendar or dt_str in known_calendar or cur_max >= "2026-08-31":
                    missing.append(dt_str)
            cur += datetime.timedelta(days=1)

        return missing

    def fetch_bhavcopy_for_date(self, date_str: str) -> Optional[pd.DataFrame]:
        """
        Fetches daily equity Bhavcopy for date_str from official NSE archives.
        Tries modern PR Bhavcopy first, followed by classic archive format.
        """
        dt = datetime.date.fromisoformat(date_str)
        yyyymmdd = dt.strftime("%Y%m%d")
        dd = dt.strftime("%d")
        mmm = dt.strftime("%b").upper()
        yyyy = dt.strftime("%Y")

        urls = [
            # 1. Modern PR Bhavcopy (2024 - Present)
            f"https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_{yyyymmdd}_F_0000.csv.zip",
            # 2. Classic NSE Equities Archive
            f"https://archives.nseindia.com/content/historical/EQUITIES/{yyyy}/{mmm}/cm{dd}{mmm}{yyyy}bhav.csv.zip",
        ]

        for url in urls:
            try:
                self.log(f"Fetching Bhavcopy from: {url}")
                resp = self.session.get(url, timeout=15)
                if resp.status_code == 200 and len(resp.content) > 1000:
                    with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
                        namelist = z.namelist()
                        csv_name = [n for n in namelist if n.endswith(".csv")][0]
                        with z.open(csv_name) as f:
                            df_raw = pd.read_csv(f)
                            self.log(f"Successfully extracted {len(df_raw):,} rows from {csv_name}")
                            return self._standardize_bhavcopy(df_raw, date_str)
                elif resp.status_code == 404:
                    self.log(f"HTTP 404 for {url} (Market may have been closed or file not yet published)")
                else:
                    self.log(f"HTTP {resp.status_code} received from {url}")
            except Exception as e:
                self.log(f"Network error accessing {url}: {e}")

        # 3. Same-day live Bhavcopy check if date_str is today
        if date_str == datetime.date.today().strftime("%Y-%m-%d"):
            live_url = "https://archives.nseindia.com/products/content/sec_bhavdata_full.csv"
            try:
                self.log(f"Attempting same-day live Bhavcopy: {live_url}")
                resp = self.session.get(live_url, timeout=15)
                if resp.status_code == 200 and len(resp.content) > 1000:
                    df_raw = pd.read_csv(io.StringIO(resp.text))
                    return self._standardize_bhavcopy(df_raw, date_str)
            except Exception as e:
                self.log(f"Network error accessing {live_url}: {e}")

        return None

    def _standardize_bhavcopy(self, raw: pd.DataFrame, fallback_date: str) -> pd.DataFrame:
        """Normalizes heterogeneous NSE Bhavcopy formats into standard OHLCV schema."""
        raw.columns = [c.strip().upper() for c in raw.columns]

        # Filter equity series
        series_col = next((c for c in ["SCTYSRS", "SERIES"] if c in raw.columns), None)
        if series_col:
            raw = raw[raw[series_col].astype(str).str.strip().str.upper().isin(["EQ", "BE", "BZ"])].copy()

        col_map = {
            # Modern PR format
            "TRADDT": "date", "TCKRSYMB": "symbol",
            "OPNPRIC": "open", "HGHPRIC": "high", "LWPRIC": "low", "CLSPRIC": "close",
            "TTLTRADGVOL": "volume",
            # Classic format
            "TIMESTAMP": "date", "DATE": "date", "SYMBOL": "symbol",
            "OPEN": "open", "OPEN_PRICE": "open",
            "HIGH": "high", "HIGH_PRICE": "high",
            "LOW": "low", "LOW_PRICE": "low",
            "CLOSE": "close", "CLOSE_PRICE": "close",
            "TOTTRDQTY": "volume", "TTL_TRD_QNTY": "volume", "VOLUME": "volume"
        }

        df = raw.rename(columns={s: d for s, d in col_map.items() if s in raw.columns})

        if "date" not in df.columns or df["date"].isnull().all():
            df["date"] = fallback_date
        else:
            df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")

        df["symbol"] = df["symbol"].astype(str).str.strip().str.upper()

        for num_col in ["open", "high", "low", "close", "volume"]:
            df[num_col] = pd.to_numeric(df[num_col], errors="coerce")

        df = df.dropna(subset=["date", "symbol", "open", "high", "low", "close", "volume"])
        df = df[(df["open"] > 0) & (df["high"] > 0) & (df["low"] > 0) & (df["close"] > 0)]

        # Retain necessary fields
        return df[["date", "symbol", "open", "high", "low", "close", "volume"]].copy()

    def fetch_live_corporate_actions(self) -> List[dict]:
        """Fetches live corporate actions list from official NSE India API."""
        url = "https://www.nseindia.com/api/corporates-corporateActions?index=equities"
        try:
            self.log(f"Connecting to official NSE Corporate Actions API...")
            # Establish session cookies
            try:
                self.session.get("https://www.nseindia.com", timeout=10)
            except Exception:
                pass

            resp = self.session.get(url, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list):
                    self.log(f"Retrieved {len(data)} live corporate action records from NSE.")
                    return data
                elif isinstance(data, dict) and "data" in data:
                    self.log(f"Retrieved {len(data['data'])} live corporate action records from NSE.")
                    return data["data"]
            self.log(f"NSE Corporate Actions API returned status {resp.status_code}")
        except Exception as e:
            self.log(f"Note: Could not reach live NSE CA API: {e}")

        return []

    def parse_corporate_actions(
        self,
        raw_actions: List[dict],
        start_date: str,
        end_date: str
    ) -> List[dict]:
        """
        Parses stock splits, bonus issues, and cash dividends from raw action records.
        Filters events where exDate is between start_date and end_date.
        """
        parsed = []
        for item in raw_actions:
            sym = str(item.get("symbol", "")).strip().upper()
            ex_date_raw = str(item.get("exDate", "")).strip()
            subject = str(item.get("subject", "")).strip()

            if not sym or not ex_date_raw or ex_date_raw == "-":
                continue

            try:
                ex_date = pd.to_datetime(ex_date_raw, format="%d-%b-%Y").strftime("%Y-%m-%d")
            except Exception:
                try:
                    ex_date = pd.to_datetime(ex_date_raw).strftime("%Y-%m-%d")
                except Exception:
                    continue

            # Check date window
            if not (start_date <= ex_date <= end_date):
                continue

            sub_lower = subject.lower()

            # 1. Parse Stock Split
            # Example patterns: "Split - Face Value Rs 10 To Rs 2", "Sub-Division From Rs 10 To Rs 1", "Split 10:1"
            m_split_fv = re.search(r"(?:split|sub[\s-]*division).*?rs\.?\s*(\d+(?:\.\d+)?).*?to.*?rs\.?\s*(\d+(?:\.\d+)?)", sub_lower)
            m_split_ratio = re.search(r"split.*?(\d+)\s*:\s*(\d+)", sub_lower)

            if m_split_fv:
                old_fv = float(m_split_fv.group(1))
                new_fv = float(m_split_fv.group(2))
                if old_fv > 0 and new_fv > 0 and old_fv != new_fv:
                    ratio = old_fv / new_fv
                    factor = 1.0 / ratio
                    parsed.append({
                        "symbol": sym,
                        "ex_date": ex_date,
                        "action_type": "split",
                        "ratio": ratio,
                        "price_factor": factor,
                        "volume_factor": 1.0 / factor,
                        "subject": subject
                    })
                    continue

            if m_split_ratio:
                r1 = float(m_split_ratio.group(1))
                r2 = float(m_split_ratio.group(2))
                if r1 > 0 and r2 > 0 and r1 != r2:
                    ratio = r2 / r1 if r2 > r1 else r1 / r2
                    factor = 1.0 / ratio
                    parsed.append({
                        "symbol": sym,
                        "ex_date": ex_date,
                        "action_type": "split",
                        "ratio": ratio,
                        "price_factor": factor,
                        "volume_factor": 1.0 / factor,
                        "subject": subject
                    })
                    continue

            # 2. Parse Bonus Issue
            # Example patterns: "Bonus 1:1", "Bonus 2:1", "Bonus Issue 1:2"
            m_bonus = re.search(r"bonus.*?(\d+(?:\.\d+)?)\s*:\s*(\d+(?:\.\d+)?)", sub_lower)
            if m_bonus:
                b_num = float(m_bonus.group(1))
                b_den = float(m_bonus.group(2))
                if b_num > 0 and b_den > 0:
                    b_ratio = b_num / b_den
                    factor = 1.0 / (1.0 + b_ratio)
                    parsed.append({
                        "symbol": sym,
                        "ex_date": ex_date,
                        "action_type": "bonus",
                        "ratio": b_ratio,
                        "price_factor": factor,
                        "volume_factor": 1.0 / factor,
                        "subject": subject
                    })
                    continue

            # 3. Parse Cash Dividend
            # Example patterns: "Dividend - Rs 2.35 Per Share", "Interim Dividend - Rs 10", "Dividend INR 5"
            m_div = re.search(r"dividend.*?(?:rs\.?|inr)\s*(\d+(?:\.\d+)?)", sub_lower)
            if m_div:
                div_amount = float(m_div.group(1))
                if div_amount > 0:
                    parsed.append({
                        "symbol": sym,
                        "ex_date": ex_date,
                        "action_type": "dividend",
                        "dividend_amount": div_amount,
                        "subject": subject
                    })
                    continue

        self.log(f"Parsed {len(parsed)} relevant corporate actions between {start_date} and {end_date}.")
        return parsed

    def apply_corporate_actions_backward(
        self,
        universe_df: pd.DataFrame,
        parsed_actions: List[dict]
    ) -> pd.DataFrame:
        """
        Applies cumulative backward adjustments to historical price and volume bars.
        For splits/bonuses: prices *= factor, volume /= factor.
        For dividends: prices *= (1 - div / close_prev).
        """
        if not parsed_actions or universe_df.empty:
            return universe_df

        df = universe_df.copy()
        raw_symbols = df["symbol"].astype(str).values
        raw_dates = df["date"].astype(str).values

        splits_and_bonuses = [a for a in parsed_actions if a["action_type"] in ["split", "bonus"]]
        dividends = [a for a in parsed_actions if a["action_type"] == "dividend"]

        # Apply splits and bonuses
        for ca in splits_and_bonuses:
            sym = ca["symbol"]
            ex_date = ca["ex_date"]
            p_fac = ca["price_factor"]
            v_fac = ca["volume_factor"]

            mask = (raw_symbols == sym) & (raw_dates < ex_date)
            if np.any(mask):
                df.loc[mask, "open"] = df.loc[mask, "open"] * p_fac
                df.loc[mask, "high"] = df.loc[mask, "high"] * p_fac
                df.loc[mask, "low"] = df.loc[mask, "low"] * p_fac
                df.loc[mask, "close"] = df.loc[mask, "close"] * p_fac
                df.loc[mask, "volume"] = df.loc[mask, "volume"] * v_fac
                self.log(f"Adjusted {np.sum(mask)} prior bars for {sym} ({ca['action_type'].upper()}, factor={p_fac:.4f})")

        # Apply cash dividends
        for ca in dividends:
            sym = ca["symbol"]
            ex_date = ca["ex_date"]
            div_val = ca["dividend_amount"]

            sym_bars = df[df["symbol"] == sym]
            prior_bars = sym_bars[sym_bars["date"] < ex_date]
            if not prior_bars.empty:
                last_close = prior_bars.iloc[-1]["close"]
                if last_close > div_val:
                    d_fac = 1.0 - (div_val / last_close)
                    mask = (raw_symbols == sym) & (raw_dates < ex_date)
                    df.loc[mask, "open"] = df.loc[mask, "open"] * d_fac
                    df.loc[mask, "high"] = df.loc[mask, "high"] * d_fac
                    df.loc[mask, "low"] = df.loc[mask, "low"] * d_fac
                    df.loc[mask, "close"] = df.loc[mask, "close"] * d_fac
                    self.log(f"Adjusted {np.sum(mask)} prior bars for {sym} (DIVIDEND ₹{div_val}, factor={d_fac:.4f})")

        return df

    def validate_invariants(self, df: pd.DataFrame) -> Tuple[bool, str]:
        """Validates all strict mathematical and schema invariants."""
        # 1. Required columns
        missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
        if missing:
            return False, f"Missing required columns: {missing}"

        # 2. Zero null prices
        for col in ["open", "high", "low", "close", "volume"]:
            null_count = int(df[col].isnull().sum())
            if null_count > 0:
                return False, f"Invariant violation: {null_count} null values in '{col}'"

        # 3. Positive prices
        for col in ["open", "high", "low", "close"]:
            non_pos = int((df[col] <= 0).sum())
            if non_pos > 0:
                return False, f"Invariant violation: {non_pos} non-positive values in '{col}'"

        # 4. Zero duplicate composite keys
        dup_count = int(df.duplicated(subset=["date", "symbol"]).sum())
        if dup_count > 0:
            return False, f"Invariant violation: {dup_count} duplicate (date, symbol) keys"

        # 5. Chronological monotonic ordering
        for sym, group in df.groupby("symbol"):
            if not group["date"].is_monotonic_increasing:
                return False, f"Invariant violation: non-monotonic dates for symbol '{sym}'"

        return True, "All invariants verified"

    def sync_universe_to_date(
        self,
        target_date: Optional[str] = None,
        dry_run: bool = False
    ) -> Dict:
        """
        Executes end-to-end synchronization:
          1. Detects date gaps.
          2. Downloads missing Bhavcopies from NSE.
          3. Fetches live corporate actions & adjusts historical bars.
          4. Validates invariants.
          5. Atomically writes updated database.
        """
        self.log("==================================================================")
        self.log("DYNAMIC MARKET DATA & CORPORATE ACTION SYNCHRONIZATION ENGINE")
        self.log("==================================================================")

        max_date = self.get_universe_max_date()
        target = target_date or datetime.date.today().strftime("%Y-%m-%d")

        self.log(f"Master Universe Latest Date: {max_date}")
        self.log(f"Target Synchronization Date: {target}")

        missing_dates = self.get_missing_trading_dates(max_date, target)
        self.log(f"Missing Trading Sessions:    {len(missing_dates)} {missing_dates if missing_dates else '(None)'}")

        if not missing_dates:
            self.log(f"✅ Universe is already up to date as of {max_date}.")
            return {
                "status": "UP_TO_DATE",
                "max_date": max_date,
                "missing_dates": [],
                "bars_added": 0
            }

        if dry_run:
            self.log("\n[DRY-RUN] Simulating Bhavcopy & Corporate Action Fetching:")
            self.log(f"[DRY-RUN] Missing dates to fetch: {missing_dates}")
            live_ca = self.fetch_live_corporate_actions()
            parsed_ca = self.parse_corporate_actions(live_ca, max_date, target)
            self.log(f"[DRY-RUN] Found {len(parsed_ca)} actionable corporate actions.")
            for ca in parsed_ca[:5]:
                self.log(f"  • {ca['symbol']} on {ca['ex_date']}: {ca['subject']}")
            self.log("[DRY-RUN] Completed simulation without modifying database files.")
            return {
                "status": "DRY_RUN_SUCCESS",
                "max_date": max_date,
                "missing_dates": missing_dates,
                "parsed_actions": len(parsed_ca)
            }

        # 1. Fetch missing Bhavcopies
        new_bars_list = []
        for d_str in missing_dates:
            self.log(f"Fetching Bhavcopy for {d_str}...")
            df_day = self.fetch_bhavcopy_for_date(d_str)
            if df_day is not None and not df_day.empty:
                new_bars_list.append(df_day)
            else:
                self.log(f"⚠️ Could not obtain Bhavcopy for {d_str}. Skipping.")

        if not new_bars_list:
            self.log("No new Bhavcopy bars were downloaded. Master universe remains unchanged.")
            return {
                "status": "NO_NEW_DATA",
                "max_date": max_date,
                "bars_added": 0
            }

        # 2. Combine new daily bars
        new_bars = pd.concat(new_bars_list, ignore_index=True)
        self.log(f"Downloaded total of {len(new_bars):,} new daily bars.")

        # 3. Load existing master universe
        self.log(f"Loading master universe from {self.universe_parquet}...")
        universe_df = pd.read_parquet(self.universe_parquet)
        existing_symbols = set(universe_df["symbol"].unique())

        # If symbol_sector_map exists, also consider its symbols
        if SECTOR_MAP_JSON.exists():
            with open(SECTOR_MAP_JSON, "r", encoding="utf-8") as f:
                sec_map = json.load(f)
            universe_symbols = existing_symbols.union(set(sec_map.keys()))
        else:
            universe_symbols = existing_symbols

        # Filter new bars to universe constituent scrips
        new_bars = new_bars[new_bars["symbol"].isin(universe_symbols)].copy()
        self.log(f"Retained {len(new_bars):,} new bars belonging to {new_bars['symbol'].nunique()} universe symbols.")

        # Load graveyard delisted symbols
        dead_symbols = set()
        if GRAVEYARD_CSV.exists():
            gy_df = pd.read_csv(GRAVEYARD_CSV)
            dead_symbols = set(gy_df[gy_df["status"] == "inactive"]["symbol"].dropna().astype(str).str.strip().str.upper())
        new_bars["is_delisted"] = new_bars["symbol"].isin(dead_symbols)

        # 4. Fetch and apply corporate actions backward
        live_ca = self.fetch_live_corporate_actions()
        parsed_ca = self.parse_corporate_actions(live_ca, max_date, target)
        if parsed_ca:
            universe_df = self.apply_corporate_actions_backward(universe_df, parsed_ca)

        # 5. Concatenate and deduplicate
        combined = pd.concat([universe_df, new_bars[REQUIRED_COLUMNS]], ignore_index=True)
        combined = combined.drop_duplicates(subset=["date", "symbol"], keep="last")
        combined = combined.sort_values(by=["symbol", "date"]).reset_index(drop=True)

        # 6. Validate invariants
        is_valid, msg = self.validate_invariants(combined)
        if not is_valid:
            raise ValueError(f"Universe invariant verification failed: {msg}")

        # 7. Atomic Write
        temp_parquet = self.universe_parquet.with_suffix(".tmp.parquet")
        self.log(f"Writing updated dataset ({len(combined):,} rows) to temporary file {temp_parquet}...")
        combined.to_parquet(temp_parquet, index=False, engine="pyarrow")
        temp_parquet.replace(self.universe_parquet)
        self.log(f"Atomically replaced master universe database at {self.universe_parquet}")

        # 8. Update Metadata Manifest
        new_sha = compute_sha256(self.universe_parquet)
        min_date = str(combined["date"].min())
        updated_max = str(combined["date"].max())
        total_bars = len(combined)
        unique_syms = int(combined["symbol"].nunique())
        delisted_cnt = int(combined[combined["is_delisted"] == True]["symbol"].nunique())
        active_cnt = unique_syms - delisted_cnt

        meta_dict = {
            "universe_name": "NIFTY 500 Point-in-Time Survivorship-Free Database",
            "file_name": self.universe_parquet.name,
            "sha256_hash": new_sha,
            "total_bars": total_bars,
            "unique_symbols": unique_syms,
            "active_symbols": active_cnt,
            "delisted_symbols": delisted_cnt,
            "start_date": min_date,
            "end_date": updated_max,
            "schema": {
                "date": "string (YYYY-MM-DD)",
                "symbol": "string (NSE Ticker)",
                "open": "float64 (Adjusted Open Price)",
                "high": "float64 (Adjusted High Price)",
                "low": "float64 (Adjusted Low Price)",
                "close": "float64 (Adjusted Close Price)",
                "volume": "float64 (Traded Quantity)",
                "is_delisted": "bool (True if graveyard constituent)"
            },
            "invariants_verified": [
                "unique_(symbol, date)_keys",
                "chronological_monotonic_sorting",
                "zero_null_prices",
                "positive_prices_guaranteed"
            ],
            "last_updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        with open(self.metadata_file, "w", encoding="utf-8") as f:
            json.dump(meta_dict, f, indent=2)

        self.log("==================================================================")
        self.log(f"SYNCHRONIZATION COMPLETED SUCCESSFULLY:")
        self.log(f"Date Coverage:  {min_date} to {updated_max}")
        self.log(f"Total Bars:     {total_bars:,} (+{len(new_bars):,} added)")
        self.log(f"New SHA-256:    {new_sha}")
        self.log("==================================================================")

        return {
            "status": "SUCCESS",
            "bars_added": len(new_bars),
            "start_date": min_date,
            "end_date": updated_max,
            "sha256": new_sha
        }


def main():
    parser = argparse.ArgumentParser(description="Automated Market Data Fetcher & Corporate Action Adjuster")
    parser.add_argument("--target-date", type=str, default=None, help="Target synchronization date (YYYY-MM-DD)")
    parser.add_argument("--dry-run", action="store_true", help="Simulate fetch & action parsing without modifying files")

    args = parser.parse_args()
    engine = MarketDataSyncEngine()
    engine.sync_universe_to_date(target_date=args.target_date, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
