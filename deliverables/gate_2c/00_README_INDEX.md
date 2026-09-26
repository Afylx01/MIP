# Gate 2c Deliverables Index (`00_README_INDEX.md`)

This index lists every file in `deliverables/gate_2c/`, explaining what it is and which step or claim it supports.

| Path | Description | Supported Step / Claim |
|---|---|---|
| `00_README_INDEX.md` | Manifest and index of all deliverables in `deliverables/gate_2c/` | Standing Deliverables Rule |
| `01_verification.md` | Comprehensive verification report containing commands, raw outputs, code, and findings | All Steps (1–7) & Standing Deliverables Rule |
| `SHA256SUMS.txt` | Cryptographic SHA-256 hashes of every deliverable file and input source file | Standing Deliverables Rule & Integrity Verification |
| `task_list.md` | Full Phase 5.5 roadmap with Gate 2c steps ticked and HALT-1b unticked | Step 7 (Task List Management) |
| `data_csv/symbol_map_v2b.csv` | Full CSV export of the Gate 2b symbol map before v3 reconstruction (1,448 rows) | Step 1.6 (Before/after comparison & archival) |
| `data_csv/symbol_map_v3.csv` | Full CSV export of the rebuilt Gate 2c v3 symbol map with decoupled statuses (1,448 rows) | Step 1.5, 1.6 (Mapping & price status separation) |
| `data_csv/canaries_2c.csv` | Regression test results for all 22 canaries under v3 rules (all remain non-auto) | Step 1.6 (Canary non-regression verification) |
| `data_csv/price_symbol_summary.csv` | Per-symbol price cache audit (first bar, last bar, bar count, missing vs calendar) | Step 2.1 (Row count reconciliation: 750 * 2883 vs 1.83M) |
| `data_csv/window_fractions.csv` | Monthly snapshot evaluation of NIFTY500 membership (mapped, covered, both fractions) | Step 3.2 (Point-in-time backtestable window report) |
| `data_csv/quarantine_gate1.csv` | Grouped suspect datetime records (`grp_2017_09_05`) across 6 index sheets (12 rows) | Step 4.2 (Gate 1 rebalance anomaly grouping) |
| `samples/raw_rows_INFY.csv` | 5 sample raw price rows for INFY demonstrating floating-point precision (>2 decimals) | Step 2.5 (Decimals audit: 97.5% closes > 2 decimals) |
| `samples/ohlc_anomalies.csv` | Full audit export of price anomalies: 3 `High < Low` and 60 `High < Close` rows | Step 2.6 (Price data quality screening) |
| `samples/divopp_2017_rows.csv` | Raw rows 124–134 of `Nifty Dividend Opportunities 50` proving strict chronological order | Step 4.1 (Gate 1 order & duplicate audit) |
| `samples/probe/cm02JAN2008bhav.csv.zip` | Downloaded official NSE Bhavcopy zip archive for 2008-01-02 from `nsearchives` | Step 5.1, 5.2 (2008 historical reachability proof) |
| `samples/probe/cm02JAN2015bhav.csv.zip` | Downloaded official NSE Bhavcopy zip archive for 2015-01-02 containing delisted stocks | Step 5.1, 5.2, 5.3 (2015 reachability & delisted coverage) |
| `samples/probe/cm14SEP2020bhav.csv.zip` | Downloaded official NSE Bhavcopy zip archive for 2020-09-14 (`covered_end`) | Step 5.1, 5.2 (2020 reachability proof) |
| `samples/probe/sec_bhavdata_full_14092020.csv` | Downloaded modern security Bhavdata CSV for 2020-09-14 | Step 5.1, 5.2 (Alternative URL pattern reachability) |
| `raw_outputs/step1.txt` | Complete verbatim terminal stdout/stderr for Step 1 v3 symbol map rebuild & unit tests | Step 1 Verification |
| `raw_outputs/step2.txt` | Complete verbatim terminal stdout/stderr for Step 2 price cache reconciliation & audit | Step 2 Verification |
| `raw_outputs/step3.txt` | Complete verbatim terminal stdout/stderr for Step 3 backtestable-window report | Step 3 Verification |
| `raw_outputs/step4.txt` | Complete verbatim terminal stdout/stderr for Step 4 Gate 1 clean-up & free-float counts | Step 4 Verification |
| `raw_outputs/step5.txt` | Complete verbatim terminal stdout/stderr for Step 5 data-source reachability probe | Step 5 Verification |
| `scripts/step1_v3_rebuild.py` | Complete runnable Python script executing Step 1 (flags fix, intervals, v3 rebuild) | Step 1 Execution Source |
| `scripts/step2_price_reconciliation.py` | Complete runnable Python script executing Step 2 (reconciliation, splits, decimals) | Step 2 Execution Source |
| `scripts/step3_backtestable_window.py` | Complete runnable Python script executing Step 3 (backtestable window & disclosure) | Step 3 Execution Source |
| `scripts/step4_gate1_cleanup.py` | Complete runnable Python script executing Step 4 (Div Opp audit, quarantine grouping) | Step 4 Execution Source |
| `scripts/step5_data_source_probe.py` | Complete runnable Python script executing Step 5 (rate-limited archive probe) | Step 5 Execution Source |
| `scripts/gate1_parse_validate.py` | Full reference source of the Gate 1 parser and date validation script | Step 4 Reference Source |
| `scripts/gate2_build_symbol_map.py` | Full reference source of the Gate 2 / 2b symbol map builder | Step 1 Reference Source |
| `scripts/gate0_inventory.py` | Full reference source of the Gate 0 bulletin inventory script | Step 4 Reference Source |
| `scripts/step0_price_inventory.py` | Full reference source of the Step 0 price cache inventory and loader | Step 2 Reference Source |
