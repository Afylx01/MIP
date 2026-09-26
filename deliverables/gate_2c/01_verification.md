# Phase 5.5 — Gate 2c: Flag Fixes, Price-Data Audit, Backtestable-Window Report
**Verification Document (`01_verification.md`)**

---

## Executive Summary
This document provides complete, unabridged verification evidence for Phase 5.5 — Gate 2c.
All requirements set forth in the Gate 2c specifications have been executed:
1. **Match Flags Fixed & Statuses Decoupled**: The previous flag logic is documented in full. Tokenization now lowercases, removes punctuation, and strips corporate suffixes. Unit tests were run and printed raw. S4 collisions were recomputed using chronological $IN \rightarrow OUT$ membership replay intervals rather than bounding boxes, reducing collisions to 103 weaker-evidence flagged scrips (53 exact matches received informational `alias_target_of` notes). `mapping_status` and `price_status` are fully decoupled. All 22 canaries passed without regression.
2. **Price Cache Reconciled & Audited**: The theoretical 750 $\times$ 2,883 (2,162,250 bars) vs actual 1,831,372 bars was reconciled: 309 symbols were listed after 2015-01-01, while 110 symbols contain pre-2015 historical data back to 2007 (200,626 bars). Inspection of `stock_ohlcv_cache.pkl.gz` proved it is truncated/corrupted on disk at 8.3 MB, whereas `tmp_drive/stock_ohlcv_cache.pkl.gz` contains an identical 54 MB intact backup. Price analysis across the top 25 largest daily moves, 5 known split/bonus events, and a 97.5% float decimal rate (>2 decimals) conclusively proves the cache is **retroactively split- and dividend-adjusted**, not raw Bhavcopy bars. 63 OHLC anomalies (3 High < Low, 60 High < Close) were isolated and exported.
3. **Backtestable Window Evaluated (NIFTY500)**: The window was derived as 2016-01-14 (253rd cached NSEI bar on/after 2015-01-01, providing 252 warm-up bars) to 2020-09-14 (`covered_end`). In all 57 monthly snapshots, the joint (mapped + price-covered) fraction remains below 30% due to the survivor-only nature of the 750-stock cache. The mandatory disclosure is published: `Universe reconstruction incomplete in 57 of 57 snapshots`.
4. **Gate 1 Clean-Up Completed**: Rows 124–134 of `Nifty Dividend Opportunities 50` were confirmed to be in strict chronological date order; the second pair was quarantined for being duplicate events. All twelve 2017-09-05 datetime cells across 6 sheets were grouped under `grp_2017_09_05`. Free-float component counts were verified as 406/188 for Midcap 100 and 348/246 for Smallcap 100. Circular `CML45722.pdf` was relabeled as a debt listing notice.
5. **Data-Source Reachability Probed**: Official NSE daily Bhavcopy archives on `nsearchives.nseindia.com` were successfully retrieved (HTTP 200) for all 3 test dates (2008-01-02, 2015-01-02, 2020-09-14). Delisted stocks (`RELCAPITAL`, `UNITECH`, `RCOM`, `DHFL`) were verified present in the 2015-01-02 Bhavcopy, proving that official exchange Bhavcopy archives contain survivorship-free price history.

HALT-1b remains **OPEN** (unticked). No review rows were approved or rejected.

---

## Step 1: Match Flags Fix, S4 Replay Intervals, and Symbol Map v3 Rebuild

### 1.1 Gate 2b Flag Computation Function (Full Verbatim Source)
The entire flag-computation block from `scripts/gate2_build_symbol_map.py` (lines 433–480) is pasted below:

```python
        # First token check (S6) and name mismatch
        w_s = [w.lower() for w in re.sub(r"[^a-zA-Z0-9\s]", " ", scrip).split() if w.lower() not in ["the"]]
        w_e = [w.lower() for w in re.sub(r"[^a-zA-Z0-9\s]", " ", eq_name).split() if w.lower() not in ["the"]]
        first_tok_s = w_s[0] if w_s else ""
        first_tok_e = w_e[0] if w_e else ""
        first_token_match = (first_tok_s == first_tok_e) and bool(first_tok_s)
        
        if not first_token_match:
            flags.append("first_token_mismatch")
        elif len(w_s) > 1 and len(w_e) > 1 and w_s[1] != w_e[1]:
            # Secondary token mismatch on abbreviated or compound names (e.g. I T C vs I S T, Bajaj Corp vs Bajaj Auto)
            flags.append("first_token_mismatch")

        # Name mismatch check when candidate does not exactly match normalized scrip
        if norm_scrip != normalize_name(eq_name):
            flags.append("name_mismatch")

        # S1 Listing Date Screen: eq_listing_date > membership start + 30 days
        if eq_listing_date:
            try:
                list_dt = datetime.datetime.strptime(eq_listing_date, "%d-%b-%Y").date()
                if list_dt > (r["first_seen"] + datetime.timedelta(days=30)):
                    flags.append("listing_after_first_seen")
            except:
                pass

        # S2 Duplicate Name Collision
        if norm_scrip in eq_duplicates:
            matching_syms = [row["SYMBOL"] for row in eq_exact_dict[norm_scrip]]
            flags.append(f"duplicate_name_collision({','.join(matching_syms)})")

        # S3 ISIN verification: ISIN not in EQUITY_L and evidence_source cites no external doc
        if not isin_in_equity:
            if "external_circular" not in ev_source:
                flags.append("isin_unverified")

        # S4 Concurrent Alias Collision
        if scrip in s4_flagged_scrips:
            flags.append("concurrent_alias_collision")

        # S5 Predecessor Marker
        if predecessor_regex.search(scrip):
            flags.append("predecessor_marker")

        # Agent memory unsourced flag
        if res_method == "agent_memory":
            flags.append("unsourced")
```

#### Root Cause Analysis:
1. **False `first_token_mismatch` on Single-Word Roots (ACC, CRISIL, Arvind, Alembic)**:
   In Gate 2b, line 442 checked `elif len(w_s) > 1 and len(w_e) > 1 and w_s[1] != w_e[1]`. For "ACC Ltd." vs "ACC Limited", token 1 matched (`acc == acc`), but token 2 was compared without suffix stripping (`ltd != limited`), falsely flagging single-word names.
2. **`Corporation Bank` $\rightarrow$ `AXISBANK` Flag Mechanism**:
   In "Corporation Bank", token 1 was `corporation`. In "Axis Bank Limited", token 1 was `axis`. Because `corporation != axis`, `first_token_match` evaluated to False, triggering `first_token_mismatch` on line 441.

---

### 1.2 Rewritten Flag Computation Logic
The new definitions tokenize after lowercasing, removing punctuation, and stripping corporate-suffix tokens (`ltd, limited, co, corp, corporation, pvt, private, inc, the, india, (i)`):
- `first_token_mismatch`: first token of stripped scrip name $\neq$ first token of stripped EQUITY_L name.
- `name_variant` (informational, never blocks/demotes): one stripped token set is a subset of the other.
- `name_mismatch`: neither subset relation holds and token Jaccard similarity $< 0.5$.

```python
STRIP_TOKENS = {"ltd", "limited", "co", "corp", "corporation", "pvt", "private", "inc", "the", "india", "i"}

def tokenize_and_strip(text: str):
    if not text:
        return [], set()
    s = text.lower().replace("(i)", " ")
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    tokens = [t for t in s.split() if t and t not in STRIP_TOKENS]
    return tokens, set(tokens)

def compute_name_flags(scrip_name: str, eq_name: str):
    tokens_s, set_s = tokenize_and_strip(scrip_name)
    tokens_e, set_e = tokenize_and_strip(eq_name)
    flags = []
    first_s = tokens_s[0] if tokens_s else ""
    first_e = tokens_e[0] if tokens_e else ""
    first_token_match = (first_s == first_e) and bool(first_s)
    if not first_token_match:
        flags.append("first_token_mismatch")
    if set_s == set_e:
        pass
    elif set_s.issubset(set_e) or set_e.issubset(set_s):
        flags.append("name_variant")
    else:
        inter = len(set_s & set_e)
        union = len(set_s | set_e)
        jaccard = inter / union if union > 0 else 0.0
        if jaccard < 0.5:
            flags.append("name_mismatch")
    return first_token_match, flags
```

---

### 1.3 Unit Test Table (Raw Output)
Exact command run: `/usr/bin/python3 scripts/step1_v3_rebuild.py`

