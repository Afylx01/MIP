# PRODUCTION MASTER DIRECTIVE: WORKSPACE PRUNING, SURVIVORSHIP UNIVERSE, TELEGRAM SCANNER & INSTITUTIONAL TEARSHEET

**Document**: `PRODUCTION_MASTER_DIRECTIVE.md`  
**From**: Lead Quantitative Architect & Auditor  
**To**: Builder Agent  
**Date**: September 26, 2026  
**Status**: ACTIVE PRODUCTION DIRECTIVE  
**Standing Gate**: **HALT-10** (Mandatory pause awaiting Auditor review and sign-off on the complete production deployment)

---

## 1. Executive Mission & Scope

Project MIP has successfully cleared all 32 empirical due-diligence gates in Phase 7 (`is_proven(results) == True`) and verified the live production pipeline mechanics in Phase 8.

The Builder Agent is hereby directed to execute this master production transition across four structured tasks:

```
                               MASTER PRODUCTION TRANSITION ROADMAP
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ Task 1: Workspace Pruning, Directory Sanitization & Fresh Git Reset / Force Push                      │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ Task 2: Standardized Survivorship-Free Master Universe Database & Idempotent Auto-Updater             │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ Task 3: Production Telegram Momentum Scanner with Pluggable RRG (Relative Rotation Graph) Hook        │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ Task 4: Institutional Interactive HTML Performance Tearsheet & Executive Visual Analytics             │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ Standing Gate HALT-10: Final Auditor Inspection & Production Certification                            │
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Technical Specification by Task

---

### Task 1: Workspace Pruning, Directory Sanitization & Fresh Git Reset / Push

#### Objective
Clean the repository of all temporary caches, redundant datasets, and intermediate test files, leaving only essential, production-grade assets. Then re-initialize Git to perform a clean, fresh push to remote repository `Afylx01/MIP` on branch `main`.

#### 1. Files & Directories to Permanently Remove:
Delete the following files from `/storage/emulated/0/Documents/Project MIP`:
- `data/yfinance_ohlcv_2007_2026.parquet` (101 MB rejected test dataset)
- `data/yfinance_batches/` (temporary download cache)
- `data/price_cache_export.parquet` (64 MB redundant duplicate)
- `data/adjusted_bhavcopy_bars_modern.parquet` (33 MB redundant duplicate)
- `data/symbol_map_backup_*.parquet` (all intermediate backup files)
- `data/symbol_map_review_*.csv`
- `data/symbol_map_unresolved.csv`
- `data/test_*.csv`
- `test_flag_definitions.py`
- `test_s4_rebuild.py`
- `phase_5_5_build_prompt-1.md`
- All `__pycache__` directories and `*.pyc` files across the entire workspace tree.

#### 2. Core Production Assets to Strictly Preserve:
Verify that the following essential files remain intact:
- `data/adjusted_bhavcopy_max_2007_2026.parquet` (Certified 20-year Bhavcopy master grid)
- `data/symbol_map.parquet` (Active/delisted ticker mapping)
- `data/trading_calendar.txt` (Official NSE trading sessions)
- `data/benchmarks/` (`NIFTY_50.csv`, `NIFTY_100.csv`, `SENSEX.csv`)
- `data/verification/survivorship_graveyard.csv` (1,209 verified dead scrips)
- `indian_backtest/` (Verified institutional backtest engine)
- `deliverables/` (Formal audit deliverables and signed rulings)
- `scripts/telegram_notify.py` (Telegram bot dispatch engine)
- `.env` and `GEMINI.md` (System configurations)

#### 3. Production `.gitignore`:
Ensure `.gitignore` contains:
```gitignore
.env
__pycache__/
*.py[cod]
*$py.class
*.log
scratch/
tmp/
.agents/
data/yfinance_batches/
```

#### 4. Clean Git Reset & Force Push:
Re-initialize the Git history to a clean, single-root commit and force push to `origin main`:
```bash
cd "/storage/emulated/0/Documents/Project MIP"
git checkout --orphan temp_clean_branch
git add -A
git commit -m "feat(core): initialize clean production codebase with verified 20-year Bhavcopy universe"
git branch -D main
git branch -m main
git push -f origin main
```
*Verification*: Run `git status` (must be clean) and `git ls-files .env` (must return empty).

---

### Task 2: Standardized Survivorship-Free Universe Database & Auto-Updater

#### Objective
Consolidate the verified master price grid into a standardized, survivorship-bias-free universe database that will serve as the permanent foundational data feed for this and future quantitative strategies, accompanied by an idempotent auto-update script.

#### 1. Master Universe Database: `data/universe/nifty500_pit_universe.parquet`
1. Create directory `data/universe/`.
2. Generate `data/universe/nifty500_pit_universe.parquet` by merging:
   - Primary data: `data/adjusted_bhavcopy_max_2007_2026.parquet` (2,137,630 bars across 1,039 symbols, 2007–2026).
   - Graveyard annotations: Cross-reference symbols with `data/verification/survivorship_graveyard.csv`.
3. Schema:
   - `date`: `datetime64[ns]` or string `YYYY-MM-DD`
   - `symbol`: `string`
   - `open`: `float64`
   - `high`: `float64`
   - `low`: `float64`
   - `close`: `float64`
   - `volume`: `int64` / `float64`
   - `is_delisted`: `bool` (`True` if the stock is delisted/bankrupt, `False` if active)
4. Enforce Invariants:
   - Unique `(symbol, date)` composite key.
   - Chronologically monotonic per symbol.
   - Zero null prices.
5. Create metadata manifest: `data/universe/universe_metadata.json` documenting:
   - `total_bars`, `unique_symbols`, `delisted_symbols`, `start_date`, `end_date`, `sha256_hash`, and schema definitions.

#### 2. Standalone Auto-Updater: `scripts/update_universe.py`
Implement `scripts/update_universe.py` with standard CLI arguments:
```bash
python3 scripts/update_universe.py [--new-bhavcopy /path/to/cm<DATE>bhav.csv] [--verify-only]
```
- Ingests new daily NSE Bhavcopy files.
- Resolves ticker changes via `data/symbol_map.parquet`.
- Applies split/bonus adjustments if ex-dates are encountered.
- Appends new daily records atomically to `data/universe/nifty500_pit_universe.parquet`.
- Automatically updates `data/universe/universe_metadata.json`.
- Includes `--verify-only` self-testing flag to certify integrity.

---

### Task 3: Production Telegram Momentum Scanner with Pluggable RRG Hook

#### Objective
Build an automated market scanner that screens the active universe on Friday EOD, formats an actionable executive alert, and dispatches it to Telegram. The architecture must include an extensible plugin hook for Relative Rotation Graphs (RRG).

#### 1. Pluggable Filter Architecture (`production/plugins/`):
1. **`production/plugins/base_plugin.py`**:
   Define the standard plugin interface:
   ```python
   from abc import ABC, abstractmethod
   import pandas as pd

   class FilterPlugin(ABC):
       @abstractmethod
       def evaluate(self, universe_df: pd.DataFrame, as_of_date: str) -> pd.DataFrame:
           """
           Takes the universe price dataframe and returns the dataframe with:
           - A boolean column 'passed_<plugin_name>'
           - Additional diagnostic indicator columns
           """
           pass
   ```
2. **`production/plugins/rrg_filter.py` (Extensible RRG Hook)**:
   - Implement the JdK Relative Rotation Graph framework:
     - Relative Strength ratio vs NIFTY 500: $\text{RS} = \text{Stock} / \text{Index}$.
     - RS-Ratio: $100 + \text{normalized moving average of RS}$.
     - RS-Momentum: $100 + \text{rate of change of RS-Ratio}$.
     - Quadrant classification: **Leading**, **Weakening**, **Lagging**, **Improving**.
   - Include configuration flag `enable_rrg=False` by default (ready to be toggled `True` when tuning parameters).

#### 2. Core Momentum Scanner: `production/scanner.py`
- Ingest `data/universe/nifty500_pit_universe.parquet` and benchmark `data/benchmarks/NIFTY_50.csv`.
- Evaluate the verified 5-tier strategy rules:
  1. **Filter 1 (Retracement)**: Close $\ge 0.80 \times 252\text{-day High}$ (within 20% of 52-week High).
  2. **Filter 2 (Trend)**: Close $>$ 200 EMA.
  3. **Filter 3 (Relative Strength)**: Stock / NIFTY 500 ratio $>$ 200 EMA of ratio.
  4. **Ranking Metric**: Volar Score = $\frac{\text{Return}_{252}}{\sigma_{252}}$.
  5. **Market Regime**: NIFTY 500 Close vs 20-day EMA (Normal vs Defensive).
- Run candidates through active plugins (including RRG hook).
- Output ranked candidates to `deliverables/phase_8/data_csv/screener_output_live.csv`.

#### 3. Telegram Formatter & Dispatcher: `production/telegram_alerts.py`
- Format an institutional HTML/Markdown message:
  - Header: Strategy Name, Date, Market Regime (NORMAL vs DEFENSIVE).
  - Top 20 Candidates Table: Rank, Symbol, Close Price, Distance from 52w High, 200 EMA Ratio, Volar Score, Volume.
  - Position Sizing Recommendations: Target whole shares and rupee outlay for ₹10 Lakhs and ₹1 Crore AUM tiers.
- Dispatch via `/usr/local/bin/telegram-notify --html`.
- Support `--dry-run` flag to preview formatted output in terminal without sending.

---

### Task 4: Institutional Interactive HTML Tearsheet & Analytics Dashboard

#### Objective
Author a self-contained, interactive HTML dashboard in `reports/mip_institutional_tearsheet.html` summarizing the backtesting performance, stress test survival, and strategy rationale.

#### Technical Specifications:
- Single standalone `.html` file (zero web server required).
- Use CDN-based Plotly.js (`https://cdn.plot.ly/plotly-2.35.2.min.js`).
- Modern dark-mode institutional UI (Bloomberg / FactSet inspired palette).

