# BUILDER DIRECTIVE: PYDROID 3 100% FEATURE PARITY & GITHUB SYNCHRONIZATION

**Directive ID**: `DIR-PROD-PYDROID3-PARITY-01`  
**Standing Gate**: `HALT-17` (Active — Pause for Auditor Review upon task completion)  
**Target Environment**: Android Standalone Application — Pydroid 3 (Python 3.13 ARM64 Mobile)  
**Workspace**: `/storage/emulated/0/Documents/Project_MIP_Pydroid3`  
**Remote Git Remote**: `git@github.com:Afylx01/Project_MIP_Pydroid3.git` (or GitHub repository under `@Afylx01`)  
**Deliverables Mirror**: `/sdcard/Documents/deliverables/auditor/`  

---

## 1. Executive Objective

Bring `/storage/emulated/0/Documents/Project_MIP_Pydroid3` to **100% feature parity** with the main institutional build (`Project MIP`), ensuring all production, data sync, sector updates, portfolio rebalancing, and alerting capabilities run natively in Pydroid 3 with zero C++ compilation dependencies, and synchronize the standalone project with GitHub.

---

## 2. Parity Requirements & Architecture

### A. Telegram Dispatcher Verification (Confirmed Active)
- `pydroid_core/telegram_sender.py` is already operational.
- Verified sending live alerts, PNG charts (`market_overview_chart.png`), and interactive Plotly HTML tearsheets (`mip_mobile_tearsheet.html`) directly via Telegram Bot API with `curl_cffi` / `requests`.

### B. Automated Dynamic Universe Update (`pydroid_core/auto_fetch.py`)
- Purpose: Eliminate manual data entry in Pydroid 3.
- Process:
  1. Inspects `data/universe.db` and queries `SELECT MAX(date) FROM prices;`.
  2. Compares with target date / today; filters out weekends and holidays using `data/trading_calendar.txt`.
  3. Uses `curl_cffi` (impersonate="chrome") to download daily Bhavcopy from NSE archives (`nsearchives.nseindia.com` or `archives.nseindia.com`).
  4. Hits live NSE Corporate Actions API (`https://www.nseindia.com/api/corporates-corporateActions?index=equities`).
  5. Applies backward adjustments (splits, bonuses, cash dividends) directly via SQL `UPDATE` queries on `universe.db`.
  6. Inserts newly fetched daily bars into `prices`.
  7. Audits invariants: zero nulls, zero duplicates, positive prices.

### C. Official NSE Sector Taxonomy Sync (`pydroid_core/sync_sectors.py`)
- Downloads official Nifty Total Market CSV (`https://www.niftyindices.com/IndexConstituent/ind_niftytotalmarket_list.csv`) using `curl_cffi`.
- Standardizes industry/sector classifications into the 12 primary macro sectors.
- Updates `data/symbol_sector_map.json`.

### D. Portfolio Rebalance & Order Ledger (`pydroid_core/portfolio.py`)
- Takes top momentum candidates from scanner.
- Computes target capital allocation across portfolio slots (e.g. 20 stocks).
- Calculates whole-share order quantities, estimates statutory friction (STT, stamp duty, GST, exchange fees), and writes trade tickets to `reports/rebalance_orders.csv`.

### E. Unified Mobile Terminal Parity (`main_pydroid.py`)
Expand `main_pydroid.py` into a complete 12-item mobile control desk:
- `[1] 🚀 Run Weekly Momentum Scanner (Breadth + RRG + Sector Rotation)`
- `[2] 📱 Preview Telegram Execution Alert`
- `[3] ⚡ Dispatch Live Telegram Alert (Text + Chart + Tearsheet)`
- `[4] 💼 Generate Rebalance Orders & Manage Portfolio Ledger`
- `[5] 📥 Ingest Daily Bhavcopy & Update Master Universe (Auto-Fetch from NSE)`
- `[6] 🔄 Sync Official NSE Sector Taxonomy (Nifty Total Market CSV)`
- `[7] 🎯 Run Interactive Custom Backtester (CLI Date / Top-N Selection)`
- `[8] 📊 Standalone Market Breadth Deep Dive (% > 200 EMA, Net Highs)`
- `[9] 🧭 Standalone JdK Relative Rotation Graph (RRG) Analyzer`
- `[10] 🔄 Standalone Sector Rotation & Relative Alpha Matrix`
- `[11] 📈 View / Regenerate Interactive Plotly Tearsheet & Matplotlib PNG`
- `[12] 🛡️ Run Full Database & Invariant Integrity Audit`
- `[0] 🚪 Exit System`

### F. GitHub Synchronization Protocol
- Initialize git tracking in `/storage/emulated/0/Documents/Project_MIP_Pydroid3`.
- Configure `.gitignore`:
  - Ignore `data/universe.db` (263 MB exceeds GitHub's 100 MB hard limit; document how `universe.db` is built or maintained).
  - Track all source code, tests, documentation, sector taxonomy, configs, and reports.
- Create remote repository on GitHub under `@Afylx01` (e.g. `Afylx01/Project_MIP_Pydroid3` via `gh repo create` or as a branch in `Afylx01/MIP`).
- Commit all files and push cleanly to GitHub.