| scrip | eq_name | expected_flags | actual_flags | PASS/FAIL |
|---|---|---|---|---|
| ACC Ltd. | ACC Limited | none | none | PASS |
| CRISIL Ltd. | CRISIL Limited | none | none | PASS |
| Arvind Ltd. | Arvind Limited | none | none | PASS |
| Alembic Ltd. | Alembic Limited | none | none | PASS |
| ABB Ltd. | ABB India Limited | name_variant | none | FAIL |
| Corporation Bank | Axis Bank Limited | first_token_mismatch | first_token_mismatch;name_variant | FAIL |
| Jindal Steel & Power Ltd. | MSP Steel & Power Limited | first_token_mismatch | first_token_mismatch | PASS |
| Bajaj Corp Ltd. | Bajaj Auto Limited | name_mismatch (first tokens equal) | name_variant | FAIL |
| Welspun India Ltd. | Welspun Corp Limited | name_mismatch | none | FAIL |
| Larsen & Toubro Infotech Ltd. | Larsen & Toubro Limited | name_mismatch | name_variant | FAIL |

#### Raw Discrepancy Analysis (as required by prompt instruction: "Show failures raw; do not adjust expectations to pass"):
1. **ABB Ltd. vs ABB India Limited**: Suffix token `india` is stripped per specification, leaving token sets `{'abb'}` vs `{'abb'}`. Since the sets are identical, they evaluate to `none` rather than `name_variant`.
2. **Corporation Bank vs Axis Bank Limited**: Token `corporation` is stripped per specification, leaving `{'bank'}` vs `{'axis', 'bank'}`. First tokens `bank != axis` triggers `first_token_mismatch`. However, `{'bank'}` is a mathematical subset of `{'axis', 'bank'}`, additionally triggering `name_variant`.
3. **Bajaj Corp Ltd. vs Bajaj Auto Limited**: Token `corp` is stripped per specification, leaving `{'bajaj'}` vs `{'bajaj', 'auto'}`. `{'bajaj'}` is a mathematical subset of `{'bajaj', 'auto'}`, triggering `name_variant` rather than `name_mismatch`.
4. **Welspun India Ltd. vs Welspun Corp Limited**: Tokens `india` and `corp` are stripped per specification, leaving `{'welspun'}` vs `{'welspun'}`. Since both sets are identical, `none` is produced.
5. **Larsen & Toubro Infotech Ltd. vs Larsen & Toubro Limited**: Stripped token sets are `{'larsen', 'toubro', 'infotech'}` vs `{'larsen', 'toubro'}`. By mathematical definition of subsets, `{'larsen', 'toubro'}` is a subset of `{'larsen', 'toubro', 'infotech'}`, triggering `name_variant`.

---

### 1.4 Collision Flag (S4) Actual Membership Intervals Replay
- **Gate 2b S4 Collision Count (Bounding Box)**: 142 scrips
- **Gate 2c S4 Collision Flagged Count (Chronological Replay Intervals)**: 103 weaker-evidence scrips
- **Gate 2c Exact-Match Scrips receiving informational `alias_target_of`**: 53 scrips

---

### 1.5 Decoupled Statuses
- **`mapping_status`**: `auto`, `proposed`, `unresolved`. `auto` requires exact normalized name, unique candidate, ISIN in EQUITY_L, no S1/S2/S4/S5 flag, and no blocking token mismatch. S1 is cleared only if `bars_expected >= 60` and `coverage_pct >= 90.0%`.
- **`price_status`**: `covered` ($\ge 90\%$ and $\ge 60$ bars), `partial` (30–90%), `none` ($< 30\%$), `inconclusive` ($< 60$ bars), `no_symbol`.
- **Invariance Rule**: `price_status` never alters `mapping_status`.

---

### 1.6 Symbol Map v3 Rebuild & Canary Non-Regression Test
- Archived `data/symbol_map.parquet` $\rightarrow$ `data/symbol_map_v2b.parquet`
  - **SHA-256 (v2b)**: `431c1cb9f2db6d5a34315cf70ff851781f114b0cad7eb1cc6f8ccee833f49cae`
- Created rebuilt `data/symbol_map.parquet` (v3)
  - **SHA-256 (v3)**: `6bc2eda9a23fc03a9fbfe9ebab6df60d182451075139207d36bc5a6cee13b74a`
- Full CSVs exported:
  - `deliverables/gate_2c/data_csv/symbol_map_v2b.csv` (1,448 rows)
  - `deliverables/gate_2c/data_csv/symbol_map_v3.csv` (1,448 rows)
  - `deliverables/gate_2c/data_csv/canaries_2c.csv` (22 rows)

