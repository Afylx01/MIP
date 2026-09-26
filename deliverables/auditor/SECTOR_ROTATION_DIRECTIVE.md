# BUILDER DIRECTIVE: IMPLEMENT SECTOR ROTATION ENGINE & TELEGRAM BROADCAST

**Directive ID**: `DIR-PROD-SECTOR-ROTATION-01`  
**Standing Gate**: `HALT-12` (Active — Pause for Auditor Review upon task completion)  
**Target Environment**: PRoot Ubuntu ARM64 (`/usr/bin/python3`)  
**Workspace**: `/storage/emulated/0/Documents/Project MIP`  
**Deliverables Mirror**: `/sdcard/Documents/deliverables/`  

---

## 1. Executive Objective

Extend the Project MIP production scanner suite (`production/scanner.py`, `production/breadth.py`, and `production/telegram_alerts.py`) to systematically analyze and broadcast **Sector Rotation dynamics** on every execution run.

Every time the scanner executes, it must:
1. Map all active universe symbols to standardized **NSE Sectoral Classifications**.
2. Compute **Sector Performance, Relative Strength (RS), Breadth, and RRG Rotation Quadrants** across all sectors.
3. Quantify **Sector Concentration of Top 20 Momentum Candidates**.
4. Broadcast an integrated **Sector Rotation Table** directly inside the Telegram execution alert via `/usr/local/bin/telegram-notify --html`.

---

## 2. Quantitative & Mathematical Specifications

### A. Sector Taxonomy (12 Primary Sectors)
All stocks in `data/universe/nifty500_pit_universe.parquet` must map deterministically to one of 12 primary sectors:
1. `Automobile & Auto Components` (`AUTO`)
2. `Banking & Financial Services` (`FINSERV`)
3. `Capital Goods & Industrials` (`CAPGOODS`)
4. `Chemicals & Petrochemicals` (`CHEMICALS`)
5. `Construction & Real Estate` (`REALTY`)
6. `Consumer Durables & Apparel` (`CONSDUR`)
7. `Fast Moving Consumer Goods` (`FMCG`)
8. `Healthcare & Pharmaceuticals` (`PHARMA`)
9. `Information Technology` (`IT`)
10. `Metals & Mining` (`METALS`)
11. `Oil, Gas & Consumable Fuels` (`ENERGY`)
12. `Telecommunication, Media & Utilities` (`INFRA_MEDIA`)

### B. Sector Metrics Engine (`production/sector_rotation.py`)
For each sector $S$ on `as_of_date`:
1. **Sector Performance**:
   - $\text{Ret}_{1M} = \text{Equal-weighted mean 21-day return of all active stocks in } S$.
   - $\text{Ret}_{3M} = \text{Equal-weighted mean 63-day return of all active stocks in } S$.
   - $\text{Ret}_{1Y} = \text{Equal-weighted mean 252-day return of all active stocks in } S$.
2. **Sector Relative Strength vs NIFTY 500**:
   - $\text{Alpha}_{1M} = \text{Ret}_{1M}(S) - \text{Ret}_{1M}(\text{NIFTY 500})$
   - $\text{Alpha}_{3M} = \text{Ret}_{3M}(S) - \text{Ret}_{3M}(\text{NIFTY 500})$
3. **Sector Breadth**:
   - $\text{Sector\_Breadth}_{200} = \frac{\sum_{i \in S} (\text{Close}_i > \text{EMA}_{200, i})}{N_S} \times 100\%$
   - $\text{Sector\_Breadth}_{52w} = \frac{\sum_{i \in S} (\text{Close}_i \ge 0.80 \times \text{High}_{252, i})}{N_S} \times 100\%$
