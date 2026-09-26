"""
indian_backtest.data.calendar_manager
====================================
NSE trading calendar scheduler and monthly rebalance snapshot generator.
"""

from pathlib import Path
from typing import List, Optional

class CalendarManager:
    def __init__(self, base_dir: Optional[Path] = None, use_bhavcopy_calendar: bool = False):
        self.base_dir = base_dir or Path("/storage/emulated/0/Documents/Project MIP")
        self.calendar_path = self.base_dir / "data/trading_calendar.txt"
        self.bhavcopy_path = self.base_dir / "data/adjusted_bhavcopy_max_2007_2026.parquet"
        self.use_bhavcopy_calendar = use_bhavcopy_calendar
        self._all_trading_days: List[str] = []
        self._load_calendar()

    def _load_calendar(self):
        if self.use_bhavcopy_calendar and self.bhavcopy_path.exists():
            import pandas as pd
            df = pd.read_parquet(self.bhavcopy_path, columns=["date"])
            self._all_trading_days = sorted(df["date"].unique().tolist())
        else:
            with open(self.calendar_path, "r", encoding="utf-8") as f:
                self._all_trading_days = sorted([line.strip() for line in f if line.strip()])

    def get_trading_days(self, start_date: str, end_date: str) -> List[str]:
        """
        Returns all valid trading days within [start_date, end_date].
        """
        return [d for d in self._all_trading_days if start_date <= d <= end_date]

    def get_monthly_rebalance_snapshots(self, start_date: str, end_date: str) -> List[str]:
        """
        Returns the first trading day of each calendar month within [start_date, end_date].
        """
        window_days = self.get_trading_days(start_date, end_date)
        months_seen = set()
        snapshot_dates = []

        for d in window_days:
            ym = d[:7]  # YYYY-MM
            if ym not in months_seen:
                months_seen.add(ym)
                snapshot_dates.append(d)

        return snapshot_dates

    def get_next_trading_day(self, current_date: str) -> Optional[str]:
        """
        Returns the immediately subsequent trading day for next-day open execution.
        """
        try:
            idx = self._all_trading_days.index(current_date)
            if idx + 1 < len(self._all_trading_days):
                return self._all_trading_days[idx + 1]
        except ValueError:
            pass
        return None
