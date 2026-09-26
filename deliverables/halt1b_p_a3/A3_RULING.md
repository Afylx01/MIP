# A-3 AUDITOR RULING

Status: REJECT

## Files inspected

- `deliverables/halt1b_p_a3/DIGEST.md` | `153dc17e670da3ba860c9a1629addeca5fcf5a4b8a5128c8e0d4b60a04368d78`
- `deliverables/halt1b_p_a3/EVIDENCE_INDEX.tsv` | `d30d9110d101695592c32f1de2a22ac6294416bbeff99af410ceac4fb05327c6`
- `deliverables/halt1b_p_a3/task_list.md` | `a9b6d0b4f0b83450bbef9d9ccdbe1cdbd97ee0803ae62795c446e7fc97e27a61`
- `deliverables/halt1b_p_a3/data_csv/gate1_download_summary.csv` | `41be14aaf6f07b914d202338b46ec00d5e37f55680c86bf276952320bb78d161`
- `deliverables/halt1b_p_a3/data_csv/gate2_spot_check_summary.csv` | `3f13811def440b79f97ac9e1a826d6216423cb43887060b6b83de69b1c8dc5d4`
- `deliverables/halt1b_p_a3/data_csv/monthly_coverage_comparison.csv` | `b8f23523a7dd8317d0473ac5e2541e706ae1ac0d0b0dfdc83c920dcd9749ba53`
- `deliverables/halt1b_p_a3/data_csv/required_symbols_dates.csv` | `30661e603dd6498638ea030b20483c2ac1569b3d4ebcb97dd45fceb0a849a4df`
- `deliverables/halt1b_p_a3/data_csv/snapshot_prerequisite_audit.csv` | `9cfeb7f23b867a2e228d946601200b07549a03b8646759a17851f86e98e9bdfd`
- `deliverables/halt1b_p_a3/data_csv/window_trading_dates.csv` | `bbaa4d0777f0dc264fc4ecae5388094212a23ab62c5f236a49c5e6c597f0e758`
- `deliverables/halt1b_p_a3/raw/gate0_prerequisites.txt` | `688ab893d0e5aa71c00f7080a16ddea504600f808b902324619ce658340ffe12`
- `deliverables/halt1b_p_a3/raw/gate1_fetch.txt` | `bf4b4e9e222e58ec78b81f8abdabf8a32cde6e3d0ee52b6c22b984350ac0a2ba`
- `deliverables/halt1b_p_a3/raw/gate2_adjustment.txt` | `8faaa23c75e7ce9e70dcae66b617eb5935a24dd3b17705768c63a4c5f7e1a4ac`
- `deliverables/halt1b_p_a3/raw/gate3_coverage.txt` | `70f3bc3b8ef36b3216ce78c551b3c6a1c4ded1e70b5f87931eb62b71a82d4d67`
- `deliverables/halt1b_p_a3/scripts/gate0_prerequisites.py` | `910832962806e410354a7ea42ce70dcc6a3c61ab5a28c900b72f909c4814cc7b`
- `deliverables/halt1b_p_a3/scripts/gate1_fetch_bhavcopies.py` | `7007a275ceceee1db51a30dd297784d4e06e86dfea233210e5681abcfaa843d1`
- `deliverables/halt1b_p_a3/scripts/gate2_adjustment.py` | `ab8cdad73de5557669775591f74e1d1d46a772e7e133ed211b295c50cb2e7ce3`
- `deliverables/halt1b_p_a3/scripts/gate3_coverage.py` | `64577cbe9957439add680285a75dc17f8438cca7e2880f6d4a5222223bfe768c`
- `data/verification/halt1b_p_a3/raw_bhavcopy_bars.parquet` | `7ef0b60b51ed87ab767b6ba6c2d1bfa4f32e8b65cf2686aaed3ad303550f4241`
- `data/verification/halt1b_p_a3/adjusted_bhavcopy_bars.parquet` | `2b8279f17f32e86ca42b933e512768ac236bfb36669c5eb3b3bc9acdf1ee4bcf`
- `data/verification/halt1b_p_a2/ca_calendar_raw.parquet` | `7661328ecfbf26828ce14950401474847de0f7919886b3085500eddc3b93b8d0`

---

## Claims verified

### Claim 1: Gate 0 — Prerequisite Derivation & Snapshot Replay
- **Evidence Path**: `deliverables/halt1b_p_a3/raw/gate0_prerequisites.txt`, `deliverables/halt1b_p_a3/data_csv/required_symbols_dates.csv`
- **Recomputation**:
  - Exactly 57 monthly snapshots confirmed matching Gate 2c baseline (2016-01-04 to 2020-09-01).
  - 734 unique constituent scrip names identified in NIFTY500 membership history over the window.
  - 435 mapped constituent symbols identified with `mapping_status in {'auto', 'approved'}`.
  - 1,154 trading days confirmed from `data/trading_calendar.txt` spanning 2016-01-04 to 2020-09-14.

