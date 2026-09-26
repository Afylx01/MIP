#!/usr/bin/env python3
"""
production/sector_map.py
Production Sector Taxonomy & Mapping Database for Project MIP.

Maps 100% of symbols in data/universe/nifty500_pit_universe.parquet to the
12 primary NSE sectors:
  1. AUTO         : Automobile & Auto Components
  2. FINSERV      : Banking & Financial Services
  3. CAPGOODS     : Capital Goods & Industrials
  4. CHEMICALS    : Chemicals & Petrochemicals
  5. REALTY       : Construction & Real Estate
  6. CONSDUR      : Consumer Durables & Apparel
  7. FMCG         : Fast Moving Consumer Goods
  8. PHARMA       : Healthcare & Pharmaceuticals
  9. IT           : Information Technology
  10. METALS      : Metals & Mining
  11. ENERGY      : Oil, Gas & Consumable Fuels
  12. INFRA_MEDIA : Telecommunication, Media & Utilities

Exports mapping to data/universe/symbol_sector_map.json
"""

import sys
import os
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd

BASE_DIR = Path("/storage/emulated/0/Documents/Project MIP")
DATA_DIR = BASE_DIR / "data"
UNIVERSE_PARQUET = DATA_DIR / "universe/nifty500_pit_universe.parquet"
OUTPUT_JSON = DATA_DIR / "universe/symbol_sector_map.json"
MIRROR_JSON = Path("/sdcard/Documents/deliverables/symbol_sector_map.json")

PRIMARY_SECTORS = [
    "AUTO",
    "FINSERV",
    "CAPGOODS",
    "CHEMICALS",
    "REALTY",
    "CONSDUR",
    "FMCG",
    "PHARMA",
    "IT",
    "METALS",
    "ENERGY",
    "INFRA_MEDIA"
]

SECTOR_NAMES = {
    "AUTO": "Automobile & Auto Components",
    "FINSERV": "Banking & Financial Services",
    "CAPGOODS": "Capital Goods & Industrials",
    "CHEMICALS": "Chemicals & Petrochemicals",
    "REALTY": "Construction & Real Estate",
    "CONSDUR": "Consumer Durables & Apparel",
    "FMCG": "Fast Moving Consumer Goods",
    "PHARMA": "Healthcare & Pharmaceuticals",
    "IT": "Information Technology",
    "METALS": "Metals & Mining",
    "ENERGY": "Oil, Gas & Consumable Fuels",
    "INFRA_MEDIA": "Telecommunication, Media & Utilities"
}

