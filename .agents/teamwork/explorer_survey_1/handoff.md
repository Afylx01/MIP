# Handoff Report — Explorer Survey 1 (Phase 5.5 Gate 2b)

**Date**: 2026-09-24  
**Author**: Explorer 1 (Data and Price Cache Surveyor)  
**Recipient**: Orchestrator Gate 2b (`d3c150ff-7336-4f70-9f7c-d7808f1a9360`)  
**Type**: Hard Handoff (Investigation Complete)  

---

## 1. Observation

### 1.1 Local Price Cache Files (`/storage/emulated/0/MIP1_Scanner/data/`)
Executed file inspection and SHA-256 computation:
- `constituents_cache.db`: 368,640 bytes, mtime `2026-08-31 19:45:24 UTC`, SHA-256 `1a0695754467c9faccac8a9055c2979dc1ce31ab064d5c99839b3313637b8227`. SQLite database with tables `index_constituents` (3,008 rows) and `symbol_industry` (1,504 rows).
- `index__NSEI_cache.pkl`: 98,579 bytes, mtime `2026-08-31 05:33:25 UTC`, SHA-256 `347fa350cd9dbb6a3426cf0526704f7068804d03ea8fc8482ab2bad4377faa38`.
- `index__NSEI_cache.pkl.gz`: 27,101 bytes, mtime `2026-08-30 18:42:51 UTC`, SHA-256 `4f5e2de5559e682365a7687c1fa0d647487e99e16b7f67e803202860185b3540`.
- `manifest.json`: 1,364 bytes, mtime `2026-08-31 19:46:10 UTC`, SHA-256 `05d4fd78584308fc8450ac07549e9321739d3947522b3a603752c7db262ed7ed`. Declares `data/index__NSEI_cache.pkl` has 4,649 rows (`2007-09-17` to `2026-08-31`) and `data/stock_ohlcv_cache.pkl` has 1,831,372 rows across 750 symbols (`2007-01-02` to `2026-08-31`).
- `stock_ohlcv_cache.pkl`: 124,854,530 bytes, mtime `2026-08-31 19:45:33 UTC`, SHA-256 `559255587b28c2796dc7a3bf6f6d06e2a15e0e8d1c45613b1fa3e3d68ee09bdf`.
- `stock_ohlcv_cache.pkl.gz`: 8,661,398 bytes, mtime `2026-08-30 18:51:33 UTC`, SHA-256 `36a5a770ea9a96580e369d6eefc17f1047b3200e6560ed6a69eb447585cea47e`.
- `tmp_drive/stock_ohlcv_cache.pkl.gz`: 56,401,642 bytes, mtime `2026-08-31 19:46:44 UTC`, SHA-256 `c229d32fd02f0be53515e8036319c0b8f3384fc00ddc71be0a8f799cd512bf71`.

### 1.2 Bhavcopy Existence
Executed:
```bash
find "/storage/emulated/0/Documents/Project MIP" "/storage/emulated/0/MIP1_Scanner/data" -iname "*bhav*"
```
Result: Exited 0 with empty output. **Zero Bhavcopy files exist.**

### 1.3 Pickle Loading Error & Pandas Version
Executed:
```python
import pandas as pd
df = pd.read_pickle('/storage/emulated/0/MIP1_Scanner/data/index__NSEI_cache.pkl')
```
Verbatim Error:
```
File "/usr/lib/python3/dist-packages/pandas/io/pickle.py", line 202, in read_pickle
  return pickle.load(handles.handle)
File "pandas/_libs/arrays.pyx", line 85, in pandas._libs.arrays.NDArrayBacked.__setstate__
File "pandas/_libs/arrays.pyx", line 103, in pandas._libs.arrays.NDArrayBacked.__setstate__
NotImplementedError: (<StringDtype(storage='python', na_value=nan)>, array(['2007-09-17', '2007-09-18', '2007-09-19', ..., '2026-08-26', '2026-08-27', '2026-08-31'], shape=(4649,), dtype=object))
```
For `stock_ohlcv_cache.pkl`:
```
NotImplementedError: (<StringDtype(storage='python', na_value=nan)>, array(['symbol', 'date', 'open', 'high', 'low', 'close', 'volume'], dtype=object))
```
Current environment: Python 3.14.4, pandas `2.3.3+dfsg-3ubuntu1`. Termux Python: 3.14.6 without pandas installed; pip install dry-run shows no binary wheels on PyPI for aarch64 Android, falling back to source tarball `pandas-3.0.6.tar.gz`.

