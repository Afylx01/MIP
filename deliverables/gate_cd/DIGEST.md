# GATES C & D DIGEST

Status: COMPLETE (PASS)
One-line summary: Executed multi-index continuity audit across all 7 broad market indices (Gate C: NIFTY500 0 orphan OUTs, 0 duplicate INs, 0 blocked events; 6 other indices structural anomalies documented), point-in-time universe reconstruction (500 start, 501 end, 32.67% turnover; 0 snapshots exceeding price gap thresholds), and comparative baseline backtest re-run over clamped window 2016–2020 (Gate D: Run (a) survivor CAGR 16.62% vs Run (b) point-in-time CAGR 12.92%, delta -3.70 pp; Standing Rule R-3 accounting residual strictly 0.00; Standing Rule R-6 reproducibility 100% byte-identical), holding standing gate HALT-4 open.
Auditor & Governance Rules Honored: Append-only event log preserved (`data/index_events.parquet` unaltered, 9,121 rows), strategy rules strictly frozen (R2, R3, R5, R6, R7, R8, R9, N=20), accounting identity verified with residual == 0.00 (Rule R-3), dual execution byte-identical reproducibility verified (Rule R-6), point-in-time coverage line disclosed (median joint coverage 87.03%, Rule R-5), standing gate HALT-4 left UNTICKED and OPEN awaiting Auditor review.

## Gate C — Multi-Index Continuity Audit across 7 Broad Market Indices

Claim: Audited continuity across all 7 broad market indices in `data/index_events.parquet` layering approved corrections from `data/corrections.parquet`. Confirmed for NIFTY500 full history (1998–2020): exactly 0 orphan OUTs and 0 duplicate INs with 501 final active constituents. For the other 6 indices (`NIFTY50`, `NIFTYNEXT50`, `NIFTY100`, `NIFTY200`, `NIFTYMIDCAP100`, `NIFTYSMALLCAP100`), documented total INs, total OUTs, and the structural anomaly of missing initial seed batches (explaining orphan OUTs from unseeded initial constituent removals). Isolated sheet-level anomalies (SAIL trailing period in NIFTYNEXT50, Indiabulls Real Estate duplicate IN in NIFTYMIDCAP100). Verified 0 blocked events for approved scrips across all 7 indices.
Evidence: `deliverables/gate_cd/data_csv/gate_c_continuity_summary.csv` and `deliverables/gate_cd/raw/gate_c_continuity.txt`
Excerpt (max 5 lines, source-labeled):
```
[gate_c_continuity.txt:23]   >> NIFTY500 Invariants Verified: 0 orphan OUTs, 0 duplicate INs, 501 active constituents. (PASS)
[gate_c_continuity.txt:104] Assertion 1 PASSED: NIFTY500 full history orphan OUTs == 0.
[gate_c_continuity.txt:105] Assertion 2 PASSED: NIFTY500 full history duplicate INs == 0.
[gate_c_continuity.txt:106] Assertion 3 PASSED: Zero blocked events for approved scrips across all 7 indices.
[gate_c_continuity.txt:107] Assertion 4 PASSED: Multi-index continuity statistics and structural anomalies documented for all 6 other indices.
```

### Multi-Index Continuity Summary Table

| Index Name | Earliest Date | Latest Date | Total Events | Total INs | Total OUTs | Orphan OUTs | Duplicate INs | Final Active | Blocked Events | Seed Batch Present | Continuity Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **NIFTY500** | 1998-08-01 | 2020-09-14 | 2,493 | 1,497 | 996 | **0** | **0** | 501 | 0 | True (500 seed) | **PASS** |
| **NIFTY50** | 1996-09-18 | 2020-07-31 | 196 | 98 | 98 | 51 | 0 | 51 | 0 | False (changes only)| PASS (Audit) |
| **NIFTYNEXT50** | 2000-01-12 | 2020-07-31 | 382 | 191 | 191 | 75 | 1 | 74 | 0 | False (changes only)| PASS (Audit) |
| **NIFTY100** | 2003-03-19 | 2020-07-31 | 336 | 168 | 168 | 82 | 0 | 82 | 0 | False (changes only)| PASS (Audit) |
| **NIFTY200** | 2011-11-22 | 2020-07-31 | 464 | 232 | 232 | 111 | 0 | 111 | 0 | False (changes only)| PASS (Audit) |
| **NIFTYMIDCAP100** | 2005-12-08 | 2020-06-26 | 592 | 296 | 296 | 105 | 1 | 104 | 0 | False (changes only)| PASS (Audit) |
| **NIFTYSMALLCAP100** | 2011-05-03 | 2020-06-26 | 594 | 297 | 297 | 102 | 0 | 102 | 0 | False (changes only)| PASS (Audit) |

