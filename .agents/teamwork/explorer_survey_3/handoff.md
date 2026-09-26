# Handoff Report — Explorer 3: Symbol Map and Review Tooling Survey (R3, R4, R5)

## 1. Observation

- **Existing Symbol Map**: `data/symbol_map.parquet` exists with 1,448 rows and 8 columns:
  `['scrip_name', 'symbol', 'isin', 'first_seen', 'last_seen', 'resolution_method', 'confidence', 'status']`.
  SHA-256 is `ae982c3e1c22bdcafcf9bec6de28385d7dd3b29d3392ad39935f4e1b0c28fc58`.
  Status breakdown: `proposed`: 739, `auto`: 709.
  Resolution methods: `equity_l_exact`: 709, `unresolved`: 516, `manual`: 223.
  All 516 unresolved candidates were previously assigned `status = "proposed"` instead of `"unresolved"`.
- **Hardcoded Renames**: In `scripts/gate2_build_symbol_map.py` (lines 31–68), `KNOWN_CORPORATE_RENAMES` defines 37 corporate renames. At line 148, these are mapped as `resolution_method = "manual"`, `confidence = "high"`, `status = "proposed"`.
- **EQUITY_L Overwrite Vulnerability**: In `data/raw_reference/EQUITY_L.csv` (2,583 rows), 6 rows share normalized company names:
  * `FEL` (Future Enterprises Limited, INE623B01027, BZ) vs `FELDVR` (Future Enterprises Limited, IN9623B01058, BZ)
  * `GATECH` (GACM Technologies Limited, INE224E01028, BE) vs `GATECHDVR` (GACM Technologies Limited, INE224E01036, BE)
  * `JISLDVREQS` (Jain Irrigation Systems Limited, IN9175A01010, EQ) vs `JISLJALEQS` (Jain Irrigation Systems Limited, INE175A01038, EQ)
  In `scripts/gate2_build_symbol_map.py` line 105 (`eq_exact[n] = (sym, isin)`), later rows silently overwrote earlier rows.
- **Predecessor Markers**: In `data/index_events.parquet` (9,121 rows, 1,448 unique scrip names), 64 scrip names match word-boundary regex `\b(old|sus|suspended|erstwhile|merge[a-z]*|arrangement|delisted)\b`. A naive substring check matches 78 names due to false positives on words like "Holdings" and "Golden".
- **Concurrent Alias Collisions**: Under current candidate ISINs, 101 scrip names share an ISIN with another scrip name while both are active in the same index concurrently.
- **Listing Date Discrepancies**: 256 candidate symbols in `EQUITY_L.csv` have listing dates > 30 days after first event appearance in index events.
- **Unremoved Seed Members**: In NIFTY500, 399 scrip names have only `IN` events (seed of 1998-08-01) and no `OUT` events. In `gate2_build_symbol_map.py` line 115, `last_seen` was set to `1998-08-01` (0-day window) instead of the index `covered_end` (`2020-09-14`).
- **Review Tool Implementation**:
  * `scripts/review_symbol_map.py` groups proposed rows into 3 tier CSVs but does not separate unresolved rows to `data/symbol_map_unresolved.csv` and omits editable override/approval note columns.
  * `scripts/apply_symbol_map_review.py` allows setting `auto`, accepts empty symbols/ISINs, does not require an `approval_note` on flagged rows, does not verify compound keys `(scrip_name, symbol, isin)`, does not backup the parquet file, and does not append to `data/symbol_map_changes.parquet`.
- **Canary Test Verification**: 18 canonical edge cases were verified to exist in `data/index_events.parquet` covering all screens S1–S6, agent memory renames, and delistings.

## 2. Logic Chain

1. **V1 Archive (R3)**: `data/symbol_map.parquet` contains the Gate 2 baseline state. Archiving to `data/symbol_map_v1.parquet` preserves the historical baseline with SHA-256 `ae982c3e1c22bdcafcf9bec6de28385d7dd3b29d3392ad39935f4e1b0c28fc58`.
2. **Schema & Resolution Methods (R3)**: Rebuilding `symbol_map.parquet` with the 21 specified columns provides full evidence lineage (`eq_name`, `eq_series`, `eq_listing_date`, `isin_in_equity_l`, `name_similarity`, `first_token_match`, `price_first_bar`, `price_last_bar`, `bars_expected`, `bars_present`, `coverage_pct`, `flags`, `evidence_source`).
3. **Screens S1–S6 (R3)**:
   - Calculating `bars_expected` based on trading calendar days within unioned membership windows (with unremoved seed stocks extending to `covered_end`) correctly evaluates data coverage.
   - S1 (`listing_after_first_seen`) demotes candidates whose listing is > 30 days after first appearance, unless `coverage_pct >= 90%` and all other auto criteria are met.
   - S2 (`duplicate_name_collision`) prevents arbitrary symbol assignment on EQUITY_L duplicate names (`FEL`, `JISLDVREQS`, `GATECH`).
   - S3 (`isin_unverified`) flags candidates not present in official exchange listing.
   - S4 (`concurrent_alias_collision`) detects active interval overlap between alias scrips.
   - S5 (`predecessor_marker`) with word-boundary regex prevents auto-resolution of 64 predecessor/delisted entities without false positives on "Holdings" or "Golden".
   - S6 (`first_token_mismatch`) flags spurious token matches where the brand name diverges.
