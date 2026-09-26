# PHASE 5.5 GATES C & D AUDITOR RULING

Status: ACCEPT

## Files inspected

- `data/corrections.parquet` | bytes: 9231 | `0edec75a63f4eadd271901d1023b34ef4f3ee32144669d497b0f6e991d06587e`
- `data/index_events.parquet` | bytes: 65497 | `7a15cfae88c53c6a4d79c5fe28dc3642a999728855d29329a892e11261d2d54a`
- `data/symbol_map.parquet` | bytes: 91649 | `ce9cc73605fcf8cd8b60cd384187dafc9ea9c74235e7cea7f317a2cb851b5154`
- `deliverables/gate_cd/DIGEST.md` | bytes: 11323 | `03af33fe3126bf92d9daf0802b1462dec2ad7702e7fd5bf1842faaabb4ed1486`
- `deliverables/gate_cd/EVIDENCE_INDEX.tsv` | bytes: 3869 | `173992fffbedb0ec14d917a4fa541c68f2f3aaa051fdead81ab3fb424c623504`
- `deliverables/gate_cd/SHA256SUMS.txt` | bytes: 1950 | `137d8f96d4eda49df8c322eba363ffa8a9367b9a1d40e8c59d8581fb8e91276d`
- `deliverables/gate_cd/task_list.md` | bytes: 2119 | `3b7db6776946ebdb1080cec5fc0c517c5177fea06cd9bec120c7f4d97bfbedca`
- `deliverables/gate_cd/data_csv/backtest_comparison_metrics.csv` | bytes: 860 | `eff09b6e64a286b5cd73e653093cdea78897aee4e437501649162bf3ccf5dc38`
- `deliverables/gate_cd/data_csv/gate_c_continuity_summary.csv` | bytes: 629 | `fc94be7d4af57fd8fd6a597edaf517b05e5a3727eee6232b6b1206e7bf1dd494`
- `deliverables/gate_cd/data_csv/holdings_attribution.csv` | bytes: 13421 | `4eae12e75a39d3c9e33348b5fdd4619767d157eb99e5a95485604ccaa0e6f470`
- `deliverables/gate_cd/data_csv/price_gaps.csv` | bytes: 476 | `7de7da3d305e22693d3ffd40a52a1f7959c5777343657e60914b8bb011da8388`
- `deliverables/gate_cd/data_csv/reconstructed_turnover.csv` | bytes: 313 | `3771f4a6e6c9268db1a55aeb0755a94cd15a05bd676afc0273e0d7039261ce50`
- `deliverables/gate_cd/raw/gate_c_continuity.txt` | bytes: 6647 | `1d3759275223c917a52bf1604f37dc27a11b0bb7aca6831723701d34b5209584`
- `deliverables/gate_cd/raw/gate_d_backtest_run_a.txt` | bytes: 4727 | `658e920cf4f269ff8ff084a7ea5ac84f615f407d4d67d768e6384c781c8f345b`
- `deliverables/gate_cd/raw/gate_d_backtest_run_b.txt` | bytes: 4723 | `501c998f3d073c3ab4201e8d34329af3cf028ca30a747e7c39a6fd44e31ed886`
- `deliverables/gate_cd/raw/gate_d_reconstruct.txt` | bytes: 2519 | `ed051578822a61b00aeb65f9bd5e45c6ebc05fedc413a3d63d9ffb236eff0f87`
- `deliverables/gate_cd/scripts/gate_c_continuity.py` | bytes: 11027 | `d02b9d23aaef9d240db321b098882a786bbe122d4898cf77a5d59d67228211fa`
- `deliverables/gate_cd/scripts/gate_d_backtest_runner.py` | bytes: 23763 | `95ae3e56811f98c16f8270b88fe6fa9bff0b57130917a0729d5b7241032f522b`
- `deliverables/gate_cd/scripts/gate_d_reconstruct.py` | bytes: 11137 | `9d0b5666ee4fccb48f0d67b3f5ca27f5c87cf9c304aaf5954a2b2de558b49014`
- `deliverables/gate_cd/scripts/generate_evidence_index.py` | bytes: 4319 | `6ebbf2cbf08f5355abde2d78d9e2d6b78f8c7d94cc7c0cbdd020f7cf8eea3203`

---

## Claims verified

