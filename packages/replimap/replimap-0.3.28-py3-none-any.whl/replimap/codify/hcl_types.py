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
        """Return items sorted deterministically."""
        if not self.items:
            return []

        if self.sort_keys:
            # Sort by specified keys
            def sort_key(item: dict) -> tuple:
                return tuple(str(item.get(k, "")) for k in self.sort_keys)

            return sorted(self.items, key=sort_key)

        # Default: sort by content hash for deterministic ordering
        def hash_func(item: dict) -> str:
            serialized = json.dumps(item, sort_keys=True, default=str)
            return hashlib.md5(serialized.encode(), usedforsecurity=False).hexdigest()

        return sorted(self.items, key=hash_func)
