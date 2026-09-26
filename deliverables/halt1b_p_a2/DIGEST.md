# A-2 DIGEST

Status: COMPLETE
One-line summary: Discovered reachable NSE CA endpoint, fetched 214 historical splits/bonuses across 2016–2020, verified schema/monotonicity/no-dups with 3 hand-checks, built pure adjuster with passing smoke test, and verified 5 real-world events on Bhavcopy data with 100% assertions passing.
Auditor decisions honored: Q5=(b), CA path=1

## Gate 0 — CA endpoint discovery

Claim: Discovered usable NSE corporate-actions endpoint supporting historical date filtering (`from_date` / `to_date`) across 2016–2020; static archive CSV endpoints returned HTTP 404.
Evidence: EVIDENCE_INDEX row 7 (`deliverables/halt1b_p_a2/raw/gate0_discovery.txt`)
Excerpt (max 5 lines, source-labeled):
```
[gate0_discovery.txt:12] Probing: NSE Date-Filtered API (2016)
[gate0_discovery.txt:14] Status: HTTP 200 | Size: 658,561 bytes | Type: application/json; charset=utf-8
[gate0_discovery.txt:91] USABLE HISTORICAL ENDPOINT IDENTIFIED: NSE Date-Filtered API (2016)
[gate0_discovery.txt:95] GATE 0 EXIT: USABLE ENDPOINT FOUND -> PROCEED TO GATE 1 ON CA PATH 1.
```

## Gate 1 — Fetch results

Claim: Fetched 9,473 raw CA records across 2016–2020, parsed 214 splits/bonuses (192 distinct symbols, 180 distinct dates), persisted to Parquet/CSV, and captured 55 reference Bhavcopies.
Evidence: EVIDENCE_INDEX row 8 (`deliverables/halt1b_p_a2/raw/gate1_fetch.txt`) and row 81 (`data/verification/halt1b_p_a2/ca_calendar_raw.parquet`)
Excerpt (max 5 lines, source-labeled):
```
[gate1_fetch.txt:19]   Total records: 214 | Distinct symbols: 192 | Distinct dates: 180
[gate1_fetch.txt:22]   Date range: 2016-01-05 to 2020-08-24 | Action breakdown: {'bonus': 134, 'split': 80}
[gate1_fetch.txt:24]   Persisted Parquet: data/verification/halt1b_p_a2/ca_calendar_raw.parquet (7,961 bytes)
[gate1_fetch.txt:67] GATE 1 EXIT: SUCCESS — CA CALENDAR PERSISTED AND GATE 4 DATA CAPTURED
```

## Gate 2 — Schema and sanity

Claim: Schema validated with exact column names/dtypes, monotonic ex_date, zero duplicates, positive ratios, 3 events hand-verified against official NSE announcements, and 456 NIFTY500 members checked.
Evidence: EVIDENCE_INDEX row 9 (`deliverables/halt1b_p_a2/raw/gate2_sanity.txt`) and row 6 (`deliverables/halt1b_p_a2/data_csv/nifty500_ca_coverage.csv`)
Excerpt (max 5 lines, source-labeled):
```
[gate2_sanity.txt:19] Assertion 2 PASSED: ex_date sorted monotonically.
[gate2_sanity.txt:23] Duplicate (symbol, ex_date, action_type) count: 0 (Assertion 3 PASSED)
[gate2_sanity.txt:49] Assertion 5 PASSED: All 3 hand-verified events (INFY, TCS, RELIANCE) confirmed against public records.
[gate2_sanity.txt:58] NIFTY500 union member symbols (2016-2020): 456 | With CA event: 79 (17.3%) | Zero CA: 377 (82.7%)
```

## Gate 3 — Adjuster located or built

Claim: Branch A found no existing adjuster in workspace; Branch B built pure function `scripts/adjust_prices.py` (`adjust_ohlc`) with passing 5-bar continuity and NaN-preservation smoke tests.
Evidence: EVIDENCE_INDEX row 10 (`deliverables/halt1b_p_a2/raw/gate3_smoke_test.txt`) and row 73 (`deliverables/halt1b_p_a2/scripts/adjust_prices.py`)
Excerpt (max 5 lines, source-labeled):
```
[gate3_smoke_test.txt:1] Raw 1-day return across ex-date: -50.00%
[gate3_smoke_test.txt:2] Adjusted 1-day return across ex-date: 0.00%
[gate3_smoke_test.txt:3] Smoke test PASSED: 5-bar series with 1-event bonus is continuous.
[gate3_smoke_test.txt:6] ALL ADJUSTER SMOKE TESTS PASSED.
```

## Gate 4 — Adjuster unit test

Claim: Tested 5 real historical corporate actions (INFY, TCS, RELIANCE, WIPRO, MOLDTKPAC) on Bhavcopy bars; verified raw step drops match ratios and adjusted returns are continuous (<3% moves, <=30% limit).
Evidence: EVIDENCE_INDEX row 11 (`deliverables/halt1b_p_a2/raw/gate4_unit_test.txt`) and row 4 (`deliverables/halt1b_p_a2/data_csv/gate4_unit_test_summary.csv`)
Excerpt (max 5 lines, source-labeled):
```
[gate4_unit_test.txt:94] INFY 2018-09-04 bonus: raw return -48.60% | adjusted return +2.79% | PASS
[gate4_unit_test.txt:95] TCS  2018-05-31 bonus: raw return -50.46% | adjusted return -0.91% | PASS
[gate4_unit_test.txt:98] WIPRO 2019-03-06 bonus: raw return -23.69% | adjusted return +1.74% | PASS
[gate4_unit_test.txt:104] GATE 4 EXIT: ALL 5 EVENTS VERIFIED — ASSERTIONS PASSED (STEP DROP VERIFIED & ADJUSTED MOVE < 30%)
```

## Open questions for auditor

1. Official NSE ex-date for TCS 2018 bonus is May 31, 2018 (Record date: June 2, 2018); prompt referenced June 1, 2018. Confirm May 31, 2018 official ex-date is accepted.
2. For Phase 5.5.A-3 coverage re-measurement: confirm whether coverage calculation should run using `adjust_ohlc` across all 456 NIFTY500 symbols or the full price cache.
