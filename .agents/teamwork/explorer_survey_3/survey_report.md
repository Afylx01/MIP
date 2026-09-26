# Survey Report: Symbol Map Rebuild, Review Tooling Refusal Hardening, and Canary Regressions

**Explorer:** Explorer 3 (Symbol Map and Review Tooling Surveyor)  
**Milestone:** Phase 5.5 — Gate 2b: Symbol Map Evidence Hardening  
**Target Requirements:** R3, R4, R5  
**Date:** 2026-09-24  
**Working Directory:** `/storage/emulated/0/Documents/Project MIP/.agents/teamwork/explorer_survey_3`

---

## 1. Executive Summary

This survey provides a comprehensive audit of the symbol resolution pipeline, review tooling, refusal enforcement mechanisms, and canary regression test suite for Phase 5.5 Gate 2b.

Key survey findings:
1. **Existing Symbol Map (`data/symbol_map.parquet`)**: Contains 1,448 rows (709 `auto`, 739 `proposed`). Current SHA-256 is `ae982c3e1c22bdcafcf9bec6de28385d7dd3b29d3392ad39935f4e1b0c28fc58`. It must be archived to `data/symbol_map_v1.parquet` before rebuilding.
2. **Hardcoded Knowledge in `scripts/gate2_build_symbol_map.py`**: A dictionary `KNOWN_CORPORATE_RENAMES` with 37 entries is currently hardcoded and assigned `resolution_method: "manual"`, `confidence: "high"`, and `status: "proposed"`. Under R3, this must be refactored to `resolution_method: "agent_memory"`, `confidence: "low"`, `status: "proposed"`, and flagged `unsourced`.
3. **Flawed "Last Row Wins" in EQUITY_L**: `EQUITY_L.csv` contains 6 rows sharing normalized company names (e.g. `FEL` vs `FELDVR`, `GATECH` vs `GATECHDVR`, `JISLDVREQS` vs `JISLJALEQS`). The previous script iterated through EQUITY_L and let later rows overwrite earlier rows, causing arbitrary symbol assignments. Screen S2 (`duplicate_name_collision`) will eliminate this vulnerability.
4. **Predecessor Markers (S5)**: Exactly 64 scrip names in `index_events.parquet` contain predecessor / suspended / merger / delisted markers. A regex using word boundaries (`\b(old|sus|suspended|erstwhile|merge[a-z]*|arrangement|delisted)\b`, case-insensitive) is essential; simple substring matching creates severe false positives on legitimate names such as "Holdings" and "Golden".
5. **Concurrent Alias Collisions (S4)**: Under the previous map, 101 scrip names triggered concurrent alias collisions (sharing the same ISIN while active in the same index concurrently). Tracking active membership intervals per index detects these collisions and demotes them to `proposed`.
6. **Listing Date Discrepancies (S1)**: 256 scrips have EQUITY_L listing dates > 30 days after first index appearance. The auto rule allows S1 to remain `auto` *only* if `coverage_pct >= 90%` and all other auto criteria are met.
7. **Never-Removed Seed Constituents**: In NIFTY500 alone, 399 scrip names have only `IN` events (from the 1998-08-01 seed) and were never removed. The previous code set `last_seen` to `1998-08-01` (0-day window). Under R3, the membership end date for an unremoved stock is the index's `covered_end` (e.g. `2020-09-14` for NIFTY500), expanding the membership window to ~22 years.
8. **Review Tool Refusal Gaps**: `scripts/apply_symbol_map_review.py` currently permits setting `auto`, accepts empty symbols/ISINs, ignores missing approval notes on flagged rows, does not verify compound keys, does not back up the parquet file, and does not maintain an append-only audit trail in `data/symbol_map_changes.parquet`.
9. **Canary Regression Suite**: 18 canonical edge cases were identified and verified present in `data/index_events.parquet` covering all screens S1–S6, corporate renames, delistings, and token collisions. None should resolve to `auto`.