# High-priority explicit overrides for key universe symbols
EXPLICIT_OVERRIDES = {
    "CUPID": "PHARMA",
    "STLTECH": "INFRA_MEDIA",
    "MTARTECH": "CAPGOODS",
    "ATHERENERG": "AUTO",
    "SANSERA": "AUTO",
    "HFCL": "INFRA_MEDIA",
    "WELCORP": "METALS",
    "LAURUSLABS": "PHARMA",
    "CPPLUS": "CAPGOODS",
    "RRKABEL": "CAPGOODS",
    "TDPOWERSYS": "CAPGOODS",
    "SKYGOLD": "CONSDUR",
    "AETHER": "CHEMICALS",
    "FEDERALBNK": "FINSERV",
    "AVALON": "CAPGOODS",
    "GRWRHITECH": "CHEMICALS",
    "MCX": "FINSERV",
    "SHILPAMED": "PHARMA",
    "DIACABS": "CAPGOODS",
    "ACUTAAS": "CHEMICALS",
    "DIXON": "CONSDUR",
    "TRENT": "CONSDUR",
    "POLYCAB": "CAPGOODS",
    "NAUKRI": "IT",
    "LTTS": "IT",
    "BHARTI": "INFRA_MEDIA",
    "BEL": "CAPGOODS",
    "HAL": "CAPGOODS",
    "SUNPHAR": "PHARMA",
    "APOLLOH": "PHARMA",
    "MAXHEAL": "PHARMA",
    "CHOLAF": "FINSERV",
    "TVSMOTO": "AUTO",
    "BAJAJ_A": "AUTO",
    "HEROMOT": "AUTO",
    "EICHERM": "AUTO",
    "CIPLA": "PHARMA",
    "DIVISLA": "PHARMA",
    "RELIANCE": "ENERGY",
    "TCS": "IT",
    "INFY": "IT",
    "HDFCBANK": "FINSERV",
    "ICICIBANK": "FINSERV",
    "SBIN": "FINSERV",
    "ITC": "FMCG",
    "HINDUNILVR": "FMCG",
    "LTI": "IT",
    "LTIM": "IT",
    "LTIMINDTRE": "IT",
    "ADANIENT": "INFRA_MEDIA",
    "ADANIPORTS": "INFRA_MEDIA",
    "ADANIGREEN": "INFRA_MEDIA",
    "ADANIPOWER": "INFRA_MEDIA",
    "ATGL": "ENERGY",
    "AWL": "FMCG",
    "TATAMOTORS": "AUTO",
    "M&M": "AUTO",
    "MARUTI": "AUTO",
    "BAJAJ-AUTO": "AUTO",
    "EICHERMOT": "AUTO",
    "HEROMOTOCO": "AUTO",
    "TVSMOTOR": "AUTO",
    "BHARATFORG": "AUTO",
    "SONACOMS": "AUTO",
    "MOTHERSON": "AUTO",
    "BOSCHLTD": "AUTO",
    "MRF": "AUTO",
    "APOLLOTYRE": "AUTO",
    "BALKRISIND": "AUTO",
    "CEAT": "AUTO",
    "EXIDEIND": "AUTO",
    "AMARAJABAT": "AUTO",
    "ARE&M": "AUTO",
    "UNOMINDA": "AUTO",
    "CRAFTSMAN": "AUTO",
    "ENDURANCE": "AUTO",
    "SUNPHARMA": "PHARMA",
    "DRREDDY": "PHARMA",
    "DIVISLAB": "PHARMA",
    "CIPLA": "PHARMA",
    "LUPIN": "PHARMA",
    "AUROPHARMA": "PHARMA",
    "TORNTPHARM": "PHARMA",
    "ALKEM": "PHARMA",
    "MANKIND": "PHARMA",
    "ZYDUSLIFE": "PHARMA",
    "BIOCON": "PHARMA",
    "GLENMARK": "PHARMA",
    "IPCALAB": "PHARMA",
    "AJANTPHARM": "PHARMA",
    "NATCOPHARM": "PHARMA",
    "GRANULES": "PHARMA",
    "JBCHEPHARM": "PHARMA",
    "GLAND": "PHARMA",
    "SYNGENE": "PHARMA",
    "APOLLOHOSP": "PHARMA",
    "MAXHEALTH": "PHARMA",
    "FORTIS": "PHARMA",
    "MEDANTA": "PHARMA",
    "NH": "PHARMA",
    "METROPOLIS": "PHARMA",
    "LALPATHLAB": "PHARMA",
    "WIPRO": "IT",
    "HCLTECH": "IT",
    "TECHM": "IT",
    "PERSISTENT": "IT",
    "COFORGE": "IT",
    "MPHASIS": "IT",
    "TATATECH": "IT",
    "TATAELXSI": "IT",
    "KPITTECH": "IT",
    "CYIENT": "IT",
    "BIRLASOFT": "IT",
    "ZENSARTECH": "IT",
    "SONATSOFTW": "IT",
    "TANLA": "IT",
    "NETWEB": "IT",
    "NEWGEN": "IT",
    "AURIONPRO": "IT",
    "INTELLECT": "IT",
    "HAPPSTMNDS": "IT",
    "OFSS": "IT",
    "KOTAKBANK": "FINSERV",
    "AXISBANK": "FINSERV",
    "INDUSINDBK": "FINSERV",
    "BANKBARODA": "FINSERV",
    "PNB": "FINSERV",
    "CANBK": "FINSERV",
    "UNIONBANK": "FINSERV",
    "IDFCFIRSTB": "FINSERV",
    "BANDHANBNK": "FINSERV",
    "BAJFINANCE": "FINSERV",
    "BAJAJFINSV": "FINSERV",
    "CHOLAFIN": "FINSERV",
    "SHRIRAMFIN": "FINSERV",
    "MUTHOOTFIN": "FINSERV",
    "MANAPPURAM": "FINSERV",
    "SUNDARMFIN": "FINSERV",
    "LTF": "FINSERV",
    "POONAWALLA": "FINSERV",
    "LICI": "FINSERV",
    "HDFCLIFE": "FINSERV",
    "SBILIFE": "FINSERV",
    "ICICIPRULI": "FINSERV",
    "ICICIGI": "FINSERV",
    "BSE": "FINSERV",
    "CDSL": "FINSERV",
    "CAMSLTD": "FINSERV",
    "ANGELONE": "FINSERV",
    "360ONE": "FINSERV",
    "MOTILALOFS": "FINSERV",
    "NAM-INDIA": "FINSERV",
    "HDFCAMC": "FINSERV",
    "UTIAMC": "FINSERV",
    "JIOFIN": "FINSERV",
    "CRISIL": "FINSERV",
    "ICRA": "FINSERV",
    "CAREERP": "FINSERV",
    "LT": "CAPGOODS",
    "SIEMENS": "CAPGOODS",
    "ABB": "CAPGOODS",
    "CUMMINSIND": "CAPGOODS",
    "BHEL": "CAPGOODS",
    "MAZDOCK": "CAPGOODS",
    "COCHINSHIP": "CAPGOODS",
    "GRSE": "CAPGOODS",
    "BEML": "CAPGOODS",
    "DATAPATTNS": "CAPGOODS",
    "KAYNES": "CAPGOODS",
    "SYRMA": "CAPGOODS",
    "ASTRAL": "CAPGOODS",
    "KEI": "CAPGOODS",
    "HAVELLS": "CAPGOODS",
    "FINCABLES": "CAPGOODS",
    "THERMAX": "CAPGOODS",
    "AIAENG": "CAPGOODS",
    "TIMKEN": "CAPGOODS",
    "SKFINDIA": "CAPGOODS",
    "SCHAEFFLER": "CAPGOODS",
    "SUZLON": "CAPGOODS",
    "INOXWIND": "CAPGOODS",
    "CGPOWER": "CAPGOODS",
    "SOLARINDS": "CAPGOODS",
    "ACE": "CAPGOODS",
    "VOLTAS": "CONSDUR",
    "BLUESTARCO": "CONSDUR",
    "TITAN": "CONSDUR",
    "KALYANKJIL": "CONSDUR",
    "SENCO": "CONSDUR",
    "DMART": "CONSDUR",
    "PAGEIND": "CONSDUR",
    "MANYAVAR": "CONSDUR",
    "RAYMOND": "CONSDUR",
    "CAMPUS": "CONSDUR",
    "METROBRAND": "CONSDUR",
    "BATAINDIA": "CONSDUR",
    "RELAXO": "CONSDUR",
    "WHIRLPOOL": "CONSDUR",
    "CROMPTON": "CONSDUR",
    "VGUARD": "CONSDUR",
    "AMBER": "CONSDUR",
    "CELLO": "CONSDUR",
    "VIPIND": "CONSDUR",
    "ETHOSLTD": "CONSDUR",
    "INDHOTEL": "CONSDUR",
    "EIHOTEL": "CONSDUR",
    "CHALET": "CONSDUR",
    "LEMON TREE": "CONSDUR",
    "LEMONTREE": "CONSDUR",
    "TATASTEEL": "METALS",
    "JSWSTEEL": "METALS",
    "JINDALSTEL": "METALS",
    "SAIL": "METALS",
    "NMDC": "METALS",
    "COALINDIA": "METALS",
    "HINDALCO": "METALS",
    "NATIONALUM": "METALS",
    "VEDL": "METALS",
    "HINDZINC": "METALS",
    "JSL": "METALS",
    "RATNAMANI": "METALS",
    "APLAPOLLO": "METALS",
    "MAHLOG": "INFRA_MEDIA",
    "CONCOR": "INFRA_MEDIA",
    "DELHIVERY": "INFRA_MEDIA",
    "BHARTIARTL": "INFRA_MEDIA",
    "INDUSTOWER": "INFRA_MEDIA",
    "TATACOMM": "INFRA_MEDIA",
    "IDEA": "INFRA_MEDIA",
    "TEJASNET": "INFRA_MEDIA",
    "RAILTEL": "INFRA_MEDIA",
    "ZEEL": "INFRA_MEDIA",
    "SUNTV": "INFRA_MEDIA",
    "PVRINOX": "INFRA_MEDIA",
    "SAREGAMA": "INFRA_MEDIA",
    "NTPC": "INFRA_MEDIA",
    "POWERGRID": "INFRA_MEDIA",
    "TATAPOWER": "INFRA_MEDIA",
    "JSWENERGY": "INFRA_MEDIA",
    "TORNTPOWER": "INFRA_MEDIA",
    "NHPC": "INFRA_MEDIA",
    "SJVN": "INFRA_MEDIA",
    "CESC": "INFRA_MEDIA",
    "DLF": "REALTY",
    "LODHA": "REALTY",
    "MACROTECH": "REALTY",
    "GODREJPROP": "REALTY",
    "OBEROIRLTY": "REALTY",
    "PRESTIGE": "REALTY",
    "BRIGADE": "REALTY",
    "SOBHA": "REALTY",
    "PHOENIXLTD": "REALTY",
    "SUNTECK": "REALTY",
    "ULTRACEMCO": "REALTY",
    "AMBUJACEM": "REALTY",
    "ACC": "REALTY",
    "DALBHARAT": "REALTY",
    "SHREECEM": "REALTY",
    "RAMCOCEM": "REALTY",
    "JKCEMENT": "REALTY",
    "PIDILITIND": "CHEMICALS",
    "SRF": "CHEMICALS",
    "AARTIIND": "CHEMICALS",
    "FLUOROCHEM": "CHEMICALS",
    "DEEPAKNTR": "CHEMICALS",
    "TATACHEM": "CHEMICALS",
    "ATUL": "CHEMICALS",
    "VINATIORGA": "CHEMICALS",
    "CLEAN": "CHEMICALS",
    "NAVINFLUOR": "CHEMICALS",
    "PIIND": "CHEMICALS",
    "UPL": "CHEMICALS",
    "COROMANDEL": "CHEMICALS",
    "CHAMBLFERT": "CHEMICALS",
    "GNFC": "CHEMICALS",
    "GSFC": "CHEMICALS",
    "SUMICHEM": "CHEMICALS",
    "ONGC": "ENERGY",
    "OIL": "ENERGY",
    "BPCL": "ENERGY",
    "IOC": "ENERGY",
    "HINDPETRO": "ENERGY",
    "GAIL": "ENERGY",
    "PETRONET": "ENERGY",
    "IGL": "ENERGY",
    "MGL": "ENERGY",
    "GUJGASLTD": "ENERGY",
    "CASTROLIND": "ENERGY",
    "MRPL": "ENERGY",
    "CHENNPETRO": "ENERGY",
    "NESTLEIND": "FMCG",
    "BRITANNIA": "FMCG",
    "DABUR": "FMCG",
    "MARICO": "FMCG",
    "GODREJCP": "FMCG",
    "COLPAL": "FMCG",
    "VBL": "FMCG",
    "TATACONSUM": "FMCG",
    "EMAMILTD": "FMCG",
    "BIKAJI": "FMCG",
    "BECTORFOOD": "FMCG",
    "JYOTHYLAB": "FMCG",
    "RADICO": "FMCG",
    "UNITDSPR": "FMCG",
    "UBL": "FMCG",
}

