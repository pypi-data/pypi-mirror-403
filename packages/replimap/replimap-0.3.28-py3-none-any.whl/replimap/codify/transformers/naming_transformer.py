"""
Minimal Naming Transformer - Generate HCL-safe resource names.

Rules:
- Replace spaces and special chars with underscores
- Ensure uniqueness (append counter on collision)
- NO random suffixes (preserve intent)
- Keep names readable and traceable to AWS console
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

from .base import BaseCodifyTransformer

if TYPE_CHECKING:
    from replimap.core.unified_storage import GraphEngineAdapter

logger = logging.getLogger(__name__)


class MinimalNamingTransformer(BaseCodifyTransformer):
    """
    Generate clean, HCL-safe resource names.

    Terraform resource names must:
    - Start with a letter or underscore
    - Contain only letters, digits, underscores, and hyphens
    - Be unique within their resource type

    This transformer ensures all resources have valid, unique names
    while keeping them readable and traceable to the AWS console.
    """

    name = "MinimalNamingTransformer"

    def __init__(self, preserve_original: bool = True) -> None:
        """
        Initialize the transformer.

        Args:
            preserve_original: If True, tries to preserve original names
        """
        self.preserve_original = preserve_original
        self._renamed_count = 0

    def transform(self, graph: GraphEngineAdapter) -> GraphEngineAdapter:
        """
        Generate HCL-safe names for all resources.

        Args:
            graph: The graph to transform

        Returns:
            The transformed graph
        """
        self._renamed_count = 0

        # Track used names per resource type for uniqueness
        used_names: dict[str, set[str]] = {}

        for resource in graph.iter_resources():
            resource_type = str(resource.resource_type)

            if resource_type not in used_names:
                used_names[resource_type] = set()

            # Generate base name
            base_name = self._generate_base_name(resource)

            # Ensure uniqueness
            unique_name = self._ensure_unique(base_name, used_names[resource_type])

            if resource.terraform_name != unique_name:
                old_name = resource.terraform_name
                resource.terraform_name = unique_name
                self._renamed_count += 1
                logger.debug(f"Renamed: {old_name} -> {unique_name}")

            used_names[resource_type].add(unique_name)

        if self._renamed_count > 0:
            logger.info(
                f"MinimalNamingTransformer: renamed {self._renamed_count} resources"
            )

        return graph

    def _generate_base_name(self, resource: object) -> str:
        """Generate a base name from the resource."""
        # Try to get a meaningful name in order of preference
        name = (
            getattr(resource, "tags", {}).get("Name")
            or getattr(resource, "original_name", None)
            or getattr(resource, "terraform_name", None)
            or getattr(resource, "id", "resource")
        )

        # Sanitize the name for HCL
        name = self._sanitize_name(name)

        # Ensure it starts with a letter or underscore
        if name and not (name[0].isalpha() or name[0] == "_"):
            name = f"r_{name}"

        # Handle empty case
        if not name:
            resource_id = getattr(resource, "id", "unknown")
            name = f"resource_{self._sanitize_name(resource_id)}"

        return name

    def _sanitize_name(self, name: str) -> str:
        """
        Sanitize a name for use as a Terraform identifier.

        Rules:
        - Replace non-alphanumeric chars (except _ and -) with underscores
        - Collapse multiple underscores
        - Convert to lowercase for consistency
        - Remove leading/trailing underscores
        """
        if not name:
            return ""

        # Replace non-alphanumeric with underscore
        result = ""
        for char in name:
            if char.isalnum() or char in "_-":
                result += char
            else:
                result += "_"

        # Collapse multiple underscores
        result = re.sub(r"_+", "_", result)

        # Remove leading/trailing underscores
        result = result.strip("_")

        # Convert to lowercase
        result = result.lower()

        return result

    def _ensure_unique(self, base: str, used: set[str]) -> str:
        """Ensure a name is unique within its type."""
        if base not in used:
            return base

        # Append numeric suffix
        counter = 1
        while f"{base}_{counter}" in used:
            counter += 1

        return f"{base}_{counter}"

    @property
    def renamed_count(self) -> int:
        """Return the number of resources renamed."""
        return self._renamed_count
