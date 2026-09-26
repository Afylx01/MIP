# Plan: Phase 5.5 - Gate 2b: Symbol Map Evidence Hardening

## Objective
Rebuild the Phase 5.5 index membership symbol map with cryptographic and price-bar evidence hardening (S1–S6 checks), repair Gate 1 anomalies, fix review tooling with strict refusal verification, run canary regressions, and recompute the Gate 2 report for NIFTY500 under HALT-1b.

## Milestones & Execution Plan

### Phase 0: Survey & Discovery (Explorers 1, 2, 3)
- Survey codebase, existing scripts, data files, price data directory (`/storage/emulated/0/MIP1_Scanner/data/`), Gate 0, 1, 2 scripts and outputs.
- Aggregate survey reports into `PROJECT.md` Feature Inventory & Code Layout.

### Milestone 0: R0 - Price Data Inventory & Safe Loading (HALT on failure)
- Inventory local price files in `/storage/emulated/0/MIP1_Scanner/data/` (path, size, format, mtime, bhavcopy presence).
- Load price cache with clean method (matching pandas / export) to create `data/price_cache_export.parquet`.
- Print and record source row count vs exported row count (match), column names and dtypes, SHA-256 of export.
- Report unique symbols, date range, symbols whose last bar is before max date, delisted names status.
- Derive official trading calendar from exported NSEI index bars (first date, last date, day count, source).

### Milestone 1: R1 - Gate 1 Repairs
- Re-run Gate 1(c) calendar validation against ambiguous rows inside calendar date range. Report day-first vs month-first trading-day hit rates on restricted set + count of rows outside calendar range.
- Inspect the 2 rows dated 2017-09-05 in `Nifty Dividend Opportunities 50` (Reliance Capital OUT, National Aluminium IN) deduplicated rather than quarantined. Print cell types (ctype) and neighbouring rows. Quarantine consistently if suspect datetime class; re-run dedupe count. Print before/after.
- Print day-first non-monotonic step count after quarantine (expected 0 for all sheets).
- Print all 10 deduplicated rows and all 10 quarantined rows in full.

### Milestone 2: R2 - Gate 0 Restatement
- Extract text from cached `nifty_replacement_circular_sep_2020.pdf` and cached rebalancing schedule HTML.
- Print up to 40 relevant lines; restate Gate 0 finding: "post-2020-09 bulletin availability NOT ESTABLISHED; deferred to Phase 5.6".

### Milestone 3: R3 - Symbol Map Rebuild with Evidence (S1–S6 Checks)
- Archive existing map as `data/symbol_map_v1.parquet` (report SHA-256).
- Remove hardcoded knowledge (`KNOWN_CORPORATE_RENAMES` only as `agent_memory`, `low` confidence, flagged `unsourced`).
- Statuses: `auto`, `proposed`, `unresolved`, `approved`, `rejected` (no candidate -> `unresolved`).
- `resolution_method`: `equity_l_exact`, `token_match`, `agent_memory`, `user_override`, `unresolved`.
- New columns: `eq_name, eq_series, eq_listing_date, isin_in_equity_l, name_similarity, first_token_match, price_first_bar, price_last_bar, bars_expected, bars_present, coverage_pct, flags, evidence_source`.
- Implement S1–S6 screens:
  - S1: `listing_after_first_seen`
  - S2: `duplicate_name_collision`
  - S3: `isin_unverified`
  - S4: `concurrent_alias_collision`
  - S5: `predecessor_marker`
  - S6: `first_token_mismatch`
- Auto rule implementation + demotion counts by flag + coverage tiers report (`>=90`, `30-90`, `<30`, `n/a`).

### Milestone 4: R4 - Review Tooling Fixes & Refusal Hardening
- `scripts/review_symbol_map.py`: proposed rows -> CSV; unresolved -> `data/symbol_map_unresolved.csv`.
- `scripts/apply_symbol_map_review.py <csv>`: strict refusal checks, key match verification, backup map, append to `data/symbol_map_changes.parquet`.
- Test all refusal paths with raw console output.

### Milestone 5: R5 - Canary Regression Test
- Create `data/verification/canaries_2b.csv` with 15+ canonical edge cases.
- Verify all are not auto and flagged with expected reasons.

### Milestone 6: R6 - Gate 2 Report Recomputation & Verification (HALT-1b)
- Recompute Gate 2 report for NIFTY500 only. Other 6 indices show "event log only, not reconstructable".
- Report name-level resolved fractions and price-covered fractions (`coverage_pct >= 90`). Zero members prints N/A.
- Add survivorship disclosure line.
- Produce `gate_2b_verification.md` with exact commands, raw outputs, and 20 sample rows per status.
- Halt at HALT-1b.