---

## 2. Symbol Map Generation & Resolution Logic Survey (R3)

### 2.1 Existing Script: `scripts/gate2_build_symbol_map.py`
The current builder script has the following structure:
- **Inputs**: `data/index_events.parquet` (9,121 rows, 1,448 unique scrips), `data/raw_reference/EQUITY_L.csv` (2,583 listed equities).
- **Matching flow**:
  1. Exact match against `eq_exact` dictionary built from `EQUITY_L.csv`. Assigns `status: "auto"`, `confidence: "high"`, `resolution_method: "equity_l_exact"`.
  2. Substring/exact match against `KNOWN_CORPORATE_RENAMES`. Assigns `status: "proposed"`, `confidence: "high"`, `resolution_method: "manual"`.
  3. Token matching against `eq_entries`: computes Jaccard token overlap after removing stopwords (`ltd`, `co`, `corp`, `pvt`, `inc`, `india`). If score >= 0.70 -> high; >= 0.50 -> medium; >= 0.35 -> low; all assigned `status: "proposed"`, `resolution_method: "manual"`.
  4. If score < 0.35: assigns empty symbol/isin, `resolution_method: "unresolved"`, `confidence: "low"`, `status: "proposed"`. Note: It improperly set `status: "proposed"` instead of `"unresolved"`.
- **Shortcomings identified**:
  - No price cache integration (no `bars_expected`, `bars_present`, `coverage_pct`).
  - No verification of listing dates (S1).
  - Susceptible to EQUITY_L duplicate names ("last row wins" overwriting DVR vs ordinary shares) (S2).
  - No verification that candidate ISIN exists in EQUITY_L (S3).
  - No detection of concurrent alias collisions (S4).
  - No handling of predecessor suffixes (S5).
  - Weak token matching produces spurious collisions (e.g. Bank of Punjab -> Bank of India; Dewan Housing -> HDFC) without first-token checking (S6).
  - Membership window calculation only took `min` and `max` of event dates, truncating unremoved seed members to 1998-08-01.

### 2.2 Inventory of `KNOWN_CORPORATE_RENAMES`
`KNOWN_CORPORATE_RENAMES` contains 37 entries in `scripts/gate2_build_symbol_map.py`:

