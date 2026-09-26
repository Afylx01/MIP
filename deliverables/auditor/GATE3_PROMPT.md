# NEXT TASK: PHASE 5.5 GATE 3 BUILD PROMPT — INDEX EVENT CORRECTIONS PROPOSAL & QUARANTINED ROWS

**Prior Phase**: Phase 5.5.M-1 (Status: **ACCEPT_WITH_CONDITIONS**, median joint coverage 86.25% clearing the $\ge 85.0\%$ PASS threshold)  
**Target Phase**: Phase 5.5 Gate 3 (Corrections Proposal)  
**Deliverables Directory**: `deliverables/gate3/`  
**Standing Gate**: **HALT-2** (Blocks on completion of Gate 3)  
**Workspace Root**: `/storage/emulated/0/Documents/Project MIP`  
**Execution Environment**: Samsung Galaxy S23, PRoot Ubuntu Linux (`/usr/bin/python3.12`), apt-managed packages  

---

## 0. MANDATE & STRATEGIC CONTEXT

With Phase 5.5.M-1 having successfully achieved **86.25% median joint coverage** on point-in-time adjusted Bhavcopy prices, **HALT-1b is resolved**.

You are now the **builder** for Phase 5.5 Gate 3. Your mandate is to resolve index constituent replay continuity errors (the 15 orphan OUTs, 1 duplicate IN, and the quarantined `grp_2017_09_05` suspect datetime rows identified during Gates 1 and 2c) by constructing a clean, auditable corrections proposal in `data/corrections.parquet`.

### Non-Negotiable Constraints:
1. **Append-Only Event Architecture**:
   - Never modify or delete raw rows in `data/index_events.parquet`.
   - All corrections live in `data/corrections.parquet` and are applied dynamically on top during replay.
2. **Strict Status Constraint (Standing Rule R-11)**:
   - You may write **ONLY** `status = 'proposed'`.
   - You do NOT approve corrections. Only the user approves (`status = 'approved'`) or rejects. Your scripts must never auto-approve.
3. **No Strategy Tuning**: Strategy parameters and backtest rules (R2, R3, R5, R6, R7, R8, R9, $N=20$) remain strictly frozen.
4. **Reproducibility & Evidence Structure**:
   - Maintain the standard deliverable format: `deliverables/gate3/DIGEST.md` and `deliverables/gate3/EVIDENCE_INDEX.tsv`.
   - Log all terminal outputs verbatim into `deliverables/gate3/raw/`.

---

## 1. DATA SCHEMA FOR CORRECTIONS

`data/corrections.parquet` must conform to the following schema:
- `index`: Name of the index (e.g. `NIFTY500`)
- `source_label`: Original source sheet label
- `effective_date`: `YYYY-MM-DD` string or datetime
- `scrip_name`: Normalized constituent company name
- `action`: `IN` | `OUT` | `RENAME` | `REMOVE`
- `correction_type`: `orphan_out_resolution` | `duplicate_in_resolution` | `date_quarantine_resolution` | `rename_link`
- `target_scrip_name`: Target company name (for renames/mergers)
- `rationale`: Verifiable historical explanation citing exchange notices, corporate renames, or circular numbers
- `status`: Strictly `'proposed'`

---

## 2. EXECUTION GATES

### Gate 0: Anomalies & Quarantined Rows Ingestion
- Ingest `data/index_events.parquet` (9,121 raw events) and `deliverables/gate_2c/data_csv/quarantine_gate1.csv`.
- Replay unblocked NIFTY500 membership from `1998-08-01` seed batch through `2020-09-14`.
- Isolate and output the exact list of:
  - 15 orphan OUT events (stocks excluded without prior recorded inclusion).
  - 1 duplicate IN event.
  - Quarantined `grp_2017_09_05` suspect datetime rows (e.g. Reliance Capital exclusion vs Max Financial Services inclusion).
- Output: `deliverables/gate3/raw/gate0_anomalies_audit.txt` and `deliverables/gate3/data_csv/unresolved_anomalies.csv`.

### Gate 1: Forensic Reconciliation & Evidence Linking
- Cross-reference each orphan OUT against historical corporate renames in `data/symbol_map.parquet` and exchange circulars.
- Identify pairs where an OUT occurred under a new/old name without an explicit change log event in `IndexInclExcl.xls`.
- Document each finding with verified corporate action evidence (e.g. merger of entity A into entity B, or ticker rename).
- Output: `deliverables/gate3/data_csv/forensic_reconciliation.csv`.

### Gate 2: Corrections Proposal Table Compilation
- Compile all proposed adjustments into `data/corrections.parquet`.
- Enforce:
  - `status == 'proposed'` on 100% of rows.
  - No empty `rationale` or `correction_type`.
  - Date format consistency (`YYYY-MM-DD`).
- Also export human-readable CSV: `deliverables/gate3/data_csv/proposed_corrections.csv` and comprehensive narrative report: `data/corrections_report.md`.
- Output: `deliverables/gate3/raw/gate2_build_corrections.txt`.

### Gate 3: Simulated Replay & Continuity Assertion
- Build a test replay engine that stacks `data/corrections.parquet` (treating `status == 'proposed'` as active for simulation only) on top of `data/index_events.parquet`.
- Assertions:
  - Orphan OUT count drops to **0**.
  - Duplicate IN count drops to **0**.
  - NIFTY500 constituent count on all monthly rebalance dates stays within the valid range $[490, 515]$.
- Output: `deliverables/gate3/raw/gate3_simulated_replay.txt` and `deliverables/gate3/data_csv/simulation_rebalance_counts.csv`.

### Gate 4: Deliverables Bundle Compilation & HALT-2
- Compile deliverables:
  - `deliverables/gate3/DIGEST.md`: Gate-by-gate findings, metrics, and evidence pointers.
  - `deliverables/gate3/EVIDENCE_INDEX.tsv`: Complete manifest of all files with SHA-256 hashes and byte counts.
  - Update `task_list.md`: Tick Gate 3 as proposed; leave **HALT-2 UNTICKED and OPEN**.
  - Dispatch Telegram completion notification using `telegram-notify`.
- **HALT-2 IS OPEN**: Cease execution and notify the Auditor and User. Await user review and formal approval of corrections before proceeding to Gate A.
