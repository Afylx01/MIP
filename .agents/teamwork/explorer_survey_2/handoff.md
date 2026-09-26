# Handoff Report — Gate Scripts and Verification Survey (Phase 5.5 Gate 2b)

**Sender:** Explorer 2 (Gate Scripts & Verification Surveyor)  
**Recipient:** Orchestrator / Implementer  
**Timestamp:** 2026-09-24T01:42:30Z  
**Working Directory:** `/storage/emulated/0/Documents/Project MIP/.agents/teamwork/explorer_survey_2`  
**Report Type:** Hard Handoff (Investigation Complete)

---

## 1. Observation

1. **Gate 1(c) Date Validation & Ambiguous Rows:**
   - In `scripts/gate1_parse_validate.py` (lines 166–182), ambiguous rows are identified when `cell.ctype == xlrd.XL_CELL_TEXT` and the day token $d \le 12$. Total ambiguous rows across all sheets: **1,633 rows**.
   - In `scripts/gate1_parse_validate.py` (lines 252–287), trading day calendar validation used a raw byte regex `re.findall(rb"\d{4}-\d{2}-\d{2}", raw)` against `/storage/emulated/0/MIP1_Scanner/data/index__NSEI_cache.pkl` and fell back to `(df_dt.weekday() < 5)` for dates prior to 2007-01-01.
   - The official trading calendar extracted from `index__NSEI_cache.pkl` spans from `2007-09-17` to `2026-08-31` (4,649 unique trading days).
   - Restricted set evaluation: Exactly **451 ambiguous rows** fall within the calendar date range (`2007-09-17` to `2026-08-31`). On this restricted set:
     - Day-first trading-day hits: **451 / 451 (100.00%)**. Non-trading day count: **0**.
     - Month-first trading-day hits: **349 / 451 (77.38%)**. Non-trading day count: **102**.
   - Ambiguous rows outside the calendar date range: Exactly **1,182 rows** (all prior to 2007-09-17, from 1998 to 2007).

2. **The 2017-09-05 Event in `Nifty Dividend Opportunities 50`:**
   - In `IndexInclExcl.xls`, Sheet `Nifty Dividend Opportunities 50`:
     - Row 128: `ctype=3` (`xlrd.XL_CELL_DATE`), `value=42983.0` (`2017-09-05`), Scrip: `Reliance Capital Ltd.`, Action: `Exclusion from Index`
     - Row 129: `ctype=3` (`xlrd.XL_CELL_DATE`), `value=42983.0` (`2017-09-05`), Scrip: `National Aluminium Co. Ltd.`, Action: `Inclusion into Index`
     - Row 130: `ctype=3` (`xlrd.XL_CELL_DATE`), `value=42983.0` (`2017-09-05`), Scrip: `Reliance Capital Ltd.`, Action: `Exclusion from Index`
     - Row 131: `ctype=3` (`xlrd.XL_CELL_DATE`), `value=42983.0` (`2017-09-05`), Scrip: `National Aluminium Co. Ltd.`, Action: `Inclusion into Index`
   - Neighbouring rows: Row 127 is `2016-11-15`, Row 132 is `2017-12-29`.
   - In `scripts/gate1_parse_validate.py`, the quarantine check (lines 211–215) only flagged rows where `dt < prev_df`. Since Row 128 follows Row 127 (`2017-09-05 > 2016-11-15`), Row 129 equals Row 128, Row 130 equals Row 129, and Row 131 equals Row 130, no row triggered `dt < prev_df`.
   - In Step 5 (Deduplication, lines 331–342), Rows 130 and 131 matched the composite key `(index, effective_date, scrip_name, action)` already established by Rows 128 and 129, and were removed as exact duplicates.
   - In 5 other sheets (`Nifty 200`, `Nifty Midcap 100`, `Nifty 500`, `Nifty Midcap 50`, `Nifty High Beta 50`), the duplicate pair was inserted into the `2017-09-29` block, where `2017-09-05 < 2017-09-29` evaluated to True, triggering quarantine (10 rows total).

3. **Current Storage of Quarantined vs Deduplicated Rows:**
   - Quarantined rows (10 rows): Stored in `data/quarantine_gate1.parquet` (columns: `source_label, effective_date, scrip_name, action, source, sheet, row, date_type`).
   - Deduplicated rows (10 rows): Printed to stdout in `scripts/gate1_parse_validate.py` (lines 343–347), but not stored in a parquet artifact.
   - Non-monotonic steps before quarantine: 10 steps (2 in each of 5 sheets).
   - Non-monotonic steps after quarantine: **0 for all 37 sheets**.

