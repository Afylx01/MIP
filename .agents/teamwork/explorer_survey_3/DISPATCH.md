## 2026-09-24T01:21:58Z

You are Explorer 3 (Symbol Map and Review Tooling Surveyor) for Phase 5.5 Gate 2b.
Your working directory is /storage/emulated/0/Documents/Project MIP/.agents/teamwork/explorer_survey_3.
You are a READ-ONLY exploration agent. DO NOT modify any codebase files.
Read the user request from /storage/emulated/0/Documents/Project MIP/.agents/teamwork/ORIGINAL_REQUEST.md (specifically R3, R4, R5).

Your specific investigation scope:
1. Symbol Map generation and resolution logic:
   - Identify current scripts / modules that generate symbol_map.parquet (e.g. scripts/build_symbol_map.py or in src/).
   - Check where KNOWN_CORPORATE_RENAMES is defined, how corporate renames and aliases are handled.
   - Map out the required changes for R3: archiving v1, resolution methods (equity_l_exact, token_match, agent_memory, user_override, unresolved), new columns (eq_name, eq_series, eq_listing_date, isin_in_equity_l, name_similarity, first_token_match, price_first_bar, price_last_bar, bars_expected, bars_present, coverage_pct, flags, evidence_source), and screens S1 through S6.
   - Check how the auto rule (exact normalized name match + unique EQUITY_L candidate + ISIN in EQUITY_L + no S1/S4/S5 flag + coverage_pct >= 90) and demotion logic should be implemented.
2. Review tooling and refusal hardening:
   - Check if scripts/review_symbol_map.py and scripts/apply_symbol_map_review.py exist or need to be rewritten/fixed.
   - Inspect their refusal paths: invalid action, refuse auto, refuse empty symbol/ISIN, refuse flagged row without approval_note, key match verification (scrip_name, symbol, isin), backup map, appending to data/symbol_map_changes.parquet.
3. Canary tests:
   - Check if data/verification/canaries_2b.csv exists or existing canary tests in tests/ or data/verification/. What are the 15+ canonical edge cases mentioned in the prompt/prior phases?

Write your comprehensive findings to /storage/emulated/0/Documents/Project MIP/.agents/teamwork/explorer_survey_3/survey_report.md and your handoff to /storage/emulated/0/Documents/Project MIP/.agents/teamwork/explorer_survey_3/handoff.md. Include a progress.md with timestamps. When done, send a message to the orchestrator.
