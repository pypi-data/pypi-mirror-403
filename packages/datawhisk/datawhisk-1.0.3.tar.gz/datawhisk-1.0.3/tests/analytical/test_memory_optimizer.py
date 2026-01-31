"""Tests for memory optimizer module."""

import numpy as np
import pandas as pd
import pytest

from datawhisk.analytical.memory_optimizer import (
    MemoryReport,
    optimize_memory,
    undo_optimization,
)
from datawhisk.exceptions import ValidationError


class TestOptimizeMemory:
    """Test cases for optimize_memory function."""

    def test_basic_optimization(self, large_dataframe):
        """Test basic memory optimization."""
        df = large_dataframe.copy()
        original_memory = df.memory_usage(deep=True).sum()

        optimized_df, _ = optimize_memory(df)
        optimized_memory = optimized_df.memory_usage(deep=True).sum()

        assert optimized_memory < original_memory
        assert len(optimized_df) == len(df)
        assert list(optimized_df.columns) == list(df.columns)

    def test_optimization_with_report(self, large_dataframe):
        """Test optimization returns proper report."""
        df = large_dataframe.copy()

        optimized_df, report = optimize_memory(df, return_report=True)

        assert isinstance(report, MemoryReport)
        assert report.original_memory_mb > 0
        assert report.optimized_memory_mb > 0
        assert report.reduction_mb >= 0
        assert report.reduction_percent >= 0
        assert isinstance(report.optimization_details, dict)

    def test_integer_downcast(self):
        """Test integer columns are downcast appropriately."""
        df = pd.DataFrame(
            {
                "small": [1, 2, 3, 4, 5],  # Should become int8
                "medium": [100, 200, 300, 400, 500],  # Should become int16
                "large": [10000, 20000, 30000, 40000, 50000],  # Should become int32
            }
        )

        optimized_df, report = optimize_memory(df, return_report=True)

        assert optimized_df["small"].dtype in [np.int8, np.uint8]
        assert optimized_df["medium"].dtype in [np.int16, np.uint16]
        assert report is not None
        assert len(report.optimization_details) > 0

    def test_categorical_conversion(self):
        """Test object columns converted to categorical."""
        df = pd.DataFrame(
            {
                "low_cardinality": ["A", "B", "C"] * 100,
                "high_cardinality": [f"item_{i}" for i in range(300)],
            }
        )

        optimized_df, report = optimize_memory(df, categorical_threshold=50, return_report=True)

        assert optimized_df["low_cardinality"].dtype.name == "category"
        assert optimized_df["high_cardinality"].dtype == "object"

    def test_aggressive_mode(self):
        """Test aggressive mode downcasts floats."""
        df = pd.DataFrame(
            {
                "float_col": np.random.randn(100).astype("float64"),
            }
        )

        optimized_df, _ = optimize_memory(df, aggressive=True)

        assert optimized_df["float_col"].dtype == np.float32

    def test_inplace_modification(self):
        """Test inplace parameter modifies original DataFrame."""
        df = pd.DataFrame(
            {
                "col": range(1000000),
            }
        )
        df_id = id(df)

        result_df, _ = optimize_memory(df, inplace=True)

        assert id(result_df) == df_id
        assert result_df["col"].dtype != np.int64

    def test_empty_dataframe(self, empty_dataframe):
        """Test handling of empty DataFrame."""
        with pytest.raises(ValidationError):
            optimize_memory(empty_dataframe)

    def test_invalid_input(self):
        """Test error handling for invalid input."""
        with pytest.raises(ValidationError):
            optimize_memory("not a dataframe")  # type: ignore

        with pytest.raises(ValidationError):
            optimize_memory([1, 2, 3])  # type: ignore

    def test_memory_reduction_calculation(self):
        """Test memory reduction percentage is calculated correctly."""
        df = pd.DataFrame(
            {
                "int_col": range(100000),
            }
        )

        _, report = optimize_memory(df, return_report=True)

        assert report is not None
        expected_reduction = (
            (report.original_memory_mb - report.optimized_memory_mb)
            / report.original_memory_mb
            * 100
        )
        assert abs(report.reduction_percent - expected_reduction) < 0.01

    def test_data_integrity(self):
        """Test that data values are preserved after optimization."""
        df = pd.DataFrame(
            {
                "int_col": [1, 2, 3, 4, 5],
                "float_col": [1.1, 2.2, 3.3, 4.4, 5.5],
                "cat_col": ["A", "B", "C", "A", "B"],
            }
        )

        optimized_df, _ = optimize_memory(df)

        # Convert optimized columns back to original dtypes for comparison
        original_dtypes_dict = {col: df[col].dtype for col in ["int_col", "cat_col"]}
        pd.testing.assert_frame_equal(
            df[["int_col", "cat_col"]],
            optimized_df[["int_col", "cat_col"]].astype(original_dtypes_dict),  # type: ignore
        )

    def test_unsigned_integers(self):
        """Test unsigned integers are used for non-negative values."""
        df = pd.DataFrame(
            {
                "positive_only": [0, 1, 2, 3, 4],
            }
        )

        optimized_df, _ = optimize_memory(df)

        assert "uint" in str(optimized_df["positive_only"].dtype)

    def test_signed_integers(self):
        """Test signed integers are used for negative values."""
        df = pd.DataFrame(
            {
                "with_negatives": [-5, -4, -3, 0, 1, 2, 3, 4, 5],
            }
        )

        optimized_df, _ = optimize_memory(df)

        assert "int" in str(optimized_df["with_negatives"].dtype)
        assert "uint" not in str(optimized_df["with_negatives"].dtype)


