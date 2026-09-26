"""
indian_backtest.engine.regime_filter
====================================
Podcast Extension E4: Market Regime 200 EMA Cash Filter.
Protects capital during major bear markets (e.g. 2008 GFC, March 2020 COVID crash)
by halting new entries when the broader market index trades below its 200 EMA.
"""

from typing import Dict, Optional

class MarketRegimeFilter:
    def __init__(self, enabled: bool = True, ema_period: int = 20):
        self.enabled = enabled
        self.ema_period = ema_period

    def evaluate_regime(
        self,
        current_date: str,
        benchmark_lookup: Dict[str, dict]
    ) -> bool:
        """
        Evaluates whether market regime allows new entries on rebalance day.
        Returns:
            True: Risk-On / Bull Regime (Close >= EMA) -> New entries allowed.
            False: Risk-Off / Bear Regime (Close < EMA) -> NO new entries allowed (Cash filter active).
        """
        if not self.enabled:
            return True  # Filter disabled: always allow entries

        row = benchmark_lookup.get(current_date)
        if not row:
            return True  # If benchmark bar missing, default to allowing entries

        close = row.get("close", 0.0)
        ema_key = f"ema_{self.ema_period}"
        ema_val = row.get(ema_key, row.get("ema_200", 0.0))

        if ema_val <= 0:
            return True

        # Bull regime: close above or equal to EMA
        is_bullish = (close >= ema_val)
        return is_bullish
