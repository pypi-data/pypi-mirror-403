"""
Default Resource Filter - Skip AWS default resources.

AWS creates default resources in every account that:
1. Cannot be deleted
2. Have special behavior
3. Cause state conflicts when imported

Skip: default VPC, default SG, default Route Table, default NACL
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING

from .base import BaseCodifyTransformer

if TYPE_CHECKING:
    from replimap.core.models import ResourceNode
    from replimap.core.unified_storage import GraphEngineAdapter

logger = logging.getLogger(__name__)


class DefaultResourceFilter(BaseCodifyTransformer):
    """
    Filter out AWS default resources that cause import conflicts.

    Default resources (default VPC, default security group, etc.) should not
    be imported into Terraform as they have special behavior and cannot be
    deleted or fully managed by Terraform.
    """

    name = "DefaultResourceFilter"

    # Patterns for identifying default resources
    # Each tuple is (terraform_type, check_function)
    # 🚨 v3.7.18 FIX: Check both snake_case and PascalCase for is_default
    # Scanner stores as snake_case, but AWS API returns PascalCase
    # 🚨 v3.7.20 FIX: Added aws_db_subnet_group "default" and ASG-managed instances
    SKIP_PATTERNS: list[tuple[str, Callable[[ResourceNode], bool]]] = [
        (
            "aws_vpc",
            lambda r: r.config.get("is_default", r.config.get("IsDefault", False))
            is True,
        ),
        (
            "aws_security_group",
            lambda r: r.config.get("GroupName") == "default"
            or r.config.get("group_name") == "default",
        ),
        (
            "aws_route_table",
            lambda r: _is_main_route_table(r),
        ),
        (
            "aws_network_acl",
            lambda r: r.config.get("is_default", r.config.get("IsDefault", False))
            is True,
        ),
        # v3.7.20: Skip AWS default db_subnet_group (AWS-managed, can't be changed)
        (
            "aws_db_subnet_group",
            lambda r: (r.config.get("name") or r.config.get("Name", "")).lower()
            == "default",
        ),
        # v3.7.20: Skip EC2 instances managed by ASG (have launch_template block)
        # These are ephemeral and should be managed via ASG, not directly
        (
            "aws_instance",
            lambda r: _is_asg_managed_instance(r),
        ),
    ]

    def __init__(self, skip_defaults: bool = True) -> None:
        """
        Initialize the filter.

        Args:
            skip_defaults: Whether to filter out default resources
        """
        self.skip_defaults = skip_defaults
        self._skipped_count = 0

    def transform(self, graph: GraphEngineAdapter) -> GraphEngineAdapter:
        """
        Remove default AWS resources from the graph.

        Args:
            graph: The graph to filter

        Returns:
            The filtered graph
        """
        if not self.skip_defaults:
            logger.debug("DefaultResourceFilter: skipping disabled")
            return graph

        self._skipped_count = 0
        resources_to_remove: list[str] = []

        for resource in graph.iter_resources():
            if self._is_default_resource(resource):
                resources_to_remove.append(resource.id)
                logger.debug(
                    f"Skipped default: {resource.resource_type}.{resource.terraform_name}"
                )

        for resource_id in resources_to_remove:
            graph.remove_resource(resource_id)
            self._skipped_count += 1

        if self._skipped_count > 0:
            logger.info(
                f"DefaultResourceFilter: skipped {self._skipped_count} default resources"
            )

        return graph

    def _is_default_resource(self, resource: ResourceNode) -> bool:
        """Check if a resource is a default AWS resource."""
        resource_type = str(resource.resource_type)

        for tf_type, check_fn in self.SKIP_PATTERNS:
            if resource_type == tf_type:
                try:
                    if check_fn(resource):
                        return True
                except Exception:
                    # If check fails, don't skip the resource
                    logger.debug(
                        f"Check function failed for {resource.id}, not skipping"
                    )

        return False

    @property
    def skipped_count(self) -> int:
        """Return the number of resources skipped."""
        return self._skipped_count


def _is_main_route_table(resource: ResourceNode) -> bool:
    """Check if a route table is the main route table for its VPC."""
    associations = resource.config.get("Associations", [])
    if not associations:
        return False

    for assoc in associations:
        if isinstance(assoc, dict) and assoc.get("Main", False):
            return True

    return False


def _is_asg_managed_instance(resource: ResourceNode) -> bool:
    """
    Check if an EC2 instance is managed by an Auto Scaling Group.

    ASG-managed instances have:
    - launch_template or LaunchTemplate in config
    - Tags like aws:autoscaling:groupName

    These instances are ephemeral and should be managed via the ASG,
    not imported as standalone Terraform resources.
    """
    config = resource.config or {}

    # Check for launch_template block (indicates ASG management)
    if config.get("launch_template") or config.get("LaunchTemplate"):
        return True

    # Check for ASG-related tags
    tags = resource.tags or config.get("tags") or config.get("Tags") or {}
    if isinstance(tags, dict):
        if "aws:autoscaling:groupName" in tags:
            return True

    # Check tags list format
    if isinstance(tags, list):
        for tag in tags:
            if isinstance(tag, dict):
                key = tag.get("Key") or tag.get("key")
                if key == "aws:autoscaling:groupName":
                    return True

    return False
