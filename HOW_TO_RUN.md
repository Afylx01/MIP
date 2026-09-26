# 🏛️ PROJECT MIP — INSTITUTIONAL OPERATOR RUNBOOK
## Plain-English Guide to the Quantitative Momentum Workstation, Backtesting Lab & Live Execution Desk

**Platform**: Dual-Platform — Samsung Galaxy S23 (PRoot Ubuntu Linux ARM64) AND Windows 10/11 (x86_64 / ARM64)  
**Workspace**: `/storage/emulated/0/Documents/Project MIP` (Linux) or root repo directory (Windows)  
**Shared Deliverables**: `/sdcard/Documents/deliverables/` (mirrored locally to `deliverables/`)  
**Master Dashboard**: `python3 run_mip.py` (Linux) or `run_mip.bat` (Windows)  

---

## 1. Quick Start: The One-Line Command

To launch the full quantitative trading desk and interactive workstation, open your terminal and run:

**On Linux / Termux PRoot Ubuntu**:
```bash
cd "/storage/emulated/0/Documents/Project MIP"
python3 run_mip.py
```

**On Windows (CMD or PowerShell)**:
```cmd
run_mip.bat
```

This opens the interactive **18-Option Quantitative Terminal Menu**:

```
========================================================================================
🏛️   PROJECT MIP — INSTITUTIONAL QUANTITATIVE RESEARCH & TRADING DESK
Samsung Galaxy S23 (PRoot Ubuntu ARM64) | System Engine: /usr/bin/python3
========================================================================================

📡 LIVE PRODUCTION & EXECUTION
  [1]  🚀 Run Weekly Momentum Scanner (Full Suite: Breadth + RRG + Sector Rotation)
  [2]  📱 Preview Telegram Execution Alert (Dry-Run ASCII/HTML Preview)
  [3]  ⚡ Dispatch Live Telegram Alert (Broadcast Signal to Channel)
  [4]  💼 Generate Rebalance Orders & Manage Portfolio Ledger (Whole Shares & Fees)
  [5]  📥 Ingest Daily Bhavcopy & Update Master Universe Database

🔬 STRATEGY BACKTESTING LAB (RUN AS DESIRED)
  [6]  🧪 Run Interactive Custom Backtest (Custom Dates, Top-N, Volar/Return, Exit Buffer)
  [7]  🏆 Run Full 20-Year Baseline Backtest (2007–2026 Official Replay)
  [8]  🎲 Run 1,000-Iteration Monte Carlo Luck/Skill Test (p-value analysis)
  [9]  💸 Run Institutional Cost & Slippage Stress Test (1x, 2x, 3x Friction Ladder)
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

  [0]  🚪 Exit Workstation
========================================================================================
Select an option [0-18]: 
```

> [!TIP]
> You can also run any option directly from the shell without entering the interactive menu:
> ```bash
> python3 run_mip.py --option 1    # Run scanner directly
> python3 run_mip.py --option 6    # Launch custom backtester directly
> python3 run_mip.py --option 16   # Regenerate HTML tearsheet directly
> ```

---

## 1.1 One-Click Self-Healing Launcher for Termux (`start_mip.sh`)

If you ever uninstall and reinstall Termux, Android will preserve your project files in `/storage/emulated/0/Documents/Project MIP`, but Termux's internal container and packages will be wiped.

Project MIP includes a **self-healing bootstrapper** (`start_mip.sh`):

### How to Run:
In the Termux native shell, type:
```bash
./start.sh
```
or
```bash
bash "/storage/emulated/0/Documents/Project MIP/start_mip.sh"
```

### What It Does:
1. **Verifies Android Storage**: Checks access to `/storage/emulated/0`; calls `termux-setup-storage` if access hasn't been granted yet.
2. **Auto-Installs `proot-distro` & Ubuntu**: Detects if PRoot Ubuntu exists. If absent, installs it automatically.
3. **Installs Quantitative Dependencies**: Probes Ubuntu for `pandas`, `pyarrow`, `numpy`, `requests`, and `python-dotenv`. If missing, installs all packages via Ubuntu `apt`.
4. **Configures Global Symlinks**: Sets up `/usr/local/bin/telegram-notify`.
5. **Idempotent & Instant**: If already installed, skips all checks and boots into `run_mip.py` in **under 0.5 seconds**.

### Android Home Screen 1-Tap Widget:
`start_mip.sh` automatically creates `~/.shortcuts/MIP`. To launch Project MIP in 1 tap:
1. Install **Termux:Widget** from F-Droid.
2. Long-press on your Samsung home screen and select **Widgets -> Termux:Widget**.
3. Select **MIP**.
4. You now have a single-tap home screen shortcut that boots the workstation directly!

