#!/usr/bin/env python3
"""
production/sync_nse_sectors.py
Official NSE Total Market Sector Classification Syncer for Project MIP.

Ingests official constituent data from NIFTY Indices:
  URL: https://www.niftyindices.com/IndexConstituent/ind_niftytotalmarket_list.csv
  Cached copy: data/raw_reference/ind_niftytotalmarket_list.csv

Maps the 22 official NSE industries directly to the 12 primary sectors:
  1. Automobile and Auto Components           -> AUTO
  2. Financial Services                       -> FINSERV
  3. Capital Goods                            -> CAPGOODS
  4. Chemicals                                -> CHEMICALS
  5. Construction, Construction Materials,    -> REALTY
     Realty
  6. Consumer Durables, Consumer Services,    -> CONSDUR
     Textiles
  7. Fast Moving Consumer Goods               -> FMCG
  8. Healthcare                               -> PHARMA
  9. Information Technology                   -> IT
  10. Metals & Mining                         -> METALS
  11. Oil Gas & Consumable Fuels, Power       -> ENERGY
  12. Telecommunication, Media Entertainment  -> INFRA_MEDIA
      & Publication, Utilities, Services,
      Forest Materials, Diversified

Merges with historical delisted graveyard records and existing overrides so that
100% of the 1,039 master universe scrips are deterministically mapped.

Exports:
  - data/universe/symbol_sector_map.json
  - /sdcard/Documents/deliverables/symbol_sector_map.json
"""

import sys
import os
import io
import json
import shutil
import urllib.request
import argparse
import datetime
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd

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
UNIVERSE_PARQUET = DATA_DIR / "universe/nifty500_pit_universe.parquet"
OUTPUT_JSON = DATA_DIR / "universe/symbol_sector_map.json"
MIRROR_JSON = get_deliverables_mirror_dir(BASE_DIR) / "symbol_sector_map.json"
LOCAL_CACHE_CSV = DATA_DIR / "raw_reference/ind_niftytotalmarket_list.csv"

PROD_DIR = BASE_DIR / "production"
if str(PROD_DIR) not in sys.path:
    sys.path.insert(0, str(PROD_DIR))

from sector_map import PRIMARY_SECTORS, SECTOR_NAMES, EXPLICIT_OVERRIDES, classify_symbol

NSE_TOTAL_MARKET_URL = "https://www.niftyindices.com/IndexConstituent/ind_niftytotalmarket_list.csv"

# Official NSE Industry to Primary Sector Mapping
INDUSTRY_TO_SECTOR = {
    "Automobile and Auto Components": "AUTO",
    "Financial Services": "FINSERV",
    "Capital Goods": "CAPGOODS",
    "Chemicals": "CHEMICALS",
    "Construction": "REALTY",
    "Construction Materials": "REALTY",
    "Realty": "REALTY",
    "Consumer Durables": "CONSDUR",
    "Consumer Services": "CONSDUR",
    "Textiles": "CONSDUR",
    "Fast Moving Consumer Goods": "FMCG",
    "Healthcare": "PHARMA",
    "Information Technology": "IT",
    "Metals & Mining": "METALS",
    "Oil Gas & Consumable Fuels": "ENERGY",
    "Power": "ENERGY",
    "Telecommunication": "INFRA_MEDIA",
    "Media Entertainment & Publication": "INFRA_MEDIA",
    "Utilities": "INFRA_MEDIA",
    "Services": "INFRA_MEDIA",
    "Diversified": "INFRA_MEDIA",
    "Forest Materials": "INFRA_MEDIA",
}


def log(msg: str):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [NSESectorSync] {msg}")


def fetch_nse_total_market_csv() -> pd.DataFrame:
    """
    Fetches the latest official NIFTY Total Market constituent CSV from NIFTY Indices.
    Falls back to local cache if network request fails.
    """
    LOCAL_CACHE_CSV.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(
        NSE_TOTAL_MARKET_URL,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    )

    try:
        log(f"Downloading official constituent list from {NSE_TOTAL_MARKET_URL}...")
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read()
        log(f"Downloaded {len(content):,} bytes. Caching locally to {LOCAL_CACHE_CSV}...")
        with open(LOCAL_CACHE_CSV, "wb") as f:
            f.write(content)
        df = pd.read_csv(io.BytesIO(content))
        return df
    except Exception as e:
        log(f"Network fetch failed ({e}). Checking local cache...")
        if LOCAL_CACHE_CSV.exists():
            log(f"Loading cached constituent list from {LOCAL_CACHE_CSV}...")
            return pd.read_csv(LOCAL_CACHE_CSV)
        raise RuntimeError(f"Unable to fetch official NSE constituent list and no local cache found: {e}")


