"""
indian_backtest.engine.execution
================================
Order execution modeling implementing Rule R8 (Next-Day Open execution) and friction modeling.
"""

from typing import Optional, Tuple

class ExecutionEngine:
    def __init__(
        self,
        slippage_bps: float = 10.0,      # 10 bps = 0.10% slippage on open price
        statutory_costs: bool = True,    # Statutory STT, turnover charges, stamp duty
        cost_multiplier: float = 1.0     # Multiplier for 2x/3x stress tests
    ):
        self.slippage_bps = slippage_bps
        self.cost_multiplier = cost_multiplier
        self.slippage_rate = (slippage_bps / 10_000.0) * cost_multiplier
        self.statutory_costs = statutory_costs

    def get_execution_price(self, row: dict, mode: str = "open") -> float:
        """
        Retrieves base execution price based on execution mode:
          - 'open': Open price
          - 'vwap': (Open + High + Low + Close) / 4 approximation
        """
        if not row:
            return 0.0
        if mode == "vwap":
            o = row.get("open", 0.0)
            h = row.get("high", o)
            l = row.get("low", o)
            c = row.get("close", o)
            if o > 0 and h > 0 and l > 0 and c > 0:
                return (o + h + l + c) / 4.0
            return o if o > 0 else c
        return row.get("open", 0.0)

    def calculate_buy_execution(self, open_price: float, allocated_cash: float) -> Tuple[int, float, float]:
        """
        Calculates execution price, integer share count, and total friction cost on entry.
        Returns: (shares, effective_buy_price, friction_cost)
        """
        if open_price <= 0 or allocated_cash <= 0:
            return 0, 0.0, 0.0

        # Slippage penalty: buyer pays slightly higher
        exec_price = open_price * (1.0 + self.slippage_rate)
        
        # Stamp duty on delivery buy (0.015% base * cost_multiplier)
        buy_charges_rate = (0.00015 * self.cost_multiplier) if self.statutory_costs else 0.0
        effective_price_per_share = exec_price * (1.0 + buy_charges_rate)

        shares = int(allocated_cash // effective_price_per_share)
        if shares <= 0:
            return 0, 0.0, 0.0

        total_cost_nominal = shares * open_price
        total_friction = (shares * exec_price * (1.0 + buy_charges_rate)) - total_cost_nominal

        return shares, exec_price, total_friction

    def calculate_sell_execution(self, open_price: float, shares: int) -> Tuple[float, float]:
        """
        Calculates execution price and total friction cost on exit.
        Returns: (effective_sell_price, friction_cost)
        """
        if open_price <= 0 or shares <= 0:
            return 0.0, 0.0

        # Slippage penalty: seller receives slightly lower
        exec_price = open_price * (1.0 - self.slippage_rate)

        # STT (0.10%) + Exchange/SEBI/GST (~0.02%) on delivery sell = 0.12% base * cost_multiplier
        sell_charges_rate = (0.0012 * self.cost_multiplier) if self.statutory_costs else 0.0
        friction_charges = (shares * exec_price) * sell_charges_rate
        slippage_cost = (shares * open_price) - (shares * exec_price)
        total_friction = slippage_cost + friction_charges

        return exec_price, total_friction
