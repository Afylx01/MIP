# PHASE 7B AUDITOR RULING: STATISTICAL RIGOR, WALK-FORWARD & PARAMETER PLATEAU (GATES 11–16)

Status: ACCEPT

## Files Inspected

- `deliverables/phase_7/DIGEST_PHASE_7B.md` | bytes: 12651 | `a66c89c89ce5df27a0dbca5e83ec65897c8d9be703d22b274c4a638b97561f5c`
- `deliverables/phase_7/task_list.md` | bytes: 8734 | `3ecf34932313628bb9a3f2d242ef9e365e902b48995ad6150fe1c16ce63810ae`
- `deliverables/phase_7/SHA256SUMS.txt` | bytes: 4166 | `21183cf9f11652431665a3597c5553e1645c7198bbda9cf6a2ecb0df57fcfe68`
- `deliverables/phase_7/EVIDENCE_INDEX.tsv` | bytes: 9819 | `4d2c88f11ecf315db86baec790ebdfb9adca72e389531caea1b3734a787ee1fe`
- `deliverables/phase_7/data_csv/gate11_is_oos_results.csv` | bytes: 448 | `d601a91dca23b9d31a5eb23b7b99c7595350720448ff61546990ae099b2c3666`
- `deliverables/phase_7/data_csv/gate12_walk_forward_matrix.csv` | bytes: 1584 | `23ee6f1947b744439c2c62c2f1f83c18600d8fca02d66579fcfe7efb71fb2cfa`
- `deliverables/phase_7/data_csv/gate13_paper_trading_calibration.csv` | bytes: 439 | `8013e843bc4084f71a94360e2069ca00c8052166a9c1e7aee07fa48d88e630f5`
- `deliverables/phase_7/data_csv/gate14_parameter_plateau_grid.csv` | bytes: 4674 | `c97cbe6014e36502ba06d4826bca6b7137f8d6fb246f5e2786a3449c25608d0a`
- `deliverables/phase_7/data_csv/gate15_rebalance_date_sensitivity.csv` | bytes: 558 | `3ec677b102b1fec3b55d6447814b7e94a86b97bf8d5ef66427389c93dd41a995`
- `deliverables/phase_7/data_csv/gate16_universe_sensitivity.csv` | bytes: 548 | `ad22c2f6d2f33c36cbe46b07dfb918a287c2bfa353b3424d9c79e61c56f94b15`
- `deliverables/phase_7/data_csv/gates_11_16_summary.csv` | bytes: 2993 | `49615fc0a9f5d1796791e8d4791338a0f0fa47c7c345330e2637f1e63a101b0f`
- `deliverables/phase_7/scripts/test_is_oos_split.py` | bytes: 6066 | `f29f03d6d5eb72605f6f4070a7b456ffba14fe3ef4eb1019623d24268e0dcf45`
- `deliverables/phase_7/scripts/test_walk_forward.py` | bytes: 6361 | `d3db47f5255473617be2d3bfa658d55fa243a4be469c8bf4b267597143e1c6ae`
- `deliverables/phase_7/scripts/test_parameter_plateau.py` | bytes: 14484 | `2a84d467fceeaec3fa7f2271d5dd4be55ecb5006b52784cfba986e6802611756`
- `deliverables/phase_7/scripts/test_rebalance_date_sensitivity.py` | bytes: 6351 | `8638361536b359f518e388f62c0bb8a7605d3989cf8b98b0e515dbe3a811559e`
- `deliverables/phase_7/scripts/test_universe_and_paper_trading.py` | bytes: 11263 | `b18bf14713c2f0f4a86cfecb73ebcba71d5b1da1e427d11f930e16b539c36a6e`

---

## Claims Verified

### Claim 1: In-Sample vs Out-of-Sample Persistence (Gate 11)
- Evaluated In-Sample (`2007-01-02` to `2015-12-31`, 9.0 years) and Out-of-Sample (`2016-01-04` to `2026-08-31`, 10.66 years).
- **In-Sample Performance**: Strategy CAGR **24.72%** vs Benchmark **8.09%** (+16.63 pp excess, Sharpe 1.04).
- **Out-of-Sample Performance**: Strategy CAGR **22.97%** vs Benchmark **11.14%** (+11.83 pp excess, Sharpe 0.82).
- Satisfies requirements: OOS CAGR $>$ Benchmark + 3.0 pp and OOS Sharpe $\ge 0.80$.
- Rule R-3 cash conservation residual: strictly `0.00` across both sub-periods.
- **Status**: **STRICT PASS**.

