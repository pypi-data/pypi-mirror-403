Quick Start Guide
=================

This guide will help you get started with datawhisk's core features.

Memory Optimization
-------------------

Reduce DataFrame memory usage automatically:

Basic Usage
~~~~~~~~~~~

.. code-block:: python

   from datawhisk.analytical import optimize_memory
   import pandas as pd

   # Create or load your DataFrame
   df = pd.read_csv('large_data.csv')

   # Optimize memory
   df_optimized, report = optimize_memory(df, return_report=True)

   print(f"Memory reduced by {report.reduction_percent:.1f}%")
   print(f"Saved {report.reduction_mb:.2f} MB")

Advanced Options
~~~~~~~~~~~~~~~~

.. code-block:: python

   # Custom categorical threshold
   df_optimized = optimize_memory(
       df,
       categorical_threshold=30,  # Convert to category if < 30% unique
       aggressive=True,            # Also downcast float64 to float32
       inplace=False               # Create copy (default)
   )

Correlation Analysis
--------------------

Analyze feature correlations with multicollinearity detection:

Basic Analysis
~~~~~~~~~~~~~~

.. code-block:: python

   from datawhisk.analytical import analyze_correlations

   # Analyze correlations
   results = analyze_correlations(df, target='price')

   # View correlation matrix
   print(results.correlation_matrix)

   # Get recommendations
   for rec in results.recommendations:
       print(f"• {rec}")

With VIF Scores
~~~~~~~~~~~~~~~

.. code-block:: python

   # Include VIF for multicollinearity detection
   results = analyze_correlations(
       df,
       target='price',
       threshold=0.8,
       calculate_vif=True
   )

   # View VIF scores
   print(results.vif_scores)

   # Check high correlations
   for feat1, feat2, corr in results.high_correlations:
       print(f"{feat1} <-> {feat2}: {corr:.3f}")

Different Methods
~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Pearson (default - linear relationships)
   results_pearson = analyze_correlations(df, method='pearson')

   # Spearman (monotonic relationships)
   results_spearman = analyze_correlations(df, method='spearman')

   # Kendall (rank correlations)
   results_kendall = analyze_correlations(df, method='kendall')

Quick EDA
---------

Generate fast exploratory data analysis reports:

Basic Report
~~~~~~~~~~~~

.. code-block:: python

   from datawhisk.analytical import quick_eda

   # Generate EDA report
   report = quick_eda(df)

   # View summary
   print(report)

   # Access specific sections
   print("Missing values:", report.missing_analysis)
   print("Outliers:", report.outlier_analysis)
   print("Recommendations:", report.recommendations)

With Visualization
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Generate report with visualizations
   report = quick_eda(df, visualize=True)

Custom Thresholds
~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Custom outlier detection
   report = quick_eda(
       df,
       outlier_method='iqr',        # or 'zscore'
       outlier_threshold=1.5,       # IQR multiplier
       high_cardinality_threshold=50  # % threshold
   )

Complete Workflow
-----------------

Combine all features for a complete analysis workflow:

.. code-block:: python

   from datawhisk.analytical import optimize_memory, analyze_correlations, quick_eda
   import pandas as pd

   # 1. Load data
   df = pd.read_csv('data.csv')
   print(f"Original size: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")

   # 2. Optimize memory
   df_opt, mem_report = optimize_memory(df, return_report=True)
   print(f"Optimized size: {mem_report.optimized_memory_mb:.2f} MB")
   print(f"Saved: {mem_report.reduction_percent:.1f}%")

   # 3. Quick EDA
   eda_report = quick_eda(df_opt)
   print(f"\nData Quality Issues: {len(eda_report.data_quality_issues)}")
   print(f"Missing values: {len(eda_report.missing_analysis)} columns")

   # 4. Correlation analysis
   corr_results = analyze_correlations(
       df_opt,
       target='target_column',
       threshold=0.8
   )
   print(f"\nHigh correlations: {len(corr_results.high_correlations)}")
   print("Recommendations:")
   for rec in corr_results.recommendations:
       print(f"  • {rec}")

Common Use Cases
----------------

Kaggle Competition
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Fast initial exploration
   import pandas as pd
   from datawhisk.analytical import quick_eda, optimize_memory

   # Load competition data
   train = pd.read_csv('train.csv')

   # Quick overview
   report = quick_eda(train)
   print(report)

   # Optimize for faster iteration
   train_opt, _ = optimize_memory(train)

Production Pipeline
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Memory-efficient data processing
   def process_batch(df):
       # Optimize memory first
       df_opt, _ = optimize_memory(df, aggressive=True)
       
       # Quick quality check
       report = quick_eda(df_opt)
       if len(report.data_quality_issues) > 0:
           raise ValueError("Data quality issues detected")
       
       return df_opt

Feature Engineering
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Identify redundant features
   from datawhisk.analytical import analyze_correlations

   results = analyze_correlations(
       df,
       target='target',
       threshold=0.9,
       calculate_vif=True
   )

   # Remove highly correlated features
   features_to_remove = []
   for feat1, feat2, corr in results.high_correlations:
       features_to_remove.append(feat2)

   df_reduced = df.drop(columns=features_to_remove)

Next Steps
----------

* Check out the :doc:`tutorials/analytical_helpers_tutorial` for in-depth examples
* Read the :doc:`api/analytical` for detailed API documentation
* See the `examples/` directory for more use cases

Tips and Best Practices
------------------------

1. **Always optimize memory first** if working with large datasets
2. **Use quick_eda** before any modeling to catch data quality issues early
3. **Check VIF scores > 10** to identify multicollinearity problems
4. **Start with default parameters** and adjust based on your specific needs
5. **Combine functions** for comprehensive data analysis workflows

Getting Help
------------

* Check the API documentation for detailed parameter descriptions
* Look at example scripts in the `examples/` directory
* Open an issue on GitHub if you encounter problems
* Join discussions on GitHub Discussions