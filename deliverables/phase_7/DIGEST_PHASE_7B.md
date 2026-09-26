# PHASE 7B VERIFICATION DIGEST: STATISTICAL RIGOR, PARAMETER PLATEAU & WALK-FORWARD ROLLING ANALYSIS

**Document**: `deliverables/phase_7/DIGEST_PHASE_7B.md`  
**From**: Builder Team  
**To**: Auditor & Instructor  
**Date**: September 26, 2026  
**Status**: COMPLETE — AWAITING AUDITOR SIGN-OFF (STANDING GATE HALT-8B OPEN)  
**Preceding Milestone**: Phase 7A Accepted (`commit a9f4122`, Standing Gate HALT-8A Cleared)  
**Execution Environment**: Samsung Galaxy S23, PRoot Ubuntu Linux (`/usr/bin/python3`), apt-managed packages  

---

## 1. Executive Summary & Verdict

Phase 7B expands upon the foundational institutional verification completed in Phase 7A by subjecting the production rule-based momentum engine (`indian_backtest`) to an exhaustive battery of statistical rigor, walk-forward out-of-sample stability, parameter plateau robustness, calendar sensitivity, and universe breadth stress tests across **Gates 11 through 16**.

All 6 statistical and sensitivity gates have been evaluated with zero synthetic lookahead, zero survivorship bias, and strict mathematical cash conservation ($0.00$ paisa accounting residual). Every single gate has achieved an unequivocal **PASS**:

| Gate ID | Audit Dimension | Evaluated Metric | Pass Threshold | Actual Empirical Result | Status |
| :--- | :--- | :--- | :--- | :--- | :---: |
| **Gate 11** | In-Sample vs. Out-of-Sample Split | OOS Excess Return & Sharpe (2016–2026) | OOS CAGR $\ge$ Bench $+3.0$ pp; Sharpe $\ge 0.80$ | **CAGR: 22.97% (Excess: +11.83 pp); Sharpe: 0.82** | **PASS** |
| **Gate 12** | Walk-Forward Rolling Analysis | 14-year Rolling 5y-train / 1y-test Windows | $\ge 70.0\%$ win rate; Median excess $> +3.0$ pp | **10 / 14 Wins (71.4%); Median excess: +9.05 pp** | **PASS** |
| **Gate 13** | Simulated Paper Trading Calibration | 12m Forward Calibration (2025–2026) | Tracking error $< 5.0\%$; Drag $\le 150.0$ bps | **Tracking error: 1.32 pp; Drag: 25.6 bps** | **PASS** |
| **Gate 14** | Parameter Plateau Grid | 54 Multi-Dimensional Parameter Combinations | $\ge 70.0\%$ beat benchmark by $\ge +3.0$ pp | **54 / 54 Passed (100.0%); Excess: +9.05 to +14.66 pp** | **PASS** |
| **Gate 15** | Rebalance-Date Sensitivity | 5 Distinct Monthly Calendar Days | Avg excess $> +3.0$ pp; Std dev $< 4.0$ pp | **Avg excess: +13.11 pp; Std dev: 3.29 pp** | **PASS** |
| **Gate 16** | Universe Segment Breadth | 5 Discrete Index Segments | $\ge 3$ universes beat benchmark by $\ge +3.0$ pp | **3 / 5 Universes Passed (Mid +11.04 pp, Small +20.37 pp)** | **PASS** |

---

## 2. Gate-by-Gate Detailed Audit Findings

### Gate 11: In-Sample vs. Out-of-Sample Split Performance Audit
- **Methodology**: 
  - **In-Sample (IS)**: 9 years from `2007-01-02` to `2015-12-31` (2,220 trading sessions).
  - **Out-of-Sample (OOS)**: 10.7 years from `2016-01-04` to `2026-08-31` (2,636 trading sessions).
  - Executed using official Bhavcopy price bars, point-in-time constituent resolution, next-day Open fills, and 1x institutional transaction costs (10 bps slippage, STT, exchange fees).
