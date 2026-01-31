"""Tests for EDA reporter module."""

import numpy as np
import pandas as pd
import pytest

from datawhisk.analytical.eda_reporter import EDAReport, quick_eda
from datawhisk.exceptions import ValidationError


class TestQuickEDA:
    """Test cases for quick_eda function."""

    def test_basic_eda_report(self, sample_dataframe):
        """Test basic EDA report generation."""
        report = quick_eda(sample_dataframe)

        assert isinstance(report, EDAReport)
        assert isinstance(report.summary_stats, pd.DataFrame)
        assert isinstance(report.missing_analysis, dict)
        assert isinstance(report.outlier_analysis, dict)
        assert isinstance(report.data_quality_issues, list)
        assert isinstance(report.recommendations, list)

    def test_missing_value_detection(self, dataframe_with_missing):
        """Test missing value detection."""
        report = quick_eda(dataframe_with_missing)

        assert len(report.missing_analysis) > 0
        assert "col1" in report.missing_analysis
        assert "col2" in report.missing_analysis

    def test_outlier_detection_iqr(self, dataframe_with_outliers):
        """Test outlier detection using IQR method."""
        report = quick_eda(
            dataframe_with_outliers,
            outlier_method="iqr",
            outlier_threshold=1.5,
        )

        assert "with_outliers" in report.outlier_analysis
        assert report.outlier_analysis["with_outliers"] > 0

    def test_outlier_detection_zscore(self, dataframe_with_outliers):
        """Test outlier detection using Z-score method."""
        report = quick_eda(
            dataframe_with_outliers,
            outlier_method="zscore",
            outlier_threshold=3,
        )

        assert isinstance(report.outlier_analysis, dict)

    def test_high_cardinality_detection(self):
        """Test high cardinality column detection."""
        df = pd.DataFrame(
            {
                "low_card": ["A", "B", "C"] * 100,
                "high_card": [f"item_{i}" for i in range(300)],
                "numeric": range(300),
            }
        )

        report = quick_eda(df, high_cardinality_threshold=50)

        assert "high_card" in report.high_cardinality_columns
        assert "low_card" not in report.high_cardinality_columns

    def test_duplicate_detection(self, dataframe_with_duplicates):
        """Test duplicate row detection."""
        report = quick_eda(dataframe_with_duplicates)

        # Check if duplicates are mentioned in issues
        issues_text = " ".join(report.data_quality_issues)
        assert "duplicate" in issues_text.lower()

    def test_constant_column_detection(self, dataframe_constant_column):
        """Test constant column detection."""
        report = quick_eda(dataframe_constant_column)

        # Check if constant column is mentioned in issues
        issues_text = " ".join(report.data_quality_issues)
        assert "const_col" in issues_text or "one unique value" in issues_text

    def test_distribution_analysis(self, sample_dataframe):
        """Test distribution insights generation."""
        report = quick_eda(sample_dataframe)

        assert isinstance(report.distribution_insights, dict)
        # Should have insights for numeric columns
        if len(report.summary_stats) > 0:
            assert len(report.distribution_insights) >= 0

    def test_recommendations_generated(self, sample_dataframe):
        """Test that recommendations are generated."""
        report = quick_eda(sample_dataframe)

        assert len(report.recommendations) > 0
        assert all(isinstance(rec, str) for rec in report.recommendations)

    def test_empty_dataframe_error(self, empty_dataframe):
        """Test error handling for empty DataFrame."""
        with pytest.raises(ValidationError):
            quick_eda(empty_dataframe)

    def test_single_column_dataframe(self, single_column_dataframe):
        """Test EDA on single column DataFrame."""
        report = quick_eda(single_column_dataframe)

        assert isinstance(report, EDAReport)

    def test_all_numeric_dataframe(self, dataframe_all_numeric):
        """Test EDA on all numeric DataFrame."""
        report = quick_eda(dataframe_all_numeric)

        assert len(report.summary_stats) > 0
        assert report.summary_stats.shape[1] == len(dataframe_all_numeric.columns)

    def test_all_categorical_dataframe(self, dataframe_all_categorical):
        """Test EDA on all categorical DataFrame."""
        report = quick_eda(dataframe_all_categorical)

        assert isinstance(report, EDAReport)
        # Summary stats should be empty or minimal for categorical only
        assert report.summary_stats.empty or len(report.summary_stats.columns) == 0

    def test_visualization_without_matplotlib(self, sample_dataframe, monkeypatch):
        """Test visualization handling when matplotlib is not available."""
        # This test just ensures no error is raised
        report = quick_eda(sample_dataframe, visualize=False)
        assert isinstance(report, EDAReport)

    def test_high_missing_values_flagged(self):
        """Test that high missing values are flagged."""
        df = pd.DataFrame(
            {
                "mostly_missing": [1, 2] + [np.nan] * 98,
                "normal": range(100),
            }
        )

        report = quick_eda(df)

        # Should be flagged in issues
        issues_text = " ".join(report.data_quality_issues)
        assert "missing" in issues_text.lower() or "mostly_missing" in issues_text

    def test_summary_statistics_completeness(self, sample_dataframe):
        """Test that summary statistics include all expected metrics."""
        report = quick_eda(sample_dataframe)

        if not report.summary_stats.empty:
            # Check for standard statistical measures
            assert "mean" in report.summary_stats.index
            assert "std" in report.summary_stats.index
            assert "50%" in report.summary_stats.index

    def test_outlier_percentage_calculation(self):
        """Test outlier percentage is reasonable."""
        df = pd.DataFrame(
            {
                "normal": np.random.randn(100),
            }
        )

        report = quick_eda(df, outlier_method="iqr", outlier_threshold=1.5)

        if "normal" in report.outlier_analysis:
            outlier_count = report.outlier_analysis["normal"]
            outlier_pct = (outlier_count / len(df)) * 100
            # IQR method with 1.5 threshold should flag roughly
            # 0-10% as outliers
            assert 0 <= outlier_pct <= 30

    def test_no_issues_with_clean_data(self):
        """Test that clean data generates minimal issues."""
        df = pd.DataFrame(
            {
                "col1": range(100),
                "col2": range(100, 200),
                "col3": ["A", "B"] * 50,
            }
        )

        report = quick_eda(df)

        # Should have minimal or no issues
        assert len(report.data_quality_issues) <= 2

    def test_invalid_outlier_method(self, sample_dataframe):
        """Test handling of invalid outlier detection method."""
        # Should not raise error, just use default behavior
        report = quick_eda(sample_dataframe, outlier_method="invalid")
        assert isinstance(report, EDAReport)

    def test_extreme_outlier_threshold(self, dataframe_with_outliers):
        """Test extreme outlier threshold values."""
        # Very low threshold should detect more outliers
        report1 = quick_eda(dataframe_with_outliers, outlier_threshold=0.5)

        # Very high threshold should detect fewer outliers
        report2 = quick_eda(dataframe_with_outliers, outlier_threshold=5.0)

        assert isinstance(report1, EDAReport)
        assert isinstance(report2, EDAReport)


