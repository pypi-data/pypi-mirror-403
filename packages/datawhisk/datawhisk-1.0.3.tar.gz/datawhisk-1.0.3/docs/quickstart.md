# Quick Start Guide

Get started with datawhisk in just a few minutes! This guide covers the three main features with practical examples.

## Installation

First, install datawhisk:

```bash
pip install datawhisk
```

## Core Features

### 1. Memory Optimizer

Automatically optimize DataFrame memory usage by downcasting numeric types and converting to categorical where appropriate.

#### Basic Usage

```python
from datawhisk.analytical import optimize_memory
import pandas as pd

# Create a DataFrame
df = pd.DataFrame({
    'id': range(1000000),
    'category': ['A', 'B', 'C'] * 333334,
    'value': [1.5] * 1000000
})

# Check original memory
print(f"Original memory: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")

# Optimize memory
optimized_df, report = optimize_memory(df, return_report=True)

# View results
print(f"Optimized memory: {report.optimized_memory_mb:.2f} MB")
print(f"Memory reduced by {report.reduction_percent:.1f}%")
print(f"\nOptimization details:")
for col, details in report.optimization_details.items():
    print(f"  {col}: {details['original']} → {details['optimized']}")
```

#### Advanced Options

```python
# Aggressive mode (downcasts floats to float32)
optimized_df, report = optimize_memory(
    df,
    aggressive=True,
    categorical_threshold=50,  # Convert to categorical if <50 unique values
    return_report=True
)

# In-place optimization (modifies original DataFrame)
optimize_memory(df, inplace=True)
```

#### Undo Optimization

```python
from datawhisk.analytical import undo_optimization

# Restore original dtypes
original_df = undo_optimization(optimized_df, report.original_dtypes)
```

---

### 2. Correlation Analyzer

Smart correlation analysis with automatic multicollinearity detection using VIF (Variance Inflation Factor).

#### Basic Usage

```python
from datawhisk.analytical import analyze_correlations
import pandas as pd
import numpy as np

# Create sample data with correlations
np.random.seed(42)
x1 = np.random.randn(1000)
x2 = x1 + np.random.randn(1000) * 0.1  # Highly correlated with x1
x3 = np.random.randn(1000)

df = pd.DataFrame({
    'feature1': x1,
    'feature2': x2,  # Multicollinear with feature1
    'feature3': x3,
    'target': 2 * x1 + x3 + np.random.randn(1000) * 0.5
})

# Analyze correlations
results = analyze_correlations(
    df,
    target='target',
    threshold=0.8,
    method='pearson'
)

# View results
print("Correlation Matrix:")
print(results.correlation_matrix)

print("\nHigh Correlations:")
for feat1, feat2, corr in results.high_correlations:
    print(f"  {feat1} ↔ {feat2}: {corr:.3f}")

print("\nVIF Scores:")
print(results.vif_scores)

print("\nRecommendations:")
for rec in results.recommendations:
    print(f"  • {rec}")
```

#### Advanced Options

```python
# Spearman correlation (for non-linear relationships)
results = analyze_correlations(
    df,
    method='spearman',
    calculate_vif=True,
    variance_threshold=0.01  # Remove low-variance features
)

# Kendall correlation (robust to outliers)
results = analyze_correlations(
    df,
    method='kendall',
    threshold=0.7
)

# Without detailed recommendations
results = analyze_correlations(
    df,
    return_details=False
)
```

---

### 3. Quick EDA Reporter

Fast exploratory data analysis with automatic anomaly detection and data quality checks.

#### Basic Usage

```python
from datawhisk.analytical import quick_eda
import pandas as pd
import numpy as np

# Create sample dataset
np.random.seed(42)
df = pd.DataFrame({
    'numeric1': np.random.randn(1000),
    'numeric2': np.random.randn(1000) * 100,
    'category': np.random.choice(['A', 'B', 'C'], 1000),
    'with_missing': [np.nan if i % 10 == 0 else i for i in range(1000)],
    'with_outliers': np.concatenate([
        np.random.randn(950),
        [100, 200, -150, 180, -175] * 10
    ])
})

# Generate EDA report
report = quick_eda(df, visualize=False)

# View summary statistics
print("Summary Statistics:")
print(report.summary_stats)

# Check missing values
print("\nMissing Values:")
for col, pct in report.missing_analysis.items():
    print(f"  {col}: {pct:.1f}%")

# Check outliers
print("\nOutliers Detected:")
for col, count in report.outlier_analysis.items():
    print(f"  {col}: {count} outliers")

# Data quality issues
print("\nData Quality Issues:")
for issue in report.data_quality_issues:
    print(f"  ⚠ {issue}")

# Recommendations
print("\nRecommendations:")
for rec in report.recommendations:
    print(f"  • {rec}")
```

#### Modular EDA (Custom Checks)

```python
# Run only specific checks
report = quick_eda(
    df,
    check_structure=True,      # Basic structure info
    check_missing=True,        # Missing value analysis
    check_outliers=True,       # Outlier detection
    check_distribution=False,  # Skip distribution analysis
    check_quality=False,       # Skip quality checks
    check_cardinality=False    # Skip cardinality checks
)
```

#### Outlier Detection Methods

```python
# IQR method (default)
report = quick_eda(
    df,
    outlier_method='iqr',
    outlier_threshold=1.5  # Standard IQR multiplier
)

# Z-score method
report = quick_eda(
    df,
    outlier_method='zscore',
    outlier_threshold=3  # Standard deviations
)
```

#### With Visualizations

```python
# Generate visualizations (requires matplotlib/seaborn)
report = quick_eda(df, visualize=True)
# This will create and display plots for distributions and correlations
```

---

## Complete Workflow Example

Here's a complete data analysis workflow using all three features:

```python
from datawhisk.analytical import optimize_memory, analyze_correlations, quick_eda
import pandas as pd
import numpy as np

# 1. Load data
np.random.seed(42)
df = pd.DataFrame({
    'id': range(10000),
    'feature1': np.random.randn(10000),
    'feature2': np.random.randn(10000) * 100,
    'feature3': np.random.choice(['A', 'B', 'C'], 10000),
    'target': np.random.randn(10000)
})

print(f"Original size: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")

# 2. Optimize memory
df_optimized, mem_report = optimize_memory(df, return_report=True)
print(f"Optimized size: {mem_report.optimized_memory_mb:.2f} MB")
print(f"Saved {mem_report.reduction_percent:.1f}% memory")

# 3. Quick EDA
eda_report = quick_eda(df_optimized)
print(f"\nDataset shape: {eda_report.shape}")
print(f"Missing values: {sum(eda_report.missing_analysis.values()):.1f}%")
print(f"Data quality issues: {len(eda_report.data_quality_issues)}")

# 4. Correlation analysis
corr_results = analyze_correlations(
    df_optimized,
    target='target',
    threshold=0.7
)
print(f"\nHigh correlations found: {len(corr_results.high_correlations)}")
print("Recommendations:")
for rec in corr_results.recommendations[:3]:  # Show first 3
    print(f"  • {rec}")
```

## Next Steps

- **[API Reference](https://github.com/Ramku3639/datawhisk/blob/main/docs/api-reference.md)** - Detailed API documentation
- **[Tutorials](https://github.com/Ramku3639/datawhisk/tree/main/docs/tutorials)** - In-depth guides

---

**Questions?** Check out the [API Reference](https://github.com/Ramku3639/datawhisk/blob/main/docs/api-reference.md) or open an issue on [GitHub](https://github.com/Ramku3639/datawhisk/issues).
