"""
Variable Type Detection v5 (df-centric)
=======================================

A complete redesign with DataFrame as the source of truth.

Returns one of:
- 'text'         : String data (open-ended, verbatims)
- 'date'         : Date/datetime/duration values
- 'categorical'  : Categorical dtype (explicitly typed)
- 'numeric'      : Numeric values (continuous or unlabeled codes)
- 'single-select': Coded categorical with value labels (from metadata)
- 'multi-select' : Binary indicator variable (0/1 pattern, from metadata)

Design Philosophy:
- Phase 1: Pure DataFrame dtype detection (always runs)
- Phase 2: Metadata refinement (when meta is available)
- df is REQUIRED, meta is OPTIONAL
- Compatible with Polars and Pandas via narwhals
- Compatible with pyreadstat and ultrasav Metadata objects

New in v5:
- df-centric design: detect_variable_type(var_name, df, meta=None, ...)
- Two-phase detection: dtype first, then metadata refinement
- Explicit 'categorical' type for Categorical dtype
- Cleaner separation of concerns
"""

import narwhals as nw
from narwhals.typing import FrameT
import polars as pl
import pandas as pd
from typing import Any
import re


# ---------------------------------------------------------------------------
# Configurable patterns for multi-select detection
# ---------------------------------------------------------------------------

SELECTION_PAIRS = [
    ("not selected", "selected"),
    ("unchecked", "checked"),
    ("no", "yes"),
    ("0", "1"),
    ("not mentioned", "mentioned"),
    ("not chosen", "chosen"),
    ("exclude", "include"),
]

GENERIC_BINARY_LABELS = [
    ("no", "yes"),
    ("false", "true"),
    ("disagree", "agree"),
    ("male", "female"),
    ("off", "on"),
    ("absent", "present"),
]

MULTI_SELECT_NAME_PATTERNS = [
    r"[_\-]?\d+$",        # ends with number
    r"Q\d+[A-Z]$",        # Q1A pattern
    r"r\d+$",             # r1 pattern
    r"_[A-Z]$",           # _A pattern
    r"[A-Z]\d+[A-Z]\d+$", # A1B1 pattern
]


# ---------------------------------------------------------------------------
# Helper: MR set lookup
# ---------------------------------------------------------------------------

def create_mr_set_lookup(meta) -> set[str]:
    """
    Create a set of all variables that belong to multi-response sets.
    
    Works with both pyreadstat metadata and ultrasav Metadata objects.
    
    Parameters
    ----------
    meta : metadata object
        pyreadstat metadata or ultrasav Metadata object
    
    Returns
    -------
    set[str]
        Set of variable names that are part of multi-response sets.
    """
    mr_set_variables: set[str] = set()
    
    if hasattr(meta, "mr_sets") and meta.mr_sets:
        for mr_set_name, mr_set_info in meta.mr_sets.items():
            if isinstance(mr_set_info, dict) and "variable_list" in mr_set_info:
                mr_set_variables.update(mr_set_info["variable_list"])
            elif isinstance(mr_set_info, (list, tuple)):
                # ultrasav Metadata might store as list directly
                mr_set_variables.update(mr_set_info)
    
    return mr_set_variables


# ---------------------------------------------------------------------------
# Helper: Metadata attribute access (works with both pyreadstat and ultrasav)
# ---------------------------------------------------------------------------

def _get_meta_attr(meta, attr_name: str, default=None):
    """
    Safely get attribute from metadata object.
    Works with both pyreadstat metadata and ultrasav Metadata objects.
    """
    if meta is None:
        return default
    return getattr(meta, attr_name, default) or default


# ---------------------------------------------------------------------------
# Helper: Value label analysis for multi-select detection
# ---------------------------------------------------------------------------

def _normalize_value_keys(keys: set[Any]) -> set[Any]:
    """
    Normalize value label keys so that 0/1, 0.0/1.0, and "0"/"1" all map to ints.
    """
    normalized: set[Any] = set()
    for k in keys:
        if isinstance(k, (int, float)) and k in [0, 1, 0.0, 1.0]:
            normalized.add(int(k))
        elif isinstance(k, str) and k in {"0", "1"}:
            normalized.add(int(k))
        else:
            normalized.add(k)
    return normalized


def _is_binary_value_dict(value_dict: dict[Any, str]) -> bool:
    """Check if a value label dict represents a 0/1 binary variable."""
    if len(value_dict) != 2:
        return False
    keys = set(value_dict.keys())
    normalized = _normalize_value_keys(keys)
    return normalized <= {0, 1}


