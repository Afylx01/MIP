#!/usr/bin/env python3
"""
scripts/step1_v3_rebuild.py
Phase 5.5 — Gate 2c Step 1: Symbol Map Rebuild v3 with Match Flags Fix & Status Decoupling

Key Deliverables:
1. Pastes and explains entire Gate 2b flag-computation function.
2. Rewrites with stripped tokens (ltd, limited, co, corp, corporation, pvt, private, inc, the, india, (i)).
3. Prints 10-case unit test table raw with PASS/FAIL and detailed discrepancy analysis.
4. Reconstructs S4 concurrent_alias_collision using actual IN->OUT membership replay intervals.
   - Flags weaker evidence rows only; exact-match rows receive alias_target_of note.
   - Prints old vs new collision counts.
5. Decouples mapping_status (auto, proposed, unresolved) from price_status (covered, partial, none, inconclusive, no_symbol).
   - S1 cleared only if bars_expected >= 60 and coverage_pct >= 90%.
6. Archives data/symbol_map.parquet -> data/symbol_map_v2b.parquet (prints SHA-256).
   Exports deliverables/gate_2c/data_csv/symbol_map_v2b.csv and symbol_map_v3.csv.
   Tests 22 canaries -> deliverables/gate_2c/data_csv/canaries_2c.csv (must all remain non-auto).
   Prints before/after summary tables.
"""

import os
import re
import shutil
import hashlib
import datetime
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

# File Paths
EVENTS_PATH = "data/index_events.parquet"
EQUITY_L_PATH = "data/raw_reference/EQUITY_L.csv"
PRICE_EXPORT_PATH = "data/price_cache_export.parquet"
TRADING_CALENDAR_TXT = "data/trading_calendar.txt"
CANARIES_2B_PATH = "data/verification/canaries_2b.csv"

CURRENT_SYMBOL_MAP = "data/symbol_map.parquet"
ARCHIVE_V2B_PARQUET = "data/symbol_map_v2b.parquet"
OUTPUT_V3_PARQUET = "data/symbol_map.parquet"

DELIVERABLES_CSV_DIR = "deliverables/gate_2c/data_csv"
DELIVERABLES_SCRIPTS_DIR = "deliverables/gate_2c/scripts"
DELIVERABLES_RAW_DIR = "deliverables/gate_2c/raw_outputs"

os.makedirs(DELIVERABLES_CSV_DIR, exist_ok=True)
os.makedirs(DELIVERABLES_SCRIPTS_DIR, exist_ok=True)
os.makedirs(DELIVERABLES_RAW_DIR, exist_ok=True)

# -----------------------------------------------------------------------------
# STEP 1.1: Pasting the ENTIRE Gate 2b flag computation function
# -----------------------------------------------------------------------------
GATE_2B_FLAG_FUNCTION = '''
        # --- ENTIRE GATE 2b FLAG COMPUTATION FUNCTION (FROM scripts/gate2_build_symbol_map.py lines 433-480) ---
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
'''

def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

# -----------------------------------------------------------------------------
# STEP 1.2: New Tokenization & Flag Definitions
# -----------------------------------------------------------------------------
STRIP_TOKENS = {"ltd", "limited", "co", "corp", "corporation", "pvt", "private", "inc", "the", "india", "i"}

def tokenize_and_strip(text: str):
    if not text:
        return [], set()
    s = text.lower().replace("(i)", " ")
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    tokens = [t for t in s.split() if t and t not in STRIP_TOKENS]
    return tokens, set(tokens)

def compute_name_flags(scrip_name: str, eq_name: str):
    tokens_s, set_s = tokenize_and_strip(scrip_name)
    tokens_e, set_e = tokenize_and_strip(eq_name)
    
    flags = []
    
    first_s = tokens_s[0] if tokens_s else ""
    first_e = tokens_e[0] if tokens_e else ""
    
    first_token_match = (first_s == first_e) and bool(first_s)
    if not first_token_match:
        flags.append("first_token_mismatch")
        
    # name_variant (informational, never blocks/demotes): one stripped token set is a subset of the other
    if set_s == set_e:
        # Identical sets
        pass
    elif set_s.issubset(set_e) or set_e.issubset(set_s):
        flags.append("name_variant")
    else:
        # neither subset relation holds
        inter = len(set_s & set_e)
        union = len(set_s | set_e)
        jaccard = inter / union if union > 0 else 0.0
        if jaccard < 0.5:
            flags.append("name_mismatch")
            
    return first_token_match, flags

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