---

## 1.2 Running on Windows 10 / 11 (`run_mip.bat`)

Project MIP features full cross-platform path resolution and runs identically on Windows (CMD or PowerShell):

### Prerequisites:
- Python 3.10+ installed on Windows.
- Ensure **"Add Python to PATH"** was checked during the Python installer.

### Launching:
1. Open the Project MIP folder on your Windows machine.
2. Double-click `run_mip.bat` (or open Command Prompt / PowerShell in the folder and type `run_mip.bat`).
3. On first run, `run_mip.bat` automatically verifies Python and installs any missing packages from `requirements.txt`.
4. The dashboard launches with native Windows console screen clearing (`cls`) and dynamic base directory resolution.

All 18 options, backtests, and HTML reports run identically on Windows!

---

## 2. Everyday Operator Playbook

Project MIP operates on a disciplined weekly cadence designed for institutional execution with **Zero Look-Ahead Bias**: signals are generated using Friday closing prices, and orders are executed at Monday market open.

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                             WEEKLY EXECUTION TIMELINE                            │
│                                                                                  │
│   FRIDAY 3:30 PM      FRIDAY 4:00 PM                   MONDAY 9:15 AM            │
│   Market Closes  ───► Run Options [1], [2], [3]  ───►  Market Opens              │
│                       (Scan & Broadcast Alert)         Execute Orders [Option 4] │
└──────────────────────────────────────────────────────────────────────────────────┘
```

### Step 1: Friday 4:00 PM — Run Scanner & Broadcast Alert

1. **Option `[1]` — Run Momentum Scanner**:
   - Evaluates all active NIFTY 500 stocks against the 5 strategy rules.
   - Automatically computes Market Breadth (% > 200 EMA), RRG Relative Rotation quadrants, and the 12-Sector Rotation matrix.
   - Saves results to `deliverables/phase_8/data_csv/screener_output_live.csv`.
2. **Option `[2]` — Preview Telegram Alert (Dry Run)**:
   - Prints the full Telegram alert directly in your terminal.
   - Verifies that the character count is safely under the 4,096-character Telegram limit (typically ~3,830 characters).
3. **Option `[3]` — Dispatch Live Alert**:
   - Sends the formatted HTML alert directly to your Telegram channel/bot.
   - Displays the Top 20 stocks, sector dynamics, market health, and exact target share sizing for ₹10 Lakhs and ₹1 Crore mandates.

### Step 2: Monday 9:15 AM — Generate Orders & Execute

1. **Option `[4]` — Generate Rebalance Orders & Portfolio Ledger**:
   - Compares your current portfolio holdings against the new Top 20 ranking.
   - Applies the **100% Exit Buffer**: any holding ranked between 1 and 40 is retained to minimize unnecessary turnover and taxes.
   - Any holding that breaks its 200 EMA, falls below 80% of its 52-week high, or drops past Rank 40 is sold at Monday Open.
   - Available cash is distributed equally among new entrants in whole integer shares.
   - Itemizes all statutory taxes (STT, Stamp Duty, GST, Exchange fees) and slippage.
   - Saves trade tickets and updates `data/portfolio/live_portfolio_ledger.json`.

### Step 3: Periodic Maintenance (Monthly or as Needed)

1. **Option `[5]` — Ingest Daily Bhavcopy**:
   - Appends newly downloaded NSE Bhavcopy CSVs to `data/universe/nifty500_pit_universe.parquet`.
   - If run without an argument, it automatically verifies database integrity.
2. **Option `[15]` — Sync Official NSE Sector Taxonomy**:
   - Downloads the latest official `ind_niftytotalmarket_list.csv` from NIFTY Indices.
   - Maps all 22 official industries into the 12 primary sectors.

---

## 3. How to Run Custom Backtests (Option `[6]`)

Option `[6]` launches the **Interactive Custom Strategy Backtester** (`production/run_custom_backtest.py`), allowing you to test any historical scenario, time horizon, portfolio size, or stress condition in under 5 seconds.

### Walkthrough of Interactive Prompts

When you select Option `[6]`, the workstation asks 8 simple questions (simply press `ENTER` to accept the sensible institutional default):

```
1. Start Date [YYYY-MM-DD, Default: 2016-01-01]: 
2. End Date   [YYYY-MM-DD, Default: 2026-08-31]: 
3. Portfolio Size (Top N holdings) [Default: 20]: 
4. Ranking Metric [1: Volar Score (Default), 2: Raw 252d Return]: 
5. Exit Buffer Rank Cutoff [Default: 40, recommended 2x Top-N]: 
6. Market Regime Filter (Pause entries if NIFTY 500 < 20 EMA) [Y/n, Default: Y]: 
7. Friction Tier [1: 1x Real Costs (Default), 2: 2x Stress, 3: 3x Extreme]: 
8. Initial Capital in INR [Default: 10000000 (₹1 Crore)]: 
```

### Common Testing Scenarios

#### Scenario A: The Full 10.6-Year Discovery Era (2016–2026)
- **Inputs**: Press `ENTER` on all 8 prompts.
- **Output**: Full 10.6-year cycle covering demonetization, 2017 bull run, 2018 NBFC crisis, 2020 COVID crash, 2021 liquidity rally, and 2022-2026 expansion.
- **Expected Results**: ~22.5% CAGR vs 10.5% Benchmark CAGR (+12% Alpha), Sharpe ~1.02, Calmar ~0.66.

#### Scenario B: The COVID Crash & Recovery (2020–2026)
- **Inputs**:
  - `Start Date`: `2020-01-01`
  - `End Date`: `2026-08-31`
- **Expected Results**: ~30.0% CAGR vs 10.7% Benchmark CAGR (+19.3% Alpha), Sharpe ~1.37, Max Drawdown ~30.4%.

#### Scenario C: Concentrated Portfolio (Top 10 Stocks)
- **Inputs**:
  - `Top N`: `10`
  - `Exit Buffer`: `20` (2x Top N)
- **What it tests**: Tests how a more aggressive, concentrated 10-stock portfolio performs vs the standard 20-stock basket.

#### Scenario D: Cost & Slippage Stress Test (3x Friction)
- **Inputs**:
  - `Friction Tier`: `3` (30 bps slippage + 3x statutory costs)
- **What it tests**: Verifies institutional profitability under extreme liquidity crunch conditions.

### Where Backtest Results Are Saved
Every run of the custom backtester exports 3 clean CSV files in the `reports/` folder:
1. `reports/custom_backtest_results.csv`: One-row summary of all parameters and performance metrics (CAGR, Alpha, Sharpe, Calmar, MaxDD, Win Rate, Profit Factor).
2. `reports/custom_backtest_trades.csv`: Detailed log of every single closed trade (symbol, buy date, buy price, sell date, sell price, PnL, exit reason, total friction paid).
3. `reports/custom_backtest_equity.csv`: Daily series of total portfolio value, cash balance, and active positions count.

---

## 4. Plain-English Indicator & Concept Guide

### 1. Volar Score vs. Raw Momentum
- **Raw Return**: Measures only how much a stock went up over the past 252 trading days ($\text{Price today} / \text{Price 1 year ago} - 1$).
  - *Problem*: Highly volatile, low-quality penny stocks can surge 200% on speculation before crashing 80%.
- **Volar Score**: $\text{Return}_{252} / \text{Volatility}_{252}$.
  - *Why it matters*: By dividing the 1-year return by its annualized daily volatility, the strategy rewards **smooth, steady, high-quality trends** and penalizes erratic price spikes. Volar cuts drawdown depth by 6.42 percentage points.

### 2. The 200 EMA Rule & 20 EMA Market Filter
- **Stock Trend Rule (200 EMA)**: A stock is only eligible for purchase if its current price is above its 200-day Exponential Moving Average. If a stock currently held in your portfolio falls below its 200 EMA on Friday close, it is sold on Monday open.
- **Market Protection Filter (20 EMA)**: Compares the NIFTY 500 index price against its 20-day EMA.
  - If $\text{NIFTY 500} \ge \text{20 EMA}$: **Market is Normal / Risk-On**. Entries are active.
  - If $\text{NIFTY 500} < \text{20 EMA}$: **Market is Defensive / Risk-Off**. New stock entries are paused, and capital stays in cash. This single rule reduces portfolio drawdown by over 12 percentage points during bear markets.

### 3. Market Breadth Health
Market Breadth measures the internal health and participation of the broader market:
- `% Above 200 EMA`: If $> 60\%$, the market is in **Strong Expansion** (broad rally). If $< 40\%$, the market is in **Contraction** (defensive caution).
- `% Within 20% of 52-Week High`: Measures how many stocks are near their annual highs. If $> 50\%$, momentum candidates are abundant.
- `Net New Highs`: $\text{New 52w Highs} - \text{New 52w Lows}$. Positive readings confirm bull market participation.

### 4. Julius de Kempenaer Relative Rotation Graphs (RRG)
RRG tracks the rotation of stocks and sectors relative to the NIFTY 500 benchmark across 4 phases:
- 🟢 **LEADING**: High relative strength and positive momentum ($\text{RS-Ratio} \ge 100$, $\text{RS-Momentum} \ge 100$). These are current market leaders.
- 🟢 **IMPROVING**: Lagging stocks that are accelerating rapidly toward leadership ($\text{RS-Ratio} < 100$, $\text{RS-Momentum} \ge 100$). Prime turnaround candidates.
- 🟡 **WEAKENING**: Leading stocks that are losing upside momentum ($\text{RS-Ratio} \ge 100$, $\text{RS-Momentum} < 100$). Time to monitor for exits.
- 🔴 **LAGGING**: Low relative strength and negative momentum ($\text{RS-Ratio} < 100$, $\text{RS-Momentum} < 100$). Stocks underperforming the market.

### 5. The 100% Exit Buffer (Rank 40 Rule)
- We buy the **Top 20** ranked momentum stocks.
- If we rebalanced strictly to the Top 20 every month, a stock slipping from Rank 19 to Rank 22 would be sold, incurring taxes and slippage, only to be rebought next month.
- **The Buffer Solution**: An existing holding is only sold for ranking reasons if it drops past **Rank 40** (2x portfolio size).
- **Result**: Cuts annual portfolio turnover by **30.4%** and saves over ₹15 Lakhs in transaction costs without sacrificing return.

### 6. Transaction Cost Schedule
Every backtest and live execution strictly models full statutory Indian institutional costs:
- **Securities Transaction Tax (STT)**: 0.10% on delivery buy and sell.
- **NSE Transaction Charges**: 0.00325%.
- **SEBI Turnover Fee**: 0.0001%.
- **GST (Goods & Services Tax)**: 18.0% on brokerage and transaction charges.
- **State Stamp Duty**: 0.015% on buys.
- **Execution Slippage**: 10.0 basis points (0.10%) per execution side.

---

## 5. Directory & File Reference Guide

| Directory / File | Description |
|---|---|
| `run_mip.py` | Master terminal dashboard and workstation launcher (18 options). |
| `HOW_TO_RUN.md` | This operator runbook and reference manual. |
| `production/scanner.py` | Production momentum screener with Breadth, RRG, and Sector Rotation. |
| `production/telegram_alerts.py` | Automated Telegram alert formatter and live broadcast dispatcher. |
| `production/run_custom_backtest.py` | Interactive custom strategy backtesting engine. |
| `production/sync_nse_sectors.py` | Official NSE constituent industry synchronization tool. |
| `production/breadth.py` | Standalone quantitative market breadth engine. |
| `production/sector_rotation.py` | Standalone 12-sector rotation and relative strength matrix engine. |
| `production/plugins/rrg_filter.py` | Standalone Julius de Kempenaer RRG quadrant analyzer. |
| `data/universe/nifty500_pit_universe.parquet` | Master point-in-time, survivorship-free daily universe (2.1M bars, 1,039 symbols). |
| `data/universe/symbol_sector_map.json` | Master mapping of 1,039 symbols to 12 primary NSE sectors. |
| `deliverables/phase_7/data_csv/nifty_500_benchmark_proxy.csv` | Continuous NIFTY 500 benchmark proxy series (2007–2026). |
| `deliverables/phase_8/data_csv/screener_output_live.csv` | Live screener output with sector tags, Volar scores, and RRG quadrants. |
| `reports/mip_institutional_tearsheet.html` | Interactive HTML tearsheet with Plotly equity charts and risk metrics. |
| `reports/custom_backtest_results.csv` | Output summary metrics from custom backtest runs. |
| `reports/custom_backtest_trades.csv` | Itemized closed trade logs from custom backtest runs. |
| `reports/custom_backtest_equity.csv` | Daily equity curve series from custom backtest runs. |
| `/sdcard/Documents/deliverables/` | Shared Android mobile folder mirrored with all live JSON, CSV, and HTML reports. |

---

## 6. Support & Troubleshooting

- **How to view the HTML tearsheet on your phone**:
  Open your Samsung Internet or Chrome browser and open `/sdcard/Documents/deliverables/mip_institutional_tearsheet.html`.
- **How to test Telegram notifications without sending**:
  Select Option `[2]` from the menu, or run `python3 run_mip.py --option 2`.
- **Emergency stop**:
  Press `Ctrl + C` at any prompt to safely return to the main workstation menu.