def _labels_lower_pair(value_dict: dict[Any, str]) -> tuple[str, str]:
    """Get labels for 0 and 1 keys, lowercased and stripped."""
    label_0 = str(
        value_dict.get(0, value_dict.get(0.0, value_dict.get("0", "")))
    ).lower().strip()
    label_1 = str(
        value_dict.get(1, value_dict.get(1.0, value_dict.get("1", "")))
    ).lower().strip()
    return label_0, label_1


def _is_generic_binary_labels(label_0: str, label_1: str) -> bool:
    """Check if labels match generic binary patterns like (no, yes)."""
    labels_set_lower = {label_0.lower(), label_1.lower()}
    for pair in GENERIC_BINARY_LABELS:
        if labels_set_lower == {p.lower() for p in pair}:
            return True
    return False


def _match_multi_name_pattern(var_name: str) -> bool:
    """Check if variable name matches multi-select naming patterns."""
    for pattern in MULTI_SELECT_NAME_PATTERNS:
        if re.search(pattern, var_name, re.IGNORECASE):
            return True
    return False


def _get_sibling_vars(meta, df_columns: list[str], var_name: str) -> list[str]:
    """
    Find variables that share the same base as var_name (e.g. Q4A, Q4B...).
    Uses meta.column_names if available, falls back to df columns.
    """
    base_match = re.match(r"(.+?)([A-Z]|\d+)$", var_name, re.IGNORECASE)
    if not base_match:
        return []
    
    base = base_match.group(1)
    
    # Try meta.column_names first, fall back to df columns
    columns = _get_meta_attr(meta, "column_names", None) or df_columns
    
    return [v for v in columns if v.startswith(base) and v != var_name]


def _get_unique_values_for_var(
    df_nw,
    var_name: str,
    unique_value_map: dict[str, set[Any]] | None = None,
) -> set[Any]:
    """
    Get unique values for a variable using narwhals.
    Uses optional cache to avoid recomputing.
    """
    if unique_value_map is not None and var_name in unique_value_map:
        return unique_value_map[var_name]

    unique_vals_df = df_nw.select(nw.col(var_name)).unique()
    unique_vals_native = nw.to_native(unique_vals_df)

    if isinstance(unique_vals_native, pl.DataFrame):
        unique_set = set(unique_vals_native[var_name].to_list())
    else:  # pandas
        unique_set = set(unique_vals_native[var_name].tolist())

    if unique_value_map is not None:
        unique_value_map[var_name] = unique_set

    return unique_set


# ---------------------------------------------------------------------------
# Phase 1: Pure DataFrame dtype detection
# ---------------------------------------------------------------------------

def _detect_from_dtype(var_name: str, df_nw, explain: bool = False):
    """
    Phase 1: Detect variable type purely from DataFrame dtype.
    
    Returns one of: 'text', 'date', 'categorical', 'numeric'
    """
    def _ret(var_type: str, reason: str):
        return (var_type, reason) if explain else var_type
    
    schema = df_nw.schema
    
    if var_name not in schema:
        return _ret("numeric", "PHASE 1: variable not in schema, fallback to numeric")
    
    dtype = schema[var_name]
    
    # String → text
    if dtype == nw.String:
        return _ret("text", "PHASE 1: dtype is String")
    
    # Date types → date
    if dtype in (nw.Date, nw.Datetime, nw.Duration):
        return _ret("date", "PHASE 1: dtype is Date/Datetime/Duration")
    
    # Categorical → categorical
    if dtype == nw.Categorical:
        return _ret("categorical", "PHASE 1: dtype is Categorical")
    
    # Boolean → treat as numeric (could be binary indicator)
    if dtype == nw.Boolean:
        return _ret("numeric", "PHASE 1: dtype is Boolean (binary indicator)")
    
    # All numeric types → numeric
    # Includes: Int8, Int16, Int32, Int64, UInt8, UInt16, UInt32, UInt64, 
    #           Float32, Float64
    # Note: We check this broadly - if it's not string/date/categorical, it's numeric
    return _ret("numeric", f"PHASE 1: dtype is {dtype} (numeric)")


# ---------------------------------------------------------------------------
# Phase 2: Metadata refinement
# ---------------------------------------------------------------------------