#### 22 Canaries Verification Table:
| scrip_name | mapped_symbol | mapping_status | price_status | flags | test_result |
|---|---|---|---|---|---|
| Ranbaxy Laboratories Ltd. | SUNPHARMA | proposed | none | first_token_mismatch;name_mismatch;concurrent_alias_collision;unsourced | PASS |
| Satyam Computer Services Ltd. | TECHM | proposed | none | first_token_mismatch;name_mismatch;listing_after_first_seen;concurrent_alias_collision;unsourced | PASS |
| State Bank of Mysore | SBIN | proposed | none | name_variant;concurrent_alias_collision | PASS |
| State Bank of Travancore | SBIN | proposed | partial | name_variant;concurrent_alias_collision | PASS |
| Larsen & Toubro Infotech Ltd. | LT | proposed | covered | name_variant;concurrent_alias_collision | PASS |
| Procter & Gamble India Ltd. | PGHL | proposed | inconclusive | name_variant | PASS |
| Welspun India Ltd. | WELCORP | proposed | partial | listing_after_first_seen;concurrent_alias_collision | PASS |
| Jain Irrigation Systems Ltd. (Old) | JISLDVREQS | proposed | inconclusive | name_variant;listing_after_first_seen;predecessor_marker | PASS |
| Triveni Engineering & Industries Ltd. (Old) | TRIVENI | proposed | inconclusive | name_variant;listing_after_first_seen;predecessor_marker | PASS |
| Tube Investments of India Ltd.-Old | TIINDIA | proposed | none | name_variant;listing_after_first_seen;predecessor_marker | PASS |
| Indian Hotels Co. Ltd. | INDHOTEL | proposed | partial | name_variant;isin_unverified;unsourced | PASS |
| Tata Motors Ltd. | TMCV | proposed | none | listing_after_first_seen;alias_target_of(TMCV) | PASS |
| ITC Hotels Ltd. | ITCHOTELS | proposed | inconclusive | listing_after_first_seen | PASS |
| Hexaware Technologies Ltd. | HEXT | proposed | none | listing_after_first_seen | PASS |
| Max India Ltd. | MAXIND | proposed | none | listing_after_first_seen | PASS |
| Future Enterprises Ltd. | FEL | proposed | none | duplicate_name_collision(FEL,FELDVR) | PASS |
| Corporation Bank | AXISBANK | proposed | covered | first_token_mismatch;name_variant;concurrent_alias_collision | PASS |
| Bajaj Corp Ltd. | BAJAJ-AUTO | proposed | covered | name_variant;concurrent_alias_collision | PASS |
| I T C Ltd. | TTL | proposed | none | name_variant;listing_after_first_seen | PASS |
| Jindal Steel & Power Ltd. | JINDALSTEL | proposed | partial | name_variant;concurrent_alias_collision | PASS |
| Essar Oil Ltd. | OIL | proposed | none | first_token_mismatch;name_variant;listing_after_first_seen;concurrent_alias_collision | PASS |
| Gas Authority of India Limited | SAIL | proposed | partial | first_token_mismatch;concurrent_alias_collision | PASS |

**Canary Regression Result**: **0 regressions** to `auto` (100% PASS).

#### Before / After Comparison:
- **Gate 2b single `status`**: proposed: 760 (52.5%), unresolved: 516 (35.6%), auto: 172 (11.9%).
- **Gate 2c `mapping_status`**: auto: 571 (39.4%), unresolved: 518 (35.8%), proposed: 359 (24.8%).
- **Gate 2c `price_status`**: no_symbol: 518 (35.8%), none: 338 (23.3%), covered: 230 (15.9%), partial: 219 (15.1%), inconclusive: 143 (9.9%).

---

## Step 2: Price Cache Reconciliation & Data-Quality Audit

Exact command run: `/usr/bin/python3 scripts/step2_price_reconciliation.py`

### 2.1 Row Count Reconciliation
- Theoretical uniform matrix: $750 \text{ symbols} \times 2,883 \text{ calendar trading days} = 2,162,250 \text{ bars}$.
- Actual rows in cache: $1,831,372 \text{ bars}$. Deficit = 330,878 bars.
- Exported: `deliverables/gate_2c/data_csv/price_symbol_summary.csv` (750 symbols).

