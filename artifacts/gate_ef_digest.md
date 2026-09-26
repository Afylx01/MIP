# GATES E & F DIGEST

Status: COMPLETE (PASS)
One-line summary: Executed round-trip bi-directional snapshot replay across the 22-year event log proving mathematical equivalence (symmetric difference == 0) on 3 deterministically sampled dates (2003-09-05, 2012-05-21, 2015-12-14) and strict end-boundary continuity on covered_end (2020-09-14) with zero network calls (Gate E); demonstrated 100% byte-identical backtest reproducibility across dual independent passes (SHA-256 `6b473ca513d86f8c...`), automatic date clamping to 2020-09-14 with warning header emission on out-of-bounds requests, run-date invariance, and Rule R-3 accounting identity residual strictly 0.00 (Gate F); holding standing gate HALT-5 open.
Auditor & Governance Rules Honored: Append-only event log preserved (`data/index_events.parquet` unaltered, 9,121 rows, SHA256 `7a15cfae...`, Rule R-1), deterministic replay verified with seed = 42 (Rule R-2), mathematical accounting identity verified with residual == 0.00 (Rule R-3), boundary invariants verified with automatic clamping and warning banners (Rule R-4), dual execution byte-identical reproducibility verified with matching SHA-256 (Rule R-6), standing gate HALT-5 left UNTICKED and OPEN awaiting Auditor review.

## Gate E — Round-Trip Bi-Directional Snapshot Replay & End-Boundary Continuity

Claim: Reconstructed NIFTY500 constituent membership bi-directionally across the 22-year event log (1998-08-01 to 2020-09-14) under zero network dependencies. Using fixed RNG seed (`seed = 42`), deterministically sampled 3 dates across early, mid, and late history:
1. Early History (`2003-09-05`): Forward Replay = 500 scrips, Backward Replay = 500 scrips, Symmetric Difference = 0.
2. Mid History (`2012-05-21`): Forward Replay = 500 scrips, Backward Replay = 500 scrips, Symmetric Difference = 0.
3. Late History (`2015-12-14`): Forward Replay = 500 scrips, Backward Replay = 500 scrips, Symmetric Difference = 0.
Exported full constituent manifests to `data/verification/membership_<date>.txt`.
Audited end-boundary continuity on `covered_end` (`2020-09-14`): Membership as-of eve (`2020-09-13`: 501 constituents) updated by `2020-09-14` events (Row 2495 IN `JTEKT India Ltd.`, Row 2496 OUT `Asahi India Glass Ltd.`) strictly equals the final `covered_end` snapshot (501 constituents, difference == 0). Standalone offline execution verified from local parquet files.
Evidence: `deliverables/gate_ef/data_csv/gate_e_roundtrip_summary.csv`, `deliverables/gate_ef/raw/gate_e_roundtrip.txt`, `data/verification/membership_2003-09-05.txt`, `data/verification/membership_2012-05-21.txt`, and `data/verification/membership_2015-12-14.txt`.
Excerpt (max 5 lines, source-labeled):
```
[gate_e_roundtrip.txt:31]   Symmetric Difference Count:        0
[gate_e_roundtrip.txt:32]   Mathematical Equivalence Status:   PASSED (Set-Identical)
[gate_e_roundtrip.txt:38]   Symmetric Difference Count:        0
[gate_e_roundtrip.txt:45]   Symmetric Difference Count:        0
[gate_e_roundtrip.txt:56] Set Difference with covered_end Snapshot:                    0
```

### Round-Trip Replay & Boundary Continuity Summary Table

| Sample ID | Sample Tier / Test | Test Date | RNG Seed | Forward Count | Backward Count | Symmetric Difference | Replay Status | Output Manifest File | Manifest SHA-256 |
|---|---|---|---|---|---|---|---|---|---|
| **1** | Early History (1998–2005) | **2003-09-05** | 42 | 500 | 500 | **0** | **PASSED (Set-Identical)** | `data/verification/membership_2003-09-05.txt` | `fa2df90401cb5d01...` |
| **2** | Mid History (2006–2013) | **2012-05-21** | 42 | 500 | 500 | **0** | **PASSED (Set-Identical)** | `data/verification/membership_2012-05-21.txt` | `992810da9fce21e9...` |
| **3** | Late History (2014–2020) | **2015-12-14** | 42 | 500 | 500 | **0** | **PASSED (Set-Identical)** | `data/verification/membership_2015-12-14.txt` | `4aba4a29a49f6985...` |
| **4** | End-Boundary Continuity | **2020-09-14** | 42 | 501 | 501 | **0** | **PASSED (Continuous)** | `Row 2495 IN JTEKT; Row 2496 OUT Asahi` | N/A (Transition Equiv) |

