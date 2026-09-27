# DIGEST: HALT-17 — Pydroid 3 Feature Parity & GitHub Launch
## Directive: DIR-PROD-PYDROID3-PARITY-01
## Standing Gate: HALT-17
## Completed: 2026-09-27

---

## Executive Summary

Brought `/storage/emulated/0/Documents/Project_MIP_Pydroid3` to **100% feature parity** with the main PRoot build. Implemented SQLite-based dynamic NSE market data auto-fetching with corporate action adjustments, official sector taxonomy sync, portfolio order generation with statutory frictions, expanded `main_pydroid.py` to a 12-item mobile trading desk, and pushed to GitHub as `Afylx01/Project_MIP_Pydroid3`.

---

## Step Completion Matrix

| Step | Description | Status | Deliverable |
|------|------------|--------|-------------|
| 1 | Automated Dynamic Universe Update | ✅ PASS | `pydroid_core/auto_fetch.py` (306 lines) |
| 2 | Official NSE Sector Taxonomy Sync | ✅ PASS | `pydroid_core/sync_sectors.py` (317 lines) |
| 3 | Portfolio Rebalancing & Order Ledger | ✅ PASS | `pydroid_core/portfolio.py` (197 lines) |
| 4 | Expand to 12-item Mobile Trading Desk | ✅ PASS | `main_pydroid.py` (v2.0.0, 12 options) |
| 5 | Git Setup & Remote Push to GitHub | ✅ PASS | `Afylx01/Project_MIP_Pydroid3` on `main` |

---

## Step 1: Automated Dynamic Universe Update (`pydroid_core/auto_fetch.py`)

**Class**: `PydroidAutoFetch`

Key methods:
- `get_missing_trading_dates()` — Queries `SELECT MAX(date) FROM prices`, cross-references `data/trading_calendar.txt`
- `fetch_bhavcopy_for_date(date_str)` — Downloads from NSE archives via `curl_cffi` (impersonate="chrome"), handles both Modern PR and Classic Bhavcopy formats
- `_standardize_bhavcopy(raw, fallback_date)` — Normalizes column names, filters `SERIES == 'EQ'`, drops nulls/non-positive
- `fetch_corporate_actions(start_date, end_date)` — Fetches from `nseindia.com/api/corporates-corporateActions`
- `parse_corporate_actions()` — Regex parsing for splits (face value / ratio), bonuses, cash dividends
- `apply_backward_adjustments(conn, actions)` — Parameterized SQL `UPDATE prices SET open=open*?, ...` for historical backward adjustment
- `sync_universe(target_date, dry_run)` — End-to-end sync with validation
- `validate_database(conn)` — Zero nulls, zero duplicates, positive prices invariant check

**Anti-bot**: Uses `curl_cffi.requests.Session(impersonate="chrome")` with fallback to `requests.Session()`

---

## Step 2: Official NSE Sector Taxonomy Sync (`pydroid_core/sync_sectors.py`)

**Function**: `sync_nse_sectors(base_dir)`

- Downloads `https://www.niftyindices.com/IndexConstituent/ind_niftytotalmarket_list.csv`
- Maps 22 official NSE industries → 12 primary sectors via `INDUSTRY_TO_SECTOR` dict
- 300+ `EXPLICIT_OVERRIDES` covering all major NIFTY 500 constituents
- NLP `classify_symbol()` fallback with keyword-based classification
- Queries universe.db for complete symbol list, ensures 100% coverage
- Exports to `data/symbol_sector_map.json` (flat dict, sorted keys)

**12 Primary Sectors**: AUTO, FINSERV, CAPGOODS, CHEMICALS, REALTY, CONSDUR, FMCG, PHARMA, IT, METALS, ENERGY, INFRA_MEDIA

---

## Step 3: Portfolio Rebalancing & Order Ledger (`pydroid_core/portfolio.py`)

**Class**: `PortfolioManager`

**Statutory Frictions (Indian Market)**:
| Component | Rate |
|-----------|------|
| STT (Securities Transaction Tax) | 0.1% |
| Exchange Turnover | 0.00345% |
| Brokerage (Discount Broker) | 0.03% |
| GST on (Brokerage + Exchange) | 18% |
| Stamp Duty | 0.015% |

- `generate_rebalance_orders(capital, top_n, current_holdings)` — Equal-weight allocation, whole-share sizing via `math.floor()`, BUY/HOLD/SELL action classification
- `export_orders(orders_df)` — CSV + human-readable TXT export to `reports/rebalance_orders.csv`

