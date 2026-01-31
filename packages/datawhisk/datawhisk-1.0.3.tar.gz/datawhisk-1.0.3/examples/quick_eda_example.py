"""
Quick EDA Example
=================

This example demonstrates how to use datawhisk's quick EDA reporter for
fast exploratory data analysis.
"""

import numpy as np
import pandas as pd

from datawhisk.analytical import quick_eda


def create_clean_data():
    """Create a clean dataset."""
    np.random.seed(42)
    return pd.DataFrame({
        'age': np.random.randint(18, 80, 1000),
        'income': np.random.uniform(30000, 150000, 1000),
        'score': np.random.uniform(0, 100, 1000),
        'category': np.random.choice(['A', 'B', 'C'], 1000),
    })


def create_messy_data():
    """Create a messy dataset with quality issues."""
    np.random.seed(42)
    df = pd.DataFrame({
        'age': np.random.randint(18, 80, 1000),
        'income': np.concatenate([
            np.random.uniform(30000, 150000, 950),
            [1000000, 2000000] * 25  # Outliers
        ]),
        'score': np.random.uniform(0, 100, 1000),
        'customer_id': [f'CUST_{i:06d}' for i in range(1000)],  # High cardinality
        'category': np.random.choice(['A', 'B', 'C'], 1000),
        'status': np.random.choice(['Active', 'Inactive'], 1000),
    })
    
    # Add missing values
    df.loc[np.random.choice(df.index, 300, replace=False), 'income'] = np.nan
    df.loc[np.random.choice(df.index, 150, replace=False), 'score'] = np.nan
    
    # Add duplicates
    df = pd.concat([df, df.iloc[:50]], ignore_index=True)
    
    return df


def example_basic_eda():
    """Example 1: Basic EDA report."""
    print("=" * 70)
    print("Example 1: Basic EDA Report")
    print("=" * 70)
    
    df = create_clean_data()
    
    # Generate EDA report
    report = quick_eda(df)
    
    print(report)
    
    print("\n\nDetailed Summary Statistics:")
    print(report.summary_stats)


def example_outlier_detection():
    """Example 2: Outlier detection."""
    print("\n" + "=" * 70)
    print("Example 2: Outlier Detection")
    print("=" * 70)
    
    df = create_messy_data()
    
    # Detect outliers using IQR method
    report = quick_eda(df, outlier_method='iqr', outlier_threshold=1.5)
    
    print("\nOutliers Detected:")
    for col, count in report.outlier_analysis.items():
        pct = (count / len(df)) * 100
        print(f"  {col:20s}: {count:4d} ({pct:.1f}%)")
    
    # Compare with Z-score method
    print("\n\nUsing Z-score method (threshold=3):")
    report_zscore = quick_eda(df, outlier_method='zscore', outlier_threshold=3)
    
    for col, count in report_zscore.outlier_analysis.items():
        pct = (count / len(df)) * 100
        print(f"  {col:20s}: {count:4d} ({pct:.1f}%)")


def example_missing_data_analysis():
    """Example 3: Missing data analysis."""
    print("\n" + "=" * 70)
    print("Example 3: Missing Data Analysis")
    print("=" * 70)
    
    df = create_messy_data()
    
    report = quick_eda(df)
    
    print("\nMissing Value Analysis:")
    if report.missing_analysis:
        for col, pct in sorted(report.missing_analysis.items(), 
                               key=lambda x: x[1], reverse=True):
            count = report.missing_counts[col]
            print(f"  {col:20s}: {count:4d} ({pct:5.1f}%) missing")
    else:
        print("  No missing values detected")


def example_data_quality_issues():
    """Example 4: Data quality issue detection."""
    print("\n" + "=" * 70)
    print("Example 4: Data Quality Issues")
    print("=" * 70)
    
    df = create_messy_data()
    
    report = quick_eda(df)
    
    print("\nData Quality Issues:")
    if report.data_quality_issues:
        for i, issue in enumerate(report.data_quality_issues, 1):
            print(f"  {i}. {issue}")
    else:
        print("  No major data quality issues detected")
    
    print("\nHigh Cardinality Columns:")
    if report.high_cardinality_columns:
        for col in report.high_cardinality_columns:
            unique_count = df[col].nunique()
            pct = (unique_count / len(df)) * 100
            print(f"  {col:20s}: {unique_count:5d} unique ({pct:.1f}%)")
    else:
        print("  No high cardinality columns detected")


