Analytical Helpers API
======================

The analytical module provides utilities for data analysis, optimization, and exploration.

.. currentmodule:: datawhisk.analytical

Memory Optimizer
----------------

.. autofunction:: optimize_memory

.. autoclass:: MemoryReport
   :members:
   :undoc-members:

.. autofunction:: datawhisk.analytical.memory_optimizer.undo_optimization

Examples
~~~~~~~~

Basic usage:

.. code-block:: python

   from datawhisk.analytical import optimize_memory
   import pandas as pd

   df = pd.DataFrame({'col': range(1000000)})
   df_opt, report = optimize_memory(df, return_report=True)
   print(f"Memory reduced by {report.reduction_percent:.1f}%")

Correlation Analyzer
--------------------

.. autofunction:: analyze_correlations

.. autoclass:: CorrelationResults
   :members:
   :undoc-members:

Examples
~~~~~~~~

Basic correlation analysis:

.. code-block:: python

   from datawhisk.analytical import analyze_correlations

   results = analyze_correlations(df, target='price', threshold=0.8)
   print(results.recommendations)

With VIF scores:

.. code-block:: python

   results = analyze_correlations(df, calculate_vif=True)
   print(results.vif_scores)

Quick EDA Reporter
------------------

.. autofunction:: quick_eda

.. autoclass:: EDAReport
   :members:
   :undoc-members:

Examples
~~~~~~~~

Generate EDA report:

.. code-block:: python

   from datawhisk.analytical import quick_eda

   report = quick_eda(df, visualize=True)
   print(report)

Custom thresholds:

.. code-block:: python

   report = quick_eda(
       df,
       outlier_method='iqr',
       outlier_threshold=1.5,
       high_cardinality_threshold=50
   )

Module Contents
---------------

.. automodule:: datawhisk.analytical
   :members:
   :undoc-members:
   :show-inheritance:

Internal Functions
------------------

Memory Optimizer Internals
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: datawhisk.analytical.memory_optimizer
   :members:
   :private-members:
   :undoc-members:

Correlation Analyzer Internals
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: datawhisk.analytical.correlation_analyzer
   :members:
   :private-members:
   :undoc-members:

EDA Reporter Internals
~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: datawhisk.analytical.eda_reporter
   :members:
   :private-members:
   :undoc-members: