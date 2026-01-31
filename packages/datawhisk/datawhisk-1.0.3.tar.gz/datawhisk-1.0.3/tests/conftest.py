"""Shared fixtures and configuration for pytest."""

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def sample_dataframe():
    """Create a sample DataFrame for testing."""
    np.random.seed(42)
    return pd.DataFrame(
        {
            "int_col": np.random.randint(0, 100, 1000),
            "float_col": np.random.randn(1000),
            "category_col": np.random.choice(["A", "B", "C"], 1000),
            "string_col": ["text_" + str(i % 10) for i in range(1000)],
        }
    )


@pytest.fixture
def large_dataframe():
    """Create a large DataFrame for memory optimization testing."""
    np.random.seed(42)
    return pd.DataFrame(
        {
            "id": range(100000),
            "small_int": np.random.randint(0, 10, 100000),
            "medium_int": np.random.randint(0, 1000, 100000),
            "large_int": np.random.randint(0, 1000000, 100000),
            "float_val": np.random.randn(100000),
            "category": np.random.choice(["A", "B", "C", "D", "E"], 100000),
            "high_cardinality": ["item_" + str(i) for i in range(100000)],
        }
    )


@pytest.fixture
def dataframe_with_missing():
    """Create a DataFrame with missing values."""
    np.random.seed(42)
    df = pd.DataFrame(
        {
            "col1": np.random.randn(100),
            "col2": np.random.randn(100),
            "col3": np.random.randn(100),
        }
    )
    # Introduce missing values
    df.loc[np.random.choice(df.index, 20, replace=False), "col1"] = np.nan
    df.loc[np.random.choice(df.index, 30, replace=False), "col2"] = np.nan
    return df


@pytest.fixture
def dataframe_with_outliers():
    """Create a DataFrame with outliers."""
    np.random.seed(42)
    df = pd.DataFrame(
        {
            "normal": np.random.randn(100),
            "with_outliers": np.concatenate([np.random.randn(95), [100, 200, -150, 180, -175]]),
        }
    )
    return df


@pytest.fixture
def correlated_dataframe():
    """Create a DataFrame with correlated features."""
    np.random.seed(42)
    x1 = np.random.randn(100)
    x2 = x1 + np.random.randn(100) * 0.1  # Highly correlated with x1
    x3 = np.random.randn(100)  # Independent
    target = 2 * x1 + 3 * x3 + np.random.randn(100) * 0.5

    return pd.DataFrame(
        {
            "feature1": x1,
            "feature2": x2,
            "feature3": x3,
            "target": target,
        }
    )


@pytest.fixture
def empty_dataframe():
    """Create an empty DataFrame."""
    return pd.DataFrame()


@pytest.fixture
def single_column_dataframe():
    """Create a DataFrame with single column."""
    return pd.DataFrame({"col1": range(100)})


@pytest.fixture
def dataframe_all_numeric():
    """Create a DataFrame with only numeric columns."""
    np.random.seed(42)
    return pd.DataFrame(
        {
            "int1": np.random.randint(0, 100, 100),
            "int2": np.random.randint(0, 100, 100),
            "float1": np.random.randn(100),
            "float2": np.random.randn(100),
        }
    )


@pytest.fixture
def dataframe_all_categorical():
    """Create a DataFrame with only categorical columns."""
    return pd.DataFrame(
        {
            "cat1": np.random.choice(["A", "B", "C"], 100),
            "cat2": np.random.choice(["X", "Y", "Z"], 100),
            "cat3": np.random.choice(["Low", "Medium", "High"], 100),
        }
    )


@pytest.fixture
def dataframe_with_duplicates():
    """Create a DataFrame with duplicate rows."""
    df = pd.DataFrame(
        {
            "col1": [1, 2, 3, 1, 2, 3, 4, 5],
            "col2": ["A", "B", "C", "A", "B", "C", "D", "E"],
        }
    )
    return df


@pytest.fixture
def dataframe_constant_column():
    """Create a DataFrame with a constant column."""
    return pd.DataFrame(
        {
            "var_col": range(100),
            "const_col": [42] * 100,
        }
    )