### 1.4 Project Workspace Files
- `data/raw_reference/EQUITY_L.csv`:
  - Size: 182,431 bytes. SHA-256: `c5fce7fdcba097e7f5607d5ec02fa430b50d0285da0e76ec926e33796304eab3`.
  - Rows: 2,583 rows. Columns: `['SYMBOL', 'NAME OF COMPANY', ' SERIES', ' DATE OF LISTING', ' PAID UP VALUE', ' MARKET LOT', ' ISIN NUMBER', ' FACE VALUE']`.
  - 0 nulls; 2,583 unique symbols and ISINs. Series: `['EQ', 'BE', 'BZ']`. Listing date format: `%d-%b-%Y`.
- `data/symbol_map.parquet`:
  - Size: 49,083 bytes. SHA-256: `ae982c3e1c22bdcafcf9bec6de28385d7dd3b29d3392ad39935f4e1b0c28fc58`.
  - Rows: 1,448 rows. Columns: `['scrip_name', 'symbol', 'isin', 'first_seen', 'last_seen', 'resolution_method', 'confidence', 'status']`.
  - Statuses: `proposed` (739), `auto` (709). Resolution methods: `equity_l_exact` (709), `unresolved` (516), `manual` (223).
- `data/raw_bulletins/nifty_replacement_circular_sep_2020.pdf`:
  - Size: 302,766 bytes. SHA-256: `649a37a9179ebfe875ea44208a594411130e9d690a597a7eec659be8421b4a8e`.
  - 21 streams, 585 text lines extracted using pure Python `zlib.decompress`.
  - Content: NSE Listing Circular `NSE/CML/45722` dated September 16, 2020: "Listing of privately placed securities on the debt market segment", not equity index replacement bulletins.
- `data/raw_bulletins/niftyindices___rebalancing_schedule_200.html`:
  - Size: 150,560 bytes. SHA-256: `fe45bb9b5247c4e51ecb1c009d17d599b70b5ee2e652a65a3d0ae69792ebf3f7`.
  - 1,216 text lines and 11 tables cleanly parsed via `BeautifulSoup` (`bs4` 4.14.3 + `lxml` 6.0.2).
  - Confirms Nifty 500 semi-annual rebalancing (March and September) and Nifty Dividend Opportunities 50 annual rebalancing (March).
- `IndexInclExcl.xls`:
  - Size: 820,736 bytes. SHA-256: `8869bb7c4df67403131a494a8cc65509e80828f9438bc150b506cdbf55378046`.
  - 37 sheets. `Nifty 500`: 2,496 rows (ctype 1 text dates). `Nifty Dividend Opportunities 50`: 229 rows (ctype 3 date floats).
  - Rows 127–130 in `Nifty Dividend Opportunities 50`:
    - Row 127: types=[1, 3, 1, 1], `['Nifty Dividend Opportunities 50', 42983.0, 'Reliance Capital Ltd.', 'Exclusion from Index']`
    - Row 128: types=[1, 3, 1, 1], `['Nifty Dividend Opportunities 50', 42983.0, 'National Aluminium Co. Ltd.', 'Inclusion into Index']`
    - Row 129: types=[1, 3, 1, 1], `['Nifty Dividend Opportunities 50', 42983.0, 'Reliance Capital Ltd.', 'Exclusion from Index']`
    - Row 130: types=[1, 3, 1, 1], `['Nifty Dividend Opportunities 50', 42983.0, 'National Aluminium Co. Ltd.', 'Inclusion into Index']`
    - Date 42983.0 = `2017-09-05`.
