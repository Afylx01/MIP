# NEXT TASK: PHASE 5.5 GATES C & D BUILD PROMPT — CONTINUITY & RECONSTRUCTED BASELINE BACKTEST

**Prior Phase**: Phase 5.5 Gates A & B (Status: **ACCEPT**, median joint coverage 87.03% >= 85.0% PASS, min resolved 86.40% >= 80.0% R-5, 22-year replay: 0 orphan OUTs, 0 duplicate INs, snapshot count strictly [500, 501])  
**Target Phase**: Phase 5.5 Gates C & D (Multi-Index Continuity Audit, Point-in-Time Universe Reconstruction & Comparative Baseline Backtest Re-Run)  
**Deliverables Directory**: `deliverables/gate_cd/`  
**Standing Gate**: **HALT-4** (Mandatory pause for Auditor review of Gates C & D before Gates E & F)  
**Workspace Root**: `/storage/emulated/0/Documents/Project MIP`  
**Execution Environment**: Samsung Galaxy S23, PRoot Ubuntu Linux (`/usr/bin/python3`), apt-managed packages  

---

## 0. MANDATE & STRATEGIC CONTEXT

With Gates A and B fully verified and accepted by the Auditor, **HALT-3 is CLEARED**.

You are now the **builder** for Phase 5.5 Gates C & D. Your mandate is:
1. **Gate C**: Complete multi-index continuity verification across all 7 broad market indices in `data/index_events.parquet`.
2. **Gate D**: Reconstruct point-in-time universe membership and execute the comparative baseline backtest re-run over the clamped window (`2016-01-04` to `2020-09-14`) comparing:
   - **Run (a)**: Survivor-biased current constituents (old baseline).
   - **Run (b)**: Point-in-time dynamic constituents (reconstructed universe using approved corrections and symbol map).

---

## 1. NON-NEGOTIABLE CONSTRAINTS & AUDITOR RULES

1. **Append-Only Integrity**: `data/index_events.parquet` must remain 100% unaltered. Approved corrections in `data/corrections.parquet` are layered dynamically during universe reconstruction.
2. **Strategy Rules Strictly Frozen**:
   - R2: `close >= 0.80 * max(close[t-252:t])`
   - R3: `close > EMA200(close)`
   - R5: Rank by 252-trading-day return descending
   - R6: Equal weight entry; retained stocks not rebalanced; exit proceeds split equally among entrants
   - R7: Rebalance first trading day of each month
   - R8: Next-day open execution
   - R9: `exit_rank = 40 = 2 * N`; held stock failing R2 or R3 exits
   - Portfolio size: $N = 20$
   - Absolutely no parameter changes, no optimization, no rule relaxation.
3. **Mathematical Identity (Standing Rule R-3)**:
   Every backtest must satisfy:
   $$\text{initial\_capital} + \text{realized\_pnl} - \text{tax} + \text{dividends} + \text{unrealized\_pnl} == \text{final\_value}$$
   with residual **exactly 0.00**. Any nonzero residual is an immediate rejection.
4. **Reproducibility (Standing Rule R-6)**:
   Both runs must be executed twice, diffed, and proven byte-identical.
5. **Coverage Disclosure (Standing Rule R-5)**:
   Disclose the exact point-in-time coverage line for Run (b) (median joint coverage 87.03%).

---

## 2. ACCEPTANCE CRITERIA

### Gate C (Continuity Audit):
- For NIFTY500 across full history: orphan OUTs == 0, duplicate INs == 0 (already established in Gate B).
- For the other 6 broad market indices (`NIFTY50`, `NIFTYNEXT50`, `NIFTY100`, `NIFTY200`, `NIFTYMIDCAP100`, `NIFTYSMALLCAP100`):
  - Audit and report total IN events, total OUT events, orphan OUTs, and duplicate INs.
  - Document any unlinked events or index-specific structural anomalies.
- Zero blocked events for approved scrips.

### Gate D (Reconstruction & Backtest Re-Run):
1. **Reconstruction**:
   - Rebuild NIFTY500 membership as-of `2016-01-04` (window start) and as-of `2020-09-14` (`covered_end`).
   - Print both counts, the count of start symbols not in the end set, and the count of end symbols not in the start set.
2. **Dual Backtest Execution**:
   - Run (a): Current constituents (survivor-biased baseline).
   - Run (b): Point-in-time dynamic membership using `snapshot_constituents_57.csv` and adjusted Bhavcopy bars.
   - Both runs over the exact same trading calendar days (`data/trading_calendar.txt`).
3. **Attribution & Comparative Output**:
   - Report initial capital, final value, net profit, CAGR, Max Drawdown, Sharpe ratio for both runs.
   - Attribute the delta: list symbols held in Run (a) but not Run (b), and vice-versa, detailing how universe differences drive performance divergence.
4. **Price Coverage Verification**:
   - Confirm zero snapshots in Run (b) have $> 20$ symbols with $> 30\%$ missing bars.

---

## 3. EXECUTION STEPS & SCRIPTS

### Step 1: Gate C — Multi-Index Continuity Script
- Script: `deliverables/gate_cd/scripts/gate_c_continuity.py`
- Ingest `data/index_events.parquet` and `data/corrections.parquet`.
- Compute continuity statistics across all 7 broad market indices.
- Export:
  - `deliverables/gate_cd/data_csv/gate_c_continuity_summary.csv`
  - `deliverables/gate_cd/raw/gate_c_continuity.txt`

### Step 2: Gate D — Universe Reconstruction & Price Gap Audit
- Script: `deliverables/gate_cd/scripts/gate_d_reconstruct.py`
- Audit Bhavcopy price coverage for all dynamic constituents in the 57 monthly snapshots.
- Export:
  - `deliverables/gate_cd/data_csv/reconstructed_turnover.csv`
  - `deliverables/gate_cd/data_csv/price_gaps.csv`
  - `deliverables/gate_cd/raw/gate_d_reconstruct.txt`

### Step 3: Gate D — Comparative Backtest Engine Execution
- Script: `deliverables/gate_cd/scripts/gate_d_backtest_runner.py`
- Execute Run (a) and Run (b) twice for byte-identical reproducibility.
- Verify the identity residual: `abs(residual) < 1e-6`.
- Export:
  - `deliverables/gate_cd/data_csv/backtest_comparison_metrics.csv`
  - `deliverables/gate_cd/data_csv/holdings_attribution.csv`
  - `deliverables/gate_cd/raw/gate_d_backtest_run_a.txt`
  - `deliverables/gate_cd/raw/gate_d_backtest_run_b.txt`

### Step 4: Deliverables Compilation & HALT-4
- Script: `deliverables/gate_cd/scripts/generate_evidence_index.py`
- Compile:
  - `deliverables/gate_cd/DIGEST.md`
  - `deliverables/gate_cd/EVIDENCE_INDEX.tsv`
  - `deliverables/gate_cd/task_list.md`: Tick Gate C and Gate D; leave **HALT-4 UNTICKED and OPEN**.
- Dispatch Telegram alert via `/usr/local/bin/telegram-notify`.
- **HALT-4 MANDATORY PAUSE**: Cease execution and notify the Auditor. Await formal ruling before proceeding to Gates E & F.
