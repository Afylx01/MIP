"""
indian_backtest.analytics.tearsheet
===================================
Institutional tearsheet report formatter for comparative multi-strategy backtest results.
"""

from typing import Dict, List
import pandas as pd

def format_strategy_tearsheet(
    label: str,
    metrics: dict,
    accounting: dict,
    sample_trades: List[dict],
    held_positions: Dict[str, dict]
) -> str:
    """
    Formats complete single-strategy execution tearsheet report.
    """
    lines = []
    lines.append("=" * 80)
    lines.append(f"MIP-RETURN-10Y / PODCAST MOMENTUM STRATEGY TEARSHEET: {label}")
    lines.append("=" * 80)
    lines.append(f"Backtest Period: {metrics.get('start_date')} to {metrics.get('final_date')} ({metrics.get('years')} years)")
    lines.append(f"Universe: Point-in-Time NIFTY 500 Constituents (Zero Survivorship Bias)")
    lines.append(f"Portfolio Constraints: N=20, Rebalance=Monthly, Execution=Next-Day Open, ExitRank=40")

    lines.append("\n[PERFORMANCE METRICS]")
    lines.append(f"  Initial Capital:       Rs. {metrics.get('initial_capital', 0.0):>14,.2f}")
    lines.append(f"  Final Portfolio Value: Rs. {metrics.get('final_value', 0.0):>14,.2f}")
    lines.append(f"  Net Profit:            Rs. {metrics.get('net_profit', 0.0):>14,.2f}")
    lines.append(f"  CAGR:                        {metrics.get('cagr', 0.0):>10.2f}%")
    lines.append(f"  Max Drawdown:                {metrics.get('max_dd', 0.0):>10.2f}%")
    lines.append(f"  Sharpe Ratio:                {metrics.get('sharpe', 0.0):>10.2f}")
    lines.append(f"  Sortino Ratio:               {metrics.get('sortino', 0.0):>10.2f}")
    lines.append(f"  Calmar Ratio:                {metrics.get('calmar', 0.0):>10.2f}")

    lines.append("\n[TRADE & ACTIVITY STATISTICS]")
    lines.append(f"  Total Closed Trades:         {metrics.get('total_closed_trades', 0):>10}")
    lines.append(f"  Winning Trades:              {metrics.get('winning_trades', 0):>10} ({metrics.get('win_rate_pct', 0.0):.1f}%)")
    lines.append(f"  Losing Trades:               {metrics.get('losing_trades', 0):>10}")
    lines.append(f"  Profit Factor:               {metrics.get('profit_factor', 0.0):>10.2f}")
    lines.append(f"  Avg Holding Period:          {metrics.get('avg_holding_days', 0.0):>10.1f} calendar days")

    lines.append("\n[ACCOUNTING IDENTITY BLOCK (Standing Rule R-3)]")
    lines.append(f"  Initial Capital:       Rs. {accounting.get('initial_capital', 0.0):>14,.2f}")
    lines.append(f"  + Realized PnL:        Rs. {accounting.get('realized_pnl', 0.0):>14,.2f}")
    lines.append(f"  - Tax:                 Rs. {accounting.get('tax', 0.0):>14,.2f}")
    lines.append(f"  + Dividends:           Rs. {accounting.get('dividends', 0.0):>14,.2f}")
    lines.append(f"  + Unrealized PnL:      Rs. {accounting.get('unrealized_pnl', 0.0):>14,.2f}")
    lines.append(f"  = Final Value:         Rs. {accounting.get('final_value', 0.0):>14,.2f}")
    lines.append(f"  Residual:                    {accounting.get('residual', 0.0):>14.8f} (assert == 0.00)")

    lines.append(f"\n[SAMPLE CLOSED TRADES (First 20 executions)]")
    for t in sample_trades[:20]:
        lines.append(
            f"  {t['sell_date']} | {t['symbol']:<10} | {t['shares']:>5} shs | Entry: {t['buy_date']} @ {t['buy_price']:>7.2f} -> Exit: {t['sell_price']:>7.2f} | PnL: {t['pnl']:>10.2f} ({t['exit_reason']})"
        )

    lines.append(f"\n[OPEN POSITIONS AT END ({metrics.get('final_date')})]")
    for sym, pos in sorted(held_positions.items()):
        lines.append(f"  HELD: {sym:<12} | {pos['shares']:>6} shs | Entry: {pos['buy_date']} @ {pos['buy_price']:.2f}")

    lines.append("=" * 80)
    return "\n".join(lines)
