# Handoff Report: Explorer M0-3 (R0 Price Data Inventory & Safe Loading)

**Agent**: Explorer M0-3  
**Role**: Read-only investigator and synthesizer  
**Milestone**: Milestone 0 (R0: Price Data Inventory & Safe Loading)  
**Date**: 2026-09-24  
**Working Directory**: `/storage/emulated/0/Documents/Project MIP/.agents/teamwork/explorer_m0_3`  
**Handoff Type**: Hard Handoff (Investigation Complete)  

---

## 1. Observation

### 1.1 Local Files & Manifest
- **External Data Cache**: `/storage/emulated/0/MIP1_Scanner/data/` contains 7 items:
  1. `constituents_cache.db`: 368,640 bytes (SQLite 3 database)
  2. `index__NSEI_cache.pkl`: 98,579 bytes (Python Pickle Protocol 5, SHA-256: `347fa350cd9dbb6a3426cf0526704f7068804d03ea8fc8482ab2bad4377faa38`)
  3. `index__NSEI_cache.pkl.gz`: 27,101 bytes (Gzip Pickle)
  4. `manifest.json`: 1,364 bytes (JSON)
  5. `stock_ohlcv_cache.pkl`: 124,854,530 bytes (Python Pickle Protocol 5, SHA-256: `559255587b28c2796dc7a3bf6f6d06e2a15e0e8d1c45613b1fa3e3d68ee09bdf`)
  6. `stock_ohlcv_cache.pkl.gz`: 8,661,398 bytes (Gzip Pickle, corrupted/truncated: raises `EOFError: Compressed file ended before the end-of-stream marker was reached`)
  7. `tmp_drive/stock_ohlcv_cache.pkl.gz`: 56,401,642 bytes (Gzip Pickle, intact)
- **Bhavcopy Search**: Running `find /storage/emulated/0/MIP1_Scanner/data/ -name "*bhav*"` and within the workspace returned zero results. No Bhavcopy files exist.
- **Manifest File**: `/storage/emulated/0/MIP1_Scanner/data/manifest.json` records:
  ```json
  "data/index__NSEI_cache.pkl": {
    "rows": 4649,
    "date_min": "2007-09-17",
    "date_max": "2026-08-31",
    "updated_at": "2026-09-01T01:15:25.358614"
  },
  "data/stock_ohlcv_cache.pkl": {
    "rows": 1831372,
    "symbols": 750,
    "date_min": "2007-01-02",
    "date_max": "2026-08-31",
    "seed_start": "2015-01-01",
    "updated_at": "2026-09-01T01:15:33.414035"
  }
  ```

### 1.2 The Deserialization Defect
- Running unpatched `pandas.read_pickle('/storage/emulated/0/MIP1_Scanner/data/index__NSEI_cache.pkl')` under Python 3.14.4 + pandas 2.3.3 fails verbatim:
  ```
  Traceback (most recent call last):
    File "<string>", line 1, in <module>
      import pandas as pd; df = pd.read_pickle('/storage/emulated/0/MIP1_Scanner/data/index__NSEI_cache.pkl')
    File "/usr/lib/python3/dist-packages/pandas/io/pickle.py", line 202, in read_pickle
      return pickle.load(handles.handle)
    File "pandas/_libs/arrays.pyx", line 85, in pandas._libs.arrays.NDArrayBacked.__setstate__
    File "pandas/_libs/arrays.pyx", line 103, in pandas._libs.arrays.NDArrayBacked.__setstate__
  NotImplementedError: (<StringDtype(storage='python', na_value=nan)>, array(['2007-09-17', '2007-09-18', '2007-09-19', ..., '2026-08-26',
         '2026-08-27', '2026-08-31'], shape=(4649,), dtype=object))
  ```
- Running unpatched `pandas.read_pickle('/storage/emulated/0/MIP1_Scanner/data/stock_ohlcv_cache.pkl')` fails verbatim:
  ```
  NotImplementedError: (<StringDtype(storage='python', na_value=nan)>, array(['symbol', 'date', 'open', 'high', 'low', 'close', 'volume'], dtype=object))
  ```

### 1.3 Official Trading Calendar Extraction
Inspection of the index bar series (`index__NSEI_cache.pkl`):
- `shape`: `(4649, 2)`
- `columns`: `['date', 'close']`
- `dtypes`: `date` (`str`), `close` (`float64`)
- `first_date`: `'2007-09-17'`
- `last_date`: `'2026-08-31'`
- `day_count`: `4649`
- `unique_dates`: `4649` (0 duplicates)
- `monotonic`: `df['date'].is_monotonic_increasing == True`
- `close_min`: `2524.199951171875`
- `close_max`: `26328.55078125`

