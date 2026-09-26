# Gate Scripts and Verification Survey Report — Phase 5.5 Gate 2b

**Surveyor:** Explorer 2 (Gate Scripts & Verification Surveyor)  
**Date:** 2026-09-24  
**Workspace:** `/storage/emulated/0/Documents/Project MIP`  
**Focus Scope:** R1 (Gate 1 Repairs), R2 (Gate 0 Restatement), R6 (Gate 2 Report Recomputation & Scoping)

---

## Executive Summary

This report delivers a comprehensive, empirical survey of the existing Gate 0, Gate 1, and Gate 2 scripts, data files, and verification mechanisms across the workspace. All observations cite exact file paths, line numbers, cell coordinates, and reproducible Python outputs.

Key survey findings:
1. **Gate 1(c) Calendar Validation:** Ambiguous rows (`string` cells with day $\le 12$) total exactly **1,633 rows**. Inside the official trading calendar range (`2007-09-17` to `2026-08-31`, 4,649 days derived from `index__NSEI_cache.pkl`), there are **451 ambiguous rows**, all of which (**100.00%**) hit official NSE trading days under day-first parsing. Under month-first parsing, only **349 rows (77.38%)** hit trading days (102 non-trading day misses). Exactly **1,182 rows** are outside the calendar date range (1998 to 2007-09-14).
2. **The 2017-09-05 Event & Deduplication vs Quarantine:** The exclusion of `Reliance Capital Ltd.` and corresponding inclusions occurred on `2017-09-05` across 7 sheets. In 5 sheets (`Nifty 200`, `Nifty Midcap 100`, `Nifty 500`, `Nifty Midcap 50`, `Nifty High Beta 50`), a duplicate copy of this pair was placed inside the `2017-09-29` block, breaking date monotonicity (`2017-09-05 < 2017-09-29`), causing them to be quarantined (10 rows). In `Nifty Dividend Opportunities 50`, duplicate Rows 130 and 131 immediately followed Rows 128 and 129 (`2017-09-05 == 2017-09-05`), so they never violated `< prev_date` and were instead removed by exact-duplicate deduplication. All 4 cells are `ctype=3` (`xlrd.XL_CELL_DATE`, float value `42983.0`). If quarantined consistently as suspect datetime rows, quarantine count increases from 10 to 12 rows, and deduplication count decreases from 10 to 8 rows.
3. **Monotonicity & Current Row Storage:** Day-first non-monotonic step count is 10 before quarantine and **0 for all 37 sheets** after quarantining the out-of-sequence rows. The 10 quarantined rows are stored in `data/quarantine_gate1.parquet`. The 10 deduplicated rows were logged to stdout in `scripts/gate1_parse_validate.py` but not written to an artifact.
4. **Gate 0 Restatement:** Decompressed stream extraction of `data/raw_bulletins/nifty_replacement_circular_sep_2020.pdf` proves it is `NSE/CML/45722` (September 16, 2020) for debt market private placements—not an equity index rebalancing document. `data/raw_bulletins/niftyindices___rebalancing_schedule_200.html` provides only broad schedule cadences. The Gate 0 finding stands: *"post-2020-09 bulletin availability NOT ESTABLISHED; deferred to Phase 5.6"*.
5. **Gate 2 Report & Reconstitution Scoping:** Reconstructed membership snapshots and resolved fractions are currently computed in `scripts/gate2_build_symbol_map.py` (lines 226–308). The script erroneously attempted to compute snapshots for all 7 indices, leading to distorted fractions (e.g., NIFTY50 showing 43–51 members, NIFTY200 showing 0 members). R6 properly restricts snapshots, resolved fractions, and Gates B–F to **NIFTY500 ONLY**, requires reporting price coverage ($\ge 90\%$), printing `event log only, not reconstructable` for the other six indices, printing `N/A` for zero-member snapshots, and appending a survivorship disclosure note.

---

## Section 1: Gate 1(c) Calendar Validation & Ambiguous Date Analysis (R1)

