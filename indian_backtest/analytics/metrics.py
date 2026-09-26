"""
indian_backtest.analytics.metrics
=================================
Quantitative performance analytics: CAGR, Max Drawdown, Sharpe, Sortino, Calmar, Win Rate, Profit Factor.
"""

from typing import Dict, List
import numpy as np
import pandas as pd

def calculate_performance_metrics(
    daily_history: List[dict],
    closed_trades: List[dict],
    initial_capital: float,
    final_value: float,
    start_date: str,
    final_date: str
) -> dict:
    """
    Computes institutional performance statistics.
    """
    d_df = pd.DataFrame(daily_history)
    if d_df.empty:
        return {}

    d_df["ret"] = d_df["value"].pct_change().fillna(0.0)
    std_ret = d_df["ret"].std()
    mean_ret = d_df["ret"].mean()

    # Sharpe Ratio (annualized, 252 trading days)
    sharpe = (mean_ret / std_ret * np.sqrt(252)) if std_ret > 0 else 0.0

    # Downside deviation & Sortino Ratio
    neg_ret = d_df["ret"][d_df["ret"] < 0]
    downside_std = neg_ret.std() if len(neg_ret) > 0 else 0.0
    sortino = (mean_ret / downside_std * np.sqrt(252)) if downside_std > 0 else 0.0

    # Peak & Maximum Drawdown
    d_df["peak"] = d_df["value"].cummax()
    d_df["dd"] = (d_df["value"] - d_df["peak"]) / d_df["peak"]
    max_dd = abs(d_df["dd"].min()) * 100.0

    # Elapsed Years & CAGR
    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(final_date)
    years = (end_dt - start_dt).days / 365.25
    cagr = ((final_value / initial_capital) ** (1.0 / years) - 1.0) * 100.0 if years > 0 else 0.0

    # Calmar Ratio
    calmar = (cagr / max_dd) if max_dd > 0 else 0.0

    # Trade Statistics
    n_trades = len(closed_trades)
    winning_trades = [t for t in closed_trades if t["pnl"] > 0]
    losing_trades = [t for t in closed_trades if t["pnl"] < 0]
    win_rate = (len(winning_trades) / n_trades * 100.0) if n_trades > 0 else 0.0

    gross_profit = sum(t["pnl"] for t in winning_trades)
    gross_loss = abs(sum(t["pnl"] for t in losing_trades))
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (999.0 if gross_profit > 0 else 0.0)

    # Average trade holding days
    holding_days = []
    for t in closed_trades:
        b_dt = pd.to_datetime(t["buy_date"])
        s_dt = pd.to_datetime(t["sell_date"])
        holding_days.append((s_dt - b_dt).days)
    avg_holding_days = float(np.mean(holding_days)) if holding_days else 0.0

    return {
        "start_date": start_date,
        "final_date": final_date,
        "years": round(years, 4),
        "initial_capital": initial_capital,
        "final_value": final_value,
        "net_profit": final_value - initial_capital,
        "cagr": round(cagr, 2),
        "max_dd": round(max_dd, 2),
        "sharpe": round(sharpe, 2),
        "sortino": round(sortino, 2),
        "calmar": round(calmar, 2),
        "total_closed_trades": n_trades,
        "winning_trades": len(winning_trades),
        "losing_trades": len(losing_trades),
        "win_rate_pct": round(win_rate, 2),
        "profit_factor": round(profit_factor, 2),
        "avg_holding_days": round(avg_holding_days, 1)
    }