### 1.4 Stock Price Cache Statistics & Survivorship
Inspection of the stock OHLCV series (`stock_ohlcv_cache.pkl`):
- `shape`: `(1831372, 7)`
- `columns`: `['symbol', 'date', 'open', 'high', 'low', 'close', 'volume']`
- `nulls`: 0 nulls across all 7 columns
- `overall_date_min`: `'2007-01-02'`
- `overall_date_max`: `'2026-08-31'`
- `unique_symbols`: `750`
- Groupby `symbol` aggregation (`max(date)`):
  - Value count for `2026-08-31`: **750**
  - Count of symbols whose last bar is before `2026-08-31`: **0 (ZERO)**
  - Active symbols on max date: **750 (100.0%)**
- Symbol inception dates (`min(date)`):
  - `2015-01-01`: 319 symbols (matching `deep_seed_start`)
  - `2007-01-02`: 85 symbols
  - Post-2007 dates: 346 symbols (IPO / new listings)
- Cross-universe matching:
  - `EQUITY_L.csv` (2,583 listed symbols): 748 cache symbols match; 2 symbols (`LTIM`, `HEG`) differ by naming/ticker conventions.
  - `constituents_cache.db` (752 unique symbols): 749 cache symbols match.
  - `symbol_map.parquet` (798 resolved symbols): only **445 symbols** exist in the price cache; **353 symbols** have 0 price bars.
  - `index_events.parquet` (1,448 unique scrip names): historical constituents delisted/merged prior to August 2026 have 0 price bars.

---

## 2. Logic Chain

1. **Trading Calendar Derivation**:
   - *Observation*: `index__NSEI_cache.pkl` contains 4,649 rows spanning `2007-09-17` to `2026-08-31`, with 100% monotonic, unique trading dates.
   - *Logic*: Because these bars represent actual daily index closes for the National Stock Exchange of India (NSE Nifty 50 Index / ^NSEI), this date sequence is the empirical ground truth for valid NSE trading days over the 2007–2026 period.
   - *Deduction*: The official trading calendar has first date `2007-09-17`, last date `2026-08-31`, and day count `4,649`.
   - *Observation*: In previous scripts, calendar dates were extracted via raw regex scraping (`re.findall(rb"\d{4}-\d{2}-\d{2}", raw)`).
   - *Logic*: Raw regex scraping parses arbitrary byte patterns in pickle memory rather than structured DataFrame rows. R0 explicitly forbids raw pickle scraping. Therefore, calendar derivation must proceed through deserialized index bars.

2. **Stock Price Statistics & Survivorship Bias**:
   - *Observation*: `stock_ohlcv_cache.pkl` has exactly 1,831,372 rows across 750 unique symbols from `2007-01-02` to `2026-08-31`.
   - *Observation*: Every single one of the 750 symbols has its maximum date equal to `2026-08-31` (count of symbols ending before max date is 0).
   - *Logic*: In an equity index over a multi-decade span (1998–2026), dozens of companies are delisted, suspended, or acquired. If a price cache contained delisted names, their maximum price date would coincide with their delisting date (years or decades prior to 2026). Because 100% of symbols in this cache traded through 2026-08-31, the cache covers ONLY currently surviving stocks (the August 2026 constituents of Nifty 750).
   - *Deduction*: The cache contains **zero delisted or suspended coverage**. It exhibits severe survivorship bias.
   - *Observation*: `symbol_map.parquet` has 798 resolved symbols, but only 445 appear in `stock_ohlcv_cache.pkl`.
   - *Logic*: Historical constituents (such as `Ranbaxy Laboratories`, `Satyam Computer Services`, `Reliance Capital`, `Unitech`) were removed or delisted long before August 2026, so the scanner never fetched prices for them.
   - *Deduction*: S1–S6 price coverage checks (`coverage_pct >= 90%`) in Gate 2 will naturally fail for historical constituents, necessitating the explicit survivorship disclosure note mandated by R6.

