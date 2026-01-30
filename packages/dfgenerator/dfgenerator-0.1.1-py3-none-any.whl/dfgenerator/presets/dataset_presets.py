"""Built-in dataset presets to speed up test data creation."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Mapping, Optional

from ..core.keys import KeyRegistry, default_registry
from ..loaders.yaml_loader import build_from_config

PRESETS: Dict[str, Mapping[str, Any]] = {
    "consumers": {
        "rows": 5,
        "faker_locale": "en_US",
        "seed": 101,
        "base": {"source": "preset_consumers"},
        "columns": [
            {
                "name": "consumer_id",
                "primary_key": {"keyspace": "consumer", "sequence": {"start": 1, "step": 1}},
            },
            {"name": "first_name", "faker": "first_name"},
            {"name": "last_name", "faker": "last_name"},
            {"name": "email", "faker": "email"},
            {"name": "city", "choices": ["Paris", "Berlin", "Madrid"]},
        ],
    },
    "orders": {
        "rows": 8,
        "faker_locale": "en_US",
        "seed": 202,
        "base": {"source": "preset_orders"},
        "columns": [
            {"name": "order_id", "sequence": {"start": 1000, "step": 1}},
            {"name": "consumer_id", "foreign_key": {"keyspace": "consumer"}},
            {"name": "amount", "faker": "pyfloat", "kwargs": {"left_digits": 2, "right_digits": 2}},
            {"name": "currency", "value": "EUR"},
        ],
    },
    "products": {
        "rows": 5,
        "faker_locale": "en_US",
        "seed": 303,
        "base": {"source": "preset_products"},
        "columns": [
            {
                "name": "product_id",
                "primary_key": {"keyspace": "product", "sequence": {"start": 10}},
            },
            {"name": "name", "faker": "word"},
            {"name": "category", "choices": ["electronics", "books", "home", "sports"]},
            {"name": "price", "faker": "pyfloat", "kwargs": {"left_digits": 2, "right_digits": 2}},
        ],
    },
}


def list_presets() -> list[str]:
    """Return available preset names."""

    return sorted(PRESETS.keys())


def get_preset(name: str) -> Mapping[str, Any]:
    """Return a deep copy of the preset configuration."""

    if name not in PRESETS:
        raise KeyError(f"Unknown preset '{name}'. Available: {', '.join(list_presets())}")
    return deepcopy(PRESETS[name])


def build_from_preset(
    name: str,
    *,
    registry: Optional[KeyRegistry] = None,
    overrides: Optional[Mapping[str, Any]] = None,
):
    """
    Build a dataset from a named preset with optional shallow overrides.

    Supported overrides keys: rows, seed, faker_locale, base, schema, columns.
    For foreign-keyed datasets (e.g., orders), pass the same registry instance
    used for the related primary dataset (e.g., consumers).
    """

    config_dict = dict(get_preset(name))
    if overrides:
        for key in ["rows", "seed", "faker_locale", "base", "schema", "columns"]:
            if key in overrides:
                config_dict[key] = overrides[key]

    reg = registry or default_registry
    return build_from_config(config_dict, registry=reg)


__all__ = ["list_presets", "get_preset", "build_from_preset"]
