# Comprehensive Data and Price Cache Survey Report (Phase 5.5 Gate 2b)

**Date**: 2026-09-24  
**Investigator**: Explorer 1 (Data and Price Cache Surveyor)  
**Workspace**: `/storage/emulated/0/Documents/Project MIP`  
**Data Cache**: `/storage/emulated/0/MIP1_Scanner/data`  
**Execution Environment**: Ubuntu 26.04.1 LTS (proot on aarch64 Android / Termux), Python 3.14.4, pandas 2.3.3, pyarrow 23.0.1  

---

## Executive Summary

1. **Price Cache Inventory (`/storage/emulated/0/MIP1_Scanner/data/`)**:
   - Contains 7 files totaling ~181.7 MB (uncompressed cache `stock_ohlcv_cache.pkl` is 124.9 MB; `index__NSEI_cache.pkl` is 98.6 KB; SQLite database `constituents_cache.db` is 368.6 KB; `manifest.json` is 1.4 KB; plus 3 gzip archives).
   - **Bhavcopy Status**: **No Bhavcopy files exist** anywhere in `/storage/emulated/0/MIP1_Scanner/data/` or in the project workspace.
   - **Pickle Deserialization Compatibility**: Attempting to load `index__NSEI_cache.pkl` or `stock_ohlcv_cache.pkl` using standard `pandas.read_pickle()` in the current environment (Python 3.14.4 + pandas 2.3.3) fails with:
     ```
     NotImplementedError: (<StringDtype(storage='python', na_value=nan)>, array([...], dtype=object))
     ```
     This failure is caused by an upstream pandas 2.3 regression / breaking change (GitHub Issue **#63078**) in Cython `pandas._libs.arrays.NDArrayBacked.__setstate__`. The pickles were serialized with pandas <= 2.2 using protocol 5 where `NDArrayBacked`'s state was serialized as a 2-tuple `(dtype, ndarray)`. Pandas 2.3.3 expects a dictionary `{"_ndarray": ..., "_dtype": ...}` and raises `NotImplementedError` when given a tuple.
   - **Termux Python Status**: Termux native Python is 3.14.6 without `pandas` installed; PyPI provides no binary wheels for Python 3.14 aarch64 on Android (compilation from source would be required, which is non-trivial and slow on mobile).
   - **R0 Mandate Alignment**: R0 strictly forbids surrogate or monkey-patched unpicklers ("*Do NOT use surrogate or monkey-patched unpicklers... If cannot be loaded faithfully, stop and report*"). Because standard `pd.read_pickle` cannot load these files without a monkey patch or a pandas/python environment matching the serialization version (e.g. pandas 2.2), this constitutes a critical condition for the orchestrator to resolve or report.

2. **Project Workspace Data (`/storage/emulated/0/Documents/Project MIP/data/`)**:
   - **`EQUITY_L.csv`**: Located at `data/raw_reference/EQUITY_L.csv` (SHA-256: `c5fce7fdcba097e7f5607d5ec02fa430b50d0285da0e76ec926e33796304eab3`). Exactly 2,583 rows, 8 columns (note leading spaces in column headers: `' SERIES'`, `' DATE OF LISTING'`, `' PAID UP VALUE'`, `' MARKET LOT'`, `' ISIN NUMBER'`, `' FACE VALUE'`), 0 null values, 2,583 unique symbols, 2,583 unique ISINs. Date of listing format is `%d-%b-%Y`.
   - **`symbol_map.parquet`**: Located at `data/symbol_map.parquet` (SHA-256: `ae982c3e1c22bdcafcf9bec6de28385d7dd3b29d3392ad39935f4e1b0c28fc58`). Exactly 1,448 rows, 8 columns (`scrip_name`, `symbol`, `isin`, `first_seen`, `last_seen`, `resolution_method`, `confidence`, `status`). Status values: `proposed` (739), `auto` (709). Resolution methods: `equity_l_exact` (709), `unresolved` (516), `manual` (223). Ready for archiving to `data/symbol_map_v1.parquet` as required by R3.
   - **Cached Circular PDF & Rebalancing Schedule HTML**:
     - `data/raw_bulletins/nifty_replacement_circular_sep_2020.pdf` (302,766 bytes, SHA-256: `649a37a9179ebfe875ea44208a594411130e9d690a597a7eec659be8421b4a8e`).
     - `data/raw_bulletins/niftyindices___rebalancing_schedule_200.html` (150,560 bytes, SHA-256: `fe45bb9b5247c4e51ecb1c009d17d599b70b5ee2e652a65a3d0ae69792ebf3f7`).
     - **Text Extraction Tooling**: Neither `pypdf`, `pdfplumber`, `pdfminer`, `fitz`, nor `pdftotext` are pre-installed. However, pure Python with built-in `zlib` stream decompression extracts all 585 text lines from `nifty_replacement_circular_sep_2020.pdf` without third-party dependencies. For HTML, `bs4` (BeautifulSoup 4.14.3) and `lxml` (6.0.2) are installed and cleanly extract all 1,216 text lines and 11 tables.
     - **R2 Finding Confirmed**: The cached PDF circular is NSE Circular Ref No 0810/2020 (September 16, 2020) regarding "Listing of privately placed securities on the debt market segment", containing zero equity index replacement announcements. This confirms the Gate 0 finding: *"post-2020-09 bulletin availability NOT ESTABLISHED; deferred to Phase 5.6"*.
   - **Raw Index Membership Sheets (`IndexInclExcl.xls`)**:
     - Located at `/storage/emulated/0/Documents/Project MIP/IndexInclExcl.xls` (SHA-256: `8869bb7c4df67403131a494a8cc65509e80828f9438bc150b506cdbf55378046`). Contains 37 index sheets.
     - `Nifty 500`: 2,496 rows. Event dates are strings (ctype 1).
     - `Nifty Dividend Opportunities 50`: 229 rows. Event dates are Excel dates (ctype 3, float numbers).
     - **R1 Anomaly Confirmed**: In `Nifty Dividend Opportunities 50`, rows 127–130 contain two identical pairs of events dated `42983.0` (2017-09-05: Reliance Capital OUT, National Aluminium IN) with ctype 3. These were deduplicated rather than quarantined alongside the 10 rows in `data/quarantine_gate1.parquet`.

---

## 1. Inventory of Local Price Files (`/storage/emulated/0/MIP1_Scanner/data/`)

### 1.1 Complete File Inventory & SHA-256 Hashes

| Relative Path | Full Absolute Path | Size (Bytes) | Format | Last Modified (UTC) | SHA-256 Hash |
|---|---|---|---|---|---|
| `constituents_cache.db` | `/storage/emulated/0/MIP1_Scanner/data/constituents_cache.db` | 368,640 | SQLite 3 database | 2026-08-31 19:45:24 | `1a0695754467c9faccac8a9055c2979dc1ce31ab064d5c99839b3313637b8227` |
| `index__NSEI_cache.pkl` | `/storage/emulated/0/MIP1_Scanner/data/index__NSEI_cache.pkl` | 98,579 | Python Pickle (v5) | 2026-08-31 05:33:25 | `347fa350cd9dbb6a3426cf0526704f7068804d03ea8fc8482ab2bad4377faa38` |
| `index__NSEI_cache.pkl.gz` | `/storage/emulated/0/MIP1_Scanner/data/index__NSEI_cache.pkl.gz` | 27,101 | Gzip compressed pickle | 2026-08-30 18:42:51 | `4f5e2de5559e682365a7687c1fa0d647487e99e16b7f67e803202860185b3540` |
| `manifest.json` | `/storage/emulated/0/MIP1_Scanner/data/manifest.json` | 1,364 | JSON | 2026-08-31 19:46:10 | `05d4fd78584308fc8450ac07549e9321739d3947522b3a603752c7db262ed7ed` |
| `stock_ohlcv_cache.pkl` | `/storage/emulated/0/MIP1_Scanner/data/stock_ohlcv_cache.pkl` | 124,854,530 | Python Pickle (v5) | 2026-08-31 19:45:33 | `559255587b28c2796dc7a3bf6f6d06e2a15e0e8d1c45613b1fa3e3d68ee09bdf` |
| `stock_ohlcv_cache.pkl.gz` | `/storage/emulated/0/MIP1_Scanner/data/stock_ohlcv_cache.pkl.gz` | 8,661,398 | Gzip compressed pickle | 2026-08-30 18:51:33 | `36a5a770ea9a96580e369d6eefc17f1047b3200e6560ed6a69eb447585cea47e` |
| `tmp_drive/stock_ohlcv_cache.pkl.gz` | `/storage/emulated/0/MIP1_Scanner/data/tmp_drive/stock_ohlcv_cache.pkl.gz` | 56,401,642 | Gzip compressed pickle | 2026-08-31 19:46:44 | `c229d32fd02f0be53515e8036319c0b8f3384fc00ddc71be0a8f799cd512bf71` |

### 1.2 Bhavcopy Existence Check
- **Observation**: An exhaustive search was executed across `/storage/emulated/0/MIP1_Scanner/data/` and `/storage/emulated/0/Documents/Project MIP/` for filenames matching `*bhav*` (case-insensitive).
- **Result**: Zero matching files.
- **Statement**: **No Bhavcopy exists** in the designated data cache or the project workspace. Price data is available strictly via the pickled DataFrames (`stock_ohlcv_cache.pkl`, `index__NSEI_cache.pkl`).

### 1.3 `manifest.json` Declared Content & Dimensions

The file `/storage/emulated/0/MIP1_Scanner/data/manifest.json` (schema version 6) declares:

```json
{
  "schema_version": 6,
  "updated_at": "2026-09-01T01:16:10.002318",
  "files": {
    "data/index__NSEI_cache.pkl.gz": {
      "rows": 4648,
      "date_min": "2007-09-17",
      "date_max": "2026-08-27",
      "updated_at": "2026-08-31T00:37:57.603338"
    },
    "data/stock_ohlcv_cache.pkl.gz": {
      "rows": 329145,
      "symbols": 106,
      "date_min": "2007-01-02",
      "date_max": "2026-08-28",
      "updated_at": "2026-08-31T00:21:17.806506"
    },
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
    },
    "history/breadth_history.pkl": {
      "rows": 17621,
      "date_min": "2023-06-08",
      "date_max": "2026-08-31",
      "updated_at": "2026-09-01T01:16:08.773476"
    },
    "history/market_breadth.pkl": {
      "rows": 800,
      "date_min": "2023-06-09",
      "date_max": "2026-08-31",
      "updated_at": "2026-09-01T01:16:09.354211"
    },
    "history/picks_history.pkl": {
      "rows": 14,
      "vintages": 2,
      "updated_at": "2026-09-01T01:16:10.002310"
    }
  }
}
```

Key observations from `manifest.json`:
- `data/index__NSEI_cache.pkl` contains 4,649 rows from `2007-09-17` to `2026-08-31`.
- `data/stock_ohlcv_cache.pkl` contains 1,831,372 rows across 750 unique symbols from `2007-01-02` to `2026-08-31` (seed start `2015-01-01`).

### 1.4 SQLite Database (`constituents_cache.db`)
- Size: 368,640 bytes (368 KB).
- Tables:
  1. `index_constituents`: 3,008 rows, columns `['index_name', 'snapshot_date', 'symbol']`.
  2. `symbol_industry`: 1,504 rows, columns `['symbol', 'industry', 'snapshot_date']`.

---

## 2. In-Depth Pickle Structure & Compatibility Analysis

### 2.1 The Deserialization Failure

When attempting to load either `index__NSEI_cache.pkl` or `stock_ohlcv_cache.pkl` using `pandas.read_pickle()` in the current environment:

```python
import pandas as pd
df = pd.read_pickle('/storage/emulated/0/MIP1_Scanner/data/index__NSEI_cache.pkl')
```

The operation fails with:
```
Traceback (most recent call last):
  File "<string>", line 6, in <module>
    df_nsei = pd.read_pickle('/storage/emulated/0/MIP1_Scanner/data/index__NSEI_cache.pkl')
  File "/usr/lib/python3/dist-packages/pandas/io/pickle.py", line 202, in read_pickle
    return pickle.load(handles.handle)
  File "pandas/_libs/arrays.pyx", line 85, in pandas._libs.arrays.NDArrayBacked.__setstate__
  File "pandas/_libs/arrays.pyx", line 103, in pandas._libs.arrays.NDArrayBacked.__setstate__
NotImplementedError: (<StringDtype(storage='python', na_value=nan)>, array(['2007-09-17', '2007-09-18', '2007-09-19', ..., '2026-08-26',
       '2026-08-27', '2026-08-31'], shape=(4649,), dtype=object))
```

And for `stock_ohlcv_cache.pkl`:
```
NotImplementedError: (<StringDtype(storage='python', na_value=nan)>, array(['symbol', 'date', 'open', 'high', 'low', 'close', 'volume'], dtype=object))
```

### 2.2 Root Cause Analysis

1. **Pickle Protocol and Opcodes**:
   - The pickle stream uses **Pickle Protocol 5** (with FRAMEs).
   - In both files, the column index and string columns are stored using `pandas.arrays.StringArray`, a subclass of `pandas._libs.arrays.NDArrayBacked`.
   - In pandas versions <= 2.2, `NDArrayBacked.__reduce__` serialized the array's backing state as a 2-tuple: `(dtype, ndarray)`.
   - During unpickling (`pickle.load`), after reconstructing the `StringArray` object, pickle executes opcode `BUILD` (e.g. opcode 9426 in `index__NSEI_cache.pkl`), which calls `obj.__setstate__(state)`.
   - In pandas 2.3.3 (the version installed in Ubuntu 26.04), `NDArrayBacked.__setstate__` was rewritten to expect a dictionary `{"_ndarray": ..., "_dtype": ...}`. When given the older 2-tuple `(dtype, ndarray)`, line 103 of `pandas/_libs/arrays.pyx` executes:
     ```python
     raise NotImplementedError(state)
     ```
   - This issue is documented upstream in pandas as **GitHub Issue #63078** (*"BUG: when np.datetime64[ns] is a type in a MultiIndex, 'NotImplementedError' when trying to return the df from a joblib.delayed"* and related `NDArrayBacked` 2-tuple pickle state deserialization bugs).

2. **Built-in `pandas.compat.pickle_compat` Evaluation**:
   - We tested `pandas.compat.pickle_compat.load()` (pandas' standard backward compatibility unpickler).
   - `pickle_compat.py` overrides `load_newobj` and `load_reduce` for legacy types (like `PeriodArray`, `DatetimeArray`, `BlockIndex`), but does **not** catch or transform the `BUILD` state tuple for `NDArrayBacked`.
   - Consequently, `pickle_compat.load()` fails with the identical `NotImplementedError`.

3. **Termux Python Feasibility**:
   - Termux provides Python 3.14.6 in `/data/data/com.termux/files/usr/bin/python3`.
   - `pandas` is not pre-installed in Termux.
   - Running `pip3 install pandas` downloads `pandas-3.0.6.tar.gz` from PyPI because there are no pre-compiled binary wheels for Python 3.14 on `aarch64` Android.
   - Compiling pandas from source inside Termux on a mobile device requires a full C/C++/Cython/Meson build environment, which would take extensive compilation time and is prone to mobile memory and toolchain limits.

4. **Safe Loading & R0 Compliance**:
   - Requirement R0 explicitly dictates:
     > *"Do NOT use surrogate or monkey-patched unpicklers. Load with a correct method (e.g. matching pandas version via Termux python or re-export) and write data/price_cache_export.parquet... If cannot be loaded faithfully, stop and report."*
   - Because standard, unpatched loading in Python 3.14 + pandas 2.3.3 raises `NotImplementedError`, and Termux python lacks a matching pre-compiled pandas package, **clean unpatched loading is currently blocked by the pandas 2.3 upstream breaking change**.
   - If an unpickler hook or state-dict adapter were considered, R0 strictly bans surrogate or monkey-patched unpicklers. Therefore, the surveyor must report this finding plainly to the orchestrator.

---

## 3. Project Workspace Reference Data Survey

### 3.1 `EQUITY_L.csv` Analysis

- **Location**: `/storage/emulated/0/Documents/Project MIP/data/raw_reference/EQUITY_L.csv`
- **File Size**: 182,431 bytes (~178.2 KB)
- **SHA-256**: `c5fce7fdcba097e7f5607d5ec02fa430b50d0285da0e76ec926e33796304eab3`
- **Row Count**: 2,583 rows (excluding header)
- **Columns (8)**:
  Notice that columns 2 through 7 contain **leading whitespace** in their header names:
  1. `SYMBOL` (`object`)
  2. `NAME OF COMPANY` (`object`)
  3. ` SERIES` (`object` — note leading space)
  4. ` DATE OF LISTING` (`object` — note leading space)
  5. ` PAID UP VALUE` (`int64` — note leading space)
  6. ` MARKET LOT` (`int64` — note leading space)
  7. ` ISIN NUMBER` (`object` — note leading space)
  8. ` FACE VALUE` (`int64` — note leading space)
- **Null Values**: 0 nulls across all 8 columns.
- **Cardinality**:
  - Unique `SYMBOL`: 2,583 (100% unique)
  - Unique `ISIN NUMBER`: 2,583 (100% unique)
  - ` SERIES` values: `['EQ', 'BE', 'BZ']`
- **Listing Date Format**: `%d-%b-%Y` (e.g. `06-OCT-2008`, `03-MAY-1995`, `19-SEP-2019`).
- **Sample Head Rows**:
  - `SYMBOL`: `20MICRONS` | `NAME OF COMPANY`: `20 Microns Limited` | ` SERIES`: `EQ` | ` DATE OF LISTING`: `06-OCT-2008` | ` ISIN NUMBER`: `INE144J01027`
  - `SYMBOL`: `21STCENMGM` | `NAME OF COMPANY`: `21st Century Management Services Limited` | ` SERIES`: `EQ` | ` DATE OF LISTING`: `03-MAY-1995` | ` ISIN NUMBER`: `INE253B01015`
  - `SYMBOL`: `360ONE` | `NAME OF COMPANY`: `360 ONE WAM LIMITED` | ` SERIES`: `EQ` | ` DATE OF LISTING`: `19-SEP-2019` | ` ISIN NUMBER`: `INE466L01038`

### 3.2 `symbol_map.parquet` Analysis

- **Location**: `/storage/emulated/0/Documents/Project MIP/data/symbol_map.parquet`
- **File Size**: 49,083 bytes (~47.9 KB)
- **SHA-256**: `ae982c3e1c22bdcafcf9bec6de28385d7dd3b29d3392ad39935f4e1b0c28fc58`
- **Row Count**: 1,448 rows
- **Columns (8)**:
  `['scrip_name', 'symbol', 'isin', 'first_seen', 'last_seen', 'resolution_method', 'confidence', 'status']`
- **Current Status Distribution**:
  - `proposed`: 739 (51.0%)
  - `auto`: 709 (49.0%)
  - *(Note: Currently 0 rows have `unresolved`, `approved`, or `rejected`; R3 requires expanding statuses to include all five).*
- **Current Resolution Method Distribution**:
  - `equity_l_exact`: 709 (49.0%)
  - `unresolved`: 516 (35.6%)
  - `manual`: 223 (15.4%)
- **Current Confidence Distribution**:
  - `high`: 750 (51.8%)
  - `low`: 533 (36.8%)
  - `medium`: 165 (11.4%)
- **Sample Rows**:
  1. `scrip_name`: `'20 Microns Ltd'` -> `symbol`: `'20MICRONS'`, `isin`: `'INE144J01027'`, `first_seen`: `2013-07-17`, `last_seen`: `2013-09-27`, `method`: `'equity_l_exact'`, `confidence`: `'high'`, `status`: `'auto'`
  2. `scrip_name`: `'20th Century Finance Corporation Ltd.'` -> `symbol`: `''`, `isin`: `''`, `first_seen`: `1998-08-01`, `last_seen`: `1999-02-03`, `method`: `'unresolved'`, `confidence`: `'low'`, `status`: `'proposed'`
  3. `scrip_name`: `'3M India Ltd.'` -> `symbol`: `'3MINDIA'`, `isin`: `'INE470A01017'`, `first_seen`: `1998-08-01`, `last_seen`: `2018-09-28`, `method`: `'equity_l_exact'`, `confidence`: `'high'`, `status`: `'auto'`
- **Rebuild Requirements (R3)**:
  - Archive current file as `data/symbol_map_v1.parquet` (recording SHA-256 `ae982c3e1c22bdcafcf9bec6de28385d7dd3b29d3392ad39935f4e1b0c28fc58`).
  - Expand columns to include 12 new evidence attributes (`eq_name`, `eq_series`, `eq_listing_date`, `isin_in_equity_l`, `name_similarity`, `first_token_match`, `price_first_bar`, `price_last_bar`, `bars_expected`, `bars_present`, `coverage_pct`, `flags`, `evidence_source`).
  - Enforce S1–S6 screens and coverage thresholds (`>=90%`).

---

## 4. Cached Bulletins, Circulars, and Schedule HTML Survey

### 4.1 Artifact Inventory in `data/raw_bulletins/`

| Filename | Size (Bytes) | SHA-256 | Description |
|---|---|---|---|
| `nifty_replacement_circular_sep_2020.pdf` | 302,766 | `649a37a9179ebfe875ea44208a594411130e9d690a597a7eec659be8421b4a8e` | Cached PDF circular from Sep 2020 |
| `niftyindices___rebalancing_schedule_200.html` | 150,560 | `fe45bb9b5247c4e51ecb1c009d17d599b70b5ee2e652a65a3d0ae69792ebf3f7` | Cached HTML schedule from niftyindices.com |
| `nifty_indices_benchmark_codes_pdf.pdf` | 327,002 | `e2a4f494957e84459b66236b3db5d5fbc70f443e261763116fcde332616f0da9` | Benchmark codes documentation |
| `nifty_replacement_press_release_mar_2021.pdf`| 3,425 | `5d3765fcab98ae61be7bf990dc2c9e7e7811dc3184ec5947c61dc033cb2cbba9` | Press release snippet / error HTML |
| `nifty_tracking_error_pdf.pdf` | 25,636 | `cb0ca94e43b185ec437c35f29910d65a6c117b4c81bcf76dc8860a92f0fb8bc3` | Tracking error PDF |
| `niftyindices___historical_data_200.html` | 110,620 | `e5aee404987f8f9e612a4336fbb06e40ea1152a0a75da7e937397732a3f7ff93` | Historical data web page capture |
| `niftyindices___monthly_reports_200.html` | 79,502 | `0e3f8489cfef71f28b4566c77bbdb633c7f9602521c7ba14fe68817a0aee7998` | Monthly reports web page capture |
| `niftyindices___press_releases_200.html` | 78,915 | `fe7ebfbe665bf72c8ea4a2ca097c5553e6b4fa0570b561df6c9f286ee2b3e839` | Press releases web page capture |
| `nse_archives___indices_directory_404.html` | 3,545 | `2f9f8c1f96440264fc8b9f1d00344d9f64bf71e16fdf9926cb915998a44be716` | Archive 404 response capture |
| `nse_archives___press_directory_404.html` | 3,545 | `a84cb06774a3f81e3557e4df7345f17d23a1a1795c6f3d9d3d3c873f8e5d36e2` | Archive 404 response capture |

### 4.2 Text Extraction Tooling Readiness
- **CLI Tools**: `pdftotext`, `tesseract`, `mutool`, `pdfinfo` are **not installed**.
- **Python Libraries**: `pypdf`, `pdfplumber`, `pdfminer`, and `fitz` (PyMuPDF) are **not installed**. (Note: `poppler-utils`, `python3-pypdf`, and `python3-pdfminer` exist in Ubuntu apt repositories if package installation is authorized in implementation turns).
- **Pure-Python PDF Extraction**: Tested and verified. Using standard library `zlib.decompress` on PDF stream objects, 100% of text streams in `nifty_replacement_circular_sep_2020.pdf` can be decompressed and decoded into text (585 lines extracted) without any third-party dependencies.
- **HTML Parsing**: Pre-installed `bs4` (BeautifulSoup 4.14.3) and `lxml` (6.0.2) cleanly parse and extract structured data from `niftyindices___rebalancing_schedule_200.html` (1,216 lines, 11 HTML tables).

### 4.3 Gate 0 Restatement Findings (R2 Verification)

#### Text Extracted from `nifty_replacement_circular_sep_2020.pdf`:
```
N S E Circular
National Stock Exchange of India Limited
DEPARTMENT : LISTING
Download Ref. No.: NSE/CML/45722
Date : September 16, 2020
Circular Ref. No.: 0810/2020
To All Members,
Sub: Listing of privately placed securities on the debt market segment of the Exchange
In pursuance of Regulation 3.1.1 of the National Stock Exchange Debt Market (Trading)
Regulations, it is hereby notified that the privately placed debt instruments as specified in the Annexure,
have been admitted to dealings on the Debt Market Segment of the Exchange with effect from today...
...
Name of the Company: Bharti Hexacom Limited
Security Description: BHL CP 26/02/21
Sec Type: CP
ISIN: INE343G14214
...
```

#### Text Extracted from `niftyindices___rebalancing_schedule_200.html`:
```
Table 0: Broad Based Indices Reconstitution Schedule
['1', 'Nifty 50', 'Semi-annually - Last working day of March and September']
['2', 'Nifty Next 50', 'Semi-annually - Last working day of March and September']
['3', 'Nifty 100', 'Semi-annually - Last working day of March and September']
['4', 'Nifty Next 100', 'Semi-annually - Last working day of March and September']
['6', 'Nifty 500', 'Semi-annually - Last working day of March and September']

Table 2: Thematic Indices Reconstitution Schedule
['37', 'Nifty Dividend Opportunities 50', 'Annually - Last working day of March']
```

#### Gate 0 Restatement Conclusion:
The cached PDF circular `nifty_replacement_circular_sep_2020.pdf` is an NSE Listing Department Debt Market circular (`NSE/CML/45722`), NOT an index reconstitution or replacement bulletin. The rebalancing schedule HTML confirms semi-annual rebalancing schedules for Nifty 500 and annual rebalancing for Nifty Dividend Opportunities 50.
Therefore, the Gate 0 finding is fully reaffirmed:
> **"post-2020-09 bulletin availability NOT ESTABLISHED; deferred to Phase 5.6"**

---

## 5. Raw Index Membership Sheets Survey (`IndexInclExcl.xls`)

### 5.1 Workbook Structure
- **File**: `/storage/emulated/0/Documents/Project MIP/IndexInclExcl.xls`
- **Size**: 820,736 bytes (~801.5 KB)
- **SHA-256**: `8869bb7c4df67403131a494a8cc65509e80828f9438bc150b506cdbf55378046`
- **Total Sheets**: 37 sheets
- **Columns across sheets**: 4 columns: `['Index Name', 'Event Date', 'Scrip Name', 'Description']`

### 5.2 Key Sheet Statistics

| Sheet Name | Row Count (including header) | Data Rows | Event Date ctype | Description |
|---|---|---|---|---|
| `Nifty 500` | 2,496 | 2,495 | ctype 1 (`XL_CELL_TEXT`) | Primary reconstruction target (seed batch of 500 INs on 1998-08-01) |
| `Nifty Dividend Opportunities 50` | 229 | 228 | ctype 3 (`XL_CELL_DATE`) | Change events only; affected by R1 anomaly |
| `Nifty 50` | 197 | 196 | ctype 1 (`XL_CELL_TEXT`) | Change events only |
| `Nifty Next 50` | 383 | 382 | ctype 1 (`XL_CELL_TEXT`) | Change events only |
| `Nifty 100` | 337 | 336 | ctype 1 (`XL_CELL_TEXT`) | Change events only |
| `Nifty 200` | 467 | 466 | ctype 1 & 3 mixed | Contains 2017-09-05 quarantined rows |
| `Nifty Midcap 100` | 595 | 594 | ctype 1 & 3 mixed | Contains 2017-09-05 quarantined rows |
| `Nifty Smallcap 100` | 595 | 594 | ctype 1 (`XL_CELL_TEXT`) | Change events only |
| `Nifty LargeMidcap 250` | 771 | 770 | ctype 1 (`XL_CELL_TEXT`) | Change events only |
| `Nifty Alpha 50` | 705 | 704 | ctype 1 (`XL_CELL_TEXT`) | Change events only |

### 5.3 R1 Anomaly Deep Dive: `Nifty Dividend Opportunities 50`

In `Nifty Dividend Opportunities 50`, rows 127–130 exhibit the exact pattern targeted by requirement R1:

```python
Row 127: types=[1, 3, 1, 1] vals=['Nifty Dividend Opportunities 50', 42983.0, 'Reliance Capital Ltd.', 'Exclusion from Index']
Row 128: types=[1, 3, 1, 1] vals=['Nifty Dividend Opportunities 50', 42983.0, 'National Aluminium Co. Ltd.', 'Inclusion into Index']
Row 129: types=[1, 3, 1, 1] vals=['Nifty Dividend Opportunities 50', 42983.0, 'Reliance Capital Ltd.', 'Exclusion from Index']
Row 130: types=[1, 3, 1, 1] vals=['Nifty Dividend Opportunities 50', 42983.0, 'National Aluminium Co. Ltd.', 'Inclusion into Index']
```

- Excel date `42983.0` converts via `xlrd.xldate_as_tuple` to `(2017, 9, 5, 0, 0, 0)` -> `2017-09-05`.
- In Gate 1, these 2 pairs were treated as duplicate entries and **deduplicated** (removing rows 129–130 and leaving rows 127–128 in the dataset).
- However, all other sheets containing `2017-09-05` events with `ctype 3` (`datetime`) were **quarantined** into `data/quarantine_gate1.parquet` (10 rows):
  - `Nifty 200`: rows 348, 354
  - `Nifty Midcap 100`: rows 392, 397
  - `Nifty 500`: rows 2136, 2162
  - `Nifty Midcap 50`: rows 287, 289
  - `Nifty High Beta 50`: rows 125, 128
- **Conclusion for R1**: The 2 rows in `Nifty Dividend Opportunities 50` belong to the exact same suspect `datetime` class as the 10 quarantined rows. They should be consistently quarantined rather than deduplicated.

---

## 6. Synthesis and Architectural Recommendations for Orchestrator

1. **R0 (Price Loading Blocking Condition)**:
   - Python 3.14 + pandas 2.3.3 Cython regression GH#63078 blocks `pd.read_pickle()` for `stock_ohlcv_cache.pkl` and `index__NSEI_cache.pkl`.
   - R0 strictly forbids surrogate/monkey-patched unpicklers.
   - The orchestrator should evaluate whether:
     (a) An official patch/re-export of the price cache from an environment running pandas 2.2 is required, OR
     (b) A standard Python unpickler adapter script that cleanly parses the protocol 5 stream and writes standard Parquet (avoiding surrogate classes) is deemed compliant under R0.
2. **R1 (Gate 1 Anomaly Repair)**:
   - The 2 rows in `Nifty Dividend Opportunities 50` (Reliance Capital OUT, National Aluminium IN) have been conclusively identified at rows 127–130 of `IndexInclExcl.xls` with ctype 3 and Excel date 42983.0 (2017-09-05). Quarantining them will bring the quarantine count from 10 to 12.
3. **R2 (Gate 0 Restatement)**:
   - Text extraction is 100% verified using native pure-Python `zlib` stream decompression for PDF (585 lines) and `bs4`/`lxml` for HTML (1,216 lines). Gate 0 finding ("post-2020-09 bulletin availability NOT ESTABLISHED; deferred to Phase 5.6") is thoroughly validated.
4. **R3 (Symbol Map Rebuild)**:
   - `data/symbol_map.parquet` (1,448 rows, SHA-256 `ae982c3e1c22bdcafcf9bec6de28385d7dd3b29d3392ad39935f4e1b0c28fc58`) and `data/raw_reference/EQUITY_L.csv` (2,583 rows, SHA-256 `c5fce7fdcba097e7f5607d5ec02fa430b50d0285da0e76ec926e33796304eab3`) are fully intact, verified, and ready for S1–S6 evidence hardening.
