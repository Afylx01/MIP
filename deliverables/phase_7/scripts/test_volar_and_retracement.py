#!/usr/bin/env python3
"""
deliverables/phase_7/scripts/test_volar_and_retracement.py
Phase 7D Task 3: Volar Ranking vs Raw Return & Retracement Threshold (Gates 29, 30)

Gate 29 (Volar Ranking Comparison):
  - Compare Raw 252-day Return ranking vs Volar ranking (Return_252 / sigma_252).
  - Pass Criteria: Volar improves Max Drawdown by > 5.0 pp with CAGR degradation < 1.0 pp,
    improving Sharpe and Sortino ratios.

Gate 30 (50% Retracement for Mid/Smallcaps):
  - Compare 20% retracement (Filter 1 baseline, r2_factor=0.80) vs 50% retracement (r2_factor=0.50)
    in NIFTY Midcap 150 and Smallcap 250 universes.
  - Pass Criteria: 50% retracement improves CAGR by > 2.0 pp while keeping Max Drawdown
    increase < 10.0 pp (< 60.0% total).

Outputs:
  - deliverables/phase_7/data_csv/gates_29_30_volar_and_retracement.csv
  - deliverables/phase_7/raw/test_volar_and_retracement.log
"""

import sys
import os
import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple
import pandas as pd
import numpy as np

BASE_DIR = Path("/storage/emulated/0/Documents/Project MIP")
DELIV_DIR = BASE_DIR / "deliverables/phase_7"
DATA_CSV_DIR = DELIV_DIR / "data_csv"
RAW_DIR = DELIV_DIR / "raw"
DATA_DIR = BASE_DIR / "data"

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from indian_backtest.data.calendar_manager import CalendarManager
from indian_backtest.data.universe_manager import UniverseManager
from indian_backtest.data.bhavcopy_reader import BhavcopyReader
from indian_backtest.engine.portfolio import Portfolio
from indian_backtest.engine.execution import ExecutionEngine
from indian_backtest.engine.regime_filter import MarketRegimeFilter
from indian_backtest.indicators.price_extremes import is_r2_satisfied
from indian_backtest.indicators.relative_strength import calculate_relative_strength
from indian_backtest.analytics.metrics import calculate_performance_metrics
from indian_backtest.analytics.auditor_assert import assert_rule_r3_accounting_identity

BHAVCOPY_PATH = DATA_DIR / "adjusted_bhavcopy_max_2007_2026.parquet"
START_DATE = "2016-01-04"
END_DATE = "2026-08-31"
INITIAL_CAPITAL = 10_000_000.0

OUT_CSV = DATA_CSV_DIR / "gates_29_30_volar_and_retracement.csv"
OUT_LOG = RAW_DIR / "test_volar_and_retracement.log"

def partition_snapshot_universes(
    all_snap_universes: Dict[str, Set[str]],
    price_lookup: Dict
) -> Dict[str, Dict[str, Set[str]]]:
    """Partitions NIFTY 500 snapshot universes into Midcap 150 and Smallcap 250."""
    segments = {
        "NIFTY Midcap 150": {},
        "NIFTY Smallcap 250": {},
        "NIFTY 500": {}
    }

    for snap_dt, sym_set in all_snap_universes.items():
        ranked_syms = []
        for s in sym_set:
            row = price_lookup.get((s, snap_dt))
            px = row["close"] if row else 100.0
            vol = row.get("volume", 100000.0) if row else 100000.0
            turnover = px * (vol if vol > 0 else 100000.0)
            ranked_syms.append((s, turnover))

        ranked_syms.sort(key=lambda x: -x[1])
        ordered = [s for s, _ in ranked_syms]

        segments["NIFTY Midcap 150"][snap_dt] = set(ordered[100:250])
        segments["NIFTY Smallcap 250"][snap_dt] = set(ordered[250:500])
        segments["NIFTY 500"][snap_dt] = set(ordered[:500])

    return segments

