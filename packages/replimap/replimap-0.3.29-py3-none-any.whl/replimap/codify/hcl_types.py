"""
HCL Type Markers - Used by renderer to determine output format.

These marker classes tell the HCL renderer how to format values:
- HCLBlock: Block syntax without '=' (e.g., `vpc_config { ... }`)
- HCLMap: Map syntax with '=' (e.g., `tags = { ... }`)
- HCLJsonEncode: jsonencode() function call
- HCLSet: Set of blocks with deterministic sorting
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any


def _normalize_for_hash(value: Any) -> Any:
    """
    Recursively normalize nested structures for deterministic hashing.

    This ensures that:
    - Dict keys are sorted
    - List elements are sorted (when comparable)
    - Nested structures are recursively normalized

    Without this, lists like ["10.0.0.2", "10.0.0.1"] and ["10.0.0.1", "10.0.0.2"]
    would produce different hashes, causing phantom drifts in terraform plan.

    Args:
        value: Any value to normalize

    Returns:
        Normalized value suitable for deterministic serialization
    """
    if isinstance(value, dict):
        # Sort dict keys and recursively normalize values
        return {k: _normalize_for_hash(v) for k, v in sorted(value.items())}
    elif isinstance(value, (list, tuple)):
        # Recursively normalize list elements
        normalized = [_normalize_for_hash(v) for v in value]
        # Try to sort the list for deterministic ordering
        try:
            # Sort by JSON representation (handles mixed types)
            return sorted(
                normalized, key=lambda x: json.dumps(x, sort_keys=True, default=str)
            )
        except TypeError:
            # If sorting fails (incomparable types), return in original order
            return normalized
    return value


@dataclass
class HCLBlock:
    """
    Marker for HCL block syntax.

    Rendered as: key { ... } (no '=')

    Example:
        vpc_config {
          subnet_ids = ["subnet-123"]
        }
    """

    content: dict[str, Any]


@dataclass
class HCLMap:
    """
    Marker for HCL map syntax.

    Rendered as: key = { ... }

    Example:
        tags = {
          Name = "my-resource"
        }
    """

    content: dict[str, Any]


@dataclass
class HCLJsonEncode:
    """
    Marker for jsonencode() call.

    Rendered as: key = jsonencode({...})

    Example:
        policy = jsonencode({
          Version = "2012-10-17"
          Statement = [...]
        })
    """

    content: dict | list


@dataclass
class HCLSet:
    """
    Marker for set of blocks that need deterministic sorting.

    Prevents phantom drifts in terraform plan by ensuring
    blocks are always rendered in the same order.

    Example:
        # These ingress blocks will always be in the same order
        ingress {
          from_port = 22
          ...
        }
        ingress {
          from_port = 443
          ...
        }
    """

    items: list[dict]
    sort_keys: list[str] | None = None

    def sorted_items(self) -> list[dict]:
        """
        Return normalized items sorted deterministically.

        Items are normalized using _normalize_for_hash() to ensure:
        - Dict keys are sorted alphabetically
        - List elements are sorted for deterministic ordering
        - Nested structures are recursively normalized

        This prevents phantom drifts when the same data is added with
        different internal ordering (e.g., cidr_blocks in different order).

        Returns:
            List of normalized items in deterministic order.
        """
        if not self.items:
            return []

        # Normalize all items first for deterministic output
        normalized_items = [_normalize_for_hash(item) for item in self.items]

        if self.sort_keys:
            # Sort by specified keys
            def sort_key(item: dict) -> tuple:
                return tuple(
                    json.dumps(item.get(k, ""), sort_keys=True, default=str)
                    for k in self.sort_keys
                )

            return sorted(normalized_items, key=sort_key)

        # Default: sort by content hash for deterministic ordering
        def hash_func(item: dict) -> str:
            serialized = json.dumps(item, sort_keys=True, default=str)
            return hashlib.md5(serialized.encode(), usedforsecurity=False).hexdigest()

        return sorted(normalized_items, key=hash_func)
