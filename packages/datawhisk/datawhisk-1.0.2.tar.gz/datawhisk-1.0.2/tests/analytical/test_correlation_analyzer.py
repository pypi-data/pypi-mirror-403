"""Tests for correlation analyzer module."""

import numpy as np
import pandas as pd
import pytest

from datawhisk.analytical.correlation_analyzer import (
    CorrelationResults,
    analyze_correlations,
)
from datawhisk.exceptions import AnalysisError, ValidationError


class TestAnalyzeCorrelations:
    """Test cases for analyze_correlations function."""

    def test_basic_correlation_analysis(self, correlated_dataframe):
        """Test basic correlation analysis."""
        results = analyze_correlations(correlated_dataframe)

        assert isinstance(results, CorrelationResults)
        assert isinstance(results.correlation_matrix, pd.DataFrame)
        assert len(results.correlation_matrix) > 0

    def test_correlation_with_target(self, correlated_dataframe):
        """Test correlation analysis with target variable."""
        results = analyze_correlations(correlated_dataframe, target="target", threshold=0.9)

        assert results.target == "target"
        assert "target" not in results.correlation_matrix.columns

    def test_high_correlation_detection(self, correlated_dataframe):
        """Test detection of high correlations."""
        results = analyze_correlations(correlated_dataframe, threshold=0.8)

        assert len(results.high_correlations) > 0
        # feature1 and feature2 should be highly correlated
        corr_pairs = [(pair[0], pair[1]) for pair in results.high_correlations]
        assert ("feature1", "feature2") in corr_pairs or ("feature2", "feature1") in corr_pairs

    def test_vif_calculation(self, dataframe_all_numeric):
        """Test VIF score calculation."""
        results = analyze_correlations(dataframe_all_numeric, calculate_vif=True)

        assert results.vif_scores is not None
        assert isinstance(results.vif_scores, pd.DataFrame)
        assert "feature" in results.vif_scores.columns
        assert "VIF" in results.vif_scores.columns

    def test_vif_disabled(self, dataframe_all_numeric):
        """Test when VIF calculation is disabled."""
        results = analyze_correlations(dataframe_all_numeric, calculate_vif=False)

        assert results.vif_scores is None

    def test_pearson_method(self, dataframe_all_numeric):
        """Test Pearson correlation method."""
        results = analyze_correlations(dataframe_all_numeric, method="pearson")

        assert results.method == "pearson"
        assert results.correlation_matrix is not None

    def test_spearman_method(self, dataframe_all_numeric):
        """Test Spearman correlation method."""
        results = analyze_correlations(dataframe_all_numeric, method="spearman")

        assert results.method == "spearman"
        assert results.correlation_matrix is not None

    def test_kendall_method(self, dataframe_all_numeric):
        """Test Kendall correlation method."""
        results = analyze_correlations(dataframe_all_numeric, method="kendall")

        assert results.method == "kendall"
        assert results.correlation_matrix is not None

    def test_invalid_method(self, dataframe_all_numeric):
        """Test error handling for invalid correlation method."""
        with pytest.raises(ValidationError):
            analyze_correlations(dataframe_all_numeric, method="invalid_method")

    def test_invalid_threshold(self, dataframe_all_numeric):
        """Test error handling for invalid threshold."""
        with pytest.raises(ValidationError):
            analyze_correlations(dataframe_all_numeric, threshold=1.5)

        with pytest.raises(ValidationError):
            analyze_correlations(dataframe_all_numeric, threshold=-0.1)

    def test_recommendations_generated(self, correlated_dataframe):
        """Test that recommendations are generated."""
        results = analyze_correlations(
            correlated_dataframe,
            target="target",
            threshold=0.8,
            return_details=True,
        )

        assert len(results.recommendations) > 0
        assert isinstance(results.recommendations[0], str)

    def test_no_recommendations_when_disabled(self, dataframe_all_numeric):
        """Test no recommendations when return_details=False."""
        results = analyze_correlations(dataframe_all_numeric, return_details=False)

        assert len(results.recommendations) == 0

    def test_variance_threshold_filtering(self):
        """Test low-variance features are filtered."""
        df = pd.DataFrame(
            {
                "low_var": [1, 1, 1, 1, 1],
                "normal_var": [1, 2, 3, 4, 5],
                "high_var": [1, 10, 20, 30, 40],
            }
        )

        results = analyze_correlations(df, variance_threshold=0.5)

        # low_var should be filtered out
        assert "low_var" not in results.correlation_matrix.columns

    def test_insufficient_features_error(self):
        """Test error when too few features remain after filtering."""
        df = pd.DataFrame(
            {
                "const1": [1] * 100,
                "const2": [2] * 100,
            }
        )

        with pytest.raises(AnalysisError):
            analyze_correlations(df, variance_threshold=0.01)

    def test_non_numeric_columns_ignored(self):
        """Test that non-numeric columns are ignored."""
        df = pd.DataFrame(
            {
                "num1": range(100),
                "num2": range(100, 200),
                "cat": ["A", "B"] * 50,
                "text": ["text"] * 100,
            }
        )

        results = analyze_correlations(df)

        assert "cat" not in results.correlation_matrix.columns
        assert "text" not in results.correlation_matrix.columns

    def test_minimum_rows_requirement(self):
        """Test that minimum rows requirement is enforced."""
        df = pd.DataFrame(
            {
                "col1": [1, 2],
                "col2": [3, 4],
            }
        )

        with pytest.raises(ValidationError):
            analyze_correlations(df)

    def test_invalid_target_column(self, dataframe_all_numeric):
        """Test error when target column doesn't exist."""
        with pytest.raises(ValidationError):
            analyze_correlations(dataframe_all_numeric, target="nonexistent_column")

    def test_all_categorical_dataframe_error(self, dataframe_all_categorical):
        """Test error when DataFrame has no numeric columns."""
        with pytest.raises(ValidationError):
            analyze_correlations(dataframe_all_categorical)


