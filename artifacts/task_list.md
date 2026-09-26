# Phase 5.5 Task List: Point-in-Time Index Membership

## Environment Context
- Device: Samsung Galaxy S23 (Termux PRoot Ubuntu Linux aarch64)
- Engine: Ubuntu system python3 with standard debian packages (no Termux python modules)
- Deliverables Directory: `deliverables/gate_2c/`

## Phase 5.5 Roadmap & Gates
- [x] Gate 0: Inventory & Bulletin Availability (`gate0_inventory.py`)
- [x] Gate 1: Parse & Date Validation (`gate1_parse_validate.py`)
- [x] Gate 2: Initial Symbol Map & Report (`gate2_build_symbol_map.py`)
- [x] Gate 2b: Symbol Map Evidence Hardening (S1–S6 screens, price loading, review tooling)
- [x] Gate 2c: Flag Fixes, Price-Data Audit, Backtestable-Window Report
  - [x] Step 1: Fix the Match Flags (`symbol_map_v2b.csv`, `symbol_map_v3.csv`, `canaries_2c.csv`, `step1_v3_rebuild.py`, `raw_outputs/step1.txt`)
  - [x] Step 2: Price Cache Reconciliation (`price_symbol_summary.csv`, `raw_rows_INFY.csv`, `ohlc_anomalies.csv`, `step2_price_reconciliation.py`, `raw_outputs/step2.txt`)
  - [x] Step 3: Backtestable-Window Report (`window_fractions.csv`, `step3_backtestable_window.py`, `raw_outputs/step3.txt`)
  - [x] Step 4: Gate 1 Clean-Up (`divopp_2017_rows.csv`, `quarantine_gate1.csv`, `step4_gate1_cleanup.py`, `raw_outputs/step4.txt`)
  - [x] Step 5: Data-Source Reachability Probe (`samples/probe/`, `step5_data_source_probe.py`, `raw_outputs/step5.txt`)
  - [x] Step 6: Read-Only Safety Verification
  - [x] Step 7: Packaging Deliverables (`00_README_INDEX.md`, `01_verification.md`, `SHA256SUMS.txt`, `task_list.md`)
- [ ] HALT-1b: Stop and wait for user review of Gate 2c deliverables (UNTICKED)
- [ ] Gate 3: Corrections Proposal (`data/corrections.parquet`)
- [ ] HALT-2: Stop and wait for user approval of corrections
- [ ] Gate A: Coverage Map (post-approval)
- [ ] Gate B: Snapshot Sanity (NIFTY500 490-510 check)
- [ ] Gate C: Continuity (zero orphans/duplicates post-corrections)
- [ ] Gate D: Reconstruct, Re-Run, Price Coverage (MIP-Return-10Y comparison)
- [ ] Gate E: Round-Trip Invariance (Forward vs Backward replay)
- [ ] Gate F: Reproducibility & Truncation Clamping
