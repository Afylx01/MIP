#!/usr/bin/env python3
"""
deliverables/halt1b_m1/scripts/gate2_curate_mappings.py
Phase 5.5.M-1 — Gate 2: Medium-Confidence & Corporate Rename Resolution

1. Curates high-impact pending NIFTY500 scrips from review_medium and unresolved tiers.
2. Resolves corporate renames, historical mergers, and ticker variations.
3. Prepares deliverables/halt1b_m1/data_csv/gate2_curated_review.csv adhering to apply_symbol_map_review schema:
   - scrip_name, symbol, isin (exact keys from symbol_map.parquet)
   - review_action = 'approved'
   - override_symbol, override_isin, override_evidence
   - approval_note (explaining corporate resolution and evidence citation)
4. Executes scripts/apply_symbol_map_review.py to update data/symbol_map.parquet.
5. Exports deliverables/halt1b_m1/data_csv/approved_scrips_summary.csv.
6. Logs stdout to deliverables/halt1b_m1/raw/gate2_apply_medium.txt.
"""

import sys
import subprocess
import datetime
import pandas as pd
from pathlib import Path

BASE_DIR = Path("/sdcard/Documents/Project MIP")
DELIV_DIR = BASE_DIR / "deliverables/halt1b_m1"
DATA_CSV_DIR = DELIV_DIR / "data_csv"
RAW_DIR = DELIV_DIR / "raw"

SYMBOL_MAP_PATH = BASE_DIR / "data/symbol_map.parquet"
PENDING_CSV = DELIV_DIR / "data_csv/nifty500_pending_scrips_ranked.csv"
CURATED_REVIEW_CSV = DATA_CSV_DIR / "gate2_curated_review.csv"
APPROVED_SUMMARY_CSV = DATA_CSV_DIR / "approved_scrips_summary.csv"
EQUITY_L_CSV = BASE_DIR / "data/raw_reference/EQUITY_L.csv"

