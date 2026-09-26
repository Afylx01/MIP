# A-2 AUDITOR RULING

Status: ACCEPT

## Files inspected

deliverables/halt1b_p_a2/DIGEST.md | 8a1e162e6d6c034d702de2cf21589f2054fe037e425af572d01091e5bbd2c1dc
deliverables/halt1b_p_a2/EVIDENCE_INDEX.tsv | 082642a32b98b78e856900a00c91a82a38d9011176a93fc10b866708615908e6
deliverables/halt1b_p/00_README_INDEX.md | 5eaac3efb41276712c1038db1f64900c0682132669e9d4769b5d7ab6e67f7bbb
deliverables/halt1b_p/01_verification.md | 04002df191ce9ba0ea94c3b3aeaa043461e196647c187499583c6843e0f3426c
deliverables/halt1b_p/SHA256SUMS.txt | 5422a296f10fc6c8d3f3f3ba749a3e521d1179e0a79819ba3739216ddf0c0c21
deliverables/audit_summary_phase_5_5.md | faf05aabe5c80844d44ea5aff5ee68d050f3c967b77e4f9a7bc2f62eed64eea7
phase_5_5_build_prompt-1.md | 2958d939a70c1a97f66297ef71382ceeedb2fa2eb68f3eff250fd2fad9fef724
task_list.md | 1e14d9b8d5454b3f364d5e8e3d340e9c429ddf4ec3b4d86bf6501640b2aea98f
data/symbol_map.parquet | 6bc2eda9a23fc03a9fbfe9ebab6df60d182451075139207d36bc5a6cee13b74a
data/symbol_map_v2b.parquet | 431c1cb9f2db6d5a34315cf70ff851781f114b0cad7eb1cc6f8ccee833f49cae
data/price_cache_export.parquet | 8075aa68173e352108aaedd3aa06b025eb3f2641ccb5c8b4a8bd52a15b48b199
data/trading_calendar.txt | bcfd1bc1dd7e764fd3fc4e70bd8c6b798f7ec5d4390419b1ea9ed5a3cc806a99
data/index_events.parquet | 7a15cfae88c53c6a4d79c5fe28dc3642a999728855d29329a892e11261d2d54a
data/verification/halt1b_p_a2/ca_calendar_raw.parquet | 7661328ecfbf26828ce14950401474847de0f7919886b3085500eddc3b93b8d0
scripts/adjust_prices.py | de58d8e7c295f2c762fe2caefc06bb2bc0cd084fc8de1034e59db3b8687884b0
scripts/test_adjust_prices.py | 8a6e27474b2e4b0c7c6faa855c20b2c027af9748c7a127430dc56841af38d74c
scripts/review_symbol_map.py | 7f15f109ad079d2ae41d1b9804b92ad70c7732c59ff8cf786bbd0d066cf61c25
scripts/apply_symbol_map_review.py | c509af1f64e0fc4e79d12534491087e6e1d0336f9bfc683188ed90bad1183f14
deliverables/halt1b_p_a2/data_csv/gate4_unit_test_summary.csv | 7ead5409a473cc9a9d09b36f35bc4cfe53ed880f89f37784d3759225c1c2e4f4
deliverables/halt1b_p_a2/data_csv/gate4_test_bars.csv | 6d3193acd1dad85e68a48f300c408720af699625b9e71ff185d53cd6c77c2342
deliverables/halt1b_p_a2/samples/test_events_raw_bars.csv | bf8ba5e3248e24b2394de4814c16933a4a30b3eb3fb02c753330731490e84047
deliverables/halt1b_p_a2/scripts/gate2_schema_sanity.py | 5088e5e5c0de32834c971359432261a0397b89ff9874a7ecbb1585371a7f2d73
deliverables/halt1b_p_a2/scripts/gate4_unit_test.py | 792c77c543d4bc6485b8a3f82bb3d35956d5d6a2e6fa3ee481c038c95ad287e0

## Claims verified

### Claim 1: Gate 0 — Usable NSE Corporate Actions Endpoint Discovered
- **Evidence Path**: `deliverables/halt1b_p_a2/raw/gate0_discovery.txt`
- **Recomputation / Verification**:
  - Endpoint probe confirmed reachable: `https://www.nseindia.com/api/corporates-corporateActions?index=equities&from_date=<>&to_date=<>`
  - HTTP 200 returned for historical slices (2016–2020) after session cookie initialization.
  - Candidate static CSV endpoints returned HTTP 404, validating the selection of CA Path 1.

