# NEXT TASK: PHASE 5.5.M-1 BUILD PROMPT — NIFTY500 SYMBOL MAP RESOLUTION & COVERAGE RE-EVALUATION

**Prior Phase**: Phase 5.5.A-3 (Ruling: **REJECT** per §1 <60.0% threshold at 59.92%, root-cause isolated to 299 unapproved constituent scrips)  
**Target Phase**: Phase 5.5.M-1 (HALT-1b-M Symbol Map Resolution)  
**Deliverables Directory**: `deliverables/halt1b_m1/`  
**Standing Gate**: **HALT-1b-M-1** (Blocks on completion of Gate 4)  
**Workspace Root**: `/storage/emulated/0/Documents/Project MIP`  
**Execution Environment**: Samsung Galaxy S23, PRoot Ubuntu Linux (`/usr/bin/python3.12`), apt-managed packages  

---

## 0. MANDATE & STRATEGIC CONTEXT

Phase 5.5.A-3 conclusively proved that historical daily Bhavcopy price availability is 99% complete, but joint universe coverage was artificially bottlenecked at **59.92%** because only **435 out of 734** unique NIFTY500 constituent scrips had `mapping_status in {'auto', 'approved'}` in `data/symbol_map.parquet`.

Your objective in Phase 5.5.M-1 is to systematically resolve the **299 unapproved NIFTY500 constituents**, apply vetted mappings using the hardened review tooling, extract raw/adjusted prices for newly mapped symbols from the locally cached 1,154 Bhavcopies (zero network required), and elevate joint universe coverage past the **$\ge 85.0\%$ PASS threshold**.

### Non-Negotiable Constraints:
1. **Tooling & Validation Discipline**:
   - All mapping updates must be applied strictly via `scripts/apply_symbol_map_review.py <review_csv_path>`.
   - Never directly mutate `data/symbol_map.parquet` via arbitrary ad-hoc scripts.
   - Any approved row bearing active flags (S1–S6) **must** have a non-empty `approval_note` citing verified evidence.
2. **No Strategy Tuning**: Strategy parameters and rules (R2, R3, R5, R6, R7, R8, R9, $N=20$) remain strictly frozen.
3. **Audit Trail & Reproducibility**:
   - Every change must be recorded automatically in `data/symbol_map_changes.parquet` (enforced by `apply_symbol_map_review.py`).
   - Deliverables must follow the standard structure: `deliverables/halt1b_m1/DIGEST.md` and `deliverables/halt1b_m1/EVIDENCE_INDEX.tsv`.

---

## 1. TARGET COVERAGE THRESHOLDS

Joint coverage across the 57 monthly snapshots:
- **PASS**: Median joint coverage $\ge 85.0\%$ (Target for Phase 5.5.M-1)
- **INDICATIVE**: Median joint coverage between $60.0\%$ and $84.9\%$ (requires user sign-off)
- **REJECT**: Median joint coverage $< 60.0\%$

---

## 2. EXECUTION GATES

### Gate 0: NIFTY500 Pending Scrip Triage & Impact Ranking
- Filter `data/symbol_map.parquet` for the 299 NIFTY500 constituent scrips currently having `status in {'proposed', 'unresolved'}`.
- Cross-reference against `deliverables/halt1b_p_a3/data_csv/monthly_coverage_comparison.csv` to rank pending scrips by snapshot occurrence frequency.
- Output: `deliverables/halt1b_m1/raw/gate0_triage.txt` and `deliverables/halt1b_m1/data_csv/nifty500_pending_scrips_ranked.csv`.

### Gate 1: High-Confidence Tier Vetting & Application
- Inspect `data/symbol_map_review_high.csv` for candidates corresponding to the pending NIFTY500 scrips.
- Verify ISIN presence in `data/raw_reference/EQUITY_L.csv` and name similarity $\ge 0.90$.
- For each verified scrip:
  - Set `review_action = approved`.
  - Populate `approval_note` with specific verification citation (e.g. `"Exact ISIN match in EQUITY_L; corporate name modernization verified"`).
- Execute:
  ```bash
  /usr/bin/python3 scripts/apply_symbol_map_review.py data/symbol_map_review_high.csv
  ```
- Output: `deliverables/halt1b_m1/raw/gate1_apply_high.txt`.

### Gate 2: Medium-Confidence & Corporate Rename Resolution
- Inspect `data/symbol_map_review_medium.csv` and `data/symbol_map_unresolved.csv` for remaining high-impact NIFTY500 constituents.
- Resolve known corporate actions, mergers, and ticker renames (e.g. historical name changes documented in exchange circulars or NSE archives).
- For approved rows: specify `override_symbol`, `override_isin`, `override_evidence`, and explicit `approval_note`.
- Execute `scripts/apply_symbol_map_review.py` on the curated review file.
- Output: `deliverables/halt1b_m1/raw/gate2_apply_medium.txt` and `deliverables/halt1b_m1/data_csv/approved_scrips_summary.csv`.

### Gate 3: Local Price Extraction for Newly Mapped Symbols (Zero Network)
- Identify all newly approved symbols resulting from Gates 1 and 2.
- Extract daily series EQ/BE bars for these symbols directly from the **1,154 cached Bhavcopy archives** already stored in PRoot Ubuntu (`deliverables/halt1b_p_a3/samples/bhav/` and cached archives).
- Apply `scripts/adjust_prices.py:adjust_ohlc()` using `data/verification/halt1b_p_a2/ca_calendar_raw.parquet`.
- Merge with the existing price dataset to produce updated Parquet: `data/verification/halt1b_m1/adjusted_bhavcopy_bars_v2.parquet`.
- Output: `deliverables/halt1b_m1/raw/gate3_price_extraction.txt`.

### Gate 4: Coverage Re-Measurement & PASS Threshold Validation
- Recompute joint universe coverage across all 57 monthly snapshots with the updated mapped universe and expanded price dataset.
- Assert median joint coverage $\ge 85.0\%$.
- Export comparative coverage table: `deliverables/halt1b_m1/data_csv/monthly_coverage_comparison_v2.csv`.
- Compile deliverables: `deliverables/halt1b_m1/DIGEST.md` and `deliverables/halt1b_m1/EVIDENCE_INDEX.tsv`.
- Send Telegram completion alert using `telegram-notify`.
- **HALT-1b-M-1 IS OPEN**: Stop and present deliverables to Auditor for formal Gate 1b approval.
