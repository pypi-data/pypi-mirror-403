"""
Correlation Analysis Example
=============================

This example demonstrates how to use datawhisk's correlation analyzer for
feature selection and multicollinearity detection.
"""

import numpy as np
import pandas as pd
from typing import cast, Literal

from datawhisk.analytical import analyze_correlations


def create_sample_data():
    """Create sample data with various correlation patterns."""
    np.random.seed(42)
    n = 1000
    
    # Create features with different correlation patterns
    x1 = np.random.randn(n)
    x2 = x1 + np.random.randn(n) * 0.1  # Highly correlated with x1
    x3 = np.random.randn(n)  # Independent
    x4 = x3 + np.random.randn(n) * 0.2  # Moderately correlated with x3
    x5 = np.random.randn(n)  # Independent
    
    # Create target variable
    target = 2 * x1 + 3 * x3 + 0.5 * x5 + np.random.randn(n)
    
    return pd.DataFrame({
        'feature1': x1,
        'feature2': x2,
        'feature3': x3,
        'feature4': x4,
        'feature5': x5,
        'target': target,
    })


def example_basic_correlation():
    """Example 1: Basic correlation analysis."""
    print("=" * 70)
    print("Example 1: Basic Correlation Analysis")
    print("=" * 70)
    
    df = create_sample_data()
    
    # Analyze correlations
    results = analyze_correlations(df, target='target')
    
    print("\nCorrelation Matrix:")
    print(results.correlation_matrix)
    
    print(f"\nHigh Correlations (threshold=0.8):")
    for feat1, feat2, corr in results.high_correlations:
        print(f"  {feat1} <-> {feat2}: {corr:.3f}")


def example_with_vif():
    """Example 2: Correlation analysis with VIF scores."""
    print("\n" + "=" * 70)
    print("Example 2: Multicollinearity Detection with VIF")
    print("=" * 70)
    
    df = create_sample_data()
    
    # Analyze with VIF calculation
    results = analyze_correlations(
        df,
        target='target',
        calculate_vif=True
    )
    
    print("\nVIF Scores:")
    print(results.vif_scores)
    
    print("\nInterpretation:")
    print("VIF < 5:  Low multicollinearity (Good)")
    print("VIF 5-10: Moderate multicollinearity (Caution)")
    print("VIF > 10: High multicollinearity (Remove feature)")


def example_feature_selection():
    """Example 3: Feature selection based on correlations."""
    print("\n" + "=" * 70)
    print("Example 3: Feature Selection Recommendations")
    print("=" * 70)
    
    df = create_sample_data()
    
    # Get recommendations for feature selection
    results = analyze_correlations(
        df,
        target='target',
        threshold=0.8,
        return_details=True
    )
    
    print("\nRecommendations:")
    for i, recommendation in enumerate(results.recommendations, 1):
        print(f"{i}. {recommendation}")


def example_different_methods():
    """Example 4: Different correlation methods."""
    print("\n" + "=" * 70)
    print("Example 4: Different Correlation Methods")
    print("=" * 70)
    
    df = create_sample_data()
    
    methods = ['pearson', 'spearman', 'kendall']
    
    for method in methods:
        results = analyze_correlations(df, target='target', method=method)
        
        print(f"\n{method.capitalize()} Correlation:")
        print(f"High correlations found: {len(results.high_correlations)}")
        
        # Show correlation with target
        if 'feature1' in results.correlation_matrix.index:
            method_typed = cast(Literal['pearson', 'spearman', 'kendall'], method)
            corr_with_target = df.corr(method=method_typed)['target']['feature1']
            print(f"feature1 vs target: {corr_with_target:.3f}")


def example_custom_threshold():
    """Example 5: Custom correlation threshold."""
    print("\n" + "=" * 70)
    print("Example 5: Custom Correlation Threshold")
    print("=" * 70)
    
    df = create_sample_data()
    
    thresholds = [0.7, 0.8, 0.9]
    
    for threshold in thresholds:
        results = analyze_correlations(df, threshold=threshold)
        
        print(f"\nThreshold = {threshold}:")
        print(f"  High correlations detected: {len(results.high_correlations)}")


