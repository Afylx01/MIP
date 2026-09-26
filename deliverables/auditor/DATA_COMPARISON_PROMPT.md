# PHASE DIRECTIVE: MAXIMUM OHLCV CONSOLIDATION, BATCHED YFINANCE INGESTION & COMPARATIVE FIDELITY AUDIT

**Document**: `deliverables/data_comparison/NEXT_TASK.md`  
**From**: Auditor & Instructor  
**To**: Builder Team  
**Date**: September 25, 2026  
**Status**: ACTIVE DIRECTIVE  
**Deliverables Directory**: `deliverables/data_comparison/`  
**Standing Gate**: **HALT-7** (Mandatory pause awaiting Auditor review and ruling)

---

## 1. Context & Motivation

With Phase 5.6 and Phase 6 formally accepted, Project MIP has verified 28 years of point-in-time universe continuity (1998–2026) and delivered the production-grade `indian_backtest` package with Relative Strength (E1) and the 200 EMA Market Regime Cash Filter (E4).

We now execute a dual objective:
1. **Maximize the Historical Ground-Truth Bhavcopy Grid**:
   Consolidate all available daily Bhavcopy price archives into a single continuous, verified dataset spanning **January 2007 to August 2026 (~19.7 years)**.
2. **Ingest & Mathematically Audit YFinance (Yahoo Finance) Data**:
   Build an optimized, batched YFinance ingestion pipeline, then conduct a rigorous comparative audit against official NSE Bhavcopy data to definitively answer: **Is YFinance data trustable for Indian equity momentum backtesting, or does it introduce fatal survivorship bias, dividend contamination, and price discrepancies?**

---

## 2. Technical Specification & Tasks

### Task 1: Environment & Dependency Setup
- Install `yfinance` in the PRoot Ubuntu system Python environment:
  ```bash
  /usr/bin/pip install yfinance
  ```
- Verify network reachability and test basic quote retrieval for a benchmark ticker (e.g. `^NSEI` or `RELIANCE.NS`).

---

### Task 2: Maximum Bhavcopy Consolidation (2007–2026)
- **Objective**: Consolidate `data/price_cache_export.parquet` (1,831,372 bars across 2007–2026), `data/verification/halt1b_m1/adjusted_bhavcopy_bars_v2.parquet`, and `data/adjusted_bhavcopy_bars_modern.parquet`.
- **Implementation**: Write `deliverables/data_comparison/scripts/consolidate_max_bhavcopy.py`.
- **Requirements**:
  1. Primary Key: Unique `(symbol, date)`.
  2. Columns: `['symbol', 'date', 'open', 'high', 'low', 'close', 'volume']`.
  3. Sort Order: Monotonically sorted by `['symbol', 'date']`.
  4. Consistency: De-duplicate any overlapping date ranges, preserving the most rigorously adjusted bars.
  5. Output: Save to `data/adjusted_bhavcopy_max_2007_2026.parquet`.
  6. Log summary metrics to `deliverables/data_comparison/raw/consolidation_log.txt`.

---

### Task 3: High-Performance Batched YFinance Ingestion Engine
- **Objective**: Download historical daily OHLCV bars for all 1,614 scrips in `data/symbol_map.parquet` from 2007-01-01 to 2026-08-31 without triggering rate limits or crashing on delisted tickers.
- **Implementation**: Write `deliverables/data_comparison/scripts/fetch_yfinance_ohlcv.py`.
- **Requirements**:
  1. **Ticker Mapping**: Append `.NS` to symbols (e.g., `TCS` -> `TCS.NS`, `M&M` -> `M&M.NS`).
  2. **Multi-Threaded Chunking**: Process in batches of 50–100 symbols using `yfinance.download(tickers=batch, group_by='ticker', threads=True, auto_adjust=False)`.
  3. **Capture Both Raw & Adjusted**:
     - Maintain raw `Open`, `High`, `Low`, `Close`, `Volume`.
     - Maintain `Adj Close` and corporate action fields (`Dividends`, `Stock Splits`).
  4. **Error Handling**: Gracefully catch 404 / empty responses for dead or delisted symbols; record them in `data_csv/coverage_comparison.csv`.
  5. **Persistence**: Save consolidated data to `data/yfinance_ohlcv_2007_2026.parquet`.
  6. Log full execution output to `deliverables/data_comparison/raw/yfinance_download_log.txt`.

---

