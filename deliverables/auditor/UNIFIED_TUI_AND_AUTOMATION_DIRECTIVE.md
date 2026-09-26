# BUILDER DIRECTIVE: UNIFIED QUANTITATIVE WORKSTATION, INTERACTIVE BACKTESTER, NSE SECTOR SYNC & RUNBOOK

**Directive ID**: `DIR-PROD-UNIFIED-TUI-02`  
**Standing Gate**: `HALT-13` (Active — Pause for Auditor Review upon task completion)  
**Target Environment**: PRoot Ubuntu ARM64 (`/usr/bin/python3`)  
**Workspace**: `/storage/emulated/0/Documents/Project MIP`  
**Deliverables Mirror**: `/sdcard/Documents/deliverables/`  

---

## 1. Executive Objective

The user correctly identified that Project MIP has built an entire institutional quantitative research ecosystem (RRG, Sector Rotation, Market Breadth, Scanner, Custom Backtester, 32-Gate Test Plan, Monte Carlo, Cost Stress Tests), but these capabilities are currently scattered across individual CLI scripts.

The mandate is to build a **Unified Institutional Quantitative Workstation (`run_mip.py`)** that unifies ALL research, backtesting, analytics, and live execution functions into an intuitive, colorized interactive terminal dashboard, complete with an **Interactive Custom Backtester** and an exhaustive **Beginner's Operations Runbook (`HOW_TO_RUN.md`)**.

---

## 2. Workstation Architecture & Menu Layout (`run_mip.py`)

The main entry point `/storage/emulated/0/Documents/Project MIP/run_mip.py` must feature an ANSI-colorized, clean terminal dashboard divided into 4 clear sections:

```
========================================================================================
🏛️  PROJECT MIP — INSTITUTIONAL QUANTITATIVE RESEARCH & TRADING DESK
Samsung Galaxy S23 (PRoot Ubuntu ARM64) | Engine: /usr/bin/python3
========================================================================================

📡 LIVE PRODUCTION & EXECUTION
  [1] 🚀 Run Weekly Momentum Scanner (Full Suite: Breadth + RRG + Sector Rotation)
  [2] 📱 Preview Telegram Execution Alert (Dry-Run ASCII/HTML Preview)
  [3] ⚡ Dispatch Live Telegram Alert (Broadcast Signal to Channel)
  [4] 💼 Generate Rebalance Orders & Manage Portfolio Ledger (Whole Shares & Fees)
  [5] 📥 Ingest Daily Bhavcopy & Update Master Universe Database

🔬 STRATEGY BACKTESTING LAB (RUN AS DESIRED)
  [6] 🧪 Run Interactive Custom Backtest (Custom Dates, Top-N, Volar/Return, Exit Buffer)
  [7] 🏆 Run Full 20-Year Baseline Backtest (2007–2026 Official Replay)
  [8] 🎲 Run 1,000-Iteration Monte Carlo Luck/Skill Test (p-value analysis)
  [9] 💸 Run Institutional Cost & Slippage Stress Test (1x, 2x, 3x Friction Ladder)
  [10] 🔄 Run Rolling Walk-Forward & Out-of-Sample Analysis (IS 2007-15 vs OOS 2016-26)
  [11] 🌪️ Run Macro Regime Historical Stress Test (2008 GFC, 2020 COVID, etc.)

🧭 ANALYTICS & DEEP DIVE TOOLS
  [12] 🌐 Standalone Market Breadth Deep Dive (% > 200 EMA, Net Highs, Regimes)
  [13] 🌀 Standalone JdK Relative Rotation Graph (RRG) Quadrant Analyzer
  [14] 🏭 Standalone Sector Rotation & Relative Strength Matrix
  [15] 🔄 Sync Official NSE Sector Taxonomy (Nifty Total Market CSV)

📊 REPORTS & SYSTEM AUDIT
  [16] 📊 View / Regenerate Institutional Interactive HTML Tearsheet (Plotly)
  [17] 🛡️ Run Master 32-Gate Automated Verification Audit (is_proven engine)
  [18] 🔍 Audit & Verify Universe Database Invariants (0 Nulls, 0 Duplicates)

  [0] 🚪 Exit System
========================================================================================
Select an option [0-18]: 
```

---

## 3. Implementation Tasks

### Task 1: Interactive Custom Strategy Backtester (`production/run_custom_backtest.py`)
- Provide a dedicated interactive script called by Option `[6]`:
  - Interactively prompts with sensible defaults (pressing `ENTER` accepts default):
    1. `Start Date [Default: 2016-01-01]: `
    2. `End Date [Default: 2026-08-31]: `
    3. `Portfolio Size (Top N) [Default: 20]: `
    4. `Ranking Metric [1: Volar Score (Default), 2: Raw 252d Return]: `
    5. `Exit Buffer Rank [Default: 40]: `
    6. `Market Regime Filter (Pause new entries if Nifty 500 < 20 EMA) [Y/n, Default: Y]: `
    7. `Friction Tier [1: 1x Real Institutional Costs (Default), 2: 2x Stress, 3: 3x Extreme]: `
    8. `Initial Capital in INR [Default: 10000000 (₹1 Crore)]: `
  - Executes the backtest using `indian_backtest` package against `data/universe/nifty500_pit_universe.parquet`.
  - Displays instant terminal performance tearsheet:
    - Strategy CAGR vs Benchmark CAGR, Excess Alpha
    - Sharpe Ratio, Sortino Ratio, Calmar Ratio
    - Maximum Drawdown (%) & Recovery Time
    - Total Trades, Win Rate (%), Profit Factor
    - Final Portfolio Value & Total Friction Paid
  - Exports trade logs and equity series to `reports/custom_backtest_results.csv`.