_MAPPING_CACHE: Optional[Dict[str, str]] = None


def _load_company_names() -> Dict[str, str]:
    """Loads company names from raw reference and graveyard files."""
    names = {}
    eq_file = DATA_DIR / "raw_reference/EQUITY_L.csv"
    if eq_file.exists():
        try:
            eq = pd.read_csv(eq_file)
            names.update(dict(zip(eq['SYMBOL'].str.strip(), eq['NAME OF COMPANY'].str.strip())))
        except Exception:
            pass

    smap_file = DATA_DIR / "symbol_map.parquet"
    if smap_file.exists():
        try:
            smap = pd.read_parquet(smap_file)
            for _, r in smap.iterrows():
                sym = str(r['symbol']).strip()
                n = str(r['scrip_name']).strip() or str(r['eq_name']).strip()
                if sym and n and sym not in names:
                    names[sym] = n
        except Exception:
            pass

    gy_file = DATA_DIR / "verification/survivorship_graveyard.csv"
    if gy_file.exists():
        try:
            gy = pd.read_csv(gy_file)
            for _, r in gy.iterrows():
                sym = str(r['symbol']).strip()
                n = str(r['company_name']).strip()
                if sym and n and sym not in names:
                    names[sym] = n
        except Exception:
            pass

    return names


