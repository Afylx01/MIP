"""
indian_backtest.engine.rebalancer
=================================
Monthly momentum ranking, candidate selection, exit triggers, and equal-weight slot allocator.
"""

from typing import Dict, List, Optional, Set, Tuple
from indian_backtest.indicators.price_extremes import is_r2_satisfied
from indian_backtest.indicators.relative_strength import calculate_relative_strength

class Rebalancer:
    def __init__(
        self,
        portfolio_size: int = 20,
        exit_rank_multiplier: int = 2,
        use_relative_strength: bool = False,
        r2_factor: float = 0.80
    ):
        self.n_portfolio = portfolio_size
        self.exit_rank = portfolio_size * exit_rank_multiplier  # default: 40
        self.use_relative_strength = use_relative_strength
        self.r2_factor = r2_factor

    def evaluate_candidates(
        self,
        universe_symbols: Set[str],
        current_date: str,
        price_lookup: Dict,
        benchmark_lookup: Optional[Dict[str, dict]] = None,
        is_first_day: bool = False
    ) -> Tuple[List[dict], Dict[str, int]]:
        """
        Evaluates and ranks all eligible universe candidates on rebalance date.
        Returns:
            (pass_candidates, rank_map)
        """
        candidates = []
        b_ret = 0.0
        if benchmark_lookup and current_date in benchmark_lookup:
            b_ret = benchmark_lookup[current_date].get("ret_252", 0.0)

        for sym in universe_symbols:
            row = price_lookup.get((sym, current_date))
            if row is None:
                continue

            cl = row["close"]
            hi = row["high_252"]
            ema = row["ema_200"]
            ret_raw = row["day1_ret"] if is_first_day else row["ret_252"]

            # Strategy Filters
            r2_pass = is_r2_satisfied(cl, hi, self.r2_factor)
            r3_pass = (cl >= ema) if is_first_day else (cl > ema)

            # Ranking Metric: E1 Relative Strength vs Raw 252-day Return
            if self.use_relative_strength:
                rank_metric = calculate_relative_strength(ret_raw, b_ret)
            else:
                rank_metric = ret_raw

            candidates.append({
                "symbol": sym,
                "close": cl,
                "high_252": hi,
                "ema_200": ema,
                "ret": ret_raw,
                "rank_metric": rank_metric,
                "r2_pass": r2_pass,
                "r3_pass": r3_pass
            })

        # Rule R5: Rank descending by rank_metric, with deterministic symbol tie-breaker
        candidates.sort(key=lambda x: (-x["rank_metric"], x["symbol"]))
        rank_map = {c["symbol"]: i + 1 for i, c in enumerate(candidates)}
        pass_candidates = [c for c in candidates if c["r2_pass"] and c["r3_pass"]]

        return pass_candidates, rank_map

    def determine_exits(
        self,
        current_holdings: Dict[str, dict],
        universe_symbols: Set[str],
        current_date: str,
        price_lookup: Dict,
        rank_map: Dict[str, int]
    ) -> Tuple[List[Tuple[str, str]], List[str]]:
        """
        Evaluates held positions to determine exits and retentions.
        Returns:
            (exits_list, retained_list)
        """
        exits = []
        retained = []

        for sym, pos in list(current_holdings.items()):
            row = price_lookup.get((sym, current_date))
            sym_rank = rank_map.get(sym, 9999)

            if sym not in universe_symbols or row is None:
                exits.append((sym, "universe_exit"))
            elif not is_r2_satisfied(row["close"], row["high_252"], self.r2_factor):
                exits.append((sym, "r2_exit"))
            elif row["close"] <= row["ema_200"]:
                exits.append((sym, "r3_exit"))
            elif sym_rank > self.exit_rank:
                exits.append((sym, "rank_exit"))
            else:
                retained.append(sym)

        return exits, retained
