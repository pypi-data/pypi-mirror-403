import narwhals as nw
from narwhals.typing import FrameT
import polars as pl
import pandas as pd
from typing import Any
from ._detect_variable_type import detect_variable_type, create_mr_set_lookup
# version_16 (added variable_format and readstat_type columns)


def precompute_value_maps(
    df: FrameT,
) -> tuple[
    dict[str, dict[Any, int]],
    dict[str, int],
    dict[str, int],
    dict[str, set[Any]],
]:
    """
    Precompute value counts, null counts, non-null counts, and unique values
    for each column in the dataframe.

    Hybrid design:
    - If the underlying native frame is Polars or Pandas, use an optimized
      backend-specific implementation (_precompute_value_maps_native).
    - Otherwise, fall back to a generic Narwhals-based implementation
      (_precompute_value_maps_narwhals), which should still be efficient and
      automatically benefit from fast backends like Polars.

    Parameters
    ----------
    df : FrameT
        Any Narwhals-compatible dataframe (Polars, Pandas, etc).

    Returns
    -------
    value_counts_map : dict[str, dict[Any, int]]
        For each column, a dict of {value -> count} (excluding nulls).
    null_count_map : dict[str, int]
        For each column, the count of null values.
    non_null_count_map : dict[str, int]
        For each column, the count of non-null values.
    unique_value_map : dict[str, set[Any]]
        For each column, the set of unique non-null values.
        This map is what you pass into detect_variable_type to avoid
        recomputing uniques.
    """
    # Normalize to a Narwhals frame
    df_nw = nw.from_native(df)
    native = nw.to_native(df_nw)

    # Fast path for Polars / Pandas
    if isinstance(native, pl.DataFrame) or isinstance(native, pd.DataFrame):
        return _precompute_value_maps_native(native)

    # Generic Narwhals path (for other backends)
    return _precompute_value_maps_narwhals(df_nw)


def _precompute_value_maps_native(
    df_native: pl.DataFrame | pd.DataFrame,
) -> tuple[
    dict[str, dict[Any, int]],
    dict[str, int],
    dict[str, int],
    dict[str, set[Any]],
]:
    """
    Backend-specific fast implementation for Polars and Pandas.

    For string/text columns, empty strings "" are treated as missing (like nulls).
    Whitespace-only strings are treated as valid non-missing data.
    """
    value_counts_map: dict[str, dict[Any, int]] = {}
    null_count_map: dict[str, int] = {}
    non_null_count_map: dict[str, int] = {}
    unique_value_map: dict[str, set[Any]] = {}

    if isinstance(df_native, pl.DataFrame):
        for col in df_native.columns:
            s = df_native[col]

            # Check if column is string type
            is_string_col = s.dtype == pl.Utf8 or s.dtype == pl.String

            if is_string_col:
                # For string columns: treat nulls AND empty strings as missing
                actual_null_count = int(s.null_count())

                # Count empty strings (only exact "", not whitespace)
                empty_string_count = int(
                    s.drop_nulls().eq("").sum()
                )

                # Total "missing" = nulls + empty strings
                null_count_map[col] = actual_null_count + empty_string_count

                # Value counts for non-null, non-empty values
                s_valid = s.filter(s.is_not_null() & (s != ""))

                if s_valid.len() > 0:
                    vc_df = s_valid.value_counts()
                    cols = vc_df.columns
                    value_col = cols[0]
                    count_col = cols[1] if len(cols) > 1 else None

                    values = vc_df[value_col].to_list()
                    counts = vc_df[count_col].to_list() if count_col else [1] * len(values)
                    vc_dict = dict(zip(values, counts))
                else:
                    values = []
                    counts = []
                    vc_dict = {}

                value_counts_map[col] = vc_dict
                unique_value_map[col] = set(values)
                non_null_count_map[col] = int(sum(counts))

            else:
                # Non-string columns: original logic
                null_count = int(s.null_count())
                null_count_map[col] = null_count

                vc_df = s.drop_nulls().value_counts()
                if vc_df.height > 0:
                    cols = vc_df.columns
                    value_col = cols[0]
                    count_col = cols[1] if len(cols) > 1 else None

                    values = vc_df[value_col].to_list()
                    counts = vc_df[count_col].to_list() if count_col else [1] * len(values)
                    vc_dict = dict(zip(values, counts))
                else:
                    values = []
                    counts = []
                    vc_dict = {}

                value_counts_map[col] = vc_dict
                unique_value_map[col] = set(values)
                non_null_count_map[col] = int(sum(counts))

    elif isinstance(df_native, pd.DataFrame):
        for col in df_native.columns:
            s = df_native[col]

            # Check if column is string/object type
            is_string_col = s.dtype == "object" or pd.api.types.is_string_dtype(s)

            if is_string_col:
                # For string columns: treat nulls AND empty strings as missing
                actual_null_count = int(s.isna().sum())

                # Count empty strings (only exact "", not whitespace)
                non_null_mask = s.notna()
                empty_string_count = int((s[non_null_mask] == "").sum())

                null_count_map[col] = actual_null_count + empty_string_count

                # Value counts for non-null, non-empty values
                valid_mask = non_null_mask & (s != "")
                s_valid = s[valid_mask]

                vc = s_valid.value_counts(dropna=True)
                vc_dict = vc.to_dict()
                value_counts_map[col] = vc_dict
                unique_value_map[col] = set(vc.index.tolist())
                non_null_count_map[col] = int(vc.sum())

            else:
                # Non-string columns: original logic
                null_count = int(s.isna().sum())
                null_count_map[col] = null_count

                vc = s.value_counts(dropna=True)
                vc_dict = vc.to_dict()
                value_counts_map[col] = vc_dict
                unique_value_map[col] = set(vc.index.tolist())
                non_null_count_map[col] = int(vc.sum())
    else:
        raise ValueError(f"Unsupported native dataframe type: {type(df_native)}")

    return value_counts_map, null_count_map, non_null_count_map, unique_value_map