def classify_symbol(symbol: str, company_name: str = "") -> str:
    """Classifies a symbol into one of the 12 primary sectors."""
    s = symbol.upper().strip()
    n = (company_name or "").upper().strip()

    if s in EXPLICIT_OVERRIDES:
        return EXPLICIT_OVERRIDES[s]

    # 1. FINSERV
    if any(k in n for k in ['BANK', 'FINANC', 'CAPITAL', 'HOLDING', 'INSURANCE', 'INVEST', 'BROKING', 'SECURITIES', 'HOUSING FINANCE', 'MUTUAL FUND', 'VENTURE', 'CREDIT', 'WEALTH', 'ASSET MANAG', 'DISCOUNT', 'FINTECH', 'EXCHANGE', 'PAYMENT', 'CLEARING', 'LEASING', 'FINCORP']):
        return 'FINSERV'

    # 2. PHARMA
    if any(k in n for k in ['PHARMA', 'HEALTH', 'HOSPITAL', 'MEDIC', 'LABORATOR', 'BIOTECH', 'DIAGNOSTIC', 'CLINIC', 'DRUGS', 'DR. REDDY', 'APOLLO HOSP', 'LIFE SCIENCES', 'REMEDIES', 'HEALTHCARE', 'VACCINE', 'BIOPHARMA']):
        return 'PHARMA'

    # 3. IT
    if (any(k in n for k in ['INFOTECH', 'SOFTWARE', 'TECHNOLOGIES', 'TECH', 'CONSULTANCY', 'DIGITAL', 'CYBER', 'SYSTEMS', 'DATA', 'SOLUTIONS', 'INTERNET', 'INFOSYS', 'WIPRO']) and not any(k in n for k in ['POWER SYSTEMS', 'PRECISION', 'THERMAX', 'DIXON', 'AUTO', 'ELECTRO', 'BATTERY', 'CABLES', 'ENGINEERING'])):
        return 'IT'

    # 4. CHEMICALS
    if any(k in n for k in ['CHEMIC', 'CHEM', 'FERTILIZ', 'PESTICID', 'AGROCHEM', 'CARBON', 'PIGMENT', 'DYE', 'ORGANIC', 'FLUOR', 'CHLOR', 'ACID', 'POLYMER', 'RESIN', 'SPECIALTIES', 'PETROCHEM']):
        return 'CHEMICALS'

    # 5. AUTO
    if any(k in n for k in ['MOTORS', 'AUTOMOTIVE', 'AUTOMOBILE', 'TYRES', 'TYRE', 'BATTERIES', 'BATTERY', 'AUTO COMP', 'BRAKES', 'AXLES', 'FORGINGS', 'WHEELS', 'GEARS', 'CLUTCH', 'SCOOTERS', 'TRACTORS', 'MOTHERSON']):
        return 'AUTO'

    # 6. METALS
    if any(k in n for k in ['STEEL', 'IRON', 'ALUMINIUM', 'COPPER', 'ZINC', 'MINING', 'MINERAL', 'METALS', 'METAL', 'ALLOY', 'PIPES', 'TUBES', 'SEAMLESS', 'FOIL', 'FOUNDRY', 'CASTINGS', 'METALLURG']):
        return 'METALS'

    # 7. ENERGY
    if any(k in n for k in ['OIL', 'PETROLEUM', 'GAS', 'REFINER', 'LUBRICANT', 'DRILLING', 'HYDROCARBON', 'OFFSHORE', 'FUELS']):
        return 'ENERGY'

    # 8. FMCG
    if any(k in n for k in ['FOOD', 'BEVERAGE', 'BREWER', 'DISTILLER', 'TOBACCO', 'CONSUMER CARE', 'PERSONAL CARE', 'DAIRY', 'TEA', 'COFFEE', 'SUGAR', 'EDIBLE', 'AGRO FOOD', 'SPICES', 'CONFECTION', 'BISCUITS', 'SNACKS', 'BREW', 'SOAP', 'DETERGENT', 'FLOUR', 'MILLS']):
        return 'FMCG'

    # 9. REALTY
    if (any(k in n for k in ['REALTY', 'PROPERTIES', 'ESTATE', 'DEVELOPER', 'CONSTRUCTION', 'INFRASTRUCTURE', 'HOUSING', 'INFRA', 'BUILD', 'PROJECTS', 'CEMENT', 'TILES', 'CERAMIC']) and not any(k in n for k in ['TELECOM', 'TOWER', 'POWER', 'PORT'])):
        return 'REALTY'

    # 10. CONSDUR
    if any(k in n for k in ['JEWELL', 'FOOTWEAR', 'APPAREL', 'TEXTIL', 'GARMENT', 'RETAIL', 'WATCH', 'LUGGAGE', 'FURNITUR', 'APPLIANCE', 'DURABLE', 'CROCKERY', 'HOME SOLUTION', 'ELECTRONIC', 'FASHION', 'LIFESTYLE', 'HOTEL', 'RESORT', 'HOSPITALITY', 'WEAR', 'SILK', 'COTTON', 'FIBRES']):
        return 'CONSDUR'

    # 11. INFRA_MEDIA
    if any(k in n for k in ['TELECOM', 'COMMUNICATION', 'MEDIA', 'ENTERTAIN', 'BROADCAST', 'NETWORK', 'POWER', 'ELECTRIC', 'ENERGY', 'UTILITY', 'SOLAR', 'WIND', 'THERMAL', 'PORTS', 'PORT', 'LOGISTICS', 'SHIPPING', 'TRANSPORT', 'AIRPORT', 'EXPRESSWAY', 'RAIL']):
        return 'INFRA_MEDIA'

    # 12. CAPGOODS (default / broad engineering & industrials)
    return 'CAPGOODS'


