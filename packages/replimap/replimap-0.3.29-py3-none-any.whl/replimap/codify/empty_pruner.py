"""
Empty Pruner - Remove empty values to clean up generated code.

This runs after type casting to remove null, empty strings,
empty lists, and empty dicts that would clutter the HCL output.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class EmptyPruner:
    """Remove empty values from configuration."""

    def __init__(self, prune_values: list[Any] | None = None):
        self.prune_values = prune_values or ["", [], {}, None]

    def prune(
        self,
        config: dict,
        keep_empty_fields: set[str] | None = None,
    ) -> dict:
        """
        Remove empty values from configuration.

        Args:
            config: Configuration dictionary
            keep_empty_fields: Fields that should keep empty values

        Returns:
            Pruned configuration
        """
        keep_empty_fields = keep_empty_fields or set()
        result = {}

        for key, value in config.items():
            # Check if this field should keep empty values
            if key in keep_empty_fields:
                result[key] = value
                continue

            # Check if value is "empty"
            if self._is_empty(value):
                logger.debug(f"Pruned empty: {key}")
                continue

            # Recurse into nested dicts
            if isinstance(value, dict):
                pruned = self.prune(value, keep_empty_fields)
                if pruned or key in keep_empty_fields:
                    result[key] = pruned
            elif isinstance(value, list):
                pruned = [
                    self.prune(item, keep_empty_fields)
                    if isinstance(item, dict)
                    else item
                    for item in value
                    if not self._is_empty(item)
                ]
                if pruned or key in keep_empty_fields:
                    result[key] = pruned
            else:
                result[key] = value

        return result

    def _is_empty(self, value: Any) -> bool:
        """Check if value is considered empty."""
        if value is None:
            return True
        if value == "":
            return True
        if value == []:
            return True
        if value == {}:
            return True
        return False