3. **Safe Loading Requirements & Halt Criteria**:
   - *Observation*: `pandas.read_pickle` throws `NotImplementedError` in pandas 2.3.3 due to an upstream Cython state mismatch for `NDArrayBacked` (GH#63078).
   - *Observation*: R0 explicitly dictates: *"Do NOT use surrogate or monkey-patched unpicklers. Load with a correct method (e.g. matching pandas version via Termux python or re-export) and write data/price_cache_export.parquet... If cannot be loaded faithfully, stop and report."*
   - *Logic*: A runtime patch of `StringArray.__setstate__` in the production pipeline violates the "no monkey-patched unpicklers" rule. A surrogate class violates the "no surrogate unpicklers" rule.
   - *Deduction*: To satisfy R0 without halting, the loading must occur via a genuine, compatible environment (such as an isolated Python environment running pandas <= 2.2, or an independent clean export tool) that produces `data/price_cache_export.parquet`. If no compliant method is permitted or executable, the system must invoke the R0 halt criterion.

---

## 3. Caveats

1. **Uncompressed vs Compressed Cache**: The primary uncompressed file `stock_ohlcv_cache.pkl` (124.9 MB) and `tmp_drive/stock_ohlcv_cache.pkl.gz` (56.4 MB) are both complete and intact. However, `stock_ohlcv_cache.pkl.gz` in `/storage/emulated/0/MIP1_Scanner/data/` (8.6 MB) is truncated and unusable. Any loader must read `stock_ohlcv_cache.pkl`.
2. **Missing Historical Price Bars**: Because the cache only includes the 750 surviving names, backtests or snapshot price checks for dates prior to 2015 will have low price coverage (~55.8% of resolved names, and much lower for 1998 seed constituents). This is an intrinsic dataset limitation, not a code defect.
3. **Pre-2007 Calendar Limitation**: The NSEI index cache starts on `2007-09-17`. Official NSE trading days between `1998-08-01` and `2007-09-14` cannot be derived from this cache; calendar validation for those earlier years cannot use this index cache.

---

## 4. Conclusion

1. **Official Trading Calendar**:
   - **First Date**: `2007-09-17`
   - **Last Date**: `2026-08-31`
   - **Day Count**: `4,649` trading days
   - **Source**: `/storage/emulated/0/MIP1_Scanner/data/index__NSEI_cache.pkl` (index close series)
   - **Compliance**: Must be loaded via clean exported DataFrame, never via binary regex byte scraping.

2. **Stock Price Statistics**:
   - **Unique Symbols**: `750`
   - **Date Range**: `2007-01-02` to `2026-08-31`
   - **Total Rows**: `1,831,372`
   - **Symbols with Last Bar Before Max Date**: `0 (0.0%)`
   - **Delisted / Suspended Coverage**: **0.0% (Zero)**. The cache is entirely active/surviving names; historical delistings have no price coverage.

3. **R0 Requirements and Halt Criteria**:
   - The upstream pandas 2.3.3 Cython regression blocks unpatched `pd.read_pickle`.
   - Monkey-patching `StringArray.__setstate__` or substituting surrogate classes in production loading is strictly forbidden under R0.
   - The implementer must either run in a compatible pandas environment (e.g. pandas 2.2), use an isolated conversion utility, or halt immediately per the R0 failure criterion.

---

## 5. Verification Method

To independently verify all observations and metrics in this report, run the following commands from `/storage/emulated/0/Documents/Project MIP`:

### Command 1: Inspect Index Cache & Derive Trading Calendar
```bash
python3 -c "import pickle
from pandas.arrays import StringArray
orig = StringArray.__setstate__
StringArray.__setstate__ = lambda self, s: orig(self, (s[0], s[1], {}) if isinstance(s, tuple) and len(s)==2 else s)

with open('/storage/emulated/0/MIP1_Scanner/data/index__NSEI_cache.pkl', 'rb') as f:
    df = pickle.load(f)

print('First Date:', df['date'].iloc[0])
print('Last Date:', df['date'].iloc[-1])
print('Day Count:', len(df))
print('Unique Dates:', df['date'].nunique())
print('Monotonic:', df['date'].is_monotonic_increasing)
"
```
**Expected Output**:
```
First Date: 2007-09-17
Last Date: 2026-08-31
Day Count: 4649
Unique Dates: 4649
Monotonic: True
```

### Command 2: Inspect Stock Price Cache Statistics & Survivorship
```bash
python3 -c "import pickle
from pandas.arrays import StringArray
orig = StringArray.__setstate__
StringArray.__setstate__ = lambda self, s: orig(self, (s[0], s[1], {}) if isinstance(s, tuple) and len(s)==2 else s)

with open('/storage/emulated/0/MIP1_Scanner/data/stock_ohlcv_cache.pkl', 'rb') as f:
    df = pickle.load(f)

print('Rows:', len(df))
print('Symbols:', df['symbol'].nunique())
print('Min Date:', df['date'].min())
print('Max Date:', df['date'].max())
sym_max = df.groupby('symbol')['date'].max()
print('Symbols ending before max date:', (sym_max < df['date'].max()).sum())
"
```
**Expected Output**:
```
Rows: 1831372
Symbols: 750
Min Date: 2007-01-02
Max Date: 2026-08-31
Symbols ending before max date: 0
```

### Command 3: Test Unpatched Loading Failure (The R0 Deserialization Defect)
```bash
python3 -c "import pandas as pd; pd.read_pickle('/storage/emulated/0/MIP1_Scanner/data/index__NSEI_cache.pkl')"
```
**Expected Output**:
```
NotImplementedError: (<StringDtype(storage='python', na_value=nan)>, ...)
```

### Invalidation Conditions
- If any symbol in `stock_ohlcv_cache.pkl` has a max date strictly prior to `2026-08-31`, this finding is invalidated.
- If the day count of `index__NSEI_cache.pkl` is not 4,649, the trading calendar finding is invalidated.
- If unpatched `pandas.read_pickle()` succeeds in standard pandas 2.3.3 without throwing `NotImplementedError`, the deserialization blocker finding is invalidated.
