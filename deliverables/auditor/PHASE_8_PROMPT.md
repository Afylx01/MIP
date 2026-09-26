# PHASE 8 DIRECTIVE: PRODUCTION EXECUTION SCREENER & LIVE DEPLOYMENT PIPELINE

**Document**: `deliverables/phase_8/NEXT_TASK.md`  
**From**: Auditor & Lead Quantitative Strategist  
**To**: Builder Team  
**Date**: September 26, 2026  
**Status**: ACTIVE DIRECTIVE  
**Deliverables Directory**: `deliverables/phase_8/`  
**Standing Gate**: **HALT-9** (Mandatory pause awaiting Auditor review and verification of live screener, order generator, and ledger mechanics)

---

## 1. Executive Context & Mission

With Phase 7 formally accepted and all 32 empirical due-diligence gates certified (`is_proven(results) == True`), the systematic momentum strategy (**MIP-1 / MIP-RS / MIP-Volar**) has completed rigorous historical verification.

We now transition from *historical backtesting* to **Live Production Deployment**.

The mission of Phase 8 is to construct an institutional-grade, automated production execution pipeline that runs every weekend:
1. **Incremental Ingestion Engine**: Dynamically ingests recent daily Bhavcopies and keeps the master price grid updated.
2. **Production Momentum Screener**: Executes the verified 5-step momentum screen on Friday EOD data (52-week High within 20%, Close > 200 EMA, Relative Strength > 200 EMA, Volar ranking, and 20 EMA Market Regime filter).
3. **Execution Order Generator**: Compares current portfolio holdings against target top-20 scrips with the 100% Exit Buffer (Exit Rank 40), computing exact whole-share buy/sell order sheets, lot constraints, STT, brokerage, GST, stamp duty, and slippage buffers.
4. **Persistent Portfolio Ledger**: Manages ongoing portfolio state, cash balances, cost basis, and realized P&L, strictly satisfying Rule R-3 cash conservation (residual `0.00`).
5. **Unified Production CLI**: Provides a single production CLI entrypoint to execute the weekly screener and output actionable trade sheets.

---

## 2. Production Strategy Specification (Verified Baseline)

The production engine must implement the exact verified parameters from Phase 7:

| Component | Production Rule | Mathematical Specification |
| :--- | :--- | :--- |
| **Eligible Universe** | Active NIFTY 500 Scrips | Filtered from active listing symbols in Bhavcopy and `symbol_map.parquet` |
| **Filter 1 (Retracement)**| Within 20% of 52-week High | $\text{Close}_t \ge 0.80 \times \max_{i \in [1, 252]}(\text{High}_{t-i})$ |
| **Filter 2 (Trend)** | Above 200-day EMA | $\text{Close}_t > \text{EMA}_{200}(\text{Close})_t$ |
| **Filter 3 (Relative Strength)**| Stock / NIFTY 500 ratio > 200 EMA | $\frac{\text{Close}_t}{\text{Index}_t} > \text{EMA}_{200}\left(\frac{\text{Close}}{\text{Index}}\right)_t$ |
| **Ranking Metric** | Volar (Risk-Adjusted Momentum) | $\text{Score} = \frac{\text{Return}_{252}}{\sigma_{252}}$ (Annualized 252d return / 252d daily std dev) |
| **Portfolio Architecture** | Top 20 Scrips, Equal Weight | Target allocation $w_i = 5.0\%$ of Total Portfolio Value per slot |
| **Exit Buffer (Rank Retention)**| Exit Rank 40 (100% Buffer) | Keep existing holding if Rank $\le 40$; exit if Rank $> 40$ or Filter 2 violated |
| **Market Regime Cash Filter** | NIFTY 500 $<$ 20 EMA | If Index $<$ 20 EMA: **Pause new entries**, hold existing positions, exit dropouts to Cash |
| **Execution Timing** | Signal at Friday Close, Execute Monday Open | Zero look-ahead: signals computed on Friday EOD; orders filled Monday Open |
| **Regulatory & Broker Charges** | Institutional Schedule | Brokerage 0.03%, STT 0.1% on delivery, Stamp Duty 0.015%, Exchange fees, GST 18%, DP ₹15.93 |
| **Slippage Buffer** | 15 bps (0.15%) | Estimated execution market impact buffer |

