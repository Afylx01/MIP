#!/usr/bin/env python3
"""
deliverables/phase_8/scripts/manage_portfolio_ledger.py
Phase 8 Task 4: Persistent Portfolio Ledger & Execution Simulator

Maintains the persistent institutional portfolio ledger:
  - Tracks holdings, average cost basis, current market value, unrealized P&L, and portfolio weights.
  - Simulates execution fills at Monday Open with exact itemized statutory costs.
  - Enforces Rule R-3 Cash Conservation:
      Total Portfolio Value == Invested Market Value + Cash Balance
      (Initial Capital + Cumulative Realized P&L + Unrealized P&L) - Total Portfolio Value == 0.00

Outputs:
  - deliverables/phase_8/data_csv/portfolio_ledger_sample.csv
  - deliverables/phase_8/data_csv/portfolio_state.json
  - deliverables/phase_8/raw/manage_portfolio_ledger.log
"""

import sys
import os
import json
import argparse
import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np

BASE_DIR = Path("/storage/emulated/0/Documents/Project MIP")
DELIV_DIR = BASE_DIR / "deliverables/phase_8"
DATA_CSV_DIR = DELIV_DIR / "data_csv"
RAW_DIR = DELIV_DIR / "raw"

DEFAULT_STATE_JSON = DATA_CSV_DIR / "portfolio_state.json"
DEFAULT_LEDGER_CSV = DATA_CSV_DIR / "portfolio_ledger_sample.csv"
LOG_FILE = RAW_DIR / "manage_portfolio_ledger.log"

# Import FeeCalculator from Task 3
if str(DELIV_DIR / "scripts") not in sys.path:
    sys.path.insert(0, str(DELIV_DIR / "scripts"))
from generate_execution_orders import FeeCalculator


