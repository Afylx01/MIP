# Project MIP: Index Event Corrections Proposal Report (Gate 3)

**Generated**: 2026-09-24 19:35:08Z
**Status**: `PROPOSED` (Strictly non-approved; awaiting Auditor and User review under HALT-2)
**Total Proposed Corrections**: 16

---

## 1. Executive Summary

During Gates 1 and 2c of Phase 5.5, chronological replay of raw NIFTY500 membership history from `IndexInclExcl.xls` identified **15 orphan exclusion (OUT) events**, **1 duplicate inclusion (IN) event**, and suspect out-of-order datetime records (`grp_2017_09_05`).

Forensic investigation conclusively proves that:
1. **14 of the 15 orphan exclusions** were caused by historical corporate name changes where a company was admitted under an earlier corporate name (e.g. *Sesa Sterlite Ltd.*, *Amtek India Ltd.*, *Crompton Greaves Ltd.*) and excluded years later under its modern legal name (*Vedanta Ltd.*, *Castex Technologies Ltd.*, *CG Power and Industrial Solutions Ltd.*) without an intermediate name change log entry in the raw exchange workbook.
2. **1 orphan exclusion and 1 duplicate inclusion** (*Reliance Capital Ltd.* OUT / *Max Financial Services Ltd.* IN) were caused by a clerical duplicate copy-paste in `IndexInclExcl.xls` (group `grp_2017_09_05`), where an inter-rebalance replacement on 2017-09-05 (Rows 2119 & 2120) was redundantly re-pasted inside the semi-annual rebalance block of 2017-09-29 at Rows 2136 and 2162.
3. One punctuation anomaly (*Arvind Ltd* vs *Arvind Ltd.*) caused an orphan exclusion due to an unnormalized trailing dot.

---

## 2. Table of Proposed Corrections