def example_real_world_housing():
    """Example 6: Real-world housing price prediction."""
    print("\n" + "=" * 70)
    print("Example 6: Real-world Housing Price Prediction")
    print("=" * 70)
    
    # Simulate housing data
    np.random.seed(42)
    n = 500
    
    # Create realistic features
    sqft = np.random.uniform(1000, 5000, n)
    rooms = np.round(sqft / 500 + np.random.randn(n) * 0.5)
    bedrooms = np.round(rooms * 0.6 + np.random.randn(n) * 0.3)
    bathrooms = np.round(bedrooms * 0.8 + np.random.randn(n) * 0.2)
    age = np.random.uniform(0, 50, n)
    condition = np.random.uniform(1, 10, n)
    
    # Price depends on multiple factors
    price = (
        sqft * 200 +
        rooms * 5000 +
        (50 - age) * 1000 +
        condition * 10000 +
        np.random.randn(n) * 50000
    )
    
    df = pd.DataFrame({
        'sqft': sqft,
        'total_rooms': rooms,
        'bedrooms': bedrooms,
        'bathrooms': bathrooms,
        'age_years': age,
        'condition_score': condition,
        'price': price,
    })
    
    print("\nHousing Dataset:")
    print(df.describe())
    
    # Analyze correlations
    results = analyze_correlations(
        df,
        target='price',
        threshold=0.7,
        calculate_vif=True
    )
    
    print("\n" + "=" * 50)
    print("Analysis Results:")
    print("=" * 50)
    
    print("\nCorrelation with Price:")
    price_corr_series: pd.Series = df.corr()['price']  # type: ignore
    price_corr = price_corr_series.sort_values(ascending=False)
    for feature, corr in price_corr.items():
        if feature != 'price':
            print(f"  {feature:20s}: {corr:.3f}")
    
    print("\nMulticollinearity Check:")
    if results.vif_scores is not None:
        for _, row in results.vif_scores.iterrows():
            vif_val = row['VIF']
            status = "⚠ HIGH" if vif_val > 10 else "✓ OK"
            vif_str = f"{vif_val:.2f}" if not np.isinf(vif_val) else "inf"
            print(f"  {row['feature']:20s}: VIF = {vif_str:>8s} {status}")
    
    print("\nRecommendations:")
    for rec in results.recommendations:
        print(f"  • {rec}")


def example_time_series_features():
    """Example 7: Time series feature engineering."""
    print("\n" + "=" * 70)
    print("Example 7: Time Series Feature Correlations")
    print("=" * 70)
    
    # Simulate time series with lag features
    np.random.seed(42)
    n = 1000
    
    # Base signal
    trend = np.linspace(0, 100, n)
    seasonal = 10 * np.sin(np.linspace(0, 8 * np.pi, n))
    noise = np.random.randn(n) * 5
    
    target = trend + seasonal + noise
    
    # Create lag features
    df = pd.DataFrame({
        'value': target,
        'lag_1': pd.Series(target).shift(1),
        'lag_2': pd.Series(target).shift(2),
        'lag_3': pd.Series(target).shift(3),
        'lag_7': pd.Series(target).shift(7),
        'rolling_mean_3': pd.Series(target).rolling(3).mean(),
        'rolling_std_3': pd.Series(target).rolling(3).std(),
    }).dropna()
    
    # Analyze which lag features are most useful
    results = analyze_correlations(
        df,
        target='value',
        threshold=0.8
    )
    
    print("\nFeature Correlations with Target:")
    target_corr_series: pd.Series = df.corr()['value']  # type: ignore
    target_corr = target_corr_series.sort_values(ascending=False)
    for feature, corr in target_corr.items():
        if feature != 'value':
            print(f"  {feature:20s}: {corr:.3f}")
    
    print("\nFeature Selection Guidance:")
    for rec in results.recommendations[:5]:
        print(f"  • {rec}")


if __name__ == "__main__":
    # Run all examples
    example_basic_correlation()
    example_with_vif()
    example_feature_selection()
    example_different_methods()
    example_custom_threshold()
    example_real_world_housing()
    example_time_series_features()
    
    print("\n" + "=" * 70)
    print("All examples completed successfully!")
    print("=" * 70)