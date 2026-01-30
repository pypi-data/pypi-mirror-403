"""Apply cleaning configuration to DataFrames."""

import polars as pl

from .class_config import Config


def clean_data(df: pl.DataFrame, cfg: Config) -> pl.DataFrame:
    """
    Apply cleaning configuration to DataFrame.

    Operations are applied in order: drop → replace → rename.

    Args:
        df: Input DataFrame.
        cfg: Config object from load_config().

    Returns:
        Cleaned DataFrame with operations applied.

    Example:
        >>> cfg = load_config("config.xlsx")
        >>> clean_df = clean_data(df, cfg)
        >>> # Or with pipe
        >>> clean_df = df.pipe(clean_data, cfg)
    """
    return (
        df
        .drop(cfg.drop)
        .with_columns(
            pl.col(col).replace(mapping)
            for col, mapping in cfg.replace.items()
        )
        .rename(cfg.rename)
    )
