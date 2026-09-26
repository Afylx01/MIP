#!/usr/bin/env python3
"""
deliverables/phase_8/scripts/generate_execution_orders.py
Phase 8 Task 3: Portfolio Rebalance & Order Generation Engine

Ingests current portfolio holdings and screener output, applies the 100% Exit Buffer (Exit Rank 40),
and generates actionable whole-share order tickets with itemized regulatory fees and slippage buffers.

Fee Model (Indian Institutional Delivery Schedule):
  - Brokerage: 0.03% (3 bps)
  - STT: 0.10% (10 bps) on delivery (Buy and Sell)
  - Stamp Duty: 0.015% (1.5 bps) on Buy only
  - Exchange Turnover: 0.00345% (0.345 bps)
  - SEBI Charges: 0.0001% (0.01 bps)
  - GST: 18% on (Brokerage + Exchange Charges + SEBI Charges)
  - DP Charges: ₹15.93 flat per Sell order
  - Slippage Buffer: 15 bps (0.15%)

Outputs:
  - deliverables/phase_8/data_csv/rebalance_orders_sample.csv
  - deliverables/phase_8/data_csv/trade_recommendations_sample.md
  - deliverables/phase_8/raw/generate_execution_orders.log
"""

import sys
import os
import json
import argparse
import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
import pandas as pd
import numpy as np

BASE_DIR = Path("/storage/emulated/0/Documents/Project MIP")
DELIV_DIR = BASE_DIR / "deliverables/phase_8"
DATA_CSV_DIR = DELIV_DIR / "data_csv"
RAW_DIR = DELIV_DIR / "raw"

DEFAULT_SCREENER_CSV = DATA_CSV_DIR / "screener_output_sample.csv"
DEFAULT_ORDERS_CSV = DATA_CSV_DIR / "rebalance_orders_sample.csv"
DEFAULT_MEMO_MD = DATA_CSV_DIR / "trade_recommendations_sample.md"
LOG_FILE = RAW_DIR / "generate_execution_orders.log"


class FeeCalculator:
    """Computes exact itemized regulatory and brokerage fees for Indian equity delivery."""

    BROKERAGE_RATE = 0.0003          # 0.03%
    STT_RATE = 0.0010                # 0.10% on delivery Buy & Sell
    STAMP_DUTY_BUY_RATE = 0.00015    # 0.015% on delivery Buy
    EXCHANGE_TURNOVER_RATE = 0.0000345  # 0.00345%
    SEBI_RATE = 0.000001             # 0.0001%
    GST_RATE = 0.18                  # 18% on (Brokerage + Exchange + SEBI)
    DP_CHARGE_PER_SELL = 15.93       # ₹15.93 flat per sell
    SLIPPAGE_BPS = 15.0              # 15 bps = 0.0015

    @classmethod
    def calculate_trade_fees(cls, action: str, gross_value: float) -> Dict[str, float]:
        """Calculates itemized costs for a given order value."""
        if gross_value <= 0 or action not in ["BUY", "SELL"]:
            return {
                "brokerage": 0.0,
                "stt": 0.0,
                "stamp_duty": 0.0,
                "exchange_charges": 0.0,
                "sebi_charges": 0.0,
                "gst": 0.0,
                "dp_charges": 0.0,
                "slippage_buffer": 0.0,
                "total_friction": 0.0
            }

        brokerage = gross_value * cls.BROKERAGE_RATE
        stt = gross_value * cls.STT_RATE
        stamp_duty = (gross_value * cls.STAMP_DUTY_BUY_RATE) if action == "BUY" else 0.0
        exchange_charges = gross_value * cls.EXCHANGE_TURNOVER_RATE
        sebi_charges = gross_value * cls.SEBI_RATE
        gst = (brokerage + exchange_charges + sebi_charges) * cls.GST_RATE
        dp_charges = cls.DP_CHARGE_PER_SELL if action == "SELL" else 0.0
        slippage = gross_value * (cls.SLIPPAGE_BPS / 10_000.0)

        total_friction = brokerage + stt + stamp_duty + exchange_charges + sebi_charges + gst + dp_charges + slippage

        return {
            "brokerage": round(brokerage, 2),
            "stt": round(stt, 2),
            "stamp_duty": round(stamp_duty, 2),
            "exchange_charges": round(exchange_charges, 2),
            "sebi_charges": round(sebi_charges, 2),
            "gst": round(gst, 2),
            "dp_charges": round(dp_charges, 2),
            "slippage_buffer": round(slippage, 2),
            "total_friction": round(total_friction, 2)
        }


