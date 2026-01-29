"""
set_value_labels.py
Apply value labels to dataframe, converting numeric codes to their string labels.

Accepts both pyreadstat metadata objects and ultrasav Metadata class objects.
Works with both pandas and polars DataFrames via narwhals.
"""

from copy import deepcopy
import warnings

import narwhals.stable.v2 as nw
from narwhals.typing import IntoFrameT


def set_value_labels(
    dataframe: IntoFrameT,
    metadata,
    formats_as_category: bool = True,
    formats_as_ordered_category: bool = False
) -> IntoFrameT:
    """
    Apply value labels to dataframe, replacing numeric codes with their string labels.
    
    This function transforms a dataframe by replacing numeric values with their 
    corresponding labels from the metadata. Returns a copy of the dataframe - 
    the original is not modified.
    
    Parameters
    ----------
    dataframe : pandas or polars DataFrame
        The dataframe to apply labels to
    metadata : pyreadstat metadata object or ultrasav Metadata
        Metadata containing value labels. Can be:
        - pyreadstat metadata object from read_sav()
        - ultrasav Metadata class instance
    formats_as_category : bool, default True
        If True, labeled variables are converted to categorical dtype
    formats_as_ordered_category : bool, default False
        If True, labeled variables are converted to ordered categorical/Enum dtype.
        Takes precedence over formats_as_category.
    
    Returns
    -------
    DataFrame
        A copy of the dataframe with values replaced by their labels.
        Same type as input (pandas or polars).
        If no appropriate formats were found, returns an unchanged copy.
    
    Notes
    -----
    - This function uses `value_labels` and `variable_to_label` from metadata
    - `value_labels` contains named sets of value labels
    - `variable_to_label` maps variable names to their label set names
    - For ultrasav Metadata, these are accessed via properties
    
    Examples
    --------
    >>> import ultrasav as ul
    >>> df, meta_raw = ul.read_sav("survey.sav")
    >>> 
    >>> # Using pyreadstat metadata directly
    >>> df_labeled = set_value_labels(df, meta_raw)
    >>> 
    >>> # Using ultrasav Metadata class
    >>> meta = ul.Metadata(meta_raw)
    >>> df_labeled = set_value_labels(df, meta)
    >>> 
    >>> # Without converting to category
    >>> df_labeled = set_value_labels(df, meta, formats_as_category=False)
    >>> 
    >>> # With ordered categories (for ordinal variables)
    >>> df_labeled = set_value_labels(df, meta, formats_as_ordered_category=True)
    """
    
    # Extract value_labels and variable_to_label from metadata
    # Handle both pyreadstat metadata and ultrasav Metadata class
    value_labels = _get_value_labels(metadata)
    variable_to_label = _get_variable_to_label(metadata)
    
    # Convert to narwhals and clone
    df_copy = nw.from_native(dataframe).clone()
    
    if value_labels and variable_to_label:
        for var_name, label_name in variable_to_label.items():
            labels = value_labels.get(label_name)
            if labels:
                labels = deepcopy(labels)
                if var_name in df_copy.columns:
                    # unique does not work for polars Object
                    if not df_copy.implementation.is_pandas() and df_copy[var_name].dtype == nw.Object:
                        unvals = list(set(df_copy[var_name].to_list()))
                    else:
                        unvals = df_copy[var_name].unique()
                    
                    # Add any values not in labels to preserve them
                    for uval in unvals:
                        if uval not in labels:
                            labels[uval] = uval
                    
                    # if all values are null, there will be nothing to replace
                    # However we cannot do replace_strict on null dtype, it raises an error
                    if not df_copy.implementation.is_pandas() and (len(df_copy[var_name]) == df_copy[var_name].null_count()):
                        continue
                    
                    # replace_strict requires that all the values are in the map
                    # polars is very difficult to convince to mix strings and numbers
                    elif not df_copy.implementation.is_pandas() and (
                        df_copy[var_name].dtype == nw.Object or 
                        not all([type(v) == type(list(labels.values())[0]) for v in labels.values() if v is not None])
                    ):
                        temp = [labels[x] for x in df_copy[var_name]]
                        newser = nw.new_series(
                            name=var_name, 
                            values=temp, 
                            dtype=nw.Object, 
                            backend=df_copy.implementation
                        )
                        df_copy = df_copy.with_columns(newser.alias(var_name))
                        if formats_as_category or formats_as_ordered_category:
                            msg = (
                                f"You requested formats_as_category=True or formats_as_ordered_category=True, "
                                f"but it was not possible to cast variable '{var_name}' to category"
                            )
                            warnings.warn(msg, RuntimeWarning)
                            continue
                    
                    # Unknown dtype handling
                    elif not df_copy.implementation.is_pandas() and df_copy[var_name].dtype == nw.Unknown:
                        msg = (
                            f"It was not possible to apply value formats to variable '{var_name}' "
                            f"due to unknown/not supported data type"
                        )
                        warnings.warn(msg, RuntimeWarning)
                        continue
                    
                    else:
                        df_copy = df_copy.with_columns(nw.col(var_name).replace_strict(labels))
                    
                    # Convert to ordered category if requested
                    if formats_as_ordered_category:
                        categories = list(set(labels.values()))
                        original_values = list(labels.keys())
                        original_values.sort()
                        revdict = dict()
                        for orival in original_values:
                            curcat = labels.get(orival)
                            if not revdict.get(curcat):
                                revdict[curcat] = orival
                        categories.sort(key=revdict.get)
                        df_copy = df_copy.with_columns(nw.col(var_name).cast(nw.Enum(categories)))
                    
                    # Convert to category if requested
                    elif formats_as_category:
                        df_copy = df_copy.with_columns(nw.col(var_name).cast(nw.Categorical))
    
    return df_copy.to_native()


def _get_value_labels(metadata) -> dict:
    """
    Extract value_labels from metadata object.
    
    Handles both pyreadstat metadata and ultrasav Metadata class.
    
    Parameters
    ----------
    metadata : pyreadstat metadata or ultrasav Metadata
        The metadata object
        
    Returns
    -------
    dict
        The value_labels dictionary, or empty dict if not found
    """
    # Check if it's ultrasav Metadata class (has the property)
    if hasattr(metadata, 'value_labels'):
        result = metadata.value_labels
        # ultrasav Metadata.value_labels returns a dict (possibly empty)
        return result if result else {}
    
    # Fallback for raw pyreadstat metadata
    return getattr(metadata, 'value_labels', {}) or {}


def _get_variable_to_label(metadata) -> dict:
    """
    Extract variable_to_label from metadata object.
    
    Handles both pyreadstat metadata and ultrasav Metadata class.
    
    Parameters
    ----------
    metadata : pyreadstat metadata or ultrasav Metadata
        The metadata object
        
    Returns
    -------
    dict
        The variable_to_label dictionary, or empty dict if not found
    """
    # Check if it's ultrasav Metadata class (has the property)
    if hasattr(metadata, 'variable_to_label'):
        result = metadata.variable_to_label
        # ultrasav Metadata.variable_to_label returns a dict (possibly empty)
        return result if result else {}
    
    # Fallback for raw pyreadstat metadata
    return getattr(metadata, 'variable_to_label', {}) or {}
