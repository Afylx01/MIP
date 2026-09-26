# Phase 5.5 Task List: Point-in-Time Index Membership, CA Calendar & Adjuster

## Environment Context
- Device: Samsung Galaxy S23 (Termux PRoot Ubuntu Linux aarch64)
- Engine: Ubuntu system python3 with standard debian packages
- Deliverables Directory: `deliverables/halt1b_p_a2/`

## Phase 5.5 Roadmap & Gates
- [x] Gates 0, 1, 2, 2b, 2c — COMPLETE (reference only)
- [ ] HALT-1b — OPEN
- [x] A-1: Network Burst Test & Prerequisite Inventory — COMPLETE, PARTIAL
- [x] A-2 Gate 0: CA Endpoint Discovery — COMPLETE (usable NSE historical API identified)
- [x] A-2 Gate 1: CA Fetch — COMPLETE (214 splits/bonuses parsed, Parquet & Bhavcopies captured)
- [x] A-2 Gate 2: Schema and Sanity — COMPLETE (monotonic sort, 0 dups, 3 hand-checks verified)
- [x] A-2 Gate 3: Adjuster Located or Built — COMPLETE (adjust_prices.py pure function & smoke test passing)
- [x] A-2 Gate 4: Adjuster Unit Test on Real Data — COMPLETE (5 events verified on real Bhavcopies)
- [ ] HALT-1b-P-2: Auditor Review of A-2 (UNTICKED, OPEN)
- [ ] Phase 5.5.A-3: Coverage Re-measurement (not started)
- [ ] Gate 3: Corrections Proposal (`data/corrections.parquet`)
- [ ] HALT-2: Stop and wait for user approval of corrections
- [ ] Gate A: Coverage Map (post-approval)
- [ ] Gate B: Snapshot Sanity (NIFTY500 490-510 check)
- [ ] Gate C: Continuity (zero orphans/duplicates post-corrections)
- [ ] Gate D: Reconstruct, Re-Run, Price Coverage (MIP-Return-10Y comparison)
- [ ] Gate E: Round-Trip Invariance (Forward vs Backward replay)
- [ ] Gate F: Reproducibility & Truncation Clamping