class TestUndoOptimization:
    """Test cases for undo_optimization function."""

    def test_undo_restores_original_dtypes(self):
        """Test undo_optimization restores original dtypes."""
        df = pd.DataFrame(
            {
                "int_col": range(100),
                "float_col": np.random.randn(100),
                "cat_col": ["A", "B", "C"] * 33 + ["A"],
            }
        )
        original_dtypes = {col: str(dtype) for col, dtype in df.dtypes.items()}

        optimized_df, report = optimize_memory(df, return_report=True)
        assert report is not None
        restored_df = undo_optimization(optimized_df, report.original_dtypes)

        for col in df.columns:
            assert str(restored_df[col].dtype) == original_dtypes[col]

    def test_undo_preserves_data(self):
        """Test undo_optimization preserves data values."""
        df = pd.DataFrame(
            {
                "col1": [1, 2, 3, 4, 5],
                "col2": ["A", "B", "C", "D", "E"],
            }
        )

        optimized_df, report = optimize_memory(df, return_report=True)
        assert report is not None
        restored_df = undo_optimization(optimized_df, report.original_dtypes)

        pd.testing.assert_frame_equal(df, restored_df)


class TestMemoryReport:
    """Test cases for MemoryReport class."""

    def test_report_string_representation(self):
        """Test MemoryReport __str__ method."""
        report = MemoryReport(
            original_memory_mb=100.0,
            optimized_memory_mb=50.0,
            reduction_mb=50.0,
            reduction_percent=50.0,
            optimization_details={"col1": {"original": "int64", "optimized": "int8"}},
            original_dtypes={"col1": "int64"},
            optimized_dtypes={"col1": "int8"},
        )

        report_str = str(report)

        assert "100.00 MB" in report_str
        assert "50.00 MB" in report_str
        assert "50.0%" in report_str

    def test_report_contains_details(self, large_dataframe):
        """Test report contains optimization details."""
        _, report = optimize_memory(large_dataframe, return_report=True)

        assert report is not None
        assert len(report.optimization_details) > 0
        assert len(report.original_dtypes) == len(large_dataframe.columns)
        assert len(report.optimized_dtypes) == len(large_dataframe.columns)
