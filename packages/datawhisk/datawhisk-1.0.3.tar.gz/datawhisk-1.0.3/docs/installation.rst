Installation
============

Requirements
------------

datawhisk requires:

* Python 3.8 or higher
* numpy >= 1.20.0
* pandas >= 1.3.0
* scipy >= 1.7.0

Optional dependencies:

* matplotlib >= 3.3.0 (for visualizations)
* seaborn >= 0.11.0 (for enhanced visualizations)

Install from PyPI
-----------------

Basic Installation
~~~~~~~~~~~~~~~~~~

To install datawhisk with core dependencies only:

.. code-block:: bash

   pip install datawhisk

With Visualization Support
~~~~~~~~~~~~~~~~~~~~~~~~~~

To include optional visualization libraries:

.. code-block:: bash

   pip install datawhisk[viz]

Development Installation
~~~~~~~~~~~~~~~~~~~~~~~~

For development with all dependencies:

.. code-block:: bash

   pip install datawhisk[dev]

All Optional Dependencies
~~~~~~~~~~~~~~~~~~~~~~~~~

To install everything (visualization, development, documentation):

.. code-block:: bash

   pip install datawhisk[all]

Install from Source
-------------------

Clone and Install
~~~~~~~~~~~~~~~~~

.. code-block:: bash

   git clone https://github.com/yourusername/datawhisk.git
   cd datawhisk
   pip install -e ".[dev]"

This installs Data in "editable" mode, which is useful for development.

Verify Installation
-------------------

To verify that datawhisk is installed correctly:

.. code-block:: python

   import datawhisk
   print(datawhisk.__version__)

   from datawhisk.analytical import optimize_memory, analyze_correlations, quick_eda
   print("datawhisk installed successfully!")

Upgrading
---------

To upgrade to the latest version:

.. code-block:: bash

   pip install --upgrade datawhisk

Uninstalling
------------

To remove datawhisk:

.. code-block:: bash

   pip uninstall datawhisk

Virtual Environments
--------------------

It's recommended to use virtual environments to avoid dependency conflicts.

Using venv
~~~~~~~~~~

.. code-block:: bash

   python -m venv datawhisk-env
   source datawhisk-env/bin/activate  # On Windows: datawhisk-env\Scripts\activate
   pip install datawhisk

Using conda
~~~~~~~~~~~

.. code-block:: bash

   conda create -n datawhisk-env python=3.11
   conda activate datawhisk-env
   pip install datawhisk

Troubleshooting
---------------

Import Error
~~~~~~~~~~~~

If you encounter import errors, ensure all dependencies are installed:

.. code-block:: bash

   pip install --upgrade numpy pandas scipy

Permission Error
~~~~~~~~~~~~~~~~

If you get permission errors during installation, use:

.. code-block:: bash

   pip install --user datawhisk

Or use a virtual environment (recommended).

Dependency Conflicts
~~~~~~~~~~~~~~~~~~~~

If you have dependency conflicts, try creating a fresh virtual environment:

.. code-block:: bash

   python -m venv fresh-env
   source fresh-env/bin/activate
   pip install datawhisk

Platform-Specific Notes
-----------------------

Windows
~~~~~~~

On Windows, you may need to install Visual C++ Build Tools for some dependencies.

macOS
~~~~~

macOS users may need to install Xcode Command Line Tools:

.. code-block:: bash

   xcode-select --install

Linux
~~~~~

Most Linux distributions should work out of the box. Ensure you have Python development headers:

.. code-block:: bash

   # Ubuntu/Debian
   sudo apt-get install python3-dev

   # Fedora/RHEL
   sudo yum install python3-devel