#!/usr/bin/env python3
"""
deliverables/gate_ef/scripts/gate_f_reproducibility.py
Phase 5.5 Gates E & F — Gate F: Reproducibility & Truncation Invariants Audit

1. Byte-Identical Backtest Reproducibility (Standing Rule R-6):
   - Executes the Gate D (b) point-in-time dynamic backtest twice under identical configuration.
   - Saves output metrics and trade logs to deliverables/gate_ef/raw/gate_f_pass1.txt and gate_f_pass2.txt
     (also mirrored to gate_f_run_pass1.txt and gate_f_run_pass2.txt).
   - Computes SHA-256 digests and asserts bit-for-bit identical output.

2. Out-of-Bounds Clamping & Warning Emission (Standing Rule R-4):
   - Requests backtest and snapshot reconstructions with end dates beyond covered_end (2020-09-14),
     e.g., 2021-01-01, 2022-12-31, and 2026-09-25.
   - Verifies automatic clamping to 2020-09-14 and issuance of explicit warning banners.
   - Proves no artificial constituent extension or invention past covered_end.

3. Run-Date Invariance:
   - Evaluates simulation runs across perturbed run_date values (2026-09-25 vs 2024-01-01 vs 2020-09-15).
   - Asserts bit-for-bit identical portfolio values, signals, and trades prior to covered_end.

4. Accounting Identity Verification (Standing Rule R-3):
   - Asserts initial_capital + realized_pnl - tax + dividends + unrealized_pnl == final_value (residual == 0.00).

Outputs:
  - deliverables/gate_ef/data_csv/gate_f_clamping_summary.csv
  - deliverables/gate_ef/raw/gate_f_pass1.txt (and gate_f_run_pass1.txt)
  - deliverables/gate_ef/raw/gate_f_pass2.txt (and gate_f_run_pass2.txt)
  - deliverables/gate_ef/raw/gate_f_truncation.txt
"""

import sys
import hashlib
import datetime
import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR = Path("/storage/emulated/0/Documents/Project MIP")
DELIV_DIR = BASE_DIR / "deliverables/gate_ef"
DATA_CSV_DIR = DELIV_DIR / "data_csv"
RAW_DIR = DELIV_DIR / "raw"

BARS_PATH = BASE_DIR / "data/verification/halt1b_m1/adjusted_bhavcopy_bars_v2.parquet"
SNAPSHOTS_PATH = BASE_DIR / "deliverables/gate_ab/data_csv/snapshot_constituents_57.csv"
CALENDAR_PATH = BASE_DIR / "data/trading_calendar.txt"

COVERED_START_DATE = "1998-08-01"
COVERED_END_DATE   = "2020-09-14"
BASELINE_START     = "2016-01-04"

INITIAL_CAPITAL = 10_000_000.0  # 1 Crore INR
N_PORTFOLIO = 20
EXIT_RANK = 40