def get_sector_map(force_refresh: bool = False) -> Dict[str, str]:
    """Returns the master dictionary mapping symbol to sector."""
    global _MAPPING_CACHE
    if _MAPPING_CACHE is not None and not force_refresh:
        return _MAPPING_CACHE

    if OUTPUT_JSON.exists() and not force_refresh:
        try:
            with open(OUTPUT_JSON, "r", encoding="utf-8") as f:
                _MAPPING_CACHE = json.load(f)
                return _MAPPING_CACHE
        except Exception:
            pass

    # Build mapping dynamically
    names = _load_company_names()
    mapping = {}

    if UNIVERSE_PARQUET.exists():
        uni = pd.read_parquet(UNIVERSE_PARQUET, columns=["symbol"])
        all_syms = sorted(uni["symbol"].unique())
    else:
        all_syms = sorted(list(names.keys()))

    for sym in all_syms:
        comp_name = names.get(sym, sym)
        sec = classify_symbol(sym, comp_name)
        mapping[sym] = sec

    _MAPPING_CACHE = mapping
    return mapping


def get_sector(symbol: str) -> str:
    """Helper function returning sector for a single symbol."""
    s_clean = symbol.upper().strip()
    s_map = get_sector_map()
    return s_map.get(s_clean, classify_symbol(s_clean))


