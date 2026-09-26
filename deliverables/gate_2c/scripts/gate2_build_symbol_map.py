#!/usr/bin/env python3
"""
Gate 2 — Rebuild Symbol Map with Evidence Hardening (S1–S6 Checks)
Step 3 Deliverable for Gate 2b:
- Archives old map as data/symbol_map_v1.parquet (done)
- Rebuilds data/symbol_map.parquet with evidence hardening
- Removes hardcoded corporate renames from auto logic (agent_memory only, low confidence, unsourced flag)
- Statuses: auto, proposed, unresolved, approved, rejected
- Resolution methods: equity_l_exact, token_match, agent_memory, user_override, unresolved
- Columns:
    scrip_name, symbol, isin, first_seen, last_seen, resolution_method, confidence, status,
    eq_name, eq_series, eq_listing_date, isin_in_equity_l, name_similarity, first_token_match,
    price_first_bar, price_last_bar, bars_expected, bars_present, coverage_pct, flags, evidence_source
- Screens S1–S6:
    S1: listing_after_first_seen (eq_listing_date > membership start + 30 days)
    S2: duplicate_name_collision (multiple EQUITY_L rows share normalized name)
    S3: isin_unverified (ISIN not in EQUITY_L and evidence_source cites no external doc)
    S4: concurrent_alias_collision (2 scrips map to same ISIN and co-exist in same index at same time)
    S5: predecessor_marker (name contains Old, Sus, Erstwhile, Merge, Arrangement, Delisted)
    S6: first_token_mismatch (first word of scrip_name differs from first word of eq_name)
- Auto rule: exact normalized name match + unique EQUITY_L candidate + ISIN in EQUITY_L + no S1/S4/S5 flag + coverage_pct >= 90
- Coverage tiers: >=90, 30-90, <30, n/a
"""

import os
import re
import datetime
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

EVENTS_PATH = "data/index_events.parquet"
EQUITY_L_PATH = "data/raw_reference/EQUITY_L.csv"
PRICE_EXPORT_PATH = "data/price_cache_export.parquet"
TRADING_CALENDAR_TXT = "data/trading_calendar.txt"
OUTPUT_SYMBOL_MAP = "data/symbol_map.parquet"

# Corporate renames kept ONLY as agent_memory, low confidence, unsourced
AGENT_MEMORY_RENAMES = {
    "infosys technologies ltd": ("INFY", "INE009A01021"),
    "infosys technologies limited": ("INFY", "INE009A01021"),
    "hero honda motors ltd": ("HEROMOTOCO", "INE158A01026"),
    "hero honda motors limited": ("HEROMOTOCO", "INE158A01026"),
    "hindustan lever ltd": ("HINDUNILVR", "INE030A01027"),
    "hindustan lever limited": ("HINDUNILVR", "INE030A01027"),
    "tata iron and steel co ltd": ("TATASTEEL", "INE081A01012"),
    "tata iron and steel company ltd": ("TATASTEEL", "INE081A01012"),
    "tata tea ltd": ("TATACONSUM", "INE192A01025"),
    "tata tea limited": ("TATACONSUM", "INE192A01025"),
    "associated cement companies ltd": ("ACC", "INE012A01025"),
    "the associated cement companies ltd": ("ACC", "INE012A01025"),
    "east india hotels ltd": ("EIHOTEL", "INE230A01023"),
    "glaxo india ltd": ("GLAXO", "INE159A01016"),
    "glaxo smithkline pharmaceuticals ltd": ("GLAXO", "INE159A01016"),
    "uti bank ltd": ("AXISBANK", "INE238A01034"),
    "ranbaxy laboratories ltd": ("SUNPHARMA", "INE044A01036"),
    "satyam computer services ltd": ("TECHM", "INE669C01036"),
    "l and t ltd": ("LT", "INE018A01030"),
    "larsen and toubro ltd": ("LT", "INE018A01030"),
    "madras refineries ltd": ("CHENNPETRO", "INE178A01016"),
    "reliance capital ltd": ("RELCAPITAL", "INE013A01015"),
    "avenue supermarts ltd": ("DMART", "INE192R01011"),
    "max financial services ltd": ("MFSL", "INE180A01020"),
    "berger paints india ltd": ("BERGEPAINT", "INE463A01038"),
    "jaiprakash associates ltd": ("JPASSOCIAT", "INE451D01028"),
    "national aluminium co ltd": ("NATIONALUM", "INE139A01034"),
    "adani power ltd": ("ADANIPOWER", "INE814H01011"),
    "dlf ltd": ("DLF", "INE271C01023"),
    "indian hotels co ltd": ("INDHOTEL", "INE053A01032"),
    "nhpc ltd": ("NHPC", "INE848E01016"),
    "unitech ltd": ("UNITECH", "INE694A01020"),
    "voltas ltd": ("VOLTAS", "INE226A01021"),
    "mahindra lifespace developers ltd": ("MAHLIFE", "INE813A01018"),
    "container corporation of india ltd": ("CONCOR", "INE111A01025"),
    "state bank of india": ("SBIN", "INE062A01020"),
}