### Task 2: Official NSE Sector Classification Syncer (`production/sync_nse_sectors.py`)
- Option `[15]` downloads `https://www.niftyindices.com/IndexConstituent/ind_niftytotalmarket_list.csv`.
- Maps official 22 NSE industries to the 12 primary sectors:
  - `Automobile and Auto Components` -> `AUTO`
  - `Financial Services` -> `FINSERV`
  - `Capital Goods` -> `CAPGOODS`
  - `Chemicals` -> `CHEMICALS`
  - `Construction`, `Construction Materials`, `Realty` -> `REALTY`
  - `Consumer Durables`, `Consumer Services`, `Textiles` -> `CONSDUR`
  - `Fast Moving Consumer Goods` -> `FMCG`
  - `Healthcare` -> `PHARMA`
  - `Information Technology` -> `IT`
  - `Metals & Mining` -> `METALS`
  - `Oil Gas & Consumable Fuels`, `Power` -> `ENERGY`
  - `Telecommunication`, `Media Entertainment & Publication`, `Utilities`, `Services`, `Forest Materials`, `Diversified` -> `INFRA_MEDIA`
- Merges with the historical delisted graveyard lookup table (`survivorship_graveyard.csv`) so 100% of the 1,039 universe scrips remain mapped.
- Exports to `data/universe/symbol_sector_map.json`.

### Task 3: Unified Interactive Terminal Dashboard (`run_mip.py`)
- Located at project root: `/storage/emulated/0/Documents/Project MIP/run_mip.py`.
- Made executable (`chmod +x run_mip.py`).
- Maps every numbered option to its respective script:
  - `[1]`: `production/scanner.py`
  - `[2]`: `production/telegram_alerts.py --dry-run`
  - `[3]`: `production/telegram_alerts.py` (live dispatch)
  - `[4]`: `deliverables/phase_8/scripts/run_production_pipeline.py` (or order generator)
  - `[5]`: `scripts/update_universe.py`
  - `[6]`: `production/run_custom_backtest.py` (interactive)
  - `[7]`: `deliverables/phase_7/scripts/init_phase7_engine.py` (20-year replay)
  - `[8]`: `deliverables/phase_7/scripts/test_random_monte_carlo.py`
  - `[9]`: `deliverables/phase_7/scripts/test_cost_sensitivity.py`
  - `[10]`: `deliverables/phase_7/scripts/test_walk_forward.py`
  - `[11]`: `deliverables/phase_7/scripts/test_macro_regimes.py`
  - `[12]`: `production/breadth.py` (standalone breadth tearsheet)
  - `[13]`: `production/plugins/rrg_filter.py` (standalone RRG quadrant display)
  - `[14]`: `production/sector_rotation.py` (standalone sector ranking)
  - `[15]`: `production/sync_nse_sectors.py`
  - `[16]`: `scripts/build_institutional_tearsheet.py`
  - `[17]`: `deliverables/phase_7/scripts/run_master_proven_gate.py` (32 Gates)
  - `[18]`: `scripts/update_universe.py --verify-only`
- Clears terminal neatly before each action, streams real-time stdout, and pauses with `Press ENTER to return to menu...`.
- Traps `KeyboardInterrupt` and errors cleanly so the operator is never thrown out of the menu unexpectedly.

### Task 4: Comprehensive Operator Runbook (`HOW_TO_RUN.md`)
- File: `/storage/emulated/0/Documents/Project MIP/HOW_TO_RUN.md` (mirrored to `/sdcard/Documents/deliverables/HOW_TO_RUN.md`).
- Exhaustive step-by-step instructions for a non-technical operator:
  1. **How to Launch the Dashboard**: Exact one-line command (`python3 run_mip.py`).
  2. **Everyday Operator Playbook**:
     - Friday 4:00 PM routine (Options 1, 2, 3).
     - Monday 9:15 AM execution routine (Option 4).
     - Monthly or periodic universe maintenance (Options 5, 15).
  3. **How to Run Custom Backtests**:
     - Step-by-step walkthrough of Option `[6]`.
     - How to test different holding sizes (Top 10 vs Top 30).
     - How to test Bear market periods only (e.g. 2008 or 2020).
  4. **Plain English Explanations**:
     - Volar Score vs Raw Momentum.
     - 200 EMA Rule and 20 EMA Market Filter.
     - Market Breadth Health (% > 200 EMA).
     - RRG Quadrant meanings (Leading, Improving, Weakening, Lagging).
     - 100% Exit Buffer (Rank 40 buffer).
     - Transaction cost schedule (STT, GST, Stamp Duty, Slippage).
  5. **Directory & File Guide**: What each folder and data file does.

### Task 5: End-to-End Verification
- Launch and test `run_mip.py` with mock inputs / automated smoke test.
- Run `production/run_custom_backtest.py` with test dates to confirm clean execution.
- Pause at Standing Gate `HALT-13` for Auditor review.

---

## 4. Standing Gate HALT-13

Upon completing Tasks 1 through 5:
1. Halt execution and wait for Auditor review.
2. Commit changes cleanly with message `feat(workstation): implement unified quantitative terminal dashboard, interactive backtester, NSE sector syncer, and operator runbook`.
3. Report completion for Auditor inspection and certification.
