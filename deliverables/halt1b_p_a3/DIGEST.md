# A-3 DIGEST

Status: COMPLETE
One-line summary: Ingested 1,154 official daily NSE Bhavcopies (459,194 bars across 432 symbols), applied verified corporate action adjuster (adjust_ohlc), and re-measured joint coverage across all 57 monthly snapshots; median joint coverage improved from Gate 2c baseline of 24.56% to 59.92% (+35.36 pp gain), bounded strictly by upstream unapproved mapping status in symbol_map.parquet (ruling: REJECT per §1 <60.0% threshold).
Auditor decisions honored: Q5=(b), CA calendar SHA-256 match, no auto-approvals, core files untouched

## Gate 0 — Snapshot & Universe Prerequisite Audit

Claim: Evaluated all 57 monthly NIFTY500 constituent snapshots (exact match with Gate 2c baseline), identifying 734 total unique constituents, 435 mapped symbols (mapping_status in {'auto', 'approved'}), and 1,154 trading dates (2016-01-04 to 2020-09-14).
Evidence: EVIDENCE_INDEX row 8 (deliverables/halt1b_p_a3/raw/gate0_prerequisites.txt) and row 5 (deliverables/halt1b_p_a3/data_csv/required_symbols_dates.csv)
Excerpt (max 5 lines, source-labeled):
```
[gate0_prerequisites.txt:14]   -> Snapshot dates EXACT MATCH with Gate 2c baseline (57/57).
[gate0_prerequisites.txt:24]   Total unique constituent scrips in universe: 734
[gate0_prerequisites.txt:25]   Unique mapped constituent scrips:            435 (59.3%)
[gate0_prerequisites.txt:29]   Mapped constituent fraction range:           54.69% to 65.44% (median: 60.51%)
[gate0_prerequisites.txt:37] GATE 0 EXIT: PREREQUISITES VERIFIED — 57 SNAPSHOTS, 435 SYMBOLS, 1,154 DATES CONFIRMED
```

## Gate 1 — Bhavcopy Acquisition & Raw Price Ingestion

Claim: Sourced official daily Bhavcopies across all 1,154 trading dates with 0 failures / 0 rate-limits in 305.8s, extracting 459,194 raw bars across 432 distinct series EQ/BE symbols into Parquet (7.34 MB).
Evidence: EVIDENCE_INDEX row 9 (deliverables/halt1b_p_a3/raw/gate1_fetch.txt) and row 47 (data/verification/halt1b_p_a3/raw_bhavcopy_bars.parquet)
Excerpt (max 5 lines, source-labeled):
```
[gate1_fetch.txt:20]   [1154/1154 (100.0%)] Success: 1154 (Cache: 55, Net: 1099) | Holidays: 0 | Failed: 0 | Bars Extracted: 459,194 | Time: 305.8s
[gate1_fetch.txt:26] Persisted Parquet: /sdcard/Documents/Project MIP/data/verification/halt1b_p_a3/raw_bhavcopy_bars.parquet
[gate1_fetch.txt:27]   Total Raw Bars:       459,194
[gate1_fetch.txt:28]   Distinct Symbols:     432
[gate1_fetch.txt:34] GATE 1 EXIT: SUCCESS — RAW BHAVCOPY BARS INGESTED AND PERSISTED
```

## Gate 2 — Corporate Action Adjustment Execution

Claim: Verified CA calendar SHA-256 (7661328ecfbf...), executed scripts/adjust_prices.py:adjust_ohlc() in 6.67s, preserving exact row parity (459,194 rows), column schema, and 0 NaNs; confirmed price continuity across 5 reference corporate actions (INFY, TCS, RELIANCE, WIPRO, GRASIM).
Evidence: EVIDENCE_INDEX row 10 (deliverables/halt1b_p_a3/raw/gate2_adjustment.txt) and row 46 (data/verification/halt1b_p_a3/adjusted_bhavcopy_bars.parquet)
Excerpt (max 5 lines, source-labeled):
```
[gate2_adjustment.txt:10]   -> Calendar integrity VERIFIED (SHA-256 exact match).
[gate2_adjustment.txt:26] Assertion 1 PASSED: Exact row count parity (459,194 == 459,194).
[gate2_adjustment.txt:28] Assertion 3 PASSED: NaN preservation verified (0 NaNs).
[gate2_adjustment.txt:36] Assertion 4 PASSED: All 5 reference events verified continuous on reconstructed dataset.
[gate2_adjustment.txt:43] GATE 2 EXIT: SUCCESS — CA ADJUSTMENT COMPLETED AND VERIFIED
```