def _precompute_value_maps_narwhals(
    df_nw: FrameT,
) -> tuple[
    dict[str, dict[Any, int]],
    dict[str, int],
    dict[str, int],
    dict[str, set[Any]],
]:
    """
    Generic Narwhals implementation.

    For string/text columns, empty strings "" are treated as missing (like nulls).
    Whitespace-only strings are treated as valid non-missing data.
    """
    value_counts_map: dict[str, dict[Any, int]] = {}
    null_count_map: dict[str, int] = {}
    non_null_count_map: dict[str, int] = {}
    unique_value_map: dict[str, set[Any]] = {}

    schema = df_nw.schema  # dict-like: {column_name: dtype}

    for col in schema.keys():
        col_expr = nw.col(col)
        col_dtype = schema[col]

        # Check if column is string type
        is_string_col = col_dtype == nw.String

        if is_string_col:
            # For string columns: treat nulls AND empty strings as missing
            
            # Count actual nulls
            actual_null_count = int(
                df_nw.select(col_expr.is_null().sum().alias("n_null")).item(0, "n_null")
            )

            # Count empty strings (only exact "", not whitespace)
            empty_string_count = int(
                df_nw.filter(~col_expr.is_null())
                .select((col_expr == nw.lit("")).sum().alias("n_empty"))
                .item(0, "n_empty")
            )

            null_count_map[col] = actual_null_count + empty_string_count

            # Filter to non-null, non-empty values
            valid_df = df_nw.filter(~col_expr.is_null() & (col_expr != nw.lit("")))

            # Get unique values and counts
            if valid_df.select(nw.len()).item(0, 0) > 0:
                # Group by and count
                vc_df = valid_df.group_by(col).agg(nw.len().alias("count"))
                native_vc = nw.to_native(vc_df)

                if isinstance(native_vc, pl.DataFrame):
                    values = native_vc[col].to_list()
                    counts = native_vc["count"].to_list()
                else:
                    values = native_vc[col].tolist()
                    counts = native_vc["count"].tolist()

                vc_dict = dict(zip(values, counts))
            else:
                values = []
                counts = []
                vc_dict = {}

            value_counts_map[col] = vc_dict
            unique_value_map[col] = set(values)
            non_null_count_map[col] = int(sum(counts))

        else:
            # Non-string columns: original logic
            null_count = int(
                df_nw.select(col_expr.is_null().sum().alias("n_null")).item(0, "n_null")
            )
            null_count_map[col] = null_count

            valid_df = df_nw.filter(~col_expr.is_null())

            if valid_df.select(nw.len()).item(0, 0) > 0:
                vc_df = valid_df.group_by(col).agg(nw.len().alias("count"))
                native_vc = nw.to_native(vc_df)

                if isinstance(native_vc, pl.DataFrame):
                    values = native_vc[col].to_list()
                    counts = native_vc["count"].to_list()
                else:
                    values = native_vc[col].tolist()
                    counts = native_vc["count"].tolist()

                vc_dict = dict(zip(values, counts))
            else:
                values = []
                counts = []
                vc_dict = {}

            value_counts_map[col] = vc_dict
            unique_value_map[col] = set(values)
            non_null_count_map[col] = int(sum(counts))

    return value_counts_map, null_count_map, non_null_count_map, unique_value_map