**Verified**: 20 BUY orders generated for ₹10,00,000 capital with correct friction computation.

---

## Step 4: 12-Item Mobile Trading Desk (`main_pydroid.py` v2.0.0)

| Option | Description | Category |
|--------|-------------|----------|
| [1] | 🚀 Run Weekly Momentum Scanner (Full Suite) | Scanner |
| [2] | 📱 Preview Telegram Alert | Telegram |
| [3] | ⚡ Dispatch Live Telegram Alert | Telegram |
| [4] | 📊 Generate Visual Charts & Tearsheets | Portfolio |
| [5] | 💼 Run Lightweight Custom Backtester | Portfolio |
| [6] | 🛡️ Run TDD Diagnostics & Integrity Suite | Maintenance |
| [7] | 💰 Portfolio Rebalancing & Order Generation | Portfolio |
| [8] | 📡 Auto-Fetch Market Data (NSE Bhavcopy Sync) | Data |
| [9] | 🏭 Sync NSE Sector Taxonomy | Data |
| [10] | 📈 Standalone Market Breadth Report | Scanner |
| [11] | 🔄 Standalone Sector Rotation & RRG Analysis | Scanner |
| [12] | 🔍 Full Database Integrity Audit | Maintenance |

CLI support: `python main_pydroid.py --option N` for headless execution (1-12).

---

## Step 5: Git Setup & GitHub Push

- **Repository**: [`Afylx01/Project_MIP_Pydroid3`](https://github.com/Afylx01/Project_MIP_Pydroid3)
- **Branch**: `main`
- **Commit**: `257f919`
- **Files Tracked**: 23 files, 14,754 insertions
- **`.gitignore`**: Excludes `data/universe.db` (263 MB), `__pycache__/`, `.env`, `reports/*`
- **Visibility**: Public

---

## Module Inventory (17 Python files)

| Module | Lines | Purpose |
|--------|-------|---------|
| `pydroid_core/__init__.py` | 7 | Package init, v2.0.0-pydroid3 |
| `pydroid_core/data_engine.py` | 258 | SQLite data access engine |
| `pydroid_core/scanner.py` | 259 | 5-tier momentum screener |
| `pydroid_core/rrg.py` | ~120 | JdK Relative Rotation Graph |
| `pydroid_core/breadth.py` | ~180 | Market breadth engine |
| `pydroid_core/sector_rotation.py` | ~200 | Sector rotation engine |
| `pydroid_core/backtest.py` | ~250 | Lightweight vector backtester |
| `pydroid_core/visuals.py` | ~300 | Matplotlib + Plotly generators |
| `pydroid_core/telegram_sender.py` | ~200 | Pure-Python Telegram dispatcher |
| `pydroid_core/auto_fetch.py` | 306 | **NEW** NSE Bhavcopy auto-sync |
| `pydroid_core/sync_sectors.py` | 317 | **NEW** NSE sector taxonomy sync |
| `pydroid_core/portfolio.py` | 197 | **NEW** Portfolio order generator |
| `main_pydroid.py` | ~480 | **EXPANDED** 12-option TUI launcher |
| `tests/01_test_environment.py` | ~60 | Runtime & package audit |
| `tests/02_test_data_engine.py` | ~80 | Database invariant audit |
| `tests/03_test_scanner.py` | ~70 | Screener pipeline audit |
| `tests/04_test_visuals.py` | ~80 | Visual & backtest audit |

---

## SHA-256 Cryptographic Attestation

See `SHA256SUMS_HALT17.txt` for complete checksums.

---

## Verification Results

| Check | Result |
|-------|--------|
| All 10 `pydroid_core` modules import | ✅ PASS |
| `main_pydroid.py --help` shows 12 options | ✅ PASS |
| Portfolio order generation (₹10L / Top 20) | ✅ PASS (21 rows, 20 BUY + SUMMARY) |
| Database: 2,146,531 rows, 1,039 symbols | ✅ PASS |
| Date range: 2007-01-02 to 2026-09-11 | ✅ PASS |
| GitHub push to `Afylx01/Project_MIP_Pydroid3` | ✅ PASS |
| `.gitignore` excludes universe.db | ✅ PASS |

---

> **Standing Gate HALT-17 is now ACTIVE and PAUSED for Auditor review.**
> The Auditor should verify mobile execution in Pydroid 3 for Options [7], [8], [9], [10], [11], [12] and confirm the GitHub repository is accessible.
