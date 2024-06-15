from pathlib import Path
import pandas as pd
import numpy as np
from stockfetcher.config import EposConfig, SkipModel


class Epos:
    def __init__(self, epos_config: EposConfig):
        self.epos_config = epos_config
        self.df = None

        self._load_epos(epos_config.epos_file)
        self._filter_families(epos_config.families)
        self._skip_models(epos_config.skip_models)
        self._filter_models(epos_config.model_filters)
        if epos_config.filter_single_model:
            self._filter_single_model(epos_config.filter_single_model)
        self._fix_whitespace()

    def _load_epos(self, epos_file: Path):
        self.df = pd.read_excel(io=epos_file, index_col=0, dtype=str)

    def _filter_families(self, families: list[str]):
        self.df = self.df[self.df["Family"].isin(families)]

    # @TODO remove for loop and use pandas magic
    def _skip_models(self, skip_models: list[SkipModel]):
        for skip_model in skip_models:
            self.df = self.df[
                ~(
                    (self.df["Model"] == skip_model.model)
                    & (self.df["Year"] == skip_model.year)
                )
            ]

    # @TODO improve name (filter vs skip)
    def _filter_models(self, model_filters: list[str]):
        """Remove models that we don't sell"""
        for model_filter in model_filters:
            self.df = self.df[~self.df["Model"].str.contains(model_filter)]

    def _filter_single_model(self, filter_single_model: str):
        """Optional: Only load a single model for quick testing"""
        self.df = self.df[self.df["Model"] == filter_single_model]

    def _fix_whitespace(self):
        """Convert double whitespace to single whitespace (Orbea sometimes makes mistakes)"""
        self.df["Summarised Colour (EN)"] = self.df[
            "Summarised Colour (EN)"
        ].str.replace(r"\s+", " ")
