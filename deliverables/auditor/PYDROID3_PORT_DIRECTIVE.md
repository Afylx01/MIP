# BUILDER DIRECTIVE: STANDALONE PYDROID 3 QUANTITATIVE WORKSTATION (TDD ARCHITECTURE)

**Directive ID**: `DIR-PROD-PYDROID3-PORT-01`  
**Standing Gate**: `HALT-16` (Active — Pause for Auditor Review & Mobile Verification upon task completion)  
**Target Environment**: Android Standalone Application — Pydroid 3 (Python 3.13 on ARM64)  
**Target Directory**: `/storage/emulated/0/Documents/Project_MIP_Pydroid3` (Shared Mobile Storage)  
**Source Master Workspace**: `/storage/emulated/0/Documents/Project MIP`  
**Deliverables Mirror**: `/sdcard/Documents/deliverables/`  

---

## 1. Executive Objective & Constraints

Build a completely standalone, lightweight, zero-compiler edition of Project MIP in `/storage/emulated/0/Documents/Project_MIP_Pydroid3/` engineered specifically to run natively inside the **Pydroid 3** mobile application on Samsung Galaxy S23 without requiring Termux, PRoot Linux, root access, or C++ build toolchains.

### Verified Pydroid 3 Environment Inventory:
- **Python Runtime**: Python 3.13 (ARM64 `linux_aarch64`)
- **Data & Math**: `pandas 3.0.3`, `numpy 2.4.4`, `sqlite3` (built-in)
- **Web & Anti-Bot**: `curl_cffi 0.16.2` (TLS/JA3/JA4 browser impersonation), `requests 2.34.2`, `beautifulsoup4 4.15.0`
- **Visualization & Export**: `matplotlib 3.10.9`, `plotly 7.0.0`, `openpyxl 3.1.5`, `pillow 12.2.0`
- **Market Data Feeds**: `yfinance 1.7.0`
- **Strictly Unsupported**: `pyarrow` / `fastparquet` (missing ARM64 wheels, compiler requirements)

### Strict Architectural Invariants:
1. **Zero PyArrow / Fastparquet Dependency**:
   - The entire master universe (2,146,531 bars, 1,039 symbols) must be migrated into Python's native standard library **SQLite (`universe.db`)** with dual compound indices:
     - `idx_prices_date ON prices (date)`
     - `idx_prices_sym_date ON prices (symbol, date)`
     - `idx_prices_sym ON prices (symbol)`
2. **Harness Pydroid 3's Native Visual Capabilities**:
   - Leverage `plotly` and `matplotlib` to generate standalone HTML tearsheets and PNG visual charts directly from mobile into `reports/`.
3. **Pure-Python Telegram Communication with TLS Impersonation**:
   - Replace PRoot Linux `/usr/local/bin/telegram-notify` with native HTTP REST calls using `curl_cffi` / `requests` / `urllib`.
4. **Test-Driven Development (TDD) Lifecycle**:
   - Deliver clear, numbered test files (`01_test_environment.py`, `02_test_data_engine.py`, `03_test_scanner.py`, `04_test_visuals.py`) so the user can open them in Pydroid 3, press the Play button, and return the execution logs for immediate auditing.

---

## 2. Directory Layout & File Architecture

Target Path: `/storage/emulated/0/Documents/Project_MIP_Pydroid3/`
```text
Project_MIP_Pydroid3/
├── data/
│   ├── universe.db                # Indexed SQLite 3 database (~228MB, 2.14M bars)
│   ├── symbol_sector_map.json     # Official NSE sector taxonomy (1,039 symbols)
│   └── trading_calendar.txt       # NSE official trading calendar
├── pydroid_core/
│   ├── __init__.py
│   ├── data_engine.py             # SQLite query engine (fast indexed bar loader)
│   ├── breadth.py                 # Market breadth engine (% > 50EMA, % > 200EMA, AD ratio)
│   ├── rrg.py                     # Relative Rotation Graph (RS-Ratio, RS-Momentum)
│   ├── sector_rotation.py         # 12 Primary sectors relative strength & candidate allocator
│   ├── scanner.py                 # Multi-factor weekly momentum scanner
│   ├── backtest.py                # Lightweight vector backtest simulator
│   ├── visuals.py                 # Mobile Matplotlib/Plotly tearsheet generator
│   └── telegram_sender.py         # Pure-Python Telegram alert & deliverable sender
├── tests/
│   ├── 01_test_environment.py     # TDD Step 1: Environment, permissions & package verification
│   ├── 02_test_data_engine.py     # TDD Step 2: SQLite database queries & benchmarks
│   ├── 03_test_scanner.py         # TDD Step 3: End-to-end scanner & alert verification
│   └── 04_test_visuals.py         # TDD Step 4: Matplotlib/Plotly chart export test
├── reports/                       # Mobile-generated charts & tearsheets (.html / .png)
├── .env.example                   # Template for TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID
├── main_pydroid.py                # Unified interactive mobile TUI (1-tap runnable in Pydroid 3)
└── PYDROID_SETUP.md               # Plain-English mobile setup & run guide
```

---

## 3. Detailed Implementation Tasks