| Normalized Scrip Name | Candidate Symbol | Candidate ISIN | Real World Corporate Event |
|---|---|---|---|
| `infosys technologies ltd` | INFY | INE009A01021 | Renamed to Infosys Ltd |
| `infosys technologies limited` | INFY | INE009A01021 | Renamed to Infosys Ltd |
| `hero honda motors ltd` | HEROMOTOCO | INE158A01026 | Renamed to Hero MotoCorp Ltd |
| `hero honda motors limited` | HEROMOTOCO | INE158A01026 | Renamed to Hero MotoCorp Ltd |
| `hindustan lever ltd` | HINDUNILVR | INE030A01027 | Renamed to Hindustan Unilever Ltd |
| `hindustan lever limited` | HINDUNILVR | INE030A01027 | Renamed to Hindustan Unilever Ltd |
| `tata iron and steel co ltd` | TATASTEEL | INE081A01012 | Renamed to Tata Steel Ltd |
| `tata iron and steel company ltd` | TATASTEEL | INE081A01012 | Renamed to Tata Steel Ltd |
| `tata tea ltd` | TATACONSUM | INE192A01025 | Renamed to Tata Consumer Products Ltd |
| `tata tea limited` | TATACONSUM | INE192A01025 | Renamed to Tata Consumer Products Ltd |
| `associated cement companies ltd` | ACC | INE012A01025 | Renamed to ACC Ltd |
| `the associated cement companies ltd` | ACC | INE012A01025 | Renamed to ACC Ltd |
| `east india hotels ltd` | EIHOTEL | INE230A01023 | Renamed to EIH Ltd |
| `glaxo india ltd` | GLAXO | INE159A01016 | Merged/Renamed to GlaxoSmithKline Pharma |
| `glaxo smithkline pharmaceuticals ltd` | GLAXO | INE159A01016 | Variant naming |
| `uti bank ltd` | AXISBANK | INE238A01034 | Renamed to Axis Bank Ltd |
| `ranbaxy laboratories ltd` | SUNPHARMA | INE044A01036 | Merged into Sun Pharma (ISIN swapped) |
| `satyam computer services ltd` | TECHM | INE669C01036 | Acquired by Tech Mahindra |
| `l and t ltd` | LT | INE018A01030 | Variant naming |
| `larsen and toubro ltd` | LT | INE018A01030 | Variant naming |
| `madras refineries ltd` | CHENNPETRO | INE178A01016 | Renamed to Chennai Petroleum Corp |
| `reliance capital ltd` | RELCAPITAL | INE013A01015 | Delisted/Insolvent (ISIN not in EQUITY_L) |
| `avenue supermarts ltd` | DMART | INE192R01011 | In EQUITY_L (Avenue Supermarts Limited) |
| `max financial services ltd` | MFSL | INE180A01020 | In EQUITY_L (Max Financial Services Limited) |
| `berger paints india ltd` | BERGEPAINT | INE463A01038 | In EQUITY_L (Berger Paints India Limited) |
| `jaiprakash associates ltd` | JPASSOCIAT | INE451D01028 | In EQUITY_L (Jaiprakash Associates Limited) |
| `national aluminium co ltd` | NATIONALUM | INE139A01034 | In EQUITY_L (National Aluminium Company Limited) |
| `adani power ltd` | ADANIPOWER | INE814H01011 | In EQUITY_L (Adani Power Limited) |
| `dlf ltd` | DLF | INE271C01023 | In EQUITY_L (DLF Limited) |
| `indian hotels co ltd` | INDHOTEL | INE053A01032 | In EQUITY_L (The Indian Hotels Company Limited) |
| `nhpc ltd` | NHPC | INE848E01016 | In EQUITY_L (NHPC Limited) |
| `unitech ltd` | UNITECH | INE694A01020 | In EQUITY_L (Unitech Limited) |
| `voltas ltd` | VOLTAS | INE226A01021 | In EQUITY_L (Voltas Limited) |
| `mahindra lifespace developers ltd` | MAHLIFE | INE813A01018 | In EQUITY_L (Mahindra Lifespace Developers Limited) |
| `container corporation of india ltd` | CONCOR | INE111A01025 | In EQUITY_L (Container Corporation of India Limited) |
| `state bank of india` | SBIN | INE062A01020 | In EQUITY_L (State Bank of India) |

**Required Changes for R3**:
1. When matched via `KNOWN_CORPORATE_RENAMES`, rows MUST NOT receive `confidence: "high"`. They must receive:
   - `resolution_method: "agent_memory"`
   - `confidence: "low"`
   - `status: "proposed"`
   - `flags`: must include `unsourced`
   - `evidence_source`: `"agent_memory"`
2. They can NEVER be auto-resolved.

### 2.3 Archiving v1
- Current file: `data/symbol_map.parquet`
- Size: 49,083 bytes, 1,448 rows
- SHA-256: `ae982c3e1c22bdcafcf9bec6de28385d7dd3b29d3392ad39935f4e1b0c28fc58`
- Archiving step: Copy to `data/symbol_map_v1.parquet` before running the rebuild.

### 2.4 Rebuilt Schema Specification
The rebuilt `data/symbol_map.parquet` must contain 21 columns:

