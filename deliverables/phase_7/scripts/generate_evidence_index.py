#!/usr/bin/env python3
"""
deliverables/phase_7/scripts/generate_evidence_index.py
Phase 7A — EVIDENCE_INDEX.tsv and SHA256SUMS Generator

Generates cryptographic checksums and evidence manifests for Phase 7A deliverables.
"""

import hashlib
from pathlib import Path

BASE_DIR = Path("/storage/emulated/0/Documents/Project MIP")
DELIV_DIR = BASE_DIR / "deliverables/phase_7"

def get_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def what_it_proves(rel_path: str) -> str:
    p = rel_path
    if "PHASE_7C_RULING.md" in p:
        return "Final Auditor Ruling formally accepting Gates 17-25 and clearing Standing Gate HALT-8C"
    if "PHASE_7B_RULING.md" in p:
        return "Final Auditor Ruling formally accepting Gates 11-16 and clearing Standing Gate HALT-8B"
    if "PHASE_7A_RULING.md" in p:
        return "Final Auditor Ruling formally accepting Gates 1-10 and clearing Standing Gate HALT-8A"
    if "NEXT_TASK.md" in p:
        return "Phase 7 active directive specifying the 32-Gate Institutional Framework and Phase 7A roadmap"
    if "DIGEST.md" in p:
        return "Phase 7A Executive Digest and verification tearsheet across Gates 1 to 10"
    if "task_list.md" in p:
        return "Phase 7A execution roadmap tracking Tasks 1-5 with Standing Gate HALT-8A open"
    if "SHA256SUMS.txt" in p:
        return "Cryptographic SHA-256 manifest of all Phase 7A deliverables"
    if "data_csv/nifty_500_benchmark_proxy.csv" in p:
        return "Synthesized continuous NIFTY 500 benchmark proxy with 100% calendar alignment across 4,857 trading sessions"
    if "data_csv/gates_1_4_integrity_audit.csv" in p:
        return "Verification records for Gates 1-4: point-in-time universe, graveyard scrip liquidation, lookahead proof, split adjustments"
    if "data_csv/gates_9_10_execution_constraints.csv" in p:
        return "Verification records for Gates 9-10: execution timing models (Open, VWAP, t+2) and circuit limit tradability guard"
    if "data_csv/gates_5_8_cost_stress_matrix.csv" in p:
        return "Transaction friction stress matrix (1x, 2x, 3x) and slippage sensitivity ladder (0.10% to 1.00%)"
    if "data_csv/daily_equity_curves.csv" in p:
        return "Standardized daily equity curves, cash balances, invested capital, benchmark values, and drawdowns (2,636 days)"
    if "data_csv/monthly_returns.csv" in p:
        return "Standardized monthly returns table with strategy return, benchmark return, and excess return (128 months)"
    if "data_csv/trade_log.csv" in p:
        return "Comprehensive itemized trade log with signal dates, execution dates, prices, friction costs, and exit reasons (1,134 trades)"
    if "data_csv/monthly_holdings_snapshots.parquet" in p:
        return "Monthly rebalance portfolio holdings snapshots detailing constituent ranks, share counts, market values, and weights"
    if "data_csv/gates_1_to_10_summary.csv" in p:
        return "Master consolidated compliance summary table certifying PASS status across Gates 1 to 10"
    if "raw/init_phase7_engine.log" in p:
        return "Raw stdout execution log of Task 1 engine configuration and benchmark synthesis"
    if "raw/test_data_integrity.log" in p:
        return "Raw stdout execution log of Task 2 data integrity and survivorship audit (Gates 1-4)"
    if "raw/test_execution_constraints.log" in p:
        return "Raw stdout execution log of Task 3 execution models and circuit limits (Gates 9-10)"
    if "raw/test_cost_sensitivity.log" in p:
        return "Raw stdout execution log of Task 4 cost stress matrix and portfolio deliverables generation"
    if "scripts/init_phase7_engine.py" in p:
        return "Engine configuration and continuous benchmark proxy ingestion builder script"
    if "scripts/test_data_integrity.py" in p:
        return "Data integrity, graveyard survivorship, lookahead bias, and corporate action audit script"
    if "scripts/test_execution_constraints.py" in p:
        return "Execution delay models and exchange circuit limit simulation script"
    if "scripts/test_cost_sensitivity.py" in p:
        return "Cost stress test, slippage ladder, and standardized portfolio deliverable exporter script"
    if "scripts/generate_evidence_index.py" in p:
        return "Phase 7A evidence manifest and cryptographic checksum generator script"
    if "data/adjusted_bhavcopy_max_2007_2026.parquet" in p:
        return "Certified maximum Bhavcopy ground-truth dataset (2007-2026, 2,137,630 bars across 1,039 symbols)"
    if "data/symbol_map.parquet" in p:
        return "Point-in-time symbol mapping table providing active constituent resolution (1,614 scrips)"
    if "data/benchmarks/NIFTY_50.csv" in p:
        return "Official NIFTY 50 index daily historical series"
    if "data/benchmarks/NIFTY_100.csv" in p:
        return "Official NIFTY 100 index daily historical series providing pre-2007 warmup coverage"
    if "data/verification/survivorship_graveyard.csv" in p:
        return "Audited survivorship graveyard register containing 1,209 vanished / delisted equities"
    if "DIGEST_PHASE_7B.md" in p:
        return "Phase 7B Executive Digest and verification tearsheet across Gates 11 to 16"
    if "gate11_is_oos_results.csv" in p:
        return "In-Sample (2007-2015) vs Out-of-Sample (2016-2026) split performance audit proving temporal generalizability (Gate 11)"
    if "gate12_walk_forward_matrix.csv" in p:
        return "14-year rolling walk-forward test matrix (5y rolling train / 1y forward test) proving 71.4% win rate over benchmark (Gate 12)"
    if "gate13_paper_trading_calibration.csv" in p:
        return "12-month forward simulated paper trading calibration (2025-2026) proving execution tracking error and drag ratio (Gate 13)"
    if "gate14_parameter_plateau_grid.csv" in p:
        return "54-combination multi-dimensional parameter plateau grid proving broad alpha stability without cliff-edges (Gate 14)"
    if "gate15_rebalance_date_sensitivity.csv" in p:
        return "Rebalance-date sensitivity across 5 monthly execution schedules proving calendar anomaly invariance (Gate 15)"
    if "gate16_universe_sensitivity.csv" in p:
        return "Universe breadth sensitivity across NIFTY 50, Next 50, Midcap 150, Smallcap 250, and 500 (Gate 16)"
    if "gates_11_16_summary.csv" in p:
        return "Master consolidated compliance summary table certifying PASS status across Gates 11 to 16"
    if "scripts/test_is_oos_split.py" in p:
        return "In-Sample vs Out-of-Sample split test runner script (Gate 11)"
    if "scripts/test_walk_forward.py" in p:
        return "Walk-forward rolling analysis test runner script (Gate 12)"
    if "scripts/test_parameter_plateau.py" in p:
        return "Multi-dimensional parameter plateau grid evaluator script (Gate 14)"
    if "scripts/test_rebalance_date_sensitivity.py" in p:
        return "Rebalance-date and calendar sensitivity test runner script (Gate 15)"
    if "scripts/test_universe_and_paper_trading.py" in p:
        return "Universe breadth sensitivity and simulated paper trading calibration script (Gates 16 & 13)"
    if "raw/test_is_oos_split.log" in p:
        return "Raw stdout execution log of Task 1 In-Sample / Out-of-Sample split test (Gate 11)"
    if "raw/test_walk_forward.log" in p:
        return "Raw stdout execution log of Task 2 Walk-Forward rolling analysis (Gate 12)"
    if "raw/test_parameter_plateau.log" in p:
        return "Raw stdout execution log of Task 3 Parameter Plateau sensitivity grid (Gate 14)"
    if "raw/test_rebalance_date_sensitivity.log" in p:
        return "Raw stdout execution log of Task 4 Rebalance-Date sensitivity test (Gate 15)"
    if "raw/test_universe_and_paper_trading.log" in p:
        return "Raw stdout execution log of Task 5 Universe breadth and paper trading test (Gates 16 & 13)"
    if "DIGEST_PHASE_7C.md" in p:
        return "Phase 7C Executive Digest and verification tearsheet across Gates 17 to 25 (Macro Regimes, Monte Carlo, Risk Decomposition, Expectancy & Statistical Significance)"
    if "gate17_macro_regimes.csv" in p:
        return "Quantitative performance and drawdown tearsheet across 6 distinct Indian macroeconomic regimes (Gate 17)"
    if "gate18_random_monte_carlo.csv" in p:
        return "1,000-run random top-20 portfolio selection Monte Carlo control proving alpha distinct from random luck (Gate 18)"
    if "gates_19_21_risk_decomposition.csv" in p:
        return "Benchmark risk decomposition and risk-adjusted ratios: Jensen's Alpha, Beta, Tracking Error, IR, Sharpe, Sortino, Calmar (Gates 19-21)"
    if "gate21_drawdown_episodes.csv" in p:
        return "Non-parametric daily underwater analysis detailing all 81 discrete drawdown episodes and recovery durations (Gate 21)"
    if "gate22_trade_statistics.csv" in p:
        return "Aggregate trade statistics, win rate, profit factor, win/loss payoff ratio, and mathematical expectancy (Gate 22)"
    if "gate22_closed_trades_itemized.csv" in p:
        return "Itemized ledger of all 557 closed round-trip trades with entry/exit dates, prices, friction costs, and realized PnL (Gate 22)"
    if "gates_23_25_statistical_significance.csv" in p:
        return "Statistical significance verification records: Newey-West HAC t-stat, Stationary Block Bootstrap CI, and Deflated Sharpe Ratio (Gates 23-25)"
    if "gates_17_25_summary.csv" in p:
        return "Master consolidated compliance summary table certifying PASS status across Gates 17 to 25"
    if "scripts/test_macro_regimes.py" in p:
        return "Macroeconomic regimes stress test runner script across 6 historical Indian market eras (Gate 17)"
    if "scripts/test_random_monte_carlo.py" in p:
        return "1,000-run random top-20 stock selection Monte Carlo simulation runner script (Gate 18)"
    if "scripts/test_benchmark_and_risk.py" in p:
        return "Jensen's Alpha, Beta, IR, Sharpe, Sortino, Calmar, and drawdown episode analysis script (Gates 19-21)"
    if "scripts/test_trade_statistics.py" in p:
        return "Trade statistics, win/loss payoff ratio, and mathematical expectancy analysis script (Gate 22)"
    if "scripts/test_statistical_significance.py" in p:
        return "Newey-West HAC, Stationary Block Bootstrap, and Deflated Sharpe Ratio runner script (Gates 23-25)"
    if "scripts/compile_phase7c_summary.py" in p:
        return "Master consolidated summary table generator script for Gates 17-25"
    if "raw/test_macro_regimes.log" in p:
        return "Raw stdout execution log of Task 1 Macro Regimes stress test (Gate 17)"
    if "raw/test_random_monte_carlo.log" in p:
        return "Raw stdout execution log of Task 2 Random Top-20 Monte Carlo control (Gate 18)"
    if "raw/test_benchmark_and_risk.log" in p:
        return "Raw stdout execution log of Task 3 Benchmark decomposition and risk metrics (Gates 19-21)"
    if "raw/test_trade_statistics.log" in p:
        return "Raw stdout execution log of Task 4 Trade statistics and expectancy analysis (Gate 22)"
    if "raw/test_statistical_significance.log" in p:
        return "Raw stdout execution log of Task 5 Statistical significance and multiple-testing deflation (Gates 23-25)"
    # Phase 7D deliverables
    if "DIGEST_PHASE_7D.md" in p:
        return "Phase 7D Executive Digest and verification tearsheet for Gates 26-32 and is_proven ruling"
    if "data_csv/gate26_component_attribution.csv" in p:
        return "Empirical component attribution and 5-step ablation study verifying non-redundant value-add (Gate 26)"
    if "data_csv/gates_27_28_buffer_and_filter.csv" in p:
        return "Exit rank buffer sensitivity and market regime filter optimization records (Gates 27, 28)"
    if "data_csv/gates_29_30_volar_and_retracement.csv" in p:
        return "Volar ranking vs raw return and 50% retracement in mid/smallcap universes evaluation (Gates 29, 30)"
    if "data_csv/gate31_capacity_liquidity.csv" in p:
        return "Portfolio capacity, order ADV distribution, and institutional liquidity constraints across AUM tiers (Gate 31)"
    if "data_csv/gate32_etf_variant.csv" in p:
        return "Multi-asset ETF basket momentum rotation variant evaluation vs NIFTY 50 (Gate 32)"
    if "data_csv/gates_1_to_32_master_compliance.csv" in p:
        return "Master institutional compliance matrix certifying 32/32 gates PASS across Phases 7A, 7B, 7C, 7D"
    if "data_csv/master_strategy_proven_results.json" in p:
        return "Programmatic JSON tearsheet certifying 16/16 criteria and delivering PROVEN INSTITUTIONAL GO ruling"
    if "scripts/test_component_attribution.py" in p:
        return "Sequential component attribution and ablation study test script (Gate 26)"
    if "scripts/test_buffer_and_market_filters.py" in p:
        return "Exit rank buffer and market regime filter optimization test script (Gates 27, 28)"
    if "scripts/test_volar_and_retracement.py" in p:
        return "Volar ranking and retracement threshold sensitivity test script (Gates 29, 30)"
    if "scripts/test_capacity_and_liquidity.py" in p:
        return "Portfolio capacity and ADV liquidity constraints test script (Gate 31)"
    if "scripts/test_etf_variant.py" in p:
        return "Multi-asset ETF basket momentum rotation test script (Gate 32)"
    if "scripts/run_master_proven_gate.py" in p:
        return "Master automated is_proven(results) institutional decision engine (Gate 32 + Synthesis)"
    if "raw/test_component_attribution.log" in p:
        return "Raw stdout execution log of Task 1 Component Attribution study (Gate 26)"
    if "raw/test_buffer_and_market_filters.log" in p:
        return "Raw stdout execution log of Task 2 Exit Buffer and Market Filter optimization (Gates 27, 28)"
    if "raw/test_volar_and_retracement.log" in p:
        return "Raw stdout execution log of Task 3 Volar and Retracement thresholds (Gates 29, 30)"
    if "raw/test_capacity_and_liquidity.log" in p:
        return "Raw stdout execution log of Task 4 Capacity and Liquidity constraints (Gate 31)"
    if "raw/test_etf_variant.log" in p:
        return "Raw stdout execution log of Task 5 Multi-Asset ETF variant (Gate 32)"
    if "raw/run_master_proven_gate.log" in p:
        return "Raw stdout execution log of Task 6 Master is_proven institutional decision engine"
    return "Artifact supporting Phase 7 institutional verification"

