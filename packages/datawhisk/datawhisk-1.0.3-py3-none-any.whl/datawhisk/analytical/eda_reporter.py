"""Quick exploratory data analysis reporter."""

from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from scipy import stats

from datawhisk.exceptions import AnalysisError
from datawhisk.utils import (
    get_categorical_columns,
    get_numeric_columns,
    validate_dataframe,
)


@dataclass
class EDAReport:
    """Comprehensive EDA report."""

    summary_stats: pd.DataFrame
    missing_analysis: Dict[str, float]
    missing_counts: Dict[str, int]
    outlier_analysis: Dict[str, int]
    distribution_insights: Dict[str, Dict[str, float]]
    data_quality_issues: List[str]
    high_cardinality_columns: List[str]
    recommendations: List[str]

    def __str__(self) -> str:
        """Return formatted report string."""
        output = [
            "Quick EDA Report",
            "=" * 60,
            f"\nDataset Shape: {self.summary_stats.shape}",
            f"Missing Values: {sum(self.missing_counts.values())} "
            f"({sum(self.missing_analysis.values()):.1f}%)",
            f"Outliers Detected: {sum(self.outlier_analysis.values())} " f"total",
            f"Data Quality Issues: {len(self.data_quality_issues)}",
        ]

        if self.missing_analysis:
            output.append("\nMissing Values Detail (Count | Percent):")
            for col, pct in self.missing_analysis.items():
                count = self.missing_counts[col]
                output.append(f"  - {col}: {count} ({pct:.1f}%)")

        if self.high_cardinality_columns:
            output.append(f"\nHigh Cardinality Columns: " f"{len(self.high_cardinality_columns)}")
            for col in self.high_cardinality_columns[:3]:
                output.append(f"  - {col}")

        if self.data_quality_issues:
            output.append("\nData Quality Issues:")
            for issue in self.data_quality_issues[:5]:
                output.append(f"  ⚠ {issue}")

        if self.recommendations:
            output.append("\nRecommendations:")
            for rec in self.recommendations[:5]:
                output.append(f"  → {rec}")

        return "\n".join(output)


def quick_eda(
    df: pd.DataFrame,
    visualize: bool = False,
    outlier_method: str = "iqr",
    outlier_threshold: float = 1.5,
    high_cardinality_threshold: int = 50,
    check_structure: bool = True,
    check_missing: bool = True,
    check_outliers: bool = True,
    check_distribution: bool = True,
    check_quality: bool = True,
    check_cardinality: bool = True,
) -> EDAReport:
    """
    Generate fast exploratory data analysis report with anomaly detection.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame to analyze.
    visualize : bool, optional
        Whether to generate summary visualizations, by default False.
    outlier_method : {'iqr', 'zscore'}, optional
        Method for outlier detection, by default 'iqr'.
    outlier_threshold : float, optional
        Threshold for outlier detection, by default 1.5.
    high_cardinality_threshold : int, optional
        Percentage threshold for high cardinality detection, by default 50.
    check_structure : bool, optional
        Whether to check basic structure and summary stats, by default True.
    check_missing : bool, optional
        Whether to analyze missing values, by default True.
    check_outliers : bool, optional
        Whether to detect outliers, by default True.
    check_distribution : bool, optional
        Whether to analyze skewness and kurtosis, by default True.
    check_quality : bool, optional
        Whether to identify data quality issues, by default True.
    check_cardinality : bool, optional
        Whether to check for high cardinality columns, by default True.

    Returns
    -------
    EDAReport
        Comprehensive EDA report with insights and recommendations.
    """
    validate_dataframe(df, min_rows=1, min_cols=1)

    try:
        # Initialize results containers
        summary_stats = pd.DataFrame()
        missing_analysis: Dict[str, float] = {}
        missing_counts: Dict[str, int] = {}
        outlier_analysis = {}
        distribution_insights = {}
        data_quality_issues = []
        high_cardinality_columns = []
        recommendations = []

        # Generate summary statistics
        if check_structure:
            summary_stats = _generate_summary_stats(df)

        # Analyze missing values
        if check_missing:
            missing_analysis, missing_counts = _analyze_missing_values(df)

        # Detect outliers
        if check_outliers:
            outlier_analysis = _detect_outliers(
                df, method=outlier_method, threshold=outlier_threshold
            )

        # Analyze distributions
        if check_distribution:
            distribution_insights = _analyze_distributions(df)

        # Identify data quality issues
        if check_quality:
            data_quality_issues = _identify_data_quality_issues(
                df, missing_analysis, outlier_analysis
            )

        # Find high cardinality columns
        if check_cardinality:
            high_cardinality_columns = _find_high_cardinality_columns(
                df, threshold=high_cardinality_threshold
            )

        # Generate recommendations based on available data
        recommendations = _generate_eda_recommendations(
            df, missing_analysis, outlier_analysis, high_cardinality_columns
        )

        # Generate visualizations if requested (and relevant data is available)
        if visualize and (check_distribution or check_outliers):
            _generate_visualizations(df, outlier_analysis)

        return EDAReport(
            summary_stats=summary_stats,
            missing_analysis=missing_analysis,
            missing_counts=missing_counts,
            outlier_analysis=outlier_analysis,
            distribution_insights=distribution_insights,
            data_quality_issues=data_quality_issues,
            high_cardinality_columns=high_cardinality_columns,
            recommendations=recommendations,
        )

    except Exception as e:
        raise AnalysisError(f"EDA generation failed: {str(e)}") from e


