# Project: Phase 5.5 - Gate 2b: Symbol Map Evidence Hardening

## Architecture
- **Data Ingestion & Price Inventory**: Validates and safely loads historical price data from `/storage/emulated/0/MIP1_Scanner/data/`, generates `data/price_cache_export.parquet`, and derives official trading calendar from exported NSEI index bars.
- **Gate 1 Ingestion & Repairs**: Verifies date format (day-first vs month-first) against trading calendar restricted set, repairs 2017-09-05 `Nifty Dividend Opportunities 50` anomaly by quarantining suspect datetime duplicate rows into `data/quarantine_gate1.parquet`, and verifies monotonicity.
- **Gate 0 Restatement**: Extracts text from cached September 2020 circular PDF and rebalancing schedule HTML, confirming that post-2020-09 bulletin availability is not established.
- **Evidence-Hardened Symbol Map**: Rebuilds `data/symbol_map.parquet` (after archiving v1 as `data/symbol_map_v1.parquet`) with S1–S6 screens, corporate rename demotions to `agent_memory`/`unsourced`, price-bar coverage checks, and auto/proposed/unresolved classifications.
- **Review Tooling & Refusal Enforcement**: Generates review CSVs for proposed/unresolved rows; provides `apply_symbol_map_review.py` with 5 strict refusal checks, compound key matching, and append-only auditing in `data/symbol_map_changes.parquet`.
- **Canary Regression**: Evaluates 18 canonical edge cases in `data/verification/canaries_2b.csv` ensuring none resolve to auto.
- **Gate 2 Scoped Reconstitution & Reporting**: Recomputes Gate 2 membership snapshots, resolved fractions, price coverage, and Gates B–F for **NIFTY500 ONLY**, reporting other 6 indices as event-log only with survivorship disclosure note under HALT-1b.

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | R0 Price Files Inventory | Inventory all files in `/storage/emulated/0/MIP1_Scanner/data/` (path, size, format, mtime; state Bhavcopy presence) | M0 | ORIGINAL_REQUEST §R0 |
| 2 | R0 Safe Loading / Export | Safe loading of stock price cache to `data/price_cache_export.parquet` (source vs export row count match, dtypes, SHA-256) | M0 | ORIGINAL_REQUEST §R0 |
| 3 | R0 Price Statistics & Coverage | Print unique symbols, date range, delisted/suspended count before max date | M0 | ORIGINAL_REQUEST §R0 |
| 4 | R0 Official Trading Calendar | Derive trading calendar from exported NSEI index bars (first date, last date, day count, source) | M0 | ORIGINAL_REQUEST §R0 |
| 5 | R1 Gate 1(c) Calendar Validation | Re-run calendar validation on restricted set inside calendar range (day-first vs month-first hit rates, rows outside range) | M1 | ORIGINAL_REQUEST §R1 |
| 6 | R1 2017-09-05 Repair | Inspect rows 127–130 in Nifty Dividend Opportunities 50; quarantine consistently; re-run dedupe count before/after | M1 | ORIGINAL_REQUEST §R1 |
| 7 | R1 Monotonic Step Verification | Verify day-first non-monotonic step count after quarantine (expected 0 across all 37 sheets) | M1 | ORIGINAL_REQUEST §R1 |
| 8 | R1 Row Print Artifacts | Print all deduplicated rows and all quarantined rows in full | M1 | ORIGINAL_REQUEST §R1 |
| 9 | R2 Gate 0 Circular Text Extraction | Extract text from `nifty_replacement_circular_sep_2020.pdf` and rebalancing schedule HTML (print up to 40 lines) | M2 | ORIGINAL_REQUEST §R2 |
| 10 | R2 Gate 0 Restatement | Restate Gate 0 finding: "post-2020-09 bulletin availability NOT ESTABLISHED; deferred to Phase 5.6" | M2 | ORIGINAL_REQUEST §R2 |
| 11 | R3 Symbol Map v1 Archival | Archive existing `data/symbol_map.parquet` to `data/symbol_map_v1.parquet` and report SHA-256 | M3 | ORIGINAL_REQUEST §R3 |
| 12 | R3 Corporate Renames Refactor | Remove hardcoding; map `KNOWN_CORPORATE_RENAMES` to `agent_memory`, `low` confidence, flagged `unsourced` | M3 | ORIGINAL_REQUEST §R3 |
| 13 | R3 Symbol Map Schema & Statuses | Add required columns and statuses (`auto`, `proposed`, `unresolved`, `approved`, `rejected`) and resolution methods | M3 | ORIGINAL_REQUEST §R3 |
| 14 | R3 S1–S6 Evidence Screens | Implement S1 (listing date), S2 (EQUITY_L duplicate names), S3 (unverified ISIN), S4 (concurrent alias), S5 (predecessor marker), S6 (first token mismatch) | M3 | ORIGINAL_REQUEST §R3 |
| 15 | R3 Auto Rule & Demotions | Apply auto rule (exact match + unique candidate + ISIN verified + no S1/S4/S5 + coverage >= 90%); print demotion counts & coverage tiers | M3 | ORIGINAL_REQUEST §R3 |
| 16 | R4 Review Export Tooling | `scripts/review_symbol_map.py`: proposed -> CSV, unresolved -> `data/symbol_map_unresolved.csv` | M4 | ORIGINAL_REQUEST §R4 |
| 17 | R4 Review Apply & Refusal Hardening | `scripts/apply_symbol_map_review.py`: 5 refusal paths, key matching, backup, audit trail in `symbol_map_changes.parquet` | M4 | ORIGINAL_REQUEST §R4 |
| 18 | R4 Refusal Test Suite | Execute tests for all refusal paths with raw console output | M4 | ORIGINAL_REQUEST §R4 |
| 19 | R5 Canary Regression Suite | Create `data/verification/canaries_2b.csv` with 18 canonical edge cases, verifying all not auto and properly flagged | M5 | ORIGINAL_REQUEST §R5 |
| 20 | R6 Gate 2 Report Recomputation | Recompute Gate 2 report for NIFTY500 ONLY; other six indices show "event log only, not reconstructable" | M6 | ORIGINAL_REQUEST §R6 |
| 21 | R6 Resolved & Price Coverage Fractions | Report name-level resolved fractions and price-covered fractions (>= 90%); zero members prints N/A | M6 | ORIGINAL_REQUEST §R6 |
| 22 | R6 Survivorship Disclosure & Artifact | Add survivorship disclosure line; generate `gate_2b_verification.md` with exact commands, raw outputs, 20 sample rows; HALT-1b | M6 | ORIGINAL_REQUEST §R6 |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M0 | R0 Price Data Inventory & Safe Loading | Inventory price files in `/storage/emulated/0/MIP1_Scanner/data/`, safe load/export `data/price_cache_export.parquet`, trading calendar | none | PLANNED |
| M1 | R1 Gate 1 Repairs | Calendar validation on restricted set, 2017-09-05 Dividend Opportunities 50 quarantine, monotonic checks | M0 | PLANNED |
| M2 | R2 Gate 0 Restatement | Text extraction from PDF & HTML, formal restatement of post-2020-09 bulletin availability | none | PLANNED |
| M3 | R3 Symbol Map Rebuild with Evidence | Archive v1, S1–S6 screens, corporate rename demotion, auto rule, coverage tiers | M0, M1 | PLANNED |
| M4 | R4 Review Tooling Fixes & Refusals | `review_symbol_map.py`, `apply_symbol_map_review.py`, refusal test execution | M3 | PLANNED |
| M5 | R5 Canary Regression Test | `data/verification/canaries_2b.csv`, 18 canonical edge cases verified | M3 | PLANNED |
| M6 | R6 Gate 2 Report Recomputation & HALT-1b | Recompute NIFTY500 snapshots & fractions, survivorship note, `gate_2b_verification.md` | M1, M2, M3, M4, M5 | PLANNED |

