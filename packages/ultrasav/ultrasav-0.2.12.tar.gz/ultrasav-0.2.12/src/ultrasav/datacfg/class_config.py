"""Config dataclass for data cleaning operations."""

from dataclasses import dataclass, field


@dataclass
class Config:
    """
    Data cleaning configuration.

    Attributes:
        drop: List of column names to drop.
        replace: Nested dict mapping column names to value replacements.
            Format: {col_name: {old_value: new_value, ...}, ...}
        rename: Dict mapping old column names to new names.
            Format: {old_name: new_name, ...}

    Example:
        >>> cfg = Config(
        ...     drop=["temp_col", "debug_col"],
        ...     replace={"status": {99: 1, 98: 2}},
        ...     rename={"old_name": "new_name"}
        ... )
        >>> cfg.drop
        ['temp_col', 'debug_col']
    """

    drop: list[str] = field(default_factory=list)
    replace: dict[str, dict[int, int]] = field(default_factory=dict)
    rename: dict[str, str] = field(default_factory=dict)
