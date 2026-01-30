"""
Global Resource Filter - Prevents multi-region duplication.

Global resources (IAM, Route53, CloudFront) must only be defined ONCE.

Strategy:
- Primary region (us-east-1): Include global resources
- Other regions: Exclude global resources
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from .base import BaseCodifyTransformer

if TYPE_CHECKING:
    from replimap.core.unified_storage import GraphEngineAdapter

logger = logging.getLogger(__name__)


# Global resource types that should only exist in the primary region
GLOBAL_RESOURCE_TYPES = {
    # IAM
    "aws_iam_role",
    "aws_iam_policy",
    "aws_iam_user",
    "aws_iam_group",
    "aws_iam_role_policy",
    "aws_iam_role_policy_attachment",
    "aws_iam_user_policy_attachment",
    "aws_iam_group_policy_attachment",
    "aws_iam_instance_profile",
    # Route53
    "aws_route53_zone",
    "aws_route53_record",
    "aws_route53_health_check",
    # CloudFront
    "aws_cloudfront_distribution",
    "aws_cloudfront_origin_access_identity",
    # WAF Global
    "aws_waf_web_acl",
    "aws_waf_rule",
    # ACM (global for CloudFront in us-east-1)
    "aws_acm_certificate",
}

DEFAULT_PRIMARY_REGION = "us-east-1"


class GlobalResourceFilter(BaseCodifyTransformer):
    """
    Filter global resources based on region.

    Global resources (IAM, Route53, CloudFront) exist at the account level,
    not the region level. To prevent duplicate definitions when generating
    code for multiple regions, we only include global resources in the
    primary region (default: us-east-1).
    """

    name = "GlobalResourceFilter"

    def __init__(
        self,
        current_region: str,
        primary_region: str = DEFAULT_PRIMARY_REGION,
        force_include_global: bool = False,
    ) -> None:
        """
        Initialize the filter.

        Args:
            current_region: The region being processed
            primary_region: The region where global resources should be defined
            force_include_global: If True, include global resources regardless of region
        """
        self.current_region = current_region
        self.primary_region = primary_region
        self.force_include_global = force_include_global
        self._skipped_count = 0

    def transform(self, graph: GraphEngineAdapter) -> GraphEngineAdapter:
        """
        Filter out global resources in non-primary regions.

        Args:
            graph: The graph to filter

        Returns:
            The filtered graph
        """
        # If forcing include or we're in the primary region, keep all resources
        if self.force_include_global or self.current_region == self.primary_region:
            logger.debug(
                f"GlobalResourceFilter: in primary region ({self.primary_region}), "
                "keeping global resources"
            )
            return graph

        self._skipped_count = 0
        resources_to_remove: list[str] = []

        for resource in graph.iter_resources():
            resource_type = str(resource.resource_type)
            if resource_type in GLOBAL_RESOURCE_TYPES:
                resources_to_remove.append(resource.id)
                logger.debug(
                    f"Skipped global resource in {self.current_region}: "
                    f"{resource_type}.{resource.terraform_name}"
                )

        for resource_id in resources_to_remove:
            graph.remove_resource(resource_id)
            self._skipped_count += 1

        if self._skipped_count > 0:
            logger.info(
                f"GlobalResourceFilter: skipped {self._skipped_count} global resources "
                f"(not in primary region {self.primary_region})"
            )

        return graph

    @property
    def skipped_count(self) -> int:
        """Return the number of resources skipped."""
        return self._skipped_count