def example_distribution_insights():
    """Example 5: Distribution analysis."""
    print("\n" + "=" * 70)
    print("Example 5: Distribution Insights")
    print("=" * 70)
    
    df = create_clean_data()
    
    report = quick_eda(df)
    
    print("\nDistribution Characteristics:")
    for col, insights in report.distribution_insights.items():
        print(f"\n{col}:")
        print(f"  Skewness: {insights['skewness']:.3f}")
        print(f"  Kurtosis: {insights['kurtosis']:.3f}")
        print(f"  Normal: {'Yes' if insights['is_normal'] else 'No'}")


def example_recommendations():
    """Example 6: Actionable recommendations."""
    print("\n" + "=" * 70)
    print("Example 6: Actionable Recommendations")
    print("=" * 70)
    
    df = create_messy_data()
    
    report = quick_eda(df)
    
    print("\nRecommendations:")
    for i, rec in enumerate(report.recommendations, 1):
        print(f"  {i}. {rec}")


def example_custom_thresholds():
    """Example 7: Custom threshold settings."""
    print("\n" + "=" * 70)
    print("Example 7: Custom Threshold Settings")
    print("=" * 70)
    
    df = create_messy_data()
    
    # Different outlier thresholds
    print("\nOutlier Detection with Different Thresholds:")
    
    for threshold in [1.0, 1.5, 2.0, 3.0]:
        report = quick_eda(df, outlier_method='iqr', outlier_threshold=threshold)
        total_outliers = sum(report.outlier_analysis.values())
        print(f"  Threshold {threshold}: {total_outliers} total outliers")
    
    # Different cardinality thresholds
    print("\n\nHigh Cardinality Detection with Different Thresholds:")
    
    for threshold in [25, 50, 75]:
        report = quick_eda(df, high_cardinality_threshold=threshold)
        print(f"  Threshold {threshold}%: {len(report.high_cardinality_columns)} columns")


def example_real_world_ecommerce():
    """Example 8: Real-world e-commerce data."""
    print("\n" + "=" * 70)
    print("Example 8: Real-world E-commerce Data Analysis")
    print("=" * 70)
    
    # Simulate e-commerce data
    np.random.seed(42)
    n = 5000
    
    # Create realistic e-commerce dataset
    df = pd.DataFrame({
        'order_id': range(n),
        'customer_age': np.random.randint(18, 75, n),
        'order_value': np.random.lognormal(4, 1, n),  # Log-normal distribution
        'items_count': np.random.poisson(3, n),
        'delivery_days': np.random.gamma(2, 2, n),
        'customer_rating': np.random.choice([1, 2, 3, 4, 5], n, p=[0.05, 0.1, 0.15, 0.3, 0.4]),
        'product_category': np.random.choice(
            ['Electronics', 'Clothing', 'Home', 'Books', 'Sports'],
            n,
            p=[0.3, 0.25, 0.2, 0.15, 0.1]
        ),
        'payment_method': np.random.choice(['Credit', 'Debit', 'PayPal'], n),
        'device': np.random.choice(['Mobile', 'Desktop', 'Tablet'], n, p=[0.6, 0.3, 0.1]),
    })
    
    # Add some realistic data issues
    # Missing ratings for some orders
    df.loc[np.random.choice(df.index, 500, replace=False), 'customer_rating'] = np.nan
    
    # Some extreme order values (fraud or errors)
    df.loc[np.random.choice(df.index, 20, replace=False), 'order_value'] = \
        np.random.uniform(5000, 10000, 20)
    
    print("\nE-commerce Dataset Overview:")
    print(f"Total Orders: {len(df):,}")
    print(f"Date Range: Last 30 days")
    print(f"Columns: {', '.join(df.columns)}")
    
    # Run comprehensive EDA
    report = quick_eda(df)
    
    print("\n" + "=" * 50)
    print("Quick EDA Report Summary")
    print("=" * 50)
    
    print(f"\nMissing Data:")
    if report.missing_analysis:
        for col, pct in report.missing_analysis.items():
            print(f"  {col:20s}: {pct:.1f}%")
    else:
        print("  None detected")
    
    print(f"\nOutliers:")
    if report.outlier_analysis:
        for col, count in report.outlier_analysis.items():
            pct = (count / len(df)) * 100
            print(f"  {col:20s}: {count:4d} ({pct:.1f}%)")
    else:
        print("  None detected")
    
    print(f"\nData Quality Issues:")
    for issue in report.data_quality_issues:
        print(f"  ⚠ {issue}")
    
    print(f"\nKey Statistics:")
    print(f"  Average order value: ${df['order_value'].mean():.2f}")
    print(f"  Median order value: ${df['order_value'].median():.2f}")
    print(f"  Average items per order: {df['items_count'].mean():.1f}")
    print(f"  Average delivery time: {df['delivery_days'].mean():.1f} days")
    
    print(f"\nRecommendations:")
    for i, rec in enumerate(report.recommendations, 1):
        print(f"  {i}. {rec}")