#### Required Dashboard Sections:

1. **Executive Headline Banner & Core Metrics**:
   - CAGR: **22.97%** | Sharpe: **0.82** | Sortino: **0.89** | Calmar: **0.50** | Max Drawdown: **45.92%** | Jensen's Alpha: **+13.03%** | Deflated Sharpe: **1.0000**.
2. **Strategy Rationale ("Why This Strategy Works")**:
   - Economic & behavioral justification: Capitalizes on post-earnings announcement drift (PEAD) and the disposition effect in Indian mid/smallcaps.
   - Risk management justification: Volar volatility-scaling suppresses low-quality high-beta spikes; the 100% exit buffer slashes turnover by 30.4%; the 20 EMA regime filter cuts peak drawdown by 12.5 pp.
3. **Interactive Plotly Visualizations**:
   - **Chart 1: Interactive Equity Curve**: Logarithmic and linear scales toggle comparing Strategy vs NIFTY 500 TRI vs NIFTY 50 (2016–2026).
   - **Chart 2: Underwater Drawdown Waterfall**: Peak-to-trough drawdown plot showing recovery times across all episodes.
   - **Chart 3: Monthly Returns Heatmap**: Interactive year $\times$ month matrix (2016 to 2026) color-coded green to red.
   - **Chart 4: Rolling Risk Ratios**: Rolling 12-month Sharpe Ratio and Jensen's Alpha.
   - **Chart 5: Monte Carlo Distribution**: 1,000-run random top-20 bootstrap distribution histogram with strategy performance highlighted at the 100th percentile ($p = 0.0000$).
