# Quick EDA Reporting Tutorial

Exploratory Data Analysis (EDA) is the first step in any data project. `quick_eda` generates a comprehensive snapshot of your data quality and characteristics in milliseconds.

## Generating a Standard Report

```python
import pandas as pd
import numpy as np
from datawhisk.analytical import quick_eda

# Create a messy dataset
df = pd.DataFrame({
    'age': [25, 30, 150, 22, np.nan],        # Outlier (150) and Missing
    'salary': [50000, 60000, 55000, 52000, 58000], 
    'group': ['A', 'A', 'A', 'A', 'A'],      # Zero variance (Constant)
    'id': range(5)                           # Unique key
})

# Run EDA
report = quick_eda(df)
```

## Interpreting the Report

The `EDAReport` object provides structured access to findings.

### 1. Data Quality Issues
Flags critical problems like duplicates or constant columns.

```python
print(report.data_quality_issues)
# Output: ['Column "group" has constant value "A"']
```

### 2. Missing Values
Shows breakdown of nulls.

```python
print(report.missing_analysis)
# {'age': 20.0}  (20% missing)
```

### 3. Outlier Detection
Default uses IQR (Interquartile Range) method (1.5x).

```python
print(report.outlier_analysis)
# {'age': 1}
```

## Customizing Checks (Modular EDA)

For large datasets, you might not want to run every check. Toggle them off for speed.

```python
# Only check for missing values and structure
fast_report = quick_eda(
    df, 
    check_outliers=False, 
    check_distribution=False,
    check_cardinality=False
)
```

## Visualizing Distributions

If `matplotlib` and `seaborn` are installed, you can generate plots instantly.

```python
quick_eda(df, visualize=True)
# This will plot histograms and boxplots for numeric features
```

## Handling Outliers

You can switch detection methods depending on your distribution assumptions.

- **IQR (Robust)**: Good for skewed data.
- **Z-Score**: Good for normal distributions.

```python
# Use Z-Score (3 standard deviations)
quick_eda(df, outlier_method='zscore', outlier_threshold=3.0)
```

## Recommendations

The report generates automated suggestions based on findings.

```python
print(report.recommendations)
# [
#   "Drop column 'group' (constant values)",
#   "Impute missing values in 'age' (20.0% missing)"
# ]
```
