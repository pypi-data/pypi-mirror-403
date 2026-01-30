"""
Core domain models and utilities for dfgenerator.

This package contains the fundamental building blocks for data generation.
"""

from .builders import DataFrameBuilder
from .constants import DEFAULT_FAKER_LOCALE, NAME
from .factories import choices, faker_value, sequence, set_default_faker_locale
from .keys import KeyRegistry, default_registry, foreign_key, primary_key
from .models import ColumnSpec, DataSet, RowTemplate
from .types import Row, ValueFactory

__all__ = [
    # Constants
    "NAME",
    "DEFAULT_FAKER_LOCALE",
    # Types
    "ValueFactory",
    "Row",
    # Models
    "ColumnSpec",
    "RowTemplate",
    "DataSet",
    # Builders
    "DataFrameBuilder",
    # Factories
    "sequence",
    "choices",
    "faker_value",
    "set_default_faker_locale",
    # Keys
    "KeyRegistry",
    "primary_key",
    "foreign_key",
    "default_registry",
]
