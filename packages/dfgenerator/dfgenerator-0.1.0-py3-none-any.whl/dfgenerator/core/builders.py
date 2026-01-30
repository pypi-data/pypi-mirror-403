"""Builders for constructing datasets."""

from __future__ import annotations

from typing import Any, Iterable, List

from .models import DataSet, RowTemplate
from .types import Row


class DataFrameBuilder:
    """Collect rows and produce a DataSet."""

    def __init__(self):
        self._rows: List[Row] = []

    def row(self, **values: Any) -> "DataFrameBuilder":
        """Add a single row using keyword arguments."""
        self._rows.append(dict(values))
        return self

    def extend(self, rows: Iterable[Row]) -> "DataFrameBuilder":
        """Add multiple pre-built rows."""
        for row in rows:
            self._rows.append(dict(row))
        return self

    def from_template(self, template: RowTemplate, count: int) -> "DataFrameBuilder":
        """Generate rows from a template."""
        self._rows.extend(template.build_rows(count))
        return self

    def build(self, schema: Any = None) -> "DataSet":
        """Return an immutable dataset with the collected rows."""
        return DataSet(self._rows, schema=schema)


__all__ = ["DataFrameBuilder"]
