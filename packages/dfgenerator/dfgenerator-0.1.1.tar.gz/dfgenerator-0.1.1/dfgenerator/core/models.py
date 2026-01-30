"""Core domain models for data generation."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, List, Optional, Sequence, Union

from .types import Row, ValueFactory


def _resolve(factory: ValueFactory, index: int) -> Any:
    """
    Resolve a value factory for the given row index.

    A factory can be a static value or a callable that receives the row index.
    """

    if callable(factory):
        return factory(index)
    return factory


@dataclass(frozen=True)
class ColumnSpec:
    """Describe a column and how to populate it."""

    name: str
    value: ValueFactory
    description: Optional[str] = None


class RowTemplate:
    """Generate rows based on column specifications."""

    def __init__(self, columns: Sequence[ColumnSpec], base: Optional[Row] = None):
        if not columns:
            raise ValueError("RowTemplate requires at least one column")
        self._columns = list(columns)
        self._base = dict(base or {})

    def build_rows(self, count: int) -> List[Row]:
        if count < 0:
            raise ValueError("count must be zero or positive")
        return [self._build_row(index) for index in range(count)]

    def _build_row(self, index: int) -> Row:
        row: Row = dict(self._base)
        for column in self._columns:
            row[column.name] = _resolve(column.value, index)
        return row


class DataSet:
    """
    Immutable collection of rows with helpers to export or convert them.
    """

    def __init__(self, rows: Iterable[Row], schema: Any = None):
        self._rows = [dict(row) for row in rows]
        self.schema = schema

    @property
    def rows(self) -> List[Row]:
        return [dict(row) for row in self._rows]

    def _fieldnames(self) -> List[str]:
        """
        Get field names in the order they first appear across all rows.

        Preserves the original column order from the schema/template.
        """
        seen: set[str] = set()
        ordered_names: List[str] = []
        for row in self._rows:
            for key in row.keys():
                if key not in seen:
                    seen.add(key)
                    ordered_names.append(key)
        return ordered_names

    def _normalized_rows(self) -> List[Row]:
        fieldnames = self._fieldnames()
        return [{field: row.get(field) for field in fieldnames} for row in self._rows]

    def to_spark(self, spark_session: Any):
        """
        Create a PySpark DataFrame using an existing SparkSession.
        """

        if spark_session is None:
            raise ValueError("spark_session must be provided for Spark export")
        if not hasattr(spark_session, "createDataFrame"):
            raise TypeError("spark_session does not look like a SparkSession")
        return spark_session.createDataFrame(self._rows, schema=self.schema)

    def to_pandas(self):
        """
        Convert to a pandas DataFrame if pandas is installed.
        """

        try:
            import pandas as pd  # type: ignore
        except ImportError as exc:  # pragma: no cover - environment dependent
            raise ImportError(
                "pandas is required for to_pandas(); install with `pip install pandas`"
            ) from exc
        return pd.DataFrame(self._rows)

    def to_file(
        self,
        path: Union[str, Path],
        fmt: Optional[str] = None,
        *,
        lines: bool = False,
    ) -> Path:
        """
        Persist rows to disk in CSV or JSON format.

        The format can be inferred from the file extension when ``fmt`` is not
        provided.
        """

        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        format_name = (fmt or target.suffix.lstrip(".")).lower()

        if format_name == "csv":
            self._write_csv(target)
        elif format_name == "json":
            self._write_json(target, lines=lines)
        else:
            raise ValueError(f"Unsupported format '{format_name}'")
        return target

    def _write_csv(self, path: Path) -> None:
        fieldnames = self._fieldnames()
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            for row in self._normalized_rows():
                writer.writerow(row)

    def _write_json(self, path: Path, *, lines: bool) -> None:
        with path.open("w", encoding="utf-8") as handle:
            if lines:
                for row in self._rows:
                    handle.write(json.dumps(row, default=str))
                    handle.write("\n")
            else:
                json.dump(self._rows, handle, indent=2, default=str)

    def preview(self, limit: int = 5) -> str:
        """Return a human-friendly preview for quick inspection."""
        return json.dumps(self._rows[:limit], indent=2, default=str)


__all__ = ["ColumnSpec", "RowTemplate", "DataSet"]