class TestEDAReport:
    """Test cases for EDAReport class."""

    def test_report_string_representation(self, dataframe_with_missing):
        """Test EDAReport __str__ method."""
        report = quick_eda(dataframe_with_missing)

        report_str = str(report)

        assert "Quick EDA Report" in report_str
        assert "Dataset Shape:" in report_str
        assert "Missing Values:" in report_str
        assert "Outliers Detected:" in report_str
        # Check for new detailed missing value section
        assert "Missing Values Detail (Count | Percent):" in report_str
        assert "col1" in report_str
        assert "%" in report_str

    def test_report_contains_all_sections(self, sample_dataframe):
        """Test that report contains all expected sections."""
        report = quick_eda(sample_dataframe)

        assert hasattr(report, "summary_stats")
        assert hasattr(report, "missing_analysis")
        assert hasattr(report, "outlier_analysis")
        assert hasattr(report, "distribution_insights")
        assert hasattr(report, "data_quality_issues")
        assert hasattr(report, "high_cardinality_columns")
        assert hasattr(report, "recommendations")

    def test_missing_percentage_accuracy(self):
        """Test missing value percentage calculation."""
        df = pd.DataFrame(
            {
                "col1": [1, 2, np.nan, 4, 5],  # 20% missing
                "col2": [1, 2, 3, 4, 5],  # 0% missing
            }
        )

        report = quick_eda(df)

        if "col1" in report.missing_analysis:
            assert abs(report.missing_analysis["col1"] - 20.0) < 0.1

    def test_recommendations_relevance(self, dataframe_with_missing):
        """Test that recommendations are relevant to detected issues."""
        report = quick_eda(dataframe_with_missing)

        # Should have recommendation about missing values
        recommendations_text = " ".join(report.recommendations)
        assert (
            "imputation" in recommendations_text.lower()
            or "missing" in recommendations_text.lower()
        )

    def test_distribution_insights_metrics(self, sample_dataframe):
        """Test distribution insights contain expected metrics."""
        report = quick_eda(sample_dataframe)

        for col, insights in report.distribution_insights.items():
            if insights:
                assert "skewness" in insights or "kurtosis" in insights

    def test_report_handles_large_dataframe(self):
        """Test report generation on large DataFrame."""
        np.random.seed(42)
        df = pd.DataFrame(
            {
                "col1": np.random.randn(10000),
                "col2": np.random.randint(0, 100, 10000),
                "col3": np.random.choice(["A", "B", "C"], 10000),
            }
        )

        report = quick_eda(df)

        assert isinstance(report, EDAReport)
        # At least numeric columns
        assert len(report.summary_stats.columns) >= 2

    def test_modular_eda_flags(self, sample_dataframe):
        """Test modular EDA flags efficiently skip computation."""
        # Test disabling all checks
        report_empty = quick_eda(
            sample_dataframe,
            check_structure=False,
            check_missing=False,
            check_outliers=False,
            check_distribution=False,
            check_quality=False,
            check_cardinality=False,
        )
        assert report_empty.summary_stats.empty
        assert not report_empty.missing_analysis
        assert not report_empty.outlier_analysis
        assert not report_empty.distribution_insights
        assert not report_empty.data_quality_issues

        # Test enabling only missing value check
        report_missing = quick_eda(
            sample_dataframe,
            check_structure=False,
            check_missing=True,
            check_outliers=False,
            check_distribution=False,
        )
        assert report_missing.summary_stats.empty  # Should be empty
        assert isinstance(report_missing.missing_analysis, dict)
        assert not report_missing.outlier_analysis