### Task 4: Comparative Fidelity & Trustability Analysis
- **Objective**: Conduct a multi-dimensional mathematical audit comparing Bhavcopy vs YFinance.
- **Implementation**: Write `deliverables/data_comparison/scripts/audit_yfinance_vs_bhavcopy.py`.
- **Evaluation Dimensions**:
  1. **Coverage & Survivorship Bias Audit**:
     - Total point-in-time scrips found in YFinance vs Bhavcopy.
     - Specifically audit known historical/delisted constituents: `PCJEWELLER`, `DHFL`, `RCOM`, `UNITECH`, `RANBAXY`, `SUZLON`, `JPASSOCIAT`.
     - Quantify the survivorship bias footprint of YFinance.
     - Export to `data_csv/coverage_comparison.csv`.
  2. **Price Discrepancy & Tracking Error**:
     - On intersecting `(symbol, date)` pairs, compute:
       * Mean Absolute Percentage Error (MAPE) on `Close` and `Open`:
         $$\text{MAPE} = \frac{1}{N} \sum \frac{|\text{Price}_{\text{YF}} - \text{Price}_{\text{Bhavcopy}}|}{\text{Price}_{\text{Bhavcopy}}} \times 100\%$$
       * Maximum percentage discrepancy and number of bars diverging $> 1.0\%$.
     - Export to `data_csv/price_tracking_error.csv`.
  3. **Corporate Action Adjustment Fidelity**:
     - Test 10 known historical bonus/split dates (e.g. `INFY` 2018-09-04, `TCS` 2018-05-31, `RELIANCE` 2017-09-07, `WIPRO` 2019-03-06).
     - Compare 1-day return across ex-date between Bhavcopy and YFinance raw vs adjusted prices.
     - Verify whether YFinance's `Adj Close` dividend adjustments introduce baseline distortion.
     - Export to `data_csv/corporate_action_fidelity.csv`.
  4. Log full audit analysis to `deliverables/data_comparison/raw/comparative_audit_log.txt`.

---

### Task 5: Comparative Strategy Backtest Re-Run
- **Objective**: Re-run the production momentum strategy (`indian_backtest`) across 2016–2026 under both data sources to evaluate bottom-line divergence.
- **Runs**:
  - **Run A**: Official NSE Bhavcopy dataset (`data/adjusted_bhavcopy_max_2007_2026.parquet`)
  - **Run B**: YFinance dataset (`data/yfinance_ohlcv_2007_2026.parquet`)
- **Comparison Metrics**:
  - Initial Capital: ₹10,000,000.00
  - Final Value, Net Profit, CAGR (%), Max Drawdown (%), Sharpe Ratio
  - Total Closed Trades, Win Rate (%), Profit Factor
  - Divergence ($\Delta$ CAGR, $\Delta$ Max DD, turnover difference)
- Export to `data_csv/comparative_backtest_delta.csv`.

---

### Task 6: Deliverables Compilation & Packaging
- Generate `deliverables/data_comparison/DIGEST.md` summarizing all findings and rendering a definitive verdict on whether YFinance is trustable for production.
- Generate `deliverables/data_comparison/EVIDENCE_INDEX.tsv` and `SHA256SUMS.txt`.
- Package all deliverables into `artifacts/data_comparison_deliverables.zip`.
- Leave Standing Gate **HALT-7 UNTICKED and OPEN** in `task_list.md`.

---

## 3. Deliverables Folder Layout

```
deliverables/data_comparison/
├── DIGEST.md                           # Executive summary and final verdict on YFinance trustability
├── EVIDENCE_INDEX.tsv                  # Manifest of all files with byte counts and SHA-256
├── SHA256SUMS.txt                      # Checksums of all deliverables
├── task_list.md                        # Task roadmap with HALT-7 left open
├── data_csv/
│   ├── coverage_comparison.csv         # Available symbols, missing/delisted tickers in YFinance
│   ├── price_tracking_error.csv        # MAPE and price errors by scrip
│   ├── corporate_action_fidelity.csv   # 1-day returns across known bonus/split dates
│   └── comparative_backtest_delta.csv  # Backtest performance delta (Bhavcopy vs YFinance)
├── raw/
│   ├── consolidation_log.txt           # Consolidation script raw log
│   ├── yfinance_download_log.txt       # Batched downloader raw log
│   └── comparative_audit_log.txt       # Comparative audit raw log
└── scripts/
    ├── consolidate_max_bhavcopy.py     # Script consolidating Bhavcopy to 2007–2026
    ├── fetch_yfinance_ohlcv.py         # Multi-threaded YFinance batch downloader
    ├── audit_yfinance_vs_bhavcopy.py   # Comparative audit and metric generator
    └── generate_evidence_index.py      # Manifest generator
```

---

## 4. Quality Gates & Stop Conditions

1. **Gate 1**: Maximum Bhavcopy dataset must span 2007-01-02 to 2026-08-31 with zero duplicate keys.
2. **Gate 2**: YFinance downloader must utilize batching, rate-limiting, and error-trapping.
3. **Gate 3**: Backtest comparison must utilize the exact same frozen strategy code (`indian_backtest`) under Rule R8 Next-Day Open execution.
4. **Standing Gate HALT-7**: Cease execution and notify the Auditor. Do not self-approve or declare final conclusions without formal Auditor review.

---
*Directive issued by Project MIP Auditor & Governance System.*
