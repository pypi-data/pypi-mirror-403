# Correlation Analysis Tutorial

Detecting multicollinearity and understanding feature relationships is crucial for building robust linear models. This tutorial demonstrates how to use `datawhisk` for smart correlation analysis.

## The Problem with Simple Correlation

Pandas' `df.corr()` gives you a raw matrix, but it lacks context:
- No automatic detection of "too high" correlations.
- No Variance Inflation Factor (VIF) calculation.
- Hard to read for wide datasets.

`analyze_correlations` solves this.

## Running an Analysis

```python
import pandas as pd
import numpy as np
from datawhisk.analytical import analyze_correlations

# Generate synthetic correlated data
np.random.seed(42)
N = 1000
x1 = np.random.randn(N)
x2 = x1 * 0.95 + np.random.randn(N) * 0.1  # Correlated with x1
x3 = np.random.randn(N)

df = pd.DataFrame({'feature_1': x1, 'feature_2': x2, 'feature_3': x3})

# Basic analysis
results = analyze_correlations(df, threshold=0.85)

print("=== Recommendations ===")
for rec in results.recommendations:
    print(f"- {rec}")
```

**Output:**
```
=== Recommendations ===
- Remove feature_2 (correlation with feature_1: 0.98)
```

## Understanding VIF (Variance Inflation Factor)

VIF measures how much the variance of an estimated regression coefficient increases if your predictors are correlated. 

- **VIF = 1**: No correlation.
- **VIF > 5-10**: High multicollinearity.

Datawhisk calculates this automatically:

```python
print(results.vif_scores)
```

Sample output:
```
     Feature       VIF
0  feature_1  9.876543
1  feature_2  9.831201
2  feature_3  1.002310
```

## Target-Aware Analysis

If you provide a target variable, the analysis becomes smarter. It calculates the correlation of each feature with the target to better inform you which feature in a correlated pair to keep (usually the one more correlated with the target).

```python
# Add a target variable
df['target'] = x1 * 3 + x3

results = analyze_correlations(df, target='target')

# The tool will typically recommend keeping 'feature_1' over 'feature_2' 
# if 'feature_1' has a higher correlation with 'target'.
```

## Choosing the Right Method

- **Pearson (Default)**: Linear relationships. Sensitive to outliers.
- **Spearman**: Monotonic relationships (rank-based). Good for ordinal data or non-linear associations.
- **Kendall**: Similar to Spearman but computationally more expensive; more robust for small samples.

```python
# Use Spearman for non-linear detection
results = analyze_correlations(df, method='spearman')
```

## Handling Non-Numeric Data

The analyzer automatically Filters for numeric columns, so you can pass your entire raw DataFrame safely.

```python
df['category'] = 'A'
results = analyze_correlations(df) # 'category' is ignored automatically
```