class TestCorrelationResults:
    """Test cases for CorrelationResults class."""

    def test_results_string_representation(self, correlated_dataframe):
        """Test CorrelationResults __str__ method."""
        results = analyze_correlations(correlated_dataframe, target="target")

        results_str = str(results)

        assert "Correlation Analysis Results" in results_str
        assert "Method:" in results_str
        assert "Features analyzed:" in results_str
        assert "target" in results_str

    def test_results_contain_all_attributes(self, dataframe_all_numeric):
        """Test that results contain all expected attributes."""
        results = analyze_correlations(dataframe_all_numeric)

        assert hasattr(results, "correlation_matrix")
        assert hasattr(results, "vif_scores")
        assert hasattr(results, "high_correlations")
        assert hasattr(results, "recommendations")
        assert hasattr(results, "method")
        assert hasattr(results, "target")

    def test_high_correlations_format(self, correlated_dataframe):
        """Test high_correlations are in correct format."""
        results = analyze_correlations(correlated_dataframe, threshold=0.8)

        if len(results.high_correlations) > 0:
            for item in results.high_correlations:
                assert len(item) == 3  # (feat1, feat2, correlation)
                assert isinstance(item[0], str)
                assert isinstance(item[1], str)
                assert isinstance(item[2], (int, float))

    def test_correlation_matrix_symmetric(self, dataframe_all_numeric):
        """Test that correlation matrix is symmetric."""
        results = analyze_correlations(dataframe_all_numeric)

        corr_matrix = results.correlation_matrix
        assert np.allclose(corr_matrix, corr_matrix.T, atol=1e-10)

    def test_vif_scores_sorted(self, dataframe_all_numeric):
        """Test that VIF scores are sorted in descending order."""
        results = analyze_correlations(dataframe_all_numeric, calculate_vif=True)

        if results.vif_scores is not None and len(results.vif_scores) > 1:
            vif_values = results.vif_scores["VIF"].values
            # Check if sorted (allowing for inf values)
            finite_vifs = vif_values[np.isfinite(vif_values)]
            if len(finite_vifs) > 1:
                assert all(
                    finite_vifs[i] >= finite_vifs[i + 1] for i in range(len(finite_vifs) - 1)
                )
