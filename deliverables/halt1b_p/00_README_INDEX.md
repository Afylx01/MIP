# Deliverables Index (`00_README_INDEX.md`)
**Phase 5.5.A-1: Network Viability Burst Test & Prerequisite Inventory**

| Path | Description | Supported Gate / Claim |
|---|---|---|
| `00_README_INDEX.md` | Manifest and index of all deliverables in `deliverables/halt1b_p/` | Standing Deliverables Rule |
| `01_verification.md` | Comprehensive verification report for Gate 0 (Q1–Q5) and Gate 1 burst test | All Gates & Standing Deliverables Rule |
| `SHA256SUMS.txt` | Cryptographic SHA-256 hashes of every file in `deliverables/halt1b_p/` | Integrity Verification |
| `task_list.md` | Updated Phase 5.5 roadmap with Gate 0 and Gate 1 ticked; HALT-1b-P-1 unticked | Task List Protocol |
| `raw_outputs/gate0.txt` | Complete verbatim terminal stdout of `scripts/gate0_inventory.py` | Gate 0 Verification (Q1–Q5) |
| `raw_outputs/gate1.txt` | Complete verbatim terminal stdout of 30-request burst runner `scripts/burst_probe.py` | Gate 1 Burst Execution |
| `raw_outputs/gate1_probe.txt` | Complete verbatim terminal stdout of `scripts/probe_content_validate.py` | Gate 1 Content Validation |
| `scripts/gate0_inventory.py` | Full source script executing Gate 0 prerequisite disk inventory | Gate 0 Source Code |
| `scripts/burst_probe.py` | Full source script executing 30-request rate-limited burst probe | Gate 1 Source Code |
| `scripts/probe_content_validate.py` | Full source script validating response payload contents, delisted greps, and spot checks | Gate 1 Source Code |
| `data_csv/burst_summary.csv` | Summary table by (pattern, year) cell with requests sent, 200s, latencies, and valid counts | Gate 1 Summary Table |
| `samples/burst_log.csv` | Exact per-request log table (30 rows) with sequence, latency, status code, bytes, and errors | Gate 1 Per-Request Logging |
| `samples/probe/csv_zip_20160208.zip` | Raw downloaded Bhavcopy archive for 2016-02-08 | Gate 1 Payload Proof (2016) |
| `samples/probe/csv_zip_20160422.zip` | Raw downloaded Bhavcopy archive for 2016-04-22 | Gate 1 Payload Proof (2016) |
| `samples/probe/csv_zip_20160615.zip` | Raw downloaded Bhavcopy archive for 2016-06-15 (used for spot check) | Gate 1 Spot Check & 2016 Proof |
| `samples/probe/csv_zip_20160909.zip` | Raw downloaded Bhavcopy archive for 2016-09-09 | Gate 1 Payload Proof (2016) |
| `samples/probe/csv_zip_20161123.zip` | Raw downloaded Bhavcopy archive for 2016-11-23 | Gate 1 Payload Proof (2016) |
| `samples/probe/csv_zip_20180206.zip` | Raw downloaded Bhavcopy archive for 2018-02-06 | Gate 1 Payload Proof (2018) |
| `samples/probe/csv_zip_20180420.zip` | Raw downloaded Bhavcopy archive for 2018-04-20 | Gate 1 Payload Proof (2018) |
| `samples/probe/csv_zip_20180629.zip` | Raw downloaded Bhavcopy archive for 2018-06-29 | Gate 1 Payload Proof (2018) |
| `samples/probe/csv_zip_20180910.zip` | Raw downloaded Bhavcopy archive for 2018-09-10 | Gate 1 Payload Proof (2018) |
| `samples/probe/csv_zip_20181126.zip` | Raw downloaded Bhavcopy archive for 2018-11-26 | Gate 1 Payload Proof (2018) |
| `samples/probe/csv_zip_20200205.zip` | Raw downloaded Bhavcopy archive for 2020-02-05 | Gate 1 Payload Proof (2020) |
| `samples/probe/csv_zip_20200423.zip` | Raw downloaded Bhavcopy archive for 2020-04-23 | Gate 1 Payload Proof (2020) |
| `samples/probe/csv_zip_20200706.zip` | Raw downloaded Bhavcopy archive for 2020-07-06 | Gate 1 Payload Proof (2020) |
| `samples/probe/csv_zip_20200914.zip` | Raw downloaded Bhavcopy archive for 2020-09-14 | Gate 1 Payload Proof (2020) |
| `samples/probe/csv_zip_20201125.zip` | Raw downloaded Bhavcopy archive for 2020-11-25 | Gate 1 Payload Proof (2020) |
| `samples/probe/sec_bhavdata_20200205.csv` | Raw downloaded sec_bhavdata CSV for 2020-02-05 | Gate 1 Payload Proof (2020 sec) |
| `samples/probe/sec_bhavdata_20200423.csv` | Raw downloaded sec_bhavdata CSV for 2020-04-23 | Gate 1 Payload Proof (2020 sec) |
| `samples/probe/sec_bhavdata_20200706.csv` | Raw downloaded sec_bhavdata CSV for 2020-07-06 | Gate 1 Payload Proof (2020 sec) |
| `samples/probe/sec_bhavdata_20200914.csv` | Raw downloaded sec_bhavdata CSV for 2020-09-14 | Gate 1 Payload Proof (2020 sec) |
| `samples/probe/sec_bhavdata_20201125.csv` | Raw downloaded sec_bhavdata CSV for 2020-11-25 | Gate 1 Payload Proof (2020 sec) |
