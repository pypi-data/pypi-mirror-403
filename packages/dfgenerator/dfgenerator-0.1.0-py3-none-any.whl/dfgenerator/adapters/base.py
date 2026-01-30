"""Base adapter interface for schema conversion."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, List, Optional

from ..core import DEFAULT_FAKER_LOCALE, ColumnSpec, KeyRegistry


class SchemaAdapter(ABC):
    """
    Abstract base class for schema adapters.

    Adapters convert external schema formats (YAML, JSON Schema, etc.)
    into internal ColumnSpec representations that the core domain understands.
    """

    @abstractmethod
    def to_columns(
        self,
        schema: Any,
        *,
        faker_locale: str = DEFAULT_FAKER_LOCALE,
        seed: Optional[int] = None,
        registry: Optional[KeyRegistry] = None,
    ) -> List[ColumnSpec]:
        """
        Convert schema to column specifications.

        Args:
            schema: The schema definition (format depends on adapter)
            faker_locale: Locale for Faker providers
            seed: Random seed for deterministic generation
            registry: KeyRegistry for primary/foreign key management

        Returns:
            List of ColumnSpec objects
        """
        pass


__all__ = ["SchemaAdapter"]