### 1.1 Implementation Architecture
- **Script Location:** `scripts/gate1_parse_validate.py`
- **Ambiguous Date Detection:** Lines 166–182:
  ```python
  if date_type == "string" and date_parts[0] <= 12:
      d, m, y = date_parts
      try:
          mf_dt = datetime.date(y, d, m)
      except ValueError:
          mf_dt = None
      ambiguous_rows.append({
          "sheet": sname,
          "row": r + 1,
          "scrip_name": scrip_name,
          "raw_string": str(date_cell.value).strip(),
          "day_first_date": dt,
          "month_first_date": mf_dt,
          "action": action,
      })
  ```
  A date is defined as ambiguous when:
  - Raw Excel cell type is text (`cell.ctype == xlrd.XL_CELL_TEXT`, `date_type == "string"`).
  - The first token (day) satisfies $d \le 12$, allowing an alternative interpretation as a month in `MM-DD-YYYY` format.

- **Current Step 3(c) Flaws (Lines 252–287):**
  - Read `TRADING_CALENDAR_PATH = "/storage/emulated/0/MIP1_Scanner/data/index__NSEI_cache.pkl"` via raw regex bytes: `re.findall(rb"\d{4}-\d{2}-\d{2}", raw)`.
  - For dates before `2007-01-01` (or if calendar was unavailable), it fell back to `is_df_td = (df_dt.weekday() < 5)` (Monday–Friday).
  - It evaluated the entire set of 1,633 ambiguous rows mixed with the weekday fallback, rather than evaluating the empirical trading calendar hit rate strictly on the evaluable date range.

### 1.2 Official Calendar Derivation
- **Source:** Exported NSE index bars from `/storage/emulated/0/MIP1_Scanner/data/index__NSEI_cache.pkl` (verified against `manifest.json`).
- **Date Range:** `2007-09-17` to `2026-08-31`
- **Total Official Trading Days:** Exactly **4,649 trading days** (all unique, sorted).

### 1.3 Restricted Set Validation Results
Restricting validation to ambiguous rows falling within `[2007-09-17, 2026-08-31]`:

| Metric | Day-First Parsing | Month-First Parsing | Notes |
|---|---|---|---|
| **Total Ambiguous Rows** | 1,633 | 1,633 | String cells with $d \le 12$ |
| **Rows Outside Calendar Range** | 1,182 | 1,182 | All dates prior to 2007-09-17 (1998–2007) |
| **Rows Inside Calendar Range (Restricted Set)** | 451 | 451 | Dates in `[2007-09-17, 2026-08-31]` |
| **Trading Day Hits on Restricted Set** | **451** | **349** | Hit count against official NSE calendar |
| **Trading Day Hit Rate (%)** | **100.00%** | **77.38%** | Day-first is flawless |
| **Non-Trading Days (Restricted Set)** | **0** | **102** | Month-first produces 102 invalid dates |

#### Breakdown of 1,182 Rows Outside Calendar Range:
- Year 1998: 558 rows (includes 500 IN seed rows for NIFTY500 on 1998-08-01)
- Year 1999: 84 rows
- Year 2000: 26 rows
- Year 2001: 44 rows
- Year 2002: 30 rows
- Year 2003: 122 rows
- Year 2004: 174 rows
- Year 2005: 22 rows
- Year 2006: 68 rows
- Year 2007 (prior to Sept 17): 54 rows
- **Total outside range:** Exactly 1,182 rows.

**Finding:** Day-first parsing achieves a **100.00% hit rate** against the official NSE trading calendar on all evaluable dates.

---

## Section 2: The 2017-09-05 Event & Deduplication vs Quarantine Analysis (R1)

### 2.1 The Event Context
In September 2017, `Reliance Capital Ltd.` underwent corporate restructuring (demerger of Reliance Home Finance Ltd.). Across 7 sheets in `IndexInclExcl.xls`, NSE recorded an exclusion of `Reliance Capital Ltd.` on effective date `2017-09-05`, paired with an inclusion of a replacement stock.

### 2.2 Survey Across All Sheets
In 6 of the 7 sheets, this transition was duplicated:

| Sheet Name | Row | Effective Date | Cell Type (`ctype`) | Scrip Name | Action | Status in Old Gate 1 |
|---|---|---|---|---|---|---|
| **Nifty 200** | 343 | 2017-09-05 | 3 (xldate) | Reliance Capital Ltd. | OUT | Active |
| Nifty 200 | 344 | 2017-09-05 | 3 (xldate) | Max Financial Services Ltd. | IN | Active |
| Nifty 200 | 348 | 2017-09-05 | 3 (xldate) | Reliance Capital Ltd. | OUT | **Quarantined** (inside 2017-09-29) |
| Nifty 200 | 354 | 2017-09-05 | 3 (xldate) | Max Financial Services Ltd. | IN | **Quarantined** (inside 2017-09-29) |
| **Nifty Midcap 100** | 388 | 2017-09-05 | 3 (xldate) | Reliance Capital Ltd. | OUT | Active |
| Nifty Midcap 100 | 389 | 2017-09-05 | 3 (xldate) | Avenue Supermarts Ltd. | IN | Active |
| Nifty Midcap 100 | 392 | 2017-09-05 | 3 (xldate) | Reliance Capital Ltd. | OUT | **Quarantined** (inside 2017-09-29) |
| Nifty Midcap 100 | 397 | 2017-09-05 | 3 (xldate) | Avenue Supermarts Ltd. | IN | **Quarantined** (inside 2017-09-29) |
| **Nifty 500** | 2119 | 2017-09-05 | 3 (xldate) | Reliance Capital Ltd. | OUT | Active |
| Nifty 500 | 2120 | 2017-09-05 | 3 (xldate) | Max Financial Services Ltd. | IN | Active |
| Nifty 500 | 2136 | 2017-09-05 | 3 (xldate) | Reliance Capital Ltd. | OUT | **Quarantined** (inside 2017-09-29) |
| Nifty 500 | 2162 | 2017-09-05 | 3 (xldate) | Max Financial Services Ltd. | IN | **Quarantined** (inside 2017-09-29) |
| **Nifty Midcap 50** | 282 | 2017-09-05 | 3 (xldate) | Reliance Capital Ltd. | OUT | Active |
| Nifty Midcap 50 | 283 | 2017-09-05 | 3 (xldate) | Berger Paints India Ltd. | IN | Active |
| Nifty Midcap 50 | 287 | 2017-09-05 | 3 (xldate) | Reliance Capital Ltd. | OUT | **Quarantined** (inside 2017-09-29) |
| Nifty Midcap 50 | 289 | 2017-09-05 | 3 (xldate) | Berger Paints India Ltd. | IN | **Quarantined** (inside 2017-09-29) |
| **Nifty High Beta 50** | 120 | 2017-09-05 | 3 (xldate) | Reliance Capital Ltd. | OUT | Active |
| Nifty High Beta 50 | 121 | 2017-09-05 | 3 (xldate) | Jaiprakash Associates Ltd. | IN | Active |
| Nifty High Beta 50 | 125 | 2017-09-05 | 3 (xldate) | Reliance Capital Ltd. | OUT | **Quarantined** (inside 2017-09-29) |
| Nifty High Beta 50 | 128 | 2017-09-05 | 3 (xldate) | Jaiprakash Associates Ltd. | IN | **Quarantined** (inside 2017-09-29) |
| **Nifty Div Opp 50** | 128 | 2017-09-05 | 3 (xldate) | Reliance Capital Ltd. | OUT | Active |
| Nifty Div Opp 50 | 129 | 2017-09-05 | 3 (xldate) | National Aluminium Co. Ltd. | IN | Active |
| Nifty Div Opp 50 | 130 | 2017-09-05 | 3 (xldate) | Reliance Capital Ltd. | OUT | **Deduplicated** (contiguous dup) |
| Nifty Div Opp 50 | 131 | 2017-09-05 | 3 (xldate) | National Aluminium Co. Ltd. | IN | **Deduplicated** (contiguous dup) |
| **LargeMidcap 250** | 609 | 2017-09-05 | 3 (xldate) | Reliance Capital Ltd. | OUT | Active (no duplicate in sheet) |
| LargeMidcap 250 | 610 | 2017-09-05 | 3 (xldate) | Max Financial Services Ltd. | IN | Active (no duplicate in sheet) |

