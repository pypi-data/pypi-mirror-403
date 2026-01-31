# Memory Optimization Tutorial

In this tutorial, we'll explore how to efficiently reduce the memory footprint of your pandas DataFrames using `datawhisk`.

## Why Optimize Memory?

Pandas often uses inefficient data types by default (e.g., `int64` for small integers, `object` for strings). For large datasets, this can lead to:
- `MemoryError` crashes
- Slow computations
- Inability to fit data in RAM

`datawhisk.analytical.optimize_memory` provides an automated way to fix these issues.

## Basic Optimization

Let's start with a simple example.

```python
import pandas as pd
import numpy as np
from datawhisk.analytical import optimize_memory

# Create a sample DataFrame taking up ~7.6 MB
rows = 100_000
df = pd.DataFrame({
    'small_int': np.random.randint(0, 100, size=rows),       # Could be int8
    'large_int': np.random.randint(0, 10000, size=rows),     # Could be int16
    'float_val': np.random.randn(rows),                      # Standard float64
    'category_col': np.random.choice(['A', 'B', 'C'], rows)  # Strings (object)
})

print(f"Original Memory: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")

# Run optimization
df_opt, report = optimize_memory(df, return_report=True)

print(f"Optimized Memory: {report.optimized_memory_mb:.2f} MB")
print(f"Reduction: {report.reduction_percent:.1f}%")
```

## Understanding the Transformations

The optimizer applies several strategies:

1. **Integer Downcasting**: 
   - `int64` -> `int8`, `int16`, or `int32` depending on the range of values.
   - Unsigned integers (`uint8`, etc.) are used where appropriate.

2. **Float Downcasting**:
   - `float64` -> `float32` (optional, via `aggressive=True`).
   
3. **Categorical Encoding**:
   - String `object` columns with low cardinality (few unique values) represent repetitive data. Converting these to `category` dtype saves massive amounts of memory.

## Optimizing for High Cardinatlity

You can control the threshold for categorical conversion.

```python
# Create data with more unique values
df = pd.DataFrame({
    'status': np.random.choice([f'state_{i}' for i in range(100)], 10000)
})

# By default, threshold is 50. Increase it to capture this column:
df_opt = optimize_memory(df, categorical_threshold=150)

print(df_opt.dtypes)
# status    category
```

## Aggressive Optimization

If you are willing to embrace a small loss of precision (e.g., for machine learning input scaling), use `aggressive=True` to convert 64-bit floats to 32-bit.

```python
df_opt = optimize_memory(df, aggressive=True)
# float64 columns become float32
```

## In-place Modification

For extremely large datasets where creating a copy would crash memory, transform the DataFrame in-place.

```python
optimize_memory(df, inplace=True)
# df is now modified directly
```

## Best Practices

1. **Optimize Early**: Apply optimization immediately after loading data (e.g., `pd.read_csv`).
2. **Be Careful with Float32**: Some high-precision calculations might suffer accumulation errors.
3. **Save Optimized Types**: If you save to Parquet or Pickle, the optimized types are preserved. CSVs lose type information.