def main():
    rows = []
    files = []

    # 1. Deliverables directory files
    for f in sorted(DELIV_DIR.glob("**/*")):
        if f.is_file() and f.name not in ["EVIDENCE_INDEX.tsv", "SHA256SUMS.txt"]:
            files.append(f)

    # 2. Core data dependencies
    for f in [
        BASE_DIR / "data/adjusted_bhavcopy_max_2007_2026.parquet",
        BASE_DIR / "data/symbol_map.parquet",
        BASE_DIR / "data/benchmarks/NIFTY_50.csv",
        BASE_DIR / "data/benchmarks/NIFTY_100.csv",
        BASE_DIR / "data/verification/survivorship_graveyard.csv"
    ]:
        if f.exists() and f.is_file():
            files.append(f)

    for f in sorted(files, key=lambda x: str(x.relative_to(BASE_DIR))):
        rel_p = str(f.relative_to(BASE_DIR))
        size = f.stat().st_size
        sha = get_sha256(f)
        desc = what_it_proves(rel_p)
        rows.append(f"{rel_p}\t{size}\t{sha}\t{desc}")

    out_tsv = DELIV_DIR / "EVIDENCE_INDEX.tsv"
    with open(out_tsv, "w", encoding="utf-8") as out:
        out.write("path\tbytes\tsha256\twhat_it_proves\n")
        for r in rows:
            out.write(r + "\n")

    print(f"Generated {out_tsv} ({out_tsv.stat().st_size:,} bytes, {len(rows)} entries).")

    # 3. Generate SHA256SUMS.txt for all files in deliverables/phase_7/
    sha_lines = []
    for f in sorted(DELIV_DIR.glob("**/*")):
        if f.is_file() and f.name != "SHA256SUMS.txt":
            rel_p = str(f.relative_to(DELIV_DIR))
            sha = get_sha256(f)
            sha_lines.append(f"{sha}  {rel_p}")

    out_sha = DELIV_DIR / "SHA256SUMS.txt"
    with open(out_sha, "w", encoding="utf-8") as out:
        for line in sha_lines:
            out.write(line + "\n")

    print(f"Generated {out_sha} ({out_sha.stat().st_size:,} bytes, {len(sha_lines)} checksums).")

if __name__ == "__main__":
    main()