class PortfolioLedger:
    """Institutional portfolio ledger and execution manager enforcing Rule R-3."""

    def __init__(
        self,
        state_file: Optional[Path] = DEFAULT_STATE_JSON,
        initial_capital: float = 10_000_000.0
    ):
        self.state_file = Path(state_file) if state_file else DEFAULT_STATE_JSON
        self.initial_capital = float(initial_capital)
        RAW_DIR.mkdir(parents=True, exist_ok=True)
        DATA_CSV_DIR.mkdir(parents=True, exist_ok=True)

        # State fields
        self.as_of_date = ""
        self.cash_balance = self.initial_capital
        self.holdings: Dict[str, dict] = {}
        self.closed_trades: List[dict] = []
        self.cumulative_realized_pnl = 0.0
        self.cumulative_friction = 0.0
        self.peak_value = self.initial_capital

        if self.state_file.exists():
            self.load_state(self.state_file)

    def log(self, msg: str, to_console: bool = True):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted = f"[{timestamp}] {msg}"
        if to_console:
            print(formatted)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(formatted + "\n")

    def load_state(self, path: Path):
        """Loads state from JSON."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.as_of_date = data.get("as_of_date", "")
        self.initial_capital = float(data.get("initial_capital", self.initial_capital))
        self.cash_balance = float(data.get("cash_balance", self.initial_capital))
        self.holdings = data.get("holdings", {})
        self.closed_trades = data.get("closed_trades", [])
        self.cumulative_realized_pnl = float(data.get("cumulative_realized_pnl", 0.0))
        self.cumulative_friction = float(data.get("cumulative_friction", 0.0))
        self.peak_value = float(data.get("peak_value", self.initial_capital))
        self.log(f"Loaded persistent ledger state from {path} (Date: {self.as_of_date}, Cash: ₹{self.cash_balance:,.2f})")

    def save_state(self, path: Optional[Path] = None):
        """Saves current state to JSON."""
        dest = Path(path) if path else self.state_file
        state_dict = {
            "as_of_date": self.as_of_date,
            "initial_capital": float(self.initial_capital),
            "cash_balance": float(self.cash_balance),
            "holdings": self.holdings,
            "closed_trades": self.closed_trades,
            "cumulative_realized_pnl": float(self.cumulative_realized_pnl),
            "cumulative_friction": float(self.cumulative_friction),
            "peak_value": float(self.peak_value)
        }
        with open(dest, "w", encoding="utf-8") as f:
            json.dump(state_dict, f, indent=2)
        self.log(f"Saved persistent ledger state to {dest}")

    def execute_orders(
        self,
        orders_df: pd.DataFrame,
        execution_date: str,
        fill_prices: Optional[Dict[str, float]] = None
    ) -> Dict:
        """
        Simulates fills for orders on execution_date.
        fill_prices: {symbol: open_price}. If omitted, reference_price from orders is used.
        """
        self.log("==================================================================")
        self.log(f"EXECUTING ORDER TICKETS ON {execution_date}")
        self.log("==================================================================")

        fill_map = fill_prices or {}
        sells = orders_df[orders_df["action"] == "SELL"]
        buys = orders_df[orders_df["action"] == "BUY"]

        # 1. Execute Sells First (to release cash)
        for _, order in sells.iterrows():
            sym = str(order["symbol"]).strip()
            shares = int(order["shares"])
            ref_px = float(order["reference_price"])
            fill_px = float(fill_map.get(sym, ref_px))

            if sym not in self.holdings:
                self.log(f"⚠️ Warning: Attempted to sell {sym} which is not in holdings. Skipping.")
                continue

            holding = self.holdings[sym]
            held_shares = int(holding["shares"])
            cost_px = float(holding["avg_cost_price"])

            actual_shares = min(shares, held_shares)
            gross_proceeds = actual_shares * fill_px
            fees = FeeCalculator.calculate_trade_fees("SELL", gross_proceeds)
            friction = fees["total_friction"]
            net_inflow = gross_proceeds - friction

            # Net realized PnL = (Proceeds - Cost) - Friction
            trade_realized_pnl = (actual_shares * fill_px) - (actual_shares * cost_px) - friction

            self.cash_balance += net_inflow
            self.cumulative_realized_pnl += trade_realized_pnl
            self.cumulative_friction += friction

            self.closed_trades.append({
                "symbol": sym,
                "shares": actual_shares,
                "buy_price": cost_px,
                "sell_price": fill_px,
                "entry_date": holding.get("entry_date", ""),
                "exit_date": execution_date,
                "gross_pnl": (actual_shares * fill_px) - (actual_shares * cost_px),
                "friction_paid": friction,
                "net_pnl": trade_realized_pnl,
                "pnl_pct": ((fill_px / cost_px - 1.0) * 100.0) if cost_px > 0 else 0.0,
                "exit_reason": order.get("reason", "ORDER_EXIT")
            })

            # Update holding
            remaining_shares = held_shares - actual_shares
            if remaining_shares <= 0:
                del self.holdings[sym]
            else:
                self.holdings[sym]["shares"] = remaining_shares

            self.log(f"SELL: {sym} x {actual_shares:,} @ ₹{fill_px:,.2f} | Net Proceeds: ₹{net_inflow:,.2f} | PnL: ₹{trade_realized_pnl:,.2f}")

        # 2. Execute Buys Next
        for _, order in buys.iterrows():
            sym = str(order["symbol"]).strip()
            shares = int(order["shares"])
            ref_px = float(order["reference_price"])
            fill_px = float(fill_map.get(sym, ref_px))

            gross_cost = shares * fill_px
            fees = FeeCalculator.calculate_trade_fees("BUY", gross_cost)
            friction = fees["total_friction"]
            total_required = gross_cost + friction

            # Check cash availability
            if total_required > self.cash_balance:
                # Clamp shares to available cash
                effective_px = fill_px * 1.003
                shares = int(self.cash_balance // effective_px)
                if shares <= 0:
                    self.log(f"⚠️ Insufficient cash to buy {sym} (Available: ₹{self.cash_balance:,.2f}). Skipping.")
                    continue
                gross_cost = shares * fill_px
                fees = FeeCalculator.calculate_trade_fees("BUY", gross_cost)
                friction = fees["total_friction"]
                total_required = gross_cost + friction

            self.cash_balance -= total_required
            self.cumulative_friction += friction
            # Buy friction is immediately accounted as a realized drag in cumulative_realized_pnl
            self.cumulative_realized_pnl -= friction

            # Record or append to holdings
            # Nominal avg_cost_price is fill_px so that market_value == shares * fill_px at entry
            if sym in self.holdings:
                curr_h = self.holdings[sym]
                old_sh = curr_h["shares"]
                old_cost = curr_h["avg_cost_price"]
                new_sh = old_sh + shares
                new_cost = ((old_sh * old_cost) + (shares * fill_px)) / new_sh
                curr_h["shares"] = new_sh
                curr_h["avg_cost_price"] = new_cost
            else:
                self.holdings[sym] = {
                    "shares": shares,
                    "avg_cost_price": fill_px,
                    "entry_date": execution_date,
                    "rank_at_entry": int(order.get("current_rank", 1)),
                    "friction_paid": friction
                }

            self.log(f"BUY:  {sym} x {shares:,} @ ₹{fill_px:,.2f} | Outlay: ₹{total_required:,.2f} (Friction: ₹{friction:,.2f})")

        self.as_of_date = execution_date
        return self.audit_accounting_identity(current_prices=fill_map)

    def audit_accounting_identity(self, current_prices: Optional[Dict[str, float]] = None) -> Dict:
        """
        Enforces Rule R-3 Cash Conservation and calculates portfolio tearsheet.
        """
        px_map = current_prices or {}
        invested_value = 0.0
        unrealized_pnl = 0.0

        for sym, h in self.holdings.items():
            sh = int(h["shares"])
            cost = float(h["avg_cost_price"])
            curr_px = float(px_map.get(sym, cost))
            mv = sh * curr_px
            u_pnl = sh * (curr_px - cost)

            invested_value += mv
            unrealized_pnl += u_pnl

        total_portfolio_value = invested_value + self.cash_balance
        if total_portfolio_value > self.peak_value:
            self.peak_value = total_portfolio_value

        drawdown = (total_portfolio_value / self.peak_value - 1.0) * 100.0 if self.peak_value > 0 else 0.0

        # Exact Rule R-3 Accounting Identity Check:
        # Total Portfolio Value == Initial Capital + Cumulative Realized P&L + Unrealized P&L
        theoretical_total = self.initial_capital + self.cumulative_realized_pnl + unrealized_pnl
        residual = total_portfolio_value - theoretical_total
        is_r3_valid = (abs(residual) < 0.01)

        audit_results = {
            "as_of_date": self.as_of_date,
            "initial_capital": self.initial_capital,
            "cash_balance": round(self.cash_balance, 2),
            "invested_market_value": round(invested_value, 2),
            "total_portfolio_value": round(total_portfolio_value, 2),
            "cumulative_realized_pnl": round(self.cumulative_realized_pnl, 2),
            "unrealized_pnl": round(unrealized_pnl, 2),
            "cumulative_friction": round(self.cumulative_friction, 2),
            "peak_value": round(self.peak_value, 2),
            "drawdown_pct": round(drawdown, 2),
            "accounting_residual": round(residual, 6),
            "is_rule_r3_valid": is_r3_valid
        }

        self.log("------------------------------------------------------------------")
        self.log(f"PORTFOLIO VALUATION & RULE R-3 ACCOUNTING AUDIT:")
        self.log(f"Invested Market Value:  ₹{invested_value:,.2f}")
        self.log(f"Cash Balance:           ₹{self.cash_balance:,.2f}")
        self.log(f"Total Portfolio Value:  ₹{total_portfolio_value:,.2f}")
        self.log(f"Cumulative Realized:    ₹{self.cumulative_realized_pnl:,.2f}")
        self.log(f"Unrealized P&L:         ₹{unrealized_pnl:,.2f}")
        self.log(f"Accounting Residual:    ₹{residual:,.6f}")
        self.log(f"Rule R-3 Compliance:    {'STRICT PASS (0.00 to the paisa)' if is_r3_valid else 'VIOLATION'}")
        self.log("------------------------------------------------------------------")

        if not is_r3_valid:
            raise AssertionError(f"Rule R-3 Cash Conservation Violated! Residual = ₹{residual:.6f}")

        return audit_results

    def export_ledger_csv(
        self,
        output_csv: Optional[Path] = None,
        current_prices: Optional[Dict[str, float]] = None
    ) -> pd.DataFrame:
        """
        Exports full portfolio holdings tearsheet to CSV.
        """
        dest_csv = Path(output_csv) if output_csv else DEFAULT_LEDGER_CSV
        px_map = current_prices or {}

        invested_val = sum(h["shares"] * px_map.get(s, h["avg_cost_price"]) for s, h in self.holdings.items())
        total_val = invested_val + self.cash_balance

        rows = []
        for sym, h in self.holdings.items():
            sh = int(h["shares"])
            cost = float(h["avg_cost_price"])
            curr_px = float(px_map.get(sym, cost))
            mv = sh * curr_px
            u_pnl = sh * (curr_px - cost)
            u_pnl_pct = (curr_px / cost - 1.0) * 100.0 if cost > 0 else 0.0
            wt = (mv / total_val * 100.0) if total_val > 0 else 0.0

            rows.append({
                "symbol": sym,
                "shares": sh,
                "avg_cost_price": round(cost, 2),
                "current_price": round(curr_px, 2),
                "market_value": round(mv, 2),
                "unrealized_pnl": round(u_pnl, 2),
                "pnl_pct": round(u_pnl_pct, 2),
                "allocation_pct": round(wt, 2),
                "rank_at_entry": int(h.get("rank_at_entry", 0)),
                "entry_date": h.get("entry_date", "")
            })

        df = pd.DataFrame(rows)
        if not df.empty:
            df = df.sort_values(by="allocation_pct", ascending=False).reset_index(drop=True)

        # Append Cash Row
        cash_wt = (self.cash_balance / total_val * 100.0) if total_val > 0 else 0.0
        cash_row = pd.DataFrame([{
            "symbol": "CASH_INR",
            "shares": 1,
            "avg_cost_price": round(self.cash_balance, 2),
            "current_price": round(self.cash_balance, 2),
            "market_value": round(self.cash_balance, 2),
            "unrealized_pnl": 0.0,
            "pnl_pct": 0.0,
            "allocation_pct": round(cash_wt, 2),
            "rank_at_entry": 0,
            "entry_date": self.as_of_date
        }])

        # Append Total Row
        u_pnl_total = df["unrealized_pnl"].sum() if not df.empty else 0.0
        u_pnl_total_pct = (u_pnl_total / (total_val - self.cash_balance) * 100.0) if (total_val - self.cash_balance) > 0 else 0.0
        total_row = pd.DataFrame([{
            "symbol": "TOTAL_PORTFOLIO",
            "shares": int(df["shares"].sum()) if not df.empty else 0,
            "avg_cost_price": round(total_val, 2),
            "current_price": round(total_val, 2),
            "market_value": round(total_val, 2),
            "unrealized_pnl": round(u_pnl_total, 2),
            "pnl_pct": round(u_pnl_total_pct, 2),
            "allocation_pct": 100.0,
            "rank_at_entry": 0,
            "entry_date": self.as_of_date
        }])

        full_df = pd.concat([df, cash_row, total_row], ignore_index=True)
        full_df.to_csv(dest_csv, index=False)
        self.log(f"Exported portfolio ledger CSV to {dest_csv}")
        return full_df


def main():
    parser = argparse.ArgumentParser(description="Persistent Portfolio Ledger Manager")
    parser.add_argument("--state-json", type=str, default=str(DEFAULT_STATE_JSON), help="Path to state JSON")
    parser.add_argument("--orders-csv", type=str, default=None, help="Path to execution orders CSV to apply")
    parser.add_argument("--execution-date", type=str, default="2026-08-24", help="Execution fill date")
    parser.add_argument("--output-csv", type=str, default=str(DEFAULT_LEDGER_CSV), help="Destination ledger CSV")
    parser.add_argument("--initial-capital", type=float, default=10_000_000.0, help="Initial capital in INR")

    args = parser.parse_args()
    ledger = PortfolioLedger(
        state_file=Path(args.state_json),
        initial_capital=args.initial_capital
    )

    if args.orders_csv and Path(args.orders_csv).exists():
        orders_df = pd.read_csv(args.orders_csv)
        ledger.execute_orders(orders_df, execution_date=args.execution_date)
        ledger.save_state()
        ledger.export_ledger_csv(output_csv=Path(args.output_csv))
    else:
        ledger.audit_accounting_identity()
        ledger.export_ledger_csv(output_csv=Path(args.output_csv))


if __name__ == "__main__":
    main()