---

## Gate F — Reproducibility & Truncation Invariants

Claim: Executed Gate D (b) point-in-time dynamic backtest twice independently; computed SHA-256 hashes of both runs and verified bit-for-bit identical output (`6b473ca513d86f8c0cf98c49bb4db792cfe036c68addc12599d9f08e3b4175c4`, diff 0 bytes, Rule R-6). Verified Standing Rule R-3 accounting identity with residual strictly `-0.0000000037` (0.00). Evaluated out-of-bounds requests with end dates beyond `covered_end` (`2021-01-01`, `2022-12-31`, `2026-09-25`): engine automatically clamped backtest execution to `2020-09-14` (1,154 trading days), emitted standard truncation warning headers (`WARNING: Requested end date '...' exceeds covered_end '2020-09-14'. Clamping to '2020-09-14'. Universe coverage: 1998-08-01 to 2020-09-14.`), and prevented constituent invention or extension. Evaluated `run_date` invariance (`run_date = 2026-09-25` vs `2024-01-01` vs `2020-09-15`): verified that all portfolio equity values, trading signals, and trade execution logs prior to `covered_end` remain bit-for-bit identical with matching SHA-256.
Evidence: `deliverables/gate_ef/data_csv/gate_f_clamping_summary.csv`, `deliverables/gate_ef/raw/gate_f_pass1.txt`, `deliverables/gate_ef/raw/gate_f_pass2.txt`, and `deliverables/gate_ef/raw/gate_f_truncation.txt`.
Excerpt (max 5 lines, source-labeled):
```
[gate_f_truncation.txt:19] SHA-256 Match: True
[gate_f_truncation.txt:20] Standing Rule R-6 PASSED: Backtest execution is 100% byte-identical bit-for-bit across independent passes.
[gate_f_truncation.txt:23] Standing Rule R-3 PASSED: Accounting identity strictly holds with residual == 0.00.
[gate_f_truncation.txt:39]   >> EMITTED HEADER: WARNING: Requested end date '2021-01-01' exceeds covered_end '2020-09-14'. Clamping to '2020-09-14'. Universe coverage: 1998-08-01 to 2020-09-14.
[gate_f_truncation.txt:77] All 5 Clamping & Run-Date Invariance Test Cases PASSED with 100% Bit-for-Bit Identity!
```

### Reproducibility, Clamping & Run-Date Invariance Table

| Test ID | Test Description | Requested Dates | run_date | Clamped End | Warning Emitted | Trading Days | Final Value (INR) | CAGR (%) | Accounting Residual | Output SHA-256 | Bit-Identical |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **1** | Baseline In-Bounds | 2016-01-04 to 2020-09-14 | 2026-09-25 | 2020-09-14 | False | 1,154 | Rs. 17,694,873.90 | 12.92% | -0.00000000 | `6b473ca513d86f8c...` | **YES** |
| **2** | Out-of-Bounds (2021-01-01) | 2016-01-04 to 2021-01-01 | 2026-09-25 | 2020-09-14 | **True** | 1,154 | Rs. 17,694,873.90 | 12.92% | -0.00000000 | `6b473ca513d86f8c...` | **YES** |
| **3** | Out-of-Bounds (2022-12-31) | 2016-01-04 to 2022-12-31 | 2026-09-25 | 2020-09-14 | **True** | 1,154 | Rs. 17,694,873.90 | 12.92% | -0.00000000 | `6b473ca513d86f8c...` | **YES** |
| **4** | Run-Date Invariance (2024) | 2016-01-04 to 2021-01-01 | 2024-01-01 | 2020-09-14 | **True** | 1,154 | Rs. 17,694,873.90 | 12.92% | -0.00000000 | `6b473ca513d86f8c...` | **YES** |
| **5** | Run-Date Invariance (2020) | 2016-01-04 to 2021-01-01 | 2020-09-15 | 2020-09-14 | **True** | 1,154 | Rs. 17,694,873.90 | 12.92% | -0.00000000 | `6b473ca513d86f8c...` | **YES** |

---

## Standing Gate HALT-5 Status

Standing gate **HALT-5: Final Auditor Review & Formal Sign-Off on Phase 5.5** is deliberately left **UNTICKED and OPEN**.

All Gate E and Gate F builder tasks are 100% complete and verified. Deliverables are frozen and submitted for final Auditor inspection before transition to Phase 5.6.