### 2.3 Detailed Inspection of Nifty Dividend Opportunities 50 (Rows 128–131)
- **Cell Details:**
  - Row 128: `ctype = 3` (`xlrd.XL_CELL_DATE`), `value = 42983.0` $\rightarrow$ `2017-09-05`
  - Row 129: `ctype = 3` (`xlrd.XL_CELL_DATE`), `value = 42983.0` $\rightarrow$ `2017-09-05`
  - Row 130: `ctype = 3` (`xlrd.XL_CELL_DATE`), `value = 42983.0` $\rightarrow$ `2017-09-05`
  - Row 131: `ctype = 3` (`xlrd.XL_CELL_DATE`), `value = 42983.0` $\rightarrow$ `2017-09-05`
- **Neighbouring Rows:**
  - Row 126: `2016-11-15` | `Tech Mahindra Ltd.` | Inclusion into Index
  - Row 127: `2016-11-15` | `Torrent Pharmaceuticals Ltd.` | Inclusion into Index
  - **Row 128:** `2017-09-05` | `Reliance Capital Ltd.` | Exclusion from Index
  - **Row 129:** `2017-09-05` | `National Aluminium Co. Ltd.` | Inclusion into Index
  - **Row 130:** `2017-09-05` | `Reliance Capital Ltd.` | Exclusion from Index
  - **Row 131:** `2017-09-05` | `National Aluminium Co. Ltd.` | Inclusion into Index
  - Row 132: `2017-12-29` | `ACC Ltd.` | Exclusion from Index
  - Row 133: `2017-12-29` | `CARE Ratings Ltd.` | Exclusion from Index

### 2.4 Why Rows 130 & 131 Were Deduplicated Rather Than Quarantined
1. **The Quarantine Criterion in `scripts/gate1_parse_validate.py` (lines 211–215):**
   ```python
   if prev_df and dt < prev_df:
       steps_df += 1
       if r["date_type"] == "datetime":
           quarantined_candidates.append(r)
   prev_df = dt
   ```
   The quarantine logic strictly caught records where `dt < prev_df` (a strictly backwards date step).
2. **Evaluation in `Nifty Dividend Opportunities 50`:**
   - Row 128 (`2017-09-05`) follows Row 127 (`2016-11-15`): `2017-09-05 < 2016-11-15` is False.
   - Row 129 (`2017-09-05`) follows Row 128 (`2017-09-05`): `2017-09-05 < 2017-09-05` is False.
   - Row 130 (`2017-09-05`) follows Row 129 (`2017-09-05`): `2017-09-05 < 2017-09-05` is False.
   - Row 131 (`2017-09-05`) follows Row 130 (`2017-09-05`): `2017-09-05 < 2017-09-05` is False.
   - Row 132 (`2017-12-29`) follows Row 131 (`2017-09-05`): `2017-12-29 < 2017-09-05` is False.
   Because Rows 130 and 131 are contiguous with Rows 128 and 129, date monotonicity was preserved. Neither row was quarantined.
3. **Evaluation in Step 5 Deduplication (lines 331–342):**
   ```python
   key = (r["index"], r["effective_date"], r["scrip_name"], r["action"])
   if key in seen_keys:
       duplicates_removed.append(r)
   else:
       seen_keys.add(key)
   ```
   Rows 128 and 129 registered keys `(NIFTYDIVOPP50, 2017-09-05, "Reliance Capital Ltd.", "OUT")` and `(NIFTYDIVOPP50, 2017-09-05, "National Aluminium Co. Ltd.", "IN")`.
   When Rows 130 and 131 were processed, their keys matched, and they were dropped as exact duplicates.