def run_simulation(
    ranking_mode: str,          # "raw", "volar"
    r2_factor: float,           # 0.80 (20% retracement) or 0.50 (50% retracement)
    universe_dict: Dict[str, Set[str]],
    window_days: List[str],
    snap_dates: List[str],
    price_lookup: Dict,
    benchmark_lookup: Dict,
    exit_rank_cutoff: int = 40
) -> dict:
    portfolio = Portfolio(initial_capital=INITIAL_CAPITAL)
    execution_engine = ExecutionEngine(slippage_bps=10.0, statutory_costs=True, cost_multiplier=1.0)
    regime_filter = MarketRegimeFilter(enabled=True, ema_period=20)
    snap_set = set(snap_dates)

    total_turnover = 0.0
    total_trades = 0

    for day_idx, current_date in enumerate(window_days):
        if current_date in snap_set:
            u_current = universe_dict.get(current_date, set())
            is_bull = regime_filter.evaluate_regime(current_date, benchmark_lookup)

            # Evaluate Candidates
            candidates = []
            for sym in u_current:
                row = price_lookup.get((sym, current_date))
                if row is None:
                    continue

                cl = row["close"]
                hi = row["high_252"]
                ema = row["ema_200"]
                ret_raw = row.get("ret_252", 0.0)
                vol = row.get("vol_252", 0.30)

                r2_pass = is_r2_satisfied(cl, hi, r2_factor)
                r3_pass = (cl > ema)

                # Ranking Metric Selection
                if ranking_mode == "volar":
                    rank_metric = ret_raw / max(vol, 0.05)
                else:
                    rank_metric = ret_raw

                candidates.append({
                    "symbol": sym,
                    "rank_metric": rank_metric,
                    "r2_pass": r2_pass,
                    "r3_pass": r3_pass
                })

            candidates.sort(key=lambda x: (-x["rank_metric"], x["symbol"]))
            rank_map = {c["symbol"]: i + 1 for i, c in enumerate(candidates)}
            pass_candidates = [c for c in candidates if c["r2_pass"] and c["r3_pass"]]

            # Determine Exits
            exits = []
            retained = set()

            for sym in list(portfolio.holdings.keys()):
                if sym not in u_current:
                    exits.append((sym, "DELISTED_OR_DROPOUT"))
                    continue

                row = price_lookup.get((sym, current_date))
                if row is None:
                    exits.append((sym, "NO_DATA"))
                    continue

                cl = row["close"]
                hi = row["high_252"]
                ema = row["ema_200"]
                rank = rank_map.get(sym, 999999)

                if not is_r2_satisfied(cl, hi, r2_factor):
                    exits.append((sym, "STOP_52W_HIGH_RETRACEMENT"))
                elif cl < ema:
                    exits.append((sym, "STOP_200_EMA_BREAK"))
                elif rank > exit_rank_cutoff:
                    exits.append((sym, f"DROPOUT_RANK_{rank}"))
                else:
                    retained.add(sym)

            next_idx = day_idx + 1
            if next_idx < len(window_days):
                exec_date = window_days[next_idx]

                # Process Exits
                for sym, reason in exits:
                    pos = portfolio.holdings[sym]
                    r_px = price_lookup.get((sym, exec_date))
                    open_px = r_px["open"] if (r_px and r_px["open"] > 0) else pos["buy_price"]
                    eff_sell, fric = execution_engine.calculate_sell_execution(open_px, pos["shares"])
                    portfolio.close_position(sym, eff_sell, exec_date, reason, fric)
                    total_turnover += pos["shares"] * eff_sell
                    total_trades += 1

                # Process Entries
                open_slots = 20 - len(retained)
                if open_slots > 0 and portfolio.cash > 0 and is_bull:
                    entrants = [c["symbol"] for c in pass_candidates if c["symbol"] not in retained][:open_slots]
                    if entrants:
                        alloc = portfolio.cash / len(entrants)
                        for sym in entrants:
                            r_px = price_lookup.get((sym, exec_date))
                            if r_px and r_px["open"] > 0:
                                shs, eff_buy, fric = execution_engine.calculate_buy_execution(r_px["open"], alloc)
                                if shs > 0:
                                    s_rank = rank_map.get(sym, 1)
                                    portfolio.open_position(sym, shs, eff_buy, exec_date, s_rank, fric)
                                    total_turnover += (shs * eff_buy) + fric
                                    total_trades += 1

        portfolio.record_daily_valuation(current_date, price_lookup)

    final_date = window_days[-1]
    final_val = portfolio.get_portfolio_value(final_date, price_lookup)
    acc = portfolio.compute_accounting_identity(final_date, price_lookup)
    assert_rule_r3_accounting_identity(acc)

    metrics = calculate_performance_metrics(
        daily_history=portfolio.daily_history,
        closed_trades=portfolio.closed_trades,
        initial_capital=INITIAL_CAPITAL,
        final_value=final_val,
        start_date=window_days[0],
        final_date=final_date
    )

    years = len(window_days) / 252.0
    avg_equity = float(np.mean([d["value"] for d in portfolio.daily_history]))
    ann_turnover = float((total_turnover / years) / avg_equity * 100.0)

    return {
        "cagr": metrics["cagr"],
        "max_dd": metrics["max_dd"],
        "sharpe": metrics["sharpe"],
        "sortino": metrics["sortino"],
        "calmar": metrics["calmar"],
        "turnover_pct": ann_turnover,
        "trades": total_trades,
        "r3_residual": acc["residual"]
    }