### Claim 1: Gate C — Multi-Index Continuity Audit across 7 Broad Market Indices
- **Evidence**: `deliverables/gate_cd/data_csv/gate_c_continuity_summary.csv`, `deliverables/gate_cd/raw/gate_c_continuity.txt`
- **Auditor Recomputation**:
  - Full history forward replay executed across all 7 broad market indices in `data/index_events.parquet`.
  - **NIFTY500**: Exactly **0 orphan OUTs**, **0 duplicate INs**, **501 final active constituents**, and **0 blocked events** across its entire 22-year event log (1998-08-01 to 2020-09-14). Continuity status: **PASS**.
  - **Other 6 Indices (`NIFTY50`, `NIFTYNEXT50`, `NIFTY100`, `NIFTY200`, `NIFTYMIDCAP100`, `NIFTYSMALLCAP100`)**:
    - Confirmed that the event log sheets for these six indices only record rebalance changes and lack the initial constituent seed batch (present only in NIFTY500 with 500 INs on 1998-08-01).
    - Consequently, the observed orphan OUT counts (51, 75, 82, 111, 105, 102) strictly reflect the unseeded removals of initial index constituents.
    - Sheet-level event anomalies correctly isolated: SAIL trailing period in NIFTYNEXT50 (`Steel Authority of India Ltd.` vs `Steel Authority of India Ltd`), and Indiabulls Real Estate duplicate IN in NIFTYMIDCAP100.
    - Zero blocked events observed for approved scrips across all 7 indices.

### Claim 2: Gate D — Point-in-Time Universe Reconstruction & Turnover Audit
- **Evidence**: `deliverables/gate_cd/data_csv/reconstructed_turnover.csv`, `deliverables/gate_cd/raw/gate_d_reconstruct.txt`
- **Auditor Recomputation**:
  - Window Start (`2016-01-04`): Exactly **500** constituents (437 unique mapped symbols).
  - Covered End (`2020-09-14`): Exactly **501** constituents (480 unique mapped symbols).
  - Turnover Dynamics: 163 start constituents removed by end; 164 constituents added since start; 337 constituents retained throughout. Gross constituent turnover: **32.67%** across the 4.7-year backtest window.

### Claim 3: Gate D — Bhavcopy Price Coverage & Price Gap Audit
- **Evidence**: `deliverables/gate_cd/data_csv/price_gaps.csv`, `deliverables/gate_cd/raw/gate_d_reconstruct.txt`
- **Auditor Recomputation**:
  - Daily Bhavcopy bars audited for all dynamic constituents across all 57 monthly snapshots.
  - Across 1,154 trading days and 57 snapshots, exactly 5 price gap instances (> 30% missing bars in holding month) were identified:
    * Snapshot #8 (2016-08-01): `SITICABLE` (11 missing days, 52.38%)
    * Snapshot #15 (2017-03-01): `SBBJ` (12 missing days, 54.55%)
    * Snapshot #29 (2018-05-02): `PRISMCEM` (20 missing days, 90.91%)
    * Snapshot #42 (2019-06-03): `MERCK` (14 missing days, 73.68%)
    * Snapshot #56 (2020-08-03): `NIITTECH` (8 missing days, 38.10%)
  - Maximum symbols with > 30% missing bars in any snapshot was **1** (mandated failure threshold: $> 20$). Exactly **0 snapshots** breached the threshold. Price coverage audit: **PASS**.

### Claim 4: Gate D — Comparative Baseline Backtest Re-Run & Survivorship Bias Quantification
- **Evidence**: `deliverables/gate_cd/data_csv/backtest_comparison_metrics.csv`, `deliverables/gate_cd/raw/gate_d_backtest_run_a.txt`, `deliverables/gate_cd/raw/gate_d_backtest_run_b.txt`
- **Auditor Recomputation**:
  - Both backtests executed over identical clamped window (`2016-01-04` to `2020-09-14`, 1,154 trading days, 4.6954 years, identical NSE trading calendar) under strictly frozen strategy rules (R2, R3, R5, R6, R7, R8, R9, $N=20$, equal entry weighting, next-day open execution, monthly rebalancing).
  - **Run (a) Survivor-Biased Baseline (Fixed constituents as of 2020-09)**:
    * Initial Capital: Rs. 10,000,000.00
    * Final Portfolio Value: Rs. 20,585,753.10
    * Net Profit: Rs. 10,585,753.10
    * CAGR: **16.62%** (hand arithmetic: $(20585753.1 / 10000000.0)^{1 / 4.6954} - 1 = 16.62\%$)
    * Max Drawdown: 44.36%
    * Sharpe Ratio: 0.80
    * Total Trades: 300 (280 closed, 20 open)
  - **Run (b) Point-in-Time Dynamic Membership (Reconstructed PIT universe)**:
    * Initial Capital: Rs. 10,000,000.00
    * Final Portfolio Value: Rs. 17,694,873.90
    * Net Profit: Rs. 7,694,873.90
    * CAGR: **12.92%** (hand arithmetic: $(17694873.9 / 10000000.0)^{1 / 4.6954} - 1 = 12.92\%$)
    * Max Drawdown: 48.03%
    * Sharpe Ratio: 0.68
    * Total Trades: 309 (289 closed, 20 open)
  - **Performance Delta (Survivorship Bias Premium)**:
    * CAGR Delta: **-3.70 percentage points** (16.62% $\to$ 12.92%)
    * Net Profit Delta: **-Rs. 2,890,879.20** (-27.3% reduction in profit when eliminating survivorship bias)
    * Max Drawdown Delta: **+3.67 percentage points** (44.36% $\to$ 48.03%, reflecting real historical drawdown during market corrections)

