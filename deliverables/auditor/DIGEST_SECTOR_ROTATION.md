# PROJECT MIP: SECTOR ROTATION ENGINE & TELEGRAM BROADCAST
## Verification Digest & Institutional Audit Report — Directive DIR-PROD-SECTOR-ROTATION-01
**Standing Gate**: `HALT-12` (PAUSED — Awaiting Institutional Auditor Review)  
**Date**: September 26, 2026  
**Environment**: Samsung Galaxy S23 (PRoot Ubuntu ARM64, Python 3.12.3)  
**Workspace**: `/storage/emulated/0/Documents/Project MIP`  
**Deliverables Mirror**: `/sdcard/Documents/deliverables/`  

---

### Executive Summary

Under Directive `DIR-PROD-SECTOR-ROTATION-01`, Project MIP's production scanner suite was extended to perform quantitative **Sector Rotation Analysis** across the 12 primary NSE sectors. On every execution run, the system now maps active scrips to sectoral categories, evaluates equal-weighted sector returns across 1-month, 3-month, and 1-year windows, measures sector relative strength (Alpha) against the NIFTY 500 benchmark, computes internal sector breadth (% > 200 EMA and % within 20% of 52w High), tracks sector RRG rotation quadrants, and quantifies the concentration share of Top 20 momentum candidates.

A consolidated ASCII **Sector Rotation & Leadership Table** was integrated into the automated Telegram alert dispatch pipeline. The message formatting was engineered to remain under Telegram's strict 4,096-character limit (achieving 3,831 characters with all market breadth, RRG, sector rotation, candidate rankings, and dual-tier position sizing). Live end-to-end verification and Telegram dispatch were executed on Friday EOD data (`2026-08-28`).

---

### 1. Sector Taxonomy & Mapping Database (`production/sector_map.py`)

A deterministic 12-sector taxonomy was codified representing the primary sectors of the National Stock Exchange of India (NSE):
1. `AUTO` — Automobile & Auto Components
2. `FINSERV` — Banking & Financial Services
3. `CAPGOODS` — Capital Goods & Industrials
4. `CHEMICALS` — Chemicals & Petrochemicals
5. `REALTY` — Construction & Real Estate
6. `CONSDUR` — Consumer Durables & Apparel
7. `FMCG` — Fast Moving Consumer Goods
8. `PHARMA` — Healthcare & Pharmaceuticals
9. `IT` — Information Technology
10. `METALS` — Metals & Mining
11. `ENERGY` — Oil, Gas & Consumable Fuels
12. `INFRA_MEDIA` — Telecommunication, Media & Utilities

#### Universe Coverage Verification
- **Total Master Universe Symbols**: 1,039
- **Unmapped / Null Symbols**: 0 (100.0% coverage)
- **Sector Distribution**:
  - `CAPGOODS`: 388 (37.3%)
  - `FINSERV`: 141 (13.6%)
  - `INFRA_MEDIA`: 85 (8.2%)
  - `PHARMA`: 72 (6.9%)
  - `IT`: 72 (6.9%)
  - `REALTY`: 65 (6.3%)
  - `CONSDUR`: 47 (4.5%)
  - `CHEMICALS`: 42 (4.0%)
  - `FMCG`: 42 (4.0%)
  - `AUTO`: 37 (3.6%)
  - `METALS`: 26 (2.5%)
  - `ENERGY`: 22 (2.1%)
- **Exported Reference**: `data/universe/symbol_sector_map.json` (mirrored to `/sdcard/Documents/deliverables/symbol_sector_map.json`).

---

### 2. Sector Rotation Quantitative Engine (`production/sector_rotation.py`)

#### Mathematical Formulation
For each sector $S$ on `as_of_date`:
1. **Performance**:
   $$\text{Ret}_{1M} = \frac{1}{N_S} \sum_{i \in S} \text{Ret}_{21d, i}, \quad \text{Ret}_{3M} = \frac{1}{N_S} \sum_{i \in S} \text{Ret}_{63d, i}, \quad \text{Ret}_{1Y} = \frac{1}{N_S} \sum_{i \in S} \text{Ret}_{252d, i}$$