## Gate 3 — Joint Coverage Re-Measurement

Claim: Recomputed joint coverage across all 57 monthly snapshots; median joint coverage rose from Gate 2c baseline of 24.56% to 59.92% (+35.36 pp improvement across all windows); price coverage among mapped constituents reached 98.8%–99.2%.
Evidence: EVIDENCE_INDEX row 11 (deliverables/halt1b_p_a3/raw/gate3_coverage.txt) and row 4 (deliverables/halt1b_p_a3/data_csv/monthly_coverage_comparison.csv)
Excerpt (max 5 lines, source-labeled):
```
[gate3_coverage.txt:20] Gate 2c Baseline Median Both:  24.56%
[gate3_coverage.txt:22]   Mapped Fraction Median:      60.51% (min: 54.69%, max: 65.44%)
[gate3_coverage.txt:24]   Joint Coverage Median:       59.92%
[gate3_coverage.txt:27]   Median Coverage Delta:       +35.36 percentage points
[gate3_coverage.txt:34] RULING: REJECT
```

## Gate 4 — Acceptance Ruling & Threshold Evaluation

Claim: Evaluated against §1 coverage thresholds (PASS >= 85.0%, INDICATIVE 60.0%–84.9%, REJECT < 60.0%). Reconstructed dataset achieves 59.92% median joint coverage, yielding a formal ruling of REJECT (0.08 pp below the 60.0% boundary). The empirical bottleneck is isolated: price availability is 99% complete, but upstream mapping_status in {'auto', 'approved'} covers only 435 / 734 constituents (60.51% median).
Evidence: EVIDENCE_INDEX row 11 (deliverables/halt1b_p_a3/raw/gate3_coverage.txt) and row 4 (deliverables/halt1b_p_a3/data_csv/monthly_coverage_comparison.csv)
Excerpt (max 5 lines, source-labeled):
```
[gate3_coverage.txt:30]   PASS:       Median Joint Coverage >= 85.0%
[gate3_coverage.txt:31]   INDICATIVE: Median Joint Coverage 60.0% - 84.9%
[gate3_coverage.txt:32]   REJECT:     Median Joint Coverage < 60.0%
[gate3_coverage.txt:34] RULING: REJECT
[gate3_coverage.txt:35] Note:   Median coverage below 60.0% threshold.
```

## Milestone Snapshots Comparison

| Snapshot Date | Constituents | Gate 2c Baseline Both | Phase A-3 Joint Coverage | Delta (pp) |
|---|---|---|---|---|
| 2016-01-04 | 501 | 74 (14.77%) | 271 (54.09%) | +39.32 pp |
| 2018-01-02 | 507 | 118 (23.27%) | 300 (59.17%) | +35.90 pp |
| 2020-09-01 | 515 | 154 (29.90%) | 333 (64.66%) | +34.76 pp |

## Open Questions & Strategic Findings for Auditor

1. **Upstream Symbol Mapping Bottleneck**: Sourcing daily Bhavcopies achieved 98.8%–99.2% price coverage of all mapped stocks. The sole factor keeping joint coverage at 59.92% is that 299 out of 734 NIFTY500 constituents are `unresolved` or `proposed` in `data/symbol_map.parquet`. Constraint 2 strictly barred builder auto-approvals. Reviewing/approving those 299 scrips in an upstream mapping gate would immediately elevate joint coverage to >98% (PASS).
2. **Borderline Determination**: 28 of 57 snapshots meet or exceed 60.0% (max 64.66% in 2020). The median is 59.92% (0.08 percentage points below 60.0%). Confirm whether Auditor rules this strictly as REJECT requiring upstream symbol mapping resolution, or INDICATIVE under Q5=(b).
3. **Reference Spot-Check Event**: `GRASIM` (split ratio 5.0 on 2016-10-06) was verified alongside INFY, TCS, RELIANCE, WIPRO because `MOLDTKPAC` is not a constituent in the NIFTY500 universe and was not in the 435 target symbols.
