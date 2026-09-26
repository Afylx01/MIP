# NEXT TASK: PHASE 5.5 GATES E & F BUILD PROMPT — ROUND-TRIP REPLAY & REPRODUCIBILITY/TRUNCATION AUDIT

**Prior Phase**: Phase 5.5 Gates C & D (Status: **ACCEPT**, multi-index continuity verified, universe reconstruction 500 start / 501 end, comparative backtest re-run proves -3.70 pp survivorship bias premium, Rule R-3 residual 0.00, Rule R-6 byte-identical)  
**Target Phase**: Phase 5.5 Gates E & F (Round-Trip Snapshot Replay & Reproducibility / Truncation Audit)  
**Deliverables Directory**: `deliverables/gate_ef/`  
**Standing Gate**: **HALT-5** (Mandatory pause for final Auditor sign-off on Phase 5.5 before Phase 5.6)  
**Workspace Root**: `/storage/emulated/0/Documents/Project MIP`  
**Execution Environment**: Samsung Galaxy S23, PRoot Ubuntu Linux (`/usr/bin/python3`), apt-managed packages  

---

## 0. MANDATE & STRATEGIC CONTEXT

With Gates C and D fully verified and accepted by the Auditor, **HALT-4 is CLEARED**.

You are now the **builder** for Phase 5.5 Gates E & F. Your mandate is:
1. **Gate E (Round-Trip Bi-Directional Replay)**:
   - Prove mathematical equivalence between forward replay and backward replay on 3 random dates across the 22-year event log.
   - Prove end-boundary continuity on `covered_end` (`2020-09-14`).
   - Prove zero network dependencies (standalone reproducibility from `data/index_events.parquet`, `data/corrections.parquet`, and `data/symbol_map.parquet` alone).
2. **Gate F (Reproducibility & Truncation Invariants)**:
   - Demonstrate byte-identical reproducibility across backtest runs with SHA-256 output verification.
   - Demonstrate automatic date clamping and warning emission when an end date beyond `covered_end` is requested.
   - Demonstrate run-date invariance (changing `run_date` does not alter historical results before `covered_end`).
3. **Phase 5.5 Final Milestone Compilation**:
   - Deliver the complete Gate E & F artifacts in `deliverables/gate_ef/`.
   - Update README and documentation for Phase 5.5 sign-off.
   - Hold standing gate **HALT-5** open for final Auditor inspection.

---

## 1. NON-NEGOTIABLE CONSTRAINTS & AUDITOR RULES

1. **Zero Network Calls**: All replay, reconstruction, and backtest operations must run 100% offline from local parquet/csv files.
2. **Deterministic Replay (Standing Rule R-2)**:
   - Fixed RNG seed specified in code/config (print the seed explicitly).
   - The membership sets computed via forward replay and backward replay must be **set-identical** (symmetric difference == $\emptyset$).
3. **Append-Only Architecture (Standing Rule R-1)**:
   - `data/index_events.parquet` must remain permanently unaltered (exact 9,121 rows, SHA256 `7a15cfae...`).
4. **Boundary Invariants (Standing Rule R-4)**:
   - Requesting a snapshot beyond `covered_end` (`2020-09-14`) must clamp to `covered_end` and print a clear warning header.
   - Membership must not be artificially extended past `covered_end`.

---

## 2. ACCEPTANCE CRITERIA

### Gate E (Round-Trip Snapshot Replay):
1. **Three-Date Random Round-Trip**:
   - Use a fixed RNG seed (e.g., `seed = 42`) to deterministically sample 3 dates across the 1998–2020 history (e.g., one early, one mid, one late).
   - For each sample date:
     * Compute membership via **Forward Replay** from the 1998-08-01 seed batch.
     * Compute membership via **Backward Replay** from the 2020-09-14 `covered_end` snapshot (reversing `IN` and `OUT` events).
     * Assert: $\text{ForwardSet} \equiv \text{BackwardSet}$ (set difference == 0).
     * Export membership manifests to `data/verification/membership_<date>.txt`.
2. **End-Boundary Continuity**:
   - Take the membership set as of the day before `covered_end` (`2020-09-13`).
   - Apply the events effective on `2020-09-14`.
   - Assert the resulting set strictly equals the snapshot at `covered_end` (501 constituents).
   - Print the exact events applied.

### Gate F (Reproducibility & Truncation Invariants):
1. **Byte-Identical Backtest Reproducibility**:
   - Run the Gate D (b) point-in-time backtest twice under the same configuration.
   - Save output metrics and trade logs to `deliverables/gate_ef/raw/gate_f_run_pass1.txt` and `gate_f_run_pass2.txt`.
   - Compute SHA-256 hashes of both files and assert they are **bit-for-bit identical**.
2. **Out-of-Bounds Clamping & Warning**:
   - Request a backtest or universe snapshot with end date `2021-01-01` (beyond `covered_end` `2020-09-14`).
   - Verify that the engine automatically clamps to `2020-09-14`, emits the standard truncation warning, and does not invent or extend constituent membership.
3. **Run-Date Invariance**:
   - Change `run_date` parameter (e.g., simulate running on `2026-09-25` vs `2024-01-01`); assert that all portfolio values and signals prior to `covered_end` remain bit-for-bit identical.

---

## 3. EXECUTION STEPS & ARTIFACTS

### Step 1: Gate E — Round-Trip Script
- Script: `deliverables/gate_ef/scripts/gate_e_roundtrip.py`
- Implements bi-directional replay engine (forward & backward).
- Outputs:
  - `data/verification/membership_<date1>.txt`
  - `data/verification/membership_<date2>.txt`
  - `data/verification/membership_<date3>.txt`
  - `deliverables/gate_ef/data_csv/gate_e_roundtrip_summary.csv`
  - `deliverables/gate_ef/raw/gate_e_roundtrip.txt`

### Step 2: Gate F — Reproducibility & Truncation Script
- Script: `deliverables/gate_ef/scripts/gate_f_reproducibility.py`
- Executes dual passes, out-of-bounds date clamping test, and run-date invariance check.
- Outputs:
  - `deliverables/gate_ef/data_csv/gate_f_clamping_summary.csv`
  - `deliverables/gate_ef/raw/gate_f_pass1.txt`
  - `deliverables/gate_ef/raw/gate_f_pass2.txt`
  - `deliverables/gate_ef/raw/gate_f_truncation.txt`

### Step 3: Compilation & Standing Gate HALT-5
- Script: `deliverables/gate_ef/scripts/generate_evidence_index.py`
- Compile:
  - `deliverables/gate_ef/DIGEST.md`
  - `deliverables/gate_ef/EVIDENCE_INDEX.tsv`
  - `deliverables/gate_ef/task_list.md`: Tick Gate E and Gate F; leave **HALT-5 UNTICKED and OPEN**.
- Dispatch Telegram alert via `/usr/local/bin/telegram-notify`.
- **HALT-5 MANDATORY PAUSE**: Cease execution and notify the Auditor. Await final Auditor review for full Phase 5.5 completion sign-off before entering Phase 5.6.
