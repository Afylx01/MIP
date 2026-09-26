# M-1 DIGEST

Status: COMPLETE
One-line summary: Resolved 192 pending NIFTY500 constituent scrips (70 high-confidence via EQUITY_L ISIN match + 122 curated corporate renames) via hardened review tooling, extracted 293,852 daily Bhavcopy bars locally from 1,154 cached archives (zero network calls), and elevated median joint universe coverage across all 57 monthly snapshots from 59.92% to 86.25% (+26.33 pp gain), decisively achieving the >=85.0% PASS threshold.
Auditor decisions honored: Tooling discipline strictly maintained (apply_symbol_map_review.py only), all S1–S6 active flags vetted with non-empty verified evidence citations, zero strategy rule modifications (R2, R3, R5, R6, R7, R8, R9, N=20 frozen), CA calendar SHA-256 verified, standing gate HALT-1b-M-1 left UNTICKED and OPEN.

## Gate 0 — NIFTY500 Pending Scrip Triage & Impact Ranking

Claim: Evaluated all 57 monthly snapshots, isolating 299 pending constituent scrips (132 unresolved, 84 review_high, 72 review_medium, 8 review_low, 3 unknown) and ranked them by snapshot occurrence frequency.
Evidence: EVIDENCE_INDEX row 8 (deliverables/halt1b_m1/data_csv/nifty500_pending_scrips_ranked.csv) and row 9 (deliverables/halt1b_m1/raw/gate0_triage.txt)
Excerpt (max 5 lines, source-labeled):
```
[gate0_triage.txt:15]   Currently Mapped (auto/approved):     435 (59.3%)
[gate0_triage.txt:16]   Pending Review (proposed/unresolved): 299 (40.7%)
[gate0_triage.txt:28] Current Base Mapped Fraction Median: 60.51%
[gate0_triage.txt:30]   Simulation [+ Review High (84 scrips)                    ]: Median Mapped = 72.50% (min: 68.79%, max: 77.28%)
[gate0_triage.txt:35] GATE 0 EXIT: PENDING SCRIPS TRIAGED — 299 SCRIPS ISOLATED AND RANKED
```

## Gate 1 — High-Confidence Tier Vetting & Application

Claim: Vetted 70 high-confidence NIFTY500 scrips with exact ISIN match in EQUITY_L and name similarity >= 0.90, setting review_action = 'approved' with explicit verification citations, and applied strictly via scripts/apply_symbol_map_review.py data/symbol_map_review_high.csv with automated backup.
Evidence: EVIDENCE_INDEX row 4 (deliverables/halt1b_m1/data_csv/gate1_vetted_high_summary.csv) and row 10 (deliverables/halt1b_m1/raw/gate1_apply_high.txt)
Excerpt (max 5 lines, source-labeled):
```
[gate1_apply_high.txt:9]  Vetted and marked 70 high-confidence scrips as 'approved'.
[gate1_apply_high.txt:19] Created backup at: data/symbol_map_backup_20260924_165422.parquet
[gate1_apply_high.txt:20] Updated data/symbol_map.parquet successfully.
[gate1_apply_high.txt:21] Appended 70 change record(s) to data/symbol_map_changes.parquet.
[gate1_apply_high.txt:29] GATE 1 EXIT: SUCCESS — 70 HIGH-CONFIDENCE SCRIPS APPROVED AND APPLIED
```

## Gate 2 — Medium-Confidence & Corporate Rename Resolution

Claim: Curated and resolved 122 high-impact corporate renames, ticker changes, and medium-tier constituents (including TITAN, HDFC, IBULHSGFIN, SRTRANSFIN, TATAMOTORS, INFRATEL, CADILAHC, MINDTREE, GMRINFRA, IDEA) with cited exchange circular evidence, applied via scripts/apply_symbol_map_review.py, lifting mapped constituent median from 60.51% to 90.77% (min 86.43%, max 94.37%).
Evidence: EVIDENCE_INDEX row 5 (deliverables/halt1b_m1/data_csv/gate2_curated_review.csv), row 3 (deliverables/halt1b_m1/data_csv/approved_scrips_summary.csv), and row 11 (deliverables/halt1b_m1/raw/gate2_apply_medium.txt)
Excerpt (max 5 lines, source-labeled):
```
[gate2_apply_medium.txt:16] Created backup at: data/symbol_map_backup_20260924_170046.parquet
[gate2_apply_medium.txt:17] Updated data/symbol_map.parquet successfully.
[gate2_apply_medium.txt:18] Appended 122 change record(s) to data/symbol_map_changes.parquet.
[gate2_apply_medium.txt:30]   approved    : 192
[gate2_apply_medium.txt:33] GATE 2 EXIT: SUCCESS — 122 CORPORATE RENAMES & MEDIUM TIER SCRIPS APPROVED
```

## Gate 3 — Local Price Extraction from Cached Bhavcopies (Zero Network)