4. **16-Criterion Due-Diligence Card & 32-Gate Compliance Table**:
   - Embed the 16-criterion institutional tearsheet (`is_proven(results) == True`).
   - Interactive, searchable table of all 32 verification gates across Data Integrity, Cost Stress, Walk-Forward, Regimes, and Component Attribution.
5. **Macro Regime Survival Tearsheet**:
   - Performance breakdown across all 6 Indian market cycles (2008 GFC, 2009–10 Recovery, 2011–13 Bear/Sideways, 2014–17 Bull, 2018–19 NBFC, 2020 COVID & Supercycle).
6. **File Exports**:
   - Save to `reports/mip_institutional_tearsheet.html`.
   - Mirror to `/sdcard/Documents/deliverables/mip_institutional_tearsheet.html` for instant mobile browser viewing.

---

## 3. Strict Execution Invariants & Standing Gate HALT-10

1. **Rule R-1 (Append-Only Integrity)**: Never mutate or delete previous gate deliverable rulings (`deliverables/*/RULING.md`).
2. **Rule R-2 (Recompute, Don't Trust)**: Compute all metrics directly from the parquet price grid.
3. **Rule R-3 (Strict Cash Conservation)**: Total Portfolio Value $\equiv$ Invested Market Value + Cash Balance. Accounting residual must strictly equal `0.00` to the paisa.
4. **Rule R-6 (PRoot ARM64 Compatibility)**: Strictly use Ubuntu system python (`/usr/bin/python3`).
5. **Rule R-10 (Standing Gate Discipline)**: **DO NOT proceed past Task 4.** Halt at **Standing Gate HALT-10** and await Auditor inspection and sign-off.

---

**Directive Status**: ACTIVE & READY FOR BUILDER EXECUTION.