- `data/quarantine_gate1.parquet`:
  - 10 rows (SHA-256 `d552478a7a17b564cd2a8d9506ff7468e22bd74cbb70b3a3de6c305fc0a8358b`), all dated `2017-09-05` with `date_type: datetime`.

---

## 2. Logic Chain

1. **Price Cache Inventory & Bhavcopy**:
   - Direct filesystem walk in `/storage/emulated/0/MIP1_Scanner/data/` cataloged exactly 7 files (Section 1.1).
   - Case-insensitive search across the project workspace and data cache returned 0 bhavcopy files (Section 1.2).
   - *Inference*: The project has never used raw Bhavcopy files; all historical prices reside inside the pickled caches `stock_ohlcv_cache.pkl` and `index__NSEI_cache.pkl`.

2. **Pickle Incompatibility & Upstream Regression**:
   - `pd.read_pickle` throws `NotImplementedError` at Cython `NDArrayBacked.__setstate__` line 103 (Section 1.3).
   - Inspection of pickle stream shows `StringArray` state serialized as 2-tuple `(dtype, ndarray)` under pandas <= 2.2 protocol 5.
   - Upstream GitHub issue #63078 confirms pandas 2.3 refactored `NDArrayBacked.__setstate__` to expect `dict` and left `raise NotImplementedError(state)` for tuple states.
   - Termux native Python 3.14 lacks pandas, and installing from PyPI requires source compilation without wheels on aarch64.
   - R0 rule states: *"Do NOT use surrogate or monkey-patched unpicklers... If cannot be loaded faithfully, stop and report."*
   - *Inference*: Loading price files directly via unpatched `pd.read_pickle` in this environment is blocked. This triggers the R0 HALT/report condition.

3. **Gate 0 Circular Restatement (R2)**:
   - Text extracted from `data/raw_bulletins/nifty_replacement_circular_sep_2020.pdf` contains debt security listings, not equity index reconstitutions (Section 1.4).
   - Rebalancing schedule HTML confirms reconstitution cycles but provides no post-2020-09 bulletin files.
   - *Inference*: R2 Gate 0 finding *"post-2020-09 bulletin availability NOT ESTABLISHED; deferred to Phase 5.6"* is verified with primary evidence.

4. **Gate 1 Anomaly Repair (R1)**:
   - Rows 127–130 in `Nifty Dividend Opportunities 50` have ctype 3 and Excel date 42983.0 (`2017-09-05`).
   - The other 10 rows from 2017-09-05 with ctype 3 across 5 sheets were quarantined into `quarantine_gate1.parquet`.
   - *Inference*: The 2 rows (Reliance Capital OUT, National Aluminium IN) were mistakenly deduplicated rather than quarantined. Treating them consistently moves them to quarantine, bringing the total quarantine count from 10 to 12.

5. **Symbol Map & Reference Data Readiness (R3)**:
   - `EQUITY_L.csv` (2,583 rows) and `symbol_map.parquet` (1,448 rows) have verified hashes and schemas.
   - Headers in `EQUITY_L.csv` have leading whitespace which must be stripped or handled when joining.
   - *Inference*: All reference artifacts for R3 are verified and available for the symbol map rebuild.

---

## 3. Caveats

1. **Pickle Loading Workarounds**: While an in-memory protocol 5 stream adapter could map the 2-tuple to a dictionary during unpickling to load the DataFrames without modifying Cython, requirement R0 strictly bans surrogate or monkey-patched unpicklers. Thus, Explorer 1 did not deploy any surrogate loader and reported the exact blocking state.
2. **Workspace Hygiene Boundary**: Explorer 1 strictly adhered to the workspace hygiene constraint and did not scan outside `/storage/emulated/0/Documents/Project MIP` and `/storage/emulated/0/MIP1_Scanner/data`.
3. **No Code Modification**: As a read-only explorer, Explorer 1 did not modify any codebase files or write any data files outside `.agents/teamwork/explorer_survey_1/`.

---

## 4. Conclusion