2. **Relative Strength Alpha vs NIFTY 500**:
   $$\text{Alpha}_{1M} = \text{Ret}_{1M}(S) - \text{Ret}_{1M}(\text{NIFTY 500})$$
   $$\text{Alpha}_{3M} = \text{Ret}_{3M}(S) - \text{Ret}_{3M}(\text{NIFTY 500})$$
3. **Sector Breadth**:
   $$\text{Sector\_Breadth}_{200} = \frac{\sum_{i \in S} (\text{Close}_i > \text{EMA}_{200, i})}{N_S} \times 100\%$$
   $$\text{Sector\_Breadth}_{52w} = \frac{\sum_{i \in S} (\text{Close}_i \ge 0.80 \times \text{High}_{252, i})}{N_S} \times 100\%$$
4. **Sector RRG Quadrant**:
   - Mean JdK RS-Ratio ($\overline{\text{RS-Ratio}}$) and mean RS-Momentum ($\overline{\text{RS-Momentum}}$):
     - `LEADING`: $\overline{\text{RS-Ratio}} \ge 100.0$ AND $\overline{\text{RS-Momentum}} \ge 100.0$
     - `WEAKENING`: $\overline{\text{RS-Ratio}} \ge 100.0$ AND $\overline{\text{RS-Momentum}} < 100.0$
     - `LAGGING`: $\overline{\text{RS-Ratio}} < 100.0$ AND $\overline{\text{RS-Momentum}} < 100.0$
     - `IMPROVING`: $\overline{\text{RS-Ratio}} < 100.0$ AND $\overline{\text{RS-Momentum}} \ge 100.0$
5. **Momentum Leadership Density**:
   $$\text{candidate\_share} = \frac{\text{candidate\_count}}{20} \times 100\%$$
6. **Composite Sector Rank Score**:
   $$\text{Score} = 0.5 \times \text{Alpha}_{1M} + 0.5 \times \text{Alpha}_{3M} + 0.2 \times (\text{Sector\_Breadth}_{200} - 50.0)$$

---

### 3. Sector Tearsheet & Rotation Snapshot (`2026-08-28`)

```
==============================================================================
SECTOR ROTATION & RELATIVE STRENGTH TEARSHEET — AS OF 2026-08-28
==============================================================================
Benchmark: NIFTY 500 (Close: ₹24,090.85 | 1M: -0.93% | 3M: +2.59%)
Top 3 Inflowing Leadership: PHARMA, AUTO, METALS
Lagging Sectors:            FMCG, INFRA_MEDIA, REALTY
------------------------------------------------------------------------------
#  SECTOR       1M-RET   1M-ALPHA  3M-ALPHA  BREADTH  RRG   SCORE   PICKS
------------------------------------------------------------------------------
1  PHARMA       +5.9%    +6.8%     +15.8%    84.5%    LEAD  +18.19  3 (15%)
2  AUTO         +5.0%    +5.9%     +12.1%    73.3%    WEAK  +13.68  2 (10%)
3  METALS       +8.2%    +9.1%     -1.5%     75.0%    LEAD  +8.82   1 (5%)
4  FINSERV      +1.8%    +2.7%     +5.3%     63.1%    LEAD  +6.60   2 (10%)
5  CAPGOODS     +3.6%    +4.6%     +5.1%     57.4%    LEAD  +6.34   6 (30%)
6  IT           +1.8%    +2.7%     +4.3%     57.1%    LEAD  +4.96   -
7  CHEMICALS    +1.2%    +2.1%     +3.8%     58.8%    LEAD  +4.72   3 (15%)
8  CONSDUR      +0.9%    +1.9%     +6.8%     50.0%    WEAK  +4.35   1 (5%)
9  ENERGY       +1.7%    +2.6%     +0.9%     52.9%    WEAK  +2.34   -
10 FMCG         +0.5%    +1.4%     +3.4%     46.4%    WEAK  +1.69   -
11 INFRA_MEDIA  +1.2%    +2.1%     -2.2%     48.3%    IMPR  -0.37   2 (10%)
12 REALTY       -1.6%    -0.7%     +2.3%     41.5%    IMPR  -0.92   -
==============================================================================
```

