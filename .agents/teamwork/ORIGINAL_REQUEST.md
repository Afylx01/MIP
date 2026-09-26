# Original User Request

## Initial Request — 2026-09-24T01:13:39Z

# PHASE 5.5 — GATE 2b: SYMBOL MAP EVIDENCE HARDENING

Rebuild the Phase 5.5 index membership symbol map with cryptographic and price-bar evidence hardening (S1–S6 checks), repair Gate 1 anomalies, fix review tooling with strict refusal verification, run canary regressions, and recompute the Gate 2 report for NIFTY500 under HALT-1b.

Working directory: `/storage/emulated/0/Documents/Project MIP`
Integrity mode: development

Working rules 0.1–0.11 from the main build prompt apply (task list first, one verification artifact per gate with exact command + full raw output + files written, no swallowed exceptions, you never set approved or rejected).

Scope for this and later gates: Only NIFTY500 has a seed batch (500 INs on 1998-08-01). The other six indices contain change events only and cannot be reconstructed. From now on, membership snapshots, resolved fractions, and Gates B–F are computed for NIFTY500 ONLY. For the other six, Gate 2 output shows "event log only, not reconstructable" instead of resolved fractions. Snapshots with zero members print N/A, never 0.0%.

Workspace hygiene: Do not scan `/storage/emulated/0` broadly. Read only: the project workspace, and the named data directory `/storage/emulated/0/MIP1_Scanner/data/`.

## Requirements

### R0. Price Data Inventory & Safe Loading (HALT on failure)
- Inventory local price files in `/storage/emulated/0/MIP1_Scanner/data/` (path, size, format, mtime; state plainly if any Bhavcopy exists).
- Do NOT use surrogate or monkey-patched unpicklers. Load with a correct method (e.g. matching pandas version via Termux python or re-export) and write `data/price_cache_export.parquet`.
- Print source row count and exported row count (must match), column names and dtypes, and the SHA-256 of the export. If cannot be loaded faithfully, stop and report.
- Print unique symbols, date range, count of symbols whose last bar is before max date (delisted/suspended coverage). State whether cache includes delisted names.
- Derive official trading calendar from exported NSEI index bars. Print first date, last date, and day count. State calendar source. Do not scrape raw pickle bytes.

### R1. Gate 1 Repairs
- Re-run Gate 1(c) calendar validation against ambiguous rows inside calendar date range. Report day-first vs month-first trading-day hit rates on restricted set, plus count of rows outside calendar range.
- Inspect the 2 rows dated 2017-09-05 in `Nifty Dividend Opportunities 50` (Reliance Capital OUT, National Aluminium IN) deduplicated rather than quarantined. Print cell types (ctype) and neighbouring rows. If suspect datetime class, quarantine consistently and re-run dedupe count. Print before/after.
- Print day-first non-monotonic step count after quarantine (expected 0 for all sheets).
- Print all 10 deduplicated rows and all 10 quarantined rows in full.

### R2. Gate 0 Restatement
- Extract text from cached `nifty_replacement_circular_sep_2020.pdf` and cached rebalancing schedule HTML.
- Print up to 40 relevant lines; restate Gate 0 finding: "post-2020-09 bulletin availability NOT ESTABLISHED; deferred to Phase 5.6".

### R3. Symbol Map Rebuild with Evidence (S1–S6 Checks)
- Archive existing map as `data/symbol_map_v1.parquet` (report SHA-256).
- Remove hardcoded knowledge (`KNOWN_CORPORATE_RENAMES` only as `agent_memory`, `low` confidence, flagged `unsourced`).
- Statuses: `auto`, `proposed`, `unresolved`, `approved`, `rejected` (no candidate -> `unresolved`).
- `resolution_method`: `equity_l_exact`, `token_match`, `agent_memory`, `user_override`, `unresolved`.
- New columns: `eq_name, eq_series, eq_listing_date, isin_in_equity_l, name_similarity, first_token_match, price_first_bar, price_last_bar, bars_expected, bars_present, coverage_pct, flags, evidence_source`.
- Evidence screens S1–S6:
  - Membership window = first IN date to last OUT date per index (or covered_end if never removed), unioned across indices for that scrip name. `bars_expected` = calendar days in window; `bars_present` = candidate symbol bars in window; `coverage_pct` = ratio.
  - S1: `listing_after_first_seen` if `eq_listing_date` > membership start + 30 days.
  - S2: `duplicate_name_collision` if several EQUITY_L rows share normalized name. Never keep last row wins.
  - S3: `isin_unverified` if ISIN not in EQUITY_L and evidence_source cites no external document.
  - S4: `concurrent_alias_collision` when two scrip names map to one ISIN and co-exist in same index at same time.
  - S5: `predecessor_marker` for names containing Old, Sus, Erstwhile, Merge, Arrangement, Delisted. Can never be auto.
  - S6: `first_token_mismatch` when first word of scrip name differs from first word of `eq_name`.
- Auto rule: exact normalized name match + unique EQUITY_L candidate + ISIN in EQUITY_L + no S1/S4/S5 flag + `coverage_pct >= 90`. (S1-flagged may stay auto only if `coverage_pct >= 90`). Everything else with candidate is `proposed`. Print demotion counts by flag.
- Report coverage tiers (`>=90`, `30-90`, `<30`, `n/a`).

### R4. Review Tooling Fixes & Refusal Hardening
- `scripts/review_symbol_map.py`: proposed rows only -> CSV. unresolved -> `data/symbol_map_unresolved.csv`. Include all evidence columns + editable columns `review_action`, `override_symbol`, `override_isin`, `override_evidence`, `approval_note`. `status` is read-only.
- `scripts/apply_symbol_map_review.py <csv>`: reads `review_action` only. Refuses invalid action, refuses `auto`, refuses empty symbol/ISIN, refuses flagged row without `approval_note`. Verifies key match `(scrip_name, symbol, isin)`. Backs up map and appends to `data/symbol_map_changes.parquet`.
- Test all refusal paths with raw console output.

### R5. Canary Regression Test
- Create `data/verification/canaries_2b.csv` with all 15+ canonical edge cases.
- All must be not auto, and flagged with expected reasons.

### R6. Gate 2 Report Recomputation (NIFTY500 Only) & HALT-1b
- Recompute Gate 2 report for NIFTY500 only. Other 6 indices show "event log only, not reconstructable".
- Report name-level resolved fractions and price-covered fractions (`coverage_pct >= 90`). Zero members prints N/A.
- Add survivorship disclosure line: `Survivorship note: <n> of <total> NIFTY500 members at <snapshot> are unresolved or lack price data.`
- Produce `gate_2b_verification.md` with exact commands, raw outputs, and 20 sample rows per status (fixed RNG seed).
- Halt at HALT-1b. Do not begin Gate 3.