Claim: Extracted daily series EQ/BE bars for all newly approved symbols directly from 1,154 locally cached Bhavcopy zip archives in 45.65s (zero network calls), merged with prior raw bars to reach 753,046 raw bars across 711 symbols, verified CA calendar SHA-256 (7661328ecfbf...), and executed adjust_ohlc() with exact row count parity (753,046 == 753,046), 0 NaNs, and verified reference corporate action spot checks.
Evidence: EVIDENCE_INDEX row 6 (deliverables/halt1b_m1/data_csv/gate3_extraction_summary.csv), row 12 (deliverables/halt1b_m1/raw/gate3_price_extraction.txt), and row 21 (data/verification/halt1b_m1/adjusted_bhavcopy_bars_v2.parquet)
Excerpt (max 5 lines, source-labeled):
```
[gate3_price_extraction.txt:23] Extraction completed in 45.65 seconds.
[gate3_price_extraction.txt:24] Total newly extracted raw bars: 293,852
[gate3_price_extraction.txt:29]   Total rows:    753,046 | Total symbols: 711 | Total dates: 1,154
[gate3_price_extraction.txt:40] Assertion 1 PASSED: Exact row count parity (753,046 == 753,046).
[gate3_price_extraction.txt:52] GATE 3 EXTRACTION & ADJUSTMENT COMPLETE: ALL ASSERTIONS PASSED
```

## Gate 4 — Coverage Re-Measurement & PASS Threshold Validation

Claim: Recomputed joint universe coverage across all 57 monthly snapshots; median joint coverage elevated to 86.25% (min: 82.04%, max: 90.49%), outperforming the Gate 2c baseline (24.56%) by +61.69 percentage points and Phase A-3 (59.92%) by +26.33 percentage points, decisively clearing the >=85.0% PASS threshold.
Evidence: EVIDENCE_INDEX row 7 (deliverables/halt1b_m1/data_csv/monthly_coverage_comparison_v2.csv) and row 13 (deliverables/halt1b_m1/raw/gate4_coverage.txt)
Excerpt (max 5 lines, source-labeled):
```
[gate4_coverage.txt:22] Phase M-1 Mapped Fraction Median:       90.77% (min: 86.43%, max: 94.37%)
[gate4_coverage.txt:25] Phase M-1 Joint Coverage Median:        86.25% (min: 82.04%, max: 90.49%)
[gate4_coverage.txt:26] Coverage Gain over Gate 2c Baseline:    +61.69 percentage points
[gate4_coverage.txt:27] Coverage Gain over Phase A-3:           +26.33 percentage points
[gate4_coverage.txt:50] VERDICT: >>> PASS <<< (Phase M-1 Median Joint Coverage 86.25% >= 85.0% threshold)
```

## Milestone Snapshots Comparison

| Snapshot Date | Constituents | Gate 2c Baseline Both | Phase A-3 Joint Coverage | Phase M-1 Joint Coverage | Delta vs Baseline | Delta vs Phase A-3 |
|---|---|---|---|---|---|---|
| 2016-01-04 (Snap #1) | 501 | 74 (14.77%) | 271 (54.09%) | 411 (82.04%) | +67.27 pp | +27.95 pp |
| 2018-01-01 (Snap #25) | 506 | 118 (23.32%) | 300 (59.29%) | 437 (86.36%) | +63.04 pp | +27.08 pp |
| 2020-09-01 (Snap #57) | 515 | 154 (29.90%) | 333 (64.66%) | 465 (90.29%) | +60.39 pp | +25.63 pp |
| **Full Window Median** | **506** | **124 (24.56%)** | **303 (59.92%)** | **438 (86.25%)** | **+61.69 pp** | **+26.33 pp** |

## Strategic Findings & Governance Compliance

1. **Root-Cause Resolution Complete**: Phase A-3 proved price data availability was ~99%, but coverage was bottlenecked at 59.92% due to 299 pending constituent scrips in `data/symbol_map.parquet`. Resolving 192 scrips (70 high-confidence + 122 curated corporate renames) lifted mapped constituent representation to 90.77% median, which immediately translated into 86.25% median joint coverage across all 57 monthly snapshots.
2. **Strict Tooling Discipline Preserved**: No direct or unvalidated mutations were made to `data/symbol_map.parquet`. All approvals passed through `scripts/apply_symbol_map_review.py`, creating point-in-time timestamped backups (`data/symbol_map_backup_*.parquet`) and appending 192 immutable audit entries with cited evidence into `data/symbol_map_changes.parquet`.
3. **Zero Network Price Ingestion**: All 293,852 additional price bars were extracted purely from the 1,154 locally pre-cached official Bhavcopy archives (`data/bhavcopy_cache/*.zip`) in 45.65 seconds, requiring zero external HTTP network calls.
4. **Frozen Strategy Invariance**: Zero modifications have been made to strategy rules (R2, R3, R5, R6, R7, R8, R9, N=20).
5. **Gate HALT-1b-M-1 Status**: Standing gate `HALT-1b-M-1` is deliberately left **UNTICKED and OPEN** pending Auditor review and formal Gate 1b approval.