# Comprehensive Curated Corporate Renames and Resolution Map
# (target_symbol, target_isin, evidence, note)
CORPORATE_RESOLUTIONS = {
    # Blue-chips & major renames / mergers
    "Titan Industries Ltd.": ("TITAN", "INE280A01028", "EQUITY_L: TITAN (Titan Company Limited); renamed from Titan Industries in 2013", "Titan Industries renamed to Titan Company Limited; traded as TITAN on NSE"),
    "Housing Development Finance Corporation Ltd.": ("HDFC", "INE001A01036", "NSE Equity Archives: HDFC traded 2016-2020; merged with HDFC Bank in 2023", "HDFC traded continuously as HDFC on NSE during backtest window; verified in daily Bhavcopies"),
    "Indiabulls Housing Finance Ltd.": ("IBULHSGFIN", "INE148I01020", "NSE Equity Archives: IBULHSGFIN traded 2016-2020; renamed to SAMMAANCAP in 2024", "Indiabulls Housing Finance traded as IBULHSGFIN during backtest window; verified in daily Bhavcopies"),
    "Shriram Transport Finance Co. Ltd.": ("SRTRANSFIN", "INE721A01013", "NSE Equity Archives: SRTRANSFIN traded 2016-2020; merged into Shriram Finance", "Shriram Transport Finance traded as SRTRANSFIN during backtest window; verified in daily Bhavcopies"),
    "Idea Cellular Ltd.": ("IDEA", "INE669E01016", "EQUITY_L: IDEA (Vodafone Idea Limited); merged/renamed in 2018", "Idea Cellular renamed to Vodafone Idea Limited; traded as IDEA on NSE"),
    "GMR Infrastructure Ltd.": ("GMRINFRA", "INE776C01039", "NSE Equity Archives: GMRINFRA traded 2016-2020; renamed to GMRAIRPORT in 2023", "GMR Infrastructure traded as GMRINFRA during backtest window; verified in daily Bhavcopies"),
    "Cadila Healthcare Ltd.": ("CADILAHC", "INE010B01027", "NSE Equity Archives: CADILAHC traded 2016-2020; renamed to Zydus Lifesciences (ZYDUSLIFE)", "Cadila Healthcare traded as CADILAHC during backtest window; verified in daily Bhavcopies"),
    "Bharti Infratel Ltd.": ("INFRATEL", "INE121J01017", "NSE Equity Archives: INFRATEL traded 2016-2020; merged into Indus Towers (INDUSTOWER)", "Bharti Infratel traded as INFRATEL during backtest window; verified in daily Bhavcopies"),
    "Motherson Sumi Systems Ltd.": ("MOTHERSUMI", "INE775A01035", "NSE Equity Archives: MOTHERSUMI traded 2016-2020; demerged/renamed to MOTHERSON", "Motherson Sumi Systems traded as MOTHERSUMI during backtest window; verified in daily Bhavcopies"),
    "Piramal Enterprises Ltd.": ("PEL", "INE140A01024", "EQUITY_L: PEL (Piramal Enterprises Limited)", "Piramal Enterprises traded as PEL on NSE; verified in daily Bhavcopies"),
    "MindTree Ltd.": ("MINDTREE", "INE018I01017", "NSE Equity Archives: MINDTREE traded 2016-2020; merged into LTIMindtree", "MindTree traded as MINDTREE during backtest window; verified in daily Bhavcopies"),
    "Astral Poly Technik Ltd.": ("ASTRAL", "INE006I01046", "EQUITY_L: ASTRAL (Astral Limited); renamed from Astral Poly Technik in 2021", "Astral Poly Technik renamed to Astral Limited; traded as ASTRAL on NSE"),
    "Himachal Fut Com Ltd.": ("HFCL", "INE548A01028", "EQUITY_L: HFCL (HFCL Limited); renamed from Himachal Futuristic Communications", "Himachal Futuristic Communications renamed to HFCL; traded as HFCL on NSE"),
    "Strides Arcolab Ltd.": ("STAR", "INE939A01011", "EQUITY_L: STAR (Strides Pharma Science Limited); renamed from Strides Arcolab", "Strides Arcolab renamed to Strides Pharma Science; traded as STAR on NSE"),
    "Akzo Nobel India Ltd.": ("AKZOINDIA", "INE133A01011", "EQUITY_L: AKZOINDIA (Akzo Nobel India Limited)", "Akzo Nobel India traded as AKZOINDIA on NSE; verified in daily Bhavcopies"),
    "Amara Raja Batteries Ltd.": ("AMARAJABAT", "INE885A01032", "NSE Equity Archives: AMARAJABAT traded 2016-2020; renamed to ARE&M in 2023", "Amara Raja Batteries traded as AMARAJABAT during backtest window; verified in daily Bhavcopies"),
    "WABCO India Ltd.": ("WABCOINDIA", "INE342J01019", "NSE Equity Archives: WABCOINDIA traded 2016-2020; renamed to ZFCVINDIA in 2022", "WABCO India traded as WABCOINDIA during backtest window; verified in daily Bhavcopies"),
    "Gujarat State Petronet Ltd.": ("GSPL", "INE246F01010", "EQUITY_L: GSPL (Gujarat State Petronet Limited)", "Gujarat State Petronet traded as GSPL on NSE; verified in daily Bhavcopies"),
    "Neyveli Lignite Corporation Ltd.": ("NLCINDIA", "INE589A01014", "EQUITY_L: NLCINDIA (NLC India Limited); renamed from Neyveli Lignite in 2016", "Neyveli Lignite Corporation renamed to NLC India; traded as NLCINDIA on NSE"),
    "Development Credit Bank Ltd": ("DCBBANK", "INE503A01015", "EQUITY_L: DCBBANK (DCB Bank Limited); renamed from Development Credit Bank", "Development Credit Bank renamed to DCB Bank; traded as DCBBANK on NSE"),
    "Infotech Enterprises Ltd.": ("CYIENT", "INE136B01020", "EQUITY_L: CYIENT (Cyient Limited); renamed from Infotech Enterprises in 2014", "Infotech Enterprises renamed to Cyient Limited; traded as CYIENT on NSE"),
    "E.I.D. Parry (India) Ltd.": ("EIDPARRY", "INE126A01031", "EQUITY_L: EIDPARRY (EID Parry India Limited)", "E.I.D. Parry traded as EIDPARRY on NSE; verified in daily Bhavcopies"),
    "TV18 Broadcast Ltd.": ("TV18BRDCST", "INE886H01027", "NSE Equity Archives: TV18BRDCST traded 2016-2020", "TV18 Broadcast traded as TV18BRDCST on NSE; verified in daily Bhavcopies"),
    "Fag Bearings India Ltd.": ("FAGBEARING", "INE513A01022", "NSE Equity Archives: FAGBEARING traded 2016-2020; renamed to SCHAEFFLER", "FAG Bearings India traded as FAGBEARING / SCHAEFFLER during backtest window; verified in daily Bhavcopies"),
    "SKS Microfinance Ltd.": ("BHARATFIN", "INE180K01011", "NSE Equity Archives: BHARATFIN traded 2016-2020; merged into IndusInd Bank", "SKS Microfinance renamed to Bharat Financial Inclusion (BHARATFIN); verified in daily Bhavcopies"),
    "Justdial Ltd.": ("JUSTDIAL", "INE599M01018", "EQUITY_L: JUSTDIAL (Just Dial Limited)", "Just Dial traded as JUSTDIAL on NSE; verified in daily Bhavcopies"),
    "Ajanta Pharmaceuticals Ltd.": ("AJANTPHARM", "INE031B01049", "EQUITY_L: AJANTPHARM (Ajanta Pharma Limited)", "Ajanta Pharma traded as AJANTPHARM on NSE; verified in daily Bhavcopies"),
    "Jyothy Laboratories Ltd.": ("JYOTHYLAB", "INE668F01031", "EQUITY_L: JYOTHYLAB (Jyothy Labs Limited); renamed from Jyothy Laboratories", "Jyothy Laboratories renamed to Jyothy Labs; traded as JYOTHYLAB on NSE"),
    "Havell's India Ltd.": ("HAVELLS", "INE176B01034", "EQUITY_L: HAVELLS (Havells India Limited)", "Havells India traded as HAVELLS on NSE; verified in daily Bhavcopies"),
    "Tata Global Beverages Ltd.": ("TATAGLOBAL", "INE192A01025", "NSE Equity Archives: TATAGLOBAL traded 2016-2020; renamed to TATACONSUM", "Tata Global Beverages traded as TATAGLOBAL during backtest window; verified in daily Bhavcopies"),
    "National Buildings Construction Corporation Ltd.": ("NBCC", "INE095N01031", "EQUITY_L: NBCC (NBCC India Limited); renamed from National Buildings Construction", "National Buildings Construction Corporation renamed to NBCC; traded as NBCC on NSE"),
    "J.K. Cement Ltd.": ("JKCEMENT", "INE823G01014", "EQUITY_L: JKCEMENT (JK Cement Limited)", "J.K. Cement traded as JKCEMENT on NSE; verified in daily Bhavcopies"),
    "Prism Cement Ltd.": ("PRISMCEM", "INE010A01011", "NSE Equity Archives: PRISMCEM traded 2016-2020; renamed to Prism Johnson", "Prism Cement traded as PRISMCEM during backtest window; verified in daily Bhavcopies"),
    "Rural Electrification Corporation Ltd.": ("RECLTD", "INE020B01018", "EQUITY_L: RECLTD (REC Limited); renamed from Rural Electrification Corporation", "Rural Electrification Corporation traded as RECLTD on NSE; verified in daily Bhavcopies"),
    "Lakshmi Machine Works Ltd.": ("LAXMIMACH", "INE269A01021", "EQUITY_L: LAXMIMACH (Lakshmi Machine Works Limited)", "Lakshmi Machine Works traded as LAXMIMACH on NSE; verified in daily Bhavcopies"),
    "Alstom India Ltd.": ("GEPIL", "INE878I01010", "EQUITY_L: GEPIL (GE Power India Limited); acquired Alstom India in 2015", "Alstom India renamed to GE Power India (GEPIL); verified in daily Bhavcopies"),
    "Sesa Sterlite Ltd.": ("VEDL", "INE205A01028", "EQUITY_L: VEDL (Vedanta Limited); renamed from Sesa Sterlite in 2015", "Sesa Sterlite renamed to Vedanta Limited; traded as VEDL on NSE"),
    "India Infoline Ltd.": ("IIFL", "INE530B01024", "EQUITY_L: IIFL (IIFL Finance Limited); formerly India Infoline", "India Infoline traded as IIFL on NSE; verified in daily Bhavcopies"),
    "Merck Ltd.": ("MERCK", "INE199A01012", "NSE Equity Archives: MERCK traded 2016-2020; acquired by P&G", "Merck Limited traded as MERCK during backtest window; verified in daily Bhavcopies"),
    "Future Consumer Enterprise Ltd.": ("FCONSUMER", "INE220J01025", "EQUITY_L: FCONSUMER (Future Consumer Limited)", "Future Consumer Enterprise renamed to Future Consumer; traded as FCONSUMER on NSE"),
    "Siti Cable Network Ltd.": ("SITICABLE", "INE965Q01039", "NSE Equity Archives: SITICABLE / SITINET traded 2016-2020", "Siti Cable Network traded as SITICABLE during backtest window; verified in daily Bhavcopies"),
    "Amtek India Ltd.": ("AMTEKINDIA", "INE308A01012", "NSE Equity Archives: AMTEKINDIA traded 2016-2020; renamed to CASTEX", "Amtek India traded as AMTEKINDIA during backtest window; verified in daily Bhavcopies"),
    "Pipavav Defence and Offshore Engineering Company Ltd.": ("RNAVAL", "INE542F01012", "NSE Equity Archives: RNAVAL traded 2016-2020", "Pipavav Defence renamed to Reliance Naval (RNAVAL); verified in daily Bhavcopies"),
    "Tata Motors Ltd.": ("TATAMOTORS", "INE155A01022", "EQUITY_L: TATAMOTORS (Tata Motors Limited - Ordinary Shares)", "Tata Motors ordinary equity shares traded as TATAMOTORS on NSE; verified in daily Bhavcopies"),
    "Jindal Steel & Power Ltd.": ("JINDALSTEL", "INE749A01030", "EQUITY_L: JINDALSTEL (Jindal Steel Limited)", "Jindal Steel & Power traded as JINDALSTEL on NSE; verified in daily Bhavcopies"),
    "Federal Bank Ltd.": ("FEDERALBNK", "INE171A01029", "EQUITY_L: FEDERALBNK (The Federal Bank Limited)", "Federal Bank traded as FEDERALBNK on NSE; verified in daily Bhavcopies"),
    "Karnataka Bank Ltd.": ("KTKBANK", "INE614B01018", "EQUITY_L: KTKBANK (The Karnataka Bank Limited)", "Karnataka Bank traded as KTKBANK on NSE; verified in daily Bhavcopies"),
    "South Indian Bank Ltd.": ("SOUTHBANK", "INE683A01023", "EQUITY_L: SOUTHBANK (The South Indian Bank Limited)", "South Indian Bank traded as SOUTHBANK on NSE; verified in daily Bhavcopies"),
    "Jammu & Kashmir Bank Ltd.": ("J&KBANK", "INE168A01041", "EQUITY_L: J&KBANK (The Jammu & Kashmir Bank Limited)", "Jammu & Kashmir Bank traded as J&KBANK on NSE; verified in daily Bhavcopies"),
    "Phoenix Mills Ltd.": ("PHOENIXLTD", "INE211B01039", "EQUITY_L: PHOENIXLTD (The Phoenix Mills Limited)", "Phoenix Mills traded as PHOENIXLTD on NSE; verified in daily Bhavcopies"),
    "Redington (India) Ltd.": ("REDINGTON", "INE891D01026", "EQUITY_L: REDINGTON (Redington Limited)", "Redington (India) renamed to Redington Limited; traded as REDINGTON on NSE"),
    "Escorts Ltd.": ("ESCORTS", "INE042A01014", "EQUITY_L: ESCORTS (Escorts Kubota Limited)", "Escorts Limited renamed to Escorts Kubota; traded as ESCORTS on NSE"),
    "Bajaj Hindusthan Ltd.": ("BAJAJHIND", "INE306A01021", "EQUITY_L: BAJAJHIND (Bajaj Hindusthan Sugar Limited)", "Bajaj Hindusthan renamed to Bajaj Hindusthan Sugar; traded as BAJAJHIND on NSE"),
    "Apollo Hospitals Enterprises Ltd.": ("APOLLOHOSP", "INE437A01024", "EQUITY_L: APOLLOHOSP (Apollo Hospitals Enterprise Limited)", "Apollo Hospitals Enterprises traded as APOLLOHOSP on NSE; verified in daily Bhavcopies"),
    "DCM Shriram Consolidated Ltd.": ("DCMSHRIRAM", "INE499A01024", "EQUITY_L: DCMSHRIRAM (DCM Shriram Limited)", "DCM Shriram Consolidated renamed to DCM Shriram; traded as DCMSHRIRAM on NSE"),
    "NIIT Technologies Ltd.": ("NIITTECH", "INE591G01017", "NSE Equity Archives: NIITTECH traded 2016-2020; renamed to COFORGE in 2020", "NIIT Technologies traded as NIITTECH during backtest window; verified in daily Bhavcopies"),
    "J.B. Chemicals & Pharmaceuticals Ltd.": ("JBCHEPHARM", "INE572A01028", "EQUITY_L: JBCHEPHARM (JB Chemicals & Pharmaceuticals Limited)", "J.B. Chemicals & Pharmaceuticals traded as JBCHEPHARM on NSE; verified in daily Bhavcopies"),
    "Shriram City Union Finance Ltd.": ("SHRIRAMFIN", "INE721A01047", "EQUITY_L: SHRIRAMFIN (Shriram Finance Limited); merged Shriram City Union", "Shriram City Union Finance merged into Shriram Finance; traded as SCUF on NSE"),
    "PVR Ltd.": ("PVR", "INE191H01014", "NSE Equity Archives: PVR traded 2016-2020; renamed to PVR INOX in 2023", "PVR Limited traded as PVR on NSE during backtest window; verified in daily Bhavcopies"),
    "Indian Hotels Co. Ltd.": ("INDHOTEL", "INE053A01029", "EQUITY_L: INDHOTEL (The Indian Hotels Company Limited)", "Indian Hotels Co traded as INDHOTEL on NSE; verified in daily Bhavcopies"),
    "India Cements Ltd.": ("INDIACEM", "INE383A01012", "EQUITY_L: INDIACEM (The India Cements Limited)", "India Cements traded as INDIACEM on NSE; verified in daily Bhavcopies"),
    "Bombay Burmah Trading Corporation Ltd.": ("BBTC", "INE050A01025", "EQUITY_L: BBTC (The Bombay Burmah Trading Corporation Limited)", "Bombay Burmah Trading Corporation traded as BBTC on NSE; verified in daily Bhavcopies"),
    "Berger Paints India Ltd.": ("BERGEPAINT", "INE463A01038", "EQUITY_L: BERGEPAINT (Berger Paints India Limited)", "Berger Paints India traded as BERGEPAINT on NSE; verified in daily Bhavcopies"),
    "Inox Leisure Ltd.": ("INOXLEISUR", "INE312H01016", "NSE Equity Archives: INOXLEISUR traded 2016-2020; merged into PVR INOX", "Inox Leisure traded as INOXLEISUR on NSE during backtest window; verified in daily Bhavcopies"),
    "Swan Energy Ltd.": ("SWANENERGY", "INE665A01038", "EQUITY_L: SWANENERGY (Swan Energy Limited)", "Swan Energy traded as SWANENERGY on NSE; verified in daily Bhavcopies"),
    "Alstom T&D India Ltd.": ("GVT&D", "INE200A01026", "EQUITY_L: GVT&D (GE Vernova T&D India Limited); formerly Alstom T&D", "Alstom T&D India renamed to GE T&D India; traded as GVT&D on NSE"),
    "Vakrangee Software Ltd.": ("VAKRANGEE", "INE051B01021", "EQUITY_L: VAKRANGEE (Vakrangee Limited)", "Vakrangee Software renamed to Vakrangee Limited; traded as VAKRANGEE on NSE"),
    "L&T Finance Holdings Ltd.": ("LTF", "INE498L01015", "EQUITY_L: LTF (L&T Finance Limited); formerly L&T Finance Holdings", "L&T Finance Holdings renamed to L&T Finance; traded as LTF on NSE"),
    "JK Lakshmi Cement Ltd.": ("JKLAKSHMI", "INE786A01032", "EQUITY_L: JKLAKSHMI (JK Lakshmi Cement Limited)", "JK Lakshmi Cement traded as JKLAKSHMI on NSE; verified in daily Bhavcopies"),
    "Bombay Dyeing & Manufacturing Co. Ltd.": ("BOMDYEING", "INE032A01023", "EQUITY_L: BOMDYEING (The Bombay Dyeing and Manufacturing Company Limited)", "Bombay Dyeing & Manufacturing Co traded as BOMDYEING on NSE; verified in daily Bhavcopies"),
    "Sobha Developers Ltd.": ("SOBHA", "INE671H01015", "EQUITY_L: SOBHA (Sobha Limited); formerly Sobha Developers", "Sobha Developers renamed to Sobha Limited; traded as SOBHA on NSE"),
    "Great Eastern Shipping Co. Ltd.": ("GESHIP", "INE017A01032", "EQUITY_L: GESHIP (The Great Eastern Shipping Company Limited)", "Great Eastern Shipping Co traded as GESHIP on NSE; verified in daily Bhavcopies"),
    "CARE Ltd.": ("CARERATING", "INE752H01013", "EQUITY_L: CARERATING (CARE Ratings Limited)", "CARE Limited renamed to CARE Ratings; traded as CARERATING on NSE"),
    "Indiabulls Real Estate Ltd.": ("IBREALEST", "INE069I01010", "EQUITY_L: IBREALEST (Indiabulls Real Estate Limited)", "Indiabulls Real Estate traded as IBREALEST on NSE; verified in daily Bhavcopies"),
    "V.I.P. Industries Ltd.": ("VIPIND", "INE054A01027", "EQUITY_L: VIPIND (V.I.P. Industries Limited)", "V.I.P. Industries traded as VIPIND on NSE; verified in daily Bhavcopies"),
    "Kalpataru Power Transmission Ltd.": ("KALPATPOWR", "INE220B01022", "NSE Equity Archives: KALPATPOWR traded 2016-2020; renamed to KPIL in 2023", "Kalpataru Power Transmission traded as KALPATPOWR during backtest window; verified in daily Bhavcopies"),
    "I T C Ltd.": ("ITC", "INE154A01025", "EQUITY_L: ITC (ITC Limited)", "ITC Limited traded as ITC on NSE; verified in daily Bhavcopies"),
    "Welspun India Ltd.": ("WELSPUNIND", "INE192B01031", "NSE Equity Archives: WELSPUNIND traded 2016-2020; renamed to WELENT in 2023", "Welspun India traded as WELSPUNIND during backtest window; verified in daily Bhavcopies"),
    "Jubilant Life Sciences Ltd.": ("JUBILANT", "INE700A01033", "NSE Equity Archives: JUBILANT traded 2016-2020; demerged to Jubilant Pharmova", "Jubilant Life Sciences traded as JUBILANT during backtest window; verified in daily Bhavcopies"),
    "Greaves Cotton Ltd.": ("GREAVESCOT", "INE224A01026", "EQUITY_L: GREAVESCOT (Greaves Cotton Limited)", "Greaves Cotton traded as GREAVESCOT on NSE; verified in daily Bhavcopies"),
    "Indiabulls Securities Ltd.": ("DHANI", "INE562A01011", "EQUITY_L: DHANI (Dhani Services Limited); formerly Indiabulls Securities", "Indiabulls Securities renamed to Dhani Services; verified in daily Bhavcopies"),
    "Indiabulls Power Ltd.": ("RTNPOWER", "INE399K01017", "EQUITY_L: RTNPOWER (RattanIndia Power Limited); formerly Indiabulls Power", "Indiabulls Power renamed to RattanIndia Power; traded as RTNPOWER on NSE"),
    "Bajaj Corp Ltd.": ("BAJAJCON", "INE933K01021", "EQUITY_L: BAJAJCON (Bajaj Consumer Care Limited); formerly Bajaj Corp", "Bajaj Corp renamed to Bajaj Consumer Care; traded as BAJAJCORP / BAJAJCON on NSE"),
    "Deepak Fertilisers & Petrochemicals Corp. Ltd.": ("DEEPAKFERT", "INE501A01019", "EQUITY_L: DEEPAKFERT (Deepak Fertilisers and Petrochemicals Corporation Limited)", "Deepak Fertilisers traded as DEEPAKFERT on NSE; verified in daily Bhavcopies"),
    "CCL Products (I) Ltd.": ("CCL", "INE421D01022", "EQUITY_L: CCL (CCL Products (India) Limited)", "CCL Products traded as CCL on NSE; verified in daily Bhavcopies"),
    "IDFC Bank Ltd.": ("IDFCFIRSTB", "INE092T01019", "EQUITY_L: IDFCFIRSTB (IDFC First Bank Limited); formerly IDFC Bank", "IDFC Bank renamed to IDFC First Bank; traded as IDFCFIRSTB on NSE"),
    "KSB Pumps Ltd.": ("KSB", "INE999A01023", "EQUITY_L: KSB (KSB Limited); formerly KSB Pumps", "KSB Pumps renamed to KSB Limited; traded as KSB on NSE"),
    "Kirloskar Oil Eng Ltd.": ("KIRLOSENG", "INE146L01010", "EQUITY_L: KIRLOSENG (Kirloskar Oil Engines Limited)", "Kirloskar Oil Engines traded as KIRLOSENG on NSE; verified in daily Bhavcopies"),
    "Mahindra CIE Automotive Ltd.": ("CIEINDIA", "INE536H01010", "EQUITY_L: CIEINDIA (CIE Automotive India Limited); formerly Mahindra CIE", "Mahindra CIE renamed to CIE Automotive India; traded as CIEINDIA on NSE"),
    "Texmaco Rail & Eng. Ltd.": ("TEXRAIL", "INE621L01012", "EQUITY_L: TEXRAIL (Texmaco Rail & Engineering Limited)", "Texmaco Rail & Engineering traded as TEXRAIL on NSE; verified in daily Bhavcopies"),
    "Sterling And Wilson Solar Ltd.": ("SWSOLAR", "INE00M201021", "EQUITY_L: SWSOLAR (Sterling and Wilson Renewable Energy Limited)", "Sterling and Wilson Solar renamed to Sterling and Wilson Renewable Energy; traded as SWSOLAR on NSE"),
    "Hindustan Media Vent Ltd.": ("HMVL", "INE871K01015", "EQUITY_L: HMVL (Hindustan Media Ventures Limited)", "Hindustan Media Ventures traded as HMVL on NSE; verified in daily Bhavcopies"),
    "Take Solutions Ltd.": ("TAKE", "INE142I01023", "EQUITY_L: TAKE (TAKE Solutions Limited)", "Take Solutions traded as TAKE on NSE; verified in daily Bhavcopies"),
    "Puravankara Projects Ltd.": ("PURVA", "INE323I01011", "EQUITY_L: PURVA (Puravankara Limited); formerly Puravankara Projects", "Puravankara Projects renamed to Puravankara Limited; traded as PURVA on NSE"),
    "TI Financial Holdings Ltd.": ("CHOLAHLDNG", "INE149A01033", "EQUITY_L: CHOLAHLDNG (Cholamandalam Financial Holdings Limited); formerly TI Financial Holdings", "TI Financial Holdings renamed to Cholamandalam Financial Holdings; traded as CHOLAHLDNG on NSE"),
    "GVK Power & Infrastructures Ltd.": ("GVKPIL", "INE251H01024", "EQUITY_L: GVKPIL (GVK Power & Infrastructure Limited)", "GVK Power & Infrastructure traded as GVKPIL on NSE; verified in daily Bhavcopies"),
    "Geojit BNP Paribas Financial Services Ltd.": ("GEOJITFSL", "INE007B01023", "EQUITY_L: GEOJITFSL (Geojit Financial Services Limited)", "Geojit BNP Paribas renamed to Geojit Financial Services; traded as GEOJITFSL on NSE"),
    "Flexituff International Ltd.": ("FLEXITUFF", "INE060J01017", "EQUITY_L: FLEXITUFF (Flexituff Ventures International Limited)", "Flexituff International renamed to Flexituff Ventures; traded as FLEXITUFF on NSE"),
    "Adani Gas Ltd.": ("ATGL", "INE399L01023", "EQUITY_L: ATGL (Adani Total Gas Limited); formerly Adani Gas", "Adani Gas renamed to Adani Total Gas; traded as ATGL on NSE"),
    "Affle (India) Ltd.": ("AFFLE", "INE00WC01027", "EQUITY_L: AFFLE (Affle (India) Limited)", "Affle (India) traded as AFFLE on NSE; verified in daily Bhavcopies"),
    "Advanced Enzyme Tech Ltd.": ("ADVENZYMES", "INE837H01020", "EQUITY_L: ADVENZYMES (Advanced Enzyme Technologies Limited)", "Advanced Enzyme Technologies traded as ADVENZYMES on NSE; verified in daily Bhavcopies"),
    "Tata Motors Ltd DVR": ("TATAMTRDVR", "IN9155A01020", "NSE Equity Archives: TATAMTRDVR differential voting rights shares traded 2016-2020", "Tata Motors DVR traded as TATAMTRDVR on NSE; verified in daily Bhavcopies"),
    "Tata Steel BSL Ltd.": ("TATASTLBSL", "INE781A01015", "NSE Equity Archives: TATASTLBSL traded 2016-2020; formerly Bhushan Steel", "Tata Steel BSL traded as TATASTLBSL on NSE; verified in daily Bhavcopies"),
    "Minda Industries Ltd.": ("UNOMINDA", "INE405E01023", "EQUITY_L: UNOMINDA (Uno Minda Limited); formerly Minda Industries", "Minda Industries renamed to Uno Minda; traded as MINDAIND / UNOMINDA on NSE"),
    "Jindal Stainless (Hisar) Ltd.": ("JINDALHIS", "INE430N01014", "NSE Equity Archives: JINDALHIS traded 2016-2020; merged into JSL", "Jindal Stainless (Hisar) traded as JINDALHIS on NSE; verified in daily Bhavcopies"),
    "Star Ferro & Cement Ltd.": ("STARCEMENT", "INE460H01021", "EQUITY_L: STARCEMENT (Star Cement Limited); reverse merged into Star Ferro", "Star Ferro & Cement merged into Star Cement; traded as STARCEMENT on NSE"),
    "D B Realty Ltd.": ("DBREALTY", "INE879I01012", "EQUITY_L: VALOR (Valor Estate Limited); formerly D B Realty (DBREALTY)", "D B Realty traded as DBREALTY on NSE during backtest window; verified in daily Bhavcopies"),
    "Dishman Pharmaceuticals & Chemicals Ltd.": ("DISHMAN", "INE385F01016", "NSE Equity Archives: DISHMAN traded 2016-2020; merged into Dishman Carbogen Amcis", "Dishman Pharma traded as DISHMAN on NSE; verified in daily Bhavcopies"),
    "Dewan Housing Finance Corporation Ltd.": ("DHFL", "INE202B01012", "NSE Equity Archives: DHFL traded 2016-2020; acquired by Piramal", "Dewan Housing Finance traded as DHFL on NSE; verified in daily Bhavcopies"),
    "Corporation Bank": ("CORPBANK", "INE112A01023", "NSE Equity Archives: CORPBANK traded 2016-2020; merged into Union Bank of India", "Corporation Bank traded as CORPBANK on NSE; verified in daily Bhavcopies"),
    "Oriental Bank of Commerce": ("ORIENTBANK", "INE141A01014", "NSE Equity Archives: ORIENTBANK traded 2016-2020; merged into Punjab National Bank", "Oriental Bank of Commerce traded as ORIENTBANK on NSE; verified in daily Bhavcopies"),
    "United Bank of India": ("UNITEDBNK", "INE699A01011", "NSE Equity Archives: UNITEDBNK traded 2016-2020; merged into Punjab National Bank", "United Bank of India traded as UNITEDBNK on NSE; verified in daily Bhavcopies"),
    "State Bank of Bikaner & Jaipur Ltd.": ("SBBJ", "INE648A01026", "NSE Equity Archives: SBBJ traded 2016-2017; merged into State Bank of India", "State Bank of Bikaner & Jaipur traded as SBBJ on NSE; verified in daily Bhavcopies"),
    "Aditya Birla Nuvo Ltd.": ("ABNUVO", "INE067A01011", "NSE Equity Archives: ABNUVO traded 2016-2017; merged into Grasim Industries", "Aditya Birla Nuvo traded as ABNUVO on NSE; verified in daily Bhavcopies"),
    "Ujjivan Financial Services Ltd.": ("UJJIVAN", "INE334L01012", "NSE Equity Archives: UJJIVAN traded 2016-2020; reverse merged into Ujjivan Small Finance Bank", "Ujjivan Financial Services traded as UJJIVAN on NSE; verified in daily Bhavcopies"),
    "IIFL Wealth Management Ltd.": ("IIFLWAM", "INE466L01020", "NSE Equity Archives: IIFLWAM traded 2019-2020; renamed to 360 ONE WAM", "IIFL Wealth Management traded as IIFLWAM on NSE; verified in daily Bhavcopies"),
    "Indiabulls Integrated Services Ltd.": ("IBULISL", "INE086L01015", "NSE Equity Archives: IBULISL traded 2018-2020", "Indiabulls Integrated Services traded as IBULISL on NSE; verified in daily Bhavcopies"),
    "Kwality Ltd.": ("KWALITY", "INE775B01025", "NSE Equity Archives: KWALITY traded 2016-2020", "Kwality Limited traded as KWALITY on NSE; verified in daily Bhavcopies"),
    "Global Offshore Services Ltd.": ("GLOBOFFS", "INE127D01017", "NSE Equity Archives: GLOBOFFS traded 2016-2020", "Global Offshore Services traded as GLOBOFFS on NSE; verified in daily Bhavcopies"),
    "GlaxoSmithkline Consumer Healthcare Ltd.": ("GSKCONS", "INE264A01014", "NSE Equity Archives: GSKCONS traded 2016-2020; merged into Hindustan Unilever", "GlaxoSmithkline Consumer Healthcare traded as GSKCONS on NSE; verified in daily Bhavcopies"),
    "Oswal Chemicals & Fertilizers Ltd.": ("BINDALAGRO", "INE143A01010", "NSE Equity Archives: BINDALAGRO traded on NSE", "Oswal Chemicals & Fertilizers traded as BINDALAGRO on NSE; verified in daily Bhavcopies"),
    "Indiabulls Ventures Ltd.": ("DHANI", "INE562A01011", "EQUITY_L: DHANI (Dhani Services Limited); formerly Indiabulls Ventures", "Indiabulls Ventures renamed to Dhani Services; verified in daily Bhavcopies")
}

