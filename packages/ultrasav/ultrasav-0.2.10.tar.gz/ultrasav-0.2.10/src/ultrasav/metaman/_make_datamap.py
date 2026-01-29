import narwhals as nw
from narwhals.typing import FrameT
import polars as pl
import pandas as pd
from ._map_engine import map_engine
# version_3 (added include_all parameter for debug columns)


def make_datamap(
    df: pl.DataFrame | pd.DataFrame,
    meta=None,
    output_format: str | None = None,
    include_all: bool = False,
) -> pl.DataFrame | pd.DataFrame:
    """
    Create a validation data map from dataframe and optional metadata.
    
    This wrapper function internally calls map_engine() to generate the core_map,
    then adds computed columns for missing value labels, missing data flags, 
    and base_n calculations.
    
    Parameters:
    -----------
    df : pl.DataFrame | pd.DataFrame
        The data dataframe (Polars or Pandas). REQUIRED.
    meta : metadata object, optional
        Metadata from pyreadstat or ultrasav Metadata object.
        When provided, enables variable labels, value labels, and 
        refined type detection (single-select, multi-select).
        When None, map is created purely from DataFrame.
    output_format : str | None
        Output format - either "polars" or "pandas"
        If None, will match the input dataframe type
    include_all : bool, default False
        If True, includes additional SPSS debug columns:
        - variable_measure: SPSS measurement level (scale, nominal, ordinal)
        - variable_format: SPSS format string (e.g., "F8.2", "A50")
        - readstat_type: low-level storage type (e.g., "double", "string")
        If False (default), these columns are excluded for cleaner output.
    
    Returns:
    --------
    pl.DataFrame | pd.DataFrame
        A data map dataframe with columns:
        - variable: variable name
        - variable_label: variable label text (empty string if no meta)
        - variable_type: variable type (categorical, numeric, text, date)
        - value_code: value code (None for missing data row, actual codes for values)
        - value_label: value label ("NULL" for missing data row, labels or None for unlabeled)
        - value_n: count of occurrences
        - base_n: total non-NULL count for the variable
        - base_pct: percentage of value_n over base_n (null if base_n is 0)
        - total_n: total count of value_n per variable
        - total_pct: percentage of value_n over total_n (null if total_n is 0)
        - missing_value_label: "Yes" if value exists in data but not in meta, else "No"
        - missing_data: "Yes" for NULL data rows only, else "No"
        
        When include_all=True, also includes:
        - variable_measure: SPSS measurement level (scale, nominal, ordinal, or "unknown")
        - variable_format: SPSS format string (e.g., "F8.2", "A50", or "unknown")
        - readstat_type: low-level storage type (e.g., "double", "string", or "unknown")
    
    Examples:
    ---------
    >>> import ultrasav as ul
    >>> 
    >>> # With metadata (full power)
    >>> df, meta = ul.read_sav('data.sav')
    >>> data_map = ul.make_datamap(df, meta)
    >>> 
    >>> # Without metadata (df-only mode)
    >>> df = pl.read_csv('data.csv')
    >>> data_map = ul.make_datamap(df)  # Still works!
    >>> 
    >>> # Include all SPSS debug columns
    >>> data_map = ul.make_datamap(df, meta, include_all=True)
    >>> 
    >>> # Export to Excel
    >>> data_map.write_excel('datamap.xlsx')  # Polars
    >>> # or
    >>> data_map_pd = ul.make_datamap(df, meta, output_format="pandas")
    >>> data_map_pd.to_excel('datamap.xlsx', index=False)  # Pandas
    """
    
    # First, get the core_map from map_engine
    core_map = map_engine(df, meta, output_format)
    
    # Then apply the data map transformations
    data_map = nw.from_native(core_map).with_columns(
        # missing_label: "Yes" if value exists in data but not in meta for single-select or multi-select variables
        nw.when(
            (~nw.col("value_code").is_null()) &
            (nw.col("value_label").is_null())
        ).then(nw.lit("Yes"))
        .otherwise(nw.lit("No"))
        .alias("missing_value_label"),
        
        # missing_data: "Yes" for NULL data rows only
        nw.when(nw.col("value_label") == "NULL")
        .then(nw.lit("Yes"))
        .otherwise(nw.lit("No"))
        .alias("missing_data"),
        
        # Calculate base_n: sum of non-NULL value_n per variable
        nw
        .when(nw.col("value_label") == "NULL")
        .then(nw.col("value_n"))
        .otherwise(
             nw
             .when((nw.col("value_label") != "NULL") | (nw.col("value_label").is_null()))
             .then(nw.col("value_n"))  
             .sum()  
             .over("variable")  
        )
        .alias("base_n")
        
    ).with_columns(
        # Standardize variable_type: convert single-select and multi-select to categorical
        nw.when(nw.col("variable_type").is_in(["single-select", "multi-select"]))
        .then(nw.lit("categorical"))
        .otherwise(nw.col("variable_type"))
        .alias("variable_type")
    ).with_columns(
        # Calculate base_pct (might create value 'NaN' if base_n is 0)
        (nw.col("value_n") / nw.col("base_n")).alias("base_pct")
    ).with_columns(
        # Replace NaN with null
        nw.when(nw.col("base_pct").is_nan())
        .then(None)  # Convert NaN to null
        .otherwise(nw.col("base_pct"))
        .alias("base_pct")
    ).with_columns(
        # Calculate total_n per variable for total_pct
        nw.col('value_n').sum().over("variable").alias('total_n')
    ).with_columns(
        # Calculate total_pct
        (nw.col('value_n')/nw.col('total_n')).alias('total_pct')
    ).with_columns(
        # Replace NaN with null
        nw.when(nw.col("total_pct").is_nan())
        .then(None)  # Convert NaN to null
        .otherwise(nw.col("total_pct"))
        .alias("total_pct")
    )
    
    # Build column list based on include_all parameter
    columns = [
        'variable',
        'variable_label',
        'variable_type',
    ]
    if include_all:
        columns.extend([
            'variable_measure',
            'variable_format',
            'readstat_type',
        ])
    columns.extend([
        'value_code',
        'value_label',
        'value_n',
        'base_n',
        'base_pct',
        'total_n',
        'total_pct',
        'missing_value_label',
        'missing_data',
    ])
    
    data_map = data_map.select(columns).to_native()
    
    return data_map
