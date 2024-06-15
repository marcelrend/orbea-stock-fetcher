from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class SkipModel:
    model: str
    year: str


@dataclass
class EposConfig:
    epos_file: Path = Path("epos_small_v2_23_24.xlsx")
    families: list[str] = field(
        default_factory=lambda: [
            "Alma",
            "Avant",
            "Kemen",
            "Kemen Suv" "Laufey",
            "Occam",
            "Occam LT",
            "Occam SL",
            "Oiz",
            "Orca",
            "Orca Aero",
            "Ordu",
            "Rallon",
            "Rise",
            "Terra",
            "Urrun",
            "Wild",
        ]
    )
    skip_models: list[SkipModel] = field(
        default_factory=lambda: [
            SkipModel(model="ORDU M30iLTD", year="2023"),
            SkipModel(model="WILD M-TEAM", year="2024"),
            SkipModel(model="WILD M-LTD", year="2024"),
            SkipModel(model="TERRA M20iTEAM", year="2024"),
        ]
    )
    model_filters: list[str] = field(
        default_factory=lambda: [
            "20mph",
            "28mph",
            " OMR",
            " OMX",
            "SPIRIT",
            "2POS FK",
        ]
    )  # Remove >mph and OMRs (frame)
    filter_single_model: str = None


@dataclass
class AppConfig:
    shopify_api_version: str = "2022-10"
