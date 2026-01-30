"""
Hardcoded ID to Reference Transformer - CONTEXT-AWARE version.

CRITICAL: Only replace IDs in fields that are ACTUAL REFERENCES.

SAFE to replace:
  - vpc_id, subnet_id, security_group_ids
  - *_id, *_ids, *_arn suffixes

UNSAFE to replace (preserves original values):
  - tags, description, user_data, metadata

This prevents drift in metadata fields.

v3.7.21 ENHANCEMENT: Ghost reference handling
  - IDs not in graph are kept hardcoded (with debug logging)
  - AWS-managed resources are always kept hardcoded
  - Statistics tracking for resolved/self_ref/hardcoded/aws_managed
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from .base import BaseCodifyTransformer

if TYPE_CHECKING:
    from replimap.core.models import ResourceNode
    from replimap.core.unified_storage import GraphEngineAdapter

logger = logging.getLogger(__name__)


# Patterns for fields that are SAFE to replace with references
SAFE_FIELD_PATTERNS = [
    r"^vpc_id$",
    r"^VpcId$",
    r"^subnet_id$",
    r"^SubnetId$",
    r"^subnet_ids$",
    r"^SubnetIds$",
    r"^security_group_ids$",
    r"^SecurityGroupIds$",
    r"^security_groups$",
    r"^SecurityGroups$",
    r"^route_table_id$",
    r"^RouteTableId$",
    r"^instance_id$",
    r"^InstanceId$",
    r"^target_group_arn$",
    r"^TargetGroupArn$",
    r"^db_subnet_group_name$",
    r"^DBSubnetGroupName$",
    r"^launch_template_id$",
    r"^LaunchTemplateId$",
    r"^source_security_group_id$",
    r"^SourceSecurityGroupId$",
    r"^network_interface_id$",
    r"^NetworkInterfaceId$",
    r"^gateway_id$",
    r"^GatewayId$",
    r"^nat_gateway_id$",
    r"^NatGatewayId$",
    r"^internet_gateway_id$",
    r"^InternetGatewayId$",
    r"^role_arn$",
    r"^RoleArn$",
    r"^kms_key_id$",
    r"^KmsKeyId$",
    r"^.*_id$",  # Generic *_id pattern
    r"^.*_ids$",  # Generic *_ids pattern
    r"^.*_arn$",  # Generic *_arn pattern
    r"^.*_arns$",  # Generic *_arns pattern (plural)
]

# Patterns for fields that should NEVER be modified
UNSAFE_FIELD_PATTERNS = [
    r"^tags$",
    r"^Tags$",
    r"^description$",
    r"^Description$",
    r"^user_data$",
    r"^UserData$",
    r"^metadata$",
    r"^Metadata$",
    r"^comment$",
    r"^Comment$",
    r"^name$",  # Skip Name fields to avoid breaking naming
    r"^Name$",
]

# Compiled patterns
SAFE_REGEX = [re.compile(p) for p in SAFE_FIELD_PATTERNS]
UNSAFE_REGEX = [re.compile(p) for p in UNSAFE_FIELD_PATTERNS]

# AWS-managed resource prefixes that should ALWAYS be kept hardcoded
# These are AWS-managed resources that users cannot create/modify
AWS_MANAGED_PREFIXES: tuple[str, ...] = (
    "arn:aws:iam::aws:",  # AWS managed IAM policies (e.g., AmazonEC2ReadOnlyAccess)
    "arn:aws:elasticloadbalancing:",  # ELB managed resources
    "arn:aws:s3:::",  # AWS S3 managed resources
    "arn:aws-cn:iam::aws:",  # AWS China managed policies
    "arn:aws-us-gov:iam::aws:",  # AWS GovCloud managed policies
)

# Patterns to identify AWS resource IDs (for ghost reference detection)
AWS_ID_PATTERNS = [
    re.compile(r"^vpc-[a-f0-9]{8,17}$"),  # VPC IDs
    re.compile(r"^subnet-[a-f0-9]{8,17}$"),  # Subnet IDs
    re.compile(r"^sg-[a-f0-9]{8,17}$"),  # Security Group IDs
    re.compile(r"^i-[a-f0-9]{8,17}$"),  # EC2 Instance IDs
    re.compile(r"^vol-[a-f0-9]{8,17}$"),  # EBS Volume IDs
    re.compile(r"^ami-[a-f0-9]{8,17}$"),  # AMI IDs
    re.compile(r"^eni-[a-f0-9]{8,17}$"),  # Network Interface IDs
    re.compile(r"^rtb-[a-f0-9]{8,17}$"),  # Route Table IDs
    re.compile(r"^igw-[a-f0-9]{8,17}$"),  # Internet Gateway IDs
    re.compile(r"^nat-[a-f0-9]{8,17}$"),  # NAT Gateway IDs
    re.compile(r"^acl-[a-f0-9]{8,17}$"),  # Network ACL IDs
    re.compile(r"^eipalloc-[a-f0-9]{8,17}$"),  # Elastic IP IDs
    re.compile(r"^lt-[a-f0-9]{8,17}$"),  # Launch Template IDs
    re.compile(r"^snap-[a-f0-9]{8,17}$"),  # Snapshot IDs
    re.compile(r"^arn:aws[a-z-]*:[a-z0-9-]+:"),  # Generic ARN pattern
]


@dataclass
class RefTransformStats:
    """Statistics for reference transformation."""

    resolved: int = 0  # IDs successfully replaced with references
    self_ref: int = 0  # Self-references preserved (to avoid circular refs)
    hardcoded: int = 0  # Ghost references kept as hardcoded IDs
    aws_managed: int = 0  # AWS-managed resources kept hardcoded
    ghost_refs: list[str] = field(default_factory=list)  # List of ghost reference IDs


class HardcodedIdToRefTransformer(BaseCodifyTransformer):
    """
    Replace hardcoded AWS IDs with Terraform resource references.

    When generating Terraform code, hardcoded IDs like "vpc-12345" should
    be replaced with resource references like "aws_vpc.main.id". This
    creates maintainable, self-documenting code with proper dependencies.

    CONTEXT-AWARE: Only replaces IDs in fields that are actual references,
    not in tags, descriptions, or metadata where the ID might be intentional.
    """

    name = "HardcodedIdToRefTransformer"

    def __init__(self, create_references: bool = True) -> None:
        """
        Initialize the transformer.

        Args:
            create_references: Whether to replace IDs with references
        """
        self.create_references = create_references
        self._id_to_resource: dict[str, ResourceNode] = {}
        self._replacements_made = 0
        self._stats = RefTransformStats()

    def transform(self, graph: GraphEngineAdapter) -> GraphEngineAdapter:
        """
        Replace hardcoded IDs with Terraform references.

        Args:
            graph: The graph to transform

        Returns:
            The transformed graph
        """
        if not self.create_references:
            logger.debug("HardcodedIdToRefTransformer: references disabled")
            return graph

        self._replacements_made = 0
        self._stats = RefTransformStats()  # Reset statistics

        # Build ID → Resource mapping
        self._id_to_resource = {}
        for resource in graph.iter_resources():
            self._id_to_resource[resource.id] = resource
            if hasattr(resource, "arn") and resource.arn:
                self._id_to_resource[resource.arn] = resource

        # Transform each resource
        for resource in graph.iter_resources():
            # 🚨 v3.7.18 FIX: Pass current resource to avoid self-references
            # ElastiCache cluster_id would otherwise reference itself!
            self._transform_config(resource.config, current_resource=resource)

        # Log statistics
        if self._stats.resolved > 0 or self._stats.hardcoded > 0:
            logger.info(
                f"HardcodedIdToRefTransformer: resolved={self._stats.resolved}, "
                f"self_ref={self._stats.self_ref}, hardcoded={self._stats.hardcoded}, "
                f"aws_managed={self._stats.aws_managed}"
            )
        if self._stats.ghost_refs:
            logger.debug(
                f"Ghost references (not in graph): {self._stats.ghost_refs[:10]}"
                f"{'...' if len(self._stats.ghost_refs) > 10 else ''}"
            )

        # Maintain backwards compatibility
        self._replacements_made = self._stats.resolved

        return graph

    def _transform_config(
        self,
        config: dict[str, Any],
        parent_key: str | None = None,
        current_resource: ResourceNode | None = None,
    ) -> None:
        """
        Recursively transform config, replacing IDs with references.

        Args:
            config: Configuration dictionary to transform
            parent_key: Key of parent field (for context)
            current_resource: The resource being processed (to avoid self-references)
        """
        if not isinstance(config, dict):
            return

        for key, value in list(config.items()):
            # Skip unsafe fields entirely
            if self._is_unsafe_field(key):
                continue

            if isinstance(value, str):
                if self._is_safe_field(key):
                    # 🚨 v3.7.21: Check for AWS-managed resources first
                    if self._is_aws_managed(value):
                        self._stats.aws_managed += 1
                        logger.debug(f"Keeping AWS-managed resource hardcoded: {value}")
                        continue

                    if value in self._id_to_resource:
                        ref_resource = self._id_to_resource[value]

                        # 🚨 v3.7.18 FIX: Skip self-references!
                        # ElastiCache cluster_id = cluster's own ID would create circular ref
                        if current_resource and ref_resource.id == current_resource.id:
                            logger.debug(
                                f"Skipping self-reference: {key}={value} on resource {current_resource.id}"
                            )
                            self._stats.self_ref += 1
                            continue

                        tf_type = str(ref_resource.resource_type)
                        tf_name = ref_resource.terraform_name

                        # Determine the attribute to reference (usually .id)
                        attr = self._get_reference_attribute(key, tf_type)

                        config[key] = f"${{{tf_type}.{tf_name}.{attr}}}"
                        self._stats.resolved += 1

                    # 🚨 v3.7.21: Ghost reference handling
                    # ID not in graph but looks like AWS ID -> keep hardcoded
                    elif self._is_aws_id(value):
                        self._stats.hardcoded += 1
                        self._stats.ghost_refs.append(value)
                        logger.debug(f"Ghost reference (not in graph): {key}={value}")
                        # Keep the hardcoded value (don't modify config[key])

            elif isinstance(value, dict):
                self._transform_config(value, key, current_resource)

            elif isinstance(value, list):
                for i, item in enumerate(value):
                    # For string items, only process if field is safe for replacement
                    if isinstance(item, str) and self._is_safe_field(key):
                        # 🚨 v3.7.21: Check for AWS-managed resources first
                        if self._is_aws_managed(item):
                            self._stats.aws_managed += 1
                            continue

                        if item in self._id_to_resource:
                            ref_resource = self._id_to_resource[item]

                            # 🚨 v3.7.18 FIX: Skip self-references in lists too
                            if (
                                current_resource
                                and ref_resource.id == current_resource.id
                            ):
                                self._stats.self_ref += 1
                                continue

                            tf_type = str(ref_resource.resource_type)
                            tf_name = ref_resource.terraform_name
                            attr = self._get_reference_attribute(key, tf_type)
                            value[i] = f"${{{tf_type}.{tf_name}.{attr}}}"
                            self._stats.resolved += 1

                        # 🚨 v3.7.21: Ghost reference handling in lists
                        elif self._is_aws_id(item):
                            self._stats.hardcoded += 1
                            self._stats.ghost_refs.append(item)

                    # 🚨 v3.7.21: Always recurse into nested dicts (they apply own field checks)
                    elif isinstance(item, dict):
                        self._transform_config(item, key, current_resource)

    def _is_safe_field(self, key: str) -> bool:
        """Check if a field is safe for reference replacement."""
        # First check if it's unsafe
        if self._is_unsafe_field(key):
            return False

        # Then check if it matches safe patterns
        return any(pattern.match(key) for pattern in SAFE_REGEX)

    def _is_unsafe_field(self, key: str) -> bool:
        """Check if a field should never be modified."""
        return any(pattern.match(key) for pattern in UNSAFE_REGEX)

    def _get_reference_attribute(self, field_name: str, tf_type: str) -> str:
        """
        Determine which attribute to reference.

        Most resources use .id, but some need special handling.
        """
        # ARN references
        if "arn" in field_name.lower():
            return "arn"

        # DB subnet group uses name
        if tf_type == "aws_db_subnet_group" and "name" in field_name.lower():
            return "name"

        # Default to id
        return "id"

    def _is_aws_managed(self, value: str) -> bool:
        """
        Check if value is an AWS-managed resource that should stay hardcoded.

        AWS-managed resources (like AWS managed IAM policies) cannot be
        created by users and must be referenced by their ARN directly.
        """
        return any(value.startswith(prefix) for prefix in AWS_MANAGED_PREFIXES)

    def _is_aws_id(self, value: str) -> bool:
        """
        Check if value looks like an AWS resource ID or ARN.

        Used for ghost reference detection - IDs that look like AWS resources
        but aren't in our graph (filtered, different region, deleted).
        """
        return any(pattern.match(value) for pattern in AWS_ID_PATTERNS)

    @property
    def replacements_made(self) -> int:
        """Return the number of replacements made."""
        return self._replacements_made

    @property
    def stats(self) -> RefTransformStats:
        """Return transformation statistics."""
        return self._stats