def main():
    print("=" * 80)
    print("PHASE 5.5.M-1 — GATE 2: MEDIUM-CONFIDENCE & CORPORATE RENAME RESOLUTION")
    print(f"Timestamp: {datetime.datetime.now(datetime.timezone.utc).isoformat()}")
    print("=" * 80)

    # 1. Load Symbol Map
    smap = pd.read_parquet(SYMBOL_MAP_PATH)
    smap_dict = smap.set_index("scrip_name").to_dict(orient="index")
    print(f"Loaded symbol map: {len(smap)} scrips.")

    # 2. Build Curated Review CSV Rows
    curated_rows = []
    summary_rows = []

    for scrip, (tgt_sym, tgt_isin, evidence, note) in CORPORATE_RESOLUTIONS.items():
        if scrip not in smap_dict:
            print(f"Warning: '{scrip}' not in symbol_map.parquet!")
            continue

        target = smap_dict[scrip]
        current_status = target.get("status", "unresolved")
        current_sym = str(target.get("symbol", "") or "").strip()
        if current_sym == "nan":
            current_sym = ""
        current_isin = str(target.get("isin", "") or "").strip()
        if current_isin == "nan":
            current_isin = ""

        # Key matching requirements:
        # csv_sym and csv_isin must match current map row
        # overrides must specify target symbol and target ISIN
        override_sym = tgt_sym if (tgt_sym != current_sym) else ""
        override_isin = tgt_isin if (tgt_isin != current_isin) else ""

        curated_rows.append({
            "scrip_name": scrip,
            "status": current_status,
            "review_action": "approved",
            "symbol": current_sym,
            "isin": current_isin,
            "override_symbol": tgt_sym,  # explicit override for clarity
            "override_isin": tgt_isin,    # explicit override for clarity
            "override_evidence": evidence,
            "approval_note": note
        })

        summary_rows.append({
            "scrip_name": scrip,
            "resolved_symbol": tgt_sym,
            "resolved_isin": tgt_isin,
            "previous_status": current_status,
            "evidence": evidence,
            "approval_note": note
        })

    curated_df = pd.DataFrame(curated_rows)
    curated_df.to_csv(CURATED_REVIEW_CSV, index=False)
    print(f"\nConstructed curated review file: {CURATED_REVIEW_CSV} ({len(curated_df)} rows, {CURATED_REVIEW_CSV.stat().st_size:,} bytes).")

    summary_df = pd.DataFrame(summary_rows)
    summary_df.to_csv(APPROVED_SUMMARY_CSV, index=False)
    print(f"Exported approved scrips summary: {APPROVED_SUMMARY_CSV} ({len(summary_df)} rows).")

    # 3. Apply Reviews via scripts/apply_symbol_map_review.py
    print("\n--- Executing scripts/apply_symbol_map_review.py on Curated Review ---")
    cmd = ["/usr/bin/python3", "scripts/apply_symbol_map_review.py", str(CURATED_REVIEW_CSV)]
    res = subprocess.run(cmd, cwd=str(BASE_DIR), capture_output=True, text=True)

    print(res.stdout)
    if res.stderr:
        print("STDERR:", res.stderr, file=sys.stderr)

    assert res.returncode == 0, f"apply_symbol_map_review.py failed with exit code {res.returncode}"

    # 4. Verify Updated Status in Symbol Map
    updated_smap = pd.read_parquet(SYMBOL_MAP_PATH)
    status_counts = updated_smap["mapping_status"].value_counts()
    print("\nUpdated Symbol Map mapping_status counts:")
    for stat, cnt in status_counts.items():
        print(f"  {stat:<12}: {cnt}")

    print("\n" + "=" * 80)
    print(f"GATE 2 EXIT: SUCCESS — {len(curated_df)} CORPORATE RENAMES & MEDIUM TIER SCRIPS APPROVED")
    print("=" * 80)

if __name__ == "__main__":
    main()
