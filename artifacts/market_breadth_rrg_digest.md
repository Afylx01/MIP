# Directive DIR-PROD-BREADTH-RRG-01: Market Breadth & RRG Automation Digest

**Document**: `deliverables/auditor/DIGEST_BREADTH_RRG.md` / Artifact Digest  
**Date**: September 26, 2026  
**Auditor**: Lead Quantitative Architect & Auditor  
**Builder**: Antigravity Quantitative Engineering Agent  
**Directive**: `DIR-PROD-BREADTH-RRG-01`  
**Standing Gate**: **HALT-11** (Active — Paused for Auditor Review)  

---

## 1. Executive Summary

In response to directive `deliverables/auditor/MARKET_BREADTH_RRG_DIRECTIVE.md`, the Builder Agent has upgraded the production momentum scanner suite (`production/scanner.py`, `production/breadth.py`, and `production/telegram_alerts.py`). Every scan run now automatically computes point-in-time **Market Breadth** across the NIFTY 500 universe and evaluates Julius de Kempenaer **Relative Rotation Graph (RRG)** analytics, incorporating both into the institutional Telegram execution dispatch.

```
                         EXECUTION & VERIFICATION SUMMARY
┌───────────────────────────────────────────────┬─────────────────────────────────────────────────────────┬──────────────┐
│ Task / Component                              │ Deliverable Asset / Command                             │ Status       │
├───────────────────────────────────────────────┼─────────────────────────────────────────────────────────┼──────────────┤
│ Task 1: Market Breadth Engine                 │ production/breadth.py                                   │ COMPLETE     │
│ Task 1b: Live Breadth Export                  │ deliverables/phase_8/data_csv/market_breadth_live.json  │ COMPLETE     │
│ Task 2: Scanner RRG & Breadth Refactor        │ production/scanner.py -> screener_output_live.csv        │ COMPLETE     │
│ Task 3: Upgraded Telegram Formatter           │ production/telegram_alerts.py                           │ COMPLETE     │
│ Task 4: End-to-End Test & Live Dispatch       │ Dry-run PASS (3,217 chars) | Telegram Msg ID: 174       │ COMPLETE     │
├───────────────────────────────────────────────┼─────────────────────────────────────────────────────────┼──────────────┤
│ Standing Gate HALT-11                         │ Final Auditor Review & Production Sign-Off              │ OPEN/HALTED  │
└───────────────────────────────────────────────┴─────────────────────────────────────────────────────────┴──────────────┘
```

---

## 2. Empirical Verification Readings (As of 2026-08-28)

### A. Market Breadth Health
Evaluated across **750 active universe scrips**:
- **Trend Participation Breadth**:
  - `% Above 200 EMA`: **59.07%** (443 / 750) — Status: `🟡 NEUTRAL`
  - `% Above 50 EMA`: **52.00%** (390 / 750) — Status: `🟡 NEUTRAL`
  - `% Above 20 EMA`: **45.47%** (341 / 750) — Status: `🔴 DEFENSIVE`
- **High Proximity & Leadership**:
  - `% Within 20% of 52w High`: **57.20%** (429 / 750) — Status: `🟢 EXPANDING`
  - `% Within 5% of 52w High`: **15.20%** (114 / 750) — Status: `🟢 LEADERSHIP`
  - `New 52-Week Highs`: **16 scrips**
  - `New 52-Week Lows`: **16 scrips**
  - `Net Highs - Lows`: **+0** — Status: `🟡 BALANCED`
- **Breadth Regime Classification**:
  - **Result**: `🟡 SELECTIVE / NEUTRAL`
  - **Rationale**: `40.0% <= pct_above_200_ema (59.07%) < 60.0%`. Leadership is selective and concentrated; risk-adjusted factor filtering (Volar) is essential.