---

## Gate D — Point-in-Time Universe Reconstruction & Price Gap Audit

Claim: Reconstructed point-in-time NIFTY500 membership as-of window start (2016-01-04: 500 constituents) and as-of covered end (2020-09-14: 501 constituents). Computed gross turnover metrics: 163 start constituents removed by end, 164 constituents added since start, 337 retained/common constituents (32.67% turnover). Audited daily Bhavcopy price coverage for all dynamic constituents across all 57 monthly snapshots: zero snapshots had > 20 symbols with > 30% missing bars (maximum observed was exactly 1 symbol in only 5 snapshots; 52 snapshots had 0 gaps).
Evidence: `deliverables/gate_cd/data_csv/reconstructed_turnover.csv`, `deliverables/gate_cd/data_csv/price_gaps.csv`, and `deliverables/gate_cd/raw/gate_d_reconstruct.txt`
Excerpt (max 5 lines, source-labeled):
```
[gate_d_reconstruct.txt:13] As-of Window Start (2016-01-04): 500 constituents
[gate_d_reconstruct.txt:14] As-of Covered End  (2020-09-14):   501 constituents
[gate_d_reconstruct.txt:38]   Snapshots with >20 Symbols with >30% Missing Bars: 0 (expected: 0)
[gate_d_reconstruct.txt:49] Assertion 1 PASSED: Start count 500 == 500, End count 501 == 501.
[gate_d_reconstruct.txt:50] Assertion 2 PASSED: Zero snapshots have > 20 symbols with > 30% missing bars (max observed: 1 <= 20).
```

---

## Gate D — Comparative Baseline Backtest Re-Run

Claim: Executed comparative baseline backtest over the clamped window (2016-01-04 to 2020-09-14, 1,154 trading days, 57 monthly rebalance snapshots) comparing survivor-biased Run (a) against point-in-time dynamic Run (b) under frozen strategy rules (R2, R3, R5, R6, R7, R8, R9, N=20). Verified Standing Rule R-3 accounting identity with residual == 0.00000000 on both runs. Verified Standing Rule R-6 reproducibility by executing both runs twice and asserting 100% byte-identical logs. Quantified survivorship bias: Run (a) CAGR was 16.62% vs Run (b) CAGR of 12.92% (delta -3.70 percentage points; net profit delta -Rs. 2,890,879.20; Max Drawdown +3.67 pp higher in Run b).
Evidence: `deliverables/gate_cd/data_csv/backtest_comparison_metrics.csv`, `deliverables/gate_cd/data_csv/holdings_attribution.csv`, `deliverables/gate_cd/raw/gate_d_backtest_run_a.txt`, and `deliverables/gate_cd/raw/gate_d_backtest_run_b.txt`
Excerpt (max 5 lines, source-labeled):
```
[gate_d_backtest_runner.py:20] Rule R-6 PASSED: Run (a) execution is 100% byte-identical across passes.
[gate_d_backtest_runner.py:24] Rule R-6 PASSED: Run (b) execution is 100% byte-identical across passes.
[gate_d_backtest_runner.py:28] Rule R-3 PASSED on Run (a): Residual is exactly 0.00.
[gate_d_backtest_runner.py:31] Rule R-3 PASSED on Run (b): Residual is exactly 0.00.
[gate_d_backtest_runner.py:44] GATE D STEP 3 COMPLETE: COMPARATIVE BACKTEST EXECUTED & AUDITED (PASS)
```

### Backtest Comparative Metrics Table

