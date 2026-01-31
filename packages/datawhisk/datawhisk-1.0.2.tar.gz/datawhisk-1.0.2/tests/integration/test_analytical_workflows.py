"""Integration tests for analytical workflows."""

import numpy as np
import pandas as pd
import pytest

from datawhisk.analytical import (
    analyze_correlations,
    optimize_memory,
    quick_eda,
)


class TestAnalyticalWorkflow:
    """Test complete analytical workflows."""

    def test_complete_data_analysis_pipeline(self):
        """Test complete data analysis pipeline."""
        # Create sample dataset
        np.random.seed(42)
        df = pd.DataFrame(
            {
                "id": range(10000),
                "feature1": np.random.randn(10000),
                "feature2": np.random.randn(10000) * 100,
                "feature3": np.random.choice(["A", "B", "C"], 10000),
                "target": np.random.randn(10000),
            }
        )

        # Step 1: Optimize memory
        df_optimized, mem_report = optimize_memory(df, return_report=True)
        assert mem_report is not None
        assert mem_report.reduction_percent > 0

        # Step 2: Quick EDA
        eda_report = quick_eda(df_optimized)
        assert len(eda_report.recommendations) > 0

        # Step 3: Correlation analysis
        corr_results = analyze_correlations(df_optimized, target="target", threshold=0.7)
        assert corr_results.correlation_matrix is not None

    def test_memory_optimization_before_eda(self):
        """Test that memory optimization works before EDA."""
        np.random.seed(42)
        df = pd.DataFrame(
            {
                "large_int": range(100000),
                "float_val": np.random.randn(100000),
                "category": np.random.choice(["A", "B", "C"], 100000),
            }
        )

        # Optimize first
        df_optimized, _ = optimize_memory(df)

        # Then run EDA
        report = quick_eda(df_optimized)

        assert isinstance(report.summary_stats, pd.DataFrame)
        assert len(report.recommendations) >= 0

    def test_correlation_after_eda(self):
        """Test correlation analysis after EDA."""
        np.random.seed(42)
        x1 = np.random.randn(1000)
        x2 = x1 + np.random.randn(1000) * 0.1
        x3 = np.random.randn(1000)

        df = pd.DataFrame(
            {
                "feature1": x1,
                "feature2": x2,
                "feature3": x3,
                "target": 2 * x1 + x3,
            }
        )

        # Generate EDA report
        _ = quick_eda(df)

        # Then correlation analysis
        corr_results = analyze_correlations(df, target="target")

        # Should detect high correlation between feature1 and feature2
        assert len(corr_results.high_correlations) > 0

    def test_chained_operations_preserve_data(self):
        """Test that chained operations preserve data integrity."""
        np.random.seed(42)
        original_df = pd.DataFrame(
            {
                "col1": range(1000),
                "col2": np.random.randn(1000),
                "col3": ["A", "B"] * 500,
            }
        )

        # Chain operations
        df_step1, _ = optimize_memory(original_df)
        _ = quick_eda(df_step1)

        # Check data integrity (values should be same, dtypes may differ)
        assert len(df_step1) == len(original_df)
        assert list(df_step1.columns) == list(original_df.columns)
        # Verify data integrity
        np.testing.assert_array_equal(df_step1["col1"].to_numpy(), original_df["col1"].to_numpy())

    def test_feature_selection_workflow(self):
        """Test complete feature selection workflow."""
        np.random.seed(42)
        # Create dataset with redundant features
        x1 = np.random.randn(500)
        x2 = x1 + np.random.randn(500) * 0.05  # Highly correlated with x1
        x3 = np.random.randn(500)
        x4 = x3 + np.random.randn(500) * 0.05  # Highly correlated with x3
        x5 = np.random.randn(500)

        df = pd.DataFrame(
            {
                "feature1": x1,
                "feature2": x2,
                "feature3": x3,
                "feature4": x4,
                "feature5": x5,
                "target": 2 * x1 + 3 * x3 + x5,
            }
        )

        # Run correlation analysis
        corr_results = analyze_correlations(df, target="target", threshold=0.8)

        # Should have recommendations to remove correlated features
        assert len(corr_results.recommendations) > 0
        assert len(corr_results.high_correlations) > 0

    def test_data_quality_pipeline(self):
        """Test data quality assessment pipeline."""
        np.random.seed(42)
        # Create dataset with quality issues
        df = pd.DataFrame(
            {
                "col1": list(range(100)) + [np.nan] * 120,
                # >50% missing (220 rows)
                "col2": [1, 2, 3, 4] * 55,  # Low variance
                "col3": np.concatenate(
                    [np.random.randn(215), [100, 100, 100, 100, 100]]
                ),  # Outliers
                "col4": ["item_" + str(i) for i in range(220)],  # High cardinality
            }
        )

        # Run EDA to detect issues
        report = quick_eda(df)

        # Should detect multiple issues
        assert len(report.data_quality_issues) > 0
        assert len(report.missing_analysis) > 0
        assert len(report.high_cardinality_columns) > 0

    def test_optimization_and_analysis_combined(self):
        """Test memory optimization combined with analysis."""
        np.random.seed(42)
        df = pd.DataFrame(
            {
                "large_id": range(50000),
                "small_category": np.random.choice(["A", "B", "C"], 50000),
                "numeric_feature": np.random.randn(50000),
                "target": np.random.randn(50000),
            }
        )
        # Track memory before optimization
        _ = df.memory_usage(deep=True).sum()

        # Optimize and analyze
        df_opt, mem_report = optimize_memory(df, return_report=True)
        corr_results = analyze_correlations(df_opt, target="target")
        eda_report = quick_eda(df_opt)

        # Verify all operations succeeded
        assert mem_report is not None
        assert mem_report.optimized_memory_mb < mem_report.original_memory_mb
        assert corr_results.correlation_matrix is not None
        assert len(eda_report.recommendations) >= 0

    def test_workflow_with_missing_data(self):
        """Test workflow handles missing data gracefully."""
        np.random.seed(42)
        df = pd.DataFrame(
            {
                "col1": np.random.randn(1000),
                "col2": np.random.randn(1000),
                "col3": np.random.randn(1000),
            }
        )
        # Add missing values
        df.loc[np.random.choice(df.index, 100, replace=False), "col1"] = np.nan
        df.loc[np.random.choice(df.index, 200, replace=False), "col2"] = np.nan

        # All operations should handle missing data
        df_opt, _ = optimize_memory(df)
        eda_report = quick_eda(df_opt)
        corr_results = analyze_correlations(df_opt)

        assert "col1" in eda_report.missing_analysis
        assert "col2" in eda_report.missing_analysis
        assert corr_results.correlation_matrix is not None

    def test_workflow_reproducibility(self):
        """Test that workflow produces consistent results."""
        np.random.seed(42)
        df = pd.DataFrame(
            {
                "col1": np.random.randn(1000),
                "col2": np.random.randn(1000),
                "col3": ["A", "B", "C"] * 333 + ["A"],
            }
        )

        # Run workflow twice
        df1_opt, report1 = optimize_memory(df.copy(), return_report=True)
        eda1 = quick_eda(df1_opt)

        df2_opt, report2 = optimize_memory(df.copy(), return_report=True)
        eda2 = quick_eda(df2_opt)

        # Results should be identical
        assert report1 is not None and report2 is not None
        # Reduction percentages should be very close
        assert abs(report1.reduction_percent - report2.reduction_percent) < 0.01
        assert len(eda1.recommendations) == len(eda2.recommendations)

    def test_large_scale_workflow(self):
        """Test workflow on larger dataset."""
        np.random.seed(42)
        df = pd.DataFrame(
            {
                "id": range(100000),
                "feature1": np.random.randn(100000),
                "feature2": np.random.randn(100000),
                "feature3": np.random.randn(100000),
                "category": np.random.choice(["A", "B", "C", "D"], 100000),
                "target": np.random.randn(100000),
            }
        )

        # Full workflow
        df_opt, mem_report = optimize_memory(df, return_report=True)
        eda_report = quick_eda(df_opt)
        corr_results = analyze_correlations(df_opt, target="target")

        # All should complete successfully
        assert mem_report is not None
        assert mem_report.reduction_percent > 0
        assert isinstance(eda_report.summary_stats, pd.DataFrame)
        assert corr_results.correlation_matrix is not None

    def test_workflow_error_recovery(self):
        """Test workflow handles errors in individual steps."""
        # Create problematic dataset
        df = pd.DataFrame(
            {
                "const1": [1] * 100,
                "const2": [2] * 100,
                "const3": [3] * 100,
            }
        )

        # Optimization should work
        df_opt, _ = optimize_memory(df)
        assert df_opt is not None

        # EDA should work
        eda_report = quick_eda(df_opt)
        assert eda_report is not None

        # Correlation might fail due to no variance
        with pytest.raises(Exception):
            analyze_correlations(df_opt)