4. **Gate 0 Cached Files:**
   - `data/raw_bulletins/nifty_replacement_circular_sep_2020.pdf`: Decompressed text contains:
     `Download Ref. No.: NSE/CML/45722 Date : September 16, 2020 Circular Ref. No.: 0810/2020 Sub: Listing of privately placed securities on the debt market segment of the Exchange`.
     Zero equity index replacement content.
   - `data/raw_bulletins/niftyindices___rebalancing_schedule_200.html`: Contains general reconstitution frequencies (e.g. "Semi-annually - Last working day of March and September") with no constituent-level transition records.

5. **Gate 2 Report & Reconstitution Scoping:**
   - Located at the end of `scripts/gate2_build_symbol_map.py` (lines 226–308).
   - Currently loops over all 7 primary indices. Because only `NIFTY500` contains a 500-member seed batch on 1998-08-01, replaying non-seed indices starts from 0 members and produces incomplete member counts (e.g., NIFTY50 showing 43–51 members; NIFTY200 and NIFTYSMALLCAP100 showing `0/0 (0.0%)` on 2010-01-01).

---

## 2. Logic Chain

1. **Calendar Validation Hit Rates (Observation 1 $\rightarrow$ Conclusion):**
   - Given that 1,182 of the 1,633 ambiguous rows predate the start of the official NSE trading calendar (`2007-09-17`), mixing them with a Monday–Friday heuristic skews the empirical hit rate.
   - Restricting evaluation to the 451 ambiguous rows inside `[2007-09-17, 2026-08-31]`, Day-First achieves a 100.00% hit rate (451/451) while Month-First drops to 77.38% (349/451).
   - Therefore, Day-First date parsing is mathematically verified as the true format of the workbook.

2. **Deduplication vs Quarantine Discrepancy (Observation 2 $\rightarrow$ Conclusion):**
   - In all 6 sheets with duplicate 2017-09-05 transitions, the publisher duplicated the `Reliance Capital Ltd.` exclusion and replacement inclusion.
   - In 5 sheets, the duplicate pair was inserted into the later `2017-09-29` section, violating date monotonicity and being routed to `quarantine_gate1.parquet`.
   - In `Nifty Dividend Opportunities 50`, the duplicate pair was placed immediately next to the primary pair, preserving date monotonicity and being routed to deduplication.
   - To treat the suspect `2017-09-05` datetime duplicate class consistently, Rows 130 and 131 should be quarantined alongside the other 10 rows. This shifts quarantine from 10 to 12 rows, and deduplication from 10 to 8 rows, leaving final active rows unchanged at 9,121.

3. **Gate 0 Finding Verification (Observation 4 $\rightarrow$ Conclusion):**
   - The cached PDF is a debt market circular (`NSE/CML/45722`), and the cached HTML is a static calendar schedule. Neither provides point-in-time constituent transitions.
   - Therefore, the finding *"post-2020-09 bulletin availability NOT ESTABLISHED; deferred to Phase 5.6"* is fully grounded in fact.

4. **Gate 2 Scoping to NIFTY500 Only (Observation 5 $\rightarrow$ Conclusion):**
   - Membership snapshots require an initial constituent baseline (seed). In `IndexInclExcl.xls`, only NIFTY500 possesses a seed (500 IN events on 1998-08-01). The other six indices contain only change events.
   - Running reconstitution on non-seed indices produces meaningless snapshots.
   - Restricting snapshot reconstitution, resolved fraction calculations, and Gates B–F to NIFTY500, while reporting other indices as `"event log only, not reconstructable"`, strictly aligns the engine with mathematical reality.

---

## 3. Caveats

1. **Pickle Loading Compatibility (R0 Interface):** In Python 3.14 / pandas 2.3.3, `pd.read_pickle` on `/storage/emulated/0/MIP1_Scanner/data/index__NSEI_cache.pkl` raises `NotImplementedError` due to Cython `NDArrayBacked.__setstate__` expecting a 3-element tuple for ExtensionDtypes. The trading days used in our survey were extracted directly from the binary stream without surrogate unpicklers. Explorer 1 / Implementer must produce `data/price_cache_export.parquet` via the approved R0 path.
2. **Pre-2007 Dates:** Trading day hit rates for the 1,182 rows prior to 2007-09-17 cannot be evaluated against `index__NSEI_cache.pkl` because the price cache begins on 2007-09-17.
3. **No Codebase Modification:** As a read-only explorer, no files in `scripts/`, `src/`, or `data/` were modified. All proposed changes are documented in `survey_report.md` and below.

---

## 4. Conclusion

1. **Gate 1(c) Calendar Validation:** Re-running against the restricted calendar range yields:
   - Day-First: **451 / 451 (100.00%)**
   - Month-First: **349 / 451 (77.38%)**
   - Outside calendar range: **1,182 rows**
2. **2017-09-05 Rows in Nifty Dividend Opportunities 50:**
   - Rows 130 and 131 (`Reliance Capital Ltd.` OUT, `National Aluminium Co. Ltd.` IN) were deduplicated because they were contiguous duplicates, avoiding the monotonic date order violation.
   - Classifying them as suspect datetime rows increases quarantine to 12 rows and reduces deduplication to 8 rows (both sets fully inventoried).
   - Post-quarantine non-monotonic step count is **0 for all 37 sheets**.
