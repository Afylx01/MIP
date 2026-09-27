# BUILDER DIRECTIVE: AUTOMATED DYNAMIC MARKET DATA FETCHER & CORPORATE ACTION ADJUSTER

**Directive ID**: `DIR-PROD-LIVE-DATA-SYNC-01`  
**Standing Gate**: `HALT-15` (Active — Pause for Auditor Review upon task completion)  
**Target Environment**: Dual: Samsung Galaxy S23 (PRoot Ubuntu ARM64) AND Windows 10/11  
**Workspace**: `/storage/emulated/0/Documents/Project MIP`  
**Deliverables Mirror**: `/sdcard/Documents/deliverables/`  

---

## 1. Executive Objective

Build a fully automated, dynamic market data synchronization engine that eliminates manual Bhavcopy downloading and manual corporate action tracking.

Whenever executed, the engine must:
1. **Detect Date Gaps**: Inspect `data/universe/nifty500_pit_universe.parquet`, find the latest date `max_date`, and identify all missing trading sessions up to today / latest market close.
2. **Download Daily Bhavcopies**: Automatically fetch official daily equity Bhavcopies directly from NSE archives (`nsearchives.nseindia.com` or `archives.nseindia.com`) for all missing dates.
3. **Fetch & Apply Corporate Actions**: Automatically fetch live corporate actions from NSE (`https://www.nseindia.com/api/corporates-corporateActions?index=equities`), extract splits, bonus issues, and cash dividends, and backward-adjust historical price series using the verified `adjust_prices.py` engine.
4. **Append & Validate Invariants**: Cleanly map symbols, enforce the 4 master invariants (zero nulls, zero duplicate keys, monotonic sorting, positive prices), perform an atomic write to `nifty500_pit_universe.parquet`, and update `universe_metadata.json` with the new SHA-256 fingerprint.
5. **Integrate into TUI**: Wire this automated synchronization into `run_mip.py` under Option `[5]` and provide a `--sync-market-data` flag for `scanner.py`.

---

## 2. Technical & Mathematical Architecture

### A. Dynamic Gap Identification (`production/auto_fetch_market_data.py`)
- Read `max_date` from `data/universe/nifty500_pit_universe.parquet`.
- Determine target date range: from `max_date + 1 day` to `today` (or target date).
- Filter candidate dates: exclude Saturdays, Sundays, and official NSE holidays (from `data/trading_calendar.txt`).
- If no missing trading days exist, log `"Universe is already up to date as of {max_date}."` and exit cleanly.

### B. NSE Daily Bhavcopy Fetcher
For each missing trading date `YYYY-MM-DD`:
- Try downloading from official NSE endpoints (with standard browser headers and session cookies):
  1. **Modern NSE PR Bhavcopy (2024–Present)**:
     `https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_{YYYYMMDD}_F_0000.csv.zip`
  2. **Classic NSE Bhavcopy Archive**:
     `https://archives.nseindia.com/content/historical/EQUITIES/{YYYY}/{MMM}/cm{DD}{MMM}{YYYY}bhav.csv.zip`
  3. **Live Same-Day Bhavcopy**:
     `https://archives.nseindia.com/products/content/sec_bhavdata_full.csv`
- Extract CSV in memory, filter `SERIES == 'EQ'`, standardize column names (`date`, `symbol`, `open`, `high`, `low`, `close`, `volume`).

### C. Live Corporate Action Parser & Backward Adjuster
- Hit official NSE Corporate Actions API:
  `https://www.nseindia.com/api/corporates-corporateActions?index=equities`
- Filter records where `exDate` falls between `max_date` and target date.
- Parse `subject`:
  - **Stock Split**:
    - Pattern matching (e.g. `Split.*Rs\s*(\d+).*to.*Rs\s*(\d+)` or `Face Value Split From Rs (\d+) To Rs (\d+)` or `Split Ratio (\d+):(\d+)`).
    - Factor $f = \text{new\_fv} / \text{old\_fv} = 1.0 / \text{ratio}$.
    - Historical bars prior to `ex_date`: $P_{\text{adj}} = P \times f$, $\text{Vol}_{\text{adj}} = \text{Vol} / f$.
  - **Bonus Issue**:
    - Pattern matching (e.g. `Bonus\s*(\d+):(\d+)`).
    - Factor $f = 1.0 / (1.0 + A/B)$.
    - Historical bars prior to `ex_date`: $P_{\text{adj}} = P \times f$, $\text{Vol}_{\text{adj}} = \text{Vol} / f$.
  - **Cash Dividend**:
    - Pattern matching (e.g. `Dividend.*Rs\s*([\d\.]+)`).
    - Cash dividend $D$ in INR per share.
    - Factor $f = 1.0 - (D / P_{\text{close, ex}-1})$.
    - Historical bars prior to `ex_date`: $P_{\text{adj}} = P \times f$ (volume unchanged).

### D. Invariant Enforcement & Atomic Ingestion
1. Apply backward adjustments to existing universe bars for affected symbols.
2. Concatenate newly fetched and adjusted daily bars.
3. Assert:
   - `df.isnull().sum().sum() == 0`
   - `df.duplicated(subset=['date', 'symbol']).sum() == 0`
   - Chronological sorting per symbol.
   - All prices $> 0$.
4. Atomic write: write to `temp_universe.parquet`, verify, replace `nifty500_pit_universe.parquet`.
5. Recompute SHA-256 and update `universe_metadata.json`.

---

## 3. Implementation Tasks

### Task 1: Build Automated Market Data Fetcher (`production/auto_fetch_market_data.py`)
- Implements `MarketDataSyncEngine`:
  - `get_missing_trading_dates(max_date, target_date)`
  - `fetch_bhavcopy_for_date(date_str) -> pd.DataFrame`
  - `fetch_live_corporate_actions() -> pd.DataFrame`
  - `apply_corporate_actions_backward(universe_df, ca_df) -> pd.DataFrame`
  - `sync_universe_to_date(target_date) -> dict`
- Provides CLI:
  `python3 production/auto_fetch_market_data.py [--target-date YYYY-MM-DD] [--dry-run]`

### Task 2: Integrate into `scripts/update_universe.py`
- Add `--auto-fetch` flag to `scripts/update_universe.py`:
  - When `--auto-fetch` is passed without `--new-bhavcopy`, invokes `MarketDataSyncEngine` to automatically fetch all missing dates from NSE.

### Task 3: Integrate into Workstation Menu (`run_mip.py`)
- Update Option `[5]`:
  `[5] 📥 Ingest Daily Bhavcopy & Update Master Universe (Auto-Fetch from NSE)`
  - Prompts: `[1] Auto-fetch latest from NSE (Default) | [2] Ingest local Bhavcopy file`.
  - Pressing `ENTER` automatically runs the dynamic sync.

### Task 4: End-to-End Verification & Dry-Run Test
- Run `python3 production/auto_fetch_market_data.py --dry-run` to test connectivity, CA parsing, and date detection.
- Verify zero syntax errors, cross-platform path compatibility, and proper error handling.

---

## 4. Standing Gate HALT-15

Upon completing Tasks 1 through 4:
1. Halt execution and wait for Auditor review.
2. Commit changes cleanly with message `feat(data): implement dynamic market data fetcher and corporate action auto-adjuster`.
3. Report completion for Auditor inspection and certification.