def sync_sector_taxonomy(force_download: bool = True) -> Dict[str, str]:
    """
    Synchronizes NSE total market constituent industries and builds the comprehensive
    symbol to sector mapping dictionary.
    """
    log("=" * 70)
    log("SYNCHRONIZING OFFICIAL NSE SECTOR CLASSIFICATION TAXONOMY")
    log("=" * 70)

    # 1. Fetch official NSE constituents
    nse_df = fetch_nse_total_market_csv()
    log(f"Parsed {len(nse_df):,} official NSE constituents across {nse_df['Industry'].nunique()} industries.")

    # 2. Map official NSE symbols to primary sectors
    official_map: Dict[str, str] = {}
    for _, row in nse_df.iterrows():
        sym = str(row.get("Symbol", "")).strip().upper()
        ind = str(row.get("Industry", "")).strip()
        sec = INDUSTRY_TO_SECTOR.get(ind)
        if not sec:
            # Fallback for unexpected industry strings
            sec = classify_symbol(sym, str(row.get("Company Name", "")))
        official_map[sym] = sec

    log(f"Mapped {len(official_map):,} official symbols to 12 primary sectors.")

    # 3. Load all master universe symbols (1,039 scrips)
    if not UNIVERSE_PARQUET.exists():
        raise FileNotFoundError(f"Master universe parquet not found at {UNIVERSE_PARQUET}")

    uni = pd.read_parquet(UNIVERSE_PARQUET, columns=["symbol"])
    universe_symbols = sorted(uni["symbol"].unique())
    log(f"Ingesting master universe database: {len(universe_symbols):,} unique scrips.")

    # 4. Synthesize complete mapping
    final_map: Dict[str, str] = {}
    source_counts = {"official_nse": 0, "explicit_override": 0, "graveyard_fallback": 0}

    for sym in universe_symbols:
        s_upper = sym.upper().strip()
        # High priority overrides
        if s_upper in EXPLICIT_OVERRIDES:
            final_map[sym] = EXPLICIT_OVERRIDES[s_upper]
            source_counts["explicit_override"] += 1
        elif s_upper in official_map:
            final_map[sym] = official_map[s_upper]
            source_counts["official_nse"] += 1
        else:
            # Historical or delisted stock fallback
            sec = classify_symbol(s_upper)
            final_map[sym] = sec
            source_counts["graveyard_fallback"] += 1

    # Invariant Check: 100% mapped, 0 nulls, all valid primary sectors
    assert len(final_map) == len(universe_symbols), "Mismatch between universe symbols and mapping keys!"
    assert all(sec in PRIMARY_SECTORS for sec in final_map.values()), "Invalid sector detected in mapping!"

    # 5. Export reference JSON and mirror
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(final_map, f, indent=2, sort_keys=True)
    log(f"Exported master symbol sector mapping ({len(final_map):,} symbols) to {OUTPUT_JSON}")

    try:
        MIRROR_JSON.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(OUTPUT_JSON, MIRROR_JSON)
        log(f"Mirrored master sector mapping to {MIRROR_JSON}")
    except Exception as e:
        log(f"Note: Could not mirror to {MIRROR_JSON}: {e}")

    # 6. Sector Distribution Summary
    dist = pd.Series(list(final_map.values())).value_counts()
    print("\n" + "=" * 65)
    print("UPDATED MASTER SECTOR TAXONOMY DISTRIBUTION (1,039 SCRIPS)")
    print("=" * 65)
    for sec in PRIMARY_SECTORS:
        cnt = dist.get(sec, 0)
        pct = (cnt / len(final_map)) * 100.0
        print(f"{sec:<13} : {cnt:>4d} ({pct:>5.1f}%) — {SECTOR_NAMES.get(sec, '')}")
    print("-" * 65)
    print(f"Mapping Sources: Official NSE: {source_counts['official_nse']} | "
          f"Overrides: {source_counts['explicit_override']} | "
          f"Graveyard/Classified: {source_counts['graveyard_fallback']}")
    print("=" * 65 + "\n")

    return final_map


def main():
    parser = argparse.ArgumentParser(description="MIP Official NSE Sector Classification Syncer")
    parser.add_argument("--no-download", action="store_true", help="Use local cache without downloading")
    args = parser.parse_args()

    sync_sector_taxonomy(force_download=(not args.no_download))


if __name__ == "__main__":
    main()
