"""
add_cases.py (v3)
Top-level function for merging SAV files or dataframes with metadata.
Following ultrasav's two-track architecture with v14 immutable Metadata API.

v3 Changes:
- meta parameter now accepts single metadata OR list of metadata
"""

import logging
from pathlib import Path
from typing import Any
from narwhals.typing import IntoFrame

from ._merge_data import merge_data
from ._merge_meta import merge_meta
from ._read_files import read_sav, read_csv, read_excel
from ._metadata import Metadata
    

logger = logging.getLogger(__name__)


def add_cases(
    inputs: list[str | Path | Any],
    meta: list[Any | None] | Any | None = None,
    output_format: str = "polars",
    source_col: str = "mrgsrc",
    meta_strategy: str = "first"
) -> tuple[Any, Metadata | None]:
    """
    Merge multiple SAV/CSV/Excel files or dataframes with their metadata.
    
    This is the main entry point for merging that combines both data and metadata
    merging following ultrasav's two-track architecture. Data and metadata are
    merged independently and returned as a tuple.
    
    Compatible with ultrasav v14's immutable Metadata API.
    
    Parameters
    ----------
    inputs : list[str | Path | DataFrame | tuple[DataFrame, Metadata]]
        List of inputs to merge. Each element can be:
        - File path (str or Path) to:
            * SAV/ZSAV files (metadata extracted automatically)
            * CSV files (no metadata)
            * Excel files (.xlsx, .xls, .xlsm, .xlsb, .ods) (no metadata)
        - A dataframe (pandas, polars, or any narwhals-supported format) without metadata
        - A combination of file paths (str/Path) and dataframes (pandas/polars/narwhals)
        - A tuple of (dataframe, metadata) for explicit data-metadata pairs
    meta : Metadata | list[Metadata | None] | None, optional
        Optional metadata to use for merging. Accepts:
        - Single metadata object (pyreadstat or ul.Metadata)
        - List of metadata objects (for merging multiple)
        - None (default): metadata is automatically extracted from SAV files
        When provided, uses ONLY these metadata objects, ignoring any metadata
        from SAV files. The list does NOT need to match input length.
    output_format : str, default "polars"
        Output dataframe format: "pandas", "polars", or "narwhals"
    source_col : str, default "mrgsrc"
        Name of the provenance column to add to track data sources.
        This column will contain:
        - For file paths: the base filename (e.g., "survey_2024.sav", "data.csv", "report.xlsx")
        - For dataframes: "source_1", "source_2", etc.
    meta_strategy : str, default "first"
        Strategy for merging metadata:
        - "first": Use first non-None meta as base, add new columns from others
        - "last": Use last non-None meta as base, add new columns from others
        
    Returns
    -------
    tuple[DataFrame, Metadata | None]
        - Merged dataframe in the specified format with provenance column
        - Merged metadata (Metadata object) or None if no metadata available
        
    Notes
    -----
    Two-Track Architecture
        Data and metadata are merged independently. This follows ultrasav's core
        principle that data and metadata are separate concerns that only converge
        at write time.
    
    Metadata Handling
        - If meta is None: uses metadata from SAV files (if any)
        - If meta is provided: uses ONLY those metadata objects, ignoring SAV metadata
        - Metadata merge follows column-level preservation (base wins for existing columns)
        - Uses v14's immutable Metadata API (all updates return new objects)
    
    Source Column
        - The source column appears as the last column in the merged dataframe
        - Default name "mrgsrc" is self-explanatory (no additional metadata added)
    
    File Format Support
    -------------------
    - SAV/ZSAV: Full support with automatic metadata extraction
    - CSV: Data only, no metadata
    - Excel: Data only (reads first sheet), no metadata
        * Supported extensions: .xlsx, .xls, .xlsm, .xlsb, .ods
    
    Examples
    --------
    >>> # Merge SAV files with automatic metadata extraction
    >>> data, meta = add_cases(["survey1.sav", "survey2.sav", "survey3.sav"])
    
    >>> # Mix different file types (SAV with metadata, CSV/Excel without)
    >>> data, meta = add_cases(["survey.sav", "additional_data.csv", "report.xlsx"])
    
    >>> # Single metadata - no list wrapper needed (v3)
    >>> data, meta = add_cases(files, supermeta)
    
    >>> # Multiple metadata - use list
    >>> data, meta = add_cases(files, [meta1, meta2])
    
    >>> # Mix different input types
    >>> df1 = pd.DataFrame({'Q1': [1, 2]})
    >>> data, meta = add_cases([df1, "survey.sav", "data.csv", (df2, meta2)])
    
    >>> # Write merged result
    >>> import ultrasav as ul
    >>> ul.write_sav(data, meta, "merged_output.sav")
    """
    
    if not inputs:
        raise ValueError("inputs list cannot be empty")
    
    # =========================================================================
    # Phase 0: Normalize meta parameter (accept single or list)
    # =========================================================================
    
    if meta is not None and not isinstance(meta, list):
        meta = [meta]
    
    # =========================================================================
    # Phase 1: Collect data sources and metadata objects
    # =========================================================================
    
    dfs = []
    metas_to_merge = []
    
    # If meta parameter is provided, use ONLY those metadata objects
    if meta is not None:
        # User provided specific metadata - always wrap in Metadata() to create a copy
        # This ensures immutability even when a single Metadata object is provided
        metas_to_merge = [Metadata(m) if m is not None else m for m in meta]
        logger.info(f"Using {len(meta)} provided metadata objects (ignoring any SAV metadata)")
    
    # Process inputs for data extraction
    for i, item in enumerate(inputs):
        if isinstance(item, tuple) and len(item) == 2:
            # It's a (dataframe, metadata) tuple
            df, tuple_meta = item
            dfs.append(df)
            
            # Only use tuple metadata if meta parameter wasn't provided
            if meta is None and tuple_meta is not None:
                # Always wrap in Metadata() to create a copy (ensures immutability)
                metas_to_merge.append(Metadata(tuple_meta))
                logger.debug(f"Using tuple metadata for input {i}")
            
        elif isinstance(item, (str, Path)):
            # It's a file path
            file_path = Path(item)
            
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            ext = file_path.suffix.lower()
            
            # Always pass file path to merge_data to preserve filename in source_col
            dfs.append(str(file_path))
            
            if ext in ['.sav', '.zsav']:
                # SAV files - extract metadata separately if needed
                # Only use SAV metadata if meta parameter wasn't provided
                if meta is None:
                    _, meta_raw = read_sav(file_path, output_format="polars")
                    if meta_raw is not None:
                        metas_to_merge.append(Metadata(meta_raw))
                        logger.debug(f"Extracted metadata from SAV file: {file_path.name}")
            elif ext == '.csv':
                # CSV files - no metadata available
                logger.debug(f"Added CSV file: {file_path.name} (no metadata)")
            elif ext in ['.xlsx', '.xls', '.xlsm', '.xlsb', '.ods']:
                # Excel files - no metadata available
                logger.debug(f"Added Excel file: {file_path.name} (no metadata)")
            else:
                # Other file types - log warning but try to process
                logger.warning(f"Unknown file type: {ext} - will attempt to process: {file_path.name}")
                
        else:
            # It's a dataframe without metadata
            dfs.append(item)
            logger.debug(f"Added dataframe {i} (no metadata)")
    
    # =========================================================================
    # Phase 2: Log input summary
    # =========================================================================
    
    logger.info(f"Processing {len(inputs)} inputs for data merge")
    
    if meta is None:
        logger.info(f"Collected {len(metas_to_merge)} metadata objects from SAV files/tuples")
    else:
        logger.info(f"Using {len(metas_to_merge)} user-provided metadata objects")
    
    # Count file types for logging
    file_type_counts = {}
    for item in inputs:
        if isinstance(item, (str, Path)):
            ext = Path(item).suffix.lower()
            file_type_counts[ext] = file_type_counts.get(ext, 0) + 1
    
    if file_type_counts:
        types_summary = ", ".join([f"{count} {ext}" for ext, count in file_type_counts.items()])
        logger.info(f"File types: {types_summary}")
    
    # =========================================================================
    # Phase 3: Merge data (Track 1)
    # =========================================================================
    
    logger.info("Merging data...")
    merged_data = merge_data(dfs, source_col=source_col, output_format=output_format)
    
    # =========================================================================
    # Phase 4: Merge metadata (Track 2)
    # =========================================================================
    
    merged_meta = None
    
    if metas_to_merge and any(m is not None for m in metas_to_merge):
        logger.info(f"Merging metadata with strategy='{meta_strategy}'...")
        merged_meta = merge_meta(metas_to_merge, strategy=meta_strategy)
    else:
        logger.info("No metadata to merge (common when merging CSV/Excel files)")
    
    # =========================================================================
    # Phase 5: Final summary and return
    # =========================================================================
    
    data_shape = merged_data.shape if hasattr(merged_data, 'shape') else "unknown"
    meta_cols = len(merged_meta.column_labels) if merged_meta and merged_meta.column_labels else 0
    meta_rows = merged_meta.number_rows if merged_meta else None
    
    logger.info(
        f"Merge complete: data shape {data_shape}, "
        f"metadata covers {meta_cols} columns"
        + (f", {meta_rows} rows tracked" if meta_rows else "")
    )
    
    return merged_data, merged_meta