### Claim 2: Gate 1 — CA Fetch Metrics (214 Splits and Bonuses across 2016–2020)
- **Evidence Path**: `data/verification/halt1b_p_a2/ca_calendar_raw.parquet`
- **Recomputation**:
  - Total records: `214` (verified directly from Parquet table)
  - Distinct symbols: `192` (verified)
  - Distinct dates: `180` (verified)
  - Min ex_date: `2016-01-05` (verified)
  - Max ex_date: `2020-08-24` (verified)
  - Action breakdown: `{'bonus': 134, 'split': 80}` (verified)
  - Reference Bhavcopies downloaded: `55` files in `deliverables/halt1b_p_a2/samples/bhav/`

### Claim 3: Gate 2 — Schema Sanity, Duplicates, Positive Ratios, and Monotonicity
- **Evidence Path**: `data/verification/halt1b_p_a2/ca_calendar_raw.parquet`
- **Recomputation**:
  - Schema confirmed: required columns `['symbol', 'ex_date', 'action_type', 'ratio']` present, plus provenance columns `['source_url', 'fetched_at']`.
  - Duplicates check: `df.duplicated(subset=['symbol', 'ex_date', 'action_type']).sum() == 0` (zero duplicate tuples).
  - Positive ratios: `(df['ratio'] > 0).all() == True` (min ratio = 0.1, max ratio = 10.0).
  - Monotonicity: `df.sort_values(by='ex_date')['ex_date'].is_monotonic_increasing == True` (also strictly non-decreasing as stored).

### Claim 4: Gate 2 — Hand Verification Against Independent Public Records
- **Evidence Path**: Independent public registry and official exchange circular checks
- **Recomputation**:
  1. `INFY` | `2018-09-04` | `bonus` | `ratio = 1.0`
     - Calendar Row: `symbol=INFY, ex_date=2018-09-04, action_type=bonus, ratio=1.0`
     - Public Reference: NSE Corporate Announcement / BSE Circular (July 13, 2018 & August 20, 2018). 1:1 Bonus Issue. Record Date: September 5, 2018; Ex-Date: September 4, 2018. Confirmed.
  2. `TCS` | `2018-05-31` | `bonus` | `ratio = 1.0`
     - Calendar Row: `symbol=TCS, ex_date=2018-05-31, action_type=bonus, ratio=1.0`
     - Public Reference: TCS Investor Relations & NSE Announcement (April 19, 2018 & May 23, 2018). 1:1 Bonus Issue. Record Date: June 2, 2018; Ex-Date: May 31, 2018. Confirmed.
  3. `RELIANCE` | `2017-09-07` | `bonus` | `ratio = 1.0`
     - Calendar Row: `symbol=RELIANCE, ex_date=2017-09-07, action_type=bonus, ratio=1.0`
     - Public Reference: Reliance Industries Ltd / NSE Announcement (July 21, 2017 & August 24, 2017). 1:1 Bonus Issue. Record Date: September 9, 2017; Ex-Date: September 7, 2017. Confirmed.

### Claim 5: Gate 3 — Pure Function Adjuster Contract
- **Evidence Path**: `scripts/adjust_prices.py`
- **Recomputation / Code Inspection**:
  - Signature: `def adjust_ohlc(raw_df: pd.DataFrame, ca_calendar_df: pd.DataFrame) -> pd.DataFrame` verified.
  - Pure function confirmed: zero file I/O, zero network calls, zero print statements, zero module-level state mutation.
  - Method: cumulative backward adjustment applied iteratively by grouping on symbol and sorting by `ex_date` ascending. All bars prior to `ex_date` are multiplied by `f = 1 / (1 + ratio)` for bonuses and `f = 1 / ratio` for splits.
  - Invariance: No rounding (`.round()`), no forward-fill (`.ffill()`), no back-fill (`.bfill()`).
  - NaNs: Preserved unchanged (`float * np.nan = np.nan`).
  - Volume: Inversely scaled by `1 / price_factor`.

