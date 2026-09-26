# Phase 5.5 Task List: Point-in-Time Index Membership & Network Viability

## Environment Context
- Device: Samsung Galaxy S23 (Termux PRoot Ubuntu Linux aarch64)
- Engine: Ubuntu system python3 with standard debian packages (no Termux python modules)
- Deliverables Directory: `deliverables/halt1b_p/`

## Phase 5.5 Roadmap & Gates
- [x] Gate 0: Inventory & Bulletin Availability (`gate0_inventory.py`) — COMPLETE (reference only)
- [x] Gate 1: Parse & Date Validation (`gate1_parse_validate.py`) — COMPLETE (reference only)
- [x] Gate 2: Initial Symbol Map & Report (`gate2_build_symbol_map.py`) — COMPLETE (reference only)
- [x] Gate 2b: Symbol Map Evidence Hardening — COMPLETE (reference only)
- [x] Gate 2c: Flag Fixes, Price-Data Audit, Backtestable-Window Report — COMPLETE (reference only)
- [ ] HALT-1b: Auditor review of Gate 2c deliverables (UNTICKED, OPEN)
- [x] Phase 5.5.A-1 Gate 0: Prerequisite Inventory (Q1–Q5) (`gate0.txt`, `gate0_inventory.py`)
- [x] Phase 5.5.A-1 Gate 1: Network Burst Test (`burst_probe.py`, `probe_content_validate.py`, `burst_log.csv`, `burst_summary.csv`)
- [ ] HALT-1b-P-1: Auditor review of Phase 5.5.A-1 (UNTICKED, OPEN)
- [ ] Phase 5.5.A-2: CA calendar + ISIN history inventory (not started)
- [ ] Phase 5.5.A-3: Coverage re-measurement (not started)
- [ ] Gate 3: Corrections Proposal (`data/corrections.parquet`)
- [ ] HALT-2: Stop and wait for user approval of corrections
- [ ] Gate A: Coverage Map (post-approval)
- [ ] Gate B: Snapshot Sanity (NIFTY500 490-510 check)
- [ ] Gate C: Continuity (zero orphans/duplicates post-corrections)
- [ ] Gate D: Reconstruct, Re-Run, Price Coverage (MIP-Return-10Y comparison)
- [ ] Gate E: Round-Trip Invariance (Forward vs Backward replay)
- [ ] Gate F: Reproducibility & Truncation Clamping
