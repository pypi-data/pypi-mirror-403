"""JSON Schema loader for building datasets."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Optional, Union

from ..core.builders import DataFrameBuilder
from ..core.constants import DEFAULT_FAKER_LOCALE
from ..core.keys import KeyRegistry
from ..core.models import DataSet, RowTemplate


def build_from_jsonschema(
    schema: Mapping[str, Any],
    *,
    rows: int = 10,
    faker_locale: str = DEFAULT_FAKER_LOCALE,
    seed: Optional[int] = None,
    registry: Optional[KeyRegistry] = None,
) -> DataSet:
    """
    Build a dataset from a JSON Schema definition.

    Expected JSON Schema structure:
    {
        "type": "object",
        "properties": {
            "id": {"type": "integer"},
            "email": {"type": "string", "format": "email"},
            "age": {"type": "integer", "minimum": 18, "maximum": 65},
            "status": {"type": "string", "enum": ["active", "inactive"]},
            "score": {"type": "number", "minimum": 0.0, "maximum": 100.0}
        },
        "required": ["id", "email"]
    }

    Args:
        schema: JSON Schema definition (must have type="object" and properties)
        rows: Number of rows to generate
        faker_locale: Locale for Faker providers
        seed: Random seed for deterministic generation
        registry: Optional KeyRegistry for primary/foreign keys

    Returns:
        DataSet with generated rows
    """
    from ..adapters.json_schema_adapter import JSONSchemaAdapter

    if rows < 0:
        raise ValueError("rows must be zero or positive")

    # Validate schema structure
    if schema.get("type") != "object":
        raise ValueError("JSON Schema must have type='object' at root level")

    # Use adapter to convert JSON Schema to columns
    adapter = JSONSchemaAdapter()
    columns = adapter.to_columns(
        schema,
        faker_locale=faker_locale,
        seed=seed,
        registry=registry,
    )

    # Build dataset
    template = RowTemplate(columns)
    return DataFrameBuilder().from_template(template, rows).build()


def load_jsonschema_dataset(
    path: Union[str, Path],
    *,
    rows: int = 10,
    faker_locale: str = DEFAULT_FAKER_LOCALE,
    seed: Optional[int] = None,
) -> DataSet:
    """
    Load a dataset from a JSON Schema file.

    Args:
        path: Path to JSON Schema file
        rows: Number of rows to generate
        faker_locale: Locale for Faker providers
        seed: Random seed for deterministic generation

    Returns:
        DataSet with generated rows
    """
    content = Path(path).read_text(encoding="utf-8")
    schema = json.loads(content)

    if not isinstance(schema, Mapping):
        raise ValueError("JSON Schema root must be an object/dictionary")

    return build_from_jsonschema(
        schema,
        rows=rows,
        faker_locale=faker_locale,
        seed=seed,
    )


__all__ = ["build_from_jsonschema", "load_jsonschema_dataset"]
