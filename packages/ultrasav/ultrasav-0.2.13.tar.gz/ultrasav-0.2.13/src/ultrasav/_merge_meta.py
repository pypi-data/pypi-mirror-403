"""
v2
merge_meta.py
Metadata merging function for ultrasav
Following the two-track architecture where metadata is independent from data

Works with both pyreadstat metadata objects and ultrasav Metadata class.
All inputs are wrapped in Metadata() for consistent property access.
"""

import logging
from typing import Any
from copy import deepcopy

# Import Metadata class
from ._metadata import Metadata

logger = logging.getLogger(__name__)


def _merge_dict_field(base_dict: dict, other_dict: dict, field_name: str) -> tuple[dict, list]:
    """
    Merge two dictionary fields at column level - base wins for existing columns.
    
    Parameters
    ----------
    base_dict : dict
        Base dictionary (takes precedence for existing keys)
    other_dict : dict
        Other dictionary (only new keys are added)
    field_name : str
        Name of the field being merged (for logging)
        
    Returns
    -------
    tuple[dict, list]
        Merged dictionary and list of new columns added
    """
    merged = base_dict.copy() if base_dict else {}
    new_columns = []
    
    for col_name, col_value in other_dict.items():
        if col_name not in merged:
            # This is a new column - add entire column:value pair
            merged[col_name] = deepcopy(col_value)
            new_columns.append(col_name)
        # If column exists in base, keep base's value entirely
    
    if new_columns:
        logger.debug(f"  Added {len(new_columns)} new columns to {field_name}: {new_columns[:5]}{'...' if len(new_columns) > 5 else ''}")
    
    return merged, new_columns


def _merge_list_field(base_list: list, other_list: list, field_name: str) -> tuple[list, list]:
    """
    Merge two list fields - base items preserved, new items added (no duplicates).
    
    Parameters
    ----------
    base_list : list
        Base list (items preserved in order)
    other_list : list
        Other list (only new items are added)
    field_name : str
        Name of the field being merged (for logging)
        
    Returns
    -------
    tuple[list, list]
        Merged list and list of new items added
    """
    merged = list(base_list) if base_list else []
    new_items = []
    
    for item in other_list:
        if item not in merged:
            merged.append(item)
            new_items.append(item)
    
    if new_items:
        logger.debug(f"  Added {len(new_items)} new items to {field_name}: {new_items[:5]}{'...' if len(new_items) > 5 else ''}")
    
    return merged, new_items