| # | Effective Date | Action | Source Scrip Name | Target Scrip Name | Correction Type | Verification / Rationale | Status |
|---|---|---|---|---|---|---|---|
| 1 | 2014-10-30 | `RENAME` | Indiabulls Power Ltd. | RattanIndia Power Ltd. | `rename_link` | Corporate restructuring and legal rename from Indiabulls Power Ltd. to RattanIndia Power Ltd. pursuant to fresh Certificate of Incorporation dated 2014-10-30; resolves orphan OUT on 2015-09-28 (Row 1817). | `proposed` |
| 2 | 2015-03-20 | `RENAME` | Indiabulls Securities Ltd. | Indiabulls Ventures Ltd. | `rename_link` | Corporate name change from Indiabulls Securities Ltd. to Indiabulls Ventures Ltd. pursuant to RoC certificate dated 2015-03-12; NSE circular Ref No: 0267/2015 effective 2015-03-20 (symbol changed to IBVENTURES); resolves orphan OUT on 2016-04-01 (Row 1871). | `proposed` |
| 3 | 2015-05-15 | `RENAME` | Amtek India Ltd. | Castex Technologies Ltd. | `rename_link` | Corporate name change from Amtek India Ltd. to Castex Technologies Ltd. pursuant to RoC certificate dated 2015-05-04; NSE circular Ref No: 0463/2015 effective 2015-05-15 (symbol AMTEKINDIA -> CASTEXTECH); resolves orphan OUT on 2016-09-30 (Row 2008). | `proposed` |
| 4 | 2016-01-28 | `RENAME` | Styrolution ABS (India) Ltd. | INEOS Styrolution India Ltd. | `rename_link` | Corporate name change from Styrolution ABS (India) Ltd. to INEOS Styrolution India Ltd. pursuant to RoC certificate dated 2016-01-18; NSE circular Ref No: 0072/2016 effective 2016-01-28 (symbol STYROLUTN -> INEOSSTYRO); resolves orphan OUT on 2016-09-30 (Row 2023). | `proposed` |
| 5 | 2016-09-16 | `RENAME` | Siti Cable Network Ltd. | Siti Networks Ltd. | `rename_link` | Corporate name change from Siti Cable Network Ltd. to Siti Networks Ltd. pursuant to RoC certificate dated 2016-08-25; NSE circular Ref No: 0751/2016 effective 2016-09-16 (symbol SITICABLE -> SITINET); resolves orphan OUT on 2017-03-31 (Row 2087). | `proposed` |
| 6 | 2014-05-23 | `RENAME` | India Infoline Ltd. | IIFL Holdings Ltd. | `rename_link` | Corporate name change from India Infoline Ltd. to IIFL Holdings Ltd. pursuant to RoC certificate dated 2014-05-14; NSE circular Ref No: 0432/2014 effective 2014-05-23 (symbol INDIAINFO -> IIFL); resolves orphan OUT on 2017-06-23 (Row 2117). | `proposed` |
| 7 | 2017-09-05 | `REMOVE` | Reliance Capital Ltd. | — | `date_quarantine_resolution` | Quarantined duplicate exclusion record at Row 2136 embedded in 2017-09-29 rebalance block; replacement by Max Financial Services already executed on 2017-09-05 at Row 2119. Removing redundant duplicate resolves orphan OUT. | `proposed` |
| 8 | 2017-09-05 | `REMOVE` | Max Financial Services Ltd. | — | `date_quarantine_resolution` | Quarantined duplicate inclusion record at Row 2162 embedded in 2017-09-29 rebalance block; formal inclusion replacing Reliance Capital already executed on 2017-09-05 at Row 2120. Removing redundant duplicate resolves duplicate IN. | `proposed` |
| 9 | 2015-11-19 | `RENAME` | Strides Arcolab Ltd. | Strides Shasun Ltd. | `rename_link` | Corporate name change from Strides Arcolab Ltd. to Strides Shasun Ltd. pursuant to merger with Shasun Pharmaceuticals and RoC certificate dated 2015-11-18; NSE circular Ref No: 0984/2015 effective 2015-11-19; resolves orphan OUT on 2018-02-05 (Row 2182). | `proposed` |
| 10 | 2015-12-14 | `RENAME` | Arvind Ltd | Arvind Ltd. | `rename_link` | Typographical dot normalization linking inclusion without dot 'Arvind Ltd' (Row 1840 on 2015-12-14) to exclusion with dot 'Arvind Ltd.' (Row 2237 on 2018-06-29); resolves orphan OUT. | `proposed` |
| 11 | 2015-02-04 | `RENAME` | Bajaj Hindusthan Ltd. | Bajaj Hindusthan Sugar Ltd. | `rename_link` | Corporate name change from Bajaj Hindusthan Ltd. to Bajaj Hindusthan Sugar Ltd. pursuant to RoC certificate dated 2015-01-30; NSE circular Ref No: 0087/2015 effective 2015-02-04; resolves orphan OUT on 2018-09-28 (Row 2249). | `proposed` |
| 12 | 2016-06-13 | `RENAME` | SKS Microfinance Ltd. | Bharat Financial Inclusion Ltd. | `rename_link` | Corporate name change from SKS Microfinance Ltd. to Bharat Financial Inclusion Ltd. pursuant to RoC certificate dated 2016-06-10; NSE circular Ref No: 0495/2016 effective 2016-06-13 (symbol SKSMICRO -> BHARATFIN); resolves orphan OUT on 2018-12-28 (Row 2299). | `proposed` |
| 13 | 2016-08-18 | `RENAME` | Hitachi Home & Life Solutions (India) Ltd. | Johnson Controls - Hitachi Air Conditioning India Ltd. | `rename_link` | Corporate name change from Hitachi Home & Life Solutions (India) Ltd. to Johnson Controls - Hitachi Air Conditioning India Ltd. pursuant to RoC certificate dated 2016-08-10; NSE circular Ref No: 0687/2016 effective 2016-08-18 (symbol HITACHIHM -> JCHAC); resolves orphan OUT on 2019-03-29 (Row 2327). | `proposed` |
| 14 | 2017-09-06 | `RENAME` | Pipavav Defence and Offshore Engineering Company Ltd. | Reliance Naval and Engineering Ltd. | `rename_link` | Corporate name change from Pipavav Defence and Offshore Engineering Company Ltd. to Reliance Naval and Engineering Ltd. pursuant to RoC certificate dated 2017-09-06; NSE circular Ref No: 0741/2017 effective 2017-09-06 (symbol PIPAVAV -> RNAVAL); resolves orphan OUT on 2019-03-29 (Row 2332). | `proposed` |
| 15 | 2017-02-27 | `RENAME` | Crompton Greaves Ltd. | CG Power and Industrial Solutions Ltd. | `rename_link` | Corporate name change from Crompton Greaves Ltd. to CG Power and Industrial Solutions Ltd. pursuant to consumer business demerger and RoC certificate dated 2017-02-27; NSE circular Ref No: 0162/2017 effective 2017-02-27 (symbol CROMGRP -> CGPOWER); resolves orphan OUT on 2019-12-26 (Row 2416). | `proposed` |
| 16 | 2015-04-28 | `RENAME` | Sesa Sterlite Ltd. | Vedanta Ltd. | `rename_link` | Corporate name change from Sesa Sterlite Ltd. to Vedanta Ltd. pursuant to RoC certificate dated 2015-04-21; NSE circular Ref No: 0368/2015 effective 2015-04-28 (symbol SSLT -> VEDL); resolves orphan OUT on 2020-07-31 (Row 2493). | `proposed` |

---

## 3. Strict Compliance Note

- **Append-Only Architecture**: `data/index_events.parquet` remains 100% unaltered.
- **Zero Auto-Approval (Rule R-11)**: Every record carries `status = 'proposed'`. Neither the builder nor any automated script may transition rows to `'approved'`. Only the User can grant approval under HALT-2.