def _generate_summary_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Generate comprehensive summary statistics."""
    numeric_cols = get_numeric_columns(df)

    if len(numeric_cols) > 0:
        numeric_df = df[numeric_cols]
        assert isinstance(numeric_df, pd.DataFrame)
        stats_df = numeric_df.describe()
        # Add additional statistics
        stats_df.loc["missing"] = numeric_df.isnull().sum()
        stats_df.loc["missing_pct"] = (numeric_df.isnull().sum() / len(df)) * 100
        return stats_df
    else:
        return pd.DataFrame()


def _analyze_missing_values(
    df: pd.DataFrame,
) -> Tuple[Dict[str, float], Dict[str, int]]:
    """Analyze missing value patterns."""
    missing_pct: Dict[str, float] = {}
    missing_counts: Dict[str, int] = {}

    for col in df.columns:
        count = int(df[col].isnull().sum())
        if count > 0:
            pct = (count / len(df)) * 100
            missing_pct[col] = pct
            missing_counts[col] = count

    return missing_pct, missing_counts


def _detect_outliers(
    df: pd.DataFrame, method: str = "iqr", threshold: float = 1.5
) -> Dict[str, int]:
    """Detect outliers in numeric columns."""
    numeric_cols = get_numeric_columns(df)
    outliers = {}

    for col in numeric_cols:
        col_data = df[col].dropna()

        if len(col_data) == 0:
            continue

        if method == "iqr":
            Q1 = col_data.quantile(0.25)
            Q3 = col_data.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - threshold * IQR
            upper_bound = Q3 + threshold * IQR
            outlier_mask = (col_data < lower_bound) | (col_data > upper_bound)

        elif method == "zscore":
            col_array: np.ndarray = col_data.to_numpy()
            z_scores_array: np.ndarray = stats.zscore(col_array)  # type: ignore[assignment]
            z_scores: pd.Series = pd.Series(np.abs(z_scores_array), index=col_data.index)
            outlier_mask = z_scores > threshold

        else:
            outlier_mask = pd.Series([False] * len(col_data), index=col_data.index)

        outlier_count: int = int(outlier_mask.sum())
        if outlier_count > 0:
            outliers[col] = outlier_count

    return outliers


def _analyze_distributions(df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
    """Analyze distribution characteristics of numeric columns."""
    numeric_cols = get_numeric_columns(df)
    distributions = {}

    for col in numeric_cols:
        col_data = df[col].dropna()

        if len(col_data) < 3 or col_data.nunique() <= 1:
            continue

        # Calculate skewness and kurtosis
        try:
            skew = float(stats.skew(col_data))
            kurt = float(stats.kurtosis(col_data))

            distributions[col] = {
                "skewness": skew,
                "kurtosis": kurt,
                "is_normal": abs(skew) < 0.5 and abs(kurt) < 3,
            }
        except Exception:
            continue

    return distributions


def _identify_data_quality_issues(
    df: pd.DataFrame,
    missing_analysis: Dict[str, float],
    outlier_analysis: Dict[str, int],
) -> List[str]:
    """Identify potential data quality issues."""
    issues = []

    # Check for high missing values
    high_missing = [col for col, pct in missing_analysis.items() if pct > 50]
    if high_missing:
        issues.append(f"Columns with >50% missing: {', '.join(high_missing)}")

    # Check for columns with all same values
    for col in df.columns:
        if df[col].nunique() == 1:
            issues.append(f"Column '{col}' has only one unique value " f"(consider removing)")

    # Check for duplicate rows
    dup_count = df.duplicated().sum()
    if dup_count > 0:
        dup_pct = (dup_count / len(df)) * 100
        issues.append(f"{dup_count} duplicate rows found ({dup_pct:.1f}%)")

    # Check for excessive outliers
    high_outliers = [col for col, count in outlier_analysis.items() if count > len(df) * 0.1]
    if high_outliers:
        issues.append(f"Columns with >10% outliers: {', '.join(high_outliers)}")

    return issues


def _find_high_cardinality_columns(df: pd.DataFrame, threshold: int = 50) -> List[str]:
    """Find columns with high cardinality."""
    categorical_cols = get_categorical_columns(df)
    high_cardinality = []

    for col in categorical_cols:
        unique_pct = (df[col].nunique() / len(df)) * 100
        if unique_pct > threshold:
            high_cardinality.append(col)

    return high_cardinality


def _generate_eda_recommendations(
    df: pd.DataFrame,
    missing_analysis: Dict[str, float],
    outlier_analysis: Dict[str, int],
    high_cardinality_columns: List[str],
) -> List[str]:
    """Generate actionable recommendations."""
    recommendations = []

    # Missing value recommendations
    if missing_analysis:
        total_missing_pct = sum(missing_analysis.values()) / len(df.columns)
        if total_missing_pct > 5:
            recommendations.append(
                "Consider imputation strategies for columns with " "missing values"
            )

    # Outlier recommendations
    if outlier_analysis:
        recommendations.append(
            f"Review {sum(outlier_analysis.values())} outliers across "
            f"{len(outlier_analysis)} columns"
        )

    # High cardinality recommendations
    if high_cardinality_columns:
        recommendations.append(
            f"Consider encoding strategies for "
            f"{len(high_cardinality_columns)} high-cardinality columns"
        )

    # Data balance recommendation
    numeric_cols = get_numeric_columns(df)
    if len(numeric_cols) > 0:
        for col in numeric_cols:
            col_range = df[col].max() - df[col].min()
            if col_range > 1000:
                recommendations.append(
                    f"Consider scaling/normalization for '{col}' " f"(wide value range)"
                )
                break

    if not recommendations:
        recommendations.append("Data quality looks good - no major issues detected")

    return recommendations


def _generate_visualizations(df: pd.DataFrame, outlier_analysis: Dict[str, int]) -> None:
    """Generate summary visualizations (requires matplotlib)."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("Warning: matplotlib not installed. Skipping visualizations.")
        return

    numeric_cols = get_numeric_columns(df)

    if len(numeric_cols) == 0:
        return

    # Create subplots
    n_cols = min(3, len(numeric_cols))
    n_rows = (len(numeric_cols) + n_cols - 1) // n_cols

    fig, axes = plt.subplots(n_rows, n_cols, figsize=(5 * n_cols, 4 * n_rows))
    if n_rows == 1 and n_cols == 1:
        axes = np.array([axes])
    axes = axes.flatten()

    # Plot distributions
    for idx, col in enumerate(numeric_cols):
        if idx < len(axes):
            df[col].hist(bins=30, ax=axes[idx], edgecolor="black")
            axes[idx].set_title(f"{col} Distribution")
            axes[idx].set_xlabel(col)
            axes[idx].set_ylabel("Frequency")

            # Highlight if outliers detected
            if col in outlier_analysis:
                axes[idx].set_title(
                    f"{col} Distribution\n" f"({outlier_analysis[col]} outliers)",
                    color="red",
                )

    # Remove empty subplots
    for idx in range(len(numeric_cols), len(axes)):
        fig.delaxes(axes[idx])

    plt.tight_layout()
    plt.show()
