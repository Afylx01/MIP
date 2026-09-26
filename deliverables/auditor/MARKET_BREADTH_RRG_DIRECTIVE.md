# BUILDER DIRECTIVE: IMPLEMENT MARKET BREADTH & AUTOMATED RRG TELEGRAM DISPATCH

**Directive ID**: `DIR-PROD-BREADTH-RRG-01`  
**Standing Gate**: `HALT-11` (Active — Pause for Auditor Review upon task completion)  
**Target Environment**: PRoot Ubuntu ARM64 (`/usr/bin/python3`)  
**Workspace**: `/storage/emulated/0/Documents/Project MIP`  
**Deliverables Mirror**: `/sdcard/Documents/deliverables/`  

---

## 1. Executive Objective

Upgrade the production momentum scanner suite (`production/scanner.py` and `production/telegram_alerts.py`) to systematically compute and broadcast **Market Breadth** and **Relative Rotation Graph (RRG)** analytics on every execution run.

Every time the scanner executes, it must:
1. Calculate institutional **Market Breadth metrics** across the point-in-time universe.
2. Calculate Julius de Kempenaer (JdK) **RRG Quadrant distribution** across the point-in-time universe.
3. Include each candidate's **RRG Quadrant** (`LEADING`, `IMPROVING`, `WEAKENING`, `LAGGING`), **RS-Ratio**, and **RS-Momentum** in the candidate ranking.
4. Format and dispatch an institutional-grade executive HTML alert to Telegram via `/usr/local/bin/telegram-notify --html`.

---

## 2. Quantitative & Mathematical Specifications

### A. Market Breadth Engine (`production/breadth.py`)
Evaluate across all active stocks in `data/universe/nifty500_pit_universe.parquet` on `as_of_date`:

1. **Trend Participation Breadth**:
   - `pct_above_200_ema`: $\frac{\sum (\text{Close} > \text{EMA}_{200})}{N} \times 100\%$ (Long-Term Structural Trend)
   - `pct_above_50_ema`: $\frac{\sum (\text{Close} > \text{EMA}_{50})}{N} \times 100\%$ (Medium-Term Swing Health)
   - `pct_above_20_ema`: $\frac{\sum (\text{Close} > \text{EMA}_{20})}{N} \times 100\%$ (Short-Term Tactical Momentum)
2. **High Proximity Breadth (Candidate Pool Viability)**:
   - `pct_within_20pct_52wh`: $\frac{\sum (\text{Close} \ge 0.80 \times \text{High}_{252})}{N} \times 100\%$
   - `pct_within_5pct_52wh`: $\frac{\sum (\text{Close} \ge 0.95 \times \text{High}_{252})}{N} \times 100\%$ (Active Leadership Density)
3. **Net New Highs**:
   - `new_52w_highs`: Count of stocks with $\text{Close} \ge 0.99 \times \text{High}_{252}$
   - `new_52w_lows`: Count of stocks with $\text{Close} \le 1.01 \times \text{Low}_{252}$
   - `net_highs_lows`: $\text{new\_52w\_highs} - \text{new\_52w\_lows}$
4. **Market Breadth Regime Classification**:
   - 🟢 **STRONG EXPANSION**: `pct_above_200_ema >= 60.0%` AND `pct_above_50_ema >= 55.0%`
   - 🟡 **SELECTIVE / NEUTRAL**: `40.0% <= pct_above_200_ema < 60.0%`
   - 🔴 **CONTRACTION / DEFENSIVE**: `pct_above_200_ema < 40.0%` OR (`pct_above_200_ema < 50.0%` AND `net_highs_lows < 0`)

### B. RRG Universe Distribution (`production/plugins/rrg_filter.py`)
Using Julius de Kempenaer (JdK) formulas:
- $\text{RS} = \frac{\text{Close}_{\text{stock}}}{\text{Close}_{\text{NIFTY 500}}}$
- $\text{RS-Ratio} = 100.0 \times \frac{\text{RS}}{\text{SMA}_{50}(\text{RS})}$
- $\text{RS-Momentum} = 100.0 \times \frac{\text{RS-Ratio}}{\text{SMA}_{10}(\text{RS-Ratio})}$
- **Quadrants**:
  - `LEADING`: $\text{RS-Ratio} \ge 100.0$ AND $\text{RS-Momentum} \ge 100.0$
  - `WEAKENING`: $\text{RS-Ratio} \ge 100.0$ AND $\text{RS-Momentum} < 100.0$
  - `LAGGING`: $\text{RS-Ratio} < 100.0$ AND $\text{RS-Momentum} < 100.0$
  - `IMPROVING`: $\text{RS-Ratio} < 100.0$ AND $\text{RS-Momentum} \ge 100.0$
- Universe breakdown: Count and percentage of universe in each quadrant.

---

## 3. Implementation Tasks

### Task 1: Build Market Breadth Module
- **File**: `production/breadth.py`
- Ingests universe bars and continuous benchmark proxy.
- Computes EMAs (20, 50, 200), 52-week High/Low, and computes all breadth metrics above.
- Returns structured dictionary and exports `deliverables/phase_8/data_csv/market_breadth_live.json`.

### Task 2: Refactor Scanner to Always Run Breadth & RRG
- **File**: `production/scanner.py`
- RRG calculation enabled by default on all universe bars (so every stock has `rrg_quadrant`, `rrg_rs_ratio`, `rrg_rs_momentum`).
- Call `MarketBreadthEngine` during each scan.
- Output combined dataset:
  - `deliverables/phase_8/data_csv/screener_output_live.csv` (includes RRG columns).
  - Include breadth summary and RRG distribution in logs and exports.

### Task 3: Upgrade Telegram Alert Formatter & Dispatcher
- **File**: `production/telegram_alerts.py`
- Format institutional HTML alert containing:
  1. Header: Date, Strategy Name, Regime Status.
  2. **Market Breadth Table** (ASCII `<pre>`): % > 200 EMA, % > 50 EMA, % > 20 EMA, % within 20% & 5% of 52wH, Net New Highs, Breadth Regime.
  3. **RRG Quadrant Distribution Table** (ASCII `<pre>`): Count & % in LEADING, IMPROVING, WEAKENING, LAGGING.
  4. **Top 20 Momentum Candidates Table** (ASCII `<pre>`): Rank, Symbol, Price, 52wH Dist, Volar, **RRG Quadrant** (`LEAD`, `IMPR`, etc.), and RS-Ratio.
  5. Position Sizing: ₹10L and ₹1Cr mandate allocations.
- Test with `--dry-run` and live dispatch via `telegram-notify --html`.

### Task 4: End-to-End Test & Verification
- Execute:
  ```bash
  /usr/bin/python3 production/scanner.py --as-of-date 2026-08-28
  /usr/bin/python3 production/telegram_alerts.py --as-of-date 2026-08-28 --dry-run
  /usr/bin/python3 production/telegram_alerts.py --as-of-date 2026-08-28
  ```
- Verify zero syntax errors, valid JSON exports, and successful Telegram delivery.

---

## 4. Standing Gate HALT-11

Upon completion of Tasks 1 through 4:
1. Halt execution and wait for Auditor review.
2. Do not modify master universe data files.
3. Present output logs, generated CSV/JSON paths, and Telegram dispatch confirmation.