4. **Auto Rule & Demotion (R3)**: Restricting `auto` to exact normalized name matches that are unique in EQUITY_L, have verified ISINs, no S4/S5 flags, and `coverage_pct >= 90%` guarantees mathematical and regulatory rigor. Demotions by flag must be tracked and reported alongside coverage tiers (`>=90%`, `30–90%`, `<30%`, `N/A`).
5. **Review Tool Refusal Hardening (R4)**: Reading `review_action` only, rejecting `auto`, rejecting empty symbols/ISINs, enforcing mandatory `approval_note` on flagged rows, and validating compound keys prevents accidental or unauthorized corruption of the symbol map. Automated pre-modification backups and audit trail appending to `data/symbol_map_changes.parquet` guarantee reproducibility.
6. **Canary Regression Suite (R5)**: Creating `data/verification/canaries_2b.csv` with the 18 verified canonical edge cases and asserting that none resolve to `auto` and all bear expected flags provides regression protection across all screens.

## 3. Caveats

1. `data/price_cache_export.parquet` has not yet been exported (Milestone 0 / Explorer 1 task). When exported from `/storage/emulated/0/MIP1_Scanner/data/stock_ohlcv_cache.pkl`, it will provide price bars from 2007-01-02 to 2026-08-31 for 750 symbols. Stocks whose membership terminated prior to 2007 will naturally fall into Coverage Tier `< 30%`.
2. The official trading calendar must be derived from exported NSEI index bars (4,649 trading days from 2007-09-17). Trading day counts for windows prior to 2007 can use weekday calendar days or a reconstructed holiday calendar.
3. No codebase modifications were made in this turn, strictly complying with the read-only exploration constraint.

## 4. Conclusion

The specifications for R3 (Symbol Map Rebuild with Evidence & S1–S6 Screens), R4 (Review Tooling Refusal Hardening), and R5 (Canary Regression Suite) are fully surveyed, validated, and ready for immediate implementation. All necessary equations, edge cases, refusal paths, and schemas are defined in detail in `.agents/teamwork/explorer_survey_3/survey_report.md`.

## 5. Verification Method

To verify these findings independently:
1. Verify existing symbol map and compute SHA-256:
   ```bash
   sha256sum data/symbol_map.parquet
   # Expected: ae982c3e1c22bdcafcf9bec6de28385d7dd3b29d3392ad39935f4e1b0c28fc58
   ```
2. Verify EQUITY_L duplicate names (S2 collision):
   ```bash
   python3 -c "import pandas as pd; eq = pd.read_csv('data/raw_reference/EQUITY_L.csv'); eq.columns = [c.strip() for c in eq.columns]; print(eq[eq.duplicated(subset=['NAME OF COMPANY'], keep=False)][['SYMBOL', 'NAME OF COMPANY', 'ISIN NUMBER']])"
   ```
3. Verify S5 predecessor regex matches 64 rows:
   ```bash
   python3 -c "import pandas as pd, re; events = pd.read_parquet('data/index_events.parquet'); p = re.compile(r'\b(old|sus|suspended|erstwhile|merge[a-z]*|arrangement|delisted)\b', re.I); print(len([s for s in set(events['scrip_name']) if p.search(s)]))"
   # Output: 64
   ```
4. Verify presence of all 18 canary edge case names in `data/index_events.parquet`:
   ```bash
   python3 -c "import pandas as pd; ev = pd.read_parquet('data/index_events.parquet'); scrips = set(ev['scrip_name']); targets = ['Tube Investments of India Ltd.-Old', 'Wockhardt Ltd. (old)', 'National Aluminium Co. Ltd. (Old)', 'Larsen & Toubro Ltd.-Sus', 'Aptech Ltd. (Erstwhile)', 'Reliance Petroleum Ltd.- Merge', 'Future Enterprises Ltd.', 'Jain Irrigation Systems Ltd.', 'Jain Irrigation Systems Ltd. (Old)', 'Hero Honda Motors Limited', 'Infosys Technologies Limited', 'Satyam Computer Services Ltd.', 'UTI Bank Ltd.', 'Ranbaxy Laboratories Ltd.', 'Dewan Housing Finance Corporation Ltd.', 'Larsen & Toubro Infotech Ltd.', 'Reliance Capital Ltd.', '20th Century Finance Corporation Ltd.']; print(all(t in scrips for t in targets))"
   # Output: True
   ```
