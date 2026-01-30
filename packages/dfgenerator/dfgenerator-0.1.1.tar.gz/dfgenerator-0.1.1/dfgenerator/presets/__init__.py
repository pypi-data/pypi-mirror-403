"""
Built-in dataset presets to speed up test data creation.
"""

from .dataset_presets import build_from_preset, get_preset, list_presets

__all__ = [
    "list_presets",
    "get_preset",
    "build_from_preset",
]
