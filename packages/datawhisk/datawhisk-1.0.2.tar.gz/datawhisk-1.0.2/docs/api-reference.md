# API Reference

This section details the functions and classes available in datawhisk.

## Analytical Module

`datawhisk.analytical` provides correct analytical tools for common data science tasks.

### Memory Optimization

#### `optimize_memory`

```python
datawhisk.analytical.optimize_memory(
    df: pd.DataFrame,
    categorical_threshold: int = 50,
    return_report: bool = False,
    inplace: bool = False,
    aggressive: bool = False
) -> Union[pd.DataFrame, Tuple[pd.DataFrame, MemoryReport]]
```

Optimizes DataFrame memory usage by downcasting numeric types and converting object columns to categorical.

**Parameters:**

- **df** (*pd.DataFrame*): Input DataFrame to optimize.
- **categorical_threshold** (*int*, default=50): Maximum number of unique values for an object column to be converted to categorical type.
- **return_report** (*bool*, default=False): If True, returns a `MemoryReport` object containing optimization details.
- **inplace** (*bool*, default=False): If True, modifies the DataFrame in-place.
- **aggressive** (*bool*, default=False): If True, uses more aggressive downcasting (e.g., float64 -> float32) which may result in minor precision loss.

**Returns:**

- **pd.DataFrame**: The optimized DataFrame.
- **MemoryReport** (optional): Report containing memory usage statistics if `return_report` is True.

---

#### `MemoryReport`

A dataclass containing memory optimization results.

**Attributes:**

- **original_memory_mb** (*float*): Original memory usage in MB.
- **optimized_memory_mb** (*float*): Optimized memory usage in MB.
- **reduction_mb** (*float*): Total memory reduction in MB.
- **reduction_percent** (*float*): Percentage of memory reduced.
- **optimization_details** (*dict*): Dictionary mapping column names to their original and optimized types.
- **original_dtypes** (*dict*): Dictionary of original column data types.
- **optimized_dtypes** (*dict*): Dictionary of optimized column data types.

---

### Correlation Analysis

#### `analyze_correlations`

```python
datawhisk.analytical.analyze_correlations(
    df: pd.DataFrame,
    target: Optional[str] = None,
    threshold: float = 0.8,
    method: str = "pearson",
    calculate_vif: bool = True,
    variance_threshold: float = 0.01,
    return_details: bool = True
) -> CorrelationResults
```

Analyzes feature correlations and detects multicollinearity.

**Parameters:**

- **df** (*pd.DataFrame*): Input DataFrame containing numeric features.
- **target** (*str*, optional): Target variable name. If provided, target correlation analysis is included.
- **threshold** (*float*, default=0.8): Correlation limit (0.0 to 1.0) above which features are flagged as highly correlated.
- **method** (*str*, default="pearson"*): Correlation method. Options: `'pearson'`, `'spearman'`, `'kendall'`.
- **calculate_vif** (*bool*, default=True): Whether to calculate Variance Inflation Factor (VIF) scores.
- **variance_threshold** (*float*, default=0.01): Minimum variance required to keep a feature.
- **return_details** (*bool*, default=True): Whether to generate detailed textual recommendations.

**Returns:**

- **CorrelationResults**: Object containing analysis results.

---

#### `CorrelationResults`

A dataclass containing correlation analysis results.

**Attributes:**

- **correlation_matrix** (*pd.DataFrame*): The computed correlation matrix.
- **high_correlations** (*List[Tuple[str, str, float]]*): List of highly correlated feature pairs and their correlation coefficient.
- **vif_scores** (*pd.DataFrame*, optional): DataFrame containing VIF scores for each feature.
- **target_correlations** (*pd.Series*, optional): Correlations between features and the target variable.
- **recommendations** (*List[str]*): List of actionable recommendations for feature selection.
- **method** (*str*): The correlation method used.
- **target** (*str*, optional): The target variable name.

---

### EDA Reporting

#### `quick_eda`

```python
datawhisk.analytical.quick_eda(
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
    check_cardinality: bool = True
) -> EDAReport
```

Generates a fast confirmatory exploratory data analysis report.

**Parameters:**

- **df** (*pd.DataFrame*): Input DataFrame.
- **visualize** (*bool*, default=False): Whether to generate plots (requires matplotlib/seaborn).
- **outlier_method** (*str*, default="iqr"*): Method for outlier detection. Options: `'iqr'`, `'zscore'`.
- **outlier_threshold** (*float*, default=1.5): Threshold for detecting outliers (multiplier for IQR, sigma for Z-score).
- **high_cardinality_threshold** (*int*, default=50): Max unique values to consider for high cardinality.
- **check_*** flag parameters: Boolean flags to enable/disable specific checks for performance.

**Returns:**

- **EDAReport**: Object containing the EDA results.

---

#### `EDAReport`

A dataclass containing EDA results.

**Attributes:**

- **summary_stats** (*pd.DataFrame*): Descriptive statistics.
- **missing_analysis** (*Dict[str, float]*): Dictionary of columns and their missing value percentages.
- **outlier_analysis** (*Dict[str, int]*): Dictionary of columns and their outlier counts.
- **data_quality_issues** (*List[str]*): List of detected quality issues (e.g., constant columns, duplicates).
- **recommendations** (*List[str]*): List of suggestions for data cleaning/preprocessing.
- **shape** (*Tuple[int, int]*): Dimensions of the dataset.
- **dtypes** (*pd.Series*): Data types of columns.
- **high_cardinality_columns** (*List[str]*): List of columns exceeding cardinality threshold.
