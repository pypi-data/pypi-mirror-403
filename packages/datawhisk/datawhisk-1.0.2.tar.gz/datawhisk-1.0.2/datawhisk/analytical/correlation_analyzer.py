"""Correlation analysis with multicollinearity detection."""

from dataclasses import dataclass
from typing import List, Optional, Tuple, Literal, cast

import numpy as np
import pandas as pd

from datawhisk.exceptions import AnalysisError, ValidationError
from datawhisk.utils import (
    check_column_exists,
    get_numeric_columns,
    validate_dataframe,
)


@dataclass
class CorrelationResults:
    """Results from correlation analysis."""

    correlation_matrix: pd.DataFrame
    vif_scores: Optional[pd.DataFrame]
    high_correlations: List[Tuple[str, str, float]]
    recommendations: List[str]
    method: str
    target: Optional[str]

    def __str__(self) -> str:
        """Return formatted results string."""
        output = [
            "Correlation Analysis Results",
            "=" * 50,
            f"Method: {self.method}",
            f"Features analyzed: {len(self.correlation_matrix)}",
        ]

        if self.target:
            output.append(f"Target variable: {self.target}")

        output.extend(
            [
                f"\nHigh Correlations Found: {len(self.high_correlations)}",
                f"Recommendations: {len(self.recommendations)}",
            ]
        )

        if self.recommendations:
            output.append("\nTop Recommendations:")
            for rec in self.recommendations[:5]:
                output.append(f"  - {rec}")

        return "\n".join(output)


def analyze_correlations(
    df: pd.DataFrame,
    target: Optional[str] = None,
    threshold: float = 0.8,
    method: str = "pearson",
    calculate_vif: bool = True,
    variance_threshold: float = 0.01,
    return_details: bool = True,
) -> CorrelationResults:
    """
    Analyze correlations with automatic filtering and multicollinearity
    detection.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame containing numeric features.
    target : str, optional
        Target variable name for feature selection, by default None.
    threshold : float, optional
        Correlation threshold for flagging high correlations (0-1),
        by default 0.8.
    method : {'pearson', 'spearman', 'kendall'}, optional
        Correlation method to use, by default 'pearson'.
    calculate_vif : bool, optional
        Whether to calculate VIF scores for multicollinearity,
        by default True.
    variance_threshold : float, optional
        Minimum variance threshold to keep features, by default 0.01.
    return_details : bool, optional
        Whether to return detailed recommendations, by default True.

    Returns
    -------
    CorrelationResults
        Object containing correlation matrix, VIF values, and
        recommendations.

    Raises
    ------
    ValidationError
        If input validation fails.
    AnalysisError
        If correlation analysis fails.

    Examples
    --------
    >>> import pandas as pd
    >>> df = pd.DataFrame({
    ...     'feature1': [1, 2, 3, 4, 5],
    ...     'feature2': [2, 4, 6, 8, 10],  # Highly correlated with feature1
    ...     'feature3': [5, 4, 3, 2, 1],
    ...     'target': [10, 20, 30, 40, 50]
    ... })
    >>> results = analyze_correlations(
    ...     df, target='target', threshold=0.9
    ... )
    >>> print(results.recommendations)
    ['Remove feature2 (correlation with feature1: 1.00)']

    Notes
    -----
    - Low-variance features (variance < variance_threshold) are
      automatically removed
    - VIF (Variance Inflation Factor) > 10 indicates high
      multicollinearity
    - The function provides actionable recommendations for feature
      selection
    """
    # Validate inputs
    validate_dataframe(df, min_rows=3, min_cols=2, require_numeric=True)

    if threshold < 0 or threshold > 1:
        raise ValidationError("threshold must be between 0 and 1")

    if method not in ["pearson", "spearman", "kendall"]:
        raise ValidationError(
            f"method must be 'pearson', 'spearman', or 'kendall', " f"got '{method}'"
        )

    # Validate target if provided
    if target:
        check_column_exists(df, target, "target")

    try:
        # Get numeric columns
        numeric_cols = get_numeric_columns(df)

        if target and target in numeric_cols:
            # Exclude target from features
            feature_cols = [col for col in numeric_cols if col != target]
        else:
            feature_cols = list(numeric_cols)

        if len(feature_cols) < 2:
            raise ValidationError(
                "At least 2 numeric features required for " "correlation analysis"
            )

        # Remove low-variance features
        features_df = df[feature_cols]
        assert isinstance(features_df, pd.DataFrame)
        feature_cols = _remove_low_variance_features(features_df, variance_threshold)

        if len(feature_cols) < 2:
            raise AnalysisError(
                "Insufficient features after removing low-variance "
                f"columns. Try lowering variance_threshold "
                f"(current: {variance_threshold})"
            )

        # Calculate correlation matrix
        features_for_corr = df[feature_cols]
        assert isinstance(features_for_corr, pd.DataFrame)
        # Cast method to literal type
        corr_method = cast(Literal["pearson", "spearman", "kendall"], method)
        corr_matrix = features_for_corr.corr(method=corr_method)

        # Find high correlations
        high_correlations = _find_high_correlations(corr_matrix, threshold)

        # Calculate VIF if requested
        vif_scores = None
        if calculate_vif and len(feature_cols) >= 2:
            features_for_vif = df[feature_cols]
            assert isinstance(features_for_vif, pd.DataFrame)
            vif_scores = _calculate_vif(features_for_vif)

        # Generate recommendations
        recommendations = []
        if return_details:
            recommendations = _generate_recommendations(
                corr_matrix, high_correlations, vif_scores, target, df
            )

        return CorrelationResults(
            correlation_matrix=corr_matrix,
            vif_scores=vif_scores,
            high_correlations=high_correlations,
            recommendations=recommendations,
            method=method,
            target=target,
        )

    except Exception as e:
        if isinstance(e, (ValidationError, AnalysisError)):
            raise
        raise AnalysisError(f"Correlation analysis failed: {str(e)}") from e


