# Task List: Phase 8 — Production Execution Screener & Live Deployment Pipeline

## Environment Context
- Device: Samsung Galaxy S23 (Termux PRoot Ubuntu Linux aarch64)
- Engine: Ubuntu system python3 with standard debian/pip packages (`/usr/bin/python3`)
- Deliverables Directory: `deliverables/phase_8/`
- Standing Gate: **HALT-9** (Mandatory pause awaiting Auditor review and verification of live screener and order execution engine)

---

## Execution Roadmap & Gates

- [x] **Task 1: Incremental Bhavcopy Ingestion Engine**:
  - [x] Implement `deliverables/phase_8/scripts/ingest_incremental_bhavcopy.py`
  - [x] Support appending new daily bars (`date, symbol, open, high, low, close, volume`) to parquet store
  - [x] Verify data integrity: unique `(symbol, date)` keys, monotonic sorting, zero null prices
  - [x] Automated self-test passed and master integrity verified (2,137,630 bars, 1,039 symbols, 0 duplicates, 0 nulls)

- [x] **Task 2: Friday EOD Production Screener & Ranker**:
  - [x] Implement `deliverables/phase_8/scripts/screen_production_momentum.py`
  - [x] Ingest active universe, compute 52w High (20%), 200 EMA, Relative Strength, and Volar scores
  - [x] Evaluate 20 EMA Market Regime filter on NIFTY 500
  - [x] Export ranked universe snapshot to `deliverables/phase_8/data_csv/screener_output_sample.csv`
  - [x] Export Run 1 (`screener_output_20260821.csv`) and Run 2 (`screener_output_20260828.csv`)

- [x] **Task 3: Portfolio Rebalance & Execution Order Generator**:
  - [x] Implement `deliverables/phase_8/scripts/generate_execution_orders.py`
  - [x] Ingest current portfolio holdings and apply 100% Exit Buffer (Exit Rank 40)
  - [x] Generate whole-share buy/sell order tickets with target allocation per position (5% per slot for 20 slots)
  - [x] Calculate itemized regulatory & broker charges (STT, brokerage, GST, stamp duty, exchange fees, DP charges)
  - [x] Export machine-readable `data_csv/rebalance_orders_sample.csv` and formatted `data_csv/trade_recommendations_sample.md`
  - [x] Export Run 1 tickets (`rebalance_orders_20260821.csv`) and Run 2 tickets (`rebalance_orders_20260828.csv`)

- [x] **Task 4: Persistent Portfolio Ledger & Execution Simulator**:
  - [x] Implement `deliverables/phase_8/scripts/manage_portfolio_ledger.py`
  - [x] Track holdings, average cost basis, realized/unrealized P&L, and cash balances
  - [x] Enforce Rule R-3 cash conservation: Total Value = Invested Value + Cash (Residual strictly 0.00 to the paisa)
  - [x] Export `deliverables/phase_8/data_csv/portfolio_ledger_sample.csv` and persistent state `portfolio_state.json`

- [x] **Task 5: End-to-End Orchestrator, Dual-Date Live Simulation & Packaging**:
  - [x] Implement `deliverables/phase_8/scripts/run_production_pipeline.py`
  - [x] Execute dual-date simulation across 2026-08-21/24 (initial deployment) and 2026-08-28/31 (weekly rebalance)
  - [x] Author operations manual and tearsheet in `deliverables/phase_8/DIGEST.md`
  - [x] Generate `deliverables/phase_8/EVIDENCE_INDEX.tsv` and `deliverables/phase_8/SHA256SUMS.txt`
  - [x] Package archive into `artifacts/phase_8_deliverables.zip` and `/sdcard/Documents/deliverables/phase_8_deliverables.zip`
  - [x] Dispatch Telegram alert via `/usr/local/bin/telegram-notify`

- [x] **Standing Gate HALT-9: Final Auditor Review & Ruling on Production Pipeline (CLEARED & CLOSED in PHASE_8_RULING.md)**
