"""
datawhisk: A Practical Utility Library for Data Scientists and ML Engineers
==========================================================================

datawhisk provides a curated collection of analytical helpers designed to
streamline common data science workflows.

Main Modules
------------
analytical
    Memory optimization, correlation analysis, and quick EDA tools.

Quick Start
-----------
>>> from datawhisk.analytical import (
...     optimize_memory, analyze_correlations, quick_eda
... )
>>> import pandas as pd
>>>
>>> # Optimize DataFrame memory
>>> df_optimized, report = optimize_memory(df, return_report=True)
>>>
>>> # Analyze correlations
>>> results = analyze_correlations(df, target='price')
>>>
>>> # Generate quick EDA report
>>> eda_report = quick_eda(df, visualize=True)
"""

from datawhisk.version import __version__

__all__ = ["__version__"]
