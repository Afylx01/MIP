# Gate 2b Verification Artifact: Symbol Map Evidence Hardening

> **Target Platform**: Samsung Galaxy S23 (arm64) running PRoot-Distro Ubuntu via Termux.
> **Python Engine**: Ubuntu System Python (`/usr/bin/python3`) with apt-managed `python3-pandas`, `python3-pyarrow`, `python3-xlrd`.
> **Integrity Mode**: Development
> **HALT State**: HALT-1b Active (Gate 2 complete; stop and report to user).

---

## Executive Summary & Gate 2b Deliverables

1. **Step 0 — Price Data Inventory & Safe Loading**:
   - Clean unpickling of external scanner caches achieved via custom `pickle.Unpickler` subclass resolving pandas 2.3+ `StringArray`/`NDArrayBacked` tuple differences without monkey patching or global state mutation.
   - Wrote [`data/price_cache_export.parquet`](file:///sdcard/Documents/Project%20MIP/data/price_cache_export.parquet): Exactly 1,831,372 rows exported matching source 1:1 (`SHA-256: 8075aa68173e352108aaedd3aa06b025eb3f2641ccb5c8b4a8bd52a15b48b199`).
   - Cache identified as **survivor-only** (all 750 cached symbols trade through 2026-08-31; 0 delisted names).
   - Derived official trading calendar from NSEI bars: 4,649 trading days from 2007-09-17 to 2026-08-31 saved to [`data/trading_calendar.txt`](file:///sdcard/Documents/Project%20MIP/data/trading_calendar.txt).

2. **Step 1 — Gate 1 Repairs**:
   - Quarantined 12 total suspect rows in [`data/quarantine_gate1.parquet`](file:///sdcard/Documents/Project%20MIP/data/quarantine_gate1.parquet): 10 chronological datetime anomalies across sheets + 2 duplicate out-of-order rebalances in `Nifty Dividend Opportunities 50` (Rows 130 and 131: Reliance Capital / National Aluminium).
   - Post-quarantine non-monotonic step count across all 37 sheets is **exactly 0**.
   - Calendar validation on ambiguous rows (day <= 12) restricted to calendar range [2007-09-17, 2026-08-31]: Day-First hit rate is **451 / 451 (100.00%)** vs Month-First **349 / 451 (77.38%)** (1,182 rows outside range).
   - Exact duplicates removed: **8 rows** (before: 10, after: 8).
   - Main event dataset saved to [`data/index_events.parquet`](file:///sdcard/Documents/Project%20MIP/data/index_events.parquet) (9,121 rows).

3. **Step 2 — Gate 0 Restatement**:
   - Extracted text from `data/raw_bulletins/nifty_replacement_circular_sep_2020.pdf` and `niftyindices___rebalancing_schedule_200.html`.
   - Formally restated Gate 0 finding: *"post-2020-09 bulletin availability NOT ESTABLISHED; deferred to Phase 5.6"*.

4. **Step 3 — Symbol Map Rebuild with Evidence Screens (S1–S6)**:
   - Archived v1 map as [`data/symbol_map_v1.parquet`](file:///sdcard/Documents/Project%20MIP/data/symbol_map_v1.parquet) (`SHA-256: ae982c3e1c22bdcafcf9bec6de28385d7dd3b29d3392ad39935f4e1b0c28fc58`).
   - Removed hardcoded renames from auto logic (`KNOWN_CORPORATE_RENAMES` demoted to `agent_memory`, `low` confidence, flagged `unsourced`).
   - Generated rebuilt [`data/symbol_map.parquet`](file:///sdcard/Documents/Project%20MIP/data/symbol_map.parquet) (1,448 rows): `auto`: 172 (11.9%), `proposed`: 760 (52.5%), `unresolved`: 516 (35.6%).
   - All S1–S6 screens and unioned membership window coverage computed.

5. **Step 4 — Review Tooling Fixes & Refusal Hardening**:
   - Updated [`scripts/review_symbol_map.py`](file:///sdcard/Documents/Project%20MIP/scripts/review_symbol_map.py): only `proposed` rows in review CSVs; `unresolved` written to [`data/symbol_map_unresolved.csv`](file:///sdcard/Documents/Project%20MIP/data/symbol_map_unresolved.csv) (reference only, cannot be approved).
   - Hardened [`scripts/apply_symbol_map_review.py`](file:///sdcard/Documents/Project%20MIP/scripts/apply_symbol_map_review.py): tested 6 distinct refusal paths with zero false permissions.

6. **Step 5 — Canary Regression Test**:
   - Wrote [`data/verification/canaries_2b.csv`](file:///sdcard/Documents/Project%20MIP/data/verification/canaries_2b.csv): **22 / 22 canonical edge cases passed** (all non-auto, status `proposed`/`unresolved`, and appropriately flagged).

7. **Step 6 — Gate 2 Report Recomputation (NIFTY500 Only)**:
   - Other 6 indices marked: *"event log only, not reconstructable"*.
   - Evaluated name-level and price-covered fractions for NIFTY500 with survivorship disclosure note.

---

## Step-by-Step Raw Command Logs

### Step 0: Price Data Inventory and Safe Loading

**Command Executed**:
```bash
python3 scripts/step0_price_inventory.py
```

**Full Raw Output**:
```text
=== STEP 0: PRICE DATA INVENTORY AND SAFE LOADING ===

--- 1. File Inventory ---
Path: /storage/emulated/0/MIP1_Scanner/data/constituents_cache.db | Size: 0.35 MB (368640 bytes) | Format: sqlite | mtime: 2026-08-31 19:45:24
Path: /storage/emulated/0/MIP1_Scanner/data/index__NSEI_cache.pkl | Size: 0.09 MB (98579 bytes) | Format: pickle | mtime: 2026-08-31 05:33:25
Path: /storage/emulated/0/MIP1_Scanner/data/index__NSEI_cache.pkl.gz | Size: 0.03 MB (27101 bytes) | Format: gzip pickle | mtime: 2026-08-30 18:42:51
Path: /storage/emulated/0/MIP1_Scanner/data/manifest.json | Size: 0.00 MB (1364 bytes) | Format: json | mtime: 2026-08-31 19:46:10
Path: /storage/emulated/0/MIP1_Scanner/data/stock_ohlcv_cache.pkl | Size: 119.07 MB (124854530 bytes) | Format: pickle | mtime: 2026-08-31 19:45:33
Path: /storage/emulated/0/MIP1_Scanner/data/stock_ohlcv_cache.pkl.gz | Size: 8.26 MB (8661398 bytes) | Format: gzip pickle | mtime: 2026-08-30 18:51:33

Bhavcopy status: NO Bhavcopy files exist. Only scanner caches exist (stock_ohlcv_cache.pkl, index__NSEI_cache.pkl, etc.).

--- 2. Safe Loading of stock_ohlcv_cache.pkl ---
Source row count: 1831372
Columns: ['symbol', 'date', 'open', 'high', 'low', 'close', 'volume']
Source dtypes:
  symbol: object
  date: object
  open: object
  high: object
  low: object
  close: object
  volume: object

Exported row count: 1831372
Row count check: MATCH (1831372 == 1831372)
Export SHA-256: 8075aa68173e352108aaedd3aa06b025eb3f2641ccb5c8b4a8bd52a15b48b199
Export dtypes:
  symbol: object
  date: object
  open: float64
  high: float64
  low: float64
  close: float64
  volume: float64

--- 3. Symbol Coverage & Delisted Analysis ---
Unique symbols in cache: 750
Date range: 2007-01-02 to 2026-08-31
Symbols whose last bar is before max date (2026-08-31): 0
Coverage type: SURVIVOR-ONLY cache. Exactly 0 symbols stop trading before 2026-08-31; every single one of the 750 cached symbols has active price bars through 2026-08-31. It does NOT include delisted names.

--- 4. Official Trading Calendar Derivation ---
Calendar source: Exported NSEI index bars from /storage/emulated/0/MIP1_Scanner/data/index__NSEI_cache.pkl
Calendar first date: 2007-09-17
Calendar last date: 2026-08-31
Calendar trading day count: 4649
Saved 4649 trading calendar dates to data/trading_calendar.txt
```

**Files Written**:
- [`data/price_cache_export.parquet`](file:///sdcard/Documents/Project%20MIP/data/price_cache_export.parquet)
- [`data/trading_calendar.txt`](file:///sdcard/Documents/Project%20MIP/data/trading_calendar.txt)

---

### Step 1: Gate 1 Repairs

**Command Executed**:
```bash
python3 scripts/gate1_parse_validate.py
```

**Full Raw Output**:
```text
================================================================================
GATE 1 — PARSE AND DATE VALIDATION (GATE 2b REPAIRS)
Source file: IndexInclExcl.xls
================================================================================
Workbook loaded: 37 sheets
Total raw sheets: 37
Total rows in workbook (including headers): 9178
Total event rows parsed: 9141

================================================================================
STEP 2: AMBIGUOUS ROWS VALIDATION (day <= 12)
================================================================================
Total count of ambiguous rows: 1633
Derived Trading Calendar range: 2007-09-17 to 2026-08-31 (4649 trading days)

Ambiguous rows inside trading calendar date range [2007-09-17, 2026-08-31]: 451
  Day-First trading-day hit rate:   451 / 451 (100.00%)
  Month-First trading-day hit rate: 349 / 451 (77.38%)
Ambiguous rows outside calendar range (not tested against calendar): 1182

================================================================================
STEP 3: QUARANTINE SUSPECT ROWS
================================================================================
Total Quarantined rows count: 12 (10 chronological anomalies + 2 duplicate anomalies in Div Opp 50)

All Quarantined rows in full:
   1. Sheet: 'Nifty 200                       ' | Row: 348   | Date: 2017-09-05 | Scrip: 'Reliance Capital Ltd.              ' | Action: OUT | ctype: datetime
   2. Sheet: 'Nifty 200                       ' | Row: 354   | Date: 2017-09-05 | Scrip: 'Max Financial Services Ltd.        ' | Action: IN  | ctype: datetime
   3. Sheet: 'Nifty Midcap 100                ' | Row: 392   | Date: 2017-09-05 | Scrip: 'Reliance Capital Ltd.              ' | Action: OUT | ctype: datetime
   4. Sheet: 'Nifty Midcap 100                ' | Row: 397   | Date: 2017-09-05 | Scrip: 'Avenue Supermarts Ltd.             ' | Action: IN  | ctype: datetime
   5. Sheet: 'Nifty 500                       ' | Row: 2136  | Date: 2017-09-05 | Scrip: 'Reliance Capital Ltd.              ' | Action: OUT | ctype: datetime
   6. Sheet: 'Nifty 500                       ' | Row: 2162  | Date: 2017-09-05 | Scrip: 'Max Financial Services Ltd.        ' | Action: IN  | ctype: datetime
   7. Sheet: 'Nifty Midcap 50                 ' | Row: 287   | Date: 2017-09-05 | Scrip: 'Reliance Capital Ltd.              ' | Action: OUT | ctype: datetime
   8. Sheet: 'Nifty Midcap 50                 ' | Row: 289   | Date: 2017-09-05 | Scrip: 'Berger Paints India Ltd.           ' | Action: IN  | ctype: datetime
   9. Sheet: 'Nifty High Beta 50              ' | Row: 125   | Date: 2017-09-05 | Scrip: 'Reliance Capital Ltd.              ' | Action: OUT | ctype: datetime
  10. Sheet: 'Nifty High Beta 50              ' | Row: 128   | Date: 2017-09-05 | Scrip: 'Jaiprakash Associates Ltd.         ' | Action: IN  | ctype: datetime
  11. Sheet: 'Nifty Dividend Opportunities 50 ' | Row: 130   | Date: 2017-09-05 | Scrip: 'Reliance Capital Ltd.              ' | Action: OUT | ctype: datetime
  12. Sheet: 'Nifty Dividend Opportunities 50 ' | Row: 131   | Date: 2017-09-05 | Scrip: 'National Aluminium Co. Ltd.        ' | Action: IN  | ctype: datetime

Quarantined suspect rows saved to: data/quarantine_gate1.parquet
Active rows after quarantine: 9129

================================================================================
STEP 4: POST-QUARANTINE DATE MONOTONICITY CHECK
================================================================================
Day-First non-monotonic step count AFTER quarantine: 0
PASS: Exactly 0 non-monotonic steps across all 37 sheets after quarantine.

================================================================================
STEP 5: DEDUPLICATION ON (index, effective_date, scrip_name, action)
================================================================================
Exact duplicates removed: 8

All Deduplicated rows in full:
   1. Sheet: 'Nifty Infrastructure     ' | Row: 44    | Index: NIFTYINFRA      | Date: 2011-10-10 | Scrip: 'Adani Power Ltd.                   ' | Action: IN
   2. Sheet: 'Nifty Infrastructure     ' | Row: 45    | Index: NIFTYINFRA      | Date: 2011-10-10 | Scrip: 'DLF Ltd.                           ' | Action: OUT
   3. Sheet: 'Nifty Infrastructure     ' | Row: 46    | Index: NIFTYINFRA      | Date: 2011-10-10 | Scrip: 'Indian Hotels Co. Ltd.             ' | Action: OUT
   4. Sheet: 'Nifty Infrastructure     ' | Row: 47    | Index: NIFTYINFRA      | Date: 2011-10-10 | Scrip: 'NHPC Ltd.                          ' | Action: IN
   5. Sheet: 'Nifty Infrastructure     ' | Row: 48    | Index: NIFTYINFRA      | Date: 2011-10-10 | Scrip: 'Unitech Ltd.                       ' | Action: OUT
   6. Sheet: 'Nifty Infrastructure     ' | Row: 49    | Index: NIFTYINFRA      | Date: 2011-10-10 | Scrip: 'Voltas Ltd.                        ' | Action: IN
   7. Sheet: 'Nifty Realty             ' | Row: 41    | Index: NIFTYREALTY     | Date: 2019-02-26 | Scrip: 'Unitech Ltd.                       ' | Action: OUT
   8. Sheet: 'Nifty Realty             ' | Row: 42    | Index: NIFTYREALTY     | Date: 2019-02-26 | Scrip: 'Mahindra Lifespace Developers Ltd. ' | Action: IN

================================================================================
STEP 6: FREE FLOAT MERGE & PER-INDEX EVENT COUNTS
================================================================================
Free Float Variants Merge Detail:
  Nifty Free Float Midcap 100 (0) + NIFTY Midcap 100 (0) -> Merged NIFTYMIDCAP100: 592
  Nifty Free Float Smallcap 100 (0) + NIFTY Smallcap 100 (0) -> Merged NIFTYSMALLCAP100: 594

Per-Index Event Counts (Primary Seven Indices):
  NIFTY50              :   196 events
  NIFTYNEXT50          :   382 events
  NIFTY100             :   336 events
  NIFTY200             :   464 events
  NIFTY500             :  2493 events
  NIFTYMIDCAP100       :   592 events
  NIFTYSMALLCAP100     :   594 events

Final deduplicated events written to: data/index_events.parquet (9121 rows)

================================================================================
GATE 1 VERIFICATION SUMMARY:
  - All 37 sheets successfully parsed.
  - Total event rows parsed: 9141
  - Ambiguous rows checked: 1633
  - Inside-calendar trading-day hit rate: Day-First 451/451 (100.00%) vs Month-First 349/451 (77.38%)
  - Post-quarantine non-monotonic step count: 0
  - Total Quarantined suspect rows: 12
  - Total Exact Duplicates removed: 8
  - Final active events written: 9121
  - Output Parquet path: data/index_events.parquet
GATE 1 PASSED.
================================================================================
```

**Files Written**:
- [`data/index_events.parquet`](file:///sdcard/Documents/Project%20MIP/data/index_events.parquet)
- [`data/quarantine_gate1.parquet`](file:///sdcard/Documents/Project%20MIP/data/quarantine_gate1.parquet)

---

### Step 2: Gate 0 Restatement

**Command Executed**:
```bash
python3 scripts/step2_gate0_restatement.py
```

**Full Raw Output**:
```text
================================================================================
STEP 2: GATE 0 RESTATEMENT — BULLETIN & REBALANCING SCHEDULE EXTRACTION
================================================================================

--- 1. Extraction from nifty_replacement_circular_sep_2020.pdf ---
Total lines extracted from PDF stream objects: 399
Sample lines (Header & Circular metadata):
  [PDF-01] Circular
  [PDF-02] onal
  [PDF-03] Stock
  [PDF-04] Exchan
  [PDF-05] ndia
  [PDF-06] DEPARTME
  [PDF-07] T : LISTING
  [PDF-08] Download Ref. No.: NSE/CML
  [PDF-09] 45722
  [PDF-10] Date :
  [PDF-11] September 16, 2020
  [PDF-12] Circular Ref. No.:
  [PDF-13] 0810
  [PDF-14] 2020
  [PDF-15] ll Members,
  [PDF-16] Sub: Listing of
  [PDF-17] privately placed
  [PDF-18] securities on the debt market segment of the Exchange
  [PDF-19] In pursuance of Regulation 3.1.1 of the National Stock Exchange
  [PDF-20] Debt Market \(

--- 2. Extraction from niftyindices___rebalancing_schedule_200.html ---
Total lines extracted from HTML text: 1421
Sample lines (Rebalancing Schedule / Index Calendar):
  [HTML-01] Index Reconstitution Calendar
  [HTML-02] NIFTY 50 ARBITRAGE
  [HTML-03] NIFTY 50 FUTURES PR
  [HTML-04] NIFTY 50 FUTURES TR
  [HTML-05] NIFTY 50 FUTURES
  [HTML-06] NIFTY 50 Hybrid Composite Debt 70:30 Index
  [HTML-07] NIFTY 50 Hybrid Composite Debt 50:50 Index
  [HTML-08] NIFTY 50 Hybrid Composite Debt 15:85 Index
  [HTML-09] NIFTY 50 Hybrid Composite Debt 65:35 Index
  [HTML-10] NIFTY 50 Hybrid Short Duration Debt 40:60 Index
  [HTML-11] NIFTY 50 Hybrid Short Duration Debt 25:75 Index
  [HTML-12] Effective date of change
  [HTML-13] Semi-annually - Last working day of March and September
  [HTML-14] Semi-annually &ndash; Last working day of March and September
  [HTML-15] Semi-annually - Last working day of June and December
  [HTML-16] Semi-annually &ndash; Last working day of June and December
  [HTML-17] Semi-annually - 10th calendar day of June and December
  [HTML-18] Annually - Rebalancing last working day of June
  [HTML-19] Index Rebalancing Schedule

================================================================================
GATE 0 FINDING RESTATEMENT:
  The 404s encountered in Gate 0 were directory listings, not individual bulletins.
  post-2020-09 bulletin availability NOT ESTABLISHED; deferred to Phase 5.6.
  (Do not parse bulletins into events at this stage.)
================================================================================
```

---

### Step 3: Symbol Map Rebuild with Evidence

**Command Executed**:
```bash
python3 scripts/gate2_build_symbol_map.py
```

**Full Raw Output**:
```text
================================================================================
GATE 2b — SYMBOL MAP REBUILD WITH EVIDENCE HARDENING (S1–S6)
================================================================================
Loaded index events: 9121 rows
Loaded EQUITY_L: 2583 rows
Loaded trading calendar: 4649 dates (2007-09-17 to 2026-08-31)
Loaded price cache: 1831372 bars across 750 symbols
Indexing price bars by symbol...
Computing membership windows across indices...
Checking S4 concurrent alias collisions...
S4 concurrent alias collision scrips flagged: 142

Successfully wrote rebuilt symbol map to data/symbol_map.parquet (1448 rows)

--- Summary by Status ---
  proposed       :  760 (52.5%)
  unresolved     :  516 (35.6%)
  auto           :  172 (11.9%)

--- Demotions from Auto by Flag ---
  listing_after_first_seen      : 130
  duplicate_name_collision      : 0
  isin_unverified               : 0
  concurrent_alias_collision    : 61
  predecessor_marker            : 0
  first_token_mismatch          : 87
  low_coverage                  : 497
  unsourced                     : 0

--- Coverage Tiers ---
  Coverage Tier >=90  :  249 (17.2%)
  Coverage Tier 30-90 :  192 (13.3%)
  Coverage Tier <30   :  491 (33.9%)
  Coverage Tier n/a   :  516 (35.6%)

State Note on Coverage:
  Low coverage can mean a symbol change or a delisted stock absent from the cache,
  not necessarily a wrong mapping. This is why coverage is evidence, not a verdict.
```

**Files Written**:
- [`data/symbol_map_v1.parquet`](file:///sdcard/Documents/Project%20MIP/data/symbol_map_v1.parquet)
- [`data/symbol_map.parquet`](file:///sdcard/Documents/Project%20MIP/data/symbol_map.parquet)

---

### Step 4: Review Tooling Fixes & Refusal Hardening

**Commands Executed**:
```bash
python3 scripts/review_symbol_map.py
bash test_review_refusals.sh
```

**Full Raw Output (Review Generation)**:
```text
================================================================================
STEP 4 — REVIEW TOOLING: GENERATING REVIEW CSVS
================================================================================
Total symbol map rows: 1448
Current status counts:
  proposed       : 760
  unresolved     : 516
  auto           : 172

Unresolved rows count: 516
Written unresolved reference CSV to: data/symbol_map_unresolved.csv

Proposed rows requiring review: 760

[Tier: HIGH] — Count: 563
  Written to: data/symbol_map_review_high.csv
  First 5 entries:
    - Scrip: '20 Microns Ltd                     ' | Sym: '20MICRONS ' | Flags: 
    - Scrip: '3i Infotech Ltd.                   ' | Sym: '3IINFOLTD ' | Flags: listing_after_first_seen
    - Scrip: '63 Moons Technologies Ltd.         ' | Sym: '63MOONS   ' | Flags: 
    - Scrip: 'ABB India Ltd.                     ' | Sym: 'ABB       ' | Flags: concurrent_alias_collision
    - Scrip: 'ABB Ltd.                           ' | Sym: 'ABB       ' | Flags: first_token_mismatch;name_mismatch;concu

[Tier: MEDIUM] — Count: 165
  Written to: data/symbol_map_review_medium.csv
  First 5 entries:
    - Scrip: 'AP Paper Mills Ltd.                ' | Sym: 'BALKRISHNA' | Flags: first_token_mismatch;name_mismatch;listi
    - Scrip: 'Accelya Kale Solutions Ltd.        ' | Sym: 'ACCELYA   ' | Flags: first_token_mismatch;name_mismatch
    - Scrip: 'Adani Gas Ltd.                     ' | Sym: 'ATGL      ' | Flags: first_token_mismatch;name_mismatch
    - Scrip: 'Aditya Birla Nuvo Ltd.             ' | Sym: 'ABCAPITAL ' | Flags: name_mismatch;listing_after_first_seen
    - Scrip: 'Advanced Enzyme Tech Ltd.          ' | Sym: 'ADVENZYMES' | Flags: name_mismatch

[Tier: LOW] — Count: 32
  Written to: data/symbol_map_review_low.csv
  First 5 entries:
    - Scrip: 'Aster DM Healthcare Ltd.           ' | Sym: 'ASTERDM   ' | Flags: name_mismatch
    - Scrip: 'Berger Paints India Ltd.           ' | Sym: 'BERGEPAINT' | Flags: name_mismatch;listing_after_first_seen;u
    - Scrip: 'D.S. Kulkarni Developers Ltd.      ' | Sym: 'DSKULKARNI' | Flags: first_token_mismatch;name_mismatch
    - Scrip: 'Dr. Datsons Labs Ltd.              ' | Sym: 'LALPATHLAB' | Flags: first_token_mismatch;name_mismatch;listi
    - Scrip: 'East India Hotels Ltd              ' | Sym: 'EIHOTEL   ' | Flags: first_token_mismatch;name_mismatch;concu

================================================================================
REVIEW CSV FILES GENERATED:
  - data/symbol_map_unresolved.csv (reference only, cannot be approved)
  - data/symbol_map_review_high.csv
  - data/symbol_map_review_medium.csv
  - data/symbol_map_review_low.csv
Note: The 'status' column is read-only. Reviewers must edit 'review_action' and provide 'approval_note' if flagged.
================================================================================
```

**Full Raw Output (Refusal Verification Suite)**:
```text
================================================================================
TESTING REVIEW APPLICATION REFUSAL PATHS
================================================================================

--- Test 1: Invalid review_action ('maybe') ---
================================================================================
APPLY SYMBOL MAP REVIEW TOOL (HARDENED)
================================================================================
Reading review file: data/test_invalid_action.csv
REFUSAL: Row 2 has unrecognized review_action='maybe'. Must be one of ['approved', 'proposed', 'rejected']!

--- Test 2: 'auto' in review_action ---
================================================================================
APPLY SYMBOL MAP REVIEW TOOL (HARDENED)
================================================================================
Reading review file: data/test_auto_action.csv
REFUSAL: Row 2 specifies review_action='auto'. Cannot manually assign 'auto' status via review!

--- Test 3: Approve with empty symbol/ISIN ---
================================================================================
APPLY SYMBOL MAP REVIEW TOOL (HARDENED)
================================================================================
Reading review file: data/test_empty_sym.csv
REFUSAL: Cannot approve row 2 ('20th Century Finance Corporation Ltd.') with empty symbol or ISIN!

--- Test 4: Approve flagged row without approval_note ---
================================================================================
APPLY SYMBOL MAP REVIEW TOOL (HARDENED)
================================================================================
Reading review file: data/test_flagged_nonote.csv
REFUSAL: Cannot approve flagged row 2 ('3i Infotech Ltd.') without an approval_note!
  Active flags: listing_after_first_seen

--- Test 5: Mismatched key (symbol altered) ---
================================================================================
APPLY SYMBOL MAP REVIEW TOOL (HARDENED)
================================================================================
Reading review file: data/test_mismatched_key.csv
REFUSAL: Key mismatch on row 2 for '20 Microns Ltd'!
  CSV key: (symbol='WRONG_SYM', isin='INE144J01027')
  Map key: (symbol='20MICRONS', isin='INE144J01027')

--- Test 6: No-op file (zero changes) ---
================================================================================
APPLY SYMBOL MAP REVIEW TOOL (HARDENED)
================================================================================
Reading review file: data/test_noop.csv

Notice: Review CSV produced ZERO status or mapping changes.
Exiting without rewriting symbol map parquet file.
```

**Files Written**:
- [`data/symbol_map_unresolved.csv`](file:///sdcard/Documents/Project%20MIP/data/symbol_map_unresolved.csv)
- [`data/symbol_map_review_high.csv`](file:///sdcard/Documents/Project%20MIP/data/symbol_map_review_high.csv)
- [`data/symbol_map_review_medium.csv`](file:///sdcard/Documents/Project%20MIP/data/symbol_map_review_medium.csv)
- [`data/symbol_map_review_low.csv`](file:///sdcard/Documents/Project%20MIP/data/symbol_map_review_low.csv)

---

### Step 5: Canary Regression Test

**Command Executed**:
```bash
python3 test_canary_eval.py
```

**Full Raw Output**:
```text
Scrip Name                                 | Status     | Symbol       | Expected Reason                          | Flags                                         | Pass?
---------------------------------------------------------------------------------------------------------------------------------------------------------------------
Ranbaxy Laboratories Ltd.                  | proposed   | SUNPHARMA    | successor ISIN, no price bars before merger | first_token_mismatch;name_mismatch;concurrent_alias_collision;unsourced | PASS
Satyam Computer Services Ltd.              | proposed   | TECHM        | successor ISIN                           | first_token_mismatch;name_mismatch;listing_after_first_seen;concurrent_alias_collision;unsourced | PASS
State Bank of Mysore                       | proposed   | SBIN         | concurrent alias collision               | name_mismatch;concurrent_alias_collision      | PASS
State Bank of Travancore                   | proposed   | SBIN         | concurrent alias collision               | name_mismatch;concurrent_alias_collision      | PASS
Larsen & Toubro Infotech Ltd.              | proposed   | LT           | first-token/name mismatch                | name_mismatch;concurrent_alias_collision      | PASS
Procter & Gamble India Ltd.                | proposed   | PGHL         | name mismatch (eq_name is Procter & Gamble Health) | name_mismatch                                 | PASS
Welspun India Ltd.                         | proposed   | WELCORP      | name mismatch                            | first_token_mismatch;name_mismatch;listing_after_first_seen;concurrent_alias_collision | PASS
Jain Irrigation Systems Ltd. (Old)         | proposed   | JISLDVREQS   | predecessor marker, DVR series           | name_mismatch;listing_after_first_seen;predecessor_marker | PASS
Triveni Engineering & Industries Ltd. (Old) | proposed   | TRIVENI      | predecessor marker                       | name_mismatch;listing_after_first_seen;predecessor_marker | PASS
Tube Investments of India Ltd.-Old         | proposed   | TIINDIA      | predecessor marker                       | name_mismatch;listing_after_first_seen;predecessor_marker | PASS
Indian Hotels Co. Ltd.                     | proposed   | INDHOTEL     | isin_unverified (EQUITY_L has INE053A01029) | name_mismatch;isin_unverified;unsourced       | PASS
Tata Motors Ltd.                           | proposed   | TMCV         | S1 listing date 2025-11-12, no earlier bars | listing_after_first_seen;concurrent_alias_collision | PASS
ITC Hotels Ltd.                            | proposed   | ITCHOTELS    | S1 listing date 2025-01-29               | listing_after_first_seen                      | PASS
Hexaware Technologies Ltd.                 | proposed   | HEXT         | S1 listing date 2025-02-19               | listing_after_first_seen                      | PASS
Max India Ltd.                             | proposed   | MAXIND       | S1 listing 2020                          | listing_after_first_seen                      | PASS
Future Enterprises Ltd.                    | proposed   | FEL          | S2 duplicate-name collision              | duplicate_name_collision(FEL,FELDVR)          | PASS
Corporation Bank                           | proposed   | AXISBANK     | first-token mismatch                     | first_token_mismatch;name_mismatch;concurrent_alias_collision | PASS
Bajaj Corp Ltd.                            | proposed   | BAJAJ-AUTO   | first-token mismatch                     | first_token_mismatch;name_mismatch;concurrent_alias_collision | PASS
I T C Ltd.                                 | proposed   | ISTLTD       | first-token mismatch                     | first_token_mismatch;name_mismatch;listing_after_first_seen | PASS
Jindal Steel & Power Ltd.                  | proposed   | MSPL         | first-token mismatch                     | first_token_mismatch;name_mismatch;listing_after_first_seen | PASS
Essar Oil Ltd.                             | proposed   | OIL          | first-token mismatch                     | first_token_mismatch;name_mismatch;listing_after_first_seen;concurrent_alias_collision | PASS
Gas Authority of India Limited             | proposed   | SAIL         | first-token mismatch                     | first_token_mismatch;name_mismatch;concurrent_alias_collision | PASS

All canaries passed: True
Written canary results to data/verification/canaries_2b.csv (22 cases)
```

**Files Written**:
- [`data/verification/canaries_2b.csv`](file:///sdcard/Documents/Project%20MIP/data/verification/canaries_2b.csv)

---

### Step 6: Gate 2 Report Recomputation (NIFTY500 Only)

**Command Executed**:
```bash
python3 scripts/gate2_report_recompute.py
```

**Full Raw Output**:
```text
================================================================================
GATE 2 REPORT RECOMPUTATION (NIFTY500 ONLY) — BEFORE VS AFTER REBUILD
================================================================================

--- 1. OVERALL STATUS COUNTS (BEFORE VS AFTER) ---
Status          | Before (v1)     | After (v2b)    
--------------------------------------------------
auto            | 709             | 172            
proposed        | 739             | 760            
unresolved      | 0               | 516            

--- 2. FLAG COUNTS IN REBUILT MAP (v2b) ---
  no_candidate                       : 516
  listing_after_first_seen           : 257
  first_token_mismatch               : 234
  name_mismatch                      : 223
  concurrent_alias_collision         : 142
  predecessor_marker                 : 23
  unsourced                          : 13
  isin_unverified                    : 3
  duplicate_name_collision           : 2

--- 3. PER-INDEX SUMMARY ---

==================== INDEX: NIFTY500 ====================
Total Unique Scrips: 1280 | Total Events: 2493

  >>> BEFORE REBUILD (v1) <<<
  Blocked Events: IN = 687, OUT = 571
  Reconstructed Snapshot Fractions:
    Snapshot 2010-01-01:
      - Name-Level Resolved Fraction : 318 / 500 (63.6%)
      - Price-Covered Fraction (>=90%):   0 / 500 (0.0%)
      - Survivorship note: 500 of 500 NIFTY500 members at 2010-01-01 are unresolved or lack price data.
    Snapshot 2014-01-01:
      - Name-Level Resolved Fraction : 322 / 500 (64.4%)
      - Price-Covered Fraction (>=90%):   0 / 500 (0.0%)
      - Survivorship note: 500 of 500 NIFTY500 members at 2014-01-01 are unresolved or lack price data.
    Snapshot 2018-01-01:
      - Name-Level Resolved Fraction : 362 / 507 (71.4%)
      - Price-Covered Fraction (>=90%):   0 / 507 (0.0%)
      - Survivorship note: 507 of 507 NIFTY500 members at 2018-01-01 are unresolved or lack price data.
    Snapshot 2020-09-14:
      - Name-Level Resolved Fraction : 391 / 515 (75.9%)
      - Price-Covered Fraction (>=90%):   0 / 515 (0.0%)
      - Survivorship note: 515 of 515 NIFTY500 members at 2020-09-14 are unresolved or lack price data.

  Monthly Rebalance Snapshots (Total = 266):
    Name-Level Resolved : Min = 44.0%, Median = 62.8%, <80% = 266
    Price-Covered (>=90%): Min = 0.0%, Median = 0.0%, <80% = 266

  >>> AFTER REBUILD (v2b) <<<
  Blocked Events: IN = 1307, OUT = 943
  Reconstructed Snapshot Fractions:
    Snapshot 2010-01-01:
      - Name-Level Resolved Fraction :  38 / 500 (7.6%)
      - Price-Covered Fraction (>=90%):  38 / 500 (7.6%)
      - Survivorship note: 462 of 500 NIFTY500 members at 2010-01-01 are unresolved or lack price data.
    Snapshot 2014-01-01:
      - Name-Level Resolved Fraction :  46 / 500 (9.2%)
      - Price-Covered Fraction (>=90%):  46 / 500 (9.2%)
      - Survivorship note: 454 of 500 NIFTY500 members at 2014-01-01 are unresolved or lack price data.
    Snapshot 2018-01-01:
      - Name-Level Resolved Fraction :  99 / 507 (19.5%)
      - Price-Covered Fraction (>=90%):  99 / 507 (19.5%)
      - Survivorship note: 408 of 507 NIFTY500 members at 2018-01-01 are unresolved or lack price data.
    Snapshot 2020-09-14:
      - Name-Level Resolved Fraction : 138 / 515 (26.8%)
      - Price-Covered Fraction (>=90%): 138 / 515 (26.8%)
      - Survivorship note: 377 of 515 NIFTY500 members at 2020-09-14 are unresolved or lack price data.

  Monthly Rebalance Snapshots (Total = 266):
    Name-Level Resolved : Min = 5.2%, Median = 7.6%, <80% = 266
    Price-Covered (>=90%): Min = 5.2%, Median = 7.6%, <80% = 266

==================== INDEX: NIFTY50 ====================
Total Unique Scrips: 133 | Total Events: 196
  Status: event log only, not reconstructable (lacks 1998-08-01 seed batch)

==================== INDEX: NIFTYNEXT50 ====================
Total Unique Scrips: 232 | Total Events: 382
  Status: event log only, not reconstructable (lacks 1998-08-01 seed batch)

==================== INDEX: NIFTY100 ====================
Total Unique Scrips: 207 | Total Events: 336
  Status: event log only, not reconstructable (lacks 1998-08-01 seed batch)

==================== INDEX: NIFTY200 ====================
Total Unique Scrips: 264 | Total Events: 464
  Status: event log only, not reconstructable (lacks 1998-08-01 seed batch)

==================== INDEX: NIFTYMIDCAP100 ====================
Total Unique Scrips: 317 | Total Events: 592
  Status: event log only, not reconstructable (lacks 1998-08-01 seed batch)

==================== INDEX: NIFTYSMALLCAP100 ====================
Total Unique Scrips: 327 | Total Events: 594
  Status: event log only, not reconstructable (lacks 1998-08-01 seed batch)
```

---

## 20 Random Sample Rows per Status (RNG Seed = 42)

#### Status: `auto` (20 random samples, seed=42)
| scrip_name | symbol | isin | res_method | conf | cov% | bars_pres/exp | flags |
|---|---|---|---|---|---|---|---|
| DCM Shriram Ltd. | DCMSHRIRAM | INE499A01024 | equity_l_exact | high | 100.0% | 303/303 | - |
| Quess Corp Ltd. | QUESS | INE615P01015 | equity_l_exact | high | 100.0% | 849/849 | - |
| Solar Industries India Ltd. | SOLARINDS | INE343H01029 | equity_l_exact | high | 100.0% | 1341/1341 | - |
| Central Depository Services (India) Ltd. | CDSL | INE736A01011 | equity_l_exact | high | 100.0% | 603/603 | - |
| Syngene International Ltd. | SYNGENE | INE398R01022 | equity_l_exact | high | 100.0% | 1094/1094 | - |
| Ujjivan Small Finance Bank Ltd. | UJJIVANSFB | INE551W01018 | equity_l_exact | high | 100.0% | 57/57 | - |
| Eris Lifesciences Ltd. | ERIS | INE406M01024 | equity_l_exact | high | 100.0% | 615/615 | - |
| Ramkrishna Forgings Ltd. | RKFORGE | INE399G01023 | equity_l_exact | high | 100.0% | 857/857 | - |
| KNR Constructions Ltd. | KNRCON | INE634I01029 | equity_l_exact | high | 100.0% | 617/617 | - |
| Bajaj Auto Ltd | BAJAJ-AUTO | INE917I01010 | equity_l_exact | high | 100.0% | 1/1 | listing_after_first_seen |
| Minda Corporation Ltd. | MINDACORP | INE842C01021 | equity_l_exact | high | 100.0% | 123/123 | - |
| JK Paper Ltd. | JKPAPER | INE789E01012 | equity_l_exact | high | 100.0% | 358/358 | - |
| Bharat Dynamics Ltd. | BDL | INE171Z01026 | equity_l_exact | high | 100.0% | 512/512 | - |
| Granules India Ltd. | GRANULES | INE101D01020 | equity_l_exact | high | 100.0% | 1094/1094 | - |
| SBI Life Insurance Company Ltd. | SBILIFE | INE123W01016 | equity_l_exact | high | 100.0% | 603/603 | - |
| Alembic Pharmaceuticals Ltd. | APLLTD | INE901L01018 | equity_l_exact | high | 100.0% | 1631/1631 | - |
| Poly Medicure Ltd. | POLYMED | INE205C01021 | equity_l_exact | high | 100.0% | 57/57 | - |
| Arvind Fashions Ltd. | ARVINDFASN | INE955V01021 | equity_l_exact | high | 100.0% | 238/238 | - |
| DCB Bank Ltd. | DCBBANK | INE503A01015 | equity_l_exact | high | 100.0% | 1407/1407 | - |
| SBI Cards and Payment Services Ltd. | SBICARD | INE018E01016 | equity_l_exact | high | 100.0% | 32/32 | - |

#### Status: `proposed` (20 random samples, seed=42)
| scrip_name | symbol | isin | res_method | conf | cov% | bars_pres/exp | flags |
|---|---|---|---|---|---|---|---|
| Lloyds Metals & Engineers Ltd. | LLOYDSME | INE281B01032 | token_match | medium | 0.0% | 0/0 | name_mismatch;listing_after_first_seen |
| JK Tyre & Industries Ltd.. | JKTYRE | INE573A01042 | equity_l_exact | high | 0.0% | 0/0 | listing_after_first_seen |
| CRISIL Ltd. | CRISIL | INE007A01025 | equity_l_exact | high | 100.0% | 3177/3177 | first_token_mismatch |
| Orient Paper & Industries Ltd. | ORIENTPPR | INE592A01026 | equity_l_exact | high | 0.0% | 0/1339 | - |
| Colgate Palmolive (I) Ltd | COLPAL | INE259A01022 | token_match | medium | 0.0% | 0/0 | name_mismatch;listing_after_first_seen |
| Oriental Hotels Ltd. | ORIENTHOT | INE750A01020 | equity_l_exact | high | 0.0% | 0/1354 | - |
| Ind-Swift Laboratories Ltd. | INDSWFTLAB | INE915B01019 | equity_l_exact | high | 0.0% | 0/1354 | - |
| Sonata Software Ltd. | SONATSOFTW | INE269A01021 | equity_l_exact | high | 44.0% | 1398/3177 | - |
| Transport Corporation of India Ltd. | TCI | INE688A01022 | equity_l_exact | high | 0.0% | 0/18 | - |
| Sadbhav Engineering Ltd. | SADBHAV | INE226H01026 | equity_l_exact | high | 0.0% | 0/369 | concurrent_alias_collision |
| Bharat Bijlee Ltd. | BBL | INE464A01036 | equity_l_exact | high | 0.0% | 0/0 | listing_after_first_seen |
| Sun Pharmaceutical Industries Ltd. | SUNPHARMA | INE044A01036 | equity_l_exact | high | 44.0% | 1398/3177 | concurrent_alias_collision |
| Nilkamal Ltd. | NILKAMAL | INE310A01015 | equity_l_exact | high | 0.0% | 0/1354 | first_token_mismatch |
| Windsor Machines Ltd. | WINDMACHIN | INE052A01021 | equity_l_exact | high | 0.0% | 0/0 | listing_after_first_seen |
| Torrent Pharmaceuticals Ltd. | TORNTPHARM | INE685A01028 | equity_l_exact | high | 44.0% | 1398/3177 | listing_after_first_seen |
| Redington (India) Ltd. | REDINGTON | INE891D01026 | token_match | high | 52.42% | 1398/2667 | first_token_mismatch;name_mismatch |
| Taj GVK Hotels & Resorts Ltd. | TAJGVK | INE586B01026 | equity_l_exact | high | 0.0% | 0/1233 | - |
| Puravankara Projects Ltd. | PURVA | INE323I01011 | token_match | medium | 23.28% | 427/1834 | first_token_mismatch;name_mismatch |
| Ashok Leyland Ltd. | ASHOKLEY | INE208A01029 | equity_l_exact | high | 100.0% | 3177/3177 | concurrent_alias_collision |
| HDFC Bank Ltd. | HDFCBANK | INE040A01034 | equity_l_exact | high | 44.0% | 1398/3177 | - |

#### Status: `unresolved` (20 random samples, seed=42)
| scrip_name | symbol | isin | res_method | conf | cov% | bars_pres/exp | flags |
|---|---|---|---|---|---|---|---|
| NEPC Agro Foods Ltd. | - | - | unresolved | low | 0.0% | 0/0 | no_candidate |
| Wellwin Industry Ltd. | - | - | unresolved | low | 0.0% | 0/0 | no_candidate |
| Sterlite Industries (India) Ltd | - | - | unresolved | low | 0.0% | 0/0 | no_candidate |
| Global Trust Bank Ltd | - | - | unresolved | low | 0.0% | 0/0 | no_candidate |
| Westlife Development Ltd. | - | - | unresolved | low | 0.0% | 0/0 | no_candidate |
| Flat Products Equipments (India) Ltd. | - | - | unresolved | low | 0.0% | 0/0 | no_candidate |
| ITW Signode India Ltd.- Sus | - | - | unresolved | low | 0.0% | 0/0 | no_candidate |
| Zee Telefilms Ltd | - | - | unresolved | low | 0.0% | 0/0 | no_candidate |
| PHIL Corporation Ltd. | - | - | unresolved | low | 0.0% | 0/0 | no_candidate |
| Jyothy Laboratories Ltd. | - | - | unresolved | low | 0.0% | 0/0 | no_candidate |
| Winsome Diamonds and Jewellery Ltd. | - | - | unresolved | low | 0.0% | 0/0 | no_candidate |
| Polaris Software Lab Ltd. | - | - | unresolved | low | 0.0% | 0/0 | no_candidate |
| Merck Ltd. | - | - | unresolved | low | 0.0% | 0/0 | no_candidate |
| Centurion Bank Ltd. | - | - | unresolved | low | 0.0% | 0/0 | no_candidate |
| Adani Transmission Ltd. | - | - | unresolved | low | 0.0% | 0/0 | no_candidate |
| Orkay Industries Ltd. | - | - | unresolved | low | 0.0% | 0/0 | no_candidate |
| Caprihans India Ltd. | - | - | unresolved | low | 0.0% | 0/0 | no_candidate |
| Amtek India Ltd. | - | - | unresolved | low | 0.0% | 0/0 | no_candidate |
| Hitech Drilling Services India Ltd. | - | - | unresolved | low | 0.0% | 0/0 | no_candidate |
| ICICI Securities Ltd. | - | - | unresolved | low | 0.0% | 0/0 | no_candidate |

---

## HALT-1b Declaration

Gate 2b implementation, evidence hardening, tool refusal testing, canary regressions, and NIFTY500 report recomputations are completed. In accordance with instruction:
**HALT-1b is reached. Halting and awaiting user review.**
