"""Memory optimization utilities for pandas DataFrames."""

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd

from datawhisk.exceptions import OptimizationError
from datawhisk.utils import get_memory_usage, validate_dataframe


@dataclass
class MemoryReport:
    """Report of memory optimization results."""

    original_memory_mb: float
    optimized_memory_mb: float
    reduction_mb: float
    reduction_percent: float
    optimization_details: Dict[str, Dict[str, str]]
    original_dtypes: Dict[str, str]
    optimized_dtypes: Dict[str, str]

    def __str__(self) -> str:
        """Return formatted report string."""
        return (
            f"Memory Optimization Report\n"
            f"{'=' * 50}\n"
            f"Original Memory:   {self.original_memory_mb:.2f} MB\n"
            f"Optimized Memory:  {self.optimized_memory_mb:.2f} MB\n"
            f"Reduction:         {self.reduction_mb:.2f} MB "
            f"({self.reduction_percent:.1f}%)\n"
            f"\nOptimizations Applied: "
            f"{len(self.optimization_details)} columns"
        )


def optimize_memory(
    df: pd.DataFrame,
    categorical_threshold: int = 50,
    return_report: bool = False,
    inplace: bool = False,
    aggressive: bool = False,
) -> Tuple[pd.DataFrame, Optional[MemoryReport]]:
    """
    Optimize DataFrame memory usage through intelligent dtype casting.

    This function automatically downcasts numeric dtypes to their optimal sizes
    and converts object columns to categorical where appropriate.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame to optimize.
    categorical_threshold : int, optional
        Maximum unique value ratio (%) to convert object to category,
        by default 50.
        For example, 50 means convert if unique values are less than
        50% of total rows.
    return_report : bool, optional
        Whether to return a detailed optimization report, by default False.
    inplace : bool, optional
        Whether to modify DataFrame in place, by default False.
    aggressive : bool, optional
        Whether to use aggressive optimization (may lose precision),
        by default False.

    Returns
    -------
    Tuple[pd.DataFrame, Optional[MemoryReport]]
        Optimized DataFrame and optional memory report.

    Raises
    ------
    ValidationError
        If input is not a valid DataFrame.
    OptimizationError
        If optimization fails.

    Examples
    --------
    >>> import pandas as pd
    >>> df = pd.DataFrame({
    ...     'id': range(1000000),
    ...     'category': ['A', 'B', 'C'] * 333334,
    ...     'value': [1.5] * 1000000
    ... })
    >>> optimized_df, report = optimize_memory(df, return_report=True)
    >>> print(f"Memory reduced by {report.reduction_percent:.1f}%")
    Memory reduced by 65.2%

    Notes
    -----
    - Integer columns are downcast to the smallest possible integer type
    - Float columns are downcast to float32 if aggressive=True
    - Object columns with low cardinality are converted to category
    - The function preserves data integrity unless aggressive=True
    """
    # Validate input
    validate_dataframe(df, min_rows=1, min_cols=1)

    # Copy if not inplace
    df_optimized = df if inplace else df.copy()

    # Calculate original memory
    original_memory = get_memory_usage(df)
    original_dtypes = {col: str(dtype) for col, dtype in df.dtypes.items()}

    optimization_details = {}

    try:
        # Optimize integer columns
        int_cols = df_optimized.select_dtypes(include=["int"]).columns
        for col in int_cols:
            original_dtype = df_optimized[col].dtype
            optimized_dtype = _optimize_integer_column(df_optimized, col)
            if optimized_dtype != original_dtype:
                optimization_details[col] = {
                    "original": str(original_dtype),
                    "optimized": str(optimized_dtype),
                    "type": "integer_downcast",
                }

        # Optimize float columns
        float_cols = df_optimized.select_dtypes(include=["float"]).columns
        for col in float_cols:
            original_dtype = df_optimized[col].dtype
            if aggressive and original_dtype == "float64":
                df_optimized[col] = df_optimized[col].astype("float32")
                optimization_details[col] = {
                    "original": "float64",
                    "optimized": "float32",
                    "type": "float_downcast",
                }

        # Optimize object columns to categorical
        object_cols = df_optimized.select_dtypes(include=["object"]).columns
        for col in object_cols:
            unique_ratio = (df_optimized[col].nunique() / len(df_optimized)) * 100
            if unique_ratio <= categorical_threshold:
                df_optimized[col] = df_optimized[col].astype("category")
                optimization_details[col] = {
                    "original": "object",
                    "optimized": "category",
                    "type": "object_to_category",
                    "unique_ratio": f"{unique_ratio:.1f}%",
                }

    except Exception as e:
        raise OptimizationError(f"Memory optimization failed: {str(e)}") from e

    # Calculate optimized memory
    optimized_memory = get_memory_usage(df_optimized)
    reduction_mb = original_memory - optimized_memory
    reduction_percent = (reduction_mb / original_memory * 100) if original_memory > 0 else 0

    optimized_dtypes = {col: str(dtype) for col, dtype in df_optimized.dtypes.items()}

    if return_report:
        report = MemoryReport(
            original_memory_mb=original_memory,
            optimized_memory_mb=optimized_memory,
            reduction_mb=reduction_mb,
            reduction_percent=reduction_percent,
            optimization_details=optimization_details,
            original_dtypes=original_dtypes,
            optimized_dtypes=optimized_dtypes,
        )
        return df_optimized, report

    return df_optimized, None


def _optimize_integer_column(df: pd.DataFrame, col: str) -> np.dtype:
    """
    Optimize a single integer column by downcasting to smallest safe type.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing the column.
    col : str
        Column name to optimize.

    Returns
    -------
    np.dtype
        The optimized dtype.
    """
    col_min = df[col].min()
    col_max = df[col].max()

    # Check if column can be unsigned
    if col_min >= 0:
        if col_max < np.iinfo(np.uint8).max:
            df[col] = df[col].astype(np.uint8)
        elif col_max < np.iinfo(np.uint16).max:
            df[col] = df[col].astype(np.uint16)
        elif col_max < np.iinfo(np.uint32).max:
            df[col] = df[col].astype(np.uint32)
        else:
            df[col] = df[col].astype(np.uint64)
    else:
        # Use signed integers
        if col_min > np.iinfo(np.int8).min and col_max < np.iinfo(np.int8).max:
            df[col] = df[col].astype(np.int8)
        elif col_min > np.iinfo(np.int16).min and col_max < np.iinfo(np.int16).max:
            df[col] = df[col].astype(np.int16)
        elif col_min > np.iinfo(np.int32).min and col_max < np.iinfo(np.int32).max:
            df[col] = df[col].astype(np.int32)
        else:
            df[col] = df[col].astype(np.int64)

    return df[col].dtype  # type: ignore


def undo_optimization(df: pd.DataFrame, original_dtypes: Dict[str, str]) -> pd.DataFrame:
    """
    Revert DataFrame to original dtypes after optimization.

    Parameters
    ----------
    df : pd.DataFrame
        Optimized DataFrame.
    original_dtypes : Dict[str, str]
        Dictionary of original column dtypes.

    Returns
    -------
    pd.DataFrame
        DataFrame with original dtypes restored.

    Examples
    --------
    >>> optimized_df, report = optimize_memory(df, return_report=True)
    >>> original_df = undo_optimization(optimized_df, report.original_dtypes)
    """
    df_restored = df.copy()

    for col, dtype in original_dtypes.items():
        if col in df_restored.columns:
            df_restored[col] = df_restored[col].astype(dtype)

    return df_restored
