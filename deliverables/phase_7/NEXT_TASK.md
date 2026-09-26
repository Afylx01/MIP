# PHASE 7D DIRECTIVE: COMPONENT ATTRIBUTION, VARIANTS & PRODUCTION GO/NO-GO ENGINE (GATES 26–32 + IS_PROVEN)

**Document**: `deliverables/phase_7/NEXT_TASK.md`  
**From**: Auditor & Lead Quantitative Strategist  
**To**: Builder Team  
**Date**: September 26, 2026  
**Status**: ACTIVE DIRECTIVE  
**Deliverables Directory**: `deliverables/phase_7/`  
**Standing Gate**: **HALT-8D** (Final Mandatory pause awaiting Auditor review and Institutional Go / No-Go Ruling)

---

## 1. Executive Context & Objectives

Phase 7C (Gates 17–25) has been formally audited and accepted (`deliverables/phase_7/PHASE_7C_RULING.md`), clearing Standing Gate HALT-8C. The baseline momentum strategy demonstrated:
- Zero structural traps across 6 macro market regimes (Average MaxDD: 35.16%, trough recovery: 1.60 years).
- Statistical superiority over 1,000 random portfolios (+10.30 pp excess CAGR, $p = 0.0000$).
- Systematic Alpha of +13.03%, Information Ratio of 0.578, Beta of 0.796, Sharpe of 0.82, and Sortino of 0.89.
- Robust trade expectancy (+11.02% per trade, Profit Factor 1.98, Win/Loss payoff 2.99x).
- Newey-West HAC $t$-statistic of 1.833, Block Bootstrap 5th percentile excess alpha of +0.75 pp (96.21% paired win rate), and Deflated Sharpe Ratio of 1.0000.

We now enter the final quadrant of the institutional verification suite: **Phase 7D: Component Attribution, Variants & Production Go/No-Go Engine (Gates 26–32 + `is_proven`)**.

The objective of Phase 7D is to:
1. Conduct an empirical ablation study proving that every rule in the strategy adds distinct, non-redundant value.
2. Optimize buffer and market regime cash filter thresholds.
3. Verify institutional portfolio capacity and liquidity constraints (ADV).
4. Evaluate the ETF multi-asset momentum variant.
5. Synthesize the final automated `is_proven(results)` master verification engine that delivers the definitive **Institutional Go / No-Go Decision**.

---

## 2. Technical Tasks & Pass/Fail Gates (Gates 26–32 + `is_proven`)

The Builder must author modular scripts in `deliverables/phase_7/scripts/` to evaluate Gates 26 through 32:

### Task 1: Sequential Component Attribution & Ablation Study (Gate 26)
- **Script**: `deliverables/phase_7/scripts/test_component_attribution.py`
- **Methodology**:
  - Build the strategy incrementally from a bare-bones baseline to the full production model across 2016–2026:
    - **Step 1 (Raw Base)**: Within 20% of 52w High + Close > 200 EMA + Top 20 equal-weight (Monthly rebalance, immediate exit at rank 21).
    - **Step 2 (+ Relative Strength)**: Add Filter 3 (Stock / NIFTY 500 ratio > 200 EMA).
    - **Step 3 (+ Volar Ranking)**: Replace raw 252d return with Volatility-Adjusted Return ($\text{Return}_{252} / \sigma_{252}$).
    - **Step 4 (+ Market Regime Filter)**: Add NIFTY 500 < 20 EMA cash rule (pause buys, exit dropouts).
    - **Step 5 (+ Exit Rank Buffer)**: Add Exit Rank 40 (100% buffer).
  - Measure CAGR, Max Drawdown, Sharpe Ratio, and Annual Turnover at each incremental step.
- **Pass Threshold**: Each added rule must improve CAGR by $> 1.0$ percentage point OR reduce Max Drawdown by $> 5.0$ percentage points without reducing CAGR by $> 2.0$ pp.
- **Fail Threshold**: Any rule adds no value or significantly harms risk-adjusted performance.
- **Export**: `deliverables/phase_7/data_csv/gate26_component_attribution.csv`.