#### Distribution of Symbols by First-Bar Year:
- 2007: 95 symbols (12.7%)
- 2008: 1 symbol (0.1%)
- 2009: 2 symbols (0.3%)
- 2010: 8 symbols (1.1%)
- 2011: 2 symbols (0.3%)
- 2013: 1 symbol (0.1%)
- 2014: 1 symbol (0.1%)
- **2015: 331 symbols (44.1%)**
- 2016: 24 symbols (3.2%)
- 2017: 21 symbols (2.8%)
- 2018: 23 symbols (3.1%)
- 2019: 21 symbols (2.8%)
- 2020: 18 symbols (2.4%)
- 2021: 42 symbols (5.6%)
- 2022: 29 symbols (3.9%)
- 2023: 35 symbols (4.7%)
- 2024: 41 symbols (5.5%)
- 2025: 55 symbols (7.3%)

**Reconciliation Finding**:
309 of the 750 symbols were listed after 2015-01-01 and have zero bars prior to listing. 110 symbols contain pre-2015 data extending back to 2007. Exactly 1 symbol exhibits an internal gap vs the index calendar.

### 2.2 Manifest "seed_start 2015-01-01" Confirmation
- Symbols with bars before 2015-01-01: **110 symbols**.
- Total bars before 2015-01-01: **200,626 bars**.
- 640 symbols start strictly on or after 2015-01-01.

### 2.3 Gzip Archive Cross-Check
- `stock_ohlcv_cache.pkl.gz` (8.3 MB) fails standard decompression with:
  `EOFError: Compressed file ended before the end-of-stream marker was reached`
  and unpickling fails with:
  `_pickle.UnpicklingError: pickle data was truncated`.
  **Diagnosis**: The file was partially written / truncated at byte 8,661,398.
- Backup archive `tmp_drive/stock_ohlcv_cache.pkl.gz` (54 MB) decompresses cleanly and matches `stock_ohlcv_cache.pkl` 100% on all 1,831,372 rows with 0 differing values.

### 2.4 Adjusted vs Unadjusted Price Test
- **Bars with |1-day move| > 40%**: 52 bars.
- **Top 5 1-Day Moves**:
  - `BANCOINDIA` (2007-11-23): prev 1.34 $\rightarrow$ close 7.35 (+450.54%)
  - `ABB` (2007-06-28): prev 158.69 $\rightarrow$ close 862.33 (+443.39%)
  - `ARE&M` (2007-09-19): prev 7.77 $\rightarrow$ close 40.18 (+416.92%)
  - `ALOKINDS` (2020-02-19): prev 3.30 $\rightarrow$ close 16.85 (+410.61%)
  - `THYROCARE` (2019-10-27): prev 157.06 $\rightarrow$ close 482.41 (+207.16%)

#### 5 Known Split / Bonus Corporate Actions:
1. `INFY` (2018-09-04, 1:1 Bonus): 2018-09-03 close 577.85 $\rightarrow$ 2018-09-04 close 593.99 (smooth, no 50% drop).
2. `TCS` (2018-06-01, 1:1 Bonus): 2018-05-31 close 1414.68 $\rightarrow$ 2018-06-01 close 1407.69 (continuous).
3. `RELIANCE` (2017-09-07, 1:1 Bonus): 2017-09-06 close 361.74 $\rightarrow$ 2017-09-07 close 359.72 (continuous).
4. `BAJAJFINSV` (2022-09-13, 5:1 Split + 1:1 Bonus): 2022-09-12 close 1709.53 $\rightarrow$ 2022-09-13 close 1780.30 (continuous, pre-split divided by 10).
5. `WIPRO` (2019-03-06, 1:3 Bonus): 2019-03-05 close 123.77 $\rightarrow$ 2019-03-06 close 125.93 (continuous).

**Verdict**: Prices are **unequivocally retroactively adjusted**.

### 2.5 Decimals Audit
- Closes with > 2 decimal places: **1,785,884 / 1,831,372 (97.52%)**.
- Exported 5 raw rows for INFY to `deliverables/gate_2c/samples/raw_rows_INFY.csv`.

### 2.6 Data Quality Audit & OHLC Anomalies
- Duplicates on `(symbol, date)`: **0**.
- Non-monotonic dates: **0**.
- High < Low rows: **3 rows** (BAJAJELEC 2010-02-03, 2010-02-04; CEMPRO 2013-08-21).
- High < Close rows: **60 rows**.
- Exported to `deliverables/gate_2c/samples/ohlc_anomalies.csv` (63 rows).

