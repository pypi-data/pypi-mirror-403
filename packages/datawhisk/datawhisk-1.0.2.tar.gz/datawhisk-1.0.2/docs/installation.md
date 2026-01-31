# Installation Guide

This guide will help you install datawhisk and set up your environment.

## Requirements

- **Python**: 3.8 or higher
- **Operating System**: Windows, macOS, or Linux

### Core Dependencies

datawhisk has minimal dependencies:

- `numpy >= 1.20.0`
- `pandas >= 1.3.0`
- `scipy >= 1.7.0`

### Optional Dependencies

For visualization support:
- `matplotlib >= 3.3.0`
- `seaborn >= 0.11.0`

## Installation Methods

### Using pip (Recommended)

Install the latest stable version from PyPI:

```bash
pip install datawhisk
```

### With Visualization Support

To include optional visualization dependencies:

```bash
pip install datawhisk[viz]
```

### Development Installation

For contributing or development:

```bash
# Clone the repository
git clone https://github.com/Ramku3639/datawhisk.git
cd datawhisk

# Install in editable mode with development dependencies
pip install -e ".[dev]"
```

### From Source

Install the latest development version directly from GitHub:

```bash
pip install git+https://github.com/Ramku3639/datawhisk.git
```

## Verifying Installation

After installation, verify that datawhisk is correctly installed:

```python
import datawhisk
print(datawhisk.__version__)
```

You should see the version number printed without any errors.

### Quick Test

Run a quick test to ensure everything works:

```python
from datawhisk.analytical import optimize_memory
import pandas as pd

# Create a test DataFrame
df = pd.DataFrame({'col': range(1000)})

# Optimize memory
optimized_df, report = optimize_memory(df, return_report=True)

print(f"Memory reduced by {report.reduction_percent:.1f}%")
```

## Platform-Specific Notes

### Windows

No special configuration required. Works with both Command Prompt and PowerShell.

### macOS

If you encounter issues with scipy installation, you may need to install additional dependencies:

```bash
brew install openblas
pip install datawhisk
```

### Linux

Most distributions work out of the box. For Ubuntu/Debian:

```bash
# Install system dependencies (if needed)
sudo apt-get update
sudo apt-get install python3-dev

# Install datawhisk
pip install datawhisk
```

## Virtual Environments

We recommend using virtual environments to avoid dependency conflicts:

### Using venv

```bash
# Create virtual environment
python -m venv datawhisk-env

# Activate (Windows)
datawhisk-env\Scripts\activate

# Activate (macOS/Linux)
source datawhisk-env/bin/activate

# Install datawhisk
pip install datawhisk
```

### Using conda

```bash
# Create conda environment
conda create -n datawhisk-env python=3.9

# Activate environment
conda activate datawhisk-env

# Install datawhisk
pip install datawhisk
```

## Troubleshooting

### Import Errors

If you encounter import errors:

1. Ensure you're using Python 3.8 or higher:
   ```bash
   python --version
   ```

2. Verify datawhisk is installed:
   ```bash
   pip show datawhisk
   ```

3. Check for conflicting packages:
   ```bash
   pip list | grep -E "numpy|pandas|scipy"
   ```

### Dependency Conflicts

If you have dependency conflicts:

```bash
# Upgrade pip
pip install --upgrade pip

# Reinstall datawhisk
pip install --upgrade --force-reinstall datawhisk
```

### Permission Errors

On Linux/macOS, if you encounter permission errors:

```bash
# Use --user flag
pip install --user datawhisk

# Or use sudo (not recommended)
sudo pip install datawhisk
```

## Upgrading

To upgrade to the latest version:

```bash
pip install --upgrade datawhisk
```

## Uninstalling

To remove datawhisk:

```bash
pip uninstall datawhisk
```

## Next Steps

Now that you have datawhisk installed, check out the [Quick Start Guide](quickstart.md) to begin using it!

---

**Need help?** Open an issue on our [GitHub repository](https://github.com/Ramku3639/datawhisk/issues).
