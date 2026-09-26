# NEXT TASK: PHASE 5.5.A-3 BUILD PROMPT — BHAVCOPY SOURCING & COVERAGE RE-MEASUREMENT

**Prior Phase**: Phase 5.5.A-2 (Status: **ACCEPTED** by Auditor per `A2_RULING.md`)  
**Target Phase**: Phase 5.5.A-3 (Bhavcopy Sourcing & Joint Coverage Re-measurement)  
**Deliverables Directory**: `deliverables/halt1b_p_a3/`  
**Standing Gate**: **HALT-1b-P-3** (Blocks on completion of Gate 4)  
**Workspace Root**: `/storage/emulated/0/Documents/Project MIP`  
**Execution Environment**: Samsung Galaxy S23, PRoot Ubuntu Linux (`/usr/bin/python3.12`), apt-managed packages  

---

## 0. MANDATE & BOUNDARIES

You are the **builder** for Phase 5.5.A-3. Your objective is to eliminate the survivorship bias identified in Gate 2c by ingesting historical NSE Bhavcopy archives across 2016-01-01 to 2020-09-14, applying the verified corporate action adjuster from Phase 5.5.A-2, and re-measuring joint universe coverage across all 57 monthly snapshots.

### Non-Negotiable Constraints:
1. **No Parameter Tuning**: Do not alter, optimize, or propose changes to strategy rules (R2, R3, R5, R6, R7, R8, R9, $N=20$).
2. **No Symbol-Map Auto-Approvals**: `mapping_status` remains strictly restricted to `{auto, approved}`. You may NOT approve `proposed` or `unresolved` rows in `data/symbol_map.parquet`.
3. **No Modification to Core Files**:
   - Do NOT modify `data/symbol_map.parquet`.
   - Do NOT modify `data/corrections.parquet`.
   - Do NOT modify `scripts/adjust_prices.py`.
   - All Phase A-3 code, raw outputs, logs, data tables, and manifests must reside in `deliverables/halt1b_p_a3/` (except ingested raw/adjusted price artifacts which must be stored in `data/verification/halt1b_p_a3/`).
4. **Reproducibility & Evidence Structure**:
   - Maintain the standard deliverable format: `DIGEST.md` and `EVIDENCE_INDEX.tsv` linking every claim to a raw on-disk file with exact byte count and SHA-256 hash.
   - Log all terminal outputs verbatim into `deliverables/halt1b_p_a3/raw/`.

---

## 1. COVERAGE ACCEPTANCE THRESHOLDS

Joint coverage is defined as:
$$\text{Joint Coverage} = \frac{|\text{Mapped} \cap \text{Price-Covered} \cap \text{Not-Flagged}|}{|\text{Snapshot Constituents}|}$$

On the 57 monthly snapshots (2016-01-14 to 2020-09-14):
- **PASS**: Median joint coverage $\ge 85.0\%$.
- **INDICATIVE**: Median joint coverage between $60.0\%$ and $84.9\%$ (requires user sign-off for residual survivor bias).
- **REJECT**: Median joint coverage $< 60.0\%$.

---

## 2. EXECUTION GATES

### Gate 0: Snapshot & Universe Prerequisite Audit
- Load the 57 monthly NIFTY500 constituent snapshots previously evaluated in Gate 2c.
- Cross-reference constituent symbols against `data/symbol_map.parquet` filtering strictly for `mapping_status in {'auto', 'approved'}`.
- Isolate the exact list of unique required symbols and the required historical trading dates from `data/trading_calendar.txt`.
- Output: `deliverables/halt1b_p_a3/raw/gate0_prerequisites.txt` and `deliverables/halt1b_p_a3/data_csv/required_symbols_dates.csv`.

### Gate 1: Bhavcopy Acquisition & Raw Price Ingestion
- Source historical daily Bhavcopy archives from official exchange archives (`nsearchives.nseindia.com`) covering trading dates from `2016-01-01` to `2020-09-14`.
- Adhere to network discipline:
  - Honest User-Agent.
  - Rate-limited burst requests with exponential backoff on HTTP 429/503.
  - Verify zip integrity (`PK\x03\x04`) and CSV headers (`SYMBOL, SERIES, OPEN, HIGH, LOW, CLOSE, TOTTRDQTY`).
- Extract series `EQ` and `BE` for all target symbols.
- Persist extracted raw price series to `data/verification/halt1b_p_a3/raw_bhavcopy_bars.parquet`.
- Output: `deliverables/halt1b_p_a3/raw/gate1_fetch.txt` and summary CSV of downloaded dates/records.

### Gate 2: Corporate Action Adjustment Execution
- Load `data/verification/halt1b_p_a2/ca_calendar_raw.parquet` (214 records, SHA-256: `7661328ecfbf26828ce14950401474847de0f7919886b3085500eddc3b93b8d0`).
- Execute `scripts/adjust_prices.py:adjust_ohlc(raw_df, ca_calendar_df)`.
- Assertions:
  - Input raw row count equals output adjusted row count.
  - No forward-filling, no dropping, no rounding introduced.
  - Spot-check continuity on the 5 reference events (INFY, TCS, RELIANCE, WIPRO, MOLDTKPAC).
- Persist adjusted price dataset to `data/verification/halt1b_p_a3/adjusted_bhavcopy_bars.parquet`.
- Output: `deliverables/halt1b_p_a3/raw/gate2_adjustment.txt`.

### Gate 3: Joint Coverage Re-Measurement
- Recompute coverage metrics for all 57 monthly snapshot dates:
  1. Total snapshot constituent count.
  2. Mapped constituent count (`status in {auto, approved}`).
  3. Price-covered constituent count (presence of valid adjusted OHLCV bar on snapshot date).
  4. Unflagged constituent count (excluding active S1–S6 flags).
  5. Joint coverage count and percentage.
- Produce a comparative table: Gate 2c baseline (median 24.56%) vs Phase A-3 reconstructed coverage across all 57 snapshots.
- Output: `deliverables/halt1b_p_a3/raw/gate3_coverage.txt` and `deliverables/halt1b_p_a3/data_csv/monthly_coverage_comparison.csv`.

### Gate 4: Acceptance Ruling & Deliverable Bundle Compilation
- Evaluate median joint coverage against §1 thresholds.
- Generate Phase 5.5.A-3 documentation:
  - `deliverables/halt1b_p_a3/DIGEST.md`: Gate-by-gate claims, metrics, and excerpts.
  - `deliverables/halt1b_p_a3/EVIDENCE_INDEX.tsv`: Complete TSV manifest (path, bytes, sha256, what_it_proves).
  - Update `task_list.md` to tick Phase 5.5.A-3 gates and leave `HALT-1b-P-3` UNTICKED.
  - Send Telegram completion alert using `telegram-notify`.
- **HALT-1b-P-3 IS OPEN**: Cease execution and notify the Auditor. Do NOT proceed to Gate 3 (corrections) or backtesting.
