# NEXT TASK: PHASE 5.5 GATES A & B BUILD PROMPT — COVERAGE MAP & SNAPSHOT SANITY

**Prior Phase**: Phase 5.5 Gate 3 (Status: **ACCEPT_WITH_CONDITIONS**, 16 proposed corrections in `data/corrections.parquet`, simulated replay proves 0 orphan OUTs, 0 duplicate INs, [500, 501] constituent range)  
**Target Phase**: Phase 5.5 Gates A & B (Coverage Map Post-Approval & Snapshot Sanity)  
**Deliverables Directory**: `deliverables/gate_ab/`  
**Standing Gate**: **HALT-3** (Blocks on completion of Gate B before Gate C / Gate D)  
**Workspace Root**: `/storage/emulated/0/Documents/Project MIP`  
**Execution Environment**: Samsung Galaxy S23, PRoot Ubuntu Linux (`/usr/bin/python3.12`), apt-managed packages  

---

## 0. MANDATE & STRATEGIC CONTEXT

With Gate 3 having forensically linked all 14 corporate renames and resolved the 2 quarantined `grp_2017_09_05` duplicates in `data/corrections.parquet`, and the user having formally approved the corrections, **HALT-2 is resolved**.

You are now the **builder** for Phase 5.5 Gates A & B. Your mandate is to execute the post-approval coverage mapping (Gate A) and formal point-in-time constituent snapshot sanity replay (Gate B) on the NIFTY500 index.

### Non-Negotiable Constraints:
1. **Append-Only Architecture**: `data/index_events.parquet` remains permanently unaltered. Corrections from `data/corrections.parquet` are layered dynamically on top during replay.
2. **Approved Data Sources Only**:
   - `data/corrections.parquet` must have `status == 'approved'` for active replay.
   - `data/symbol_map.parquet` mappings with `status in {'auto', 'approved'}` are active.
3. **No Strategy Tuning**: Strategy parameters and backtest rules (R2, R3, R5, R6, R7, R8, R9, $N=20$) remain strictly frozen.
4. **Reproducibility & Evidence Structure**:
   - Maintain the standard deliverable format: `deliverables/gate_ab/DIGEST.md` and `deliverables/gate_ab/EVIDENCE_INDEX.tsv`.
   - Log all terminal outputs verbatim into `deliverables/gate_ab/raw/`.

---

## 1. ACCEPTANCE CRITERIA

### Gate A (Coverage Map):
- **Resolved Fraction**: $\ge 80.0\%$ on all 57 monthly snapshots (2016-01-04 to 2020-09-01).
- **Joint Coverage**: Median $\ge 85.0\%$ across all 57 monthly snapshots.
- **Blocked Events**: Zero blocked events for approved scrips.

### Gate B (Snapshot Sanity):
- **Constituent Count**: Strictly within statutory range $[490, 515]$ across all 57 monthly snapshots (expected $[500, 501]$).
- **Continuity**: Exactly **0 orphan OUTs** and **0 duplicate INs** across entire 22-year event log.

---

## 2. EXECUTION GATES

### Gate 0: Active Dataset Audit & Prerequisite Check
- Verify that `data/corrections.parquet` has been transitioned to `status == 'approved'` pursuant to user approval under HALT-2.
- Verify `data/symbol_map.parquet` contains 571 `auto` + 192 `approved` scrips.
- Verify price dataset `data/verification/halt1b_m1/adjusted_bhavcopy_bars_v2.parquet` (753,046 bars across 711 symbols) is present and accessible.
- Output: `deliverables/gate_ab/raw/gate0_prerequisites.txt`.

### Gate 1: Gate A — Post-Approval Coverage Map Execution
- Recompute point-in-time coverage metrics for all 57 monthly rebalance snapshots:
  1. Unblocked constituent count.
  2. Resolved constituent count (`status in {'auto', 'approved'}`).
  3. Resolved fraction ($\frac{\text{Resolved}}{\text{Unblocked}}$).
  4. Price-covered constituent count (presence of valid adjusted Bhavcopy bar).
  5. Unflagged constituent count.
  6. Joint coverage count and percentage.
- Assert:
  - Resolved fraction $\ge 80.0\%$ on 100% of snapshots (Standing Rule R-5 compliance).
  - Median joint coverage $\ge 85.0\%$ (PASS).
  - Blocked events drop to 0 for approved scrips.
- Output: `deliverables/gate_ab/raw/gate1_coverage_map.txt` and `deliverables/gate_ab/data_csv/gate_a_coverage_map.csv`.

### Gate 2: Gate B — Chronological Snapshot Sanity Replay
- Execute chronological forward replay from `1998-08-01` seed batch through `2020-09-14` applying `data/corrections.parquet` on top of `data/index_events.parquet`.
- Assertions:
  - Orphan OUT count across full history == **0**.
  - Duplicate IN count across full history == **0**.
  - Constituent count on every monthly snapshot is within $[490, 515]$.
- Export complete constituent lists for all 57 snapshots: `deliverables/gate_ab/data_csv/snapshot_constituents_57.csv`.
- Output: `deliverables/gate_ab/raw/gate2_snapshot_sanity.txt`.

### Gate 3: Deliverables Compilation & HALT-3
- Compile deliverables:
  - `deliverables/gate_ab/DIGEST.md`: Gate-by-gate findings, metrics, and evidence pointers.
  - `deliverables/gate_ab/EVIDENCE_INDEX.tsv`: Complete manifest of all files with SHA-256 hashes and byte counts.
  - Update `task_list.md`: Tick Gate A and Gate B; leave **HALT-3 UNTICKED and OPEN**.
  - Dispatch Telegram completion alert using `telegram-notify`.
- **HALT-3 IS OPEN**: Cease execution and notify the Auditor. Await auditor review before proceeding to Gate C (continuity audit) and Gate D (re-run backtest).