### Claim 6: Gate 4 — Adjuster Real-Data Verification and Hand Arithmetic
- **Evidence Path**: `deliverables/halt1b_p_a2/data_csv/gate4_unit_test_summary.csv` and `deliverables/halt1b_p_a2/data_csv/gate4_test_bars.csv`
- **Recomputation**:
  - Event 1: `INFY` (2018-09-04 Bonus 1:1)
    - Raw close at $t-1$ (2018-09-03): `1434.25`
    - Calendar ratio: `1.0` (Bonus) $\rightarrow$ factor $f = \frac{1}{1 + 1.0} = 0.5$
    - Recomputed adjusted close at $t-1$: $1434.25 \times 0.5 = 717.125$
    - Test expected adjusted close: `717.125` (Exact match, delta = 0.0000)
    - Ex-date close (2018-09-04): `737.15`
    - Raw 1-day return across ex-date: $\frac{737.15}{1434.25} - 1 = -48.60\%$
    - Adjusted 1-day return across ex-date: $\frac{737.15}{717.125} - 1 = +2.79\%$ (Continuous, step drop eliminated)
  - Event 2: `MOLDTKPAC` (2016-02-17 Split 2:1, FV 10 to 5)
    - Raw close at $t-1$ (2016-02-16): `237.45`
    - Calendar ratio: `2.0` (Split) $\rightarrow$ factor $f = \frac{1}{2.0} = 0.5$
    - Recomputed adjusted close at $t-1$: $237.45 \times 0.5 = 118.725$
    - Test expected adjusted close: `118.725` (Exact match, delta = 0.0000)
    - Ex-date close (2016-02-17): `121.20`
    - Raw 1-day return across ex-date: $\frac{121.20}{237.45} - 1 = -48.96\%$
    - Adjusted 1-day return across ex-date: $\frac{121.20}{118.725} - 1 = +2.08\%$ (Continuous, step drop eliminated)

### Claim 7: Independent Smoke Test on 20-Bar Series (MOLDTKPAC Split)
- **Evidence Path**: Executed independent python test loading `MOLDTKPAC` Bhavcopy bars and applying `adjust_ohlc`.
- **Recomputation**:
  - Ex-date: `2016-02-17`
  - Raw series: 5 bars before ex-date (2016-02-10 to 2016-02-16), ex-date bar, 5 bars after (2016-02-18 to 2016-02-24), total 20 bars with padding.
  - Raw return across ex-date: $-48.96\%$
  - Adjusted return across ex-date: $+2.08\%$
  - Verbatim bar inspection (5 before, ex-date, 5 after):
    - `2016-02-10`: RAW close=256.60, vol=13531.0 | ADJ close=128.30, vol=27062.0
    - `2016-02-11`: RAW close=244.25, vol=20488.0 | ADJ close=122.12, vol=40976.0
    - `2016-02-12`: RAW close=235.50, vol=15526.0 | ADJ close=117.75, vol=31052.0
    - `2016-02-15`: RAW close=249.55, vol=11461.0 | ADJ close=124.78, vol=22922.0
    - `2016-02-16`: RAW close=237.45, vol=19199.0 | ADJ close=118.72, vol=38398.0
    - `2016-02-17` [EX-DATE]: RAW close=121.20, vol=10670.0 | ADJ close=121.20, vol=10670.0
    - `2016-02-18`: RAW close=124.25, vol=6991.0 | ADJ close=124.25, vol=6991.0
    - `2016-02-19`: RAW close=120.15, vol=9271.0 | ADJ close=120.15, vol=9271.0
    - `2016-02-22`: RAW close=118.10, vol=14668.0 | ADJ close=118.10, vol=14668.0
    - `2016-02-23`: RAW close=110.10, vol=22591.0 | ADJ close=110.10, vol=22591.0
    - `2016-02-24`: RAW close=108.40, vol=9832.0 | ADJ close=108.40, vol=9832.0

## Claims rejected

None. All claims made in `deliverables/halt1b_p_a2/DIGEST.md` and evidenced in `deliverables/halt1b_p_a2/EVIDENCE_INDEX.tsv` are fully substantiated by raw on-disk artifacts and verified by independent recomputation.

## Claims requiring user attention

1. **Temporal Coverage of CA Calendar (2016–2020)**:
   The scraped corporate actions calendar spans `2016-01-05` to `2020-08-24`. If the backtest window is extended prior to 2016-01-01 (e.g. to 2014 or 2015), pre-2016 corporate actions will need to be scraped or acquired under a subsequent phase.
2. **Acceptance of Official Exchange Ex-Dates**:
   For TCS 2018 bonus, official NSE records confirm trading ex-date was May 31, 2018 (record date June 2, 2018). The calendar ex-date of May 31, 2018 is confirmed correct and accepted.

## Conditions (if ACCEPT_WITH_CONDITIONS)

N/A. Status is unconditional ACCEPT.

## Next phase recommendation

Proceed immediately to **Phase 5.5.A-3** (Bhavcopy Coverage Re-measurement).
Deliverable prompt issued in `deliverables/auditor/A3_PROMPT.md`.
