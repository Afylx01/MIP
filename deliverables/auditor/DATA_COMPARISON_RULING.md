# DATA COMPARISON AUDITOR RULING: MAXIMUM BHAVCOPY CONSOLIDATION & YFINANCE FIDELITY AUDIT

Status: ACCEPT

## Files inspected

- `deliverables/data_comparison/DIGEST.md` | bytes: 10387 | `9d0549cd800ea1c733e7521dbbfe9b11a6e2e40edeab4b12eb274f732c36667b`
- `deliverables/data_comparison/EVIDENCE_INDEX.tsv` | bytes: 3816 | `9feb6c2fb6e7bb0e88b2b1ffc17d8ce2d33a6324432e0ba8136994be298f7a16`
- `deliverables/data_comparison/task_list.md` | bytes: 3161 | `20c332a9580b40f19d1a7e50c84dc46e1c895f185dc702af0c1a9d0e1db16aa4`
- `deliverables/data_comparison/SHA256SUMS.txt` | bytes: 1619 | `463ff856e4096057c793ff826456fa39f5c225027bb215579f168b5770335804`
- `deliverables/data_comparison/data_csv/coverage_comparison.csv` | bytes: 77904 | `f1efb5045dc76c874960de0b5b83426e0818681f67ce671b3042c1130099d2e0`
- `deliverables/data_comparison/data_csv/price_tracking_error.csv` | bytes: 41380 | `7cb16c2da66aa7327ea325b17d5eda3cab1824130e487b52d0f59cbfb28f4aef`
- `deliverables/data_comparison/data_csv/corporate_action_fidelity.csv` | bytes: 851 | `cde7a154618844cedf387975891f5d3a8380929ebbe1f701a9d91bba72fefca5`
- `deliverables/data_comparison/data_csv/comparative_backtest_delta.csv` | bytes: 1041 | `0a9467ec10bf5ce12aaaec21b72cdf61a26ca6299d297aeecb32aee36fc86870`
- `deliverables/data_comparison/raw/consolidation_log.txt` | bytes: 1682 | `a6b1e4838ea4267aa217c476d1a6cf05b15413d808c3d63eb65b2b95b4228dcc`
- `deliverables/data_comparison/raw/yfinance_download_log.txt` | bytes: 4851 | `ccfeadffbb4ea7346af2ea79ff2f1a08610535e9716b234eb105c7f962bfd61d`
- `deliverables/data_comparison/raw/comparative_audit_log.txt` | bytes: 3413 | `2b2c73a910d002bee1dd079de4c3d2b9480aa85e6ec7a351276eed5fd1458fde`
- `deliverables/data_comparison/raw/comparative_backtest_log.txt` | bytes: 11285 | `88c4afb380f69d08d6dfff60e70d2d0b967b8a7c01e2c1b41c5a830fee8705e5`
- `deliverables/data_comparison/scripts/consolidate_max_bhavcopy.py` | bytes: 6251 | `b5a8e046926201223181f7ab80bc3f2880e296db60680a4a3037cfe1fcb963ed`
- `deliverables/data_comparison/scripts/fetch_yfinance_ohlcv.py` | bytes: 12815 | `6da40b008eed4529ae5ee1030ee59c7f445967f30f027811c34a164ff9020950`
- `deliverables/data_comparison/scripts/audit_yfinance_vs_bhavcopy.py` | bytes: 10604 | `95b3681b7702ea8259fe5317c4996eee47a3985a81670ad1b93c82d3722a56ba`
- `deliverables/data_comparison/scripts/run_comparative_backtest.py` | bytes: 13412 | `3cb8fe1994953e20acbaa77ad4e04d57fad700bec4fa93ba402f75f658502c2e`
- `data/adjusted_bhavcopy_max_2007_2026.parquet` | bytes: 68061592 | `d83ad78e162661fdd8ca54247c125783104d6912eaab34530ba641802b7b21e7`
- `data/yfinance_ohlcv_2007_2026.parquet` | bytes: 105248348 | `9ed8525ce416654563250575d5c16f3ebc953153ee731234cfc52d672804e54b`

---

## Claims verified

