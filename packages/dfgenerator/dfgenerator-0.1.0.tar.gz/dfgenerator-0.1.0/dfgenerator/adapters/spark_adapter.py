"""Spark DataFrame adapter for inferring schemas from existing Spark/Iceberg dataframes."""

from __future__ import annotations

import re
from typing import Any, Callable, List, Optional

from ..core import DEFAULT_FAKER_LOCALE, ColumnSpec, KeyRegistry, choices, faker_value, sequence
from .base import SchemaAdapter

# Regex patterns for inference
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
UUID_RE = re.compile(
    r"^[a-f0-9]{8}-[a-f0-9]{4}-[1-5][a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$",
    re.IGNORECASE,
)
PHONE_RE = re.compile(r"^[\d\-\+\s\(\)]{7,}$")


class SparkDataFrameAdapter(SchemaAdapter):
    """
    Adapter that infers column specifications from a Spark DataFrame.

    This adapter analyzes an existing Spark DataFrame (including Iceberg tables)
    and generates appropriate ColumnSpec objects to create similar test data.

    Features:
    - Infers data types from Spark schema
    - Detects common patterns (emails, UUIDs, phone numbers)
    - Handles low-cardinality columns as choices
    - Supports nested structures (StructType, ArrayType, MapType)
    - Works with Iceberg tables loaded as Spark DataFrames

    Example:
        >>> from pyspark.sql import SparkSession
        >>> spark = SparkSession.builder.getOrCreate()
        >>> df = spark.read.format("iceberg").load("db.users")
        >>>
        >>> adapter = SparkDataFrameAdapter()
        >>> columns = adapter.to_columns(df, rows=100, seed=42)
        >>> # Now use columns to generate test data
    """

    def to_columns(
        self,
        schema: Any,  # Spark DataFrame
        *,
        faker_locale: str = DEFAULT_FAKER_LOCALE,
        seed: Optional[int] = None,
        registry: Optional[KeyRegistry] = None,
        sample_size: int = 100,
        cardinality_threshold: int = 10,
    ) -> List[ColumnSpec]:
        """
        Infer column specifications from a Spark DataFrame.

        Args:
            schema: Spark DataFrame to analyze
            faker_locale: Locale for Faker providers
            seed: Random seed for deterministic generation
            registry: Optional KeyRegistry (not used for inference)
            sample_size: Number of rows to sample for inference (default: 100)
            cardinality_threshold: Max unique values to treat as choices (default: 10)

        Returns:
            List of ColumnSpec objects

        Raises:
            ImportError: If pyspark is not installed
            ValueError: If schema is not a Spark DataFrame
        """
        # Validate we have a Spark DataFrame
        try:
            from pyspark.sql import DataFrame as SparkDataFrame  # type: ignore[import-not-found]
        except ImportError as exc:
            raise ImportError(
                "pyspark is required for SparkDataFrameAdapter; "
                "install with `pip install pyspark`"
            ) from exc

        if not isinstance(schema, SparkDataFrame):
            raise ValueError(
                f"SparkDataFrameAdapter requires a Spark DataFrame, got {type(schema)}"
            )

        df = schema
        columns: List[ColumnSpec] = []

        # Sample data for inference
        sample_data = self._sample_dataframe(df, sample_size)

        # Analyze each field in the schema
        for field in df.schema.fields:
            col_name = field.name
            col_type = field.dataType

            # Get sample values for this column
            sample_values = [row[col_name] for row in sample_data if row[col_name] is not None]

            # Infer the appropriate value factory
            value_factory = self._infer_value_factory(
                col_name,
                col_type,
                sample_values,
                faker_locale=faker_locale,
                seed=seed,
                cardinality_threshold=cardinality_threshold,
            )

            # Create ColumnSpec
            columns.append(
                ColumnSpec(
                    name=col_name,
                    value=value_factory,
                    description=field.metadata.get("comment") if field.metadata else None,
                )
            )

        return columns

    def _sample_dataframe(self, df: Any, sample_size: int) -> List[Any]:
        """Sample rows from the DataFrame for analysis."""
        try:
            # Use limit for efficiency (avoids full scan)
            sampled = df.limit(sample_size).collect()
            return sampled
        except Exception:
            # Fallback: return empty list if sampling fails
            return []

    def _infer_value_factory(
        self,
        col_name: str,
        col_type: Any,
        sample_values: List[Any],
        *,
        faker_locale: str,
        seed: Optional[int],
        cardinality_threshold: int,
    ) -> Callable[[int], Any]:
        """
        Infer the appropriate value factory based on column name, type, and sample data.
        """
        from pyspark.sql import types as T

        # String types
        if isinstance(col_type, T.StringType):
            return self._infer_string_factory(
                col_name, sample_values, faker_locale, seed, cardinality_threshold
            )

        # Numeric types
        elif isinstance(col_type, (T.IntegerType, T.LongType, T.ShortType, T.ByteType)):
            return self._infer_integer_factory(col_name, sample_values, seed)

        elif isinstance(col_type, (T.FloatType, T.DoubleType, T.DecimalType)):
            return self._infer_float_factory(col_name, sample_values, faker_locale, seed)

        # Boolean
        elif isinstance(col_type, T.BooleanType):
            return choices([True, False])

        # Date/Timestamp
        elif isinstance(col_type, T.DateType):
            return faker_value("date_object", locale=faker_locale, seed=seed)

        elif isinstance(col_type, T.TimestampType):
            return faker_value("date_time", locale=faker_locale, seed=seed)

        # Complex types - return simple representations
        elif isinstance(col_type, T.ArrayType):
            # Return empty array or simple array based on element type
            return lambda idx: []

        elif isinstance(col_type, T.MapType):
            return lambda idx: {}

        elif isinstance(col_type, T.StructType):
            # Return empty dict for nested structs
            return lambda idx: {}

        # Binary
        elif isinstance(col_type, T.BinaryType):
            return faker_value("binary", locale=faker_locale, seed=seed, length=16)

        # Default: return None
        else:
            return lambda idx: None

    def _infer_string_factory(
        self,
        col_name: str,
        sample_values: List[Any],
        faker_locale: str,
        seed: Optional[int],
        cardinality_threshold: int,
    ) -> Callable[[int], Any]:
        """Infer value factory for string columns."""
        lname = col_name.lower()

        # Get first non-null sample for pattern matching
        sample = str(sample_values[0]) if sample_values else ""

        # Pattern-based inference
        if "email" in lname or (sample and EMAIL_RE.match(sample)):
            return faker_value("email", locale=faker_locale, seed=seed)

        if "first" in lname and "name" in lname:
            return faker_value("first_name", locale=faker_locale, seed=seed)

        if ("last" in lname and "name" in lname) or "surname" in lname:
            return faker_value("last_name", locale=faker_locale, seed=seed)

        if lname in {"name", "fullname", "full_name", "username", "user_name"}:
            return faker_value("name", locale=faker_locale, seed=seed)

        if "phone" in lname or "mobile" in lname or (sample and PHONE_RE.match(sample)):
            return faker_value("phone_number", locale=faker_locale, seed=seed)

        if "city" in lname or "town" in lname:
            return faker_value("city", locale=faker_locale, seed=seed)

        if "country" in lname:
            return faker_value("country", locale=faker_locale, seed=seed)

        if "state" in lname or "province" in lname:
            return faker_value("state", locale=faker_locale, seed=seed)

        if "postcode" in lname or "zipcode" in lname or "zip" in lname:
            return faker_value("postcode", locale=faker_locale, seed=seed)

        if "address" in lname or "street" in lname:
            return faker_value("street_address", locale=faker_locale, seed=seed)

        if "company" in lname or "organization" in lname:
            return faker_value("company", locale=faker_locale, seed=seed)

        if "job" in lname or "title" in lname or "position" in lname:
            return faker_value("job", locale=faker_locale, seed=seed)

        if "url" in lname or "website" in lname:
            return faker_value("url", locale=faker_locale, seed=seed)

        if "iban" in lname:
            return faker_value("iban", locale=faker_locale, seed=seed)

        if "uuid" in lname or (sample and UUID_RE.match(sample)):
            return faker_value("uuid4", locale=faker_locale, seed=seed)

        if "color" in lname or "colour" in lname:
            return faker_value("color_name", locale=faker_locale, seed=seed)

        if "description" in lname or "comment" in lname:
            return faker_value("text", locale=faker_locale, seed=seed, max_nb_chars=200)

        # Low cardinality -> use choices
        unique_values = list(dict.fromkeys([str(v) for v in sample_values if v]))
        if 0 < len(unique_values) <= cardinality_threshold:
            return choices(unique_values)

        # Default: random word
        return faker_value("word", locale=faker_locale, seed=seed)

    def _infer_integer_factory(
        self,
        col_name: str,
        sample_values: List[Any],
        seed: Optional[int],
    ) -> Callable[[int], Any]:
        """Infer value factory for integer columns."""
        lname = col_name.lower()

        # ID columns use sequence
        if "id" in lname or lname.endswith("_id") or lname.startswith("id_"):
            if sample_values:
                start = min(int(v) for v in sample_values if v is not None)
            else:
                start = 1
            return sequence(start=start, step=1)

        # Age columns
        if "age" in lname:
            return faker_value("pyint", seed=seed, min_value=18, max_value=100)

        # Year columns
        if "year" in lname:
            return faker_value("pyint", seed=seed, min_value=1900, max_value=2030)

        # Count/quantity columns
        if any(word in lname for word in ["count", "quantity", "qty", "amount", "total"]):
            return faker_value("pyint", seed=seed, min_value=0, max_value=1000)

        # Default: sequence starting from min value
        if sample_values:
            start = min(int(v) for v in sample_values if v is not None)
        else:
            start = 1
        return sequence(start=start, step=1)

    def _infer_float_factory(
        self,
        col_name: str,
        sample_values: List[Any],
        faker_locale: str,
        seed: Optional[int],
    ) -> Callable[[int], Any]:
        """Infer value factory for float columns."""
        lname = col_name.lower()

        # Price/cost/amount columns
        if any(word in lname for word in ["price", "cost", "amount", "total", "fee"]):
            return faker_value(
                "pyfloat",
                locale=faker_locale,
                seed=seed,
                left_digits=3,
                right_digits=2,
                positive=True,
            )

        # Percentage/rate columns
        if any(word in lname for word in ["rate", "percent", "ratio"]):
            return faker_value(
                "pyfloat",
                locale=faker_locale,
                seed=seed,
                left_digits=2,
                right_digits=2,
                positive=True,
                min_value=0,
                max_value=100,
            )

        # Score columns
        if "score" in lname or "rating" in lname:
            return faker_value(
                "pyfloat",
                locale=faker_locale,
                seed=seed,
                left_digits=1,
                right_digits=2,
                positive=True,
                min_value=0,
                max_value=10,
            )

        # Coordinate columns
        if "lat" in lname or "latitude" in lname:
            return faker_value("latitude", locale=faker_locale, seed=seed)

        if "lon" in lname or "lng" in lname or "longitude" in lname:
            return faker_value("longitude", locale=faker_locale, seed=seed)

        # Default: generic float
        return faker_value(
            "pyfloat",
            locale=faker_locale,
            seed=seed,
            left_digits=2,
            right_digits=2,
        )


__all__ = ["SparkDataFrameAdapter"]
