"""YAML schema adapter for converting YAML configs to ColumnSpec definitions."""

from __future__ import annotations

from typing import Any, List, Mapping, Optional

from ..core import (
    DEFAULT_FAKER_LOCALE,
    ColumnSpec,
    KeyRegistry,
    choices,
    faker_value,
    foreign_key,
    primary_key,
    sequence,
)
from .base import SchemaAdapter


class YAMLSchemaAdapter(SchemaAdapter):
    """
    Adapter for YAML configuration format.

    Converts YAML config dictionaries to ColumnSpec objects.
    Supports: sequence, choices, faker, value, primary_key, foreign_key.
    """

    def to_columns(
        self,
        schema: Mapping[str, Any],
        *,
        faker_locale: str = DEFAULT_FAKER_LOCALE,
        seed: Optional[int] = None,
        registry: Optional[KeyRegistry] = None,
    ) -> List[ColumnSpec]:
        """Convert YAML config columns to ColumnSpec list."""
        from ..core import default_registry

        columns_cfg = schema.get("columns") or []
        if not columns_cfg:
            raise ValueError("YAML config must provide at least one column definition")

        reg = registry or default_registry
        columns: List[ColumnSpec] = []

        for col in columns_cfg:
            name = col.get("name")
            if not name:
                raise ValueError("column definition missing 'name'")

            columns.append(
                self._column_from_spec(
                    name,
                    col,
                    faker_locale=faker_locale,
                    seed=seed,
                    registry=reg,
                )
            )

        return columns

    def _column_from_spec(
        self,
        name: str,
        col: Mapping[str, Any],
        *,
        faker_locale: str,
        seed: Optional[int],
        registry: KeyRegistry,
    ) -> ColumnSpec:
        """Create a ColumnSpec from a YAML column definition."""
        description = col.get("description")
        kwargs = col.get("kwargs") or {}

        # Handle primary_key
        if "primary_key" in col:
            pk_conf = col.get("primary_key") or {}
            keyspace = pk_conf.get("keyspace") or name

            if "sequence" in pk_conf:
                seq_conf = pk_conf.get("sequence") or {}
                factory = sequence(
                    start=int(seq_conf.get("start", 1)),
                    step=int(seq_conf.get("step", 1)),
                )
            elif "faker" in pk_conf:
                factory = faker_value(
                    pk_conf["faker"],
                    locale=faker_locale,
                    seed=pk_conf.get("seed", seed),
                    **kwargs,
                )
            else:
                raise ValueError("primary_key requires 'sequence' or 'faker'")

            return ColumnSpec(
                name=name,
                value=primary_key(keyspace, factory, registry=registry),
                description=description,
            )

        # Handle foreign_key
        if "foreign_key" in col:
            fk_conf = col.get("foreign_key") or {}
            keyspace = fk_conf.get("keyspace") or name
            return ColumnSpec(
                name=name,
                value=foreign_key(keyspace, registry=registry),
                description=description,
            )

        # Handle faker
        if "faker" in col:
            return ColumnSpec(
                name=name,
                value=faker_value(col["faker"], locale=faker_locale, seed=seed, **kwargs),
                description=description,
            )

        # Handle sequence
        if "sequence" in col:
            seq_conf = col.get("sequence") or {}
            return ColumnSpec(
                name=name,
                value=sequence(
                    start=int(seq_conf.get("start", 1)),
                    step=int(seq_conf.get("step", 1)),
                ),
                description=description,
            )

        # Handle choices
        if "choices" in col:
            return ColumnSpec(
                name=name,
                value=choices(col["choices"]),
                description=description,
            )

        # Handle static value
        if "value" in col:
            return ColumnSpec(name=name, value=col["value"], description=description)

        raise ValueError(
            f"column '{name}' must specify one of: "
            "faker, sequence, choices, value, primary_key, or foreign_key"
        )


__all__ = ["YAMLSchemaAdapter"]