| Column Name | Dtype | Nullable | Description & Expected Values |
|---|---|---|---|
| `scrip_name` | string | No | Raw company name from index events |
| `symbol` | string | No | Candidate or resolved NSE ticker symbol (empty string if unresolved) |
| `isin` | string | No | Candidate or resolved ISIN (empty string if unresolved) |
| `first_seen` | date / string | No | Earliest event date across all indices (`YYYY-MM-DD`) |
| `last_seen` | date / string | No | Latest membership end date across all indices (`YYYY-MM-DD`) |
| `resolution_method` | string | No | One of: `equity_l_exact`, `token_match`, `agent_memory`, `user_override`, `unresolved` |
| `confidence` | string | No | `high`, `medium`, `low`, or `none` |
| `status` | string | No | One of: `auto`, `proposed`, `unresolved`, `approved`, `rejected` |
| `eq_name` | string | No | `NAME OF COMPANY` from EQUITY_L (empty string if not matched) |
| `eq_series` | string | No | `SERIES` from EQUITY_L (e.g. `EQ`, empty string if not matched) |
| `eq_listing_date` | date / string | Yes/No | `DATE OF LISTING` from EQUITY_L (`YYYY-MM-DD`, empty if not matched) |
| `isin_in_equity_l` | boolean | No | `True` if candidate ISIN is in EQUITY_L, `False` otherwise |
| `name_similarity` | float | No | Token overlap score [0.0, 1.0] (1.0 for exact normalized match) |
| `first_token_match` | boolean | No | `True` if first word of normalized scrip == first word of normalized eq_name |
| `price_first_bar` | date / string | Yes/No | Earliest date of available price bar in price cache (empty if none) |
| `price_last_bar` | date / string | Yes/No | Latest date of available price bar in price cache (empty if none) |
| `bars_expected` | int | No | Count of trading calendar days within unioned membership window |
| `bars_present` | int | No | Count of candidate symbol price bars within unioned membership window |
| `coverage_pct` | float | No | `bars_present / bars_expected * 100` (0.0 if bars_expected == 0) |
| `flags` | string | No | Comma-separated list of triggered screen flags (empty string if none) |
| `evidence_source` | string | No | Source citation (e.g. `EQUITY_L.csv`, `agent_memory`, `none`) |

### 2.5 Detailed Logic for Evidence Screens S1–S6

#### Unioned Membership Window Definition
For each `scrip_name`:
1. Find all appearances in `data/index_events.parquet`.
2. Group events by index:
   - `start_date`: date of the first `IN` event (or minimum event date if orphan OUT).
   - `end_date`: date of the last `OUT` event. If the last event is an `IN` (stock was never excluded), set `end_date = covered_end[index]`.
   - Index `covered_end` dates:
     * `NIFTY500`: `2020-09-14`
     * `NIFTY50`, `NIFTY100`, `NIFTY200`, `NIFTYNEXT50`: `2020-07-31`
     * `NIFTYMIDCAP100`, `NIFTYSMALLCAP100`: `2020-06-26`
     * Sectoral / others: maximum effective date in that index.
3. Union the intervals across all indices: `window_start = min(start_date)`, `window_end = max(end_date)`.
4. `bars_expected` = number of trading days in the official trading calendar falling in `[window_start, window_end]`.
5. `bars_present` = number of price bars for candidate `symbol` in `data/price_cache_export.parquet` falling in `[window_start, window_end]`.
6. `coverage_pct` = `(bars_present / bars_expected * 100)` if `bars_expected > 0` else 0.0.

#### Screen S1: `listing_after_first_seen`
- **Condition**: `eq_listing_date > window_start + timedelta(days=30)`.
- **Finding**: 256 scrips trigger this screen.
- **Rule**: Demotes to `proposed`, **EXCEPT** if candidate meets all other auto conditions (exact normalized name match, unique EQUITY_L candidate, ISIN in EQUITY_L, no S4/S5) **AND** `coverage_pct >= 90%`.