def merge_meta_and_actual_values(
    meta_values: dict[Any, str],
    actual_value_counts: dict[Any, int],
) -> list[tuple[Any, str | None, int, bool]]:
    """
    Merge metadata value labels with actual value counts from data.

    Returns a sorted list of (code, label, count, is_missing_label) tuples.
    - code: the value code
    - label: the label from meta (or None if unlabeled)
    - count: the count from data (0 if not in data)
    - is_missing_label: True if code exists in data but not in meta
    
    Handles type mismatches between meta keys (often int) and actual data keys
    (may be string if column was cast to Categorical/String). Only applies
    normalization when a clear mismatch pattern is detected.
    """
    meta_keys = set(meta_values.keys())
    actual_keys = set(actual_value_counts.keys())
    
    # Detect if normalization is needed:
    # Pattern: meta has numeric keys, actual has string versions of those numbers
    # Only normalize if this specific mismatch pattern is detected
    should_normalize = False
    normalization_map: dict[Any, Any] = {}  # actual_key -> normalized_key
    
    if meta_keys and actual_keys:
        # Check if meta keys are numeric and actual keys are strings
        meta_all_numeric = all(isinstance(k, (int, float)) for k in meta_keys)
        actual_all_strings = all(isinstance(k, str) for k in actual_keys)
        
        if meta_all_numeric and actual_all_strings:
            # Try to build a normalization map
            # Only proceed if ALL string keys can be converted to match meta keys
            temp_map = {}
            can_normalize = True
            
            for key in actual_keys:
                try:
                    float_val = float(key)
                    if float_val.is_integer():
                        normalized = int(float_val)
                    else:
                        normalized = float_val
                    temp_map[key] = normalized
                except (ValueError, TypeError):
                    # Found a string that can't be converted - don't normalize
                    can_normalize = False
                    break
            
            if can_normalize:
                # Verify that normalization actually helps (creates overlap with meta keys)
                normalized_actual_keys = set(temp_map.values())
                overlap = normalized_actual_keys & meta_keys
                
                # Only use normalization if it creates meaningful overlap
                if overlap:
                    should_normalize = True
                    normalization_map = temp_map
    
    # Apply normalization if needed
    if should_normalize:
        normalized_actual: dict[Any, int] = {}
        for key, count in actual_value_counts.items():
            normalized_key = normalization_map.get(key, key)
            if normalized_key in normalized_actual:
                normalized_actual[normalized_key] += count
            else:
                normalized_actual[normalized_key] = count
    else:
        normalized_actual = actual_value_counts
    
    all_codes: set[Any] = set(meta_values.keys()) | set(normalized_actual.keys())
    result: list[tuple[Any, str | None, int, bool]] = []

    # Sort codes robustly (mixed types handled via (type_name, str(value)))
    try:
        sorted_codes = sorted(all_codes)
    except TypeError:
        sorted_codes = sorted(all_codes, key=lambda x: (type(x).__name__, str(x)))

    for code in sorted_codes:
        if code in meta_values or code in normalized_actual:
            label: str | None = meta_values.get(code, None)
            count: int = normalized_actual.get(code, 0)
            is_missing_label: bool = code not in meta_values
            result.append((code, label, count, is_missing_label))

    return result