predecessor_regex = re.compile(r"\b(old|sus|erstwhile|merge|arrangement|delisted)\b", re.IGNORECASE)

def main():
    print("=" * 80)
    print("PHASE 5.5 — GATE 2c: STEP 1 (SYMBOL MAP V3 REBUILD & EVIDENCE HARDENING)")
    print("=" * 80)

    # 1. Print Gate 2b flag function
    print("\n[1.1] ENTIRE PREVIOUS FLAG COMPUTATION FUNCTION (GATE 2b):")
    print(GATE_2B_FLAG_FUNCTION)
    print("\nRoot Cause Analysis of Gate 2b Flag Issues:")
    print("  a) False 'first_token_mismatch' on single-word names (ACC, CRISIL, Arvind, Alembic):")
    print("     The secondary token check `elif len(w_s) > 1 and len(w_e) > 1 and w_s[1] != w_e[1]`")
    print("     compared token 2 directly without stripping corporate suffixes. In 'ACC Ltd.' vs 'ACC Limited',")
    print("     w_s[1] was 'ltd' while w_e[1] was 'limited', causing a false mismatch flag.")
    print("  b) 'Corporation Bank' -> AXISBANK flag explanation:")
    print("     In Gate 2b, token 1 of 'Corporation Bank' was 'corporation' and token 1 of 'Axis Bank Limited'")
    print("     was 'axis'. Because 'corporation' != 'axis', it triggered `first_token_mismatch` as intended.")

    # 2. Run Step 1.3 Unit Tests Table
    print("\n" + "=" * 80)
    print("[1.3] UNIT TESTS ON NEW TOKENIZATION & FLAG DEFINITIONS")
    print("=" * 80)

    unit_tests = [
        ("ACC Ltd.", "ACC Limited", "none"),
        ("CRISIL Ltd.", "CRISIL Limited", "none"),
        ("Arvind Ltd.", "Arvind Limited", "none"),
        ("Alembic Ltd.", "Alembic Limited", "none"),
        ("ABB Ltd.", "ABB India Limited", "name_variant"),
        ("Corporation Bank", "Axis Bank Limited", "first_token_mismatch"),
        ("Jindal Steel & Power Ltd.", "MSP Steel & Power Limited", "first_token_mismatch"),
        ("Bajaj Corp Ltd.", "Bajaj Auto Limited", "name_mismatch (first tokens equal)"),
        ("Welspun India Ltd.", "Welspun Corp Limited", "name_mismatch"),
        ("Larsen & Toubro Infotech Ltd.", "Larsen & Toubro Limited", "name_mismatch"),
    ]

    header = f"| {'scrip':<30} | {'eq_name':<30} | {'expected_flags':<35} | {'actual_flags':<35} | {'PASS/FAIL'} |"
    sep = "|" + "-"*32 + "|" + "-"*32 + "|" + "-"*37 + "|" + "-"*37 + "|-----------|"
    print(header)
    print(sep)

    for scrip, eq, exp in unit_tests:
        _, act_flags = compute_name_flags(scrip, eq)
        act_str = ";".join(act_flags) if act_flags else "none"
        passed = (act_str == exp) or (exp.startswith(act_str) and "(" in exp)
        p_str = "PASS" if passed else "FAIL"
        print(f"| {scrip:<30} | {eq:<30} | {exp:<35} | {act_str:<35} | {p_str:<9} |")

    print("\nDetailed Analysis of Raw Discrepancies (Instruction: 'Show failures raw; do not adjust expectations to pass'):")
    print("  1. ABB Ltd. vs ABB India Limited:")
    print("     Stripped tokens: scrip = {'abb'}, eq = {'abb'}. Suffix token 'india' is stripped per prompt rule.")
    print("     Resulting sets are identical ({'abb'} == {'abb'}), producing 'none' rather than 'name_variant'.")
    print("  2. Corporation Bank vs Axis Bank Limited:")
    print("     Stripped tokens: scrip = {'bank'} (corporation is stripped), eq = {'axis', 'bank'}.")
    print("     First tokens ('bank' vs 'axis') trigger 'first_token_mismatch'. Additionally, {'bank'} is a subset")
    print("     of {'axis', 'bank'}, triggering 'name_variant' under the literal subset rule.")
    print("  3. Bajaj Corp Ltd. vs Bajaj Auto Limited:")
    print("     Stripped tokens: scrip = {'bajaj'} (corp stripped), eq = {'bajaj', 'auto'}.")
    print("     {'bajaj'} is a subset of {'bajaj', 'auto'}, triggering 'name_variant' rather than 'name_mismatch'.")
    print("  4. Welspun India Ltd. vs Welspun Corp Limited:")
    print("     Stripped tokens: scrip = {'welspun'} (india stripped), eq = {'welspun'} (corp stripped).")
    print("     Resulting sets are identical ({'welspun'} == {'welspun'}), yielding 'none'.")
    print("  5. Larsen & Toubro Infotech Ltd. vs Larsen & Toubro Limited:")
    print("     Stripped tokens: scrip = {'larsen', 'toubro', 'infotech'}, eq = {'larsen', 'toubro'}.")
    print("     {'larsen', 'toubro'} is a subset of {'larsen', 'toubro', 'infotech'}, triggering 'name_variant'.")

    # 3. Load Inputs
    print("\n" + "=" * 80)
    print("LOADING DATA FOR V3 REBUILD")
    print("=" * 80)

    events_df = pd.read_parquet(EVENTS_PATH)
    print(f"Loaded index events: {len(events_df)} rows")

    eq_df = pd.read_csv(EQUITY_L_PATH)
    eq_df.columns = [c.strip() for c in eq_df.columns]
    print(f"Loaded EQUITY_L: {len(eq_df)} rows")

    with open(TRADING_CALENDAR_TXT) as f:
        cal_dates_str = [line.strip() for line in f if line.strip()]
    cal_dates = [datetime.datetime.strptime(d, "%Y-%m-%d").date() for d in cal_dates_str]
    print(f"Loaded trading calendar: {len(cal_dates)} dates ({cal_dates[0]} to {cal_dates[-1]})")

    price_df = pd.read_parquet(PRICE_EXPORT_PATH)
    print(f"Loaded price cache: {len(price_df)} bars across {price_df['symbol'].nunique()} symbols")

    # Index price bars
    price_symbol_dates = {}
    for sym, grp in price_df.groupby("symbol"):
        price_symbol_dates[sym] = set(grp["date"].values)

    price_symbol_ranges = {}
    for sym, grp in price_df.groupby("symbol"):
        price_symbol_ranges[sym] = (grp["date"].min(), grp["date"].max())

    # Build EQUITY_L lookups
    eq_df["norm_name"] = eq_df["NAME OF COMPANY"].apply(normalize_name)
    eq_norm_counts = eq_df["norm_name"].value_counts().to_dict()
    eq_duplicates = {n for n, c in eq_norm_counts.items() if c > 1}

    eq_exact_dict = {}
    for _, r in eq_df.iterrows():
        n = r["norm_name"]
        if n not in eq_exact_dict:
            eq_exact_dict[n] = []
        eq_exact_dict[n].append(r)

    eq_isin_set = set(eq_df["ISIN NUMBER"].dropna().unique())
    eq_symbol_map = {r["SYMBOL"]: r for _, r in eq_df.iterrows()}

    eq_entries = []
    for _, r in eq_df.iterrows():
        _, tokens = tokenize_and_strip(r["NAME OF COMPANY"])
        eq_entries.append({
            "symbol": r["SYMBOL"],
            "name": r["NAME OF COMPANY"],
            "isin": r["ISIN NUMBER"],
            "series": r["SERIES"],
            "listing_date": r["DATE OF LISTING"],
            "norm": r["norm_name"],
            "tokens": tokens
        })

    # Precompute per-scrip dates & actual membership intervals from event replay
    print("\n[1.4] REPLAYING ACTUAL MEMBERSHIP INTERVALS & S4 COLLISION ANALYSIS")
    covered_end_map = events_df.groupby("index")["effective_date"].max().to_dict()
    covered_start_map = events_df.groupby("index")["effective_date"].min().to_dict()

    scrip_first_seen = events_df.groupby("scrip_name")["effective_date"].min().to_dict()
    scrip_last_seen = events_df.groupby("scrip_name")["effective_date"].max().to_dict()

    # Reconstruct actual IN -> OUT segments per (index, scrip)
    scrip_index_intervals = {}
    for (idx_name, scrip), grp in events_df.groupby(["index", "scrip_name"]):
        grp_sorted = grp.sort_values("effective_date")
        intervals = []
        current_start = None
        for _, row in grp_sorted.iterrows():
            act = row["action"]
            dt = row["effective_date"]
            if act == "IN":
                if current_start is None:
                    current_start = dt
            elif act == "OUT":
                if current_start is not None:
                    intervals.append((current_start, dt))
                    current_start = None
                else:
                    # Stock was present from index start
                    intervals.append((covered_start_map[idx_name], dt))
        if current_start is not None:
            intervals.append((current_start, covered_end_map[idx_name]))
        scrip_index_intervals[(idx_name, scrip)] = intervals

    # Scrip union of actual intervals across all indices
    all_scrips = sorted(events_df["scrip_name"].unique())
    scrip_actual_expected_bars = {}
    for scrip in all_scrips:
        union_days = set()
        for idx_name in covered_end_map:
            ints = scrip_index_intervals.get((idx_name, scrip), [])
            for w_start, w_end in ints:
                for d in cal_dates:
                    if w_start <= d <= w_end:
                        union_days.add(d)
        scrip_actual_expected_bars[scrip] = union_days

    # 4. Resolve Candidates
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

        if norm_scrip in eq_duplicates:
            # S2 Duplicate Collision
            res_method = "token_match"
            conf = "low"
            ev_source = "equity_l_duplicate_collision"
            matching_rows = eq_exact_dict[norm_scrip]
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
            _, scrip_tokens = tokenize_and_strip(scrip)
            best_match = None
            best_score = 0.0
            for entry in eq_entries:
                entry_tokens = entry["tokens"]
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

    # 5. Compute S4 Collisions using actual replay intervals
    isin_to_scrips = {}
    for _, r in cand_df.iterrows():
        if r["isin"]:
            isin_to_scrips.setdefault(r["isin"], set()).add(r["scrip_name"])

    scrip_method = cand_df.set_index("scrip_name")["resolution_method"].to_dict()

    s4_flagged_weaker = {}  # weaker_scrip -> set of colliding scrips
    exact_alias_targets = {}  # exact_scrip -> set of weaker scrips colliding with it

    for isin, scrip_set in isin_to_scrips.items():
        if len(scrip_set) > 1:
            scrip_list = sorted(scrip_set)
            for i in range(len(scrip_list)):
                for j in range(i + 1, len(scrip_list)):
                    s1, s2 = scrip_list[i], scrip_list[j]
                    for idx_name in covered_end_map:
                        int1 = scrip_index_intervals.get((idx_name, s1), [])
                        int2 = scrip_index_intervals.get((idx_name, s2), [])
                        for start1, end1 in int1:
                            for start2, end2 in int2:
                                overlap_start = max(start1, start2)
                                overlap_end = min(end1, end2)
                                if overlap_start <= overlap_end:
                                    m1 = scrip_method.get(s1, "unresolved")
                                    m2 = scrip_method.get(s2, "unresolved")
                                    if m1 == "equity_l_exact" and m2 != "equity_l_exact":
                                        s4_flagged_weaker.setdefault(s2, set()).add(s1)
                                        exact_alias_targets.setdefault(s1, set()).add(s2)
                                    elif m2 == "equity_l_exact" and m1 != "equity_l_exact":
                                        s4_flagged_weaker.setdefault(s1, set()).add(s2)
                                        exact_alias_targets.setdefault(s2, set()).add(s1)
                                    else:
                                        s4_flagged_weaker.setdefault(s1, set()).add(s2)
                                        s4_flagged_weaker.setdefault(s2, set()).add(s1)

    print(f"Gate 2b S4 collision count (bounding box): 142")
    print(f"Gate 2c S4 collision weaker-evidence flagged count (actual intervals): {len(s4_flagged_weaker)}")
    print(f"Gate 2c exact-match scrips receiving informational 'alias_target_of': {len(exact_alias_targets)}")

    # 6. Build v3 Rows with Decoupled Statuses
    print("\n[1.5] BUILDING V3 SYMBOL MAP ROWS (DECOUPLED MAPPING & PRICE STATUS)")
    final_rows = []
    
    flag_counts = {}

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

        if not sym or res_method == "unresolved":
            final_rows.append({
                "scrip_name": scrip,
                "symbol": "",
                "isin": "",
                "first_seen": r["first_seen"],
                "last_seen": r["last_seen"],
                "resolution_method": "unresolved",
                "confidence": "low",
                "mapping_status": "unresolved",
                "price_status": "no_symbol",
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
            flag_counts["no_candidate"] = flag_counts.get("no_candidate", 0) + 1
            continue

        # Expected & present bars from actual replay intervals
        expected_cal_dates = scrip_actual_expected_bars[scrip]
        bars_expected = len(expected_cal_dates)
        sym_dates_str = price_symbol_dates.get(sym, set())
        bars_present = sum(1 for d in expected_cal_dates if d.strftime("%Y-%m-%d") in sym_dates_str)
        coverage_pct = round((bars_present / bars_expected * 100.0) if bars_expected > 0 else 0.0, 2)
        price_first_bar, price_last_bar = price_symbol_ranges.get(sym, ("", ""))

        # Token & name flags
        first_token_match, name_flags = compute_name_flags(scrip, eq_name)
        flags.extend(name_flags)

        # S1 Listing Date Screen
        has_s1 = False
        if eq_listing_date:
            try:
                list_dt = datetime.datetime.strptime(eq_listing_date, "%d-%b-%Y").date()
                if list_dt > (r["first_seen"] + datetime.timedelta(days=30)):
                    flags.append("listing_after_first_seen")
                    has_s1 = True
            except:
                pass

        # S2 Duplicate Name Collision
        if norm_scrip in eq_duplicates:
            matching_syms = [row["SYMBOL"] for row in eq_exact_dict[norm_scrip]]
            flags.append(f"duplicate_name_collision({','.join(matching_syms)})")

        # S3 ISIN verification
        if not isin_in_equity:
            if "external_circular" not in ev_source:
                flags.append("isin_unverified")

        # S4 Concurrent Alias Collision
        if scrip in s4_flagged_weaker:
            flags.append("concurrent_alias_collision")

        # Informational alias_target_of for exact matches
        if scrip in exact_alias_targets:
            weaker_names = sorted(exact_alias_targets[scrip])
            flags.append(f"alias_target_of({','.join(weaker_names)})")

        # S5 Predecessor Marker
        if predecessor_regex.search(scrip):
            flags.append("predecessor_marker")

        # Agent memory unsourced flag
        if res_method == "agent_memory":
            flags.append("unsourced")

        # Track flag counts
        for f in flags:
            base_f = f.split("(")[0]
            flag_counts[base_f] = flag_counts.get(base_f, 0) + 1

        # ---------------------------------------------------------------------
        # Determine price_status:
        # covered (>= 90% AND >= 60 bars), partial (30-90%), none (< 30%), inconclusive (< 60 bars), no_symbol
        # ---------------------------------------------------------------------
        if not sym:
            price_status = "no_symbol"
        elif bars_expected < 60:
            price_status = "inconclusive"
        elif coverage_pct >= 90.0:
            price_status = "covered"
        elif coverage_pct >= 30.0:
            price_status = "partial"
        else:
            price_status = "none"

        # ---------------------------------------------------------------------
        # Determine mapping_status:
        # auto requires: exact normalized name, unique EQUITY_L candidate, ISIN in EQUITY_L, no S1/S2/S4/S5 flag.
        # An S1 flag can be cleared ONLY by price evidence with >= 60 expected bars and coverage >= 90%.
        # Price status never changes mapping_status.
        # ---------------------------------------------------------------------
        is_exact = (res_method == "equity_l_exact") and (norm_scrip not in eq_duplicates)
        has_s2 = any(f.startswith("duplicate_name_collision") for f in flags)
        has_s3 = "isin_unverified" in flags
        has_s4 = "concurrent_alias_collision" in flags
        has_s5 = "predecessor_marker" in flags
        has_blocking_token_flag = ("first_token_mismatch" in flags) or ("name_mismatch" in flags) or ("unsourced" in flags)

        s1_cleared = False
        if has_s1:
            if bars_expected >= 60 and coverage_pct >= 90.0:
                s1_cleared = True

        can_be_auto = (
            is_exact
            and isin_in_equity
            and (not has_s2)
            and (not has_s3)
            and (not has_s4)
            and (not has_s5)
            and (not has_blocking_token_flag)
            and ((not has_s1) or s1_cleared)
        )

        mapping_status = "auto" if can_be_auto else "proposed"

        final_rows.append({
            "scrip_name": scrip,
            "symbol": sym,
            "isin": isin,
            "first_seen": r["first_seen"],
            "last_seen": r["last_seen"],
            "resolution_method": res_method,
            "confidence": conf,
            "mapping_status": mapping_status,
            "price_status": price_status,
            "status": mapping_status,  # backwards compatibility
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

    v3_df = pd.DataFrame(final_rows)
    cols = [
        "scrip_name", "symbol", "isin", "first_seen", "last_seen", "resolution_method", "confidence",
        "mapping_status", "price_status", "status",
        "eq_name", "eq_series", "eq_listing_date", "isin_in_equity_l", "name_similarity", "first_token_match",
        "price_first_bar", "price_last_bar", "bars_expected", "bars_present", "coverage_pct", "flags", "evidence_source"
    ]
    v3_df = v3_df[cols]

    # 7. Archiving and Output Writing
    print("\n" + "=" * 80)
    print("[1.6] ARCHIVING & OUTPUT EXPORTS")
    print("=" * 80)

    # Check and archive v2b
    if os.path.exists(CURRENT_SYMBOL_MAP):
        v2b_sha = sha256_file(CURRENT_SYMBOL_MAP)
        shutil.copy2(CURRENT_SYMBOL_MAP, ARCHIVE_V2B_PARQUET)
        print(f"Archived current symbol map to {ARCHIVE_V2B_PARQUET}")
        print(f"  SHA-256 (v2b): {v2b_sha}")

        # Also export v2b to data_csv
        v2b_df = pd.read_parquet(ARCHIVE_V2B_PARQUET)
        v2b_csv_path = os.path.join(DELIVERABLES_CSV_DIR, "symbol_map_v2b.csv")
        v2b_df.to_csv(v2b_csv_path, index=False)
        print(f"  Exported full v2b CSV: {v2b_csv_path} ({len(v2b_df)} rows)")
    else:
        v2b_df = None

    # Write v3 parquet
    pq.write_table(pa.Table.from_pandas(v3_df), OUTPUT_V3_PARQUET)
    v3_sha = sha256_file(OUTPUT_V3_PARQUET)
    print(f"\nWrote rebuilt v3 symbol map to {OUTPUT_V3_PARQUET} ({len(v3_df)} rows)")
    print(f"  SHA-256 (v3): {v3_sha}")

    # Export full v3 CSV
    v3_csv_path = os.path.join(DELIVERABLES_CSV_DIR, "symbol_map_v3.csv")
    v3_df.to_csv(v3_csv_path, index=False)
    print(f"  Exported full v3 CSV: {v3_csv_path} ({len(v3_df)} rows)")

    # 8. Re-run 22 Canaries
    print("\n" + "=" * 80)
    print("CANARY REGRESSION VERIFICATION (22 CANARIES)")
    print("=" * 80)

    canaries_2b = pd.read_csv(CANARIES_2B_PATH)
    canary_results = []
    regressions = []

    v3_map_dict = v3_df.set_index("scrip_name").to_dict(orient="index")

    for _, c_row in canaries_2b.iterrows():
        scrip = c_row["scrip_name"]
        exp_reason = c_row["expected_reason"]
        
        if scrip not in v3_map_dict:
            res_row = {
                "scrip_name": scrip,
                "symbol": "NOT_FOUND",
                "isin": "",
                "mapping_status": "unresolved",
                "price_status": "no_symbol",
                "resolution_method": "unresolved",
                "flags": "not_in_map",
                "expected_reason": exp_reason,
                "test_result": "FAIL"
            }
            regressions.append(scrip)
        else:
            r = v3_map_dict[scrip]
            is_non_auto = r["mapping_status"] in ["proposed", "unresolved"]
            test_res = "PASS" if is_non_auto else "REGRESSION_AUTO"
            if not is_non_auto:
                regressions.append(scrip)

            res_row = {
                "scrip_name": scrip,
                "symbol": r["symbol"],
                "isin": r["isin"],
                "mapping_status": r["mapping_status"],
                "price_status": r["price_status"],
                "resolution_method": r["resolution_method"],
                "flags": r["flags"],
                "expected_reason": exp_reason,
                "test_result": test_res
            }
        canary_results.append(res_row)

    canary_df = pd.DataFrame(canary_results)
    canaries_csv_path = os.path.join(DELIVERABLES_CSV_DIR, "canaries_2c.csv")
    canary_df.to_csv(canaries_csv_path, index=False)
    print(f"Exported canaries test result to {canaries_csv_path}")

    print("\nCanary Evaluation Results:")
    c_header = f"| {'scrip_name':<35} | {'symbol':<12} | {'map_status':<11} | {'price_status':<13} | {'flags':<35} | {'result'} |"
    c_sep = "|" + "-"*37 + "|" + "-"*14 + "|" + "-"*13 + "|" + "-"*15 + "|" + "-"*37 + "|--------|"
    print(c_header)
    print(c_sep)
    for _, cr in canary_df.iterrows():
        print(f"| {cr['scrip_name']:<35} | {cr['symbol']:<12} | {cr['mapping_status']:<11} | {cr['price_status']:<13} | {cr['flags'][:35]:<35} | {cr['test_result']:<6} |")

    if regressions:
        print(f"\nFATAL: Canary regressions found! Scrips becoming auto: {regressions}")
    else:
        print(f"\nAll 22 canaries successfully PASSED (0 regressions to 'auto').")

    # 9. Before / After Comparison Tables
    print("\n" + "=" * 80)
    print("BEFORE / AFTER SUMMARY COMPARISON")
    print("=" * 80)

    if v2b_df is not None:
        print("\n--- Status Comparison ---")
        print(f"  Gate 2b single status:")
        for s, c in v2b_df["status"].value_counts().items():
            print(f"    {s:<15}: {c:4d} ({c/len(v2b_df)*100:.1f}%)")

        print(f"\n  Gate 2c mapping_status:")
        for s, c in v3_df["mapping_status"].value_counts().items():
            print(f"    {s:<15}: {c:4d} ({c/len(v3_df)*100:.1f}%)")

        print(f"\n  Gate 2c price_status:")
        for s, c in v3_df["price_status"].value_counts().items():
            print(f"    {s:<15}: {c:4d} ({c/len(v3_df)*100:.1f}%)")

        print(f"\n--- Flag Counts in Gate 2c v3 ---")
        for f, c in sorted(flag_counts.items(), key=lambda x: -x[1]):
            print(f"  {f:<35}: {c:4d}")

    # Copy script to deliverables/gate_2c/scripts/
    shutil.copy2(__file__, os.path.join(DELIVERABLES_SCRIPTS_DIR, "step1_v3_rebuild.py"))
    print(f"\nCopied script to {os.path.join(DELIVERABLES_SCRIPTS_DIR, 'step1_v3_rebuild.py')}")
    print("\n" + "=" * 80)
    print("STEP 1 COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
