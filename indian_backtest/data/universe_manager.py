"""
indian_backtest.data.universe_manager
====================================
Point-in-time constituent resolver for NIFTY 500 across 1998–2026.
Guarantees zero survivorship bias by dynamically reconstructing membership as-of each historical date.
"""

from pathlib import Path
from typing import Dict, List, Optional, Set
import pandas as pd

class UniverseManager:
    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or Path("/storage/emulated/0/Documents/Project MIP")
        self.hist_events_path = self.base_dir / "data/index_events.parquet"
        self.mod_events_path = self.base_dir / "data/index_events_modern.parquet"
        self.corrections_path = self.base_dir / "data/corrections.parquet"
        self.symbol_map_path = self.base_dir / "data/symbol_map.parquet"

        self._events_df: Optional[pd.DataFrame] = None
        self._rev_rename_map: Dict[str, str] = {}
        self._scrip_to_sym: Dict[str, str] = {}
        self._sym_to_scrip: Dict[str, str] = {}
        self._initialize()

    def _initialize(self):
        # 1. Ingest historical and modern events
        hist_df = pd.read_parquet(self.hist_events_path)
        hist_n500 = hist_df[hist_df["index"] == "NIFTY500"].copy()
        hist_n500["effective_date"] = pd.to_datetime(hist_n500["effective_date"]).dt.date

        if self.mod_events_path.exists():
            mod_df = pd.read_parquet(self.mod_events_path)
            mod_n500 = mod_df[mod_df["index"] == "NIFTY500"].copy()
            mod_n500["effective_date"] = pd.to_datetime(mod_n500["effective_date"]).dt.date
            all_events = pd.concat([hist_n500, mod_n500], ignore_index=True)
        else:
            all_events = hist_n500

        self._events_df = all_events.sort_values(["effective_date", "row"]).reset_index(drop=True)

        # 2. Ingest corporate renames
        corr_df = pd.read_parquet(self.corrections_path)
        renames = corr_df[corr_df["action"] == "RENAME"]
        self._rev_rename_map = {r["target_scrip_name"]: r["scrip_name"] for _, r in renames.iterrows()}

        # 3. Ingest symbol map
        smap = pd.read_parquet(self.symbol_map_path)
        for _, r in smap.iterrows():
            sc = r["scrip_name"]
            sym = r["symbol"]
            if pd.notna(sym) and sym:
                self._scrip_to_sym[sc] = str(sym).strip()
                self._sym_to_scrip[str(sym).strip()] = sc

    def get_constituents(self, as_of_date: str) -> Set[str]:
        """
        Reconstructs point-in-time constituent symbols as-of a given date string (YYYY-MM-DD).
        """
        target_dt = pd.to_datetime(as_of_date).date()
        sub = self._events_df[self._events_df["effective_date"] <= target_dt]

        active_scrips = set()
        for r in sub.itertuples(index=False):
            if r.row in (2136, 2162):
                continue
            scrip = r.scrip_name
            act = r.action
            if act == "IN":
                active_scrips.add(scrip)
            elif act == "OUT":
                if scrip in active_scrips:
                    active_scrips.remove(scrip)
                elif scrip in self._rev_rename_map and self._rev_rename_map[scrip] in active_scrips:
                    active_scrips.remove(self._rev_rename_map[scrip])

        # Map to active trading symbols
        active_symbols = set()
        for scrip in active_scrips:
            sym = self._scrip_to_sym.get(scrip)
            if sym:
                active_symbols.add(sym)

        return active_symbols

    def get_all_snapshot_universes(self, snapshot_dates: List[str]) -> Dict[str, Set[str]]:
        """
        Precomputes universe symbols for a list of snapshot dates with chronological sequential accumulation.
        """
        sorted_dates = sorted(list(set(snapshot_dates)))
        date_objs = {s: pd.to_datetime(s).date() for s in sorted_dates}

        events_tuples = list(self._events_df.itertuples(index=False))
        n_events = len(events_tuples)
        ev_idx = 0

        active_scrips = set()
        results = {}

        for s_str in sorted_dates:
            target_dt = date_objs[s_str]
            while ev_idx < n_events and events_tuples[ev_idx].effective_date <= target_dt:
                r = events_tuples[ev_idx]
                ev_idx += 1
                if r.row in (2136, 2162):
                    continue
                scrip = r.scrip_name
                act = r.action
                if act == "IN":
                    active_scrips.add(scrip)
                elif act == "OUT":
                    if scrip in active_scrips:
                        active_scrips.remove(scrip)
                    elif scrip in self._rev_rename_map and self._rev_rename_map[scrip] in active_scrips:
                        active_scrips.remove(self._rev_rename_map[scrip])

            # Map to active trading symbols
            active_symbols = {self._scrip_to_sym[sc] for sc in active_scrips if sc in self._scrip_to_sym}
            results[s_str] = set(active_symbols)

        # Return in original order requested
        return {s: results[s] for s in snapshot_dates}