1. **Price Cache**: 7 files inventoried. Zero Bhavcopy files exist. `manifest.json` indicates 1,831,372 rows / 750 symbols for stocks and 4,649 rows for NSEI index. Loading via `pd.read_pickle` is blocked by pandas 2.3 Cython regression GH#63078.
2. **Gate 0 Restatement**: Confirmed via pure-Python extraction that `nifty_replacement_circular_sep_2020.pdf` contains debt listings, verifying that post-2020-09 bulletin availability is not established.
3. **Gate 1 Anomaly**: The 2 rows in `Nifty Dividend Opportunities 50` (rows 127–130, ctype 3, 2017-09-05) are identical to the quarantined class in `quarantine_gate1.parquet` and should be quarantined.
4. **Symbol Map & Reference Data**: `EQUITY_L.csv` (2,583 rows) and `symbol_map.parquet` (1,448 rows) are fully verified and ready for R3 archiving and evidence hardening.

---

## 5. Verification Method

To independently verify all findings:

1. **Verify Bhavcopy Non-Existence**:
   ```bash
   find "/storage/emulated/0/Documents/Project MIP" "/storage/emulated/0/MIP1_Scanner/data" -iname "*bhav*"
   ```
   (Must output empty / exit 0).

2. **Verify Pickle Deserialization Error**:
   ```bash
   python3 -c "import pandas as pd; pd.read_pickle('/storage/emulated/0/MIP1_Scanner/data/index__NSEI_cache.pkl')"
   ```
   (Must reproduce `NotImplementedError: (<StringDtype(storage='python', na_value=nan)>, ...)`).

3. **Verify EQUITY_L.csv and symbol_map.parquet Integrity**:
   ```bash
   python3 -c "
   import pandas as pd, hashlib
   for p in ['/storage/emulated/0/Documents/Project MIP/data/raw_reference/EQUITY_L.csv', '/storage/emulated/0/Documents/Project MIP/data/symbol_map.parquet']:
       with open(p, 'rb') as f: h = hashlib.sha256(f.read()).hexdigest()
       df = pd.read_csv(p) if p.endswith('.csv') else pd.read_parquet(p)
       print(p, 'SHA256:', h, 'Rows:', len(df))
   "
   ```
   Expected: `EQUITY_L.csv` = 2,583 rows (`c5fce7fdcba097e7f5607d5ec02fa430b50d0285da0e76ec926e33796304eab3`), `symbol_map.parquet` = 1,448 rows (`ae982c3e1c22bdcafcf9bec6de28385d7dd3b29d3392ad39935f4e1b0c28fc58`).

4. **Verify Nifty Dividend Opportunities 50 Excel Date & ctype**:
   ```bash
   python3 -c "
   import xlrd
   wb = xlrd.open_workbook('/storage/emulated/0/Documents/Project MIP/IndexInclExcl.xls')
   s = wb.sheet_by_name('Nifty Dividend Opportunities 50')
   for r in [127, 128, 129, 130]:
       print(r, [s.cell_type(r, c) for c in range(4)], [s.cell_value(r, c) for c in range(4)], xlrd.xldate_as_tuple(s.cell_value(r, 1), wb.datemode))
   "
   ```
   Expected: Rows 127–130 have `types=[1, 3, 1, 1]` and date tuple `(2017, 9, 5, 0, 0, 0)`.

5. **Verify PDF Pure-Python Text Extraction**:
   ```bash
   python3 -c "
   import zlib, re
   with open('/storage/emulated/0/Documents/Project MIP/data/raw_bulletins/nifty_replacement_circular_sep_2020.pdf', 'rb') as f: data = f.read()
   streams = re.findall(rb'stream[\r\n]+(.*?)[\r\n]+endstream', data, re.DOTALL)
   text = '\n'.join([c.decode('latin1', errors='replace') for s in streams for c in re.findall(rb'\((.*?)\)\s*Tj', zlib.decompress(s)) if re.findall(rb'\((.*?)\)\s*Tj', zlib.decompress(s))])
   print('NSE/CML/45722 in text:', 'NSE/CML/45722' in text, 'Debt in text:', 'debt' in text.lower())
   "
   ```
   Expected: True, True.
