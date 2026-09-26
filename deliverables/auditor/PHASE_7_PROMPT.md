# PHASE 7 DIRECTIVE: INSTITUTIONAL MOMENTUM VERIFICATION SUITE & 32-GATE DUE-DILIGENCE FRAMEWORK

**Document**: `deliverables/phase_7/NEXT_TASK.md`  
**From**: Auditor & Lead Quantitative Strategist  
**To**: Builder Team  
**Date**: September 25, 2026  
**Status**: ACTIVE DIRECTIVE  
**Deliverables Directory**: `deliverables/phase_7/`  
**Standing Gate**: **HALT-8A** (Mandatory pause awaiting Auditor review and verification of Gates 1–10)

---

## 1. Executive Context & Objectives

Following the certification of the 20-year consolidated Bhavcopy dataset (`data/adjusted_bhavcopy_max_2007_2026.parquet` with 2,137,630 bars across 1,039 symbols) and the clearance of HALT-7, Project MIP enters **Phase 7: The Institutional Due-Diligence & Verification Suite**.

We now implement the comprehensive **32-Gate Institutional Backtester Test Plan** inspired by rigorous institutional asset management standards and quantitative momentum literature. To ensure complete architectural reliability and avoid monolithic execution errors, Phase 7 is partitioned into four structured, auditable sub-phases:

```
                                  PHASE 7 EXECUTION ARCHITECTURE
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ Phase 7A: Data Integrity, Execution Realism & Cost Stress Testing (Gates 1–10)  --> [HALT-8A]          │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ Phase 7B: Statistical Rigor, Walk-Forward & Parameter Plateau Sensitivity (Gates 11–16) --> [HALT-8B] │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ Phase 7C: 6-Regime Stress Test, Monte Carlo & Core Risk Distribution (Gates 17–25)     --> [HALT-8C] │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ Phase 7D: Component Attribution, Variants & Production Go/No-Go Engine (Gates 26–32)   --> [HALT-8D] │
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

The Builder team is hereby directed to execute **Phase 7A (Gates 1–10)** immediately. Subsequent phases will be unlocked sequentially upon formal Auditor acceptance rulings.

---

## 2. Baseline Momentum Strategy Specification (MIP-1 / MIP-RS / MIP-Volar)

All test gates must evaluate the following standardized baseline momentum model:

| Parameter / Rule | Production Specification | Mathematical Definition |
| :--- | :--- | :--- |
| **Universe** | Point-in-Time NIFTY 500 | Active constituents on rebalance date from `data/symbol_map.parquet` & Bhavcopy |
| **Filter 1 (High Retracement)** | Within 20% of 52-week High | $\text{Close}_t \ge 0.80 \times \max_{i \in [1, 252]}(\text{High}_{t-i})$ |
| **Filter 2 (Trend Filter)** | Above 200-day EMA | $\text{Close}_t > \text{EMA}_{200}(\text{Close})_t$ |
| **Filter 3 (Relative Strength)**| Stock / NIFTY 500 ratio > 200 EMA | $\frac{\text{Close}_t}{\text{Index}_t} > \text{EMA}_{200}\left(\frac{\text{Close}}{\text{Index}}\right)_t$ |
| **Ranking Metric** | 252-day Return or Volar | Raw: $\frac{P_t}{P_{t-252}} - 1$ \| Volar: $\frac{\text{Return}_{252}}{\sigma_{252}}$ |
| **Portfolio Sizing** | Top 20 Scrips, Equal Weight | Target weight $w_i = 5.0\%$ per position (max 20 slots) |
| **Exit Buffer (Rank Retention)**| Exit Rank 40 (100% buffer) | Hold stock while rank $\le 40$; exit if rank $> 40$ or Filter 2 violated |
| **Rebalance Schedule** | Monthly, 1st Trading Day | Re-evaluate universe, rank, and rebalance on first valid session of each month |
| **Market Regime Cash Filter** | NIFTY 500 $<$ 20 EMA | If Index $<$ 20 EMA: **pause new entries**, hold surviving positions, exit dropouts to cash |
| **Execution Timing** | Signal at Close $t$, Execute $t+1$ Open | Zero look-ahead: signals generated EOD $t$; trades executed at Open price $t+1$ |
| **Realistic Costs** | Institutional Tiered Schedule | Round-trip: Large-cap 0.35%, Mid/Small-cap 0.75%, Micro-cap 1.25% + STT + GST |
| **Benchmark** | NIFTY 500 TRI / NIFTY 50 TRI | Ingested from verified benchmark series (`data/benchmarks/NIFTY_50.csv`) |

---

## 3. Phase 7A Technical Tasks: Data Integrity, Execution Realism & Cost Stress (Gates 1–10)

The Builder must write modular, self-contained verification scripts in `deliverables/phase_7/scripts/` to execute and prove Gates 1 through 10.

### Task 1: Engine Configuration & Benchmark Ingestion
- Create `deliverables/phase_7/scripts/init_phase7_engine.py`.
- Ingest `data/adjusted_bhavcopy_max_2007_2026.parquet` and `data/benchmarks/NIFTY_50.csv`.
- Implement NIFTY 500 benchmark proxy and verify alignment of calendar dates (2007–2026).
- Verify that `indian_backtest` can execute the baseline parameters seamlessly.

---

### Task 2: Data Integrity & Survivorship Verification (Gates 1, 2, 3, 4)
Implement `deliverables/phase_7/scripts/test_data_integrity.py` covering:

- **Gate 1: Point-in-Time Universe Audit**:
  - *Requirement*: At every monthly rebalance from 2007 to 2026, verify that the eligible candidate universe strictly contains historical constituents, not current survivors.
  - *Pass Threshold*: 100% of rebalances use verifiable point-in-time constituent lists.
  - *Fail Threshold*: Any presence of modern-only tickers in historical rebalance pools.

- **Gate 2: Delisting & Survivorship Invariant**:
  - *Requirement*: Verify that delisted, acquired, and bankrupt stocks from `data/verification/survivorship_graveyard.csv` (e.g. `DHFL`, `RANBAXY`, `AMTEKINDIA`, `JPASSOCIAT`) enter the strategy when valid, and execute terminal liquidation returns upon delisting.
  - *Pass Threshold*: 100% of vanished stocks have recorded terminal liquidation; zero silently dropped scrips.
  - *Fail Threshold*: Purging or ignoring delisted constituents.

- **Gate 3: Look-Ahead Bias Proof**:
  - *Requirement*: Mathematically prove that signals generated at EOD $t$ utilize strictly information up to $t$ (shifted by 1 day), and trade execution is filled at $t+1$ Open.
  - *Pass Threshold*: Strictly $t+1$ Open execution; zero look-ahead in rolling indicators or filters.
  - *Fail Threshold*: Any same-day Close execution ($t$ Close signal executed at $t$ Close).

- **Gate 4: Corporate Action Integrity**:
  - *Requirement*: Audit all 1-day trade returns across verified bonus/split dates.
  - *Pass Threshold*: Corporate actions do not generate artificial 1-day moves $> 5.0\%$.
  - *Fail Threshold*: Presence of unadjusted split drop artifacts.

- *Output*: Export evidence to `deliverables/phase_7/data_csv/gates_1_4_integrity_audit.csv`.

---

### Task 3: Execution Realism & Circuit Limit Simulation (Gates 9, 10)
Implement `deliverables/phase_7/scripts/test_execution_constraints.py` covering:

- **Gate 9: Execution Delay & Timing Sensitivity**:
  - *Requirement*: Run identical strategy across three execution models:
    1. Execution at $t+1$ Open.
    2. Execution at $t+1$ VWAP (approximated as $(O + H + L + C) / 4$).
    3. Execution at $t+2$ Open (1-day operational delay).
  - *Pass Threshold*: $t+1$ VWAP CAGR within 20% relative to $t+1$ Open; positive alpha maintained under $t+2$ execution.
  - *Fail Threshold*: Strategy collapses or only works with zero-delay execution.

- **Gate 10: Circuit Limit & Tradability Guard**:
  - *Requirement*: Model daily upper and lower price bands (5%, 10%, 20% circuits). If a stock hits Upper Circuit on $t+1$, BUY orders cannot be executed. If a stock hits Lower Circuit on $t+1$, SELL orders cannot exit until the circuit opens.
  - *Pass Threshold*: $> 80\%$ of intended trades fully executable on the scheduled rebalance date.
  - *Fail Threshold*: $> 20\%$ of rebalance trades permanently blocked by circuit locks.

- *Output*: Export evidence to `deliverables/phase_7/data_csv/gates_9_10_execution_constraints.csv`.

---

### Task 4: Transaction Cost & Slippage Stress Matrix (Gates 5, 6, 7, 8)
Implement `deliverables/phase_7/scripts/test_cost_sensitivity.py` covering:

- **Gate 5: Base Institutional Cost Model**:
  - Brokerage: 0.03% or institutional flat.
  - STT: 0.1% on delivery Buy/Sell.
  - Exchange turnover fees, SEBI charges, Stamp duty (0.015%), GST (18%).
  - Slippage: 0.10% baseline.
  - *Pass Threshold*: Net CAGR $>$ Benchmark CAGR + 4.0 percentage points.
  - *Fail Threshold*: Net CAGR $<$ Benchmark CAGR + 2.0 percentage points.

- **Gate 6: 2x Cost Stress Test**:
  - Double all brokerage, exchange fees, STT, and slippage (Round-trip drag ~1.50%).
  - *Pass Threshold*: Net CAGR remains $>$ Benchmark CAGR + 2.0 percentage points.
  - *Fail Threshold*: Strategy alpha disappears or drops below benchmark.

- **Gate 7: 3x Cost Stress Test**:
  - Triple all execution friction costs (Round-trip drag ~2.25%).
  - *Pass Threshold*: Net excess return over benchmark remains strictly positive ($> 0.0\%$).
  - *Fail Threshold*: Negative excess return (strategy destroyed by friction).

- **Gate 8: Slippage Sensitivity Ladder**:
  - Evaluate discrete slippage tiers: $0.10\%$, $0.25\%$, $0.50\%$, and $1.00\%$ per trade.
  - *Pass Threshold*: Max Drawdown increase $< 10$ percentage points; CAGR degradation $< 30\%$ relative across the ladder.
  - *Fail Threshold*: CAGR drops below benchmark at $\le 0.50\%$ slippage.

- *Output*: Export evidence to `deliverables/phase_7/data_csv/gates_5_8_cost_stress_matrix.csv`.

---

### Task 5: Compilation of Phase 7A Deliverables & Standing Gate HALT-8A
- Compile all execution outputs, metrics, and tearsheets into `deliverables/phase_7/DIGEST.md`.
- Generate `deliverables/phase_7/EVIDENCE_INDEX.tsv` and `deliverables/phase_7/SHA256SUMS.txt`.
- Generate `deliverables/phase_7/task_list.md` with Standing Gate HALT-8A initially UNTICKED and OPEN.
- Package deliverables into `artifacts/phase_7a_deliverables.zip` and `/sdcard/Documents/deliverables/phase_7a_deliverables.zip`.
- Halt execution and await Auditor inspection.

---

## 4. Required Output Artifacts & Data Schema

All backtest runs across Phase 7 must export standardized data tables in `deliverables/phase_7/data_csv/`:

1. **Daily Portfolio Series** (`daily_equity_curves.csv`):
   - `date, portfolio_value, cash_balance, invested_capital, benchmark_value, drawdown, active_positions`
2. **Monthly Returns Table** (`monthly_returns.csv`):
   - `year, month, strategy_return, benchmark_return, excess_return`
3. **Comprehensive Trade Log** (`trade_log.csv`):
   - `trade_id, ticker, signal_date, exec_date, side, shares, price, gross_value, net_costs, slippage, exit_reason`
4. **Holdings & Universe Snapshots** (`monthly_holdings_snapshots.parquet`):
   - Snapshot of all 20 holdings, rank, weight, and valuation at each monthly rebalance.
5. **Gates 1–10 Verification Summary** (`gates_1_to_10_summary.csv`):
   - Metric, Test Name, Pass Threshold, Fail Threshold, Actual Value, Test Status (PASS/FAIL).

---

## 5. Strict Execution Invariants

The Builder must adhere without exception to the project's standing laws:
1. **Rule R-1 (Append-Only Integrity)**: Never mutate or overwrite historical verified deliverables.
2. **Rule R-2 (Recompute, Don't Trust)**: Compute all metrics directly from price series; zero hardcoded statistics.
3. **Rule R-3 (Strict Cash Conservation)**: Total Portfolio Value = Invested Market Value + Cash + Unsettled Dues. Accounting residual must equal `0.00` to the paisa at every timestamp.
4. **Rule R-6 (ARM64 PRoot Compatibility)**: Strictly use Ubuntu system python (`/usr/bin/python3`). Zero external GUI dependencies.
5. **Rule R-10 (Standing Gate Discipline)**: **DO NOT proceed past Task 5.** Hold at **Standing Gate HALT-8A** until the Auditor delivers a signed ruling.

---

**Directive Status**: ISSUED. Builder may proceed with Phase 7A implementation.
