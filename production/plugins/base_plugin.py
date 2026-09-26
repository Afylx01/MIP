#!/usr/bin/env python3
"""
production/plugins/base_plugin.py
Standard abstract plugin interface for quantitative filter extensions in Project MIP.
"""

from abc import ABC, abstractmethod
import pandas as pd


class FilterPlugin(ABC):
    """Abstract base class for all pluggable screening and ranking filters."""

    def __init__(self, name: str, enabled: bool = True):
        self.name = name
        self.enabled = enabled

    @abstractmethod
    def evaluate(self, universe_df: pd.DataFrame, as_of_date: str) -> pd.DataFrame:
        """
        Takes the universe price dataframe and returns the dataframe with:
          - A boolean column 'passed_<plugin_name>'
          - Additional diagnostic indicator columns
        """
        pass
