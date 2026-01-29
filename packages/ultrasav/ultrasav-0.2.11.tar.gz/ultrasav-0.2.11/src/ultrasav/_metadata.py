#_v14_mergeable_readonly_fields
"""
Metadata class with immutable/functional API (Polars-style).

All update operations return NEW Metadata objects - nothing is modified in place.
This allows safe creation of multiple variations from a single base metadata.

v14 Changes:
- Added support for merging "read-only" fields (viewable but not written to SAV)
- These fields can now be updated via .update() for merge operations
- column_names, original_variable_types, readstat_variable_types, value_labels,
  variable_to_label, missing_user_values, variable_alignment, variable_storage_width, mr_sets
"""

import warnings
from pathlib import Path
from typing import Any
from copy import deepcopy

# Valid measure types for SPSS
VALID_MEASURES = frozenset({"nominal", "ordinal", "scale", "unknown"})


class Metadata:
    """
    A class to handle SPSS metadata with immutable/functional updates (Polars-style).
    
    This class takes the original pyreadstat metadata and allows explicit updates.
    All update operations return NEW Metadata objects - nothing is modified in place.
    
    Parameters
    ----------
    meta_obj : pyreadstat metadata object, Metadata, dict, or None
        Can be:
        - pyreadstat metadata object from read_sav()
        - Another Metadata instance (creates a deep copy)
        - dict with metadata parameters to set
        - None for empty metadata
    
    Examples
    --------
    >>> # From pyreadstat
    >>> df, meta_raw = pyreadstat.read_sav("file.sav")
    >>> meta = Metadata(meta_raw)
    
    >>> # Immutable updates - returns NEW object
    >>> meta2 = meta.update(column_labels={"Q1": "Question 1"})
    >>> # meta is UNCHANGED, meta2 has the update
    
    >>> # Multiple updates at once (efficient - single copy)
    >>> meta3 = meta.update(
    ...     column_labels={"Q1": "Question 1"},
    ...     variable_measure={"Q1": "nominal"},
    ...     variable_value_labels={"Q1": {1: "Yes", 0: "No"}},
    ...     file_label="My Survey"
    ... )
    
    >>> # Convenience with_*() methods (syntactic sugar for update())
    >>> meta4 = (meta
    ...     .with_column_labels({"Q1": "Question 1"})
    ...     .with_variable_measure({"Q1": "nominal"})
    ...     .with_file_label("My Survey")
    ... )
    
    >>> # Create from scratch with dict
    >>> meta = Metadata({
    ...     "column_labels": {"Q1": "Question 1"},
    ...     "variable_measure": {"Q1": "nominal"},
    ...     "file_label": "My Survey"
    ... })
    """
    
    # Class-level constant for valid measures
    VALID_MEASURES = VALID_MEASURES
    
    def __init__(self, meta_obj=None):
        """
        Initialize Metadata instance.
        
        Parameters
        ----------
        meta_obj : pyreadstat metadata object, Metadata, dict, or None
            Can be pyreadstat metadata, another Metadata instance, 
            a dict of parameters, or None for empty
        """
        # Store the original metadata object
        self._original_meta: Any | None = None
        
        # User updates for WRITABLE fields (written to SAV)
        self._user_column_labels: dict[str, str] | None = None
        self._user_variable_value_labels: dict[str, dict[int | float | str, str]] | None = None
        self._user_variable_format: dict[str, str] | None = None
        self._user_variable_measure: dict[str, str] | None = None
        self._user_variable_display_width: dict[str, int] | None = None
        self._user_missing_ranges: dict[str, list] | None = None
        self._user_note: str | list[str] | None = None
        self._user_file_label: str | None = None
        self._user_compress: bool | None = None
        self._user_row_compress: bool | None = None
        
        # User updates for MERGEABLE fields (viewable but NOT written to SAV)
        self._user_column_names: list[str] | None = None
        self._user_number_columns: int | None = None
        self._user_number_rows: int | None = None
        self._user_original_variable_types: dict[str, str] | None = None
        self._user_readstat_variable_types: dict[str, str] | None = None
        self._user_value_labels: dict[str, dict] | None = None
        self._user_variable_to_label: dict[str, str] | None = None
        self._user_missing_user_values: dict | None = None
        self._user_variable_alignment: dict[str, str] | None = None
        self._user_variable_storage_width: dict[str, int] | None = None
        self._user_mr_sets: dict | None = None
        
        if meta_obj is not None:
            # Check if it's already a Metadata instance - copy its internals
            if isinstance(meta_obj, Metadata):
                self._original_meta = meta_obj._original_meta
                
                # Copy writable field updates
                self._user_column_labels = deepcopy(meta_obj._user_column_labels)
                self._user_variable_value_labels = deepcopy(meta_obj._user_variable_value_labels)
                self._user_variable_format = deepcopy(meta_obj._user_variable_format)
                self._user_variable_measure = deepcopy(meta_obj._user_variable_measure)
                self._user_variable_display_width = deepcopy(meta_obj._user_variable_display_width)
                self._user_missing_ranges = deepcopy(meta_obj._user_missing_ranges)
                self._user_note = deepcopy(meta_obj._user_note)
                self._user_file_label = meta_obj._user_file_label
                self._user_compress = meta_obj._user_compress
                self._user_row_compress = meta_obj._user_row_compress
                
                # Copy mergeable field updates (v14)
                self._user_column_names = deepcopy(meta_obj._user_column_names)
                self._user_number_columns = meta_obj._user_number_columns
                self._user_number_rows = meta_obj._user_number_rows
                self._user_original_variable_types = deepcopy(meta_obj._user_original_variable_types)
                self._user_readstat_variable_types = deepcopy(meta_obj._user_readstat_variable_types)
                self._user_value_labels = deepcopy(meta_obj._user_value_labels)
                self._user_variable_to_label = deepcopy(meta_obj._user_variable_to_label)
                self._user_missing_user_values = deepcopy(meta_obj._user_missing_user_values)
                self._user_variable_alignment = deepcopy(meta_obj._user_variable_alignment)
                self._user_variable_storage_width = deepcopy(meta_obj._user_variable_storage_width)
                self._user_mr_sets = deepcopy(meta_obj._user_mr_sets)
                
            # Check if it's pyreadstat metadata (has specific attributes)
            elif hasattr(meta_obj, 'column_names') and hasattr(meta_obj, 'column_labels'):
                # It's pyreadstat metadata
                self._original_meta = meta_obj
            elif isinstance(meta_obj, dict):
                # It's user-provided dict of updates - apply via update()
                # Create a temporary copy and apply updates
                self._apply_updates_internal(**meta_obj)
            else:
                # Try to detect if it's pyreadstat metadata by other attributes
                if hasattr(meta_obj, 'number_columns') or hasattr(meta_obj, 'file_label'):
                    self._original_meta = meta_obj
                else:
                    raise TypeError(
                        f"Unsupported metadata type: {type(meta_obj)}. "
                        "Expected pyreadstat metadata object, Metadata, dict, or None."
                    )
    
    @classmethod
    def from_pyreadstat(cls, meta_obj):
        """
        Create a Metadata instance from a pyreadstat metadata object.
        
        DEPRECATED: Use Metadata(meta_obj) instead.
        
        Parameters
        ----------
        meta_obj : pyreadstat metadata object or None
            The metadata object returned by pyreadstat.read_sav()
        
        Returns
        -------
        Metadata
            A new Metadata instance
        """
        warnings.warn(
            "Metadata.from_pyreadstat() is deprecated. Use Metadata(meta_obj) instead.",
            DeprecationWarning,
            stacklevel=2
        )
        return cls(meta_obj)
    
    def _merge_with_original(self, user_dict: dict | None, 
                           original_attr: str, 
                           process_values: bool = False) -> dict:
        """
        Generic method to merge user updates with original metadata.
        
        Parameters
        ----------
        user_dict : dict or None
            User-provided updates
        original_attr : str
            Name of the attribute in original metadata
        process_values : bool
            If True, process value labels (convert keys to numbers)
        
        Returns
        -------
        dict
            Merged dictionary (original + updates)
        """
        # If no user updates, return original
        if not user_dict:
            if not self._original_meta or not hasattr(self._original_meta, original_attr):
                return {}
            original = getattr(self._original_meta, original_attr)
            return original.copy() if original else {}
        
        # If no original metadata, return user updates
        if not self._original_meta or not hasattr(self._original_meta, original_attr):
            if process_values:
                # Convert keys to numbers if possible for value labels
                converted = {}
                for var, lbls in user_dict.items():
                    converted[var] = self._convert_keys_to_numbers_if_possible(lbls)
                return converted
            return user_dict.copy()
        
        # Merge: start with original, then apply user updates
        original = getattr(self._original_meta, original_attr)
        existing = original.copy() if original else {}
        
        # Apply user updates
        for key, value in user_dict.items():
            if process_values:
                existing[key] = self._convert_keys_to_numbers_if_possible(value)
            else:
                existing[key] = value
        
        return existing
    
    # ===================================================================
    # VALIDATION HELPERS
    # ===================================================================
    
    def _validate_measure_values(self, measure_dict: dict[str, str]) -> None:
        """
        Validate that all measure values are valid SPSS measure types.
        
        Parameters
        ----------
        measure_dict : dict
            Dictionary of {variable_name: measure_type}
            
        Raises
        ------
        ValueError
            If any measure value is not in VALID_MEASURES
        """
        invalid_entries = {
            var: measure for var, measure in measure_dict.items() 
            if measure not in VALID_MEASURES
        }
        
        if invalid_entries:
            invalid_list = [f"'{var}': '{measure}'" for var, measure in invalid_entries.items()]
            raise ValueError(
                f"Invalid measure type(s): {', '.join(invalid_list)}. "
                f"Valid options are: {', '.join(sorted(VALID_MEASURES))}"
            )
    
    def _validate_format_type_changes(self, new_formats: dict[str, str]) -> None:
        """
        Warn if variable_format changes involve incompatible type changes.
        
        Compares new format strings against original formats and warns if
        the format type category changes (e.g., numeric to string).
        
        Parameters
        ----------
        new_formats : dict[str, str]
            Dictionary of {variable_name: new_format_string}
        """
        if not new_formats or not self._original_meta:
            return
        
        # Get original formats
        original_formats = getattr(self._original_meta, 'original_variable_types', {})
        if not original_formats:
            return
        
        # Check each new format against original
        for var_name, new_format in new_formats.items():
            if var_name not in original_formats:
                continue  # New variable, no comparison needed
            
            old_format = original_formats[var_name]
            old_type = _get_format_type(old_format)
            new_type = _get_format_type(new_format)
            
            # Warn if types are different and neither is unknown
            if old_type != new_type and old_type != 'unknown' and new_type != 'unknown':
                warnings.warn(
                    f"variable_format type change for '{var_name}': "
                    f"'{old_format}' ({old_type}) → '{new_format}' ({new_type}). "
                    f"Ensure the column data type matches the new format, "
                    f"or this may cause read/write errors.",
                    UserWarning,
                    stacklevel=4  # Points to the user's code calling update()/with_*()
                )
    
    def _validate_zsav_extension(self, dst_path: str | Path) -> None:
        """
        Validate that compressed files use .zsav extension.
        
        Parameters
        ----------
        dst_path : str or Path
            Destination file path
            
        Raises
        ------
        ValueError
            If compress=True but file extension is not .zsav
        """
        path = Path(dst_path)
        extension = path.suffix.lower()
        
        if self.compress and extension != '.zsav':
            raise ValueError(
                f"Metadata has compress=True but destination file '{dst_path}' "
                f"has extension '{extension}'. Compressed SPSS files must use "
                f"the '.zsav' extension. Either change the file extension to '.zsav' "
                f"or set compress=False in the metadata."
            )
    
    # ===================================================================
    # WRITABLE PROPERTIES (written to SAV via get_write_params)
    # ===================================================================
    
    @property
    def column_labels(self) -> dict[str, str]:
        """Get current column labels (original + updates)."""
        if not self._user_column_labels:
            if not self._original_meta:
                return {}
            # Special handling for column_labels as it's stored differently
            if hasattr(self._original_meta, 'column_names') and hasattr(self._original_meta, 'column_labels'):
                return dict(zip(self._original_meta.column_names, 
                              self._original_meta.column_labels))
            return {}
        
        if self._original_meta is None:
            return self._user_column_labels.copy()
        
        # Start with existing labels
        existing = {}
        if hasattr(self._original_meta, 'column_names') and hasattr(self._original_meta, 'column_labels'):
            existing = dict(zip(self._original_meta.column_names, 
                              self._original_meta.column_labels))
        
        # Override with user updates
        return {**existing, **self._user_column_labels}
    
    @property
    def variable_value_labels(self) -> dict[str, dict[int | float | str, str]]:
        """Get current variable value labels (original + updates)."""
        return self._merge_with_original(
            self._user_variable_value_labels,
            'variable_value_labels',
            process_values=True
        )
    
    @property
    def variable_format(self) -> dict[str, str]:
        """Get current variable formats (original + updates)."""
        # First try variable_format, then fall back to original_variable_types
        if hasattr(self._original_meta, 'variable_format') and self._original_meta.variable_format:
            return self._merge_with_original(
                self._user_variable_format,
                'variable_format'
            )
        elif hasattr(self._original_meta, 'original_variable_types') and not self._user_variable_format:
            # Use original_variable_types as fallback if no variable_format exists
            return self._original_meta.original_variable_types.copy()
        else:
            # Merge user updates with original_variable_types if available
            if self._user_variable_format:
                if hasattr(self._original_meta, 'original_variable_types'):
                    existing = self._original_meta.original_variable_types.copy()
                    for key, value in self._user_variable_format.items():
                        existing[key] = value
                    return existing
                return self._user_variable_format.copy()
            return {}
    
    @property
    def variable_measure(self) -> dict[str, str]:
        """Get current variable measures (original + updates)."""
        return self._merge_with_original(
            self._user_variable_measure,
            'variable_measure'
        )
    
    @property
    def variable_display_width(self) -> dict[str, int]:
        """Get current variable display widths (original + updates)."""
        return self._merge_with_original(
            self._user_variable_display_width,
            'variable_display_width'
        )
    
    @property
    def missing_ranges(self) -> dict[str, list] | None:
        """Get current missing ranges (original + updates)."""
        # missing_ranges follows same merge pattern
        if not self._user_missing_ranges:
            return getattr(self._original_meta, "missing_ranges", None) if self._original_meta else None
        
        if not self._original_meta or not hasattr(self._original_meta, "missing_ranges"):
            return self._user_missing_ranges.copy()
        
        # Merge: start with original, apply user updates
        original = getattr(self._original_meta, "missing_ranges", {})
        if original:
            merged = original.copy()
            for key, value in self._user_missing_ranges.items():
                merged[key] = value
            return merged
        return self._user_missing_ranges.copy()
    
    @property
    def note(self) -> str | list[str] | None:
        """Get current note (user or original)."""
        if self._user_note is not None:
            return self._user_note
        if self._original_meta and hasattr(self._original_meta, "notes") and self._original_meta.notes:
            return self._original_meta.notes
        return None
    
    @property
    def file_label(self) -> str:
        """Get current file label (user or original)."""
        if self._user_file_label is not None:
            return self._user_file_label
        return getattr(self._original_meta, "file_label", "") if self._original_meta else ""
    
    @property
    def compress(self) -> bool:
        """Get compress setting."""
        return self._user_compress if self._user_compress is not None else False
    
    @property
    def row_compress(self) -> bool:
        """Get row_compress setting."""
        return self._user_row_compress if self._user_row_compress is not None else False
    
    # ===================================================================
    # MERGEABLE PROPERTIES (viewable, NOT written to SAV)
    # These can be updated via .update() for merge operations
    # ===================================================================
    
    @property
    def notes(self) -> str | list[str] | None:
        """Get notes from original metadata (same as note property)."""
        return self.note
    
    @property
    def creation_time(self) -> str | None:
        """Get creation time from original metadata."""
        return getattr(self._original_meta, "creation_time", None) if self._original_meta else None
    
    @property
    def modification_time(self) -> str | None:
        """Get modification time from original metadata."""
        return getattr(self._original_meta, "modification_time", None) if self._original_meta else None
    
    @property
    def file_encoding(self) -> str | None:
        """Get file encoding from original metadata."""
        return getattr(self._original_meta, "file_encoding", None) if self._original_meta else None
    
    @property
    def table_name(self) -> str | None:
        """Get table name from original metadata."""
        return getattr(self._original_meta, "table_name", None) if self._original_meta else None
    
    @property
    def column_names(self) -> list[str]:
        """Get column names (original + user updates for merged metadata)."""
        # Start with original
        original_names = []
        if self._original_meta and hasattr(self._original_meta, 'column_names'):
            original_names = list(self._original_meta.column_names)
        
        # If no user updates, return original
        if not self._user_column_names:
            return original_names
        
        # Merge: original + new names from user (preserving order, no duplicates)
        merged = list(original_names)
        for name in self._user_column_names:
            if name not in merged:
                merged.append(name)
        return merged
    
    @property
    def column_names_to_labels(self) -> dict[str, str]:
        """Get column names to labels mapping (same as column_labels property)."""
        return self.column_labels
    
    @property
    def number_columns(self) -> int | None:
        """Get number of columns (user value or from original metadata)."""
        if self._user_number_columns is not None:
            return self._user_number_columns
        return getattr(self._original_meta, "number_columns", None) if self._original_meta else None
    
    @property
    def number_rows(self) -> int | None:
        """Get number of rows (user value or from original metadata)."""
        if self._user_number_rows is not None:
            return self._user_number_rows
        return getattr(self._original_meta, "number_rows", None) if self._original_meta else None
    
    @property
    def original_variable_types(self) -> dict[str, str]:
        """Get original variable types (original + user updates for merged metadata)."""
        return self._merge_with_original(
            self._user_original_variable_types,
            'original_variable_types'
        )
    
    @property
    def readstat_variable_types(self) -> dict[str, str]:
        """Get readstat variable types (original + user updates for merged metadata)."""
        return self._merge_with_original(
            self._user_readstat_variable_types,
            'readstat_variable_types'
        )
    
    @property
    def value_labels(self) -> dict:
        """Get value labels (original + user updates for merged metadata)."""
        return self._merge_with_original(
            self._user_value_labels,
            'value_labels'
        )
    
    @property
    def variable_to_label(self) -> dict[str, str]:
        """Get variable to label mapping (original + user updates for merged metadata)."""
        return self._merge_with_original(
            self._user_variable_to_label,
            'variable_to_label'
        )
    
    @property
    def missing_user_values(self) -> dict | None:
        """Get missing user values (original + user updates for merged metadata)."""
        if not self._user_missing_user_values:
            return getattr(self._original_meta, "missing_user_values", None) if self._original_meta else None
        
        if not self._original_meta or not hasattr(self._original_meta, "missing_user_values"):
            return self._user_missing_user_values.copy()
        
        original = getattr(self._original_meta, "missing_user_values", {})
        if original:
            merged = original.copy()
            for key, value in self._user_missing_user_values.items():
                if key not in merged:
                    merged[key] = value
            return merged
        return self._user_missing_user_values.copy()
    
    @property
    def variable_alignment(self) -> dict[str, str]:
        """Get variable alignment (original + user updates for merged metadata)."""
        return self._merge_with_original(
            self._user_variable_alignment,
            'variable_alignment'
        )
    
    @property
    def variable_storage_width(self) -> dict[str, int]:
        """Get variable storage width (original + user updates for merged metadata)."""
        return self._merge_with_original(
            self._user_variable_storage_width,
            'variable_storage_width'
        )
    
    @property
    def mr_sets(self) -> dict | None:
        """Get multiple response sets (original + user updates for merged metadata)."""
        if not self._user_mr_sets:
            return getattr(self._original_meta, "mr_sets", None) if self._original_meta else None
        
        if not self._original_meta or not hasattr(self._original_meta, "mr_sets"):
            return self._user_mr_sets.copy()
        
        original = getattr(self._original_meta, "mr_sets", {})
        if original:
            merged = original.copy()
            for key, value in self._user_mr_sets.items():
                if key not in merged:
                    merged[key] = value
            return merged
        return self._user_mr_sets.copy()
    
    # ===================================================================
    # IMMUTABLE UPDATE METHODS (return NEW Metadata objects)
    # ===================================================================
    
    def _apply_updates_internal(self, **kwargs) -> None:
        """
        Internal method to apply updates directly to this instance.
        Used only during __init__ when constructing from dict.
        
        This is NOT part of the public API - use update() or with_*() methods.
        """
        for key, value in kwargs.items():
            # Writable fields (written to SAV)
            if key == 'column_labels':
                self._user_column_labels = value
            elif key == 'variable_value_labels':
                self._user_variable_value_labels = value
            elif key == 'variable_format':
                self._user_variable_format = value
            elif key == 'variable_measure':
                if value is not None:
                    self._validate_measure_values(value)
                self._user_variable_measure = value
            elif key == 'variable_display_width':
                self._user_variable_display_width = value
            elif key == 'missing_ranges':
                self._user_missing_ranges = value
            elif key == 'note':
                self._user_note = value
            elif key == 'file_label':
                self._user_file_label = value
            elif key == 'compress':
                self._user_compress = value
            elif key == 'row_compress':
                self._user_row_compress = value
            
            # Mergeable fields (viewable but NOT written to SAV) - v14
            elif key == 'column_names':
                self._user_column_names = value
            elif key == 'number_columns':
                self._user_number_columns = value
            elif key == 'number_rows':
                self._user_number_rows = value
            elif key == 'original_variable_types':
                self._user_original_variable_types = value
            elif key == 'readstat_variable_types':
                self._user_readstat_variable_types = value
            elif key == 'value_labels':
                self._user_value_labels = value
            elif key == 'variable_to_label':
                self._user_variable_to_label = value
            elif key == 'missing_user_values':
                self._user_missing_user_values = value
            elif key == 'variable_alignment':
                self._user_variable_alignment = value
            elif key == 'variable_storage_width':
                self._user_variable_storage_width = value
            elif key == 'mr_sets':
                self._user_mr_sets = value
            
            else:
                warnings.warn(f"Unknown metadata attribute: {key}", UserWarning, stacklevel=3)
    
    def update(
        self,
        # Writable fields (written to SAV)
        column_labels: dict[str, str] | None = None,
        variable_value_labels: dict[str, dict[int | float | str, str]] | None = None,
        variable_format: dict[str, str] | None = None,
        variable_measure: dict[str, str] | None = None,
        variable_display_width: dict[str, int] | None = None,
        missing_ranges: dict[str, list] | None = None,
        note: str | list[str] | None = None,
        file_label: str | None = None,
        compress: bool | None = None,
        row_compress: bool | None = None,
        # Mergeable fields (viewable but NOT written to SAV) - v14
        column_names: list[str] | None = None,
        number_columns: int | None = None,
        number_rows: int | None = None,
        original_variable_types: dict[str, str] | None = None,
        readstat_variable_types: dict[str, str] | None = None,
        value_labels: dict[str, dict] | None = None,
        variable_to_label: dict[str, str] | None = None,
        missing_user_values: dict | None = None,
        variable_alignment: dict[str, str] | None = None,
        variable_storage_width: dict[str, int] | None = None,
        mr_sets: dict | None = None,
    ) -> 'Metadata':
        """
        Return a NEW Metadata object with the specified updates applied.
        
        This method does NOT modify the current object (immutable/Polars-style).
        Updates are merged with existing values - new keys are added, existing keys
        are replaced.
        
        Parameters
        ----------
        column_labels : dict[str, str], optional
            Variable labels {var_name: label}
        variable_value_labels : dict[str, dict], optional
            Value labels {var_name: {code: label}}
        variable_format : dict[str, str], optional
            SPSS format strings {var_name: format} e.g., {"age": "F3.0", "name": "A50"}
        variable_measure : dict[str, str], optional
            Measure types {var_name: measure}
            Valid values: "nominal", "ordinal", "scale", "unknown"
        variable_display_width : dict[str, int], optional
            Display widths {var_name: width}
        missing_ranges : dict[str, list], optional
            Missing value definitions {var_name: [values or ranges]}
        note : str | list[str], optional
            File note(s)
        file_label : str, optional
            File label
        compress : bool, optional
            If True, write as compressed .zsav
        row_compress : bool, optional
            If True, use row compression
        
        Mergeable Fields (v14) - viewable but NOT written to SAV
        ---------------------------------------------------------
        column_names : list[str], optional
            Column names to add (merged with existing, no duplicates)
        number_columns : int, optional
            Number of columns (for merged metadata)
        number_rows : int, optional
            Number of rows (for merged metadata)
        original_variable_types : dict[str, str], optional
            Original SPSS format types
        readstat_variable_types : dict[str, str], optional
            Readstat internal types
        value_labels : dict[str, dict], optional
            Named value label set definitions
        variable_to_label : dict[str, str], optional
            Variable to label set mapping
        missing_user_values : dict, optional
            Additional missing value info
        variable_alignment : dict[str, str], optional
            Variable alignment (left/center/right)
        variable_storage_width : dict[str, int], optional
            Internal storage width
        mr_sets : dict, optional
            Multiple response set definitions
        
        Returns
        -------
        Metadata
            A NEW Metadata object with updates applied
        
        Examples
        --------
        >>> meta2 = meta.update(
        ...     column_labels={"Q1": "Question 1", "Q2": "Question 2"},
        ...     variable_measure={"Q1": "nominal", "Q2": "ordinal"},
        ...     file_label="My Survey 2025"
        ... )
        >>> # meta is UNCHANGED, meta2 has the updates
        """
        # Create a copy of this instance
        new_meta = Metadata(self)
        
        # === Writable fields (written to SAV) ===
        
        # Merge updates with existing user updates (not replace entirely)
        if column_labels is not None:
            existing = new_meta._user_column_labels or {}
            new_meta._user_column_labels = {**existing, **column_labels}
        
        if variable_value_labels is not None:
            existing = new_meta._user_variable_value_labels or {}
            new_meta._user_variable_value_labels = {**existing, **variable_value_labels}
        
        if variable_format is not None:
            self._validate_format_type_changes(variable_format)
            existing = new_meta._user_variable_format or {}
            new_meta._user_variable_format = {**existing, **variable_format}
        
        if variable_measure is not None:
            self._validate_measure_values(variable_measure)
            existing = new_meta._user_variable_measure or {}
            new_meta._user_variable_measure = {**existing, **variable_measure}
        
        if variable_display_width is not None:
            existing = new_meta._user_variable_display_width or {}
            new_meta._user_variable_display_width = {**existing, **variable_display_width}
        
        if missing_ranges is not None:
            existing = new_meta._user_missing_ranges or {}
            new_meta._user_missing_ranges = {**existing, **missing_ranges}
        
        # These replace entirely (not dicts)
        if note is not None:
            new_meta._user_note = note
        
        if file_label is not None:
            new_meta._user_file_label = file_label
        
        if compress is not None:
            new_meta._user_compress = compress
        
        if row_compress is not None:
            new_meta._user_row_compress = row_compress
        
        # === Mergeable fields (viewable but NOT written to SAV) - v14 ===
        
        if column_names is not None:
            existing = new_meta._user_column_names or []
            # For list: add new items not already present
            merged_names = list(existing)
            for name in column_names:
                if name not in merged_names:
                    merged_names.append(name)
            new_meta._user_column_names = merged_names
        
        # These replace entirely (not dicts/lists) - calculated during merge
        if number_columns is not None:
            new_meta._user_number_columns = number_columns
        
        if number_rows is not None:
            new_meta._user_number_rows = number_rows
        
        if original_variable_types is not None:
            existing = new_meta._user_original_variable_types or {}
            new_meta._user_original_variable_types = {**existing, **original_variable_types}
        
        if readstat_variable_types is not None:
            existing = new_meta._user_readstat_variable_types or {}
            new_meta._user_readstat_variable_types = {**existing, **readstat_variable_types}
        
        if value_labels is not None:
            existing = new_meta._user_value_labels or {}
            new_meta._user_value_labels = {**existing, **value_labels}
        
        if variable_to_label is not None:
            existing = new_meta._user_variable_to_label or {}
            new_meta._user_variable_to_label = {**existing, **variable_to_label}
        
        if missing_user_values is not None:
            existing = new_meta._user_missing_user_values or {}
            new_meta._user_missing_user_values = {**existing, **missing_user_values}
        
        if variable_alignment is not None:
            existing = new_meta._user_variable_alignment or {}
            new_meta._user_variable_alignment = {**existing, **variable_alignment}
        
        if variable_storage_width is not None:
            existing = new_meta._user_variable_storage_width or {}
            new_meta._user_variable_storage_width = {**existing, **variable_storage_width}
        
        if mr_sets is not None:
            existing = new_meta._user_mr_sets or {}
            new_meta._user_mr_sets = {**existing, **mr_sets}
        
        return new_meta
    
    # ===================================================================
    # CONVENIENCE with_*() METHODS (syntactic sugar, call update() internally)
    # ===================================================================
    
    def with_column_labels(self, labels: dict[str, str]) -> 'Metadata':
        """
        Return a NEW Metadata with updated column labels.
        
        This is syntactic sugar for: meta.update(column_labels=labels)
        
        Parameters
        ----------
        labels : dict[str, str]
            Column labels to add/update {var_name: label}
            
        Returns
        -------
        Metadata
            New Metadata object with updated labels
            
        Examples
        --------
        >>> meta2 = meta.with_column_labels({"Q1": "Question 1", "Q2": "Question 2"})
        """
        return self.update(column_labels=labels)
    
    def with_variable_value_labels(
        self, 
        labels: dict[str, dict[int | float | str, str]]
    ) -> 'Metadata':
        """
        Return a NEW Metadata with updated variable value labels.
        
        This is syntactic sugar for: meta.update(variable_value_labels=labels)
        
        Parameters
        ----------
        labels : dict[str, dict]
            Value labels {var_name: {code: label}}
            
        Returns
        -------
        Metadata
            New Metadata object with updated value labels
            
        Examples
        --------
        >>> meta2 = meta.with_variable_value_labels({
        ...     "Q1": {1: "Yes", 0: "No"},
        ...     "Q2": {1: "Agree", 2: "Neutral", 3: "Disagree"}
        ... })
        """
        return self.update(variable_value_labels=labels)
    
    def with_variable_format(self, formats: dict[str, str]) -> 'Metadata':
        """
        Return a NEW Metadata with updated variable formats.
        
        This is syntactic sugar for: meta.update(variable_format=formats)
        
        Parameters
        ----------
        formats : dict[str, str]
            Variable formats {var_name: format_string}
            Common formats: "F8.2" (numeric), "A50" (string), "F3.0" (integer)
            
        Returns
        -------
        Metadata
            New Metadata object with updated formats
            
        Examples
        --------
        >>> meta2 = meta.with_variable_format({
        ...     "age": "F3.0",
        ...     "income": "F10.2",
        ...     "city": "A50"
        ... })
        """
        return self.update(variable_format=formats)
    
    def with_variable_measure(self, measures: dict[str, str]) -> 'Metadata':
        """
        Return a NEW Metadata with updated variable measures.
        
        This is syntactic sugar for: meta.update(variable_measure=measures)
        
        Parameters
        ----------
        measures : dict[str, str]
            Variable measures {var_name: measure_type}
            Valid types: "nominal", "ordinal", "scale", "unknown"
            
        Returns
        -------
        Metadata
            New Metadata object with updated measures
            
        Raises
        ------
        ValueError
            If any measure value is not valid
            
        Examples
        --------
        >>> meta2 = meta.with_variable_measure({
        ...     "gender": "nominal",
        ...     "satisfaction": "ordinal",
        ...     "age": "scale"
        ... })
        """
        return self.update(variable_measure=measures)
    
    def with_variable_display_width(self, widths: dict[str, int]) -> 'Metadata':
        """
        Return a NEW Metadata with updated variable display widths.
        
        This is syntactic sugar for: meta.update(variable_display_width=widths)
        
        Parameters
        ----------
        widths : dict[str, int]
            Display widths {var_name: width}
            
        Returns
        -------
        Metadata
            New Metadata object with updated display widths
            
        Examples
        --------
        >>> meta2 = meta.with_variable_display_width({"Q1": 10, "long_text": 50})
        """
        return self.update(variable_display_width=widths)
    
    def with_missing_ranges(self, ranges: dict[str, list]) -> 'Metadata':
        """
        Return a NEW Metadata with updated missing value definitions.
        
        This is syntactic sugar for: meta.update(missing_ranges=ranges)
        
        Parameters
        ----------
        ranges : dict[str, list]
            Missing values {var_name: [values or {"lo": x, "hi": y} ranges]}
            
        Returns
        -------
        Metadata
            New Metadata object with updated missing ranges
            
        Examples
        --------
        >>> meta2 = meta.with_missing_ranges({
        ...     "Q1": [99],  # Single discrete value
        ...     "Q2": [98, 99],  # Multiple discrete values
        ...     "age": [{"lo": 998, "hi": 999}]  # Range
        ... })
        """
        return self.update(missing_ranges=ranges)
    
    def with_note(self, note: str | list[str]) -> 'Metadata':
        """
        Return a NEW Metadata with updated file note.
        
        This is syntactic sugar for: meta.update(note=note)
        
        Parameters
        ----------
        note : str | list[str]
            File note(s). If list, will be joined with newlines when writing.
            
        Returns
        -------
        Metadata
            New Metadata object with updated note
            
        Examples
        --------
        >>> meta2 = meta.with_note("Created on 2025-01-19")
        >>> meta3 = meta.with_note(["Line 1", "Line 2", "Line 3"])
        """
        return self.update(note=note)
    
    def with_file_label(self, label: str) -> 'Metadata':
        """
        Return a NEW Metadata with updated file label.
        
        This is syntactic sugar for: meta.update(file_label=label)
        
        Parameters
        ----------
        label : str
            File label
            
        Returns
        -------
        Metadata
            New Metadata object with updated file label
            
        Examples
        --------
        >>> meta2 = meta.with_file_label("Customer Satisfaction Survey 2025")
        """
        return self.update(file_label=label)
    
    def with_compress(self, compress: bool = True) -> 'Metadata':
        """
        Return a NEW Metadata with compression setting.
        
        This is syntactic sugar for: meta.update(compress=compress)
        
        Parameters
        ----------
        compress : bool, default True
            If True, file will be written as compressed .zsav
            
        Returns
        -------
        Metadata
            New Metadata object with updated compression setting
            
        Examples
        --------
        >>> meta2 = meta.with_compress(True)  # Will write as .zsav
        """
        return self.update(compress=compress)
    
    def with_row_compress(self, row_compress: bool = True) -> 'Metadata':
        """
        Return a NEW Metadata with row compression setting.
        
        This is syntactic sugar for: meta.update(row_compress=row_compress)
        
        Parameters
        ----------
        row_compress : bool, default True
            If True, use row compression when writing
            
        Returns
        -------
        Metadata
            New Metadata object with updated row compression setting
            
        Note
        ----
        compress and row_compress cannot both be True.
        
        Examples
        --------
        >>> meta2 = meta.with_row_compress(True)
        """
        return self.update(row_compress=row_compress)
    
    # ===================================================================
    # UTILITY METHODS
    # ===================================================================
    
    def _convert_keys_to_numbers_if_possible(self, value_labels_dict):
        """Convert string keys to numbers where possible (from v1.0 logic)."""
        updated = {}
        for k, v in value_labels_dict.items():
            try:
                temp = float(k)
                if temp.is_integer():
                    temp = int(temp)
                updated[temp] = v
            except (ValueError, TypeError):
                updated[k] = v
        return updated
    
    def _force_string_labels(self, labels_dict):
        """Ensure all labels are strings (from v1.0 logic)."""
        if not labels_dict:
            return {}
        fixed = {}
        for col_name, lbl_val in labels_dict.items():
            col_name_str = str(col_name)
            label_str = str(lbl_val) if lbl_val is not None else ""
            fixed[col_name_str] = label_str
        return fixed
    
    def _resolve_compress_settings(self):
        """Resolve compression settings."""
        final_compress = self.compress
        final_row_compress = self.row_compress
        
        if final_compress and final_row_compress:
            warnings.warn(
                "Both 'compress' and 'row_compress' are True; prioritizing 'compress' over 'row_compress'.",
                UserWarning,
                stacklevel=2
            )
            final_row_compress = False
        
        return final_compress, final_row_compress
    
    def get_write_params(self, dst_path: str | Path | None = None) -> dict[str, Any]:
        """
        Get parameters formatted for pyreadstat.write_sav().
        
        Only returns WRITABLE fields - mergeable fields (column_names, 
        original_variable_types, etc.) are NOT included.
        
        Parameters
        ----------
        dst_path : str or Path, optional
            Destination file path. If provided and compress=True, validates
            that the file extension is .zsav.
        
        Returns
        -------
        dict
            Dictionary of parameters ready to pass to write_sav
            
        Raises
        ------
        ValueError
            If compress=True but dst_path does not have .zsav extension
        """
        # Validate zsav extension if dst_path provided and compress is True
        if dst_path is not None:
            self._validate_zsav_extension(dst_path)
        
        # Ensure column labels are all strings
        column_labels = self._force_string_labels(self.column_labels)
        
        # Resolve note formatting
        final_note = self.note
        if isinstance(final_note, list):
            final_note = "\n".join(final_note)
        
        # Resolve compression settings
        final_compress, final_row_compress = self._resolve_compress_settings()
        
        params = {
            'file_label': self.file_label,
            'column_labels': column_labels if column_labels else None,
            'compress': final_compress,
            'row_compress': final_row_compress,
            'note': final_note,
            'variable_value_labels': self.variable_value_labels if self.variable_value_labels else None,
            'missing_ranges': self.missing_ranges,
            'variable_display_width': self.variable_display_width if self.variable_display_width else None,
            'variable_measure': self.variable_measure if self.variable_measure else None,
            'variable_format': self.variable_format if self.variable_format else None,
        }
        
        # Remove None values for cleaner params
        return {k: v for k, v in params.items() if v is not None}
    
    def copy(self) -> 'Metadata':
        """
        Create a deep copy of the metadata.
        
        Returns
        -------
        Metadata
            A new Metadata object that is a complete copy of this one
        """
        return Metadata(self)
    
    @property
    def meta(self) -> dict[str, Any]:
        """
        Return all metadata properties as a dictionary.
        
        This provides a complete snapshot of all metadata - both writable and
        mergeable properties - in a single dict for easy export or inspection.
        
        Returns
        -------
        dict[str, Any]
            Dictionary containing all metadata properties organized as:
            - File-level info: file_label, note, creation_time, modification_time,
              file_encoding, table_name, number_columns, number_rows
            - Writable properties: column_labels, variable_value_labels, variable_format,
              variable_measure, variable_display_width, missing_ranges, compress, row_compress
            - Mergeable properties: column_names, original_variable_types,
              readstat_variable_types, value_labels, variable_to_label,
              missing_user_values, variable_alignment, variable_storage_width, mr_sets
        
        Examples
        --------
        >>> # Get all metadata as dict
        >>> all_meta = ulmeta.meta
        >>> all_meta['column_labels']
        {'Q1': 'Question 1', 'Q2': 'Question 2', ...}
        
        >>> # Export to py file
        >>> with open('meta_backup.py', 'w') as f:
        ...     f.write(f"metadata = {repr(ulmeta.meta)}")
        
        >>> # Iterate through all properties
        >>> for name, value in ulmeta.meta.items():
        ...     print(f"{name}: {type(value).__name__}")
        """
        return {
            # === File-level info (base only, not merged) ===
            'file_label': self.file_label,
            'note': self.note,
            'creation_time': self.creation_time,
            'modification_time': self.modification_time,
            'file_encoding': self.file_encoding,
            'table_name': self.table_name,
            'number_columns': self.number_columns,
            'number_rows': self.number_rows,
            
            # === Writable properties (written to SAV) ===
            'column_labels': self.column_labels,
            'variable_value_labels': self.variable_value_labels,
            'variable_format': self.variable_format,
            'variable_measure': self.variable_measure,
            'variable_display_width': self.variable_display_width,
            'missing_ranges': self.missing_ranges,
            'compress': self.compress,
            'row_compress': self.row_compress,
            
            # === Mergeable properties (viewable, NOT written to SAV) ===
            'column_names': self.column_names,
            'original_variable_types': self.original_variable_types,
            'readstat_variable_types': self.readstat_variable_types,
            'value_labels': self.value_labels,
            'variable_to_label': self.variable_to_label,
            'missing_user_values': self.missing_user_values,
            'variable_alignment': self.variable_alignment,
            'variable_storage_width': self.variable_storage_width,
            'mr_sets': self.mr_sets,
        }
    
    def summary(self) -> None:
        """
        Print a summary of the metadata contents.
        
        Displays counts for all metadata properties and highlights user updates.
        
        Examples
        --------
        >>> meta.summary()
        Metadata Summary
        ================
        File Label: My Survey 2025
        ...
        """
        # Count user updates for writable fields
        user_updates = {}
        if self._user_column_labels:
            user_updates['column_labels'] = len(self._user_column_labels)
        if self._user_variable_value_labels:
            user_updates['variable_value_labels'] = len(self._user_variable_value_labels)
        if self._user_variable_format:
            user_updates['variable_format'] = len(self._user_variable_format)
        if self._user_variable_measure:
            user_updates['variable_measure'] = len(self._user_variable_measure)
        if self._user_variable_display_width:
            user_updates['variable_display_width'] = len(self._user_variable_display_width)
        if self._user_missing_ranges:
            user_updates['missing_ranges'] = len(self._user_missing_ranges)
        if self._user_note is not None:
            user_updates['note'] = 1
        if self._user_file_label is not None:
            user_updates['file_label'] = 1
        
        # Count user updates for mergeable fields (v14)
        if self._user_column_names:
            user_updates['column_names'] = len(self._user_column_names)
        if self._user_number_columns is not None:
            user_updates['number_columns'] = 1
        if self._user_number_rows is not None:
            user_updates['number_rows'] = 1
        if self._user_original_variable_types:
            user_updates['original_variable_types'] = len(self._user_original_variable_types)
        if self._user_readstat_variable_types:
            user_updates['readstat_variable_types'] = len(self._user_readstat_variable_types)
        if self._user_value_labels:
            user_updates['value_labels'] = len(self._user_value_labels)
        if self._user_variable_to_label:
            user_updates['variable_to_label'] = len(self._user_variable_to_label)
        if self._user_missing_user_values:
            user_updates['missing_user_values'] = len(self._user_missing_user_values)
        if self._user_variable_alignment:
            user_updates['variable_alignment'] = len(self._user_variable_alignment)
        if self._user_variable_storage_width:
            user_updates['variable_storage_width'] = len(self._user_variable_storage_width)
        if self._user_mr_sets:
            user_updates['mr_sets'] = len(self._user_mr_sets)
        
        print("Metadata Summary")
        print("=" * 50)
        
        # File-level info
        print(f"File Label:        {self.file_label or '(none)'}")
        if self.creation_time:
            print(f"Creation Time:     {self.creation_time}")
        if self.modification_time:
            print(f"Modification Time: {self.modification_time}")
        if self.file_encoding:
            print(f"File Encoding:     {self.file_encoding}")
        
        print()
        print("Column/Row Information")
        print("-" * 50)
        nc_marker = "  (merged)" if 'number_columns' in user_updates else ""
        nr_marker = "  (merged)" if 'number_rows' in user_updates else ""
        print(f"Number of Columns: {self.number_columns or 0}{nc_marker}")
        print(f"Number of Rows:    {self.number_rows or 0}{nr_marker}")
        
        print()
        print("Writable Properties (merged: original + user updates)")
        print("-" * 50)
        
        def format_count(name, merged_count, user_key):
            user_count = user_updates.get(user_key, 0)
            if user_count > 0:
                return f"{name:26} {merged_count:>6} items  (+{user_count} user updates)"
            return f"{name:26} {merged_count:>6} items"
        
        print(format_count("column_labels:", len(self.column_labels), 'column_labels'))
        print(format_count("variable_value_labels:", len(self.variable_value_labels), 'variable_value_labels'))
        print(format_count("variable_format:", len(self.variable_format), 'variable_format'))
        print(format_count("variable_measure:", len(self.variable_measure), 'variable_measure'))
        print(format_count("variable_display_width:", len(self.variable_display_width), 'variable_display_width'))
        
        mr = self.missing_ranges
        mr_count = len(mr) if mr else 0
        print(format_count("missing_ranges:", mr_count, 'missing_ranges'))
        
        # Note display
        note_display = "(none)"
        if self.note:
            if isinstance(self.note, list):
                note_display = f"{len(self.note)} lines"
            else:
                note_display = f"{len(self.note)} chars" if len(self.note) > 50 else f'"{self.note}"'
        user_note_marker = "  (user set)" if 'note' in user_updates else ""
        print(f"{'note:':<26} {note_display}{user_note_marker}")
        
        print()
        print("Compression Settings")
        print("-" * 50)
        print(f"compress:          {self.compress}")
        print(f"row_compress:      {self.row_compress}")
        
        print()
        print("Mergeable Properties (viewable, NOT written to SAV)")
        print("-" * 50)
        print(format_count("column_names:", len(self.column_names), 'column_names'))
        print(format_count("original_variable_types:", len(self.original_variable_types), 'original_variable_types'))
        print(format_count("readstat_variable_types:", len(self.readstat_variable_types), 'readstat_variable_types'))
        print(format_count("value_labels:", len(self.value_labels), 'value_labels'))
        print(format_count("variable_to_label:", len(self.variable_to_label), 'variable_to_label'))
        print(format_count("variable_alignment:", len(self.variable_alignment), 'variable_alignment'))
        print(format_count("variable_storage_width:", len(self.variable_storage_width), 'variable_storage_width'))
        
        muv = self.missing_user_values
        muv_count = len(muv) if muv else 0
        print(format_count("missing_user_values:", muv_count, 'missing_user_values'))
        
        mr_sets = self.mr_sets
        mr_sets_count = len(mr_sets) if mr_sets else 0
        print(format_count("mr_sets:", mr_sets_count, 'mr_sets'))
    
    def __repr__(self) -> str:
        info = []
        if self._original_meta:
            info.append(f"columns={self.number_columns}")
        if self.column_labels:
            info.append(f"labels={len(self.column_labels)}")
        if self.variable_value_labels:
            info.append(f"value_labels={len(self.variable_value_labels)}")
        
        return f"Metadata({', '.join(info)})"