### Claim 2: Gate 1 — Bhavcopy Acquisition & Raw Bar Ingestion
- **Evidence Path**: `data/verification/halt1b_p_a3/raw_bhavcopy_bars.parquet`, `deliverables/halt1b_p_a3/raw/gate1_fetch.txt`
- **Recomputation**:
  - Total records: `459,194` raw OHLCV bars ingested (verified).
  - Distinct symbols: `432` series EQ/BE symbols (3 mapped symbols had zero historical exchange listings during the window).
  - Distinct trading dates: `1,154` (100.0% date coverage, zero missing days).
  - 0 network failures, 0 HTTP rate-limits reported across all 1,154 fetches.

### Claim 3: Gate 2 — Corporate Action Adjustment Execution & Continuity
- **Evidence Path**: `data/verification/halt1b_p_a3/adjusted_bhavcopy_bars.parquet`, `deliverables/halt1b_p_a3/raw/gate2_adjustment.txt`
- **Recomputation**:
  - CA Calendar input integrity: SHA-256 matches `7661328ecfbf26828ce14950401474847de0f7919886b3085500eddc3b93b8d0` exactly.
  - Row parity: `459,194 == 459,194` (zero row loss, zero dropped bars).
  - Invariance: 0 NaNs introduced (`df_adj['close'].isna().sum() == 0`).
  - Spot-check continuity on 5 reference corporate actions verified:
    - `INFY` (2018-09-04 Bonus 1:1): raw return $-48.60\% \rightarrow$ adjusted return $+2.79\%$ (PASS)
    - `TCS` (2018-05-31 Bonus 1:1): raw return $-50.46\% \rightarrow$ adjusted return $-0.91\%$ (PASS)
    - `RELIANCE` (2017-09-07 Bonus 1:1): raw return $-50.28\% \rightarrow$ adjusted return $-0.56\%$ (PASS)
    - `WIPRO` (2019-03-06 Bonus 1:3): raw return $-23.69\% \rightarrow$ adjusted return $+1.74\%$ (PASS)
    - `GRASIM` (2016-10-06 Split 5:1): raw return $-79.54\% \rightarrow$ adjusted return $+2.28\%$ (PASS)

### Claim 4: Gate 3 — Joint Coverage Re-Measurement & Delta from Baseline
- **Evidence Path**: `deliverables/halt1b_p_a3/data_csv/monthly_coverage_comparison.csv`, `deliverables/halt1b_p_a3/raw/gate3_coverage.txt`
- **Recomputation**:
  - Gate 2c baseline median joint coverage: `24.56%`.
  - Phase A-3 median joint coverage: `59.92%`.
  - Median coverage gain: `+35.36 percentage points` (improvement across all 57 snapshots).
  - Price availability conditional on mapping: **98.8% to 99.2%**.

---

## Claims rejected

### Claim: Acceptance for Backtesting Entry under §1 Thresholds
- **Evidence Path**: §1 of `deliverables/auditor/A3_PROMPT.md` and `deliverables/halt1b_p_a3/raw/gate3_coverage.txt`
- **Reason**:
  - The specification explicitly set the following acceptance boundaries:
    - **PASS**: Median joint coverage $\ge 85.0\%$
    - **INDICATIVE**: Median joint coverage $60.0\% \text{ to } 84.9\%$ (requires user sign-off for residual bias)
    - **REJECT**: Median joint coverage $< 60.0\%$
  - The measured median joint coverage is **59.92%**, which falls strictly into the **REJECT** band ($0.08$ percentage points below $60.00\%$).
  - Per Standing Rule R-14 ("No middle ground. A ruling is ACCEPT, REJECT, or ACCEPT_WITH_CONDITIONS. There is no 'looks good,' no 'probably fine'"), this phase cannot be approved as passing the coverage threshold for backtesting.

---

## Claims requiring user attention

1. **Root-Cause Diagnosis: Symbol Mapping vs. Price Availability**:
   - The pricing pipeline (Gate 1 and Gate 2) succeeded completely: 1,154 days of Bhavcopies were ingested and adjusted with 99% coverage of all mapped constituents.
   - The failure to meet the $\ge 60\%$ or $\ge 85\%$ threshold is **100% caused by the upstream symbol map (`data/symbol_map.parquet`)**, where only **435 out of 734** NIFTY500 constituent scrips currently carry `status in {'auto', 'approved'}`.
   - The remaining **299 scrips** are sitting in `proposed` (review CSVs) or `unresolved` status. The builder strictly obeyed Constraint 2 and did not auto-approve them.
2. **Actionable Remediation**:
   - The user must authorize the review and resolution of the 299 pending NIFTY500 constituents under gate **HALT-1b-M**.
   - Approving the high-confidence and medium-confidence candidate mappings in `data/symbol_map_review_high.csv` will immediately elevate mapped constituents from 435 to $>650$ ($>88\%$), immediately driving joint coverage above **86%** ($\ge 85\%$ PASS threshold).

---

## Conditions (if ACCEPT_WITH_CONDITIONS)

N/A. Ruling is **REJECT** on Phase 5.5.A-3 coverage gate.

---

## Next phase recommendation

Halt price pipeline progression and switch immediately to **HALT-1b-M (Phase 5.5.M-1: Systematic NIFTY500 Symbol Map Resolution)**.  
The actionable task prompt for the builder/reviewer has been written to [NEXT_TASK.md](file:///storage/emulated/0/Documents/Project%20MIP/deliverables/halt1b_p_a3/NEXT_TASK.md).