def _remove_low_variance_features(df: pd.DataFrame, threshold: float) -> List[str]:
    """Remove features with variance below threshold."""
    variances: pd.Series = df.var()  # type: ignore[assignment]
    high_variance_features = variances[variances >= threshold]
    return high_variance_features.index.tolist()  # type: ignore


def _find_high_correlations(
    corr_matrix: pd.DataFrame, threshold: float
) -> List[Tuple[str, str, float]]:
    """Find pairs of features with correlation above threshold."""
    high_corr = []

    for i in range(len(corr_matrix.columns)):
        for j in range(i + 1, len(corr_matrix.columns)):
            corr_value = abs(corr_matrix.iloc[i, j])
            if corr_value >= threshold:
                high_corr.append(
                    (
                        corr_matrix.columns[i],
                        corr_matrix.columns[j],
                        corr_matrix.iloc[i, j],
                    )
                )

    return sorted(high_corr, key=lambda x: abs(x[2]), reverse=True)


def _calculate_vif(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate Variance Inflation Factor for each feature.

    VIF measures how much the variance of a coefficient is inflated due to
    multicollinearity with other features.
    """
    from numpy.linalg import LinAlgError

    vif_data = []

    for i, col in enumerate(df.columns):
        try:
            # Calculate R-squared using correlation

            # For simplicity, use average correlation as proxy for R-squared
            correlations = df.corr()[col].drop(col)
            r_squared = np.mean(correlations**2)

            # Calculate VIF: VIF = 1 / (1 - R²)
            if r_squared < 0.9999:  # Avoid division by zero
                vif = 1 / (1 - r_squared)
            else:
                vif = np.inf

            vif_data.append({"feature": col, "VIF": vif})

        except (LinAlgError, ZeroDivisionError):
            vif_data.append({"feature": col, "VIF": np.inf})

    return pd.DataFrame(vif_data).sort_values("VIF", ascending=False)


def _generate_recommendations(
    corr_matrix: pd.DataFrame,
    high_correlations: List[Tuple[str, str, float]],
    vif_scores: Optional[pd.DataFrame],
    target: Optional[str],
    df: pd.DataFrame,
) -> List[str]:
    """Generate actionable recommendations based on analysis."""
    recommendations = []

    # Recommendations based on high correlations
    if high_correlations:
        recommendations.append(
            f"Found {len(high_correlations)} pairs of highly " f"correlated features"
        )

        for feat1, feat2, corr in high_correlations[:3]:  # Top 3
            if target:
                # Recommend keeping feature more correlated with target
                if feat1 in corr_matrix.index and target in corr_matrix.columns:
                    target_corr1 = abs(corr_matrix.loc[feat1, target])
                else:
                    target_corr1 = 0
                if feat2 in corr_matrix.index and target in corr_matrix.columns:
                    target_corr2 = abs(corr_matrix.loc[feat2, target])
                else:
                    target_corr2 = 0

                if target_corr1 > target_corr2:
                    recommendations.append(
                        f"Remove '{feat2}' (corr with '{feat1}': "
                        f"{corr:.2f}, target corr: {target_corr2:.2f} "
                        f"vs {target_corr1:.2f})"
                    )
                else:
                    recommendations.append(
                        f"Remove '{feat1}' (corr with '{feat2}': "
                        f"{corr:.2f}, target corr: {target_corr1:.2f} "
                        f"vs {target_corr2:.2f})"
                    )
            else:
                recommendations.append(
                    f"Consider removing one of '{feat1}' or '{feat2}' " f"(correlation: {corr:.2f})"
                )

    # Recommendations based on VIF
    if vif_scores is not None:
        high_vif = vif_scores[vif_scores["VIF"] > 10]
        if len(high_vif) > 0:
            recommendations.append(f"Found {len(high_vif)} features with high VIF (>10)")
            for _, row in high_vif.head(3).iterrows():
                vif_val = row["VIF"]
                vif_str = f"{vif_val:.2f}" if not np.isinf(vif_val) else "inf"
                recommendations.append(f"Consider removing '{row['feature']}' " f"(VIF: {vif_str})")

    if not recommendations:
        recommendations.append("No significant multicollinearity detected")
        recommendations.append("All features can be safely retained")

    return recommendations