def _refine_with_metadata(
    var_name: str,
    phase1_type: str,
    phase1_reason: str,
    df_nw,
    meta,
    mr_set_variables: set[str],
    unique_value_map: dict[str, set[Any]] | None,
    strict_multi: bool,
    explain: bool,
):
    """
    Phase 2: Refine Phase 1 result using metadata.
    
    Can refine:
    - numeric → multi-select (if MR set or binary patterns)
    - numeric → single-select (if value labels exist)
    - categorical → single-select (if value labels confirm)
    """
    def _ret(var_type: str, reason: str):
        return (var_type, reason) if explain else var_type
    
    # Get metadata attributes
    variable_value_labels = _get_meta_attr(meta, "variable_value_labels", {})
    readstat_types = _get_meta_attr(meta, "readstat_variable_types", {})
    original_types = _get_meta_attr(meta, "original_variable_types", {})
    variable_measure = _get_meta_attr(meta, "variable_measure", {})
    
    var_readstat_type = readstat_types.get(var_name)
    var_original_type = original_types.get(var_name, "")
    var_measure = variable_measure.get(var_name, "unknown")
    
    # Get df columns for sibling detection
    df_columns = df_nw.columns
    
    # -------------------------------------------------------------------------
    # Text type: confirm with readstat or return as-is
    # -------------------------------------------------------------------------
    if phase1_type == "text":
        if var_readstat_type == "string":
            return _ret("text", "PHASE 2: confirmed by readstat type 'string'")
        return _ret("text", phase1_reason)
    
    # -------------------------------------------------------------------------
    # Date type: confirm with original_types or return as-is
    # -------------------------------------------------------------------------
    if phase1_type == "date":
        if isinstance(var_original_type, str) and any(
            x in var_original_type.upper() for x in ["DATE", "TIME", "DATETIME"]
        ):
            return _ret("date", "PHASE 2: confirmed by SPSS original type")
        return _ret("date", phase1_reason)
    
    # -------------------------------------------------------------------------
    # Categorical type: map to single-select if value labels exist
    # -------------------------------------------------------------------------
    if phase1_type == "categorical":
        if var_name in variable_value_labels and variable_value_labels[var_name]:
            return _ret("single-select", "PHASE 2: categorical with value labels → single-select")
        return _ret("categorical", phase1_reason)
    
    # -------------------------------------------------------------------------
    # Numeric type: the most complex refinement path
    # -------------------------------------------------------------------------
    if phase1_type == "numeric":
        
        # STEP 2a: Check SPSS Multi-Response Sets
        if var_name in mr_set_variables:
            return _ret("multi-select", "PHASE 2: variable is in meta.mr_sets")
        
        # STEP 2b: DataFrame value pattern analysis with metadata gating
        try:
            schema = df_nw.schema
            
            # Only check binary patterns for non-string columns
            if var_name in schema and schema[var_name] != nw.String:
                
                # Check if metadata confirms 0/1 coding
                metadata_confirms_01_coding = False
                series_confirms_01_coding = False
                
                if var_name in variable_value_labels:
                    keys = set(variable_value_labels[var_name].keys())
                    normalized_keys = _normalize_value_keys(keys)
                    if normalized_keys <= {0, 1}:
                        metadata_confirms_01_coding = True
                
                if not metadata_confirms_01_coding:
                    # Check sibling series context
                    sibling_vars = _get_sibling_vars(meta, df_columns, var_name)
                    if len(sibling_vars) >= 2:
                        siblings_with_01_coding = 0
                        for sibling_var in sibling_vars[:5]:
                            if sibling_var in variable_value_labels:
                                sibling_keys = set(variable_value_labels[sibling_var].keys())
                                sibling_norm = _normalize_value_keys(sibling_keys)
                                if sibling_norm <= {0, 1}:
                                    siblings_with_01_coding += 1
                        if siblings_with_01_coding >= 2:
                            series_confirms_01_coding = True
                
                # Get actual unique values from data
                unique_set = _get_unique_values_for_var(df_nw, var_name, unique_value_map)
                unique_set_no_null = {
                    v for v in unique_set
                    if v is not None and not (isinstance(v, float) and pd.isna(v))
                }
                
                # Multi-select patterns - two tiers:
                # Tier 1: Both 0 and 1 present (strong evidence)
                # Tier 2: Single value {0} or {1} (weak evidence, needs metadata/sibling confirmation)
                strong_patterns = [{0, 1}, {0.0, 1.0}]
                weak_patterns = [{1}, {1.0}, {0}, {0.0}]
                
                is_strong_pattern = unique_set_no_null in strong_patterns
                is_weak_pattern = unique_set_no_null in weak_patterns
                
                # Gating logic - different requirements for strong vs weak patterns
                # Strong pattern: allow if any evidence OR unlabeled
                # Weak pattern: require metadata or sibling confirmation (NOT just unlabeled)
                if is_strong_pattern:
                    gated_ok = (
                        metadata_confirms_01_coding
                        or series_confirms_01_coding
                        or var_name not in variable_value_labels
                        or not strict_multi
                    )
                elif is_weak_pattern:
                    # Stricter: must have metadata or sibling evidence
                    # Being unlabeled alone is NOT enough for single-value patterns
                    gated_ok = (
                        metadata_confirms_01_coding
                        or series_confirms_01_coding
                        or not strict_multi
                    )
                else:
                    gated_ok = False
                
                pattern_match = is_strong_pattern or is_weak_pattern
                
                if gated_ok and pattern_match:
                    reason_parts = []
                    if metadata_confirms_01_coding:
                        reason_parts.append("metadata confirms 0/1")
                    if series_confirms_01_coding:
                        reason_parts.append("sibling series confirms 0/1")
                    if var_name not in variable_value_labels:
                        reason_parts.append("unlabeled")
                    if not strict_multi:
                        reason_parts.append("strict_multi=False")
                    
                    return _ret(
                        "multi-select",
                        f"PHASE 2: binary pattern ({', '.join(reason_parts)})"
                    )
        except Exception:
            pass  # Fall through on any error
        
        # STEP 2c: Value label analysis for categorical detection
        has_value_labels = (
            var_name in variable_value_labels 
            and bool(variable_value_labels[var_name])
        )
        
        if has_value_labels:
            value_dict = variable_value_labels[var_name]
            is_binary = _is_binary_value_dict(value_dict)
            
            if is_binary:
                label_0, label_1 = _labels_lower_pair(value_dict)
                
                # TIER 2: Descriptive label on 1
                if not label_0 or label_0 in ["null", "none", "not selected", ""]:
                    if label_1 and label_1 not in ["yes", "selected", "true", "1"]:
                        return _ret(
                            "multi-select",
                            "PHASE 2: binary with descriptive label on 1"
                        )
                
                # TIER 3: Selection pair + naming pattern
                labels_set_lower = {label_0, label_1}
                for pair in SELECTION_PAIRS:
                    if labels_set_lower == {p.lower() for p in pair}:
                        if _match_multi_name_pattern(var_name):
                            return _ret(
                                "multi-select",
                                "PHASE 2: selection pair labels + naming pattern"
                            )
                
                # TIER 3b: Binary sibling series
                sibling_vars = _get_sibling_vars(meta, df_columns, var_name)
                if len(sibling_vars) >= 2:
                    all_binary = True
                    for similar_var in sibling_vars[:3]:
                        if similar_var in variable_value_labels:
                            similar_dict = variable_value_labels[similar_var]
                            if not _is_binary_value_dict(similar_dict):
                                all_binary = False
                                break
                    if all_binary:
                        return _ret(
                            "multi-select",
                            "PHASE 2: part of binary-coded series"
                        )
                
                # TIER 4: Generic binary → single-select
                if _is_generic_binary_labels(label_0, label_1):
                    return _ret(
                        "single-select",
                        "PHASE 2: generic binary labels (yes/no, etc.)"
                    )
            
            # Non-binary with labels → single-select
            return _ret("single-select", "PHASE 2: has value labels → single-select")
        
        # STEP 2d: Measurement level fallback
        # Note: Only use measurement level to confirm numeric.
        # We do NOT return single-select for nominal/ordinal without value labels,
        # because without labels we can't meaningfully enumerate categories.
        if var_measure == "scale":
            return _ret("numeric", "PHASE 2: measurement level is 'scale'")
        
        # STEP 2e: Readstat type fallback
        if var_readstat_type in ["double", "numeric", "integer", "long"]:
            return _ret("numeric", "PHASE 2: readstat type confirms numeric")
        
        # No refinement possible
        return _ret("numeric", phase1_reason)
    
    # Fallback (shouldn't reach here)
    return _ret(phase1_type, phase1_reason)


