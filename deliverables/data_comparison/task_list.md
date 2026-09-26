# Task List: Maximum OHLCV Consolidation, YFinance Ingestion & Comparative Fidelity Audit

## Environment Context
- Device: Samsung Galaxy S23 (Termux PRoot Ubuntu Linux aarch64)
- Engine: Ubuntu system python3 with standard debian/pip packages (`/usr/bin/python3`)
- Deliverables Directory: `deliverables/data_comparison/`

## Execution Roadmap & Gates
- [x] **Task 1: Environment & Dependency Setup**:
  - [x] Install `yfinance` via `/usr/bin/pip install yfinance` (`yfinance-1.7.0` installed via system pip)
  - [x] Verify imports and network reachability to Yahoo Finance (successfully fetched `^NSEI` and `RELIANCE.NS`)

- [x] **Task 2: Maximum Bhavcopy Consolidation (2007–2026)**:
  - [x] Implement `scripts/consolidate_max_bhavcopy.py`
  - [x] Merge `data/price_cache_export.parquet`, `adjusted_bhavcopy_bars_v2.parquet`, and `adjusted_bhavcopy_bars_modern.parquet`
  - [x] Output: `data/adjusted_bhavcopy_max_2007_2026.parquet` (2,137,630 bars across 1,039 symbols, 2007-01-02 to 2026-08-31)
  - [x] Verify zero duplicated `(symbol, date)` keys and strict date ordering

- [x] **Task 3: High-Performance Batched YFinance Ingestion Engine**:
  - [x] Implement `scripts/fetch_yfinance_ohlcv.py` with multi-threaded chunking (50 symbols per batch)
  - [x] Target universe: all 1,149 point-in-time scrips from `data/symbol_map.parquet` and Bhavcopy archive (`<SYMBOL>.NS`)
  - [x] Configure `auto_adjust=False` to preserve both raw OHLC and adjusted data
  - [x] Output: `data/yfinance_ohlcv_2007_2026.parquet` (3,821,604 bars across 1,093 symbols, 100.37 MB)
  - [x] Log unresolvable / delisted tickers to `data_csv/coverage_comparison.csv`

- [x] **Task 4: Comparative Fidelity & Trustability Analysis**:
  - [x] Implement `scripts/audit_yfinance_vs_bhavcopy.py`
  - [x] Coverage audit: Quantify survivorship bias in YFinance (56 scrips / 4.87% purged, e.g. DHFL, RANBAXY)
  - [x] Price discrepancy audit: Compute MAPE (9.11% on Close, 50.23% bars diverging > 1.0%)
  - [x] Corporate action fidelity: Verify 1-day returns across 10 known bonus/split dates (10/10 PASS, 0.00% error)
  - [x] Export: `data_csv/price_tracking_error.csv` and `data_csv/corporate_action_fidelity.csv`

- [x] **Task 5: Comparative Strategy Backtest Re-Run**:
  - [x] Implement `scripts/run_comparative_backtest.py`
  - [x] Execute production momentum strategy (`indian_backtest`) across 2016–2026 using:
    - Run A: Official NSE Bhavcopy dataset (21.75% CAGR, 48.72% Max DD, 497 trades)
    - Run B: YFinance dataset (27.27% CAGR, 38.79% Max DD, 486 trades)
  - [x] Quantify CAGR delta (+5.52 pp artificial inflation) and Max Drawdown delta (-9.93 pp understatement)
  - [x] Export: `data_csv/comparative_backtest_delta.csv`

- [x] **Task 6: Deliverables Compilation & Packaging**:
  - [x] Generate `deliverables/data_comparison/DIGEST.md` with final verdict on YFinance trustability
  - [x] Generate `deliverables/data_comparison/EVIDENCE_INDEX.tsv` and `SHA256SUMS.txt`
  - [x] Bundle zip archive into `artifacts/data_comparison_deliverables.zip`

- [x] **Standing Gate HALT-7: Final Auditor Review & Ruling on Data Fidelity and YFinance Trustability (CLEARED & CLOSED)**
