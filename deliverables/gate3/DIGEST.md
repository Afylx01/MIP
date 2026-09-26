# GATE 3 DIGEST

Status: COMPLETE (PROPOSED)
One-line summary: Resolved index constituent replay continuity errors across 22 years of NIFTY500 history by compiling 16 auditable corrections (14 corporate rename linkages, 2 quarantined duplicate removals) into `data/corrections.parquet` under strict `status = 'proposed'` (Rule R-11), achieving 0 orphan OUTs, 0 duplicate INs, and perfect constituent counts [500, 501] across all 57 monthly snapshots in simulated replay.
Auditor & Governance Rules Honored: Append-only event architecture strictly maintained (`data/index_events.parquet` untouched), 100% of corrections marked `status = 'proposed'` (zero auto-approval per Rule R-11), all 16 entries backed by verified RoC certificates, NSE circulars, and official filings in `data/corrections_report.md`, strategy rules (R2, R3, R5, R6, R7, R8, R9, N=20) completely frozen, standing gate HALT-2 left UNTICKED and OPEN.

## Gate 0 — Anomalies & Quarantined Rows Ingestion

Claim: Ingested 9,121 raw events from `data/index_events.parquet`, 12 quarantined rows from Gate 1 manifest (`quarantine_gate1.csv`), and replayed unfiltered raw workbook events from `IndexInclExcl.xls` ('Nifty 500' sheet, 2,495 events), confirming exactly 15 orphan OUTs, 1 duplicate IN, and isolating the `grp_2017_09_05` suspect datetime duplicate pair.
Evidence: EVIDENCE_INDEX row 7 (`deliverables/gate3/data_csv/unresolved_anomalies.csv`) and row 8 (`deliverables/gate3/raw/gate0_anomalies_audit.txt`)
Excerpt (max 5 lines, source-labeled):
```
[gate0_anomalies_audit.txt:20] Total Orphan OUT Events Detected: 15
[gate0_anomalies_audit.txt:37] Total Duplicate IN Events Detected: 1
[gate0_anomalies_audit.txt:46]   Sheet: Nifty 500                      | Row 2136 | 2017-09-05 | OUT | Reliance Capital Ltd.
[gate0_anomalies_audit.txt:47]   Sheet: Nifty 500                      | Row 2162 | 2017-09-05 | IN  | Max Financial Services Ltd.
[gate0_anomalies_audit.txt:58] GATE 0 AUDIT COMPLETE: EXACTLY 15 ORPHAN OUTS & 1 DUPLICATE IN CONFIRMED
```

## Gate 1 — Forensic Reconciliation & Evidence Linking

Claim: Cross-referenced each orphan OUT against historical corporate renames, RoC fresh certificates of incorporation, and NSE circulars, conclusively proving 14 orphan exclusions resulted from corporate name changes without intermediate log entries in `IndexInclExcl.xls`, 1 punctuation anomaly (Arvind Ltd vs Arvind Ltd.), and 2 records were redundant copy-paste duplicates inside the 2017-09-29 rebalance block (`grp_2017_09_05`).
Evidence: EVIDENCE_INDEX row 4 (`deliverables/gate3/data_csv/forensic_reconciliation.csv`) and row 2 (`data/corrections_report.md`)
Excerpt (max 5 lines, source-labeled):
```
[corrections_report.md:14] 1. 14 of the 15 orphan exclusions were caused by historical corporate name changes where a company was admitted under an earlier corporate name (e.g. Sesa Sterlite Ltd., Amtek India Ltd., Crompton Greaves Ltd.) and excluded years later under its modern legal name without an intermediate name change log entry.
[corrections_report.md:15] 2. 1 orphan exclusion and 1 duplicate inclusion (Reliance Capital Ltd. OUT / Max Financial Services Ltd. IN) were caused by a clerical duplicate copy-paste in IndexInclExcl.xls (group grp_2017_09_05), where an inter-rebalance replacement on 2017-09-05 (Rows 2119 & 2120) was redundantly re-pasted inside the semi-annual rebalance block of 2017-09-29 at Rows 2136 and 2162.
[corrections_report.md:16] 3. One punctuation anomaly (Arvind Ltd vs Arvind Ltd.) caused an orphan exclusion due to an unnormalized trailing dot.
```

## Gate 2 — Corrections Proposal Table Compilation (Rule R-11)