# =============================================================================
# MODULE-LEVEL HELPER FUNCTIONS
# =============================================================================

def _get_format_type(format_str: str) -> str:
    """
    Determine the format type category from an SPSS format string.
    
    Parameters
    ----------
    format_str : str
        SPSS format string like 'F8.2', 'A50', 'DATETIME40'
        
    Returns
    -------
    str
        Format type category: 'string', 'numeric', 'datetime', or 'unknown'
    """
    if not format_str or not isinstance(format_str, str):
        return 'unknown'
    
    # Normalize to uppercase for comparison
    fmt = format_str.upper().strip()
    
    # String formats: A (alphanumeric), AHEX
    if fmt.startswith('A'):
        return 'string'
    
    # Numeric formats: F, N, E, COMMA, DOLLAR, PCT, etc.
    numeric_prefixes = ('F', 'N', 'E', 'COMMA', 'DOLLAR', 'DOT', 'PCT', 'PIBHEX', 'RBHEX', 
                        'Z', 'IB', 'PIB', 'P', 'PK', 'RB', 'CCA', 'CCB', 'CCC', 'CCD', 'CCE')
    if any(fmt.startswith(prefix) for prefix in numeric_prefixes):
        return 'numeric'
    
    # Date/Time formats
    datetime_prefixes = ('DATE', 'ADATE', 'EDATE', 'JDATE', 'SDATE', 'QYR', 'MOYR', 'WKYR',
                         'DATETIME', 'TIME', 'DTIME', 'WKDAY', 'MONTH', 'YMDHMS')
    if any(fmt.startswith(prefix) for prefix in datetime_prefixes):
        return 'datetime'
    
    return 'unknown'
