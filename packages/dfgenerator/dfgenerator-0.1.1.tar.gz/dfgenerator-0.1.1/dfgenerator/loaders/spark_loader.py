"""Spark DataFrame loader for building test datasets from existing Spark/Iceberg dataframes."""

from __future__ import annotations

from typing import Any, Optional

from ..core.builders import DataFrameBuilder
from ..core.constants import DEFAULT_FAKER_LOCALE
from ..core.keys import KeyRegistry
from ..core.models import DataSet, RowTemplate


def build_from_spark(
    spark_df: Any,
    *,
    rows: int = 10,
    faker_locale: str = DEFAULT_FAKER_LOCALE,
    seed: Optional[int] = None,
    registry: Optional[KeyRegistry] = None,
    sample_size: int = 100,
    cardinality_threshold: int = 10,
) -> DataSet:
    """
    Build a test dataset by inferring schema from an existing Spark DataFrame.

    This function analyzes a Spark DataFrame (including Iceberg tables) and generates
    similar test data with the same structure. Perfect for creating test fixtures
    from production data schemas.

    Args:
        spark_df: Spark DataFrame to analyze (can be from Iceberg, Parquet, etc.)
        rows: Number of rows to generate in the test dataset
        faker_locale: Locale for Faker providers (e.g., 'en_US', 'fr_FR')
        seed: Random seed for deterministic generation
        registry: Optional KeyRegistry for primary/foreign keys
        sample_size: Number of rows to sample from source for inference (default: 100)
        cardinality_threshold: Max unique values to treat as choices (default: 10)

    Returns:
        DataSet with generated test data matching the source schema

    Raises:
        ImportError: If pyspark is not installed
        ValueError: If spark_df is not a valid Spark DataFrame

    Example:
        >>> from pyspark.sql import SparkSession
        >>> spark = SparkSession.builder.getOrCreate()
        >>>
        >>> # Load from Iceberg
        >>> prod_df = spark.read.format("iceberg").load("prod.users")
        >>>
        >>> # Generate test data with same schema
        >>> test_data = build_from_spark(prod_df, rows=100, seed=42)
        >>>
        >>> # Export to various formats
        >>> test_data.to_file("test_users.csv")
        >>> test_df = test_data.to_spark(spark)
        >>> test_pandas = test_data.to_pandas()

    Example with multiple related tables:
        >>> # Generate test data for related tables
        >>> registry = KeyRegistry()
        >>>
        >>> # Generate users (with primary keys)
        >>> users_df = spark.read.format("iceberg").load("prod.users")
        >>> test_users = build_from_spark(users_df, rows=50, seed=42, registry=registry)
        >>>
        >>> # Generate orders (with foreign keys to users)
        >>> orders_df = spark.read.format("iceberg").load("prod.orders")
        >>> test_orders = build_from_spark(orders_df, rows=200, seed=43, registry=registry)
    """
    from ..adapters.spark_adapter import SparkDataFrameAdapter

    if rows < 0:
        raise ValueError("rows must be zero or positive")

    # Use adapter to infer columns from Spark DataFrame
    adapter = SparkDataFrameAdapter()
    columns = adapter.to_columns(
        spark_df,
        faker_locale=faker_locale,
        seed=seed,
        registry=registry,
        sample_size=sample_size,
        cardinality_threshold=cardinality_threshold,
    )

    # Build dataset
    template = RowTemplate(columns)
    return DataFrameBuilder().from_template(template, rows).build()


def infer_spark_schema(
    spark_df: Any,
    *,
    faker_locale: str = DEFAULT_FAKER_LOCALE,
    seed: Optional[int] = None,
    sample_size: int = 100,
    cardinality_threshold: int = 10,
) -> dict:
    """
    Infer a YAML-compatible configuration from a Spark DataFrame.

    This function analyzes a Spark DataFrame and returns a configuration dict
    that can be saved as YAML and used with build_from_config().

    Args:
        spark_df: Spark DataFrame to analyze
        faker_locale: Locale for Faker providers
        seed: Random seed for deterministic generation
        sample_size: Number of rows to sample for inference
        cardinality_threshold: Max unique values to treat as choices

    Returns:
        Dictionary with YAML-compatible configuration

    Example:
        >>> import yaml
        >>> from pyspark.sql import SparkSession
        >>>
        >>> spark = SparkSession.builder.getOrCreate()
        >>> df = spark.read.format("iceberg").load("prod.users")
        >>>
        >>> # Infer config
        >>> config = infer_spark_schema(df, seed=42)
        >>>
        >>> # Save as YAML for reuse
        >>> with open("users_schema.yaml", "w") as f:
        ...     yaml.dump(config, f)
        >>>
        >>> # Later, load and generate data
        >>> from dfgenerator import load_yaml_dataset
        >>> test_data = load_yaml_dataset("users_schema.yaml")
    """
    from ..adapters.spark_adapter import SparkDataFrameAdapter

    adapter = SparkDataFrameAdapter()
    columns = adapter.to_columns(
        spark_df,
        faker_locale=faker_locale,
        seed=seed,
        sample_size=sample_size,
        cardinality_threshold=cardinality_threshold,
    )

    # Convert ColumnSpec objects to YAML-compatible dicts
    column_configs = []
    for col in columns:
        col_dict = {"name": col.name}

        # Extract the value factory details
        # This is a simplified representation - actual implementation
        # would need to inspect the factory to determine its type
        if col.description:
            col_dict["description"] = col.description

        # Note: Full implementation would reverse-engineer the factory
        # For now, we just note that it's a factory
        col_dict["value"] = "inferred"

        column_configs.append(col_dict)

    return {
        "rows": 10,
        "faker_locale": faker_locale,
        "seed": seed,
        "columns": column_configs,
    }


__all__ = ["build_from_spark", "infer_spark_schema"]
