"""
Managed Resource Filter - Skip already-TF-managed resources.

If a resource ID exists in the provided Terraform state, exclude it.
This prevents conflicts when importing into existing configurations.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from .base import BaseCodifyTransformer

if TYPE_CHECKING:
    from replimap.core.unified_storage import GraphEngineAdapter

logger = logging.getLogger(__name__)


class ManagedResourceFilter(BaseCodifyTransformer):
    """
    Filter out resources already managed by Terraform.

    When adopting brownfield infrastructure, some resources may already
    be managed by existing Terraform configurations. This filter removes
    those resources to avoid state conflicts.
    """

    name = "ManagedResourceFilter"

    def __init__(self, managed_ids: set[str] | None = None) -> None:
        """
        Initialize the filter.

        Args:
            managed_ids: Set of resource IDs already managed by Terraform
        """
        self.managed_ids = managed_ids or set()
        self._skipped_count = 0

    def transform(self, graph: GraphEngineAdapter) -> GraphEngineAdapter:
        """
        Remove resources already in Terraform state.

        Args:
            graph: The graph to filter

        Returns:
            The filtered graph
        """
        if not self.managed_ids:
            logger.debug("ManagedResourceFilter: no managed IDs provided, skipping")
            return graph

        self._skipped_count = 0
        resources_to_remove: list[str] = []

        for resource in graph.iter_resources():
            if resource.id in self.managed_ids:
                resources_to_remove.append(resource.id)
                logger.debug(
                    f"Skipped managed: {resource.resource_type}.{resource.terraform_name}"
                )

        for resource_id in resources_to_remove:
            graph.remove_resource(resource_id)
            self._skipped_count += 1

        if self._skipped_count > 0:
            logger.info(
                f"ManagedResourceFilter: skipped {self._skipped_count} "
                "already-managed resources"
            )

        return graph

    @property
    def skipped_count(self) -> int:
        """Return the number of resources skipped."""
        return self._skipped_count

    @classmethod
    def from_terraform_state(cls, state_file: str) -> ManagedResourceFilter:
        """
        Create a filter from a Terraform state file.

        Args:
            state_file: Path to terraform.tfstate file

        Returns:
            Configured ManagedResourceFilter
        """
        import json
        from pathlib import Path

        managed_ids: set[str] = set()
        state_path = Path(state_file)

        if not state_path.exists():
            logger.warning(f"State file not found: {state_file}")
            return cls(managed_ids=set())

        try:
            with open(state_path) as f:
                state = json.load(f)

            # Extract resource IDs from state
            for resource in state.get("resources", []):
                for instance in resource.get("instances", []):
                    attributes = instance.get("attributes", {})
                    if "id" in attributes:
                        managed_ids.add(attributes["id"])

            logger.info(f"Loaded {len(managed_ids)} managed IDs from {state_file}")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse state file: {e}")
        except Exception as e:
            logger.error(f"Failed to read state file: {e}")

        return cls(managed_ids=managed_ids)