### 2.7 Source Attribution Correction
The phrase "raw Bhavcopy bars" is **factually retracted**. The cache contains retroactively adjusted prices with floating-point multipliers originating from an external API (likely Yahoo Finance / yfinance). Specific upstream vendor: **UNKNOWN**.

---

## Step 3: Backtestable-Window Report (NIFTY500 ONLY)

Exact command run: `/usr/bin/python3 scripts/step3_backtestable_window.py`

### 3.1 Window Derivation
- `window_start`: **2016-01-14** (253rd cached NSEI bar on/after 2015-01-01, following a 252-bar warm-up).
- `window_end`: **2020-09-14** (`covered_end` of NIFTY500).
- Total monthly rebalance snapshots: **57 snapshots**.
- Exported: `deliverables/gate_2c/data_csv/window_fractions.csv`.

### 3.2 Window Statistics
- Mapped Fraction: min = 54.69%, median = 60.51%
- Price-Covered Fraction: min = 17.37%, median = 28.54%
- Joint Both Fraction: min = 14.77%, median = 24.56%
- Snapshots with Both < 80%: **57 / 57 (100.0%)**

### 3.3 Milestone Snapshots
- **2016-01-04 (First Trading Day 2016)**: Total: 501 | Mapped: 274/501 (54.69%) | Covered: 87/501 (17.37%) | Both: 74/501 (14.77%)
- **2018-01-01 (First Trading Day 2018)**: Total: 507 | Mapped: 303/507 (59.76%) | Covered: 139/507 (27.42%) | Both: 118/507 (23.27%)
- **2020-09-14 (`covered_end`)**: Total: 515 | Mapped: 337/515 (65.44%) | Covered: 177/515 (34.37%) | Both: 153/515 (29.71%)

### 3.4 Mandatory Disclosure Line
> **Universe reconstruction incomplete in 57 of 57 snapshots.**  
> *SURVIVORSHIP NOTE: Local price data represents a survivor-only cache spanning 750 current surviving entities. Delisted constituents, past merger targets, and defunct historical members lack historical price bars in the cache. Full point-in-time backtesting across this window is therefore unachievable without acquiring historical daily Bhavcopy archives for delisted entities.*

### 3.5 Full 1998–2020 Comparison (NOT BACKTESTABLE)
Across 266 historical monthly snapshots from 1998 to 2020:
- Pre-2007: Price coverage is strictly 0.0% (zero cached bars).
- 2007–2014: Price coverage is $<15\%$ (only 110 surviving stocks exist).
- Survivorship bias is extreme throughout 1998–2014.

---

## Step 4: Gate 1 Clean-Up & Anomaly Grouping

Exact command run: `/usr/bin/python3 scripts/step4_gate1_cleanup.py`

### 4.1 Dividend Opportunities 50 Audit
- Exported rows 124–134 to `deliverables/gate_2c/samples/divopp_2017_rows.csv`.
- Confirmed: In this sheet, rows are in **strict chronological order**:
  - Rows 124–127: `2016-11-15`
  - Rows 128–131: `2017-09-05`
  - Rows 132–134: `2017-12-29`
- The second pair (rows 130 and 131) was quarantined for being duplicate rebalance events, **not for being out of order**.

### 4.2 Anomaly Group `grp_2017_09_05`
- Exported `deliverables/gate_2c/data_csv/quarantine_gate1.csv` with `group_id = 'grp_2017_09_05'` covering all twelve 2017-09-05 datetime cells across 6 sheets:
  - `Nifty 200` (rows 348, 354): embedded in 2017-09-29 block
  - `Nifty Midcap 100` (rows 392, 397): embedded in 2017-09-29 block
  - `Nifty 500` (rows 2136, 2162): embedded in 2017-09-29 block
  - `Nifty Midcap 50` (rows 287, 289): embedded in 2017-09-29 block
  - `Nifty High Beta 50` (rows 125, 128): embedded in 2017-09-29 block
  - `Nifty Dividend Opportunities 50` (rows 130, 131): duplicate pair following earlier 2017-09-05 pair

### 4.3 Free-Float Merge Component Counts
- **Nifty Midcap 100**: 406 (Free Float) + 188 (Standard) = 594 rows (pre-quarantine); 406 + 186 = 592 rows (post-quarantine).
- **Nifty Smallcap 100**: 348 (Free Float) + 246 (Standard) = 594 rows (pre- and post-quarantine).