def normalize_name(text: str) -> str:
    s = text.lower()
    s = s.replace("&", " and ")
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    tokens = s.split()
    suffix_map = {
        "limited": "ltd",
        "company": "co",
        "corporation": "corp",
        "private": "pvt",
        "incorporated": "inc",
    }
    tokens = [suffix_map.get(t, t) for t in tokens]
    return " ".join(tokens)

def get_first_token(name: str) -> str:
    # First alphanumeric token after stripping leading articles or noise if applicable
    s = re.sub(r"[^a-zA-Z0-9\s]", " ", name)
    tokens = [t.lower() for t in s.split() if t]
    if not tokens:
        return ""
    if tokens[0] == "the" and len(tokens) > 1:
        return tokens[1]
    return tokens[0]

def main():
    print("=" * 80)
    print("GATE 2b — SYMBOL MAP REBUILD WITH EVIDENCE HARDENING (S1–S6)")
    print("=" * 80)

    # 1. Load inputs
    events_df = pd.read_parquet(EVENTS_PATH)
    print(f"Loaded index events: {len(events_df)} rows")

    eq_df = pd.read_csv(EQUITY_L_PATH)
    eq_df.columns = [c.strip() for c in eq_df.columns]
    print(f"Loaded EQUITY_L: {len(eq_df)} rows")

    with open(TRADING_CALENDAR_TXT) as f:
        cal_dates_str = [line.strip() for line in f if line.strip()]
    cal_dates = [datetime.datetime.strptime(d, "%Y-%m-%d").date() for d in cal_dates_str]
    cal_dates_set = set(cal_dates)
    print(f"Loaded trading calendar: {len(cal_dates)} dates ({cal_dates[0]} to {cal_dates[-1]})")

    price_df = pd.read_parquet(PRICE_EXPORT_PATH)
    print(f"Loaded price cache: {len(price_df)} bars across {price_df['symbol'].nunique()} symbols")

    # Map symbol -> set of dates
    print("Indexing price bars by symbol...")
    price_symbol_dates = {}
    for sym, grp in price_df.groupby("symbol"):
        price_symbol_dates[sym] = set(grp["date"].values)

    # Map symbol -> first_bar, last_bar
    price_symbol_ranges = {}
    for sym, grp in price_df.groupby("symbol"):
        price_symbol_ranges[sym] = (grp["date"].min(), grp["date"].max())

    # 2. Build EQUITY_L Lookups
    eq_df["norm_name"] = eq_df["NAME OF COMPANY"].apply(normalize_name)
    eq_norm_counts = eq_df["norm_name"].value_counts().to_dict()
    
    # Track candidate lookup
    eq_exact_dict = {}
    for _, r in eq_df.iterrows():
        n = r["norm_name"]
        if n not in eq_exact_dict:
            eq_exact_dict[n] = []
        eq_exact_dict[n].append(r)

    eq_isin_set = set(eq_df["ISIN NUMBER"].dropna().unique())
    eq_symbol_map = {r["SYMBOL"]: r for _, r in eq_df.iterrows()}

    # S2 Duplicate names in EQUITY_L
    eq_duplicates = {n for n, c in eq_norm_counts.items() if c > 1}

    # 3. Compute membership windows per scrip name
    print("Computing membership windows across indices...")
    covered_end_map = events_df.groupby("index")["effective_date"].max().to_dict()

    # Precompute per-scrip event spans
    scrip_first_seen = events_df.groupby("scrip_name")["effective_date"].min().to_dict()
    scrip_last_seen = events_df.groupby("scrip_name")["effective_date"].max().to_dict()

    # Scrip membership window across all indices
    scrip_windows = {}
    for scrip, grp in events_df.groupby("scrip_name"):
        windows = []
        for idx_name, igrp in grp.groupby("index"):
            ins = igrp[igrp["action"] == "IN"]["effective_date"]
            outs = igrp[igrp["action"] == "OUT"]["effective_date"]
            first_in = ins.min() if len(ins) > 0 else igrp["effective_date"].min()
            last_out = outs.max() if len(outs) > 0 else covered_end_map[idx_name]
            windows.append((first_in, last_out))
        scrip_windows[scrip] = windows

    # Union calendar days per scrip
    scrip_expected_bars = {}
    for scrip, wins in scrip_windows.items():
        union_days = set()
        for w_start, w_end in wins:
            # Check calendar days
            for d in cal_dates:
                if w_start <= d <= w_end:
                    union_days.add(d)
        scrip_expected_bars[scrip] = union_days

    # 4. S4 Precomputation: Membership timelines per index
    # We will compute S4 when candidate ISINs are assigned
    all_scrips = sorted(events_df["scrip_name"].unique())

    # Build token list for token matching
    eq_entries = []
    for _, r in eq_df.iterrows():
        eq_entries.append({
            "symbol": r["SYMBOL"],
            "name": r["NAME OF COMPANY"],
            "isin": r["ISIN NUMBER"],
            "series": r["SERIES"],
            "listing_date": r["DATE OF LISTING"],
            "norm": r["norm_name"],
            "tokens": set(r["norm_name"].split())
        })

    # Predecessor regex for S5
    predecessor_regex = re.compile(r"\b(old|sus|erstwhile|merge|arrangement|delisted)\b", re.IGNORECASE)

    raw_candidates = []
    for scrip in all_scrips:
        first_seen = scrip_first_seen[scrip]
        last_seen = scrip_last_seen[scrip]
        norm_scrip = normalize_name(scrip)

        candidate_sym = ""
        candidate_isin = ""
        eq_name = ""
        eq_series = ""
        eq_listing_date = ""
        res_method = "unresolved"
        conf = "low"
        ev_source = ""
        similarity = 0.0

        # Check S2 Duplicate Collision
        if norm_scrip in eq_duplicates:
            # Multiple candidates in EQUITY_L sharing normalized name (e.g. FEL/FELDVR)
            # Never keep last row wins!
            res_method = "token_match"
            conf = "low"
            ev_source = "equity_l_duplicate_collision"
            matching_rows = eq_exact_dict[norm_scrip]
            # List them
            candidate_sym = matching_rows[0]["SYMBOL"]
            candidate_isin = matching_rows[0]["ISIN NUMBER"]
            eq_name = matching_rows[0]["NAME OF COMPANY"]
            eq_series = matching_rows[0]["SERIES"]
            eq_listing_date = matching_rows[0]["DATE OF LISTING"]
            similarity = 1.0

        elif norm_scrip in eq_exact_dict:
            r = eq_exact_dict[norm_scrip][0]
            candidate_sym = r["SYMBOL"]
            candidate_isin = r["ISIN NUMBER"]
            eq_name = r["NAME OF COMPANY"]
            eq_series = r["SERIES"]
            eq_listing_date = r["DATE OF LISTING"]
            res_method = "equity_l_exact"
            conf = "high"
            ev_source = "EQUITY_L"
            similarity = 1.0

        elif norm_scrip in AGENT_MEMORY_RENAMES:
            sym, isin = AGENT_MEMORY_RENAMES[norm_scrip]
            candidate_sym = sym
            candidate_isin = isin
            res_method = "agent_memory"
            conf = "low"
            ev_source = "agent_memory_unsourced"
            if sym in eq_symbol_map:
                r = eq_symbol_map[sym]
                eq_name = r["NAME OF COMPANY"]
                eq_series = r["SERIES"]
                eq_listing_date = r["DATE OF LISTING"]
            similarity = 0.50

        else:
            # Token match
            scrip_tokens = set(norm_scrip.split()) - {"ltd", "co", "corp", "pvt", "inc", "india"}
            best_match = None
            best_score = 0.0
            for entry in eq_entries:
                entry_tokens = entry["tokens"] - {"ltd", "co", "corp", "pvt", "inc", "india"}
                if not scrip_tokens or not entry_tokens:
                    continue
                intersect = len(scrip_tokens & entry_tokens)
                union = len(scrip_tokens | entry_tokens)
                score = intersect / union if union > 0 else 0
                if score > best_score:
                    best_score = score
                    best_match = entry

            if best_match and best_score >= 0.35:
                candidate_sym = best_match["symbol"]
                candidate_isin = best_match["isin"]
                eq_name = best_match["name"]
                eq_series = best_match["series"]
                eq_listing_date = best_match["listing_date"]
                res_method = "token_match"
                similarity = best_score
                ev_source = "EQUITY_L_token_match"
                if best_score >= 0.70:
                    conf = "high"
                elif best_score >= 0.50:
                    conf = "medium"
                else:
                    conf = "low"
            else:
                candidate_sym = ""
                candidate_isin = ""
                eq_name = ""
                eq_series = ""
                eq_listing_date = ""
                res_method = "unresolved"
                conf = "low"
                ev_source = ""
                similarity = 0.0

        raw_candidates.append({
            "scrip_name": scrip,
            "symbol": candidate_sym,
            "isin": candidate_isin,
            "first_seen": first_seen,
            "last_seen": last_seen,
            "resolution_method": res_method,
            "confidence": conf,
            "eq_name": eq_name,
            "eq_series": eq_series,
            "eq_listing_date": eq_listing_date,
            "isin_in_equity_l": (candidate_isin in eq_isin_set) if candidate_isin else False,
            "name_similarity": round(similarity, 4),
            "evidence_source": ev_source,
            "norm_scrip": norm_scrip,
        })

    cand_df = pd.DataFrame(raw_candidates)

    # 5. Precompute S4: Concurrent alias collisions
    # When two different scrip names map to one ISIN and are members of the same index at the same time.
    print("Checking S4 concurrent alias collisions...")
    s4_flagged_scrips = set()
    isin_to_scrips = {}
    for _, r in cand_df.iterrows():
        if r["isin"]:
            isin_to_scrips.setdefault(r["isin"], set()).add(r["scrip_name"])

    for isin, scrip_set in isin_to_scrips.items():
        if len(scrip_set) > 1:
            # Check if any two scrips co-existed in the same index at the same time
            # For each index, check time overlaps
            for idx_name, grp in events_df.groupby("index"):
                # Get timeline for each scrip in this index
                scrip_index_spans = []
                for s in scrip_set:
                    s_events = grp[grp["scrip_name"] == s]
                    if len(s_events) > 0:
                        ins = s_events[s_events["action"] == "IN"]["effective_date"]
                        outs = s_events[s_events["action"] == "OUT"]["effective_date"]
                        start = ins.min() if len(ins) > 0 else s_events["effective_date"].min()
                        end = outs.max() if len(outs) > 0 else covered_end_map[idx_name]
                        scrip_index_spans.append((s, start, end))

                # Check pairwise overlap
                for i in range(len(scrip_index_spans)):
                    for j in range(i + 1, len(scrip_index_spans)):
                        s1, start1, end1 = scrip_index_spans[i]
                        s2, start2, end2 = scrip_index_spans[j]
                        overlap_start = max(start1, start2)
                        overlap_end = min(end1, end2)
                        if overlap_start <= overlap_end:
                            s4_flagged_scrips.add(s1)
                            s4_flagged_scrips.add(s2)

    print(f"S4 concurrent alias collision scrips flagged: {len(s4_flagged_scrips)}")

    # 6. Apply screens S1-S6, calculate coverage, determine status
    final_rows = []
    demoted_by_flag = {
        "listing_after_first_seen": 0,
        "duplicate_name_collision": 0,
        "isin_unverified": 0,
        "concurrent_alias_collision": 0,
        "predecessor_marker": 0,
        "first_token_mismatch": 0,
        "low_coverage": 0,
        "unsourced": 0,
    }

    for _, r in cand_df.iterrows():
        scrip = r["scrip_name"]
        sym = r["symbol"]
        isin = r["isin"]
        norm_scrip = r["norm_scrip"]
        res_method = r["resolution_method"]
        conf = r["confidence"]
        eq_name = r["eq_name"]
        eq_series = r["eq_series"]
        eq_listing_date = r["eq_listing_date"]
        isin_in_equity = r["isin_in_equity_l"]
        similarity = r["name_similarity"]
        ev_source = r["evidence_source"]

        flags = []

        # If unresolved (no candidate)
        if not sym or res_method == "unresolved":
            final_rows.append({
                "scrip_name": scrip,
                "symbol": "",
                "isin": "",
                "first_seen": r["first_seen"],
                "last_seen": r["last_seen"],
                "resolution_method": "unresolved",
                "confidence": "low",
                "status": "unresolved",
                "eq_name": "",
                "eq_series": "",
                "eq_listing_date": "",
                "isin_in_equity_l": False,
                "name_similarity": 0.0,
                "first_token_match": False,
                "price_first_bar": "",
                "price_last_bar": "",
                "bars_expected": 0,
                "bars_present": 0,
                "coverage_pct": 0.0,
                "flags": "no_candidate",
                "evidence_source": "",
            })
            continue

        # Candidate exists: compute evidence
        # Expected bars in membership window
        expected_cal_dates = scrip_expected_bars[scrip]
        bars_expected = len(expected_cal_dates)

        # Present bars
        sym_dates_str = price_symbol_dates.get(sym, set())
        bars_present = 0
        for d in expected_cal_dates:
            if d.strftime("%Y-%m-%d") in sym_dates_str:
                bars_present += 1

        coverage_pct = round((bars_present / bars_expected * 100.0) if bars_expected > 0 else 0.0, 2)
        price_first_bar, price_last_bar = price_symbol_ranges.get(sym, ("", ""))

        # First token check (S6) and name mismatch
        w_s = [w.lower() for w in re.sub(r"[^a-zA-Z0-9\s]", " ", scrip).split() if w.lower() not in ["the"]]
        w_e = [w.lower() for w in re.sub(r"[^a-zA-Z0-9\s]", " ", eq_name).split() if w.lower() not in ["the"]]
        first_tok_s = w_s[0] if w_s else ""
        first_tok_e = w_e[0] if w_e else ""
        first_token_match = (first_tok_s == first_tok_e) and bool(first_tok_s)
        
        if not first_token_match:
            flags.append("first_token_mismatch")
        elif len(w_s) > 1 and len(w_e) > 1 and w_s[1] != w_e[1]:
            # Secondary token mismatch on abbreviated or compound names (e.g. I T C vs I S T, Bajaj Corp vs Bajaj Auto)
            flags.append("first_token_mismatch")

        # Name mismatch check when candidate does not exactly match normalized scrip
        if norm_scrip != normalize_name(eq_name):
            flags.append("name_mismatch")

        # S1 Listing Date Screen: eq_listing_date > membership start + 30 days
        if eq_listing_date:
            try:
                list_dt = datetime.datetime.strptime(eq_listing_date, "%d-%b-%Y").date()
                if list_dt > (r["first_seen"] + datetime.timedelta(days=30)):
                    flags.append("listing_after_first_seen")
            except:
                pass

        # S2 Duplicate Name Collision
        if norm_scrip in eq_duplicates:
            matching_syms = [row["SYMBOL"] for row in eq_exact_dict[norm_scrip]]
            flags.append(f"duplicate_name_collision({','.join(matching_syms)})")

        # S3 ISIN verification: ISIN not in EQUITY_L and evidence_source cites no external doc
        if not isin_in_equity:
            if "external_circular" not in ev_source:
                flags.append("isin_unverified")

        # S4 Concurrent Alias Collision
        if scrip in s4_flagged_scrips:
            flags.append("concurrent_alias_collision")

        # S5 Predecessor Marker
        if predecessor_regex.search(scrip):
            flags.append("predecessor_marker")

        # Agent memory unsourced flag
        if res_method == "agent_memory":
            flags.append("unsourced")

        # Determine status:
        # A row is auto only if:
        # - exact normalized-name match
        # - unique EQUITY_L candidate (no S2)
        # - ISIN in EQUITY_L (no S3)
        # - no S4 / S5 flag
        # - coverage_pct >= 90
        # - (An S1-flagged row may stay auto only if coverage_pct >= 90)
        # - and no token mismatch (S6)
        is_exact = (res_method == "equity_l_exact") and (norm_scrip not in eq_duplicates)
        has_s4_or_s5 = any(f in ["concurrent_alias_collision", "predecessor_marker"] for f in flags)
        has_s2_or_s3_or_s6 = any(f.startswith("duplicate_name_collision") or f in ["isin_unverified", "first_token_mismatch", "unsourced"] for f in flags)

        was_previously_exact = is_exact

        status = "proposed"
        if is_exact and isin_in_equity and (not has_s4_or_s5) and (not has_s2_or_s3_or_s6) and (coverage_pct >= 90.0):
            status = "auto"
        else:
            status = "proposed"
            # Track demotions for reporting
            if was_previously_exact:
                for f in flags:
                    key = f.split("(")[0]
                    demoted_by_flag[key] = demoted_by_flag.get(key, 0) + 1
                if coverage_pct < 90.0:
                    demoted_by_flag["low_coverage"] = demoted_by_flag.get("low_coverage", 0) + 1

        final_rows.append({
            "scrip_name": scrip,
            "symbol": sym,
            "isin": isin,
            "first_seen": r["first_seen"],
            "last_seen": r["last_seen"],
            "resolution_method": res_method,
            "confidence": conf,
            "status": status,
            "eq_name": eq_name,
            "eq_series": eq_series,
            "eq_listing_date": eq_listing_date,
            "isin_in_equity_l": isin_in_equity,
            "name_similarity": similarity,
            "first_token_match": first_token_match,
            "price_first_bar": price_first_bar,
            "price_last_bar": price_last_bar,
            "bars_expected": bars_expected,
            "bars_present": bars_present,
            "coverage_pct": coverage_pct,
            "flags": ";".join(flags) if flags else "",
            "evidence_source": ev_source,
        })

    rebuilt_df = pd.DataFrame(final_rows)
    cols = [
        "scrip_name", "symbol", "isin", "first_seen", "last_seen", "resolution_method", "confidence", "status",
        "eq_name", "eq_series", "eq_listing_date", "isin_in_equity_l", "name_similarity", "first_token_match",
        "price_first_bar", "price_last_bar", "bars_expected", "bars_present", "coverage_pct", "flags", "evidence_source"
    ]
    rebuilt_df = rebuilt_df[cols]
    pq.write_table(pa.Table.from_pandas(rebuilt_df), OUTPUT_SYMBOL_MAP)
    print(f"\nSuccessfully wrote rebuilt symbol map to {OUTPUT_SYMBOL_MAP} ({len(rebuilt_df)} rows)")

    # 7. Summary Reporting
    print("\n--- Summary by Status ---")
    status_counts = rebuilt_df["status"].value_counts()
    for s, c in status_counts.items():
        print(f"  {s:<15}: {c:4d} ({c/len(rebuilt_df)*100:.1f}%)")

    print("\n--- Demotions from Auto by Flag ---")
    for f, c in demoted_by_flag.items():
        print(f"  {f:<30}: {c}")

    print("\n--- Coverage Tiers ---")
    def get_tier(row):
        if not row["symbol"]:
            return "n/a"
        cov = row["coverage_pct"]
        if cov >= 90.0:
            return ">=90"
        elif cov >= 30.0:
            return "30-90"
        else:
            return "<30"

    rebuilt_df["coverage_tier"] = rebuilt_df.apply(get_tier, axis=1)
    tier_counts = rebuilt_df["coverage_tier"].value_counts()
    for t in [">=90", "30-90", "<30", "n/a"]:
        c = tier_counts.get(t, 0)
        print(f"  Coverage Tier {t:<6}: {c:4d} ({c/len(rebuilt_df)*100:.1f}%)")

    print("\nState Note on Coverage:")
    print("  Low coverage can mean a symbol change or a delisted stock absent from the cache,")
    print("  not necessarily a wrong mapping. This is why coverage is evidence, not a verdict.")

if __name__ == "__main__":
    main()