4. **Sector RRG Quadrant**:
   - Compute mean JdK RS-Ratio and mean RS-Momentum for sector $S$:
     - `LEADING`: $\overline{\text{RS-Ratio}} \ge 100.0$ AND $\overline{\text{RS-Momentum}} \ge 100.0$
     - `WEAKENING`: $\overline{\text{RS-Ratio}} \ge 100.0$ AND $\overline{\text{RS-Momentum}} < 100.0$
     - `LAGGING`: $\overline{\text{RS-Ratio}} < 100.0$ AND $\overline{\text{RS-Momentum}} < 100.0$
     - `IMPROVING`: $\overline{\text{RS-Ratio}} < 100.0$ AND $\overline{\text{RS-Momentum}} \ge 100.0$
5. **Momentum Leadership Density**:
   - `candidate_count`: Number of Top 20 qualified momentum scrips belonging to sector $S$.
   - `candidate_share`: $\frac{\text{candidate\_count}}{20} \times 100\%$.

---

## 3. Implementation Tasks

### Task 1: Sector Taxonomy & Mapping Database (`production/sector_map.py`)
- Create standard dictionary mapping for NSE symbols to the 12 primary sectors.
- Ensure 100% of symbols currently in `data/universe/nifty500_pit_universe.parquet` have a valid sector mapping (fallback to most appropriate sector or `CAPGOODS`/`CONSDUR` based on company name/business).
- Provide helper function `get_sector(symbol: str) -> str`.
- Export mapping reference to `data/universe/symbol_sector_map.json`.

### Task 2: Build Sector Rotation Engine (`production/sector_rotation.py`)
- Ingest active universe bars and benchmark data.
- Compute all 5 sector metrics defined in Section 2B.
- Rank sectors by composite momentum score:
  $$\text{Sector\_Rank\_Score} = 0.5 \times \text{Alpha}_{1M} + 0.5 \times \text{Alpha}_{3M} + 0.2 \times (\text{Sector\_Breadth}_{200} - 50.0)$$
- Export live sector rotation snapshot to `deliverables/phase_8/data_csv/sector_rotation_live.json` and mirror to `/sdcard/Documents/deliverables/`.

### Task 3: Scanner Integration (`production/scanner.py`)
- Add `sector` column to universe snapshot and candidate ranking.
- Call `SectorRotationEngine` during `run_scan()`.
- Export `sector` column in `deliverables/phase_8/data_csv/screener_output_live.csv`.
- Log ranked sector rotation summary in scanner terminal output.

### Task 4: Telegram Alert Formatting (`production/telegram_alerts.py`)
- Incorporate a dedicated **Sector Rotation & Leadership Table** into the Telegram HTML alert:
  - `<pre>` formatted table:
    ```
    SECTOR       1M-ALPHA  BREADTH  RRG   PICKS
    -------------------------------------------
    CAPGOODS       +4.2%    74.1%   LEAD    6
    PHARMA         +2.8%    68.5%   LEAD    4
    AUTO           +1.5%    62.0%   IMPR    3
    ...
    ```
- Display Top 3 Inflowing Sectors (Rotating into Leadership) and Lagging Sectors.
- Ensure total Telegram message length remains strictly **under 4,096 characters** (streamline candidate table or spacing as needed to keep overall message ~3,500 characters).

### Task 5: End-to-End Verification & Live Dispatch
- Execute:
  ```bash
  /usr/bin/python3 production/scanner.py --as-of-date 2026-08-28
  /usr/bin/python3 production/telegram_alerts.py --as-of-date 2026-08-28 --dry-run
  /usr/bin/python3 production/telegram_alerts.py --as-of-date 2026-08-28
  ```
- Verify zero syntax errors, valid JSON outputs, character limit invariance, and live delivery to Telegram.

---

## 4. Standing Gate HALT-12

Upon completion of Tasks 1 through 5:
1. Halt execution and wait for Auditor review.
2. Commit changes cleanly with message `feat(sector): implement sector rotation engine and telegram broadcast`.
3. Report completion so the Auditor can inspect code, verify sector relative strength math, and certify HALT-12.
