"""Utility functions shared across datawhisk modules."""

from typing import Union

import numpy as np
import pandas as pd

from datawhisk.exceptions import ValidationError


def validate_dataframe(
    df: pd.DataFrame,
    min_rows: int = 1,
    min_cols: int = 1,
    require_numeric: bool = False,
    param_name: str = "df",
) -> None:
    """
    Validate that input is a proper DataFrame with expected characteristics.

    Parameters
    ----------
    df : pd.DataFrame
        The DataFrame to validate.
    min_rows : int, optional
        Minimum number of rows required, by default 1.
    min_cols : int, optional
        Minimum number of columns required, by default 1.
    require_numeric : bool, optional
        Whether to require at least one numeric column, by default False.
    param_name : str, optional
        Parameter name for error messages, by default "df".

    Raises
    ------
    ValidationError
        If validation fails.
    """
    if not isinstance(df, pd.DataFrame):
        raise ValidationError(f"{param_name} must be a pandas DataFrame, got {type(df)}")

    if len(df) < min_rows:
        raise ValidationError(f"{param_name} must have at least {min_rows} rows, " f"got {len(df)}")

    if len(df.columns) < min_cols:
        raise ValidationError(
            f"{param_name} must have at least {min_cols} columns, " f"got {len(df.columns)}"
        )

    if require_numeric:
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) == 0:
            raise ValidationError(f"{param_name} must contain at least one numeric column")


def get_memory_usage(df: pd.DataFrame, deep: bool = True) -> float:
    """
    Calculate total memory usage of a DataFrame in megabytes.

    Parameters
    ----------
    df : pd.DataFrame
        The DataFrame to measure.
    deep : bool, optional
        Whether to introspect object dtypes, by default True.

    Returns
    -------
    float
        Memory usage in megabytes.
    """
    memory_bytes: float = df.memory_usage(deep=deep).sum()
    return float(memory_bytes / 1024**2)


def get_numeric_columns(df: pd.DataFrame) -> pd.Index:
    """
    Get all numeric columns from a DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame.

    Returns
    -------
    pd.Index
        Index of numeric column names.
    """
    return df.select_dtypes(include=[np.number]).columns


def get_categorical_columns(df: pd.DataFrame) -> pd.Index:
    """
    Get all categorical/object columns from a DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame.

    Returns
    -------
    pd.Index
        Index of categorical/object column names.
    """
    return df.select_dtypes(include=["object", "category"]).columns


def safe_divide(numerator: Union[float, int], denominator: Union[float, int]) -> float:
    """
    Safely divide two numbers, returning 0 if denominator is 0.

    Parameters
    ----------
    numerator : float or int
        The numerator.
    denominator : float or int
        The denominator.

    Returns
    -------
    float
        The result of division, or 0 if denominator is 0.
    """
    if denominator == 0:
        return 0.0
    return numerator / denominator


def format_bytes(bytes_value: float) -> str:
    """
    Format bytes into human-readable string.

    Parameters
    ----------
    bytes_value : float
        Size in bytes.

    Returns
    -------
    str
        Formatted string (e.g., "1.5 MB", "256.3 KB").
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} PB"


def check_column_exists(df: pd.DataFrame, column: str, param_name: str = "column") -> None:
    """
    Check if a column exists in the DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        The DataFrame to check.
    column : str
        Column name to verify.
    param_name : str, optional
        Parameter name for error messages, by default "column".

    Raises
    ------
    ValidationError
        If column doesn't exist.
    """
    if column not in df.columns:
        raise ValidationError(
            f"{param_name} '{column}' not found in DataFrame. "
            f"Available columns: {list(df.columns)}"
        )