class ExecutionOrderGenerator:
    """Generates execution order tickets from screener output and current portfolio holdings."""

    def __init__(
        self,
        portfolio_aum: float = 10_000_000.0,  # ₹1 Crore default
        target_slots: int = 20,
        exit_rank_buffer: int = 40            # 100% buffer = rank 40
    ):
        self.portfolio_aum = float(portfolio_aum)
        self.target_slots = int(target_slots)
        self.exit_rank_buffer = int(exit_rank_buffer)
        RAW_DIR.mkdir(parents=True, exist_ok=True)
        DATA_CSV_DIR.mkdir(parents=True, exist_ok=True)

    def log(self, msg: str, to_console: bool = True):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted = f"[{timestamp}] {msg}"
        if to_console:
            print(formatted)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(formatted + "\n")

    def load_current_holdings(self, holdings_path: Optional[Path]) -> Dict[str, dict]:
        """
        Loads current holdings map: {symbol: {shares, avg_price, ...}}.
        Returns empty dict if no holdings file provided (initial deployment).
        """
        if not holdings_path or not Path(holdings_path).exists():
            return {}

        hp = Path(holdings_path)
        if hp.suffix == ".json":
            with open(hp, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("holdings", {})
        elif hp.suffix == ".csv":
            df = pd.read_csv(hp)
            holdings = {}
            for _, row in df.iterrows():
                holdings[str(row["symbol"]).strip()] = {
                    "shares": int(row["shares"]),
                    "avg_price": float(row.get("avg_cost_price", row.get("avg_price", 0.0)))
                }
            return holdings
        return {}

    def generate_orders(
        self,
        screener_csv: Path,
        holdings_path: Optional[Path] = None,
        as_of_date: Optional[str] = None,
        force_deploy: bool = False,
        orders_csv: Optional[Path] = None,
        memo_md: Optional[Path] = None
    ) -> Tuple[pd.DataFrame, str]:
        """
        Generates full rebalance order tickets applying the 100% Exit Buffer (Exit Rank 40).
        """
        dest_csv = Path(orders_csv) if orders_csv else DEFAULT_ORDERS_CSV
        dest_md = Path(memo_md) if memo_md else DEFAULT_MEMO_MD

        self.log("==================================================================")
        self.log(f"GENERATING EXECUTION ORDER TICKETS (AUM: ₹{self.portfolio_aum:,.2f})")
        self.log("==================================================================")

        # 1. Load Screener Results
        if not Path(screener_csv).exists():
            raise FileNotFoundError(f"Screener output not found at {screener_csv}")
        screen_df = pd.read_csv(screener_csv)
        self.log(f"Loaded screener data: {len(screen_df)} stocks.")

        # Create symbol lookups
        screener_lookup = {}
        for _, row in screen_df.iterrows():
            sym = str(row["symbol"]).strip()
            screener_lookup[sym] = row.to_dict()

        qualified_df = screen_df[screen_df["is_qualified"] == True].sort_values(by="rank").reset_index(drop=True)
        self.log(f"Total qualified momentum stocks: {len(qualified_df)}")

        # 2. Load Current Holdings
        current_holdings = self.load_current_holdings(holdings_path)
        is_initial_deployment = (len(current_holdings) == 0)
        self.log(f"Current held positions: {len(current_holdings)} ({'INITIAL SEEDING' if is_initial_deployment else 'WEEKLY REBALANCE'})")

        # 3. Determine Market Regime
        # If screener output has market regime or check index
        is_defensive = False
        regime_status_str = "NORMAL (Risk-On)"
        # Check from screener log or check benchmark
        bench_csv = BASE_DIR / "deliverables/phase_7/data_csv/nifty_500_benchmark_proxy.csv"
        if bench_csv.exists() and as_of_date:
            b_df = pd.read_csv(bench_csv)
            b_row = b_df[b_df["date"] == as_of_date]
            if not b_row.empty:
                c = float(b_row["close"].values[0])
                e20 = float(b_row["ema_20"].values[0])
                if c < e20:
                    is_defensive = True
                    regime_status_str = f"DEFENSIVE (Risk-Off: Close ₹{c:.2f} < 20 EMA ₹{e20:.2f})"

        self.log(f"Market Regime Status: {regime_status_str}")

        # 4. Process Holdings & Exits (100% Exit Buffer: Exit Rank 40)
        orders = []
        retained_symbols = set()
        exits_count = 0
        order_idx = 1

        for sym, pos in current_holdings.items():
            shares = int(pos["shares"])
            if shares <= 0:
                continue

            scr_row = screener_lookup.get(sym)
            if scr_row is None:
                # Delisted / Purged
                px = float(pos.get("avg_price", 100.0))
                gross = shares * px
                fees = FeeCalculator.calculate_trade_fees("SELL", gross)
                orders.append({
                    "order_id": f"ORD-{order_idx:03d}",
                    "action": "SELL",
                    "symbol": sym,
                    "shares": shares,
                    "reference_price": round(px, 2),
                    "gross_value": round(gross, 2),
                    **fees,
                    "net_cash_impact": round(gross - fees["total_friction"], 2),
                    "current_rank": 9999,
                    "reason": "DELISTED_OR_PURGED_FROM_UNIVERSE"
                })
                order_idx += 1
                exits_count += 1
                continue

            rank = int(scr_row.get("rank", 9999))
            cl = float(scr_row.get("close", 0.0))
            ema = float(scr_row.get("ema_200", 0.0))
            f1 = bool(scr_row.get("filter1_pass", False))
            f2 = bool(scr_row.get("filter2_pass", False))

            # Exit Conditions:
            # 1. Rank > Exit Buffer (40)
            # 2. Close < 200 EMA (Trend Break)
            # 3. Retracement failure (> 20% drop from 52w high)
            exit_reason = None
            if cl < ema:
                exit_reason = f"STOP_200_EMA_BREAK (Close ₹{cl:.2f} < EMA ₹{ema:.2f})"
            elif not f1:
                exit_reason = f"STOP_52W_HIGH_BREAK (Retracement > 20%)"
            elif rank > self.exit_rank_buffer:
                exit_reason = f"EXIT_BUFFER_BREACH (Rank {rank} > Cutoff {self.exit_rank_buffer})"

            if exit_reason:
                gross = shares * cl
                fees = FeeCalculator.calculate_trade_fees("SELL", gross)
                orders.append({
                    "order_id": f"ORD-{order_idx:03d}",
                    "action": "SELL",
                    "symbol": sym,
                    "shares": shares,
                    "reference_price": round(cl, 2),
                    "gross_value": round(gross, 2),
                    **fees,
                    "net_cash_impact": round(gross - fees["total_friction"], 2),
                    "current_rank": rank,
                    "reason": exit_reason
                })
                order_idx += 1
                exits_count += 1
            else:
                # Position RETAINED
                retained_symbols.add(sym)
                gross = shares * cl
                orders.append({
                    "order_id": f"ORD-{order_idx:03d}",
                    "action": "HOLD",
                    "symbol": sym,
                    "shares": shares,
                    "reference_price": round(cl, 2),
                    "gross_value": round(gross, 2),
                    "brokerage": 0.0,
                    "stt": 0.0,
                    "stamp_duty": 0.0,
                    "exchange_charges": 0.0,
                    "sebi_charges": 0.0,
                    "gst": 0.0,
                    "dp_charges": 0.0,
                    "slippage_buffer": 0.0,
                    "total_friction": 0.0,
                    "net_cash_impact": 0.0,
                    "current_rank": rank,
                    "reason": f"RETAINED_WITHIN_BUFFER (Rank {rank} <= {self.exit_rank_buffer})"
                })
                order_idx += 1

        self.log(f"Exits identified: {exits_count} | Retained holdings: {len(retained_symbols)}")

        # 5. Process Entries (Top-ranked qualifying candidates)
        open_slots = self.target_slots - len(retained_symbols)
        target_capital_per_slot = self.portfolio_aum / float(self.target_slots)
        self.log(f"Open slots to fill: {open_slots} (Target capital per slot: ₹{target_capital_per_slot:,.2f})")

        entries_allowed = (not is_defensive) or force_deploy or is_initial_deployment
        if not entries_allowed:
            self.log(f"⚠️ Defensive Regime Active: New entries FROZEN. {open_slots} open slot(s) kept in Cash.")
        else:
            if is_initial_deployment:
                self.log(f"🚀 Initial Portfolio Deployment: Seeding Top {self.target_slots} scrips.")
            elif force_deploy:
                self.log(f"⚡ Force Deploy Flag Active: Proceeding with entries despite Defensive regime.")

            entrants_df = qualified_df[~qualified_df["symbol"].isin(retained_symbols)].head(open_slots)

            for _, row in entrants_df.iterrows():
                sym = str(row["symbol"]).strip()
                rank = int(row["rank"])
                px = float(row["close"])
                if px <= 0:
                    continue

                # Estimate fees to calculate whole shares
                # Target: (shares * px) + fees <= target_capital_per_slot
                est_charges_rate = (
                    FeeCalculator.BROKERAGE_RATE +
                    FeeCalculator.STT_RATE +
                    FeeCalculator.STAMP_DUTY_BUY_RATE +
                    FeeCalculator.EXCHANGE_TURNOVER_RATE +
                    (FeeCalculator.SLIPPAGE_BPS / 10_000.0)
                )
                effective_px = px * (1.0 + est_charges_rate)
                shares = int(target_capital_per_slot // effective_px)
                if shares <= 0:
                    shares = 1

                gross = shares * px
                fees = FeeCalculator.calculate_trade_fees("BUY", gross)
                net_impact = -(gross + fees["total_friction"])

                reason = "INITIAL_PORTFOLIO_DEPLOYMENT" if is_initial_deployment else f"TOP_MOMENTUM_ENTRY (Rank {rank})"

                orders.append({
                    "order_id": f"ORD-{order_idx:03d}",
                    "action": "BUY",
                    "symbol": sym,
                    "shares": shares,
                    "reference_price": round(px, 2),
                    "gross_value": round(gross, 2),
                    **fees,
                    "net_cash_impact": round(net_impact, 2),
                    "current_rank": rank,
                    "reason": reason
                })
                order_idx += 1

        orders_df = pd.DataFrame(orders)

        # Sort: SELLs first, then BUYs, then HOLDs
        action_order = {"SELL": 1, "BUY": 2, "HOLD": 3}
        orders_df["sort_order"] = orders_df["action"].map(action_order)
        orders_df = orders_df.sort_values(by=["sort_order", "current_rank", "symbol"]).reset_index(drop=True)
        orders_df = orders_df.drop(columns=["sort_order"])

        # Re-number order IDs sequentially
        orders_df["order_id"] = [f"ORD-{i+1:03d}" for i in range(len(orders_df))]

        # Save machine-readable orders CSV
        orders_df.to_csv(dest_csv, index=False)
        self.log(f"Exported {len(orders_df)} order tickets to {dest_csv}")

        # 6. Format Human-Readable Trade Recommendation Markdown Memo
        memo_content = self._format_markdown_memo(
            orders_df=orders_df,
            as_of_date=as_of_date or str(datetime.date.today()),
            regime_status=regime_status_str,
            open_slots=open_slots,
            entries_allowed=entries_allowed
        )

        with open(dest_md, "w", encoding="utf-8") as f:
            f.write(memo_content)
        self.log(f"Exported human-readable trade memo to {dest_md}")

        return orders_df, memo_content

    def _format_markdown_memo(
        self,
        orders_df: pd.DataFrame,
        as_of_date: str,
        regime_status: str,
        open_slots: int,
        entries_allowed: bool
    ) -> str:
        sells = orders_df[orders_df["action"] == "SELL"]
        buys = orders_df[orders_df["action"] == "BUY"]
        holds = orders_df[orders_df["action"] == "HOLD"]

        total_buy_gross = buys["gross_value"].sum()
        total_sell_gross = sells["gross_value"].sum()
        total_turnover = total_buy_gross + total_sell_gross
        total_friction = buys["total_friction"].sum() + sells["total_friction"].sum()
        net_cash_flow = sells["net_cash_impact"].sum() + buys["net_cash_impact"].sum()

        lines = [
            f"# Institutional Momentum Portfolio — Execution Order Sheet",
            f"**Strategy**: MIP Institutional Momentum (Volar + RS + 100% Exit Buffer)",
            f"- **Execution Memo Date**: {as_of_date}",
            f"- **Target Execution Window**: Monday Open (t+1 Next-Day Open Fill)",
            f"- **Total Portfolio AUM**: ₹{self.portfolio_aum:,.2f}",
            f"- **Target Position Allocation**: 5.0% per slot (₹{self.portfolio_aum/self.target_slots:,.2f}) across {self.target_slots} slots",
            f"- **Market Regime Status**: **{regime_status}**",
            f"",
            f"---",
            f"",
            f"## 1. Executive Rebalance Summary",
            f"",
            f"| Metric | Summary Value |",
            f"| :--- | :--- |",
            f"| **Active Holdings Evaluated** | {len(holds) + len(sells)} |",
            f"| **Positions Retained (HOLD)** | {len(holds)} scrips |",
            f"| **Positions Liquidated (SELL)** | {len(sells)} scrips |",
            f"| **New Positions Initiated (BUY)**| {len(buys)} scrips |",
            f"| **Open Cash Slots** | {self.target_slots - len(holds) - len(buys)} slots |",
            f"| **Gross Buy Turnover** | ₹{total_buy_gross:,.2f} |",
            f"| **Gross Sell Turnover** | ₹{total_sell_gross:,.2f} |",
            f"| **Total Portfolio Turnover** | ₹{total_turnover:,.2f} ({total_turnover/self.portfolio_aum*100:.2f}% of AUM) |",
            f"| **Estimated Total Friction & Taxes** | ₹{total_friction:,.2f} ({((total_friction/total_turnover*10000) if total_turnover > 0 else 0.0):.1f} bps of turnover) |",
            f"| **Net Cash Flow Impact** | ₹{net_cash_flow:,.2f} |",
            f"",
            f"---",
            f"",
            f"## 2. Order Ticket Details",
            f""
        ]

        if not sells.empty:
            lines.extend([
                f"### A. Liquidations & Exits (SELL Orders)",
                f"| Order ID | Symbol | Shares | Est. Price | Gross Proceeds | Taxes & Fees | Net Inflow | Rank | Reason |",
                f"| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |"
            ])
            for _, r in sells.iterrows():
                lines.append(
                    f"| `{r['order_id']}` | **{r['symbol']}** | {r['shares']:,} | ₹{r['reference_price']:,.2f} | "
                    f"₹{r['gross_value']:,.2f} | ₹{r['total_friction']:,.2f} | ₹{r['net_cash_impact']:,.2f} | "
                    f"{r['current_rank']} | {r['reason']} |"
                )
            lines.append("")

        if not buys.empty:
            lines.extend([
                f"### B. New Entries & Re-allocations (BUY Orders)",
                f"| Order ID | Symbol | Shares | Est. Price | Gross Outlay | Taxes & Fees | Net Cash Req. | Rank | Reason |",
                f"| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |"
            ])
            for _, r in buys.iterrows():
                lines.append(
                    f"| `{r['order_id']}` | **{r['symbol']}** | {r['shares']:,} | ₹{r['reference_price']:,.2f} | "
                    f"₹{r['gross_value']:,.2f} | ₹{r['total_friction']:,.2f} | ₹{abs(r['net_cash_impact']):,.2f} | "
                    f"{r['current_rank']} | {r['reason']} |"
                )
            lines.append("")

        if not holds.empty:
            lines.extend([
                f"### C. Retained Holdings (HOLD / No Action Required)",
                f"| Symbol | Shares | Current Price | Market Value | Current Rank | Retention Rationale |",
                f"| :--- | :--- | :--- | :--- | :--- | :--- |"
            ])
            for _, r in holds.iterrows():
                lines.append(
                    f"| **{r['symbol']}** | {r['shares']:,} | ₹{r['reference_price']:,.2f} | "
                    f"₹{r['gross_value']:,.2f} | {r['current_rank']} | {r['reason']} |"
                )
            lines.append("")

        lines.extend([
            f"---",
            f"",
            f"## 3. Statutory Fee & Frictional Breakdown",
            f"",
            f"| Charge Component | Rate / Rule | Estimated Amount |",
            f"| :--- | :--- | :--- |",
            f"| **Brokerage** | 0.03% on delivery | ₹{orders_df['brokerage'].sum():,.2f} |",
            f"| **Securities Transaction Tax (STT)** | 0.10% on delivery Buy & Sell | ₹{orders_df['stt'].sum():,.2f} |",
            f"| **Stamp Duty** | 0.015% on delivery Buy | ₹{orders_df['stamp_duty'].sum():,.2f} |",
            f"| **Exchange Turnover Charges** | 0.00345% on turnover | ₹{orders_df['exchange_charges'].sum():,.2f} |",
            f"| **SEBI Turnover Charges** | 0.0001% on turnover | ₹{orders_df['sebi_charges'].sum():,.2f} |",
            f"| **Goods & Services Tax (GST)** | 18% on (Brokerage + Exchange + SEBI)| ₹{orders_df['gst'].sum():,.2f} |",
            f"| **Depository Participant (DP) Charges**| ₹15.93 per sell ticket | ₹{orders_df['dp_charges'].sum():,.2f} |",
            f"| **Execution Slippage Buffer** | 15 bps (0.15%) | ₹{orders_df['slippage_buffer'].sum():,.2f} |",
            f"| **Total Transaction Friction** | **Itemized Aggregate** | **₹{total_friction:,.2f}** |",
            f"",
            f"---",
            f"*Generated by Project MIP Production Execution Engine (`deliverables/phase_8/scripts/generate_execution_orders.py`).*"
        ])

        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Portfolio Rebalance & Execution Order Generator")
    parser.add_argument("--screener-csv", type=str, default=str(DEFAULT_SCREENER_CSV), help="Path to screener CSV")
    parser.add_argument("--holdings", type=str, default=None, help="Path to current holdings JSON/CSV")
    parser.add_argument("--aum", type=float, default=10_000_000.0, help="Total Portfolio AUM in INR")
    parser.add_argument("--slots", type=int, default=20, help="Target portfolio positions")
    parser.add_argument("--exit-buffer", type=int, default=40, help="Exit Rank cutoff")
    parser.add_argument("--as-of-date", type=str, default="2026-08-21", help="Signal Date")
    parser.add_argument("--force-deploy", action="store_true", help="Force new entries even if regime is defensive")
    parser.add_argument("--output-csv", type=str, default=str(DEFAULT_ORDERS_CSV), help="Destination orders CSV")
    parser.add_argument("--output-md", type=str, default=str(DEFAULT_MEMO_MD), help="Destination trade memo MD")

    args = parser.parse_args()
    engine = ExecutionOrderGenerator(
        portfolio_aum=args.aum,
        target_slots=args.slots,
        exit_rank_buffer=args.exit_buffer
    )
    engine.generate_orders(
        screener_csv=Path(args.screener_csv),
        holdings_path=Path(args.holdings) if args.holdings else None,
        as_of_date=args.as_of_date,
        force_deploy=args.force_deploy,
        orders_csv=Path(args.output_csv),
        memo_md=Path(args.output_md)
    )


if __name__ == "__main__":
    main()