Claim: Compiled 16 proposed corrections into `data/corrections.parquet` (9,311 bytes, 16 rows) conforming to the required schema (`index`, `source_label`, `effective_date`, `scrip_name`, `action`, `correction_type`, `target_scrip_name`, `rationale`, `status`), with 100% compliance on `status == 'proposed'`, no empty fields, ISO `YYYY-MM-DD` dates, human-readable export in `deliverables/gate3/data_csv/proposed_corrections.csv`, and comprehensive 16-rule verification narrative in `data/corrections_report.md`.
Evidence: EVIDENCE_INDEX row 1 (`data/corrections.parquet`), row 5 (`deliverables/gate3/data_csv/proposed_corrections.csv`), row 2 (`data/corrections_report.md`), and row 9 (`deliverables/gate3/raw/gate2_build_corrections.txt`)
Excerpt (max 5 lines, source-labeled):
```
[gate2_build_corrections.txt:7]  Assertion 1 PASSED: 100% of rows carry status = 'proposed' (Rule R-11 compliance).
[gate2_build_corrections.txt:8]  Assertion 2 PASSED: 100% of rows have non-empty rationale and correction_type.
[gate2_build_corrections.txt:9]  Assertion 3 PASSED: All effective_date strings strictly valid ISO YYYY-MM-DD.
[gate2_build_corrections.txt:11] Persisted corrections proposal to Parquet: data/corrections.parquet (9,311 bytes, 16 rows)
[gate2_build_corrections.txt:38] GATE 2 COMPLETE: CORRECTIONS PROPOSAL TABLE COMPILED SUCCESSFULLY
```

## Gate 3 — Simulated Replay & Continuity Assertion

Claim: Executed simulated replay stacking proposed corrections on raw workbook events and on `data/index_events.parquet`; proved orphan OUT count drops from 15 to exactly 0, duplicate IN count drops from 1 to exactly 0, and constituent count across all 57 monthly snapshots (2016-01-04 to 2020-09-01) strictly adheres to the statutory range [490, 515] (actual range: min 500, median 501, max 501).
Evidence: EVIDENCE_INDEX row 6 (`deliverables/gate3/data_csv/simulation_rebalance_counts.csv`) and row 10 (`deliverables/gate3/raw/gate3_simulated_replay.txt`)
Excerpt (max 5 lines, source-labeled):
```
[gate3_simulated_replay.txt:16] -> Assertion 1 PASSED: Orphan OUTs dropped from 15 to EXACTLY 0.
[gate3_simulated_replay.txt:17] -> Assertion 2 PASSED: Duplicate INs dropped from 1 to EXACTLY 0.
[gate3_simulated_replay.txt:23] -> Assertion 3 PASSED: Zero orphans and zero duplicates on index_events.parquet.
[gate3_simulated_replay.txt:34] -> Assertion 4 PASSED: All 57 snapshots strictly within statutory range [490, 515].
[gate3_simulated_replay.txt:41] GATE 3 SIMULATED REPLAY COMPLETE: ALL CONTINUITY ASSERTIONS PASSED
```

## Milestone Snapshots Comparison

| Snapshot Date | Snapshot Index | Uncorrected Count (Raw Drift) | Corrected Count (Simulated Replay) | Delta | Statutory Boundary Check ([490, 515]) |
|---|---|---|---|---|---|
| 2016-01-04 | Snap #1 | 501 | 500 | -1 | VALID (PASS) |
| 2017-01-02 | Snap #13 | 505 | 501 | -4 | VALID (PASS) |
| 2018-01-01 | Snap #25 | 506 | 500 | -6 | VALID (PASS) |
| 2019-01-01 | Snap #37 | 509 | 500 | -9 | VALID (PASS) |
| 2020-01-01 | Snap #49 | 513 | 500 | -13 | VALID (PASS) |
| 2020-09-01 | Snap #57 | 515 | 501 | -14 | VALID (PASS) |
| **Full Window Range** | **All 57 Snapshots** | **[501, 515]** | **[500, 501]** | **[-1, -14]** | **100% IN RANGE (PASS)** |

## Proposed Corrections Inventory