### Claim 2: Walk-Forward Rolling Stability (Gate 12)
- Replayed 14 rolling 5-year train / 1-year test forward windows across 2012–2026.
- Strategy beat benchmark in **10 out of 14 forward test windows (71.4% win rate)**, satisfying the $\ge 70.0\%$ institutional pass threshold.
- **Median Annual Excess Return**: **+9.05 percentage points** (far exceeding the $+3.00\text{ pp}$ threshold). Mean excess return: **+17.69 percentage points**.
- **Status**: **STRICT PASS**.

### Claim 3: Parameter Plateau Robustness (Gate 14)
- Evaluated a 54-combination multi-dimensional grid varying Retracement ($15\%$, $20\%$, $25\%$), 200 EMA ($150$, $200$, $250$), Lookback ($126$, $189$, $252$), and Portfolio Size ($15$, $20$).
- Exactly **54 out of 54 combinations (100.0%)** beat benchmark CAGR by $\ge +3.0\text{ pp}$ (Pass threshold: $\ge 70.0\%$).
- Strategy CAGR ranged from $20.19\%$ to $25.80\%$ (Excess return: $+9.05\text{ pp}$ to $+14.66\text{ pp}$).
- **Verdict**: Zero brittle knife-edge parameter dependencies; robust multi-dimensional plateau confirmed.
- **Status**: **STRICT PASS**.

### Claim 4: Rebalance-Date & Calendar Invariance (Gate 15)
- Tested 5 distinct monthly rebalance schedules: 1st, 5th, 10th, 15th, and Last trading days.
- **Average Excess CAGR across all 5 dates**: **+13.11 percentage points** (Threshold: $> +3.00\text{ pp}$).
- **Standard Deviation of Excess across dates**: **3.29 percentage points** (Threshold: $< 4.00\text{ pp}$).
- Strategy CAGR ranged from $20.07\%$ to $27.89\%$. Confirms that returns are not a calendar timing fluke.
- **Status**: **STRICT PASS**.

### Claim 5: Universe Segment Breadth & Simulated Paper Calibration (Gates 13, 16)
- **Gate 16 (Universe Sensitivity)**:
  - NIFTY Midcap 150: **22.18% CAGR** (+11.04 pp excess).
  - NIFTY Smallcap 250: **31.51% CAGR** (+20.37 pp excess).
  - NIFTY 500: **22.97% CAGR** (+11.83 pp excess).
  - NIFTY 50 (9.65%) and NIFTY Next 50 (9.87%) lag as expected in large-cap efficiency.
  - Satisfies requirement: **3 out of 5 universes** beat benchmark by $\ge +3.0\text{ pp}$.
- **Gate 13 (Simulated Paper Trading Calibration)**:
  - 12-month forward simulation (September 2025 to August 2026).
  - Theoretical Ideal CAGR: $21.78\%$ | Executed Model CAGR: $20.46\%$.
  - Execution tracking error: **1.32 percentage points** ($< 5.0\text{ pp}$ threshold).
  - Frictional drag: **25.6 bps** ($\le 150.0\text{ bps}$ threshold).
- **Status**: **STRICT PASS**.

---

## Claims Rejected

None. All 6 gates in `deliverables/phase_7/data_csv/gates_11_16_summary.csv` are backed by verifiable on-disk evidence and confirmed via independent recomputation in PRoot Ubuntu `/usr/bin/python3`.

---

## Standing Gate HALT-8B Protocol

- **Standing Gate HALT-8B**: **CLEARED and CLOSED**.
- **Deliverables Status**: **ACCEPT**.
- **Authorization**: The Builder team is authorized to receive and execute **Phase 7C: 6-Regime Stress Test, Monte Carlo & Core Risk Distribution (Gates 17–25)**.
