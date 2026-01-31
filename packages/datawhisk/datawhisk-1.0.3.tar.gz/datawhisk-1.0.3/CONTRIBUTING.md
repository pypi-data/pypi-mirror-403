# Contributing to datawhisk

Thank you for your interest in contributing to datawhisk! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Code Style](#code-style)
- [Documentation](#documentation)
- [Submitting Changes](#submitting-changes)
- [Review Process](#review-process)

## Code of Conduct

We are committed to providing a welcoming and inclusive environment. Please be respectful and professional in all interactions.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/Ramku3639/datawhisk.git
   cd datawhisk
   ```
3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/originalowner/datawhisk.git
   ```

## Development Setup

### Prerequisites

- Python 3.8 or higher
- pip and virtualenv

### Setup Instructions

1. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install development dependencies**:
   ```bash
   pip install -e ".[dev]"
   ```

3. **Verify installation**:
   ```bash
   pytest
   ```

## Making Changes

### Branch Naming

Use descriptive branch names:
- `feature/add-new-utility` - New features
- `fix/memory-optimizer-bug` - Bug fixes
- `docs/update-readme` - Documentation changes
- `refactor/improve-performance` - Code refactoring

### Commit Messages

Follow these conventions:
- Use present tense ("Add feature" not "Added feature")
- Use imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit first line to 72 characters
- Reference issues and PRs liberally

Examples:
```
Add memory optimization for categorical columns

- Implement automatic category dtype conversion
- Add tests for edge cases
- Update documentation

Fixes #123
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/analytical/test_memory_optimizer.py

# Run with coverage
pytest --cov=datawhisk --cov-report=html

# Run specific test
pytest tests/analytical/test_memory_optimizer.py::test_basic_optimization
```

### Writing Tests

- Write tests for all new functionality
- Maintain minimum 90% code coverage
- Use descriptive test names: `test_<functionality>_<condition>_<expected_result>`
- Include edge cases and error conditions

Example:
```python
def test_memory_optimizer_handles_empty_dataframe():
    """Test that memory optimizer handles empty DataFrames gracefully."""
    df = pd.DataFrame()
    result, _ = optimize_memory(df)
    assert result.equals(df)
```

### Test Organization

```
tests/
├── analytical/
│   ├── test_memory_optimizer.py
│   ├── test_correlation_analyzer.py
│   └── test_eda_reporter.py
├── integration/
│   └── test_analytical_workflows.py
└── conftest.py  # Shared fixtures
```

## Code Style

### Python Style Guide

We follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) with these tools:

```bash
# Format code
black datawhisk tests

# Sort imports
isort datawhisk tests

# Check style
flake8 datawhisk tests

# Type checking
mypy datawhisk

# Lint code
pylint datawhisk
```

### Type Hints

All functions must include type hints:

```python
from typing import Optional, Tuple
import pandas as pd

def optimize_memory(
    df: pd.DataFrame,
    return_report: bool = False
) -> Tuple[pd.DataFrame, Optional[dict]]:
    """Optimize DataFrame memory usage."""
    ...
```

### Docstrings

Use NumPy-style docstrings:

```python
def analyze_correlations(
    df: pd.DataFrame,
    target: Optional[str] = None,
    threshold: float = 0.8,
    method: str = 'pearson'
) -> CorrelationResults:
    """
    Analyze correlations with multicollinearity detection.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame containing numeric features.
    target : str, optional
        Target variable name for feature selection, by default None.
    threshold : float, optional
        Correlation threshold for flagging high correlations, by default 0.8.
    method : {'pearson', 'spearman', 'kendall'}, optional
        Correlation method to use, by default 'pearson'.

    Returns
    -------
    CorrelationResults
        Object containing correlation matrix, VIF values, and recommendations.

    Raises
    ------
    ValueError
        If threshold is not between 0 and 1.
    TypeError
        If df is not a pandas DataFrame.

    Examples
    --------
    >>> results = analyze_correlations(df, target='price', threshold=0.9)
    >>> print(results.recommendations)
    ['Remove feature_X (VIF=12.3)', 'Keep feature_Y (VIF=2.1)']

    Notes
    -----
    The function automatically removes low-variance features before analysis.
    VIF (Variance Inflation Factor) values above 10 indicate high multicollinearity.
    """
    ...
```

## Documentation

### Building Documentation

```bash
cd docs
make html
# Open docs/_build/html/index.html in browser
```

### Documentation Standards

- Update docstrings for all new functions
- Add examples to docstrings
- Update API reference if adding new modules
- Create tutorial notebooks for complex features
- Update README.md for major changes

## Submitting Changes

### Pull Request Process

1. **Update your fork**:
   ```bash
   git fetch upstream
   git checkout main
   git merge upstream/main
   ```

2. **Create feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**:
   - Write code
   - Add tests
   - Update documentation

4. **Run quality checks**:
   ```bash
   black datawhisk tests
   isort datawhisk tests
   flake8 datawhisk tests
   mypy datawhisk
   pytest --cov=datawhisk
   ```

5. **Commit changes**:
   ```bash
   git add .
   git commit -m "Add your feature"
   ```

6. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Create Pull Request** on GitHub

### Pull Request Checklist

- [ ] Code follows style guidelines
- [ ] Tests added/updated and passing
- [ ] Documentation updated
- [ ] Type hints added
- [ ] CHANGELOG.md updated
- [ ] No merge conflicts
- [ ] All CI checks passing

## Review Process

1. **Automated Checks**: CI/CD pipeline runs automatically
2. **Code Review**: Maintainers review code quality and design
3. **Discussion**: Address feedback and make requested changes
4. **Approval**: At least one maintainer approval required
5. **Merge**: Maintainer merges after approval

### Review Timeline

- Simple fixes: 1-2 days
- New features: 3-7 days
- Major changes: 1-2 weeks

## Getting Help

- **Questions**: Open a [Discussion](https://github.com/Ramku3639/datawhisk/discussions)
- **Bugs**: Open an [Issue](https://github.com/Ramku3639/datawhisk/issues)
- **Security**: ramku3639@gmail.com

## Recognition

Contributors are recognized in:
- GitHub contributors page
- Release notes
- README.md acknowledgments

Thank you for contributing to datawhisk! 🎉