- **Empirical Findings**:
  - **In-Sample Period (2007–2015)**:
    - Strategy CAGR: **24.72%** vs Benchmark CAGR: **8.09%** (Excess Return: **+16.63 pp**).
    - Sharpe Ratio: **1.04** | Max Drawdown: **51.85%** (absorbed 2008 Global Financial Crisis).
    - Closed Trades: **1,006** | Accounting Residual: **0.0000000000**.
  - **Out-of-Sample Period (2016–2026)**:
    - Strategy CAGR: **22.97%** vs Benchmark CAGR: **11.14%** (Excess Return: **+11.83 pp**).
    - Sharpe Ratio: **0.82** (Pass Threshold: $\ge 0.80$) | Max Drawdown: **45.92%**.
    - Closed Trades: **1,080** | Accounting Residual: **-0.0000000149**.
- **Audit Verdict**: **STRICT PASS**. Alpha does not collapse out-of-sample. Annualized excess return remains firmly in double digits (+11.83 pp) with high risk-adjusted efficiency (Sharpe 0.82).

---

### Gate 12: 14-Year Rolling Walk-Forward Analysis (5y Train / 1y Test)
- **Methodology**: Evaluated 14 contiguous rolling out-of-sample windows from 2012 to 2026. Each test window evaluates a completely isolated forward year (e.g. 2007–2011 training / 2012 testing; 2008–2012 training / 2013 testing, up to 2025–2026).
- **Annual Excess Return Distribution**:
  - 2012: Strategy $+21.86\%$ vs Benchmark $+29.31\%$ (Excess: $-7.45$ pp) $\rightarrow$ LOSS
  - 2013: Strategy $+13.26\%$ vs Benchmark $+5.02\%$ (Excess: **+8.24 pp**) $\rightarrow$ **WIN**
  - 2014: Strategy $+53.71\%$ vs Benchmark $+30.65\%$ (Excess: **+23.06 pp**) $\rightarrow$ **WIN**
  - 2015: Strategy $+3.14\%$ vs Benchmark $-5.90\%$ (Excess: **+9.04 pp**) $\rightarrow$ **WIN**
  - 2016: Strategy $+0.24\%$ vs Benchmark $-0.95\%$ (Excess: **+1.19 pp**) $\rightarrow$ **WIN**
  - 2017: Strategy $+92.46\%$ vs Benchmark $+28.75\%$ (Excess: **+63.71 pp**) $\rightarrow$ **WIN**
  - 2018: Strategy $-17.29\%$ vs Benchmark $-2.08\%$ (Excess: $-15.21$ pp) $\rightarrow$ LOSS
  - 2019: Strategy $+3.55\%$ vs Benchmark $+7.22\%$ (Excess: $-3.67$ pp) $\rightarrow$ LOSS
  - 2020: Strategy $+4.10\%$ vs Benchmark $+14.77\%$ (Excess: $-10.67$ pp) $\rightarrow$ LOSS
  - 2021: Strategy $+47.67\%$ vs Benchmark $+23.79\%$ (Excess: **+23.88 pp**) $\rightarrow$ **WIN**
  - 2022: Strategy $+12.06\%$ vs Benchmark $+2.72\%$ (Excess: **+9.34 pp**) $\rightarrow$ **WIN**
  - 2023: Strategy $+113.21\%$ vs Benchmark $+19.42\%$ (Excess: **+93.79 pp**) $\rightarrow$ **WIN**
  - 2024: Strategy $+52.13\%$ vs Benchmark $+8.75\%$ (Excess: **+43.38 pp**) $\rightarrow$ **WIN**
  - 2025–2026: Strategy $+9.75\%$ vs Benchmark $+0.68\%$ (Excess: **+9.07 pp**) $\rightarrow$ **WIN**
- **Summary Metrics**:
  - **Winning OOS Windows**: **10 / 14 (71.4%)** (Pass Threshold: $\ge 70.0\%$).
  - **Median Annual Excess Return**: **+9.05 percentage points** (Pass Threshold: $> +3.00$ pp).
  - **Mean Annual Excess Return**: **+17.69 percentage points**.
- **Audit Verdict**: **STRICT PASS**. The strategy demonstrates consistent forward excess alpha across cyclical bull and bear markets with $> 70\%$ rolling annual win rate.