| Metric | Run (a): Survivor Baseline | Run (b): Point-in-Time Dynamic | Delta (Run b - Run a) | Attribution & Auditor Status |
|---|---|---|---|---|
| **Universe Description** | Fixed Current Constituents (2020-09) | Reconstructed Point-in-Time | Reconstructed Dynamic PIT | Evaluated across 57 snapshots |
| **Universe Coverage Line** | Survivor constituents (458 symbols) | PIT dynamic (median joint cov 87.03%) | Disclosed per Standing Rule R-5 | Mandated disclosure honored |
| **Clamped Window Start** | 2016-01-04 | 2016-01-04 | 0 days | Identical trading calendar |
| **Clamped Window End** | 2020-09-14 | 2020-09-14 | 0 days | Identical trading calendar |
| **Total Trading Days** | 1,154 days | 1,154 days | 0 days | Identical trading calendar |
| **Years Elapsed** | 4.6954 years | 4.6954 years | 0.0000 | Calendar basis (365.25 d/yr) |
| **Initial Capital** | Rs. 10,000,000.00 | Rs. 10,000,000.00 | Rs. 0.00 | Equal entry allocation |
| **Final Portfolio Value** | **Rs. 20,585,753.10** | **Rs. 17,694,873.90** | **-Rs. 2,890,879.20** | **Survivorship bias impact** |
| **Net Profit** | **Rs. 10,585,753.10** | **Rs. 7,694,873.90** | **-Rs. 2,890,879.20 (-27.3%)**| **Realistic PIT returns** |
| **CAGR (%)** | **16.62%** | **12.92%** | **-3.70 percentage points** | **Survivorship bias premium** |
| **Max Drawdown (%)** | **44.36%** | **48.03%** | **+3.67 pp (higher drawdown)**| **PIT reflects market stress** |
| **Sharpe Ratio** | **0.80** | **0.68** | **-0.12** | **Risk-adjusted divergence** |
| **Total Trades Executed** | 300 trades | 309 trades | +9 trades | Dynamic membership turnover |
| **Closed Trades** | 280 trades | 289 trades | +9 trades | Dynamic membership exits |
| **Open Positions at End** | 20 positions | 20 positions | 0 positions | Target portfolio size N=20 |
| **Accounting Residual** | **0.00000000** | **0.00000000** | **0.00** | **Rule R-3 STRICT PASS (0.00)** |
| **Reproducibility** | **Byte-Identical** | **Byte-Identical** | **Diff: 0 bytes** | **Rule R-6 STRICT PASS** |

---

## Holdings Attribution & Root Cause Analysis of Performance Divergence

The comparative backtest demonstrates the quantitative impact of survivorship bias on quantitative momentum strategies:

1. **Survivorship Bias Premium (+3.70% CAGR)**:
   - The survivor-biased baseline (Run a) yields a CAGR of **16.62%**, whereas the point-in-time dynamic backtest (Run b) yields **12.92%**.
   - Survivorship bias artificially inflated net profits by **+Rs. 2,890,879.20 (+27.3%)** and understated maximum drawdown by **3.67 percentage points** (44.36% vs 48.03%).

2. **Holdings Attribution Breakdown (233 Unique Symbols Traded)**:
   - **Symbols Traded Only in Run (a)**: 17 symbols (e.g., `VENKEYS`, `HSCL`, `TIMETECHNO`).
     * `VENKEYS`: Generated +Rs. 1,164,126.00 in Run (a), but was not eligible in Run (b) during that phase, accounting for 40.3% of the total profit divergence!
     * `HSCL`: Generated +Rs. 387,816.80 in Run (a), but was absent in Run (b).
   - **Symbols Traded Only in Run (b)**: 34 symbols (e.g., `PCJEWELLER`, `ADANIENT`, `ORIENTELEC`, `LINDEINDIA`, `WELCORP`).
     * `PCJEWELLER`: Was an active NIFTY500 constituent in 2016–2018 before suffering a severe collapse and index exclusion. Run (b) held `PCJEWELLER` according to point-in-time rules and realized a loss of **-Rs. 292,600.00**. Run (a) had complete survivor foresight, excluding `PCJEWELLER` entirely from the universe.
     * `WELCORP`, `TATAGLOBAL`, `ADANIENT`: Dynamic entrants that incurred drawdowns during their index tenure.
   - **Symbols Traded in Both Runs**: 182 symbols.
     * Differences in cash flow timing, entrant capital availability, and relative rank ordering caused performance divergence even among shared symbols (e.g., `GRAPHITE`, `VMART`, `BHARATRAS`).

3. **Standing Rule Compliance**:
   - **Rule R-3 (Mathematical Identity)**: $\text{initial\_capital} + \text{realized\_pnl} - \text{tax} + \text{dividends} + \text{unrealized\_pnl} == \text{final\_value}$ with residual strictly **0.00** across both runs.
   - **Rule R-6 (Reproducibility)**: Both runs executed twice, diffed, and confirmed 100% byte-identical.
   - **Rule R-5 (Coverage Disclosure)**: Median joint coverage line (**87.03%**) explicitly disclosed.

---

## Standing Gate HALT-4 Status

Standing gate **HALT-4: Stop and wait for auditor review of Gates C & D deliverables** is deliberately left **UNTICKED and OPEN**.

In accordance with Auditor instructions, all builder execution is halted. The deliverables are frozen and submitted for Auditor inspection and formal ruling before proceeding to Gates E & F.