4. **Contrast with the Other 5 Sheets:**
   In `Nifty 200`, `Nifty Midcap 100`, `Nifty 500`, `Nifty Midcap 50`, and `Nifty High Beta 50`, the second copy of the `2017-09-05` pair was misplaced by the publisher inside the `2017-09-29` rebalance block.
   Because `2017-09-05 < 2017-09-29`, they triggered the `dt < prev_df` check and were quarantined before reaching Step 5 deduplication.

### 2.5 Impact of Consistent Quarantine Treatment (Before vs After)
If Rows 130 and 131 in `Nifty Dividend Opportunities 50` are quarantined as suspect datetime rows along with the other sheets:

| Metric | Before (Current Gate 1) | After Consistent Quarantine | Delta |
|---|---|---|---|
| **Quarantined Rows Count** | 10 | **12** | +2 |
| **Deduplicated Rows Count** | 10 | **8** | -2 |
| **Active Event Rows Written** | 9,121 | **9,121** | 0 |
| **Day-first Non-monotonic Steps** | 0 | **0** | 0 |

---

## Section 3: Monotonicity Checks, Quarantined Rows & Deduplicated Rows Inventory (R1)

### 3.1 Non-Monotonic Step Counts by Sheet
Before quarantine, exactly 5 sheets have non-monotonic steps (2 steps each, caused by the out-of-sequence `2017-09-05` rows inside the `2017-09-29` block):
- `Nifty 200`: 2 steps
- `Nifty Midcap 100`: 2 steps
- `Nifty 500`: 2 steps
- `Nifty Midcap 50`: 2 steps
- `Nifty High Beta 50`: 2 steps
- All other 32 sheets: 0 steps.
**Total non-monotonic steps before quarantine:** 10 steps under Day-First (compared to 106 steps under Month-First).
**Total non-monotonic steps after quarantine:** **0 for all 37 sheets**.

### 3.2 Inventory of the 10 Quarantined Rows (Current `data/quarantine_gate1.parquet`)

| # | Sheet Name | Row | Effective Date | Scrip Name | Action | Date Type | Notes |
|---|---|---|---|---|---|---|---|
| 1 | Nifty 200 | 348 | 2017-09-05 | Reliance Capital Ltd. | OUT | datetime | Inside 2017-09-29 block |
| 2 | Nifty 200 | 354 | 2017-09-05 | Max Financial Services Ltd. | IN | datetime | Inside 2017-09-29 block |
| 3 | Nifty Midcap 100 | 392 | 2017-09-05 | Reliance Capital Ltd. | OUT | datetime | Inside 2017-09-29 block |
| 4 | Nifty Midcap 100 | 397 | 2017-09-05 | Avenue Supermarts Ltd. | IN | datetime | Inside 2017-09-29 block |
| 5 | Nifty 500 | 2136 | 2017-09-05 | Reliance Capital Ltd. | OUT | datetime | Inside 2017-09-29 block |
| 6 | Nifty 500 | 2162 | 2017-09-05 | Max Financial Services Ltd. | IN | datetime | Inside 2017-09-29 block |
| 7 | Nifty Midcap 50 | 287 | 2017-09-05 | Reliance Capital Ltd. | OUT | datetime | Inside 2017-09-29 block |
| 8 | Nifty Midcap 50 | 289 | 2017-09-05 | Berger Paints India Ltd. | IN | datetime | Inside 2017-09-29 block |
| 9 | Nifty High Beta 50 | 125 | 2017-09-05 | Reliance Capital Ltd. | OUT | datetime | Inside 2017-09-29 block |
| 10 | Nifty High Beta 50 | 128 | 2017-09-05 | Jaiprakash Associates Ltd. | IN | datetime | Inside 2017-09-29 block |

### 3.3 Inventory of the 10 Deduplicated Rows (Current Gate 1 Output)

