"""
indian_backtest
===============
Production-grade rule-based momentum backtesting engine for the Indian equity market (NSE NIFTY 500).

Modules:
    - data: Bhavcopy bar reader, point-in-time universe manager, calendar manager
    - indicators: Moving averages (EMA 200), 52-week price channels (High 252), Relative Strength (RS)
    - engine: Portfolio accounting, rebalancing rules, execution modeling, market regime filter
    - analytics: Performance statistics, tearsheet generator, Rule R-3 accounting assertion
"""

__version__ = "1.0.0"
__author__ = "Project MIP Team"