#### Screen S2: `duplicate_name_collision`
- **Condition**: Multiple rows in `EQUITY_L.csv` share the same normalized name.
- **Finding**: 3 pairs (6 rows) collide in `EQUITY_L.csv`:
  1. `FEL` (Future Enterprises Limited, INE623B01027, BZ) vs `FELDVR` (Future Enterprises Limited, IN9623B01058, BZ)
  2. `GATECH` (GACM Technologies Limited, INE224E01028, BE) vs `GATECHDVR` (GACM Technologies Limited, INE224E01036, BE)
  3. `JISLDVREQS` (Jain Irrigation Systems Limited, IN9175A01010, EQ) vs `JISLJALEQS` (Jain Irrigation Systems Limited, INE175A01038, EQ)
- **Rule**: Never keep "last row wins". When a scrip matches one of these colliding normalized names, flag with `duplicate_name_collision`. It can NEVER be auto-resolved; it must be demoted to `proposed`.

#### Screen S3: `isin_unverified`
- **Condition**: Candidate ISIN is not present in `EQUITY_L.csv` and `evidence_source` does not cite an official external document.
- **Finding**: Applies to unlisted/delisted entities (e.g. `Reliance Capital Ltd.` -> `RELCAPITAL`, ISIN `INE013A01015`, which is absent from EQUITY_L) or candidates matched without ISIN verification.
- **Rule**: Flag with `isin_unverified`. Demotes to `proposed`.

#### Screen S4: `concurrent_alias_collision`
- **Condition**: Two distinct `scrip_name`s resolve to the same candidate ISIN and co-exist in the same index concurrently.
- **Finding**: 101 scrips trigger S4 under the previous map (e.g. `ABB India Ltd.` & `ABB Ltd.`; `Ashok Leyland Finance Ltd.` & `Ashok Leyland Ltd.`; `Bank of India` & `Bank of Punjab Ltd.`).
- **Rule**: Trace active membership day-by-day in each index. If at any date, two different scrips active in that index share the same candidate ISIN, flag both with `concurrent_alias_collision`. Can NEVER be auto.

#### Screen S5: `predecessor_marker`
- **Condition**: `scrip_name` contains predecessor / suspension / merger / delisting tokens.
- **Implementation Requirement**: Must use regex word boundaries:  
  `pattern = re.compile(r'\b(old|sus|suspended|erstwhile|merge[a-z]*|arrangement|delisted)\b', re.IGNORECASE)`
- **Finding**: 64 scrip names match this regex in `index_events.parquet`. Without word boundaries, names like "Holdings" and "Golden" would trigger false positives.
- **Rule**: Flag with `predecessor_marker`. Can NEVER be auto.

#### Screen S6: `first_token_mismatch`
- **Condition**: First token of normalized `scrip_name` != first token of normalized candidate `eq_name`.
- **Finding**: Catches spurious token matches (e.g. `Dewan Housing Finance Corporation Ltd.` matching `Housing Development Finance Corporation Ltd.` / HDFC; `Corporation Bank` matching `Axis Bank Ltd.`; `Bongaigaon Refinery` matching `Mangalore Refinery`).
- **Rule**: Flag with `first_token_mismatch`. Demotes to `proposed`.

### 2.6 Auto Rule Specification & Demotion Logic
A candidate is assigned `status: "auto"` if and only if:
1. `resolution_method == "equity_l_exact"` (exact normalized name match).
2. Unique candidate in EQUITY_L (no S2 flag `duplicate_name_collision`).
3. `isin_in_equity_l == True` (no S3 flag `isin_unverified`).
4. No S4 flag (`concurrent_alias_collision`).
5. No S5 flag (`predecessor_marker`).
6. `coverage_pct >= 90.0%` (if S1 `listing_after_first_seen` is present, it may stay `auto` if `coverage_pct >= 90.0%`; if `coverage_pct < 90.0%`, it is demoted).

If a candidate exists but fails any auto requirement, it is demoted to `status: "proposed"`.  
If no candidate exists, `status: "unresolved"`.