| # | Sheet Name | Row | Effective Date | Scrip Name | Action | Date Type | Reason Removed |
|---|---|---|---|---|---|---|---|
| 1 | Nifty Dividend Opportunities 50 | 130 | 2017-09-05 | Reliance Capital Ltd. | OUT | datetime | Duplicate of Row 128 |
| 2 | Nifty Dividend Opportunities 50 | 131 | 2017-09-05 | National Aluminium Co. Ltd. | IN | datetime | Duplicate of Row 129 |
| 3 | Nifty Infrastructure | 44 | 2011-10-10 | Adani Power Ltd. | IN | datetime | Block duplication of Row 41 |
| 4 | Nifty Infrastructure | 45 | 2011-10-10 | DLF Ltd. | OUT | datetime | Block duplication of Row 38 |
| 5 | Nifty Infrastructure | 46 | 2011-10-10 | Indian Hotels Co. Ltd. | OUT | datetime | Block duplication of Row 39 |
| 6 | Nifty Infrastructure | 47 | 2011-10-10 | NHPC Ltd. | IN | datetime | Block duplication of Row 42 |
| 7 | Nifty Infrastructure | 48 | 2011-10-10 | Unitech Ltd. | OUT | datetime | Block duplication of Row 40 |
| 8 | Nifty Infrastructure | 49 | 2011-10-10 | Voltas Ltd. | IN | datetime | Block duplication of Row 43 |
| 9 | Nifty Realty | 41 | 2019-02-26 | Unitech Ltd. | OUT | datetime | Block duplication of Row 39 |
| 10 | Nifty Realty | 42 | 2019-02-26 | Mahindra Lifespace Developers Ltd. | IN | datetime | Block duplication of Row 40 |

---

## Section 4: Gate 0 Restatement & Bulletin Inspection (R2)

### 4.1 Cached Artifact Inspection
1. **File:** `data/raw_bulletins/nifty_replacement_circular_sep_2020.pdf` (302,766 bytes)
   - Extracted using `zlib.decompress` on FlateDecode content streams:
     ```
     Download Ref. No.: NSE/CML/45722
     Date : September 16, 2020
     Circular Ref. No.: 0810/2020
     To All Members,
     Sub: Listing of privately placed securities on the debt market segment of the Exchange
     In pursuance of Regulation 3.1.1 of the National Stock Exchange Debt Market Trading Regulations...
     ```
   - **Finding:** This circular is a standard NSE Debt Market listing circular for privately placed debt securities. It contains **zero equity index maintenance or replacement information**.
2. **File:** `data/raw_bulletins/niftyindices___rebalancing_schedule_200.html` (150,560 bytes)
   - HTML parsed with BeautifulSoup:
     ```
     Index Reconstitution Calendar
     Nifty Auto: Semi-annually - Last working day of March and September
     Nifty Bank: Semi-annually - Last working day of March and September
     ...
     Nifty500 Healthcare: Semi-annually - Last working day of March and September
     ```
   - **Finding:** This webpage contains only broad schedule cadences for semi-annual and quarterly rebalancings. It contains **no constituent-level change data, replacements, or historical transitions**.

### 4.2 Gate 0 Restatement Formulation
The Gate 0 inventory conclusion is re-confirmed verbatim:
> **"post-2020-09 bulletin availability NOT ESTABLISHED; deferred to Phase 5.6"**

---

## Section 5: Gate 2 Report Recomputation & Verification Architecture (R6)

### 5.1 Current Script Analysis
- The Gate 2 report is currently implemented directly inside `scripts/gate2_build_symbol_map.py` (lines 226–308).
- The script iterates through `PRIMARY_INDICES`:
  `["NIFTY50", "NIFTYNEXT50", "NIFTY100", "NIFTY200", "NIFTY500", "NIFTYMIDCAP100", "NIFTYSMALLCAP100"]`
- For each index, it performs:
  1. Scrip categorization: auto, proposed (with candidate), unresolved (no candidate), and blocked IN/OUT counts.
  2. Unblocked replay across Gate B snapshot dates (`2010-01-01`, `2014-01-01`, `2018-01-01`, and `covered_end`).
  3. Monthly rebalance snapshots across the full date range.