## Interface Contracts
### Price Cache Export ↔ Symbol Map Rebuild
- **Artifact**: `data/price_cache_export.parquet`
- **Schema**: `symbol` (str), `date` (date/datetime), `open` (float), `high` (float), `low` (float), `close` (float), `volume` (int/float)
- **Official Calendar**: `2007-09-17` to `2026-08-31` (4,649 trading days)

### Symbol Map ↔ Review Tooling
- **Artifact**: `data/symbol_map.parquet`
- **Composite Key**: `(scrip_name, symbol, isin)`
- **Statuses**: `auto`, `proposed`, `unresolved`, `approved`, `rejected`
- **Resolution Methods**: `equity_l_exact`, `token_match`, `agent_memory`, `user_override`, `unresolved`

### Gate 1 Quarantined Events ↔ Index Events
- **Artifacts**: `data/index_events.parquet` (9,121 rows), `data/quarantine_gate1.parquet` (12 rows after repairing 2017-09-05)

## Code Layout
- `data/price_cache_export.parquet` — Clean parquet price cache
- `data/symbol_map_v1.parquet` — Archived v1 symbol map
- `data/symbol_map.parquet` — Hardened symbol map
- `data/symbol_map_changes.parquet` — Append-only audit log of manual overrides
- `data/symbol_map_unresolved.csv` — Unresolved scrip names
- `data/quarantine_gate1.parquet` — Quarantined Gate 1 rows (12 rows)
- `data/verification/canaries_2b.csv` — Canary regression edge cases
- `scripts/gate1_parse_validate.py` — Gate 1 parsing and validation script
- `scripts/gate2_build_symbol_map.py` — Symbol map generation and Gate 2 report
- `scripts/review_symbol_map.py` — Review CSV generator
- `scripts/apply_symbol_map_review.py` — Review application script with refusal enforcement
- `gate_2b_verification.md` — Final verification artifact