The builder script must record and report:
- Total exact matches.
- Demotion count by flag:
  * Demoted by `coverage_pct < 90`
  * Demoted by S1 (`listing_after_first_seen` with coverage < 90)
  * Demoted by S2 (`duplicate_name_collision`)
  * Demoted by S3 (`isin_unverified`)
  * Demoted by S4 (`concurrent_alias_collision`)
  * Demoted by S5 (`predecessor_marker`)
  * Demoted by S6 (`first_token_mismatch`)
  * Demoted by method (`agent_memory` / `token_match`)
- Coverage tiers:
  * Tier `>= 90%`
  * Tier `30% – 90%`
  * Tier `< 30%`
  * Tier `N/A` (unresolved / missing symbol)

---

## 3. Review Tooling & Refusal Hardening Survey (R4)

### 3.1 Review Generation: `scripts/review_symbol_map.py`
**Current Behavior**: Reads `data/symbol_map.parquet`, filters `status == "proposed"`, groups into 3 tiers, and writes `data/symbol_map_review_<tier>.csv`. Leaves `unresolved` mixed in.

**Required Changes**:
1. Split `unresolved` entries (`status == "unresolved"`):
   - Export to `data/symbol_map_unresolved.csv`.
   - Columns: `scrip_name, first_seen, last_seen, bars_expected, evidence_source, flags`.
2. Export `proposed` entries (`status == "proposed"`):
   - Export to `data/symbol_map_review.csv` (and/or tier-based CSVs `data/symbol_map_review_<tier>.csv`).
   - Include all 21 evidence columns from `symbol_map.parquet`.
   - Include editable columns for human review:
     * `review_action`: defaults to `"proposed"`. Editable to `"approved"`, `"rejected"`, or `"override"`.
     * `override_symbol`: empty by default.
     * `override_isin`: empty by default.
     * `override_evidence`: empty by default.
     * `approval_note`: empty by default. **Mandatory** if row has flags!
   - Keep `status` column read-only (reflecting original status).

### 3.2 Review Application & Refusal Hardening: `scripts/apply_symbol_map_review.py <csv>`
**Current Behavior**: Checks if status value is in `{"approved", "rejected", "proposed", "auto"}`. Directly updates `symbol_map.parquet`. No refusal enforcement for missing notes, empty symbols, or key mismatches. No backup or audit trail.

**Required Refusal Paths & Hardening**:

1. **Reads `review_action` Only**:
   - The tool must inspect `review_action` column exclusively. Any user modifications to `status` column must be ignored.
2. **Refusal Path 1: Invalid Action**:
   - Allowed values: `{"approved", "rejected", "proposed", "override"}`.
   - If any row has a value outside this set (e.g. typos like `approve`, `accept`, `yes`, `valid`), REFUSE and abort with exit code 2.
3. **Refusal Path 2: Refuse Auto**:
   - If any row attempts to set `review_action == "auto"`, REFUSE with exit code 2. Only the automated pipeline can set `auto`.
4. **Refusal Path 3: Refuse Empty Symbol / ISIN on Approval**:
   - If `review_action == "approved"` (or `"override"`), the effective candidate (`symbol` or `override_symbol`, and `isin` or `override_isin`) must not be empty, null, or whitespace.
   - Approving an empty symbol/ISIN must REFUSE with exit code 2.
5. **Refusal Path 4: Refuse Flagged Row without `approval_note`**:
   - If a row has non-empty `flags` AND `review_action == "approved"`, it MUST have a non-empty `approval_note` explaining why the reviewer accepts the flagged candidate.
   - If `approval_note` is empty, whitespace, or NaN, REFUSE with exit code 2.
6. **Refusal Path 5: Key Match Verification**:
   - For every row in the review CSV, verify that `(scrip_name, symbol, isin)` matches the existing entry in `data/symbol_map.parquet`.
   - If `scrip_name` does not exist or candidate keys have been altered without using override columns, REFUSE with exit code 2.