### Task 1: Parquet-to-SQLite Bridge (`scripts/export_universe_to_sqlite.py`)
- Execute inside PRoot Ubuntu (where `pyarrow` is available).
- Reads `data/universe/nifty500_pit_universe.parquet` (2,146,531 rows).
- Writes schema to `/storage/emulated/0/Documents/Project_MIP_Pydroid3/data/universe.db`:
  ```sql
  CREATE TABLE prices (
      date TEXT NOT NULL,
      symbol TEXT NOT NULL,
      open REAL,
      high REAL,
      low REAL,
      close REAL,
      volume REAL,
      is_delisted INTEGER DEFAULT 0
  );
  CREATE INDEX idx_prices_date ON prices (date);
  CREATE INDEX idx_prices_sym_date ON prices (symbol, date);
  CREATE INDEX idx_prices_sym ON prices (symbol);
  ```
- Copies `symbol_sector_map.json` and `trading_calendar.txt` into `Project_MIP_Pydroid3/data/`.
- Verifies record count matches exactly 2,146,531 rows.

### Task 2: Pydroid 3 Data Engine (`pydroid_core/data_engine.py`)
- Zero `pyarrow` imports. Uses standard library `sqlite3` + `pandas`.
- Functions:
  - `get_connection() -> sqlite3.Connection`: Connects to `data/universe.db`.
  - `get_latest_date() -> str`: Fast `SELECT MAX(date) FROM prices`.
  - `get_symbols() -> list[str]`: `SELECT DISTINCT symbol FROM prices`.
  - `load_bars(start_date=None, end_date=None, symbols=None) -> pd.DataFrame`: Dynamically queries indexed rows and returns standardized pandas DataFrame.
  - `load_symbol_history(symbol, lookback_bars=250) -> pd.DataFrame`: Sub-millisecond lookup using `idx_prices_sym_date`.

### Task 3: Quantitative Core Adaptations (`pydroid_core/`)
1. **`breadth.py`**:
   - Calculates % stocks above 50 EMA and 200 EMA, Net New 52-Week Highs, Advance/Decline ratio using SQLite bar slices.
2. **`rrg.py`**:
   - Computes JdK RS-Ratio and RS-Momentum against Nifty benchmark or universe equal-weight index.
   - Classifies universe and sectors into Leading, Weakening, Lagging, Improving quadrants.
3. **`sector_rotation.py`**:
   - Uses `symbol_sector_map.json` to aggregate sector performance across the 12 primary NSE sectors.
   - Calculates 1-month and 3-month relative alpha and ranks top sectors.
4. **`scanner.py`**:
   - Combines 12-month momentum, 6-month momentum, RRG quadrant filtering, and sector alignment.
   - Generates top momentum candidates with strict volume and price filters.
5. **`visuals.py`**:
   - Generates high-resolution PNG charts via `matplotlib` and interactive HTML files via `plotly` directly on device.
6. **`telegram_sender.py`**:
   - Dispatches formatted HTML messages and charts/reports directly via Telegram Bot API using `curl_cffi` / `requests`.

### Task 4: Test-Driven Development (TDD) Test Harness (`tests/`)
1. **`01_test_environment.py`**:
   - Checks Python version, architecture (ARM64), storage read/write in Pydroid 3.
   - Validates available packages: `pandas 3.0.3`, `numpy 2.4.4`, `curl_cffi 0.16.2`, `requests`, `matplotlib`, `plotly`, `openpyxl`.
   - Clear PASS/FAIL visual output.
2. **`02_test_data_engine.py`**:
   - Connects to `universe.db`, runs query benchmarks (symbol lookup, date range slice).
   - Validates total rows = 2,146,531, null count = 0, positive prices = 100%.
3. **`03_test_scanner.py`**:
   - Runs Breadth + RRG + Sector Rotation + Momentum Scanner on the latest date in `universe.db`.
   - Prints full ASCII tearsheet and tests dry-run Telegram generation.
4. **`04_test_visuals.py`**:
   - Tests generating a mobile market breadth & RRG chart using Matplotlib/Plotly into `reports/`.

### Task 5: Master Single-Tap Launcher (`main_pydroid.py`)
- Clean, responsive ANSI terminal menu designed for mobile viewing:
  - `[1] 🚀 Run Weekly Momentum Scanner (Full Suite)`
  - `[2] 📱 Preview Telegram Alert (Terminal Preview)`
  - `[3] ⚡ Dispatch Live Telegram Alert`
  - `[4] 📊 Generate Visual Charts & Tearsheets (Plotly/Matplotlib)`
  - `[5] 💼 Run Lightweight Custom Backtester`
  - `[6] 🛡️ Run TDD Diagnostics & Integrity Suite`
  - `[0] 🚪 Exit`

---

## 4. Verification & Audit Gate Rules (HALT-16)

Upon executing the directive:
1. All files must be placed in `/storage/emulated/0/Documents/Project_MIP_Pydroid3/`.
2. The user will open `01_test_environment.py` inside Pydroid 3 and provide the console output.
3. If any package or permission error occurs, the Builder must provide exact mobile remediations.
4. Once verified, notify Telegram using `telegram-notify`.