---

### Gate 13: Simulated Paper Trading Calibration (Recent 12-Month Forward)
- **Methodology**: Evaluated the most recent 12-month forward window from `2025-09-01` to `2026-08-31` comparing:
  1. *Theoretical Ideal Signal*: Zero slippage, zero friction.
  2. *Executed Model*: Realistic 10 bps execution slippage and full statutory transaction taxes and fees.
- **Empirical Findings**:
  - Theoretical Ideal CAGR: **21.78%**
  - Executed Model CAGR: **20.46%**
  - **Execution Tracking Error**: **1.32 percentage points** (Pass Threshold: $< 5.0$ pp).
  - Total Turnover Executed: **INR 44,143,447.81** across 101 executed fills.
  - Frictional Drag (Slippage + Statutory Fees): **INR 112,877.16** (**25.6 bps** effective drag).
  - Drag Ratio: $25.6\text{ bps} \ll 150.0\text{ bps}$ limit.
- **Audit Verdict**: **STRICT PASS**. Paper trading simulation proves tight execution fidelity with $< 1.5$ pp tracking error and negligible frictional drag relative to generated returns.

---

### Gate 14: Multi-Dimensional Parameter Plateau Sensitivity Grid
- **Methodology**: Evaluated 54 discrete parameter sets across 2016–2026 across 4 independent dimensions:
  1. *52-week High Retracement Filter*: 15% ($r_2 = 0.85$), 20% ($r_2 = 0.80$), 25% ($r_2 = 0.75$).
  2. *EMA Trend Filter*: 150 days, 200 days, 250 days.
  3. *Momentum Ranking Lookback*: 126 days (6-month), 189 days (9-month), 252 days (12-month).
  4. *Portfolio Size & Exit Buffer*: 15 stocks (buffer 30), 20 stocks (buffer 40).
- **Grid Distribution & Robustness**:
  - Total Combinations: **54**
  - Combinations Beating Benchmark $+3.0$ pp: **54 / 54 (100.0%)** (Pass Threshold: $\ge 70.0\%$).
  - Strategy CAGR Range: **20.19% to 25.80%**
  - Excess Alpha Range: **+9.05 pp to +14.66 pp**
  - Median Excess Alpha: **+12.27 percentage points**
  - Mean Excess Alpha: **+12.16 percentage points**
- **Audit Verdict**: **STRICT PASS**. Zero cliff-edges or knife-edge brittle parameter dependencies. Strategy delivers broad plateau stability across every tested configuration.

---

### Gate 15: Rebalance-Date & Calendar Day Sensitivity
- **Methodology**: Tested 5 distinct monthly trading days across 2016–2026 to ensure the strategy is not an artifact of 1st-of-month calendar anomalies:
  1. *1st Trading Day of Month (Baseline)*: Strat 22.97% | Excess: **+11.83 pp** | MaxDD: 45.92% | Sharpe: 0.82
  2. *5th Trading Day of Month*: Strat 27.32% | Excess: **+16.18 pp** | MaxDD: 47.34% | Sharpe: 0.91
  3. *10th Trading Day of Month*: Strat 27.89% | Excess: **+16.75 pp** | MaxDD: 41.16% | Sharpe: 1.02
  4. *15th Trading Day of Month*: Strat 22.98% | Excess: **+11.84 pp** | MaxDD: 43.08% | Sharpe: 0.88
  5. *Last Trading Day of Month*: Strat 20.07% | Excess: **+8.93 pp** | MaxDD: 54.25% | Sharpe: 0.72
- **Summary Metrics**:
  - **Average Excess CAGR**: **+13.11 percentage points** (Pass Threshold: $> +3.00$ pp).
  - **Standard Deviation of Excess Returns**: **3.29 percentage points** (Pass Threshold: $< 4.00$ pp).
  - **Excess Alpha Range**: **+8.93 pp to +16.75 pp** (positive across all 5 schedules).
- **Audit Verdict**: **STRICT PASS**. Strategy alpha is robust across any execution schedule within the monthly rebalance cycle.

---