### Claim 5: Standing Rule R-3 Accounting Identity Invariant
- **Evidence**: `deliverables/gate_cd/raw/gate_d_backtest_run_a.txt`, `deliverables/gate_cd/raw/gate_d_backtest_run_b.txt`
- **Auditor Recomputation**:
  - Run (a): $\text{Rs. } 10,000,000.00 + \text{Rs. } 4,692,068.00 - 0.00 + 0.00 + \text{Rs. } 5,893,685.10 == \text{Rs. } 20,585,753.10$. Residual: **-0.00000000** (exact 0.00).
  - Run (b): $\text{Rs. } 10,000,000.00 + \text{Rs. } 2,831,528.35 - 0.00 + 0.00 + \text{Rs. } 4,863,345.55 == \text{Rs. } 17,694,873.90$. Residual: **-0.00000000** (exact 0.00).
  - **Rule R-3 is strictly satisfied on both runs**.

### Claim 6: Standing Rule R-6 Reproducibility & Standing Rule R-5 Disclosure
- **Evidence**: `deliverables/gate_cd/raw/gate_d_backtest_run_a.txt`, `deliverables/gate_cd/raw/gate_d_backtest_run_b.txt`, `deliverables/gate_cd/data_csv/backtest_comparison_metrics.csv`
- **Auditor Recomputation**:
  - Both Run (a) and Run (b) were executed twice (Pass 1 vs Pass 2); output logs diffed with 0 byte differences (**100% byte-identical**).
  - Standing Rule R-5 coverage line explicitly disclosed: `"Point-in-time dynamic membership (median joint coverage 87.03%)"`.

### Claim 7: Holdings Attribution & Performance Divergence Root Cause
- **Evidence**: `deliverables/gate_cd/data_csv/holdings_attribution.csv`
- **Auditor Recomputation**:
  - 233 unique symbols traded across the backtest window:
    * 17 symbols held in Run (a) only: e.g. `VENKEYS` (+Rs. 1,164,126.00 profit in Run a, ineligible in Run b, driving 40.3% of the entire net profit divergence), `HSCL` (+Rs. 387,816.80).
    * 34 symbols held in Run (b) only: e.g. `PCJEWELLER` (-Rs. 292,600.00 loss in Run b, completely omitted in Run a due to survivor foresight), `WELCORP`, `TATAGLOBAL`, `ADANIENT`.
    * 182 symbols held in both runs: Divergence driven by entry rank differences, cash availability, and sizing.
  - Total attribution realized PnL delta (-Rs. 2,890,879.21) matches the macro portfolio net profit delta to within 1 cent.

### Claim 8: Standing Gate HALT-4
- **Evidence**: `deliverables/gate_cd/task_list.md`
- **Auditor Verification**: Standing gate `HALT-4: Stop and wait for auditor review of Gates C & D deliverables` was left UNTICKED and OPEN awaiting this formal ruling.

---

## Claims rejected

None. All claims made in `deliverables/gate_cd/DIGEST.md` are supported by verified on-disk raw artifacts and confirmed by independent recomputation in PRoot Ubuntu system Python (`/usr/bin/python3`).

---

## Claims requiring user attention

None. The comparative backtest successfully isolates the survivorship bias premium (+3.70% CAGR in survivor baseline vs realistic 12.92% CAGR in point-in-time reconstruction) while strictly honoring accounting identity Rule R-3 (residual 0.00) and reproducibility Rule R-6.

---

## Conditions (if ACCEPT_WITH_CONDITIONS)

N/A — Status is **ACCEPT**.

---

## Next phase recommendation

Standing gate **HALT-4 is now CLEARED and CLOSED**.

The builder is directed to proceed immediately to **Phase 5.5 Gates E & F: Round-Trip Snapshot Replay & Reproducibility/Truncation Audit**.

The builder prompt has been placed in the same directory:
- [NEXT_TASK.md](file:///storage/emulated/0/Documents/Project%20MIP/deliverables/gate_cd/NEXT_TASK.md)
