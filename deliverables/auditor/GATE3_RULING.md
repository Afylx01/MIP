# GATE 3 AUDITOR RULING

Status: ACCEPT_WITH_CONDITIONS

## Files inspected

- `deliverables/gate3/DIGEST.md` | `c5b01e9f0efdf01800c2832d8538bd92678550765ea53d9259477e275ca47a36`
- `deliverables/gate3/EVIDENCE_INDEX.tsv` | `df0ce7fb5d194b27b9a8db7e7f6befeb795dd559207c8e76cbb1b4cd857c24f5`
- `deliverables/gate3/task_list.md` | `ca68de364fde44525a4515cbe9c569696233d5e91aa6b74c2d4dcdc488c4b201`
- `deliverables/gate3/data_csv/forensic_reconciliation.csv` | `c375f8067efe50ccee7368731ac389b8b36066fea6f6d7c3cb1336eacee20b46`
- `deliverables/gate3/data_csv/proposed_corrections.csv` | `04bcafb6f815bdfce9b8b3954b92815561adfbc3698a0f24d98ceb8cbb7076c4`
- `deliverables/gate3/data_csv/simulation_rebalance_counts.csv` | `ae3b5c97ad4991b3805a486cb36abf3842ff605c2d09c400e8f3371e5f40ce4b`
- `deliverables/gate3/data_csv/unresolved_anomalies.csv` | `49658d132f52b7dbeb711fb79b679501bf6c09ad473993639887dc847a877de8`
- `deliverables/gate3/raw/gate0_anomalies_audit.txt` | `5e5d9c7e8696312540a9e5ceb7d54a26616a6db42f152a47f65e8bfb5d6b4a3a`
- `deliverables/gate3/raw/gate2_build_corrections.txt` | `f4bf8d2bebdf185fcbbd74bb87c6e91f535c15134441d2db65682dcdb4e5cd33`
- `deliverables/gate3/raw/gate3_simulated_replay.txt` | `7f315c58f69d1d7937d0e50f7235337159b9f22e92092c90814145af2a22006d`
- `deliverables/gate3/scripts/gate0_anomalies_audit.py` | `e52981b5f1a720f59840c25fa21f5bde274467be91bc5fcc1654c470bac52ddd`
- `deliverables/gate3/scripts/gate1_forensic_reconciliation.py` | `25acfa8069162ea881492be6f3226968511c14e4524085dba7d9ccd6823182cf`
- `deliverables/gate3/scripts/gate2_build_corrections.py` | `be705922b2e814e4fb1bc7c6e879bef49863ef0fa14ceabdc489e71809388e0e`
- `deliverables/gate3/scripts/gate3_simulated_replay.py` | `f979451d109dfbdad9cba00f73f88c6b0ed7e2eaef5833aa744e4dff6f98f276`
- `deliverables/gate3/scripts/generate_evidence_index.py` | `b47a5dcef0b6531b896c0ab79203b46056eac7c5f261f211b8974fe90f75e039`
- `data/corrections.parquet` | `08ab36133e595a5d2f9ec1d881e31704502e27fdf03cb476acc8d54d75921bdb`
- `data/corrections_report.md` | `46a4ac02db47588991d0cf09bfb6200bd9ea3dd5b3dcc3c66f80479d4d258b90`
- `data/index_events.parquet` | `7a15cfae88c53c6a4d79c5fe28dc3642a999728855d29329a892e11261d2d54a`

---

## Claims verified

### Claim 1: Gate 0 — Anomalies & Quarantined Rows Audit
- **Evidence**: `deliverables/gate3/raw/gate0_anomalies_audit.txt`, `deliverables/gate3/data_csv/unresolved_anomalies.csv`
- **Recomputation**: Replay of raw uncorrected workbook events confirmed:
  - 15 orphan OUT events (stocks excluded without prior recorded inclusion).
  - 1 duplicate IN event.
  - Quarantined duplicate pair from `grp_2017_09_05` isolated: Reliance Capital Ltd. OUT (Row 2136) and Max Financial Services Ltd. IN (Row 2162).