def export_sector_map(output_path: Optional[Path] = None) -> Path:
    """Exports symbol sector map to JSON and mirrors to shared storage."""
    dest_path = Path(output_path) if output_path else OUTPUT_JSON
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    mapping = get_sector_map(force_refresh=True)
    with open(dest_path, "w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=2, sort_keys=True)
    print(f"Exported symbol sector mapping ({len(mapping):,} symbols) to {dest_path}")

    try:
        MIRROR_JSON.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(dest_path, MIRROR_JSON)
        print(f"Mirrored symbol sector mapping to {MIRROR_JSON}")
    except Exception as e:
        print(f"Note: Could not mirror to {MIRROR_JSON}: {e}")

    return dest_path


def main():
    dest = export_sector_map()
    mapping = get_sector_map()
    counts = pd.Series(list(mapping.values())).value_counts()
    print("\n================== SECTOR DISTRIBUTION ==================")
    for sec in PRIMARY_SECTORS:
        cnt = counts.get(sec, 0)
        pct = (cnt / len(mapping)) * 100.0 if len(mapping) > 0 else 0.0
        print(f"{sec:<12} : {cnt:>4d} ({pct:>5.1f}%) — {SECTOR_NAMES.get(sec, '')}")
    print("=========================================================\n")


if __name__ == "__main__":
    main()
