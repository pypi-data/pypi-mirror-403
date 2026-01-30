"""
datacfg - Excel-based data cleaning configuration.

Load cleaning configs from Excel and apply to DataFrames.

Usage:
    from ultrasav.datacfg import load_config, clean_data

    cfg = load_config("config.xlsx")
    clean_df = df.pipe(clean_data, cfg)

    # Access config attributes
    cfg.drop      # list of columns to drop
    cfg.replace   # dict of value replacements
    cfg.rename    # dict of column renames
"""

from .class_config import Config
from .constants import (
    COL_DROP,
    COL_RENAME_NEW,
    COL_RENAME_OLD,
    COL_REPLACE_MAPPING,
    COL_REPLACE_VAR,
)
from .def_clean_data import clean_data
from .def_load_config import load_config

__all__ = [
    # Main API
    "load_config",
    "clean_data",
    "Config",
    # Constants (for customization)
    "COL_DROP",
    "COL_REPLACE_VAR",
    "COL_REPLACE_MAPPING",
    "COL_RENAME_OLD",
    "COL_RENAME_NEW",
]
