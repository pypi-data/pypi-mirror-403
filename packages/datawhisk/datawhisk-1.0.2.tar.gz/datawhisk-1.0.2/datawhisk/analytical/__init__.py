"""
Analytical Helpers Module
=========================

This module provides utilities for data analysis, optimization, and
exploration.

Functions
---------
optimize_memory
    Optimize DataFrame memory usage through intelligent dtype casting.
analyze_correlations
    Analyze feature correlations with multicollinearity detection.
quick_eda
    Generate fast exploratory data analysis reports.
"""

from datawhisk.analytical.correlation_analyzer import (
    CorrelationResults,
    analyze_correlations,
)
from datawhisk.analytical.eda_reporter import EDAReport, quick_eda
from datawhisk.analytical.memory_optimizer import MemoryReport, optimize_memory

__all__ = [
    "optimize_memory",
    "MemoryReport",
    "analyze_correlations",
    "CorrelationResults",
    "quick_eda",
    "EDAReport",
]