7. **Safety & Audit Trail**:
   - **Backup**: Before modifying `data/symbol_map.parquet`, create a backup copy: `data/symbol_map_backup_<timestamp>.parquet`.
   - **Audit Trail**: Append applied changes to `data/symbol_map_changes.parquet` with schema:
     `timestamp, scrip_name, old_symbol, new_symbol, old_isin, new_isin, old_status, new_status, old_resolution_method, new_resolution_method, flags, approval_note, review_source_csv`.
   - If `data/symbol_map_changes.parquet` does not exist, create it; if it exists, append to it.

### 3.3 Test Suite for Refusal Paths
To fulfill R4 ("Test all refusal paths with raw console output"), test CSVs covering all refusal conditions must be prepared and executed against `scripts/apply_symbol_map_review.py`:
- `test_refuse_invalid_action.csv` (`review_action: "approve"`) -> Error 2.
- `test_refuse_auto.csv` (`review_action: "auto"`) -> Error 2.
- `test_refuse_empty_symbol.csv` (`review_action: "approved"`, empty symbol) -> Error 2.
- `test_refuse_flagged_no_note.csv` (`review_action: "approved"`, flags present, empty note) -> Error 2.
- `test_refuse_key_mismatch.csv` (`scrip_name` or candidate keys altered) -> Error 2.
- `test_valid_approval.csv` (flagged row approved with note, non-flagged row approved, override row approved) -> Successfully updates map, creates backup, appends to `symbol_map_changes.parquet`.

---

## 4. Canary Regression Test Suite Survey (R5)

### 4.1 Requirement Specification
Requirement R5 mandates creating `data/verification/canaries_2b.csv` with all 15+ canonical edge cases.  
Every canary case must:
- Have status NOT `auto` (i.e. `proposed` or `unresolved`).
- Be flagged with expected reasons.

### 4.2 Verified 18 Canonical Edge Cases
All 18 scrip names below have been confirmed present in `data/index_events.parquet`:

| # | Scrip Name in `index_events.parquet` | Expected Status | Expected Flags | Resolution Method | Category / Description |
|---|---|---|---|---|---|
| 1 | `Tube Investments of India Ltd.-Old` | `proposed` | `predecessor_marker` | `token_match` | S5 Predecessor Marker (`-Old`) |
| 2 | `Wockhardt Ltd. (old)` | `proposed` | `predecessor_marker` | `token_match` | S5 Predecessor Marker (`(old)`) |
| 3 | `National Aluminium Co. Ltd. (Old)` | `proposed` | `predecessor_marker` | `token_match` | S5 Predecessor Marker (`(Old)`) |
| 4 | `Larsen & Toubro Ltd.-Sus` | `proposed` | `predecessor_marker` | `token_match` | S5 Suspended Line Marker (`-Sus`) |
| 5 | `Aptech Ltd. (Erstwhile)` | `proposed` | `predecessor_marker` | `token_match` | S5 Erstwhile Line Marker (`(Erstwhile)`) |
| 6 | `Reliance Petroleum Ltd.- Merge` | `proposed` | `predecessor_marker` | `token_match` | S5 Merger Marker (`- Merge`) |
| 7 | `Future Enterprises Ltd.` | `proposed` | `duplicate_name_collision` | `equity_l_exact` | S2 EQUITY_L Duplicate Name (`FEL` vs `FELDVR`) |
| 8 | `Jain Irrigation Systems Ltd.` | `proposed` | `duplicate_name_collision` | `equity_l_exact` | S2 EQUITY_L Duplicate Name (`JISLDVREQS` vs `JISLJALEQS`) |
| 9 | `Jain Irrigation Systems Ltd. (Old)` | `proposed` | `duplicate_name_collision,predecessor_marker` | `equity_l_exact` | S2 Duplicate Name + S5 Predecessor Marker |
| 10 | `Hero Honda Motors Limited` | `proposed` | `unsourced` | `agent_memory` | Corporate Rename (`HEROMOTOCO`, agent memory) |
| 11 | `Infosys Technologies Limited` | `proposed` | `unsourced` | `agent_memory` | Corporate Rename (`INFY`, agent memory) |
| 12 | `Satyam Computer Services Ltd.` | `proposed` | `unsourced` | `agent_memory` | Corporate Acquisition/Rename (`TECHM`, agent memory) |
| 13 | `UTI Bank Ltd.` | `proposed` | `unsourced` | `agent_memory` | Corporate Rename (`AXISBANK`, agent memory) |
| 14 | `Ranbaxy Laboratories Ltd.` | `proposed` | `unsourced` | `agent_memory` | Corporate Acquisition (`SUNPHARMA`, agent memory) |
| 15 | `Dewan Housing Finance Corporation Ltd.` | `proposed` | `concurrent_alias_collision,first_token_mismatch` | `token_match` | S4 Concurrent Alias Collision + S6 Token Mismatch |
| 16 | `Larsen & Toubro Infotech Ltd.` | `proposed` | `concurrent_alias_collision` | `token_match` | S4 Concurrent Alias Collision (`LT` subsidiary) |
| 17 | `Reliance Capital Ltd.` | `proposed` | `isin_unverified` | `agent_memory` | S3 ISIN Unverified (`RELCAPITAL` delisted) |
| 18 | `20th Century Finance Corporation Ltd.` | `unresolved` | `none` (or `unresolved`) | `unresolved` | Historical delisted NBFC (no candidate in EQUITY_L) |

### 4.3 Structure of `data/verification/canaries_2b.csv`
Columns:
`scrip_name,expected_status,expected_flags,category,rationale`

---

## 5. Implementation Blueprint & Recommendations

### 5.1 Execution Order
1. **Archive v1**:
   Run `cp data/symbol_map.parquet data/symbol_map_v1.parquet` and record SHA-256 (`ae982c3e1c22bdcafcf9bec6de28385d7dd3b29d3392ad39935f4e1b0c28fc58`).
2. **Rebuild `scripts/gate2_build_symbol_map.py`**:
   - Implement the 21-column schema.
   - Implement S1 through S6 screens.
   - Implement unioned membership window logic with `covered_end` clamping for unremoved scrips.
   - Integrate trading calendar and price cache bars (`bars_expected`, `bars_present`, `coverage_pct`).
   - Implement the strict auto rule and demotion tracking.
   - Output coverage tiers and per-index summary.
3. **Rebuild `scripts/review_symbol_map.py`**:
   - Split `status == "unresolved"` to `data/symbol_map_unresolved.csv`.
   - Write `status == "proposed"` to `data/symbol_map_review_<tier>.csv` with evidence and editable override columns.
4. **Harden `scripts/apply_symbol_map_review.py`**:
   - Implement all 5 refusal checks.
   - Implement automatic backup creation (`data/symbol_map_backup_<timestamp>.parquet`).
   - Implement audit trail appending (`data/symbol_map_changes.parquet`).
   - Execute all refusal test cases and capture console output.
5. **Generate and Run Canary Tests**:
   - Write `data/verification/canaries_2b.csv` with all 18 verified edge cases.
   - Run verification script to assert that none of the 18 canaries are `auto`, and all match their expected flags/statuses.

### 5.2 Pitfalls & Mitigations
- **Substring Matching in S5**: Never use `in s.lower()`. Always use regex word boundaries `\b(old|sus|suspended|erstwhile|merge[a-z]*|arrangement|delisted)\b` to prevent matching "Holdings" or "Golden".
- **EQUITY_L Overwrite in S2**: Detect duplicate normalized names during reference loading and map them to a collision set instead of letting the last row win.
- **Window Calculation for Seed Stocks**: When a stock has no `OUT` event, do not clamp the window to the `IN` event date; use the index `covered_end`.
- **Calendar Basis for `bars_expected`**: `bars_expected` must count official trading days from the trading calendar within the window, NOT raw calendar days, so that actively traded stocks can reach `coverage_pct >= 90%`.

---
*Report compiled by Explorer 3 (Symbol Map and Review Tooling Surveyor) on 2026-09-24.*
