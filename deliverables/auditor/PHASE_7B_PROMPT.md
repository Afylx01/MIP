# PHASE 7B DIRECTIVE: STATISTICAL RIGOR, WALK-FORWARD & PARAMETER PLATEAU SENSITIVITY (GATES 11–16)

**Document**: `deliverables/phase_7/NEXT_TASK.md`  
**From**: Auditor & Lead Quantitative Strategist  
**To**: Builder Team  
**Date**: September 26, 2026  
**Status**: ACTIVE DIRECTIVE  
**Deliverables Directory**: `deliverables/phase_7/`  
**Standing Gate**: **HALT-8B** (Mandatory pause awaiting Auditor review and verification of Gates 11–16)

---

## 1. Executive Context & Objectives

Phase 7A (Gates 1–10) has been formally audited and accepted by the Auditor (`deliverables/phase_7/PHASE_7A_RULING.md`), clearing Standing Gate HALT-8A. All data integrity invariants (Point-in-Time continuity, zero survivorship purging, zero look-ahead, circuit tradability, and institutional cost resilience) have been verified with 100% mathematical compliance.

We now initiate **Phase 7B: Statistical Rigor, Walk-Forward & Parameter Plateau Sensitivity (Gates 11–16)**.

The objective of Phase 7B is to mathematically prove that the strategy's excess returns are **robust, persistent, and not the result of parameter over-fitting, calendar anomalies, or isolated universe selection bias**.

---

## 2. Technical Tasks & Pass/Fail Gates (Gates 11–16)

The Builder must author self-contained execution scripts in `deliverables/phase_7/scripts/` to evaluate Gates 11 through 16:

### Task 1: In-Sample (IS) vs Out-of-Sample (OOS) Split Analysis (Gate 11)
- **Script**: `deliverables/phase_7/scripts/test_is_oos_split.py`
- **Methodology**:
  - Partition the 20-year consolidated Bhavcopy dataset into:
    1. **In-Sample (IS)**: `2007-01-02` to `2015-12-31` (9.0 years, covering GFC 2008 and 2011–2013 sideways market).
    2. **Out-of-Sample (OOS)**: `2016-01-04` to `2026-08-31` (10.66 years, modern era).
  - Execute the identical baseline strategy (MIP-1 / MIP-RS / MIP-Volar) across both sub-periods using the continuous NIFTY 500 benchmark proxy.
- **Pass Threshold**: OOS CAGR $>$ Benchmark CAGR + 3.0 percentage points; OOS Sharpe Ratio $> 0.80$.
- **Fail Threshold**: OOS excess return $<$ 2.0 percentage points or OOS Sharpe $< 0.50$.
- **Export**: `deliverables/phase_7/data_csv/gate11_is_oos_results.csv`.

---

### Task 2: Walk-Forward Rolling Analysis (Gate 12)
- **Script**: `deliverables/phase_7/scripts/test_walk_forward.py`
- **Methodology**:
  - Implement a 5-year rolling training window and a 1-year forward out-of-sample testing window:
    - Train Window 1: 2007–2011 $\to$ Test Window 1: 2012
    - Train Window 2: 2008–2012 $\to$ Test Window 2: 2013
    - Train Window 3: 2009–2013 $\to$ Test Window 3: 2014
    - ...
    - Train Window 14: 2020–2024 $\to$ Test Window 14: 2025–2026
  - Compute annual excess returns over NIFTY 500 benchmark proxy for each forward test year.
- **Pass Threshold**: $\ge 70\%$ of rolling OOS test years produce positive excess return over benchmark; median annual excess return $>$ 3.0 percentage points.
- **Fail Threshold**: $< 50\%$ positive excess years.
- **Export**: `deliverables/phase_7/data_csv/gate12_walk_forward_matrix.csv`.

---

### Task 3: Multi-Dimensional Parameter Plateau Sensitivity Grid (Gate 14)
- **Script**: `deliverables/phase_7/scripts/test_parameter_plateau.py`
- **Methodology**:
  - Systematically evaluate the baseline momentum strategy across a multi-dimensional parameter matrix to detect overfitting or brittle knife-edge parameter dependencies:
    1. **Retracement Filter**: $15\%$, $20\%$, $25\%$, $30\%$ from 52-week High.
    2. **EMA Trend Filter**: $150$, $200$, $250$ days.
    3. **Ranking Lookback**: $126$ days (6-month), $189$ days (9-month), $252$ days (12-month).
    4. **Portfolio Size**: $15$, $20$, $25$, $30$ stocks.
    5. **Exit Rank Buffer**: $25$ (25%), $30$ (50%), $40$ (100%), $50$ (150%).
  - Total combinations evaluated: At least $3 \times 3 \times 3 \times 2 = 54$ discrete parameter sets across 2016–2026.