3. **Gate 0 Finding:** Confirmed and restated verbatim: *"post-2020-09 bulletin availability NOT ESTABLISHED; deferred to Phase 5.6"*.
4. **Gate 2 Report:** Must be restructured to:
   - Compute membership snapshots, resolved fractions, price coverage ($\ge 90\%$), and monthly rebalance statistics for **NIFTY500 ONLY**.
   - Output `"event log only, not reconstructable"` for the other six indices.
   - Print `N/A` for any snapshot with 0 members.
   - Include the survivorship disclosure line for each snapshot.

---

## 5. Verification Method

To independently verify all claims made in this report, execute the following commands in the workspace:

1. **Verify Ambiguous Calendar Hit Rates (Restricted Set & Outside Count):**
   ```bash
   python3 -c "
   import xlrd, datetime, re
   from scripts.gate1_parse_validate import parse_date_cell, normalize_action
   with open('/storage/emulated/0/MIP1_Scanner/data/index__NSEI_cache.pkl', 'rb') as f:
       raw = f.read()
   cal = set(d.decode('ascii') for d in re.findall(rb'\x8c\x0a(\d{4}-\d{2}-\d{2})', raw))
   min_c, max_c = min(cal), max(cal)
   wb = xlrd.open_workbook('IndexInclExcl.xls')
   amb = []
   for s in wb.sheets():
       for r in range(1, s.nrows):
           c1, c2, c3 = s.cell(r, 1), str(s.cell_value(r, 2)), str(s.cell_value(r, 3))
           dt, dt_type, parts = parse_date_cell(c1, wb.datemode)
           if dt_type == 'string' and parts[0] <= 12:
               try: mf = datetime.date(parts[2], parts[0], parts[1])
               except ValueError: mf = None
               amb.append((dt, mf))
   in_cal = [x for x in amb if min_c <= x[0].strftime('%Y-%m-%d') <= max_c]
   out_cal = [x for x in amb if not (min_c <= x[0].strftime('%Y-%m-%d') <= max_c)]
   df_hits = sum(1 for x in in_cal if x[0].strftime('%Y-%m-%d') in cal)
   mf_hits = sum(1 for x in in_cal if x[1] and x[1].strftime('%Y-%m-%d') in cal)
   print(f'Total: {len(amb)}, Inside: {len(in_cal)}, Outside: {len(out_cal)}')
   print(f'Day-first: {df_hits}/{len(in_cal)} ({df_hits/len(in_cal)*100:.2f}%)')
   print(f'Month-first: {mf_hits}/{len(in_cal)} ({mf_hits/len(in_cal)*100:.2f}%)')
   "
   ```
   **Expected Output:**
   `Total: 1633, Inside: 451, Outside: 1182`
   `Day-first: 451/451 (100.00%)`
   `Month-first: 349/451 (77.38%)`

2. **Verify Nifty Dividend Opportunities 50 Rows 128–131:**
   ```bash
   python3 -c "
   import xlrd
   wb = xlrd.open_workbook('IndexInclExcl.xls')
   s = wb.sheet_by_name('Nifty Dividend Opportunities 50')
   for r in [127, 128, 129, 130]:
       c1, c2, c3 = s.cell(r, 1), s.cell(r, 2), s.cell(r, 3)
       dt = xlrd.xldate_as_datetime(c1.value, wb.datemode).date()
       print(f'Row {r+1}: ctype={c1.ctype} val={c1.value} dt={dt} | scrip={c2.value} | desc={c3.value}')
   "
   ```

3. **Verify Post-Quarantine Monotonicity (Expected 0 for all sheets):**
   ```bash
   python3 -c "
   import xlrd
   from scripts.gate1_parse_validate import parse_date_cell, normalize_action
   wb = xlrd.open_workbook('IndexInclExcl.xls')
   q_set = {('Nifty 200', 348), ('Nifty 200', 354), ('Nifty Midcap 100', 392), ('Nifty Midcap 100', 397), ('Nifty 500', 2136), ('Nifty 500', 2162), ('Nifty Midcap 50', 287), ('Nifty Midcap 50', 289), ('Nifty High Beta 50', 125), ('Nifty High Beta 50', 128)}
   bad = {}
   for s in wb.sheets():
       prev = None
       for r in range(1, s.nrows):
           if (s.name, r+1) in q_set: continue
           dt, _, _ = parse_date_cell(s.cell(r, 1), wb.datemode)
           if prev and dt < prev: bad[s.name] = bad.get(s.name, 0) + 1
           prev = dt
   print('Non-monotonic sheets after quarantine:', bad)
   "
   ```
   **Expected Output:** `Non-monotonic sheets after quarantine: {}`