---

### Task 2: Exit Buffer & Market Filter Optimization (Gates 27, 28)
- **Script**: `deliverables/phase_7/scripts/test_buffer_and_market_filters.py`
- **Methodology**:
  - **Gate 27 (Exit Rank Buffer Sensitivity)**:
    - Compare 4 buffer settings: 0% buffer (exit rank 21), 50% buffer (exit rank 30), 100% buffer (exit rank 40), and 200% buffer (exit rank 60).
    - Measure annual portfolio turnover, trade count, CAGR, and Max Drawdown.
    - *Pass Threshold*: 100% buffer cuts turnover by $> 20.0\%$ with CAGR drop $< 1.0$ percentage point.
    - *Fail Threshold*: Buffer fails to reduce turnover or causes significant performance drag.
  - **Gate 28 (Market Regime Filter Comparison)**:
    - Compare 4 regime protection models:
      1. **Filter Off**: 100% equity invested at all times.
      2. **20 EMA Filter**: Pause entries if NIFTY 500 < 20 EMA (Podcast baseline).
      3. **200 EMA Filter**: Pause entries if NIFTY 500 < 200 EMA (Macro trend filter).
      4. **Macro Cash Switch (Extension E4)**: Shift 100% unallocated cash to 6% risk-free yield when NIFTY 50 < 200 EMA (from `data/benchmarks/NIFTY_50.csv`).
    - *Pass Threshold*: Market filter cuts Max Drawdown by $> 10.0$ percentage points with CAGR drop $< 2.0$ percentage points.
    - *Fail Threshold*: Market filter causes CAGR to drop by $> 5.0$ percentage points.
- **Export**: `deliverables/phase_7/data_csv/gates_27_28_buffer_and_filter.csv`.

---

### Task 3: Volar Ranking vs Raw Return & Retracement Threshold (Gates 29, 30)
- **Script**: `deliverables/phase_7/scripts/test_volar_and_retracement.py`
- **Methodology**:
  - **Gate 29 (Volar Ranking Comparison)**:
    - Compare Raw 252-day Return ranking vs Volar ranking ($\text{Return}_{252} / \sigma_{252}$).
    - *Pass Threshold*: Volar improves Max Drawdown by $> 5.0$ percentage points with CAGR degradation $< 1.0$ pp, improving Sharpe and Sortino ratios.
    - *Fail Threshold*: Volar ranking reduces CAGR by $> 3.0$ percentage points.
  - **Gate 30 (50% Retracement for Mid/Smallcaps)**:
    - Compare 20% retracement (Filter 1 baseline) vs 50% retracement in NIFTY Midcap 150 and Smallcap 250 universes.
    - *Pass Threshold*: 50% retracement improves CAGR by $> 2.0$ pp while keeping Max Drawdown increase $< 10.0$ pp ($< 60.0\%$ total).
    - *Fail Threshold*: Max Drawdown exceeds $60.0\%$.
- **Export**: `deliverables/phase_7/data_csv/gates_29_30_volar_and_retracement.csv`.

---

### Task 4: Portfolio Capacity & Liquidity Constraints (Gate 31)
- **Script**: `deliverables/phase_7/scripts/test_capacity_and_liquidity.py`
- **Methodology**:
  - Evaluate market impact and execution feasibility across multiple AUM tiers: ₹1 Crore, ₹5 Crore, ₹10 Crore, and ₹25 Crore.
  - For each intended trade, calculate trade value relative to 20-day Average Daily Volume (ADV) in rupees (`ADV_20 = Volume * Close`).
  - Compute maximum position ADV percentage, median position ADV percentage, and percentage of orders exceeding 10% of ADV.
- **Pass Threshold**: Maximum position size $< 10.0\%$ of 20-day ADV at target AUM (₹10 Crore); viable institutional capacity $\ge ₹10$ Crore.
- **Fail Threshold**: Maximum position size $> 25.0\%$ of ADV or viable capacity $< ₹5$ Crore.
- **Export**: `deliverables/phase_7/data_csv/gate31_capacity_liquidity.csv`.