- **Pass Threshold**: $\ge 70.0\%$ of evaluated parameter combinations beat Benchmark CAGR by $\ge +3.0$ percentage points.
- **Fail Threshold**: $< 40.0\%$ of parameter combinations meet the threshold.
- **Export**: `deliverables/phase_7/data_csv/gate14_parameter_plateau_grid.csv`.

---

### Task 4: Rebalance-Date & Calendar Day Sensitivity (Gate 15)
- **Script**: `deliverables/phase_7/scripts/test_rebalance_date_sensitivity.py`
- **Methodology**:
  - Test rebalancing on 5 distinct monthly trading days to eliminate calendar anomalies:
    1. **1st Trading Day of Month** (Baseline).
    2. **5th Trading Day of Month**.
    3. **10th Trading Day of Month**.
    4. **15th Trading Day of Month**.
    5. **Last Trading Day of Month**.
  - Calculate CAGR, Max Drawdown, and excess return for each rebalance schedule across 2016–2026.
- **Pass Threshold**: Average excess CAGR across all 5 dates $>$ 3.0 percentage points; standard deviation of excess returns across dates $< 3.0$ percentage points.
- **Fail Threshold**: Strategy works on only one specific date or excess return exhibits extreme variance ($\text{std} > 4.0\text{ pp}$).
- **Export**: `deliverables/phase_7/data_csv/gate15_rebalance_date_sensitivity.csv`.

---

### Task 5: Universe Segment Sensitivity & Simulated Paper Trading (Gates 13, 16)
- **Script**: `deliverables/phase_7/scripts/test_universe_and_paper_trading.py`
- **Methodology**:
  - **Gate 16 (Universe Sensitivity)**:
    - Test baseline strategy across discrete index universes:
      1. NIFTY 50 (Mega-cap).
      2. NIFTY Next 50 (Large/Midcap transition).
      3. NIFTY Midcap 150.
      4. NIFTY Smallcap 250.
      5. NIFTY 500 (Composite universe).
    - Pass Threshold: At least 3 universes beat their respective benchmark CAGR by $\ge +3.0$ percentage points.
    - Fail Threshold: Only microcaps produce positive alpha or large/midcap fail completely.
  - **Gate 13 (Simulated Paper Trading Calibration)**:
    - Run recent 12-month forward simulation (September 2025 to August 2026).
    - Pass Threshold: Simulated execution tracking error vs theoretical signal $< 5.0\%$; effective slippage $\le 1.5\times$ base cost.
- **Export**: `deliverables/phase_7/data_csv/gate16_universe_sensitivity.csv` and `deliverables/phase_7/data_csv/gate13_paper_trading_calibration.csv`.

---

### Task 6: Master Summary & Deliverables Compilation
- Generate master compliance table: `deliverables/phase_7/data_csv/gates_11_16_summary.csv`.
- Author detailed verification report in `deliverables/phase_7/DIGEST_PHASE_7B.md`.
- Update `deliverables/phase_7/EVIDENCE_INDEX.tsv` and `deliverables/phase_7/SHA256SUMS.txt`.
- Update `deliverables/phase_7/task_list.md` to record Phase 7B tasks and establish **Standing Gate HALT-8B** as UNTICKED and OPEN.
- Package deliverables bundle into `artifacts/phase_7b_deliverables.zip` and `/sdcard/Documents/deliverables/phase_7b_deliverables.zip`.
- Dispatch Telegram alert via `/usr/local/bin/telegram-notify`.
- **Halt and yield to Auditor**.

---

## 3. Strict Execution Invariants

1. **Ubuntu System Python (`/usr/bin/python3`)**: All scripts must run inside PRoot Ubuntu using system packages.
2. **Rule R-1 (Append-Only Integrity)**: Do not overwrite Phase 7A deliverables (`gates_1_to_10_summary.csv`, `PHASE_7A_RULING.md`, etc.).
3. **Rule R-2 (Recompute, Don't Trust)**: All statistics must be computed directly from historical daily price bars; zero hardcoding.
4. **Rule R-3 (Strict Cash Conservation)**: Total Portfolio Value = Invested Value + Cash. Accounting residual must strictly equal `0.00` to the paisa.
5. **Rule R-10 (Standing Gate Discipline)**: **DO NOT proceed to Phase 7C.** Halt at **Standing Gate HALT-8B** and await Auditor review.