def merge_meta(
    metas: list[Any | None],
    strategy: str = "first"
) -> Metadata:
    """
    Merge multiple metadata objects with column-level preservation.
    
    This function merges metadata from multiple sources following ultrasav's
    principle that metadata is independent from data. The merge operates at
    the column level - for each column, we take ALL metadata from one source,
    never mixing metadata values within a column.
    
    Works with both pyreadstat metadata objects and ultrasav Metadata class.
    All inputs are wrapped in Metadata() for consistent property access.
    
    Parameters
    ----------
    metas : list[Metadata | pyreadstat_meta | None]
        List of metadata objects or None values. Can include:
        - ultrasav Metadata objects
        - pyreadstat metadata objects from read_sav()
        - None for missing metadata
    strategy : str, default "first"
        Merge strategy for combining metadata:
        - "first": Use first non-None meta as base, add new columns from others
        - "last": Use last non-None meta as base, add new columns from others
        
    Returns
    -------
    Metadata
        Merged Metadata object with combined metadata from all sources
        
    Notes
    -----
    The merge strategy works at the COLUMN level, not value level:
    - If base meta has metadata for column "Q1", it keeps ALL of Q1's metadata
    - Only columns NOT in base are added from subsequent metas
    - No mixing of values within a column's metadata
    
    Writable fields merged (written to SAV):
    - column_labels
    - variable_value_labels  
    - variable_format
    - variable_measure
    - variable_display_width
    - missing_ranges
    
    Mergeable fields merged (viewable, NOT written to SAV):
    - column_names
    - original_variable_types
    - readstat_variable_types
    - value_labels
    - variable_to_label
    - missing_user_values
    - variable_alignment
    - variable_storage_width
    - mr_sets
    
    File-level metadata (notes, file_label, compress, row_compress) are taken 
    from base only and not merged.
    
    Examples
    --------
    >>> # Merge metadata from multiple SAV files
    >>> _, meta1 = read_sav("file1.sav")
    >>> _, meta2 = read_sav("file2.sav")
    >>> _, meta3 = read_sav("file3.sav")
    >>> merged_meta = merge_meta([meta1, meta2, meta3])
    
    >>> # Handle None values
    >>> merged_meta = merge_meta([None, meta1, None, meta2])
    
    >>> # Use last strategy
    >>> merged_meta = merge_meta([meta1, meta2, meta3], strategy="last")
    
    >>> # Access merged fields (including previously "read-only" fields)
    >>> merged_meta.column_names           # All columns from all files
    >>> merged_meta.original_variable_types # All format info from all files
    """
    
    # Filter out None values
    valid_metas = [m for m in metas if m is not None]
    
    if not valid_metas:
        # Return empty metadata if all are None
        logger.info("All metadata objects are None, returning empty Metadata")
        return Metadata()
    
    # Wrap ALL valid metas in Metadata class for consistent property access
    wrapped_metas = []
    for m in valid_metas:
        if isinstance(m, Metadata):
            wrapped_metas.append(m)
        else:
            wrapped_metas.append(Metadata(m))
    
    if len(wrapped_metas) == 1:
        # Only one valid metadata, return it (already wrapped)
        logger.info("Only one valid metadata found, returning as Metadata object")
        return wrapped_metas[0]
    
    # Select base metadata based on strategy
    if strategy == "first":
        base_meta = wrapped_metas[0]
        others = wrapped_metas[1:]
        logger.info(f"Using first non-None metadata as base, merging {len(others)} others")
    elif strategy == "last":
        base_meta = wrapped_metas[-1]
        others = wrapped_metas[:-1]
        logger.info(f"Using last non-None metadata as base, merging {len(others)} others")
    else:
        raise ValueError(f"Unknown merge strategy: {strategy}. Use 'first' or 'last'")
    
    # =========================================================================
    # Initialize accumulators with base values
    # =========================================================================
    
    # Writable dict fields (written to SAV)
    writable_dict_fields = [
        'column_labels',
        'variable_value_labels',
        'variable_format',
        'variable_measure',
        'variable_display_width',
        'missing_ranges',
    ]
    
    # Mergeable dict fields (viewable, NOT written to SAV)
    mergeable_dict_fields = [
        'original_variable_types',
        'readstat_variable_types',
        'value_labels',
        'variable_to_label',
        'missing_user_values',
        'variable_alignment',
        'variable_storage_width',
        'mr_sets',
    ]
    
    all_dict_fields = writable_dict_fields + mergeable_dict_fields
    
    # Initialize accumulators from base
    merged_fields = {}
    for field_name in all_dict_fields:
        field_value = getattr(base_meta, field_name, None)
        if field_value and isinstance(field_value, dict):
            merged_fields[field_name] = field_value.copy()
        else:
            merged_fields[field_name] = {}
    
    # Special handling for column_names (list, not dict)
    merged_column_names = list(base_meta.column_names) if base_meta.column_names else []
    
    # Track total rows (sum of all metadata's number_rows)
    total_rows = base_meta.number_rows or 0
    
    # =========================================================================
    # Process each subsequent metadata object
    # =========================================================================
    
    for i, other_meta in enumerate(others):
        logger.debug(f"Merging metadata {i+1} of {len(others)}")
        
        # Accumulate number_rows (sum of all files)
        if other_meta.number_rows:
            total_rows += other_meta.number_rows
        
        # Merge column_names (list)
        other_column_names = other_meta.column_names
        if other_column_names:
            merged_column_names, new_cols = _merge_list_field(
                merged_column_names, 
                other_column_names, 
                'column_names'
            )
        
        # Merge all dict fields
        for field_name in all_dict_fields:
            other_field = getattr(other_meta, field_name, None)
            
            # Skip if other field is None or not a dict
            if other_field is None or not isinstance(other_field, dict):
                continue
            
            # Get current merged field
            current_merged = merged_fields.get(field_name, {})
            
            # Merge the field (base wins for existing keys)
            merged_result, _ = _merge_dict_field(current_merged, other_field, field_name)
            merged_fields[field_name] = merged_result
    
    # =========================================================================
    # Apply all merged values using immutable .update() API
    # =========================================================================
    
    # Build update kwargs
    update_kwargs = {}
    
    # Add column_names if we have any
    if merged_column_names:
        update_kwargs['column_names'] = merged_column_names
        # number_columns = length of merged column_names
        update_kwargs['number_columns'] = len(merged_column_names)
    
    # Add number_rows (sum of all files)
    if total_rows > 0:
        update_kwargs['number_rows'] = total_rows
    
    # Add all dict fields that have values
    for field_name in all_dict_fields:
        if merged_fields.get(field_name):
            update_kwargs[field_name] = merged_fields[field_name]
    
    # Apply all updates at once using immutable API (returns new Metadata object)
    if update_kwargs:
        merged = base_meta.update(**update_kwargs)
        logger.debug(f"Applied updates for {len(update_kwargs)} fields")
    else:
        merged = base_meta
    
    # =========================================================================
    # Log summary
    # =========================================================================
    
    total_columns = set()
    for field_name in all_dict_fields:
        field_value = getattr(merged, field_name, None)
        if field_value and isinstance(field_value, dict):
            total_columns.update(field_value.keys())
    
    # Also include column_names
    if merged.column_names:
        total_columns.update(merged.column_names)
    
    logger.info(f"Merge complete: {len(wrapped_metas)} metadata objects merged, {len(total_columns)} unique columns in result")
    
    return merged