---

### Task 5: Multi-Asset ETF Basket Variant (Gate 32)
- **Script**: `deliverables/phase_7/scripts/test_etf_variant.py`
- **Methodology**:
  - Replay the momentum framework across liquid Indian exchange-traded funds (ETFs) in modern history (2020–2026):
    - Large-cap: `NIFTYBEES`, `JUNIORBEES`
    - Sector/Thematic: `BANKBEES`, `ITBEES`, `CPSEETF`, `AUTOBEES`, `PHARMABEES`
    - Commodities: `GOLDBEES`, `SILVERBEES`
  - Select Top 3 ETFs monthly; hold cash/Gold when trend filter broken.
- **Pass Threshold**: Strategy functions in modern era (post 2022–2023) with positive excess return over NIFTY 50 ($> +2.0\text{ pp}$).
- **Fail Threshold**: No excess return or negative alpha over benchmark.
- **Export**: `deliverables/phase_7/data_csv/gate32_etf_variant.csv`.

---

### Task 6: Master Automated `is_proven(results)` Go / No-Go Decision Engine
- **Script**: `deliverables/phase_7/scripts/run_master_proven_gate.py`
- **Methodology**:
  - Aggregate verified results across all 32 gates from Phase 7A, 7B, 7C, and 7D.
  - Implement programmatic `is_proven(results)` engine executing all 16 core gating criteria:
    ```python
    def is_proven(results):
        return all([
            results.point_in_time_universe,       # Gate 1: 100% PIT
            results.delisting_included,            # Gate 2: Graveyard tracked
            results.no_lookahead,                  # Gate 3: t+1 Open fill
            results.corporate_actions_clean,       # Gate 4: Zero CA plunge
            results.cagr_after_2x_costs > results.benchmark_cagr + 0.02, # Gate 6
            results.oos_cagr > results.benchmark_cagr + 0.03,            # Gate 11
            results.sharpe >= 0.80,                # Gate 20
            results.sortino > 0.80,                # Gate 20
            results.calmar >= 0.50,                # Gate 20
            results.max_dd < 0.50,                 # Gate 20
            results.recovery_years < 3.0,          # Gate 21
            results.param_plateau_pct >= 0.70,     # Gate 14
            results.random_top20_excess > 0.03,    # Gate 18
            results.t_stat > 1.50,                 # Gate 23
            results.deflated_sharpe > 0.50,        # Gate 25
            results.max_position_adv_pct < 0.10,   # Gate 31
        ])
    ```
  - Export comprehensive 32-Gate Compliance Matrix: `deliverables/phase_7/data_csv/gates_1_to_32_master_compliance.csv`.
  - Export final JSON/CSV tearsheet: `deliverables/phase_7/data_csv/master_strategy_proven_results.json`.
  - Author executive completion report in `deliverables/phase_7/DIGEST_PHASE_7D.md`.
  - Update `EVIDENCE_INDEX.tsv` and `SHA256SUMS.txt`.
  - Update `task_list.md` with **Standing Gate HALT-8D** unticked.
  - Bundle archive to `artifacts/phase_7d_deliverables.zip` and `/sdcard/Documents/deliverables/phase_7d_deliverables.zip`.
  - Dispatch Telegram completion alert.
  - **Halt and yield to Auditor for Final Institutional Sign-off**.

---

## 3. Strict Execution Invariants

1. **Ubuntu System Python (`/usr/bin/python3`)**: Strictly execute using system python in PRoot Ubuntu.
2. **Rule R-1 (Append-Only Integrity)**: Do not overwrite Phase 7A, 7B, or 7C deliverables.
3. **Rule R-2 (Recompute, Don't Trust)**: Compute all metrics directly from price series; zero hardcoded statistics.
4. **Rule R-3 (Strict Cash Conservation)**: Total Portfolio Value = Invested Value + Cash. Accounting residual must strictly equal `0.00` to the paisa.
5. **Rule R-10 (Standing Gate Discipline)**: **DO NOT mark HALT-8D as closed.** Halt at **Standing Gate HALT-8D** and await Auditor review.
