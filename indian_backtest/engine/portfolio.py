"""
indian_backtest.engine.portfolio
================================
Portfolio accounting state manager with integrated Rule R-3 mathematical identity validation.
"""

from typing import Dict, List, Optional
import pandas as pd

class Portfolio:
    def __init__(self, initial_capital: float = 10_000_000.0):
        self.initial_capital = float(initial_capital)
        self.cash = float(initial_capital)
        self.holdings: Dict[str, dict] = {}  # sym -> {shares, buy_price, buy_date, entry_rank}
        self.closed_trades: List[dict] = []
        self.daily_history: List[dict] = []
        self.trade_log: List[str] = []
        self.interest_earned: float = 0.0

    def add_interest(self, amount: float):
        """Credits risk-free cash yield to portfolio and records for Rule R-3 accounting."""
        self.cash += amount
        self.interest_earned += amount

    def get_portfolio_value(self, current_date: str, price_lookup: Dict) -> float:
        """
        Computes total portfolio value (cash + marked-to-market holdings at close).
        """
        val = self.cash
        for sym, pos in self.holdings.items():
            row = price_lookup.get((sym, current_date))
            px = row["close"] if row else pos["buy_price"]
            val += pos["shares"] * px
        return val

    def record_daily_valuation(self, current_date: str, price_lookup: Dict):
        """
        Records daily snapshot for equity curve and drawdown metrics.
        """
        val = self.get_portfolio_value(current_date, price_lookup)
        self.daily_history.append({
            "date": current_date,
            "value": val,
            "cash": self.cash,
            "holdings_count": len(self.holdings)
        })

    def open_position(self, symbol: str, shares: int, buy_price: float, buy_date: str, entry_rank: int, friction: float = 0.0):
        """
        Deducts cash and adds new stock position.
        """
        cost = (shares * buy_price) + friction
        self.cash -= cost
        self.holdings[symbol] = {
            "shares": shares,
            "buy_price": buy_price,
            "buy_date": buy_date,
            "entry_rank": entry_rank,
            "entry_friction": friction
        }
        self.trade_log.append(
            f"BUY : {buy_date} | {symbol:<12} | {shares:>6} shs @ {buy_price:>8.2f} | Rank: {entry_rank:>2} | Cost: {cost:>11.2f}"
        )

    def close_position(self, symbol: str, sell_price: float, sell_date: str, exit_reason: str, friction: float = 0.0):
        """
        Removes stock position, credits cash, and logs closed trade.
        """
        pos = self.holdings.pop(symbol)
        shs = pos["shares"]
        proceeds = (shs * sell_price) - friction
        self.cash += proceeds
        entry_cost = (shs * pos["buy_price"]) + pos.get("entry_friction", 0.0)
        pnl = proceeds - entry_cost

        trade_record = {
            "symbol": symbol,
            "buy_date": pos["buy_date"],
            "buy_price": pos["buy_price"],
            "sell_date": sell_date,
            "sell_price": sell_price,
            "shares": shs,
            "pnl": pnl,
            "exit_reason": exit_reason,
            "total_friction": pos.get("entry_friction", 0.0) + friction
        }
        self.closed_trades.append(trade_record)
        self.trade_log.append(
            f"SELL: {sell_date} | {symbol:<12} | {shs:>6} shs @ {sell_price:>8.2f} | PnL: {pnl:>11.2f} ({exit_reason})"
        )

    def compute_accounting_identity(self, final_date: str, price_lookup: Dict) -> dict:
        """
        Standing Rule R-3 Accounting Identity:
            initial_capital + realized_pnl - tax + dividends + unrealized_pnl == final_value
        Residual must satisfy abs(residual) < 1e-6 (strictly 0.00).
        """
        final_val = self.cash
        unrealized_pnl = 0.0
        for sym, pos in self.holdings.items():
            r = price_lookup.get((sym, final_date))
            px = r["close"] if r else pos["buy_price"]
            val = pos["shares"] * px
            final_val += val
            unrealized_pnl += (pos["shares"] * (px - pos["buy_price"])) - pos.get("entry_friction", 0.0)

        realized_pnl = sum(t["pnl"] for t in self.closed_trades)
        net_profit = final_val - self.initial_capital
        residual = (self.initial_capital + realized_pnl + unrealized_pnl + self.interest_earned) - final_val

        return {
            "initial_capital": self.initial_capital,
            "final_value": final_val,
            "net_profit": net_profit,
            "realized_pnl": realized_pnl,
            "unrealized_pnl": unrealized_pnl,
            "tax": 0.0,
            "dividends": self.interest_earned,
            "residual": residual,
            "is_valid_r3": (abs(residual) < 1e-6)
        }
