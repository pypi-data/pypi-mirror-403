"""
Public exports for the dfgenerator package.
"""

# Adapters
from .adapters import JSONSchemaAdapter, SchemaAdapter, SparkDataFrameAdapter, YAMLSchemaAdapter

# Core domain
from .core import (
    DEFAULT_FAKER_LOCALE,
    NAME,
    ColumnSpec,
    DataFrameBuilder,
    DataSet,
    KeyRegistry,
    Row,
    RowTemplate,
    ValueFactory,
    choices,
    default_registry,
    faker_value,
    foreign_key,
    primary_key,
    sequence,
    set_default_faker_locale,
)

# Inference
from .inference import build_from_inferred, infer_config_from_df, infer_config_from_file

# Loaders
from .loaders import (
    build_from_config,
    build_from_jsonschema,
    build_from_spark,
    infer_spark_schema,
    load_jsonschema_dataset,
    load_yaml_dataset,
)

# Presets
from .presets import build_from_preset, get_preset, list_presets

__all__ = [
    # Core
    "NAME",
    "DEFAULT_FAKER_LOCALE",
    "ValueFactory",
    "Row",
    "ColumnSpec",
    "RowTemplate",
    "DataSet",
    "DataFrameBuilder",
    "sequence",
    "choices",
    "faker_value",
    "set_default_faker_locale",
    "KeyRegistry",
    "primary_key",
    "foreign_key",
    "default_registry",
    # Loaders
    "build_from_config",
    "load_yaml_dataset",
    "build_from_jsonschema",
    "load_jsonschema_dataset",
    "build_from_spark",
    "infer_spark_schema",
    # Presets
    "build_from_preset",
    "get_preset",
    "list_presets",
    # Inference
    "infer_config_from_df",
    "infer_config_from_file",
    "build_from_inferred",
    # Adapters
    "SchemaAdapter",
    "YAMLSchemaAdapter",
    "JSONSchemaAdapter",
    "SparkDataFrameAdapter",
]
