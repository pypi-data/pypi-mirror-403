datawhisk Documentation
======================

**A lightweight, practical utility library for data scientists and ML engineers.**

datawhisk provides a curated collection of analytical helpers designed to streamline common data science workflows. Built with speed, simplicity, and reliability in mind.

.. image:: https://badge.fury.io/py/datawhisk.svg
   :target: https://badge.fury.io/py/datawhisk
   :alt: PyPI version

.. image:: https://img.shields.io/pypi/pyversions/datawhisk.svg
   :target: https://pypi.org/project/datawhisk/
   :alt: Python Support

.. image:: https://img.shields.io/badge/License-MIT-yellow.svg
   :target: https://opensource.org/licenses/MIT
   :alt: License: MIT

Quick Start
-----------

Installation
~~~~~~~~~~~~

.. code-block:: bash

   pip install datawhisk

With visualization support:

.. code-block:: bash

   pip install datawhisk[viz]

Simple Example
~~~~~~~~~~~~~~

.. code-block:: python

   from datawhisk.analytical import optimize_memory, analyze_correlations, quick_eda
   import pandas as pd

   # Load your data
   df = pd.read_csv('your_data.csv')

   # Optimize memory usage
   df_optimized, report = optimize_memory(df, return_report=True)
   print(f"Memory reduced by {report.reduction_percent:.1f}%")

   # Analyze correlations
   results = analyze_correlations(df_optimized, target='price')
   print(results.recommendations)

   # Quick EDA
   eda_report = quick_eda(df_optimized, visualize=True)
   print(eda_report)

Why datawhisk?
-------------

🚀 **Fast**: Optimized implementations faster than manual approaches

🎯 **Practical**: Solves real problems data scientists face daily

🪶 **Lightweight**: Minimal dependencies, quick to install

📊 **Reliable**: 90%+ test coverage, production-ready

🧩 **Intuitive**: Clean APIs that "just work"

Key Features
------------

Analytical Helpers
~~~~~~~~~~~~~~~~~~

* **Memory Optimizer**: Automatically downcast dtypes and optimize memory usage
* **Correlation Analyzer**: Calculate correlations with VIF and multicollinearity detection
* **Quick EDA Reporter**: Fast statistical summaries with anomaly detection

User Guide
----------

.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   installation
   quickstart

.. toctree::
   :maxdepth: 2
   :caption: Tutorials

   tutorials/analytical_helpers_tutorial

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api/analytical

.. toctree::
   :maxdepth: 1
   :caption: Development

   contributing
   changelog

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`