# NEXT TASK: PHASE 5.5 GATES E & F BUILD PROMPT — ROUND-TRIP INVARIANCE & TRUNCATION BEHAVIOR

**Prior Phase**: Phase 5.5 Gates C & D (Status: **ACCEPT**, NIFTY500 0 orphans/duplicates, 0 blocked events, start 500 / end 501, Run a CAGR 16.62% vs Run b CAGR 12.92%, delta -3.70 pp, accounting identity residual 0.00, reproducibility byte-identical)  
**Target Phase**: Phase 5.5 Gates E & F (Round-Trip Invariance, Reproducibility & Truncation Clamping)  
**Deliverables Directory**: `deliverables/gate_ef/`  
**Standing Gate**: **HALT-5** (Mandatory pause for Auditor review of Gates E & F deliverables)  
**Workspace Root**: `/storage/emulated/0/Documents/Project MIP`  
**Execution Environment**: Samsung Galaxy S23, PRoot Ubuntu Linux (`/usr/bin/python3`), apt-managed packages  

---

## 0. MANDATE & STRATEGIC CONTEXT

With Gates C and D fully verified and accepted by the Auditor, **HALT-4 is CLEARED**.

You are now the **builder** for Phase 5.5 Gates E & F. Your mandate is:
1. **Gate E**: Round-trip invariance testing (no network):
   - Using a fixed RNG seed (e.g. `seed = 42`, print it), pick three snapshot dates across the full 22-year range.
   - For each date, compute NIFTY500 membership two independent ways:
     * (1) Forward chronological replay from the 1998-08-01 seed batch.
     * (2) Backward chronological replay from the `covered_end` (2020-09-14) snapshot.
   - Prove the forward and backward constituent sets are 100% identical.
   - Export full membership manifests to `data/verification/membership_<date>.txt`.
   - Step-transition test at `covered_end`: Take snapshot the day before `covered_end`, apply `covered_end` events, and prove resulting set equals the snapshot at `covered_end`.
2. **Gate F**: Reproducibility, Truncation & Clamping Verification (no network):
   - Dual execution of the Gate D (b) point-in-time dynamic backtest: verify byte-identical output and compute SHA-256 hashes of each output file.
   - Truncation clamping test: Request an end date beyond `covered_end` (e.g. `2024-01-01` or `2026-08-31`). Verify that the engine strictly clamps to `2020-09-14`, prints the mandatory truncation warning and `Universe coverage` line, and does not silently extend membership.
   - `run_date` invariance test: Change `run_date` only and confirm results before `covered_end` are 100% unchanged.

---

## 1. NON-NEGOTIABLE CONSTRAINTS & AUDITOR RULES

1. **Append-Only Integrity**: `data/index_events.parquet` must remain 100% unaltered. Approved corrections in `data/corrections.parquet` are layered dynamically during universe reconstruction.
2. **Zero Network Calls**: All replay, symbol mapping, indicator computation, and backtesting must run strictly offline against cached local parquet/txt data.
3. **Mathematical Identity (Standing Rule R-3)**:
   Every backtest execution must satisfy:
   $$\text{initial\_capital} + \text{realized\_pnl} - \text{tax} + \text{dividends} + \text{unrealized\_pnl} == \text{final\_value}$$
   with residual **exactly 0.00**.
4. **Reproducibility (Standing Rule R-6)**:
   Every test must be executed twice, diffed, and proven byte-identical.
5. **Coverage Disclosure (Standing Rule R-5)**:
   Disclose the exact point-in-time coverage line for Run (b) (`median joint coverage 87.03%`).

---

## 2. ACCEPTANCE CRITERIA

### Gate E (Round-Trip Invariance):
1. **Three-Date Invariance**:
   - Fixed RNG seed chosen and printed.
   - Three distinct dates across the range selected.
   - For all three dates: $\text{Forward Replay Set} \equiv \text{Backward Replay Set}$.
   - Save sets to `data/verification/membership_<date>.txt`.
2. **Final Event Step Invariance**:
   - Take constituent set on the day immediately preceding `covered_end` (`2020-09-13`).
   - Apply effective events dated `2020-09-14`.
   - Prove resulting set strictly equals snapshot at `2020-09-14`.
   - Print applied events in full.
3. **Reproducibility**:
   - Every snapshot reproducible from `data/index_events.parquet`, `data/symbol_map.parquet`, and approved `data/corrections.parquet` alone.

### Gate F (Reproducibility & Truncation Clamping):
1. **Backtest Reproducibility**:
   - Run Gate D (b) backtest twice.
   - SHA-256 hashes of both runs match 100% (byte-identical).
2. **Post-2020 Truncation Clamping**:
   - Request end date beyond `covered_end` (e.g. `2022-12-31`).
   - Confirm run clamps cleanly to `2020-09-14`.
   - Confirm console prints warning and `Universe coverage: 1998-08-01 to 2020-09-14`.
   - Confirm constituent count does not drift or extend.
3. **Run-Date Invariance**:
   - Re-run backtest with alternate `run_date`; assert all historical results prior to `covered_end` are identical.

---

## 3. EXECUTION STEPS & SCRIPTS

### Step 1: Gate E — Round-Trip Invariance Script
- Script: `deliverables/gate_ef/scripts/gate_e_roundtrip.py`
- Ingest `data/index_events.parquet` and approved `data/corrections.parquet`.
- Implement forward replay and backward replay from `covered_end`.
- Export:
  - `data/verification/membership_<date1>.txt`
  - `data/verification/membership_<date2>.txt`
  - `data/verification/membership_<date3>.txt`
  - `deliverables/gate_ef/data_csv/gate_e_roundtrip_summary.csv`
  - `deliverables/gate_ef/raw/gate_e_roundtrip.txt`

### Step 2: Gate F — Reproducibility & Clamping Script
- Script: `deliverables/gate_ef/scripts/gate_f_clamping.py`
- Execute Gate D (b) backtest twice; verify identical SHA-256 hashes.
- Test post-2020 request and confirm clamping + warning banner.
- Test `run_date` perturbation and assert invariance.
- Export:
  - `deliverables/gate_ef/data_csv/gate_f_clamping_summary.csv`
  - `deliverables/gate_ef/raw/gate_f_clamping.txt`

### Step 3: Deliverables Compilation & HALT-5
- Script: `deliverables/gate_ef/scripts/generate_evidence_index.py`
- Compile:
  - `deliverables/gate_ef/DIGEST.md`
  - `deliverables/gate_ef/EVIDENCE_INDEX.tsv`
  - `deliverables/gate_ef/task_list.md`: Tick Gate E and Gate F; leave **HALT-5 UNTICKED and OPEN**.
- Package `artifacts/gate_ef_deliverables.zip` and generate `SHA256SUMS.txt`.
- Dispatch Telegram alert via `/usr/local/bin/telegram-notify`.
- **HALT-5 MANDATORY PAUSE**: Cease execution and notify the Auditor. Await formal ruling.
