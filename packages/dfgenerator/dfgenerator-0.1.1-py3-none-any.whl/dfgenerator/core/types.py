"""Type definitions for dfgenerator."""

from typing import Any, Callable, Dict, Union

ValueFactory = Union[Any, Callable[[int], Any]]
Row = Dict[str, Any]

__all__ = ["ValueFactory", "Row"]