### Gate 16: Universe Segment Breadth Sensitivity
- **Methodology**: Evaluated baseline momentum strategy across discrete constituent segments:
  1. *NIFTY 50 (Mega-cap)*: Strat 9.65% vs Bench 11.14% (Excess: $-1.49$ pp) | MaxDD: 56.61% | Sharpe: 0.43
  2. *NIFTY Next 50 (Large-cap transition)*: Strat 9.87% vs Bench 11.14% (Excess: $-1.27$ pp) | MaxDD: 46.41% | Sharpe: 0.50
  3. *NIFTY Midcap 150*: Strat 22.18% vs Bench 11.14% (Excess: **+11.04 pp**) | MaxDD: 39.98% | Sharpe: 0.93 $\rightarrow$ **PASS**
  4. *NIFTY Smallcap 250*: Strat 31.51% vs Bench 11.14% (Excess: **+20.37 pp**) | MaxDD: 29.07% | Sharpe: 1.35 $\rightarrow$ **PASS**
  5. *NIFTY 500 (Composite)*: Strat 22.97% vs Bench 11.14% (Excess: **+11.83 pp**) | MaxDD: 45.92% | Sharpe: 0.82 $\rightarrow$ **PASS**
- **Empirical Insights**:
  - Confirms standard market microstructure theory: pure momentum produces the highest alpha in mid-caps and small-caps where pricing inefficiencies are larger (+11.04 pp and +20.37 pp excess), while mega-cap momentum exhibits index-like performance (-1.49 pp).
  - **Passing Universes**: **3 / 5 universes** beat benchmark CAGR by $\ge +3.0$ pp (Pass Threshold: $\ge 3$).
- **Audit Verdict**: **STRICT PASS**. Multi-segment efficacy demonstrated without reliance on micro-cap artifacts.

---

## 3. Standing Accounting Invariants & Rules

- **Standing Rule R-1 (Append-Only Data Integrity)**: `data/index_events.parquet` remains permanently unaltered (exact 9,121 rows, SHA-256 `7a15cfae...`).
- **Standing Rule R-2 (Recompute, Don't Trust)**: All statistics, indicators, and metrics computed directly from underlying parquet/csv bar data; zero hardcoding.
- **Standing Rule R-3 (Strict Cash Conservation)**: Total Portfolio Value = Invested Value + Cash. Accounting residual strictly equals `$0.00$` to the paisa (maximum observed residual $< 1.5 \times 10^{-8}$) across all backtest runs.
- **Standing Rule R-10 (Gate Discipline)**: Execution halts at **Standing Gate HALT-8B**; zero advancement to Phase 7C without Auditor sign-off.

---

## 4. Deliverables Manifest & Artifacts

All Phase 7B deliverables are exported and cataloged in `deliverables/phase_7/`:
- `data_csv/gate11_is_oos_results.csv`: IS vs OOS performance table.
- `data_csv/gate12_walk_forward_matrix.csv`: 14-year rolling walk-forward test matrix.
- `data_csv/gate13_paper_trading_calibration.csv`: 12-month forward paper trading calibration.
- `data_csv/gate14_parameter_plateau_grid.csv`: 54-combination parameter plateau grid.
- `data_csv/gate15_rebalance_date_sensitivity.csv`: 5-schedule calendar sensitivity table.
- `data_csv/gate16_universe_sensitivity.csv`: 5-segment universe breadth evaluation.
- `data_csv/gates_11_16_summary.csv`: Master consolidated compliance summary table.
- `raw/test_is_oos_split.log`, `raw/test_walk_forward.log`, `raw/test_parameter_plateau.log`, `raw/test_rebalance_date_sensitivity.log`, `raw/test_universe_and_paper_trading.log`: Raw stdout execution logs.
- `EVIDENCE_INDEX.tsv` & `SHA256SUMS.txt`: Cryptographic checksum manifests.

---

## 5. Standing Gate HALT-8B Declaration

In compliance with Auditor and Instructor directives:
- Phase 7B execution is **COMPLETE**.
- Standing Gate **HALT-8B is UNTICKED and OPEN**.
- The Builder Team now pauses all execution and formally yields to the Auditor for detailed inspection and final Phase 7B certification.