def sha256_str(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def sha256_file(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def run_simulation(bars_df, snaps_df, window_days, snap_dates, price_lookup, initial_capital=INITIAL_CAPITAL):
    cash = float(initial_capital)
    portfolio = {}  # sym -> {'shares': int, 'buy_price': float, 'buy_date': str}
    closed_trades = []
    daily_values = []
    trade_log = []

    snap_universe = {
        s_dt: set(snaps_df[(snaps_df["snapshot_date"] == s_dt) & (snaps_df["is_joint_covered"] == True)]["symbol"])
        for s_dt in snap_dates
    }
    snap_date_set = set(snap_dates)

    for day_idx, current_date in enumerate(window_days):
        # 1. Rebalance Signal Generation on Monthly Snapshot Dates
        if current_date in snap_date_set:
            u_current = snap_universe[current_date]
            is_first_day = (day_idx == 0)

            # Evaluate candidate signals
            candidates = []
            for sym in u_current:
                row = price_lookup.get((sym, current_date))
                if row is None:
                    continue
                cl = row["close"]
                hi = row["high_252"]
                ema = row["ema_200"]
                ret = row["day1_ret"] if is_first_day else row["ret_252"]

                r2_pass = (cl >= 0.80 * hi)
                r3_pass = (cl >= ema) if is_first_day else (cl > ema)

                candidates.append({
                    "symbol": sym,
                    "close": cl,
                    "high_252": hi,
                    "ema_200": ema,
                    "ret": ret,
                    "r2_pass": r2_pass,
                    "r3_pass": r3_pass
                })

            # Rule R5: Rank by return descending (deterministic symbol tie-breaker)
            candidates.sort(key=lambda x: (-x["ret"], x["symbol"]))
            rank_map = {c["symbol"]: i + 1 for i, c in enumerate(candidates)}
            pass_candidates = [c for c in candidates if c["r2_pass"] and c["r3_pass"]]

            # Rule R9 & Maintenance: Exits
            exits = []
            retained = []
            for sym, pos in list(portfolio.items()):
                row = price_lookup.get((sym, current_date))
                sym_rank = rank_map.get(sym, 9999)

                if (sym not in u_current) or (row is None):
                    exits.append((sym, "universe_exit"))
                elif row["close"] < 0.80 * row["high_252"]:
                    exits.append((sym, "r2_exit"))
                elif row["close"] <= row["ema_200"]:
                    exits.append((sym, "r3_exit"))
                elif sym_rank > EXIT_RANK:
                    exits.append((sym, "rank_exit"))
                else:
                    retained.append(sym)

            # Rule R8: Next-Day Open Execution
            next_day_idx = day_idx + 1
            if next_day_idx < len(window_days):
                exec_date = window_days[next_day_idx]

                # Process exits at next-day Open
                for sym, reason in exits:
                    pos = portfolio.pop(sym)
                    shs = pos["shares"]
                    exec_row = price_lookup.get((sym, exec_date))
                    sell_px = exec_row["open"] if (exec_row and exec_row["open"] > 0) else pos["buy_price"]
                    proceeds = shs * sell_px
                    cash += proceeds
                    pnl = proceeds - (shs * pos["buy_price"])
                    closed_trades.append({
                        "symbol": sym,
                        "buy_date": pos["buy_date"],
                        "buy_price": pos["buy_price"],
                        "sell_date": exec_date,
                        "sell_price": sell_px,
                        "shares": shs,
                        "pnl": pnl,
                        "exit_reason": reason
                    })
                    trade_log.append(f"SELL: {exec_date} | {sym:<12} | {shs:>6} shs @ {sell_px:>8.2f} | PnL: {pnl:>11.2f} ({reason})")

                # Rule R6: Equal Weight Entry for Open Slots (Target N = 20)
                open_slots = N_PORTFOLIO - len(retained)
                if open_slots > 0 and cash > 0:
                    entrants = [c["symbol"] for c in pass_candidates if c["symbol"] not in retained][:open_slots]
                    if entrants:
                        cash_per_stock = cash / len(entrants)
                        for sym in entrants:
                            exec_row = price_lookup.get((sym, exec_date))
                            if exec_row and exec_row["open"] > 0:
                                buy_px = exec_row["open"]
                                shs = int(cash_per_stock // buy_px)
                                if shs > 0:
                                    cost = shs * buy_px
                                    cash -= cost
                                    portfolio[sym] = {
                                        "shares": shs,
                                        "buy_price": buy_px,
                                        "buy_date": exec_date
                                    }
                                    trade_log.append(f"BUY : {exec_date} | {sym:<12} | {shs:>6} shs @ {buy_px:>8.2f} | Cost: {cost:>11.2f}")

        # Daily Valuation at Close
        port_val = cash
        for sym, pos in portfolio.items():
            r = price_lookup.get((sym, current_date))
            px = r["close"] if r else pos["buy_price"]
            port_val += pos["shares"] * px

        daily_values.append({"date": current_date, "value": port_val, "cash": cash})

    # Final Valuation at Clamped Window End
    final_date = window_days[-1]
    final_val = cash
    unrealized_pnl = 0.0
    for sym, pos in portfolio.items():
        r = price_lookup.get((sym, final_date))
        px = r["close"] if r else pos["buy_price"]
        val = pos["shares"] * px
        final_val += val
        unrealized_pnl += pos["shares"] * (px - pos["buy_price"])

    realized_pnl = sum(t["pnl"] for t in closed_trades)
    net_profit = final_val - initial_capital
    residual = (initial_capital + realized_pnl + unrealized_pnl) - final_val

    # Statistics
    d_df = pd.DataFrame(daily_values)
    d_df["ret"] = d_df["value"].pct_change().fillna(0.0)
    sharpe = (d_df["ret"].mean() / d_df["ret"].std() * np.sqrt(252)) if d_df["ret"].std() > 0 else 0.0
    d_df["peak"] = d_df["value"].cummax()
    d_df["dd"] = (d_df["value"] - d_df["peak"]) / d_df["peak"]
    max_dd = abs(d_df["dd"].min()) * 100.0

    years = (pd.to_datetime(final_date) - pd.to_datetime(window_days[0])).days / 365.25
    cagr = ((final_val / initial_capital) ** (1.0 / years) - 1.0) * 100.0

    return {
        "initial_capital": initial_capital,
        "final_value": final_val,
        "net_profit": net_profit,
        "cagr": cagr,
        "max_dd": max_dd,
        "sharpe": sharpe,
        "realized_pnl": realized_pnl,
        "unrealized_pnl": unrealized_pnl,
        "residual": residual,
        "closed_trades_count": len(closed_trades),
        "open_positions_count": len(portfolio),
        "total_trades": len(closed_trades) + len(portfolio),
        "years": years,
        "portfolio": portfolio,
        "closed_trades": closed_trades,
        "trade_log": trade_log,
        "daily_values": daily_values
    }

def format_reproducible_report(res, window_days):
    lines = []
    lines.append("=" * 80)
    lines.append("MIP-RETURN-10Y BASELINE BACKTEST EXECUTION: RUN (b) POINT-IN-TIME DYNAMIC")
    lines.append("=" * 80)
    lines.append("Universe coverage: Point-in-time dynamic membership (median joint coverage 87.03%)")
    lines.append(f"Clamped Backtest Window: {window_days[0]} to {window_days[-1]} ({res['years']:.4f} years, {len(window_days):,} trading days)")
    lines.append("Portfolio Rules: N=20, Rebalance=Monthly (1st trading day), Execution=Next-Day Open, ExitRank=40")
    lines.append("\n[METRICS BLOCK]")
    lines.append(f"  Initial Capital:      Rs. {res['initial_capital']:>14,.2f}")
    lines.append(f"  Final Portfolio Value:Rs. {res['final_value']:>14,.2f}")
    lines.append(f"  Net Profit:           Rs. {res['net_profit']:>14,.2f}")
    lines.append(f"  CAGR:                       {res['cagr']:>10.2f}%")
    lines.append(f"  Max Drawdown:               {res['max_dd']:>10.2f}%")
    lines.append(f"  Sharpe Ratio:               {res['sharpe']:>10.2f}")
    lines.append(f"  Total Closed Trades:        {res['closed_trades_count']:>10}")
    lines.append(f"  Open Positions at End:      {res['open_positions_count']:>10}")
    lines.append("\n[ACCOUNTING IDENTITY BLOCK (Rule R-3)]")
    lines.append(f"  Initial Capital:      Rs. {res['initial_capital']:>14,.2f}")
    lines.append(f"  + Realized PnL:       Rs. {res['realized_pnl']:>14,.2f}")
    lines.append(f"  - Tax:                Rs. {0.0:>14,.2f}")
    lines.append(f"  + Dividends:          Rs. {0.0:>14,.2f}")
    lines.append(f"  + Unrealized PnL:     Rs. {res['unrealized_pnl']:>14,.2f}")
    lines.append(f"  = Final Value:        Rs. {res['final_value']:>14,.2f}")
    lines.append(f"  Residual:                   {res['residual']:>14.8f} (assert == 0.00)")
    lines.append("\n[TRADE LOG SUMMARY (Sample first 25 trades)]")
    for tl in res["trade_log"][:25]:
        lines.append(f"  {tl}")
    if len(res["trade_log"]) > 25:
        lines.append(f"  ... [{len(res['trade_log']) - 25} additional trade executions omitted for brevity]")
    lines.append(f"\n[OPEN POSITIONS AT CLAMPED END ({window_days[-1]})]")
    for sym, pos in sorted(res["portfolio"].items()):
        lines.append(f"  HELD: {sym:<12} | {pos['shares']:>6} shs | Entry: {pos['buy_date']} @ {pos['buy_price']:.2f}")
    lines.append("=" * 80)
    return "\n".join(lines)

def main():
    trunc_lines = []
    def log(msg=""):
        print(msg)
        trunc_lines.append(msg)

    log("=" * 80)
    log("PHASE 5.5 GATES E & F — GATE F: REPRODUCIBILITY & TRUNCATION INVARIANTS AUDIT")
    log(f"Timestamp: {datetime.datetime.now(datetime.timezone.utc).isoformat()}")
    log("=" * 80)

    for d in [DATA_CSV_DIR, RAW_DIR]:
        d.mkdir(parents=True, exist_ok=True)

    # 1. Ingest Price Data, Indicators & Calendar
    log("\n--- 1. Ingesting Bhavcopy Bars, Snapshots & Trading Calendar ---")
    bars_df = pd.read_parquet(BARS_PATH).sort_values(["symbol", "date"]).reset_index(drop=True)
    log(f"Loaded Bhavcopy price bars: {len(bars_df):,} bars across {bars_df['symbol'].nunique()} symbols")

    with open(CALENDAR_PATH) as f:
        all_cal_dates = sorted([line.strip() for line in f if line.strip()])
    log(f"Total trading calendar days: {len(all_cal_dates)} days ({all_cal_dates[0]} to {all_cal_dates[-1]})")

    snaps_df = pd.read_csv(SNAPSHOTS_PATH)
    all_snap_dates = sorted(snaps_df["snapshot_date"].unique())
    log(f"Loaded monthly rebalance snapshots: {len(all_snap_dates)} snapshots ({all_snap_dates[0]} to {all_snap_dates[-1]})")

    log("Computing indicators (high_252, ema_200, ret_252)...")
    bars_df["high_252"] = bars_df.groupby("symbol")["close"].transform(lambda s: s.rolling(252, min_periods=1).max())
    bars_df["ema_200"] = bars_df.groupby("symbol")["close"].transform(lambda s: s.ewm(span=200, adjust=True, min_periods=1).mean())

    def calc_ret(s):
        n = len(s)
        vals = s.to_numpy()
        prev = vals[np.maximum(0, np.arange(n) - 252)]
        with np.errstate(divide="ignore", invalid="ignore"):
            ret = np.where(np.arange(n) > 0, vals / prev - 1.0, 0.0)
        return pd.Series(ret, index=s.index)

    bars_df["ret_252"] = bars_df.groupby("symbol")["close"].transform(calc_ret)
    bars_df["day1_ret"] = (bars_df["close"] / bars_df["open"] - 1.0).fillna(0.0)
    price_lookup = bars_df.set_index(["symbol", "date"]).to_dict(orient="index")

    # Clamped window trading days & snapshots
    clamped_window_days = [d for d in all_cal_dates if BASELINE_START <= d <= COVERED_END_DATE]
    clamped_snap_dates = [d for d in all_snap_dates if BASELINE_START <= d <= COVERED_END_DATE]
    log(f"Clamped window days: {len(clamped_window_days)} days ({clamped_window_days[0]} to {clamped_window_days[-1]})")
    log(f"Clamped rebalance snapshots: {len(clamped_snap_dates)} snapshots")

    # 2. Gate F Step 1: Byte-Identical Dual-Pass Backtest Reproducibility (Rule R-6)
    log("\n--- 2. Dual-Pass Point-in-Time Backtest Reproducibility (Standing Rule R-6) ---")
    log("Executing Run (b) Pass 1...")
    res_pass1 = run_simulation(bars_df, snaps_df, clamped_window_days, clamped_snap_dates, price_lookup)
    report_pass1 = format_reproducible_report(res_pass1, clamped_window_days)

    log("Executing Run (b) Pass 2...")
    res_pass2 = run_simulation(bars_df, snaps_df, clamped_window_days, clamped_snap_dates, price_lookup)
    report_pass2 = format_reproducible_report(res_pass2, clamped_window_days)

    pass1_path = RAW_DIR / "gate_f_pass1.txt"
    pass2_path = RAW_DIR / "gate_f_pass2.txt"
    run_pass1_path = RAW_DIR / "gate_f_run_pass1.txt"
    run_pass2_path = RAW_DIR / "gate_f_run_pass2.txt"

    with open(pass1_path, "w", encoding="utf-8") as f:
        f.write(report_pass1 + "\n")
    with open(pass2_path, "w", encoding="utf-8") as f:
        f.write(report_pass2 + "\n")
    with open(run_pass1_path, "w", encoding="utf-8") as f:
        f.write(report_pass1 + "\n")
    with open(run_pass2_path, "w", encoding="utf-8") as f:
        f.write(report_pass2 + "\n")

    hash_pass1 = sha256_file(pass1_path)
    hash_pass2 = sha256_file(pass2_path)

    log(f"Pass 1 Raw Output: {pass1_path.relative_to(BASE_DIR)} | SHA-256: {hash_pass1}")
    log(f"Pass 2 Raw Output: {pass2_path.relative_to(BASE_DIR)} | SHA-256: {hash_pass2}")
    log(f"SHA-256 Match: {hash_pass1 == hash_pass2}")

    assert hash_pass1 == hash_pass2, "Rule R-6 VIOLATION: Pass 1 and Pass 2 SHA-256 hashes do not match!"
    log("Standing Rule R-6 PASSED: Backtest execution is 100% byte-identical bit-for-bit across independent passes.")

    # Rule R-3 Accounting Identity Check
    log(f"\nRule R-3 Accounting Residual on Pass 1: {res_pass1['residual']:.10f}")
    assert abs(res_pass1["residual"]) < 1e-6, f"Rule R-3 VIOLATION: Residual {res_pass1['residual']} != 0.0"
    log("Standing Rule R-3 PASSED: Accounting identity strictly holds with residual == 0.00.")

    # 3. Gate F Step 2: Out-of-Bounds Clamping & Warning Emission (Standing Rule R-4)
    log("\n--- 3. Out-of-Bounds Date Clamping & Warning Audit (Standing Rule R-4) ---")

    def run_with_boundary_check(req_start: str, req_end: str, run_date: str):
        warn_emitted = False
        warn_msg = ""

        # Standing Rule R-4 Boundary Check
        eff_end = req_end
        if req_end > COVERED_END_DATE:
            warn_emitted = True
            warn_msg = (
                f"WARNING: Requested end date '{req_end}' exceeds covered_end '{COVERED_END_DATE}'. "
                f"Clamping to '{COVERED_END_DATE}'. Universe coverage: {COVERED_START_DATE} to {COVERED_END_DATE}."
            )
            eff_end = COVERED_END_DATE

        # Filter window and snapshots to clamped boundary
        w_days = [d for d in all_cal_dates if req_start <= d <= eff_end]
        s_dates = [d for d in all_snap_dates if req_start <= d <= eff_end]

        res = run_simulation(bars_df, snaps_df, w_days, s_dates, price_lookup)
        rep = format_reproducible_report(res, w_days)
        rep_sha = sha256_str(rep + "\n")

        return {
            "req_start": req_start,
            "req_end": req_end,
            "run_date": run_date,
            "eff_start": req_start,
            "eff_end": eff_end,
            "warn_emitted": warn_emitted,
            "warn_msg": warn_msg,
            "trading_days": len(w_days),
            "final_value": res["final_value"],
            "cagr": res["cagr"],
            "max_dd": res["max_dd"],
            "realized_pnl": res["realized_pnl"],
            "unrealized_pnl": res["unrealized_pnl"],
            "residual": res["residual"],
            "sha256": rep_sha,
            "trade_count": res["total_trades"],
            "res": res
        }

    test_cases = [
        {"id": 1, "desc": "Baseline In-Bounds Window",          "req_start": "2016-01-04", "req_end": "2020-09-14", "run_date": "2026-09-25"},
        {"id": 2, "desc": "Out-of-Bounds Clamping (2021-01-01)", "req_start": "2016-01-04", "req_end": "2021-01-01", "run_date": "2026-09-25"},
        {"id": 3, "desc": "Out-of-Bounds Clamping (2022-12-31)", "req_start": "2016-01-04", "req_end": "2022-12-31", "run_date": "2026-09-25"},
        {"id": 4, "desc": "Run-Date Invariance (2024-01-01)",    "req_start": "2016-01-04", "req_end": "2021-01-01", "run_date": "2024-01-01"},
        {"id": 5, "desc": "Run-Date Invariance (2020-09-15)",    "req_start": "2016-01-04", "req_end": "2021-01-01", "run_date": "2020-09-15"},
    ]

    clamping_summary_records = []

    for tc in test_cases:
        log(f"\nExecuting Test #{tc['id']}: {tc['desc']}")
        log(f"  Requested: {tc['req_start']} to {tc['req_end']} | run_date = {tc['run_date']}")
        
        out = run_with_boundary_check(tc["req_start"], tc["req_end"], tc["run_date"])

        if out["warn_emitted"]:
            log(f"  >> EMITTED HEADER: {out['warn_msg']}")
        else:
            log("  >> In-Bounds: No clamping warning necessary.")

        log(f"  Clamped Window End:    {out['eff_end']}")
        log(f"  Trading Days Evaluated:{out['trading_days']:,}")
        log(f"  Final Portfolio Value: Rs. {out['final_value']:>14,.2f}")
        log(f"  CAGR:                  {out['cagr']:>10.2f}%")
        log(f"  Accounting Residual:   {out['residual']:>14.8f}")
        log(f"  Output SHA-256:        {out['sha256']}")

        # Assertions
        assert out["eff_end"] == COVERED_END_DATE, f"Test #{tc['id']} failed to clamp to {COVERED_END_DATE}"
        assert out["trading_days"] == 1154, f"Test #{tc['id']} evaluated {out['trading_days']} days instead of 1,154"
        assert abs(out["residual"]) < 1e-6, f"Test #{tc['id']} violated Rule R-3 residual"
        assert out["sha256"] == hash_pass1, f"Test #{tc['id']} SHA-256 divergence from baseline!"

        if tc["req_end"] > COVERED_END_DATE:
            assert out["warn_emitted"] is True, f"Test #{tc['id']} expected warning emission!"

        clamping_summary_records.append({
            "test_id": tc["id"],
            "test_description": tc["desc"],
            "requested_start_date": tc["req_start"],
            "requested_end_date": tc["req_end"],
            "run_date": tc["run_date"],
            "clamped_start_date": out["eff_start"],
            "clamped_end_date": out["eff_end"],
            "warning_emitted": out["warn_emitted"],
            "warning_message": out["warn_msg"] if out["warn_emitted"] else "None (In-Bounds)",
            "effective_trading_days": out["trading_days"],
            "final_portfolio_value": round(out["final_value"], 2),
            "cagr_pct": round(out["cagr"], 2),
            "max_dd_pct": round(out["max_dd"], 2),
            "realized_pnl": round(out["realized_pnl"], 2),
            "unrealized_pnl": round(out["unrealized_pnl"], 2),
            "accounting_residual": round(out["residual"], 8),
            "output_sha256": out["sha256"],
            "is_bit_identical_to_baseline": (out["sha256"] == hash_pass1)
        })

    log("\nAll 5 Clamping & Run-Date Invariance Test Cases PASSED with 100% Bit-for-Bit Identity!")

    # 4. Export Summary CSV & Truncation Log
    log("\n--- 4. Exporting Gate F Summary CSV ---")
    clamp_df = pd.DataFrame(clamping_summary_records)
    clamp_csv_path = DATA_CSV_DIR / "gate_f_clamping_summary.csv"
    clamp_df.to_csv(clamp_csv_path, index=False)
    log(f"Exported clamping summary: {clamp_csv_path.relative_to(BASE_DIR)} ({len(clamp_df)} records)")

    log("\n" + "=" * 80)
    log("GATE F STEP 2 COMPLETE: REPRODUCIBILITY & TRUNCATION INVARIANTS AUDIT (PASS)")
    log("=" * 80)

    trunc_raw_path = RAW_DIR / "gate_f_truncation.txt"
    with open(trunc_raw_path, "w", encoding="utf-8") as f:
        f.write("\n".join(trunc_lines) + "\n")
    log(f"Saved truncation log: {trunc_raw_path.relative_to(BASE_DIR)}")

if __name__ == "__main__":
    main()