def get_meta_summary(meta: Any) -> dict:
    """
    Get a summary of metadata contents for debugging/logging.
    
    Parameters
    ----------
    meta : Metadata or pyreadstat metadata
        Metadata object to summarize
        
    Returns
    -------
    dict
        Summary statistics about the metadata
    """
    if meta is None:
        return {"status": "None"}
    
    # Wrap in Metadata for consistent access
    if not isinstance(meta, Metadata):
        meta = Metadata(meta)
    
    summary = {
        # Writable fields
        "column_labels": len(meta.column_labels),
        "variable_value_labels": len(meta.variable_value_labels),
        "variable_format": len(meta.variable_format),
        "variable_measure": len(meta.variable_measure),
        "variable_display_width": len(meta.variable_display_width),
        "missing_ranges": len(meta.missing_ranges) if meta.missing_ranges else 0,
        
        # Mergeable fields
        "column_names": len(meta.column_names),
        "number_columns": meta.number_columns,
        "number_rows": meta.number_rows,
        "original_variable_types": len(meta.original_variable_types),
        "readstat_variable_types": len(meta.readstat_variable_types),
        "value_labels": len(meta.value_labels),
        "variable_to_label": len(meta.variable_to_label),
        "missing_user_values": len(meta.missing_user_values) if meta.missing_user_values else 0,
        "variable_alignment": len(meta.variable_alignment),
        "variable_storage_width": len(meta.variable_storage_width),
        "mr_sets": len(meta.mr_sets) if meta.mr_sets else 0,
    }
    
    # Add file-level metadata if present
    if meta.file_label:
        summary['file_label'] = meta.file_label
    if meta.note:
        summary['has_notes'] = True
        
    return summary
