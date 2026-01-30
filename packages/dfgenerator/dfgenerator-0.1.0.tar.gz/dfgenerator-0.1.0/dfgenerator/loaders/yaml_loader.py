"""YAML configuration loader for building datasets."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Optional, Union

from ..core.builders import DataFrameBuilder
from ..core.constants import DEFAULT_FAKER_LOCALE
from ..core.keys import KeyRegistry
from ..core.models import DataSet, RowTemplate


def build_from_config(
    config: Mapping[str, Any], *, registry: Optional[KeyRegistry] = None
) -> DataSet:
    """
    Build a dataset from a Python mapping (e.g., loaded from YAML).

    Expected shape:
    {
        "rows": 10,
        "schema": null,
        "base": {"source": "yaml"},
        "faker_locale": "en_US",
        "seed": 42,
        "columns": [
            {"name": "id", "sequence": {"start": 1, "step": 1}},
            {"name": "city", "choices": ["Paris", "Berlin"]},
            {"name": "first_name", "faker": "first_name"},
            {"name": "age", "faker": "pyint", "kwargs": {"min_value": 18, "max_value": 65}},
            {"name": "note", "value": "static"},
        ],
    }
    """
    from ..adapters.yaml_adapter import YAMLSchemaAdapter

    rows = int(config.get("rows", 0))
    if rows < 0:
        raise ValueError("rows must be zero or positive")

    faker_locale = config.get("faker_locale", DEFAULT_FAKER_LOCALE)
    seed = config.get("seed")
    base = config.get("base") or {}
    schema = config.get("schema")

    # Use adapter to convert YAML config to columns
    adapter = YAMLSchemaAdapter()
    columns = adapter.to_columns(
        config,
        faker_locale=faker_locale,
        seed=seed,
        registry=registry,
    )

    template = RowTemplate(columns, base=base)
    return DataFrameBuilder().from_template(template, rows).build(schema=schema)


def load_yaml_dataset(path: Union[str, Path]) -> DataSet:
    """
    Load a dataset from a YAML configuration file.
    """

    try:
        import yaml  # type: ignore
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise ImportError(
            "pyyaml is required for load_yaml_dataset(); install with `pip install pyyaml`"
        ) from exc

    content = Path(path).read_text(encoding="utf-8")
    config = yaml.safe_load(content) or {}
    if not isinstance(config, Mapping):
        raise ValueError("YAML root must be a mapping/dictionary")
    return build_from_config(config)


__all__ = ["build_from_config", "load_yaml_dataset"]