---

## 3. Technical Tasks for Phase 8

The Builder team must implement modular scripts in `deliverables/phase_8/scripts/` to build and prove the production pipeline.

```
                                  PHASE 8 PRODUCTION WORKFLOW
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ Task 1: Incremental Bhavcopy Ingestion Engine (`scripts/ingest_incremental_bhavcopy.py`)              │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ Task 2: Friday EOD Production Screener & Ranker (`scripts/screen_production_momentum.py`)              │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ Task 3: Portfolio Rebalance & Order Generation Engine (`scripts/generate_execution_orders.py`)        │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ Task 4: Persistent Portfolio Ledger & Execution Simulator (`scripts/manage_portfolio_ledger.py`)      │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ Task 5: End-to-End Orchestrator, Dual-Date Simulation & Deliverables Packaging (`run_pipeline.py`)    │
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

### Task 1: Incremental Bhavcopy Ingestion Engine
- **File**: `deliverables/phase_8/scripts/ingest_incremental_bhavcopy.py`
- **Objective**: Ingest new daily Bhavcopy files into the parquet data store without requiring a complete re-processing of the 20-year history.
- **Requirements**:
  1. Read master parquet dataset: `data/adjusted_bhavcopy_max_2007_2026.parquet`.
  2. Support appending new daily bars (`date, symbol, open, high, low, close, volume`).
  3. Enforce data integrity invariants: unique `(symbol, date)` keys, monotonic sorting, zero null prices.
  4. Provide helper to fetch/verify current EOD bhavcopy from exchange archives or local drop-folder.

---

### Task 2: Friday EOD Production Screener & Ranker
- **File**: `deliverables/phase_8/scripts/screen_production_momentum.py`
- **Objective**: Execute the institutional screening and ranking algorithm as of any target Friday close.
- **Requirements**:
  1. Load price history up to date $T$ (Friday EOD).
  2. Compute 52-week High, 200 EMA, Relative Strength ratio vs NIFTY 500, and Volar score ($\text{Ret}_{252} / \sigma_{252}$).
  3. Evaluate Market Regime: compute NIFTY 500 20-day EMA. Determine whether market is in **Normal Regime** (Entries Active) or **Defensive Regime** (Entries Paused).
  4. Filter eligible candidates and output the ranked table of all qualifying stocks (Ranks 1 to $N$).
  5. Export ranked universe snapshot to `deliverables/phase_8/data_csv/screener_output_sample.csv`.

---

### Task 3: Portfolio Rebalance & Execution Order Generator
- **File**: `deliverables/phase_8/scripts/generate_execution_orders.py`
- **Objective**: Ingest current portfolio holdings and screener output, apply the 100% Exit Buffer, and generate actionable whole-share order recommendations.
- **Requirements**:
  1. Input: `current_portfolio.json` (or ledger state) + `screener_output.csv` + Portfolio AUM (e.g., ₹10,00,000 baseline, or ₹1,00,00,000 institutional).
  2. Apply Rebalance Logic:
     - **SELL / EXIT**: Existing stock whose rank $> 40$, or Close $<$ 200 EMA, or delisted.
     - **HOLD / KEEP**: Existing stock whose rank $\le 40$ and Close $>$ 200 EMA.
     - **BUY / ENTER**: Top-ranked qualifying candidates to fill empty slots up to 20 positions (if Market Regime is Normal; freeze buys if Defensive).
  3. Position Sizing:
     - Target capital per position = $\text{Total Portfolio Value} / 20$.
     - Compute whole share quantities = $\lfloor \text{Target Allocation} / \text{Price} \rfloor$.
  4. Precise Fee Breakdown:
     - Calculate itemized transaction costs: Brokerage (0.03%), STT (0.1% on delivery buy/sell), Stamp duty (0.015% on buy), Exchange turnover (0.00345%), GST (18% on brokerage+turnover), DP charge (₹15.93 per sell), and Slippage buffer (15 bps).
  5. Output:
     - Machine-readable execution sheet: `deliverables/phase_8/data_csv/rebalance_orders_sample.csv`.
     - Human-readable markdown sheet: `deliverables/phase_8/data_csv/trade_recommendations_sample.md`.

---

### Task 4: Persistent Portfolio Ledger & Execution Simulator
- **File**: `deliverables/phase_8/scripts/manage_portfolio_ledger.py`
- **Objective**: Track ongoing portfolio holdings, cash balances, realized capital gains, and corporate actions.
- **Requirements**:
  1. Ledger Schema (`portfolio_ledger.parquet` / `.json`):
     - `symbol, shares, avg_cost_price, current_price, market_value, unrealized_pnl, allocation_pct`
  2. Cash Account Schema:
     - `cash_balance, invested_capital, total_portfolio_value, peak_value, current_drawdown`
  3. Execute Orders:
     - Simulate fill at Monday Open price.
     - Debit/credit cash balance including all itemized transaction charges.
  4. Enforce Rule R-3 Cash Conservation:
     $$\text{Total Portfolio Value} \equiv \text{Invested Market Value} + \text{Cash Balance}$$
     Residual must strictly equal `0.00` to the paisa.

---

### Task 5: End-to-End Orchestrator, Dual-Date Live Simulation & Packaging
- **File**: `deliverables/phase_8/scripts/run_production_pipeline.py`
- **Objective**: Create a unified CLI tool that runs the complete pipeline and demonstrate its execution across two historical test dates to verify reproducibility:
  - **Rebalance Run 1 (As of Friday 2026-08-21)**: Initial portfolio deployment of ₹1,00,00,000 (₹1 Crore) into Top 20 scrips at Monday Open 2026-08-24.
  - **Rebalance Run 2 (As of Friday 2026-08-28)**: Subsequent weekly rebalance at Monday Open 2026-08-31, generating exits, entries, holdings retention, and updated ledger.
- **Deliverables Compilation**:
  1. Author executive guide and operations manual: `deliverables/phase_8/DIGEST.md`.
  2. Generate `deliverables/phase_8/EVIDENCE_INDEX.tsv` and `deliverables/phase_8/SHA256SUMS.txt`.
  3. Generate `deliverables/phase_8/task_list.md` with Standing Gate **HALT-9** unticked.
  4. Package archive into `artifacts/phase_8_deliverables.zip` and `/sdcard/Documents/deliverables/phase_8_deliverables.zip`.
  5. Dispatch Telegram alert via `/usr/local/bin/telegram-notify`.
  6. Pause at **Standing Gate HALT-9** for Auditor inspection.

---

## 4. Required Output Artifacts & Data Schema

The Builder must export standardized files into `deliverables/phase_8/data_csv/`:
1. `screener_output_sample.csv`: Ranked table of all qualifying momentum stocks.
2. `rebalance_orders_sample.csv`: Actionable whole-share buy/sell order tickets with itemized fees.
3. `trade_recommendations_sample.md`: Formatted execution memo for the investment desk.
4. `portfolio_ledger_sample.csv`: Complete holdings breakdown, cost basis, and cash balances.
5. `pipeline_execution_log.txt`: Raw operational execution log in `deliverables/phase_8/raw/`.

---

## 5. Strict Execution Invariants

1. **Rule R-1 (Append-Only Integrity)**: Never mutate or delete previous phase deliverables.
2. **Rule R-2 (Zero Trust / Recompute)**: All technical indicators and ranks must be calculated fresh from the parquet price grid.
3. **Rule R-3 (Strict Cash Conservation)**: Total Portfolio Value = Invested Value + Cash. Accounting residual must equal strictly `0.00` to the paisa.
4. **Rule R-6 (ARM64 PRoot Compatibility)**: Strictly use Ubuntu system python (`/usr/bin/python3`).
5. **Rule R-10 (Standing Gate Discipline)**: **DO NOT proceed past Task 5.** Hold at **Standing Gate HALT-9** until the Auditor delivers a signed ruling.

---

**Directive Status**: ISSUED. Builder may proceed with Phase 8 implementation.