### 5.2 Flaws in Existing Gate 2 Replay and Reporting
1. **Replay Distortion on Non-Seed Indices:**
   - In `IndexInclExcl.xls`, only `NIFTY500` starts with a constituent seed batch (500 IN events on 1998-08-01).
   - The other six indices (`NIFTY50`, `NIFTYNEXT50`, `NIFTY100`, `NIFTY200`, `NIFTYMIDCAP100`, `NIFTYSMALLCAP100`) contain only subsequent change events.
   - When `scripts/gate2_build_symbol_map.py` replayed NIFTY50, it started from 0 members, resulting in:
     - 2010-01-01: 24 / 43 members resolved (55.8%)
     - 2014-01-01: 28 / 45 members resolved (62.2%)
     - 2018-01-01: 34 / 50 members resolved (68.0%)
     - 2020-07-31: 36 / 51 members resolved (70.6%)
   - For `NIFTY200` and `NIFTYSMALLCAP100` on 2010-01-01, total members was 0, and the script printed `0/0 (0.0%)`, which is statistically invalid.
2. **Missing Price-Coverage Fraction:**
   - The script only reported name-level resolution (`status in ('auto', 'approved')`).
   - It did not evaluate whether the resolved stocks had sufficient price bars (`coverage_pct >= 90`).
3. **Missing Survivorship Disclosure:**
   - It lacked the required transparency note disclosing how many members in each snapshot are unresolved or lack price coverage.

### 5.3 Required Design for Gate 2b Report (R6)
1. **Scope Restriction:**
   - **NIFTY500 ONLY** receives membership snapshots, resolved fractions, price-covered fractions, and monthly rebalance statistics.
   - The other six indices output an event log summary (scrip counts, blocked events) followed explicitly by:
     `"event log only, not reconstructable"`
2. **Zero-Member Handling:**
   - Any snapshot with 0 members must display `N/A`, never `0.0%`.
3. **Price Coverage Metric:**
   - Evaluated using candidate symbol bars in the membership window:
     $$\text{coverage\_pct} = \frac{\text{bars\_present}}{\text{bars\_expected}} \times 100$$
   - Report fraction with `coverage_pct >= 90.0%`.
4. **Survivorship Disclosure Format:**
   - For each evaluated snapshot, append:
     `Survivorship note: <n> of <total> NIFTY500 members at <snapshot> are unresolved or lack price data.`
     where $<n> = \text{total} - \text{count}(\text{status} \in \{\text{'auto'}, \text{'approved'}\} \land \text{coverage\_pct} \ge 90)$.
5. **Downstream Gates B–F:**
   - Point-in-time portfolio reconstruction and backtesting in Gates B–F must strictly target NIFTY500 only.

---

## Section 6: Actionable Implementation Recommendations for Implementer

1. **For R1 (`scripts/gate1_parse_validate.py`):**
   - Update `load_trading_calendar()` to read the official exported trading days from `data/price_cache_export.parquet` (or NSEI bars) rather than regex-scraping raw pickle bytes.
   - Refactor Gate 1(c) validation to explicitly separate rows inside the calendar range from those outside, reporting:
     - Total ambiguous rows: 1,633
     - Ambiguous rows outside calendar range: 1,182
     - Restricted set hit rate: Day-First = 451/451 (100.00%) vs Month-First = 349/451 (77.38%).
   - Classify Rows 130 and 131 of `Nifty Dividend Opportunities 50` as suspect datetime rows, adding them to `quarantine_gate1.parquet` (bringing quarantine to 12 rows, and deduplication to 8 rows).
   - Add explicit artifact writing for deduplicated rows (e.g., `data/deduped_gate1.parquet` or clear console table).
2. **For R2 (Gate 0 Restatement):**
   - Embed the exact verbatim citation and restatement in `gate_2b_verification.md` referencing the debt market listing circular (`NSE/CML/45722`) and schedule HTML.
3. **For R6 (`scripts/gate2_build_symbol_map.py`):**
   - Branch reporting logic by index: if `idx_name == "NIFTY500"`, compute snapshots, resolved fractions, price coverage fractions, and survivorship notes.
   - If `idx_name != "NIFTY500"`, print scrip counts and blocked event counts, then print `"event log only, not reconstructable"`.
   - Ensure snapshots with 0 members output `N/A`.
   - Add the survivorship disclosure line per snapshot.