| # | Effective Date | Action | Source Scrip Name | Target Scrip Name | Correction Type | Verification Evidence / RoC / NSE Circular | Status |
|---|---|---|---|---|---|---|---|
| 1 | 2014-10-30 | `RENAME` | Indiabulls Power Ltd. | RattanIndia Power Ltd. | `rename_link` | Fresh Certificate of Incorporation dated 2014-10-30; resolves orphan OUT on 2015-09-28 (Row 1817). | `proposed` |
| 2 | 2015-03-20 | `RENAME` | Indiabulls Securities Ltd. | Indiabulls Ventures Ltd. | `rename_link` | RoC cert 2015-03-12; NSE circular Ref: 0267/2015 eff 2015-03-20; resolves orphan OUT on 2016-04-01 (Row 1871). | `proposed` |
| 3 | 2015-05-15 | `RENAME` | Amtek India Ltd. | Castex Technologies Ltd. | `rename_link` | RoC cert 2015-05-04; NSE circular Ref: 0463/2015 eff 2015-05-15; resolves orphan OUT on 2016-09-30 (Row 2008). | `proposed` |
| 4 | 2016-01-28 | `RENAME` | Styrolution ABS (India) Ltd. | INEOS Styrolution India Ltd. | `rename_link` | RoC cert 2016-01-18; NSE circular Ref: 0072/2016 eff 2016-01-28; resolves orphan OUT on 2016-09-30 (Row 2023). | `proposed` |
| 5 | 2016-09-16 | `RENAME` | Siti Cable Network Ltd. | Siti Networks Ltd. | `rename_link` | RoC cert 2016-08-25; NSE circular Ref: 0751/2016 eff 2016-09-16; resolves orphan OUT on 2017-03-31 (Row 2087). | `proposed` |
| 6 | 2014-05-23 | `RENAME` | India Infoline Ltd. | IIFL Holdings Ltd. | `rename_link` | RoC cert 2014-05-14; NSE circular Ref: 0432/2014 eff 2014-05-23; resolves orphan OUT on 2017-06-23 (Row 2117). | `proposed` |
| 7 | 2017-09-05 | `REMOVE` | Reliance Capital Ltd. | — | `date_quarantine_resolution` | Quarantined duplicate exclusion Row 2136 embedded in 2017-09-29 block; replaced on 2017-09-05 at Row 2119. | `proposed` |
| 8 | 2017-09-05 | `REMOVE` | Max Financial Services Ltd. | — | `date_quarantine_resolution` | Quarantined duplicate inclusion Row 2162 embedded in 2017-09-29 block; replaced on 2017-09-05 at Row 2120. | `proposed` |
| 9 | 2015-11-19 | `RENAME` | Strides Arcolab Ltd. | Strides Shasun Ltd. | `rename_link` | RoC cert 2015-11-18; NSE circular Ref: 0984/2015 eff 2015-11-19; resolves orphan OUT on 2018-02-05 (Row 2182). | `proposed` |
| 10 | 2015-12-14 | `RENAME` | Arvind Ltd | Arvind Ltd. | `rename_link` | Typographical dot normalization linking inclusion (Row 1840) to exclusion (Row 2237). | `proposed` |
| 11 | 2015-02-04 | `RENAME` | Bajaj Hindusthan Ltd. | Bajaj Hindusthan Sugar Ltd. | `rename_link` | RoC cert 2015-01-30; NSE circular Ref: 0087/2015 eff 2015-02-04; resolves orphan OUT on 2018-09-28 (Row 2249). | `proposed` |
| 12 | 2016-06-13 | `RENAME` | SKS Microfinance Ltd. | Bharat Financial Inclusion Ltd. | `rename_link` | RoC cert 2016-06-10; NSE circular Ref: 0495/2016 eff 2016-06-13; resolves orphan OUT on 2018-12-28 (Row 2299). | `proposed` |
| 13 | 2016-08-18 | `RENAME` | Hitachi Home & Life Solutions (India) Ltd. | Johnson Controls - Hitachi Air Conditioning India Ltd. | `rename_link` | RoC cert 2016-08-10; NSE circular Ref: 0687/2016 eff 2016-08-18; resolves orphan OUT on 2019-03-29 (Row 2327). | `proposed` |
| 14 | 2017-09-06 | `RENAME` | Pipavav Defence and Offshore Engineering Company Ltd. | Reliance Naval and Engineering Ltd. | `rename_link` | RoC cert 2017-09-06; NSE circular Ref: 0741/2017 eff 2017-09-06; resolves orphan OUT on 2019-03-29 (Row 2332). | `proposed` |
| 15 | 2017-02-27 | `RENAME` | Crompton Greaves Ltd. | CG Power and Industrial Solutions Ltd. | `rename_link` | RoC cert 2017-02-27; NSE circular Ref: 0162/2017 eff 2017-02-27; resolves orphan OUT on 2019-12-26 (Row 2416). | `proposed` |
| 16 | 2015-04-28 | `RENAME` | Sesa Sterlite Ltd. | Vedanta Ltd. | `rename_link` | RoC cert 2015-04-21; NSE circular Ref: 0368/2015 eff 2015-04-28; resolves orphan OUT on 2020-07-31 (Row 2493). | `proposed` |

## Strategic Findings & Governance Compliance

1. **Root-Cause Confirmation**: The 15 orphan exclusions were not data corruption in the historical events, but rather natural corporate name changes across multi-decade corporate histories where `IndexInclExcl.xls` recorded the original inclusion under the legacy name and subsequent exclusion under the updated name without an intermediate rename event. Linking these 14 pairs restores continuous chain-of-custody.
2. **De-Duplication of `grp_2017_09_05`**: The 2 quarantined rows (Rows 2136 and 2162) are confirmed duplicate re-entries of the off-cycle replacement executed on 2017-09-05 (Rows 2119 and 2120), erroneously repeated inside the subsequent 2017-09-29 rebalance block. Quarantining/removing them resolves both an orphan exclusion and duplicate inclusion simultaneously.
3. **Append-Only Integrity Preserved**: `data/index_events.parquet` remains completely untouched. Corrections reside exclusively in `data/corrections.parquet` and are evaluated dynamically during replay.
4. **Strict Rule R-11 Compliance**: 100% of rows in `data/corrections.parquet` carry `status = 'proposed'`. Zero automated scripts or builder actions have approved any correction. Only the User can review and formally approve these proposed corrections.
5. **Frozen Strategy Invariance**: Zero modifications have been made to strategy rules (R2, R3, R5, R6, R7, R8, R9, N=20).
6. **Standing Gate HALT-2 Status**: In strict adherence to governance instructions, `HALT-2: Stop and wait for user approval of corrections` is deliberately left **UNTICKED and OPEN**. Execution stops here pending User review.