### B. JdK Relative Rotation Graph (RRG) Universe Distribution
- **Leading** ($\text{RS-Ratio} \ge 100$, $\text{RS-Momentum} \ge 100$): **217 scrips (28.93%)** — Bias: `🟢 OUTPERFORM`
- **Improving** ($\text{RS-Ratio} < 100$, $\text{RS-Momentum} \ge 100$): **191 scrips (25.47%)** — Bias: `🟢 ACCELERATING`
- **Weakening** ($\text{RS-Ratio} \ge 100$, $\text{RS-Momentum} < 100$): **170 scrips (22.67%)** — Bias: `🟡 DECELERATING`
- **Lagging** ($\text{RS-Ratio} < 100$, $\text{RS-Momentum} < 100$): **172 scrips (22.93%)** — Bias: `🔴 UNDERPERFORM`

---

## 3. Top 20 Candidates Table Sample (With RRG Analytics)

```
#  SYMBOL     PRICE    52wH%   VOLAR  RRG  RS-RAT
-------------------------------------------------
1  CUPID      ₹282.3   -5.6%   12.71  WEAK 121.7 
2  STLTECH    ₹723.8   -0.7%   7.70   LEAD 122.5 
3  MTARTECH   ₹6997.0  -19.7%  6.25   LEAD 103.5 
4  ATHERENERG ₹1616.3  -0.8%   5.54   LEAD 125.6 
5  SANSERA    ₹3859.0  -4.5%   5.21   WEAK 112.5 
6  HFCL       ₹251.5   -1.4%   5.14   LEAD 117.5 
7  WELCORP    ₹2373.8  -2.9%   4.41   LEAD 137.0 
8  LAURUSLABS ₹1938.5  0.0%    4.27   LEAD 116.4 
9  CPPLUS     ₹3576.6  -12.6%  4.13   LEAD 100.9 
10 RRKABEL    ₹2905.2  -2.6%   3.89   LEAD 114.2 
11 TDPOWERSYS ₹752.7   -5.8%   3.84   WEAK 120.2 
12 SKYGOLD    ₹811.4   -6.6%   3.44   WEAK 122.4 
13 AETHER     ₹1696.8  -1.2%   3.39   LEAD 114.1 
14 FEDERALBNK ₹344.2   -7.1%   3.12   WEAK 100.7 
15 AVALON     ₹2231.7  -5.1%   3.12   LEAD 120.8 
16 GRWRHITECH ₹7224.5  -9.6%   3.10   LEAD 103.7 
17 MCX        ₹3332.0  -4.0%   3.09   LEAD 117.0 
18 SHILPAMED  ₹903.8   -1.6%   3.06   LEAD 133.1 
19 DIACABS    ₹349.4   -7.8%   3.04   WEAK 122.6 
20 ACUTAAS    ₹3281.6  -12.3%  3.03   IMPR 98.0  
```

---

## 4. Telegram Notification Confirmation

- **Dry-run character count**: 3,217 characters (strictly under Telegram's 4,096 limit).
- **Live Dispatch**: Dispatched to configured bot via `/usr/local/bin/telegram-notify --html`.
- **Telegram Confirmation**: `Message ID: 174` (HTTP 200, sent successfully).

---

## 5. Standing Gate HALT-11

In accordance with Directive `DIR-PROD-BREADTH-RRG-01`, execution is halted at **Standing Gate HALT-11**:
- Master universe data files have remained strictly unaltered.
- Generated assets:
  - `production/breadth.py`
  - `deliverables/phase_8/data_csv/market_breadth_live.json`
  - `deliverables/phase_8/data_csv/screener_output_live.csv`
  - `production/scanner.py`
  - `production/telegram_alerts.py`
- `task_list.md` records:
  ```markdown
  - [ ] **Standing Gate HALT-11: Final Auditor Review on Market Breadth & RRG Alert Suite (UNTICKED, OPEN)**
  ```

Awaiting Lead Quantitative Architect & Auditor inspection and review.
