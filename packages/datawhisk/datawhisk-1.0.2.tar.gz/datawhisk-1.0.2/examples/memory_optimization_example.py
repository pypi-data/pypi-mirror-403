"""
Memory Optimization Example
============================

This example demonstrates how to use datawhisk's memory optimizer to reduce
DataFrame memory usage automatically.
"""

import numpy as np
import pandas as pd

from datawhisk.analytical import optimize_memory


def create_sample_data():
    """Create a sample DataFrame with various data types."""
    np.random.seed(42)
    
    return pd.DataFrame({
        'customer_id': range(1000000),
        'age': np.random.randint(18, 80, 1000000),
        'purchase_count': np.random.randint(0, 100, 1000000),
        'total_spent': np.random.uniform(0, 10000, 1000000),
        'category': np.random.choice(['Electronics', 'Clothing', 'Food', 'Books'], 1000000),
        'region': np.random.choice(['North', 'South', 'East', 'West'], 1000000),
        'status': np.random.choice(['Active', 'Inactive'], 1000000),
    })


def example_basic_optimization():
    """Example 1: Basic memory optimization."""
    print("=" * 70)
    print("Example 1: Basic Memory Optimization")
    print("=" * 70)
    
    # Create sample data
    df = create_sample_data()
    
    print(f"\nOriginal DataFrame:")
    print(f"Shape: {df.shape}")
    print(f"Memory usage: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
    print(f"\nOriginal dtypes:")
    print(df.dtypes)
    
    # Optimize memory
    df_optimized, report = optimize_memory(df, return_report=True)
    
    print(f"\n{report}")
    print(f"\nOptimized dtypes:")
    print(df_optimized.dtypes)


def example_with_categorical_threshold():
    """Example 2: Custom categorical threshold."""
    print("\n" + "=" * 70)
    print("Example 2: Custom Categorical Threshold")
    print("=" * 70)
    
    df = create_sample_data()
    
    # Only convert columns with < 20% unique values to categorical
    df_optimized, report = optimize_memory(
        df,
        categorical_threshold=20,
        return_report=True
    )
    
    print(f"\nWith 20% threshold:")
    if report is not None:
        print(f"Memory reduced by {report.reduction_percent:.1f}%")
        print(f"\nOptimization details:")
        for col, details in report.optimization_details.items():
            print(f"  {col}: {details['original']} -> {details['optimized']}")


def example_aggressive_mode():
    """Example 3: Aggressive optimization mode."""
    print("\n" + "=" * 70)
    print("Example 3: Aggressive Optimization")
    print("=" * 70)
    
    df = pd.DataFrame({
        'precise_value': np.random.randn(100000) * 1e-6,
        'large_value': np.random.randn(100000) * 1e6,
    })
    
    print(f"Original dtypes: {df.dtypes.to_dict()}")
    print(f"Original memory: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
    
    # Aggressive mode converts float64 to float32
    df_optimized, report = optimize_memory(df, aggressive=True, return_report=True)
    
    print(f"\nAggressive optimization:")
    print(f"Optimized dtypes: {df_optimized.dtypes.to_dict()}")
    if report is not None:
        print(f"Memory reduced by {report.reduction_percent:.1f}%")


def example_inplace_optimization():
    """Example 4: In-place optimization."""
    print("\n" + "=" * 70)
    print("Example 4: In-place Optimization")
    print("=" * 70)
    
    df = create_sample_data()
    df_id_before = id(df)
    
    print(f"DataFrame ID before: {df_id_before}")
    
    # Optimize in-place (modifies original DataFrame)
    df_optimized, _ = optimize_memory(df, inplace=True)
    
    print(f"DataFrame ID after: {id(df_optimized)}")
    print(f"Same object: {id(df_optimized) == df_id_before}")


def example_undo_optimization():
    """Example 5: Undo optimization."""
    print("\n" + "=" * 70)
    print("Example 5: Undo Optimization")
    print("=" * 70)
    
    from datawhisk.analytical.memory_optimizer import undo_optimization
    
    df = pd.DataFrame({
        'col1': range(1000),
        'col2': ['A', 'B', 'C'] * 333 + ['A'],
    })
    
    print(f"Original dtypes: {df.dtypes.to_dict()}")
    
    # Optimize
    df_optimized, report = optimize_memory(df, return_report=True)
    print(f"Optimized dtypes: {df_optimized.dtypes.to_dict()}")
    
    # Undo optimization
    if report is not None:
        df_restored = undo_optimization(df_optimized, report.original_dtypes)
        print(f"Restored dtypes: {df_restored.dtypes.to_dict()}")


def example_real_world_scenario():
    """Example 6: Real-world e-commerce scenario."""
    print("\n" + "=" * 70)
    print("Example 6: Real-world E-commerce Scenario")
    print("=" * 70)
    
    # Simulate e-commerce transaction data
    np.random.seed(42)
    df = pd.DataFrame({
        'transaction_id': range(500000),
        'user_id': np.random.randint(0, 50000, 500000),
        'product_id': np.random.randint(0, 10000, 500000),
        'quantity': np.random.randint(1, 10, 500000),
        'price': np.random.uniform(10, 1000, 500000),
        'discount_pct': np.random.uniform(0, 30, 500000),
        'payment_method': np.random.choice(['Credit', 'Debit', 'PayPal', 'Cash'], 500000),
        'shipping_region': np.random.choice(['Domestic', 'International'], 500000),
        'device_type': np.random.choice(['Mobile', 'Desktop', 'Tablet'], 500000),
    })
    
    original_size = df.memory_usage(deep=True).sum() / 1024**2
    print(f"\nOriginal transaction data:")
    print(f"Rows: {len(df):,}")
    print(f"Columns: {len(df.columns)}")
    print(f"Memory: {original_size:.2f} MB")
    
    # Optimize
    df_optimized, report = optimize_memory(df, return_report=True)
    
    print(f"\nAfter optimization:")
    if report is not None:
        print(f"Memory: {report.optimized_memory_mb:.2f} MB")
        print(f"Saved: {report.reduction_mb:.2f} MB ({report.reduction_percent:.1f}%)")
        print(f"\nColumns optimized: {len(report.optimization_details)}")
        
        # Show cost savings
        # Assuming AWS pricing: $0.10 per GB-month for memory
        monthly_savings = (report.reduction_mb / 1024) * 0.10 * 24 * 30  # Per instance
        print(f"\nEstimated monthly savings (per instance): ${monthly_savings:.2f}")


if __name__ == "__main__":
    # Run all examples
    example_basic_optimization()
    example_with_categorical_threshold()
    example_aggressive_mode()
    example_inplace_optimization()
    example_undo_optimization()
    example_real_world_scenario()
    
    print("\n" + "=" * 70)
    print("All examples completed successfully!")
    print("=" * 70)