### Claim 1: Maximum Bhavcopy Consolidation (2007–2026)
- **Consolidated Dataset**: `data/adjusted_bhavcopy_max_2007_2026.parquet`
- **Total Price Bars**: **2,137,630 bars** across **1,039 unique symbols**.
- **Date Range**: `2007-01-02` to `2026-08-31` (19.7 years, 4,857 trading days).
- **Quality Invariants**: Exactly **0 duplicate `(symbol, date)` keys**. Monotonically sorted. Fully corporate-action adjusted.
- **Status**: **STRICT PASS**.

### Claim 2: High-Performance Batched YFinance Ingestion
- **Dataset Generated**: `data/yfinance_ohlcv_2007_2026.parquet` (3,821,604 bars across 1,093 symbols).
- Executed via chunked multi-threading with `auto_adjust=False` to isolate raw OHLC vs dividend-adjusted series.

### Claim 3: Survivorship Bias in Yahoo Finance
- **Auditor Recomputation**: Out of 1,149 universe symbols audited, exactly **56 past NIFTY 500 constituents (4.87%)** are completely missing / purged from Yahoo Finance (HTTP 404 / 0 bars).
- Verified dead/delisted canary scrips missing from YFinance: `DHFL`, `RANBAXY`, `JPASSOCIAT`, `AMTEKINDIA`, `CADILAHC`, `BHARATFIN`.
- **Verdict**: **Yahoo Finance suffers from severe, fatal survivorship bias**.

### Claim 4: Price Discrepancy & Corporate Action Fidelity
- **Corporate Action Fidelity**: Verified 10 known splits/bonuses (INFY, TCS, RELIANCE, WIPRO, HDFCBANK, EICHERMOT, IRCTC, TATASTEEL, ITC, BAJFINANCE). All 10 exhibit **0.00% difference** on split ratio adjustment for surviving blue chips.
- **Overall Price Tracking Error**: Across 2,087,843 overlapping bars, Close price Mean Absolute Percentage Error (MAPE) is **6.77% - 9.11%**, with **50.23% of bars diverging by > 1.0%** due to dividend yield adjustments, rights issues, and demerger handling.

### Claim 5: Backtest Outcome Divergence (Bhavcopy vs YFinance)
- Replayed identical production momentum strategy across 2016–2026:
  - **Run A (Ground Truth Bhavcopy)**: ₹1.00 Cr $\to$ ₹8.14 Cr | **21.75% CAGR** | **48.72% Max Drawdown** | Residual: `0.00`
  - **Run B (Yahoo Finance)**: ₹1.00 Cr $\to$ ₹13.06 Cr | **27.27% CAGR** | **38.79% Max Drawdown** | Residual: `0.00`
- **Divergence**:
  - YFinance artificially inflates CAGR by **+5.52 percentage points** (and phantom profit of **+₹4.92 Crore / +60.4%**).
  - YFinance suppresses Max Drawdown by **-9.93 percentage points** because bankrupt stocks like `DHFL` cannot be bought.
- **Accounting Invariant (Rule R-3)**: Strictly satisfied across both runs (residual $0.00$).

### Claim 6: Standing Gate HALT-7 Discipline
- Standing gate HALT-7 was properly held unticked and open awaiting Auditor review.

---

## Claims rejected

None. All claims made in `deliverables/data_comparison/DIGEST.md` are supported by verifiable on-disk evidence and confirmed via independent recomputation in PRoot Ubuntu `/usr/bin/python3`.

---

## Final Auditor Verdict on Yahoo Finance

> [!CAUTION]
> **RULING: YAHOO FINANCE (`yfinance`) IS REJECTED FOR HISTORICAL STRATEGY VALIDATION.**  
> Yahoo Finance purges delisted equities and contaminates technical indicators with dividend yield adjustments. It overstates momentum CAGR by +5.52 pp and severely hides downside drawdowns (-9.93 pp). Official NSE Bhavcopies remain the only permissible ground-truth price source for Project MIP.

---

## Gate Status & Next Directive

- **Standing Gate HALT-7**: **CLEARED and CLOSED**.
- **Deliverables Status**: **ACCEPT**.
- **Consolidated Master Bhavcopy**: [`data/adjusted_bhavcopy_max_2007_2026.parquet`](file:///storage/emulated/0/Documents/Project%20MIP/data/adjusted_bhavcopy_max_2007_2026.parquet) is now the certified master execution dataset for Project MIP.