#### Top 20 Candidates Sector Allocation Invariant
- `CAPGOODS`: 6 scrips (`MTARTECH`, `CPPLUS`, `RRKABEL`, `TDPOWERSYS`, `AVALON`, `DIACABS`)
- `PHARMA`: 3 scrips (`CUPID`, `LAURUSLABS`, `SHILPAMED`)
- `CHEMICALS`: 3 scrips (`AETHER`, `GRWRHITECH`, `ACUTAAS`)
- `AUTO`: 2 scrips (`ATHERENERG`, `SANSERA`)
- `FINSERV`: 2 scrips (`FEDERALBNK`, `MCX`)
- `INFRA_MEDIA`: 2 scrips (`STLTECH`, `HFCL`)
- `CONSDUR`: 1 scrip (`SKYGOLD`)
- `METALS`: 1 scrip (`WELCORP`)
- **Total Picks Count**: $6 + 3 + 3 + 2 + 2 + 2 + 1 + 1 = 20$ (100.0% conservation)

---

### 4. Telegram Alert & Character Count Verification

The Telegram alert formatter (`production/telegram_alerts.py`) was enhanced with:
1. Executive Header with Benchmark Regime and 20 EMA comparison.
2. Market Breadth Health table (6 trend and proximity indicators).
3. RRG Relative Rotation Distribution table.
4. **Sector Rotation & Leadership Dynamics table** with top inflowing and lagging sector callouts.
5. Top 20 Momentum Candidates table with prices, 52w high distances, Volar scores, RRG quadrants, and RS-ratios.
6. Target Position Sizing recommendations for ₹10 Lakhs and ₹1 Crore portfolios.
7. Execution rules reminders.

- **Telegram Message Size**: **3,831 characters** (strictly below the 4,096 max character limit).
- **Network Dispatch**: Successfully delivered via `/usr/local/bin/telegram-notify --html`.

---

### 5. Task Completion Status & HALT-12 Readiness

| Task | Description | Status | Verification Detail |
|---|---|---|---|
| **Task 1** | Sector Taxonomy & Mapping Database | **PASS** | 1,039 universe symbols mapped (0 nulls) in `symbol_sector_map.json` |
| **Task 2** | Sector Rotation Engine (`production/sector_rotation.py`) | **PASS** | 5 quantitative metrics, composite ranking, JSON export & console table |
| **Task 3** | Scanner Integration (`production/scanner.py`) | **PASS** | `sector` column in `screener_output_live.csv` (750 rows), terminal summary |
| **Task 4** | Telegram Alert Formatting (`production/telegram_alerts.py`) | **PASS** | `<pre>` Sector Rotation Table, 3,831 / 4,096 chars limit satisfied |
| **Task 5** | End-to-End Verification & Live Dispatch | **PASS** | Scanner executed, dry-run verified, live Telegram alert dispatched |
| **HALT-12** | Standing Gate HALT-12 | **ACTIVE** | Paused for Auditor review and formal ruling |

---

### 6. Verification Artifacts & Deliverables

All deliverables have been generated and mirrored to `/sdcard/Documents/deliverables/`:
- `data/universe/symbol_sector_map.json`
- `deliverables/phase_8/data_csv/sector_rotation_live.json`
- `deliverables/phase_8/data_csv/screener_output_live.csv`
- `deliverables/phase_8/data_csv/market_breadth_live.json`
- `artifacts/sector_rotation_digest.md`