def map_engine(
    df: pl.DataFrame | pd.DataFrame,
    meta=None,
    output_format: str | None = None
) -> pl.DataFrame | pd.DataFrame:
    """
    Create a data validation core map from dataframe and optional metadata.

    This function serves as the core map engine that analyzes both metadata and
    actual data to produce a comprehensive mapping for data validation and analysis.

    It identifies:
    - Missing data (nulls)
    - Unlabeled values (values in data but not in meta)
    - Value distributions (counts for each value)

    Parameters
    ----------
    df : pl.DataFrame | pd.DataFrame
        The data dataframe (Polars or Pandas). REQUIRED.
    meta : metadata object, optional
        Metadata from pyreadstat or ultrasav Metadata object.
        When provided, enables:
        - Variable labels (column_names_to_labels)
        - Value labels (variable_value_labels)
        - Multi-response set detection (mr_sets)
        - More precise type detection (single-select vs multi-select)
        When None, map is created purely from DataFrame with detected types.
    output_format : str | None
        Output format - either "polars" or "pandas".
        If None, will match the input dataframe type.

    Returns
    -------
    pl.DataFrame | pd.DataFrame
        A dataframe with columns:
        - variable: variable name
        - variable_label: variable label text from meta (empty string if no meta)
        - variable_type: variable type (single-select, multi-select, categorical, numeric, text, date)
        - variable_measure: SPSS measurement level (scale, nominal, ordinal, or "unknown")
        - variable_format: SPSS format string (e.g., "F8.2", "A50", "DATETIME20", or "unknown")
        - readstat_type: low-level storage type (e.g., "double", "string", or "unknown")
        - value_code: value code (None for missing-data row, codes for categories)
        - value_label: value label ("NULL" for missing-data row, labels or None for unlabeled)
        - value_n: count of occurrences
    
    Examples
    --------
    >>> import polars as pl
    >>> import ultrasav as ul
    >>> 
    >>> # With metadata (full power)
    >>> df, meta = ul.read_sav("survey.sav")
    >>> core_map = ul.map_engine(df, meta)
    >>> 
    >>> # Without metadata (df-only mode)
    >>> df = pl.read_csv("survey.csv")
    >>> core_map = ul.map_engine(df)  # Still works!
    >>> 
    >>> # Force pandas output
    >>> core_map_pd = ul.map_engine(df, meta, output_format="pandas")
    """

    # Determine output format
    if output_format is None:
        if isinstance(df, pl.DataFrame):
            output_format = "polars"
        elif isinstance(df, pd.DataFrame):
            output_format = "pandas"
        else:
            raise ValueError(f"Unsupported dataframe type: {type(df)}")

    if output_format not in {"polars", "pandas"}:
        raise ValueError(f"output_format must be 'polars' or 'pandas', got '{output_format}'")

    # Handle optional meta - extract what we can or use empty defaults
    if meta is not None:
        mr_set_variables: set[str] = create_mr_set_lookup(meta)
        col_names_to_labels: dict[str, str] = getattr(meta, "column_names_to_labels", {}) or {}
        variable_value_labels: dict[str, dict[Any, str]] = (
            getattr(meta, "variable_value_labels", {}) or {}
        )
        variable_measure: dict[str, str] = (
            getattr(meta, "variable_measure", {}) or {}
        )
        readstat_types: dict[str, str] = (
            getattr(meta, "readstat_variable_types", {}) or {}
        )
        original_types: dict[str, str] = (
            getattr(meta, "original_variable_types", {}) or {}
        )
    else:
        mr_set_variables = set()
        col_names_to_labels = {}
        variable_value_labels = {}
        variable_measure = {}
        readstat_types = {}
        original_types = {}

    # Precompute value counts, null counts, non-null counts, and unique sets
    (
        value_counts_map,
        null_count_map,
        non_null_count_map,
        unique_value_map,
    ) = precompute_value_maps(df)

    # Initialize lists to store final map rows
    variables: list[str] = []
    variable_labels: list[str] = []
    variable_types: list[str] = []
    value_codes: list[Any] = []
    value_labels: list[Any] = []
    value_ns: list[int] = []

    # Iterate through variables in dataframe column order
    df_nw = nw.from_native(df)
    for var_name in df_nw.columns:
        # Variable label (empty string if no meta)
        variable_label: str = col_names_to_labels.get(var_name, "")

        # Detect variable type using new df-centric signature
        var_type: str = detect_variable_type(
            df,                                # df is position 1 (required)
            var_name,                          # var_name is position 2
            meta,                              # meta is position 3 (optional)
            mr_set_variables=mr_set_variables,
            unique_value_map=unique_value_map,
        )

        # Pull precomputed counts
        value_count_dict: dict[Any, int] = value_counts_map.get(var_name, {})
        null_count: int = null_count_map.get(var_name, 0)
        non_null_count: int = non_null_count_map.get(var_name, 0)

        # Categorical types get value enumeration (single-select, multi-select, categorical)
        is_categorical: bool = var_type in ["single-select", "multi-select", "categorical"]

        # STEP 1: Add missing data row if nulls exist
        if null_count > 0:
            variables.append(var_name)
            variable_labels.append(variable_label)
            variable_types.append(var_type)
            value_codes.append(None)
            value_labels.append("NULL")
            value_ns.append(null_count)

        # STEP 2: Categorical vs non-categorical handling
        if is_categorical:
            # Meta value labels for this variable (empty dict if no meta)
            meta_values: dict[Any, str] = variable_value_labels.get(var_name, {})

            # Merge meta and actual values
            merged_values = merge_meta_and_actual_values(meta_values, value_count_dict)

            for code, label, count, _is_missing_label in merged_values:
                variables.append(var_name)
                variable_labels.append(variable_label)
                variable_types.append(var_type)
                value_codes.append(code)
                value_labels.append(label)
                value_ns.append(count)
        else:
            # Non-categorical (numeric, text, date)
            # Always add a row to show variable info, even with no data
            variables.append(var_name)
            variable_labels.append(variable_label)
            variable_types.append(var_type)
            value_codes.append(None)
            value_labels.append(None)
            value_ns.append(non_null_count)  # Will be 0 if no data

    # Build final core map dataframe
    if output_format == "polars":
        # Decide dtype for value_code column based on non-None codes
        non_none_codes = [v for v in value_codes if v is not None]

        if non_none_codes:
            try:
                numeric_values = [float(v) for v in non_none_codes]
                if all(v.is_integer() for v in numeric_values):
                    value_code_dtype = pl.Int64
                    value_codes_typed = [
                        int(float(v)) if v is not None else None for v in value_codes
                    ]
                else:
                    value_code_dtype = pl.Float64
                    value_codes_typed = [
                        float(v) if v is not None else None for v in value_codes
                    ]
            except (ValueError, TypeError):
                value_code_dtype = pl.Utf8
                value_codes_typed = [
                    str(v) if v is not None else None for v in value_codes
                ]
        else:
            value_code_dtype = pl.Float64
            value_codes_typed = value_codes

        core_map = pl.DataFrame(
            {
                "variable": variables,
                "variable_label": variable_labels,
                "variable_type": variable_types,
                "variable_measure": [variable_measure.get(var) for var in variables],
                "variable_format": [original_types.get(var) for var in variables],
                "readstat_type": [readstat_types.get(var) for var in variables],
                "value_code": pl.Series(value_codes_typed, dtype=value_code_dtype),
                "value_label": value_labels,
                "value_n": value_ns,
            }
        )
        
        # Fill nulls for string columns
        core_map = core_map.with_columns(
            pl.col("variable_measure").fill_null("unknown"),
            pl.col("variable_format").fill_null("unknown"),
            pl.col("readstat_type").fill_null("unknown"),
        )
        
    else:  # "pandas"
        core_map = pd.DataFrame(
            {
                "variable": variables,
                "variable_label": variable_labels,
                "variable_type": variable_types,
                "variable_measure": [variable_measure.get(var) for var in variables],
                "variable_format": [original_types.get(var) for var in variables],
                "readstat_type": [readstat_types.get(var) for var in variables],
                "value_code": value_codes,
                "value_label": value_labels,
                "value_n": value_ns,
            }
        )
        
        # Fill nulls for string columns
        core_map["variable_measure"] = core_map["variable_measure"].fillna("unknown")
        core_map["variable_format"] = core_map["variable_format"].fillna("unknown")
        core_map["readstat_type"] = core_map["readstat_type"].fillna("unknown")

    return core_map


# Example usage:
if __name__ == "__main__":
    import pyreadstat

    # Example 1: With metadata (full power)
    df_pd, meta = pyreadstat.read_sav("your_file.sav", user_missing=True)
    df_pl = pl.from_pandas(df_pd)
    core_map = map_engine(df_pl, meta)
    print("With metadata:")
    print(core_map.head())

    # Example 2: Without metadata (df-only mode)
    df_csv = pl.read_csv("your_file.csv")
    core_map_no_meta = map_engine(df_csv)  # meta=None by default
    print("\nWithout metadata:")
    print(core_map_no_meta.head())

    # Save to files
    core_map.write_excel("data_core_map.xlsx")