### Claim 2: Gate 1 — Forensic Reconciliation & Evidence Linking
- **Evidence**: `deliverables/gate3/data_csv/forensic_reconciliation.csv`, `data/corrections_report.md`
- **Recomputation**:
  - 14 orphan exclusions conclusively linked to corporate name changes without log entries in the workbook. Each link is backed by verified RoC fresh certificates of incorporation and official NSE listing circulars.
  - 1 orphan exclusion caused by a trailing punctuation dot (*Arvind Ltd* vs *Arvind Ltd.*).
  - 2 redundant duplicate entries inside the 2017-09-29 rebalance block confirmed as identical copies of the 2017-09-05 inter-rebalance replacement.

### Claim 3: Gate 2 — Corrections Proposal Table Compilation (Rule R-11 Compliance)
- **Evidence**: `data/corrections.parquet`, `deliverables/gate3/data_csv/proposed_corrections.csv`
- **Recomputation**:
  - `data/corrections.parquet` contains exactly 16 rows.
  - 100% of rows carry `status = 'proposed'` (Standing Rule R-11 verified; zero auto-approval).
  - All 16 rows have non-empty `rationale`, `correction_type`, and ISO `YYYY-MM-DD` effective dates.
  - `data/index_events.parquet` remains 100% unaltered (append-only architecture respected).

### Claim 4: Gate 3 — Simulated Replay & Constituent Count Invariants
- **Evidence**: `deliverables/gate3/raw/gate3_simulated_replay.txt`, `deliverables/gate3/data_csv/simulation_rebalance_counts.csv`
- **Recomputation**:
  - Orphan OUT count drops from 15 to **0** (exact parity).
  - Duplicate IN count drops from 1 to **0** (exact parity).
  - Rebalance constituent counts across all 57 monthly snapshots (2016-01-04 to 2020-09-01):
    - Min count: **500**
    - Median count: **501.0**
    - Max count: **501**
    - 57 of 57 snapshots (100.0%) strictly adhere to statutory range $[490, 515]$.

---

## Claims rejected

None. All claims made in `deliverables/gate3/DIGEST.md` are supported by raw on-disk artifacts and validated by independent recomputation.

---

## Claims requiring user attention

1. **User Approval of Corrections Proposal (HALT-2 Gate)**:
   - In accordance with Standing Rule R-11 and the Phase 5.5 specification: *"Statuses you may write: proposed. Statuses only the user sets: approved, rejected. Your scripts never auto-approve."*
   - All 16 corrections in `data/corrections.parquet` currently carry `status = 'proposed'`.
   - The user must review the proposed corrections in [proposed_corrections.csv](file:///sdcard/Documents/Project%20MIP/deliverables/gate3/data_csv/proposed_corrections.csv) and [corrections_report.md](file:///sdcard/Documents/Project%20MIP/data/corrections_report.md) and formally approve them.

---

## Conditions (if ACCEPT_WITH_CONDITIONS)

1. **User Approval**: The user formally approves the 16 proposed corrections in `data/corrections.parquet`.
2. **Transition to Approved**: Upon user approval, the status of the 16 rows in `data/corrections.parquet` transitions from `'proposed'` to `'approved'`, formally satisfying **HALT-2**.
3. **Append-Only Integrity**: `data/index_events.parquet` must remain permanently unaltered.

---

## Next phase recommendation

Upon user approval of the corrections proposal, **HALT-2 is resolved**.  
Proceed immediately to **Phase 5.5 Gate A: Coverage Map (Post-Approval) & Gate B: Snapshot Sanity**.  

The actionable builder prompt has been placed directly in the same directory:
- [NEXT_TASK.md](file:///sdcard/Documents/Project%20MIP/deliverables/gate3/NEXT_TASK.md)