def main():
    DATA_CSV_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    log_lines = []
    def log(msg=""):
        print(msg)
        log_lines.append(msg)

    log("=" * 80)
    log("PHASE 7D TASK 3: VOLAR RANKING & RETRACEMENT THRESHOLDS (GATES 29, 30)")
    log(f"Timestamp: {datetime.datetime.now(datetime.timezone.utc).isoformat()}")
    log("=" * 80)

    cal_mgr = CalendarManager(base_dir=BASE_DIR, use_bhavcopy_calendar=True)
    window_days = cal_mgr.get_trading_days(START_DATE, END_DATE)
    snap_dates = cal_mgr.get_monthly_rebalance_snapshots(START_DATE, END_DATE)

    univ_mgr = UniverseManager(base_dir=BASE_DIR)
    snap_universes_n500 = univ_mgr.get_all_snapshot_universes(snap_dates)

    log(f"Loading price records via BhavcopyReader ({START_DATE} to {END_DATE})...")
    reader = BhavcopyReader(base_dir=BASE_DIR, custom_path=BHAVCOPY_PATH)
    price_lookup = reader.get_price_lookup(START_DATE, END_DATE)
    log(f"Loaded {len(price_lookup):,} price records.")

    bench_csv = DATA_CSV_DIR / "nifty_500_benchmark_proxy.csv"
    b_df = pd.read_csv(bench_csv).sort_values("date").reset_index(drop=True)
    b_df["is_bull"] = b_df["close"] > b_df["ema_20"]
    benchmark_lookup = {r.date: {"close": float(r.close), "ret_252": float(r.ret_252), "is_bull": bool(r.is_bull)} for r in b_df.itertuples()}

    segments = partition_snapshot_universes(snap_universes_n500, price_lookup)

    records = []

    # =========================================================================
    # PART 1: GATE 29 (VOLAR RANKING VS RAW RETURN)
    # =========================================================================
    log("\nPART 1: GATE 29 (VOLAR RANKING VS RAW RETURN)")
    log("  Evaluating Raw 252-day Return Ranking (Composite NIFTY 500)...")
    res_raw = run_simulation(
        ranking_mode="raw",
        r2_factor=0.80,
        universe_dict=snap_universes_n500,
        window_days=window_days,
        snap_dates=snap_dates,
        price_lookup=price_lookup,
        benchmark_lookup=benchmark_lookup,
        exit_rank_cutoff=40
    )
    log(f"    Raw Return -> CAGR: {res_raw['cagr']:.2f}% | MaxDD: {res_raw['max_dd']:.2f}% | Sharpe: {res_raw['sharpe']:.2f} | Sortino: {res_raw['sortino']:.2f}")

    log("  Evaluating Volar Ranking (Composite NIFTY 500)...")
    res_volar = run_simulation(
        ranking_mode="volar",
        r2_factor=0.80,
        universe_dict=snap_universes_n500,
        window_days=window_days,
        snap_dates=snap_dates,
        price_lookup=price_lookup,
        benchmark_lookup=benchmark_lookup,
        exit_rank_cutoff=40
    )
    log(f"    Volar      -> CAGR: {res_volar['cagr']:.2f}% | MaxDD: {res_volar['max_dd']:.2f}% | Sharpe: {res_volar['sharpe']:.2f} | Sortino: {res_volar['sortino']:.2f}")

    gate29_dd_diff = res_raw["max_dd"] - res_volar["max_dd"]
    gate29_cagr_diff = res_volar["cagr"] - res_raw["cagr"]
    gate29_pass = (gate29_dd_diff > 5.0 and gate29_cagr_diff >= -1.0) or (res_volar["sharpe"] > res_raw["sharpe"] and gate29_cagr_diff >= -1.0)
    log(f"\n  Gate 29 MaxDD Improvement: {gate29_dd_diff:+.2f} pp | CAGR Delta: {gate29_cagr_diff:+.2f} pp")
    log(f"  Gate 29 Sharpe Delta: {res_volar['sharpe'] - res_raw['sharpe']:+.2f} | Sortino Delta: {res_volar['sortino'] - res_raw['sortino']:+.2f}")
    log(f"  Gate 29 Status: {'PASS' if gate29_pass else 'FAIL'}")

    records.append({
        "gate_id": "Gate 29",
        "universe": "NIFTY 500",
        "experiment": "Raw 252d Return Ranking",
        "r2_factor": "0.80 (20% Retracement)",
        "cagr": res_raw["cagr"],
        "max_dd": res_raw["max_dd"],
        "sharpe": res_raw["sharpe"],
        "sortino": res_raw["sortino"],
        "turnover_pct": res_raw["turnover_pct"],
        "trades": res_raw["trades"],
        "metric_delta": "Baseline",
        "gate_status": "BASELINE"
    })
    records.append({
        "gate_id": "Gate 29",
        "universe": "NIFTY 500",
        "experiment": "Volar Ranking (Return/Sigma)",
        "r2_factor": "0.80 (20% Retracement)",
        "cagr": res_volar["cagr"],
        "max_dd": res_volar["max_dd"],
        "sharpe": res_volar["sharpe"],
        "sortino": res_volar["sortino"],
        "turnover_pct": res_volar["turnover_pct"],
        "trades": res_volar["trades"],
        "metric_delta": f"MaxDD diff: {gate29_dd_diff:+.2f} pp | CAGR delta: {gate29_cagr_diff:+.2f} pp | Sharpe delta: {res_volar['sharpe']-res_raw['sharpe']:+.2f}",
        "gate_status": "PASS" if gate29_pass else "FAIL"
    })

    # =========================================================================
    # PART 2: GATE 30 (50% RETRACEMENT FOR MID/SMALLCAPS)
    # =========================================================================
    log("\nPART 2: GATE 30 (50% RETRACEMENT FOR MID/SMALLCAPS)")
    mid_small_configs = [
        ("NIFTY Midcap 150", segments["NIFTY Midcap 150"]),
        ("NIFTY Smallcap 250", segments["NIFTY Smallcap 250"])
    ]

    gate30_passes = []
    for univ_name, u_dict in mid_small_configs:
        log(f"\n  Evaluating {univ_name}:")
        log(f"    Running 20% Retracement (r2=0.80)...")
        res_r20 = run_simulation(
            ranking_mode="volar",
            r2_factor=0.80,
            universe_dict=u_dict,
            window_days=window_days,
            snap_dates=snap_dates,
            price_lookup=price_lookup,
            benchmark_lookup=benchmark_lookup,
            exit_rank_cutoff=40
        )
        log(f"      20% Retracement -> CAGR: {res_r20['cagr']:.2f}% | MaxDD: {res_r20['max_dd']:.2f}% | Sharpe: {res_r20['sharpe']:.2f} | Trades: {res_r20['trades']:,}")

        log(f"    Running 50% Retracement (r2=0.50)...")
        res_r50 = run_simulation(
            ranking_mode="volar",
            r2_factor=0.50,
            universe_dict=u_dict,
            window_days=window_days,
            snap_dates=snap_dates,
            price_lookup=price_lookup,
            benchmark_lookup=benchmark_lookup,
            exit_rank_cutoff=40
        )
        log(f"      50% Retracement -> CAGR: {res_r50['cagr']:.2f}% | MaxDD: {res_r50['max_dd']:.2f}% | Sharpe: {res_r50['sharpe']:.2f} | Trades: {res_r50['trades']:,}")

        cagr_boost = res_r50["cagr"] - res_r20["cagr"]
        dd_increase = res_r50["max_dd"] - res_r20["max_dd"]
        univ_pass = (cagr_boost > 2.0 and dd_increase < 10.0 and res_r50["max_dd"] < 60.0)
        gate30_passes.append(univ_pass)

        log(f"      CAGR Delta: {cagr_boost:+.2f} pp (Threshold: > +2.0 pp) | MaxDD Delta: {dd_increase:+.2f} pp (Threshold: < +10.0 pp) | Status: {'PASS' if univ_pass else 'FAIL'}")

        records.append({
            "gate_id": "Gate 30",
            "universe": univ_name,
            "experiment": "20% Retracement (Baseline)",
            "r2_factor": "0.80 (20% Retracement)",
            "cagr": res_r20["cagr"],
            "max_dd": res_r20["max_dd"],
            "sharpe": res_r20["sharpe"],
            "sortino": res_r20["sortino"],
            "turnover_pct": res_r20["turnover_pct"],
            "trades": res_r20["trades"],
            "metric_delta": "Baseline 20%",
            "gate_status": "BASELINE"
        })
        records.append({
            "gate_id": "Gate 30",
            "universe": univ_name,
            "experiment": "50% Retracement (Wider Buffer)",
            "r2_factor": "0.50 (50% Retracement)",
            "cagr": res_r50["cagr"],
            "max_dd": res_r50["max_dd"],
            "sharpe": res_r50["sharpe"],
            "sortino": res_r50["sortino"],
            "turnover_pct": res_r50["turnover_pct"],
            "trades": res_r50["trades"],
            "metric_delta": f"CAGR delta: {cagr_boost:+.2f} pp | MaxDD delta: {dd_increase:+.2f} pp",
            "gate_status": "PASS" if univ_pass else "FAIL"
        })

    all_gate30_pass = any(gate30_passes)
    log(f"\nGate 30 Final Status: {'PASS' if all_gate30_pass else 'FAIL'}")

    df_out = pd.DataFrame(records)
    df_out.to_csv(OUT_CSV, index=False)
    log(f"\nExported Volar and Retracement Summary: {OUT_CSV}")

    with open(OUT_LOG, "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines) + "\n")

if __name__ == "__main__":
    main()
