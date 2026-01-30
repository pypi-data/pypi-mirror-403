"""
Schema adapters for converting various schema formats to ColumnSpec definitions.

This package implements the Adapter pattern to support multiple schema input formats
(YAML configs, JSON Schema, etc.) while keeping the core domain logic independent.
"""

from .base import SchemaAdapter
from .json_schema_adapter import JSONSchemaAdapter
from .spark_adapter import SparkDataFrameAdapter
from .yaml_adapter import YAMLSchemaAdapter

__all__ = [
    "SchemaAdapter",
    "YAMLSchemaAdapter",
    "JSONSchemaAdapter",
    "SparkDataFrameAdapter",
]
