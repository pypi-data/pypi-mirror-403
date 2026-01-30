"""Load cleaning configuration from Excel files."""

from pathlib import Path

import polars as pl

from .class_config import Config
from .constants import (
    COL_DROP,
    COL_RENAME_NEW,
    COL_RENAME_OLD,
    COL_REPLACE_MAPPING,
    COL_REPLACE_VAR,
)


def _parse_replace_mapping(s: str) -> dict[int, int]:
    """
    Parse replace mapping string into dict.

    Args:
        s: Mapping string in format "1:2,3:4,5:6"

    Returns:
        Dict mapping old values to new values.

    Example:
        >>> _parse_replace_mapping("1:2,3:4")
        {1: 2, 3: 4}
    """
    return {
        int(k): int(v)
        for pair in s.split(",")
        for k, v in [pair.strip().split(":")]
    }


def _validate_excel_structure(df: pl.DataFrame, path: str | Path) -> None:
    """
    Validate Excel has at least one recognized config column.

    Args:
        df: DataFrame read from Excel.
        path: File path for error messages.

    Raises:
        ValueError: If no recognized columns found.
    """
    recognized = {COL_DROP, COL_REPLACE_VAR, COL_REPLACE_MAPPING, COL_RENAME_OLD, COL_RENAME_NEW}
    found = set(df.columns) & recognized

    if not found:
        raise ValueError(
            f"No recognized config columns in '{path}'. "
            f"Expected at least one of: {sorted(recognized)}"
        )

    # Check paired columns
    has_replace_var = COL_REPLACE_VAR in df.columns
    has_replace_map = COL_REPLACE_MAPPING in df.columns
    if has_replace_var != has_replace_map:
        missing = COL_REPLACE_MAPPING if has_replace_var else COL_REPLACE_VAR
        raise ValueError(f"Missing paired column '{missing}' in '{path}'")

    has_rename_old = COL_RENAME_OLD in df.columns
    has_rename_new = COL_RENAME_NEW in df.columns
    if has_rename_old != has_rename_new:
        missing = COL_RENAME_NEW if has_rename_old else COL_RENAME_OLD
        raise ValueError(f"Missing paired column '{missing}' in '{path}'")


def load_config(path: str | Path, sheet: str | None = None) -> Config:
    """
    Load cleaning configuration from Excel file.

    Expected Excel columns (all optional, but at least one required):
        - drop: Column names to drop
        - replace_var, replace_mapping: Value replacements (format: "1:2,3:4")
        - rename_old, rename_new: Column renames

    Args:
        path: Path to Excel file.
        sheet: Sheet name (default: first sheet).

    Returns:
        Config object with drop, replace, rename attributes.

    Raises:
        ValueError: If no recognized columns found or conflicting mappings.
        FileNotFoundError: If Excel file doesn't exist.

    Example:
        >>> cfg = load_config("config.xlsx")
        >>> cfg.drop
        ['unwanted_col']
        >>> cfg = load_config("config.xlsx", sheet="file2")
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: '{path}'")

    df = pl.read_excel(path, sheet_name=sheet)
    _validate_excel_structure(df, path)

    # Parse drop
    drop: list[str] = []
    if COL_DROP in df.columns:
        drop = df.get_column(COL_DROP).drop_nulls().to_list()

    # Parse replace
    replace: dict[str, dict[int, int]] = {}
    if COL_REPLACE_VAR in df.columns and COL_REPLACE_MAPPING in df.columns:
        replace_df = df.select([COL_REPLACE_VAR, COL_REPLACE_MAPPING]).drop_nulls()

        for var, mapping_str in zip(
            replace_df.get_column(COL_REPLACE_VAR).to_list(),
            replace_df.get_column(COL_REPLACE_MAPPING).to_list(),
        ):
            parsed = _parse_replace_mapping(mapping_str)

            if var not in replace:
                replace[var] = parsed
            else:
                for k, v in parsed.items():
                    if k in replace[var] and replace[var][k] != v:
                        raise ValueError(
                            f"Conflict in '{var}': key {k} mapped to both "
                            f"{replace[var][k]} and {v}"
                        )
                replace[var].update(parsed)

    # Parse rename
    rename: dict[str, str] = {}
    if COL_RENAME_OLD in df.columns and COL_RENAME_NEW in df.columns:
        rename_df = df.select([COL_RENAME_OLD, COL_RENAME_NEW]).drop_nulls()
        rename = dict(
            zip(
                rename_df.get_column(COL_RENAME_OLD).to_list(),
                rename_df.get_column(COL_RENAME_NEW).to_list(),
            )
        )

    return Config(drop=drop, replace=replace, rename=rename)