def example_comparison_before_after():
    """Example 9: Before and after data cleaning."""
    print("\n" + "=" * 70)
    print("Example 9: Before/After Data Cleaning Comparison")
    print("=" * 70)
    
    # Original messy data
    df_before = create_messy_data()
    
    print("\nBEFORE Cleaning:")
    report_before = quick_eda(df_before)
    print(f"  Missing values: {len(report_before.missing_analysis)} columns")
    print(f"  Outliers: {sum(report_before.outlier_analysis.values())} total")
    print(f"  Quality issues: {len(report_before.data_quality_issues)}")
    print(f"  Duplicates: {df_before.duplicated().sum()}")
    
    # Clean the data
    df_after = df_before.copy()
    
    # Remove duplicates
    df_after = df_after.drop_duplicates()
    
    # Fill missing values (simple strategy)
    for col in df_after.select_dtypes(include=[np.number]).columns:
        df_after[col].fillna(df_after[col].median(), inplace=True)
    
    # Remove outliers from income
    Q1 = df_after['income'].quantile(0.25)
    Q3 = df_after['income'].quantile(0.75)
    IQR = Q3 - Q1
    df_after = df_after[
        (df_after['income'] >= Q1 - 1.5 * IQR) &
        (df_after['income'] <= Q3 + 1.5 * IQR)
    ]
    assert isinstance(df_after, pd.DataFrame)
    
    print("\nAFTER Cleaning:")
    report_after = quick_eda(df_after)
    print(f"  Missing values: {len(report_after.missing_analysis)} columns")
    print(f"  Outliers: {sum(report_after.outlier_analysis.values())} total")
    print(f"  Quality issues: {len(report_after.data_quality_issues)}")
    print(f"  Duplicates: {df_after.duplicated().sum()}")
    print(f"  Rows removed: {len(df_before) - len(df_after)}")


def example_modular_eda():
    """Example 10: Modular EDA with specific checks."""
    print("\n" + "=" * 70)
    print("Example 10: Modular EDA (Selective Checks)")
    print("=" * 70)

    df = create_messy_data()

    # Case 1: Only check missing values
    print("\n1. Checking ONLY missing values:")
    report_missing = quick_eda(
        df,
        check_structure=False,
        check_missing=True,
        check_outliers=False,
        check_distribution=False,
        check_quality=False,
        check_cardinality=False
    )
    if report_missing.missing_analysis:
        print(f"  Found missing values in {len(report_missing.missing_analysis)} columns")
    if not report_missing.outlier_analysis:
        print("  Skipped outlier detection (as expected)")

    # Case 2: Only check structure and distribution
    print("\n2. Checking ONLY structure and distribution:")
    report_dist = quick_eda(
        df,
        check_structure=True,
        check_missing=False,
        check_outliers=False,
        check_distribution=True,
        check_quality=False,
        check_cardinality=False
    )
    print(f"  Dataset shape: {report_dist.summary_stats.shape}")
    print(f"  Distribution insights available: {'Yes' if report_dist.distribution_insights else 'No'}")
    print(f"  Missing analysis available: {'Yes' if report_dist.missing_analysis else 'No'}")


if __name__ == "__main__":
    # Run all examples
    example_basic_eda()
    example_outlier_detection()
    example_missing_data_analysis()
    example_data_quality_issues()
    example_distribution_insights()
    example_recommendations()
    example_custom_thresholds()
    example_real_world_ecommerce()
    example_comparison_before_after()
    example_modular_eda()
    
    print("\n" + "=" * 70)
    print("All examples completed successfully!")
    print("=" * 70)