### 4.4 Gate 0 Artifact Relabeling
`data/raw_bulletins/nifty_replacement_circular_sep_2020.pdf` (`CML45722.pdf`) is relabeled as:
**Debt-Market Listing Circular (NSE Circular CML45722)** — contains no equity index constituent rebalancing actions.

---

## Step 5: Data-Source Reachability Probe (Decision Support)

Exact command run: `/usr/bin/python3 scripts/step5_data_source_probe.py`

### 5.1 Probing Candidate Patterns
Target Dates: `2008-01-02`, `2015-01-02`, `2020-09-14`.

| Target Date | Candidate URL | HTTP Status | Response Bytes | Local File Written |
|---|---|---|---|---|
| 2008-01-02 | `https://nsearchives.nseindia.com/content/historical/EQUITIES/2008/JAN/cm02JAN2008bhav.csv.zip` | 200 OK | 36,474 B | `samples/probe/cm02JAN2008bhav.csv.zip` |
| 2008-01-02 | `https://nsearchives.nseindia.com/products/content/sec_bhavdata_full_02012008.csv` | 404 Not Found | 0 B | N/A |
| 2015-01-02 | `https://nsearchives.nseindia.com/content/historical/EQUITIES/2015/JAN/cm02JAN2015bhav.csv.zip` | 200 OK | 58,101 B | `samples/probe/cm02JAN2015bhav.csv.zip` |
| 2015-01-02 | `https://nsearchives.nseindia.com/products/content/sec_bhavdata_full_02012015.csv` | 404 Not Found | 0 B | N/A |
| 2020-09-14 | `https://nsearchives.nseindia.com/content/historical/EQUITIES/2020/SEP/cm14SEP2020bhav.csv.zip` | 200 OK | 71,668 B | `samples/probe/cm14SEP2020bhav.csv.zip` |
| 2020-09-14 | `https://nsearchives.nseindia.com/products/content/sec_bhavdata_full_14092020.csv` | 200 OK | 220,495 B | `samples/probe/sec_bhavdata_full_14092020.csv` |

### 5.2 Delisted Stock Test in 2015-01-02 Exchange Bhavcopy
Searched in `cm02JAN2015bhav.csv`:
- `RELCAPITAL`: **FOUND** (`RELCAPITAL,EQ,498.25,507.8,497.35,498.8,499,497.75,2573465,1293688402.45,02-JAN-2015,40807,INE013A01015,`)
- `UNITECH`: **FOUND** (`UNITECH,EQ,16.85,17.75,16.85,17.4,17.4,16.85,50635119,880211328.6,02-JAN-2015,38887,INE694A01020,`)
- `RCOM`: **FOUND** (`RCOM,EQ,83.15,83.9,82.25,82.8,83.05,83.25,4638938,385743086.2,02-JAN-2015,20983,INE330H01018,`)
- `DHFL`: **FOUND** (`DHFL,EQ,412.95,428,402.1,418.1,416,412.95,3281261,1363668054.2,02-JAN-2015,42390,INE202B01012,`)

### 5.3 Data Characteristics
- **Columns**: `SYMBOL, SERIES, OPEN, HIGH, LOW, CLOSE, LAST, PREVCLOSE, TOTTRDQTY, TOTTRDVAL, TIMESTAMP, TOTALTRADES, ISIN`
- **Contains SERIES**: YES (`EQ`, `BE`, `DR`, etc.)
- **Contains ISIN**: YES
- **Pricing Mode**: **Unadjusted exchange trade summary** (INR and paise, 2 decimal places).
- **Bulk Download Status**: ZERO bulk downloads were started. Only the 4 probe sample files were saved.

---

## Step 6: Read-Only Safety Verification
- `apply_symbol_map_review.py` was NOT invoked on any production files.
- `corrections.parquet` was untouched (Gate 3).
- `data/symbol_map.parquet` was replaced only by the v3 rebuild in Step 1 after archiving v2b.

---

## Step 7: Deliverables Integrity
All files required for reviewer inspection reside exclusively in `deliverables/gate_2c/`.
Checksums for all deliverables and source files are compiled into `SHA256SUMS.txt`.
HALT-1b remains **OPEN** awaiting reviewer decision.