# ---------------------------------------------------------------------------
# Main detection function
# ---------------------------------------------------------------------------

def detect_variable_type(
    df: FrameT,
    var_name: str,
    meta: Any | None = None,
    *,
    mr_set_variables: set[str] | None = None,
    unique_value_map: dict[str, set[Any]] | None = None,
    strict_multi: bool = True,
    explain: bool = False,
) -> str | tuple[str, str]:
    """
    Detect the type of a survey variable using a two-phase approach.
    
    Phase 1: Pure DataFrame dtype detection (always runs)
    Phase 2: Metadata refinement (when meta is provided)
    
    Parameters
    ----------
    df : DataFrame (Polars or Pandas)
        The data DataFrame. REQUIRED - this is the source of truth.
    var_name : str
        The variable name to classify.
    meta : metadata object, optional
        Metadata from pyreadstat or ultrasav Metadata object.
        When provided, enables refinement of numeric → single-select/multi-select.
    mr_set_variables : set[str], optional
        Pre-computed set of variables in multi-response sets.
        If None and meta is provided, will be computed from meta.mr_sets.
    unique_value_map : dict[str, set[Any]], optional
        Cache for unique values per variable.
        Pass an empty dict {} to enable caching across multiple calls.
    strict_multi : bool, default True
        If True, requires metadata confirmation (0/1 labels or sibling context)
        before classifying unlabeled binary variables as multi-select.
    explain : bool, default False
        If True, returns (var_type, reason) tuple instead of just var_type.
    
    Returns
    -------
    str or tuple[str, str]
        Variable type classification:
        - 'text': String data (open-ended responses)
        - 'date': Date/datetime values
        - 'categorical': Categorical dtype (rare, requires explicit casting)
        - 'numeric': Continuous numeric or unlabeled codes
        - 'single-select': Coded categorical with value labels (requires meta)
        - 'multi-select': Binary indicator variable (requires meta)
        
        If explain=True, returns (var_type, reason) tuple.
    
    Examples
    --------
    >>> import polars as pl
    >>> import ultrasav as ul
    >>> 
    >>> # DataFrame only (no metadata)
    >>> df = pl.read_csv("survey.csv")
    >>> ul.detect_variable_type(df, "Q1")
    'numeric'
    >>> 
    >>> # With metadata (from SPSS)
    >>> df, meta = ul.read_sav("survey.sav")
    >>> ul.detect_variable_type(df, "Q1", meta)
    'single-select'
    >>> 
    >>> # With explanation
    >>> ul.detect_variable_type(df, "Q1", meta, explain=True)
    ('single-select', 'PHASE 2: has value labels → single-select')
    >>> 
    >>> # Batch processing with caching
    >>> cache = {}
    >>> for var in df.columns:
    ...     var_type = ul.detect_variable_type(df, var, meta, unique_value_map=cache)
    
    Notes
    -----
    Phase 1 (df-only) possible returns: 'text', 'date', 'categorical', 'numeric'
    Phase 2 (with meta) can refine to: 'single-select', 'multi-select'
    
    Without metadata, coded numeric variables (1, 2, 3, etc.) will be classified
    as 'numeric' since we cannot infer survey semantics from values alone.
    """
    # Convert to narwhals for cross-library compatibility
    df_nw = nw.from_native(df)
    
    # -------------------------------------------------------------------------
    # Phase 1: Pure dtype detection
    # -------------------------------------------------------------------------
    if explain:
        phase1_type, phase1_reason = _detect_from_dtype(var_name, df_nw, explain=True)
    else:
        phase1_type = _detect_from_dtype(var_name, df_nw, explain=False)
        phase1_reason = ""
    
    # -------------------------------------------------------------------------
    # Phase 2: Metadata refinement (if meta provided)
    # -------------------------------------------------------------------------
    if meta is None:
        # No metadata - return Phase 1 result
        return (phase1_type, phase1_reason) if explain else phase1_type
    
    # Initialize mr_set_variables if not provided
    if mr_set_variables is None:
        mr_set_variables = create_mr_set_lookup(meta)
    
    # Refine with metadata
    return _refine_with_metadata(
        var_name=var_name,
        phase1_type=phase1_type,
        phase1_reason=phase1_reason,
        df_nw=df_nw,
        meta=meta,
        mr_set_variables=mr_set_variables,
        unique_value_map=unique_value_map,
        strict_multi=strict_multi,
        explain=explain,
    )
