"""Column name constants for config Excel files."""

# Drop columns
COL_DROP = "drop"

# Replace columns
COL_REPLACE_VAR = "replace_var"
COL_REPLACE_MAPPING = "replace_mapping"

# Rename columns
COL_RENAME_OLD = "rename_old"
COL_RENAME_NEW = "rename_new"

# All expected columns
EXPECTED_COLUMNS = {
    COL_DROP,
    COL_REPLACE_VAR,
    COL_REPLACE_MAPPING,
    COL_RENAME_OLD,
    COL_RENAME_NEW,
}
