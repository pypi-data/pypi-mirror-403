"""
IAM Attachment Normalizer - Prevent accidental permission stripping.

CRITICAL: IAM has two attachment modes:

  1. EXCLUSIVE (Dangerous):
     aws_iam_role.managed_policy_arns = [...]  # Deletes unlisted policies!
     aws_iam_role.inline_policy { ... }         # Deletes unlisted inline!

  2. NON-EXCLUSIVE (Safe):
     aws_iam_role_policy_attachment { ... }     # Only manages what's defined

RULE: NEVER generate inline policy blocks. ALWAYS use standalone attachments.

This ensures RepliMap-generated code "coexists peacefully" with manually
added policies that haven't been imported yet.
"""

from __future__ import annotations

import json
import logging
import uuid
from typing import TYPE_CHECKING, Any

from replimap.core.models import ResourceNode, ResourceType

from .base import BaseCodifyTransformer

if TYPE_CHECKING:
    from replimap.core.unified_storage import GraphEngineAdapter

logger = logging.getLogger(__name__)


class IamAttachmentNormalizer(BaseCodifyTransformer):
    """
    Normalize IAM attachments to use non-exclusive pattern.

    Converts inline policies and managed_policy_arns to standalone
    attachment resources. This prevents accidental permission removal
    when other policies exist that aren't being imported.
    """

    name = "IamAttachmentNormalizer"

    def __init__(self, normalize_attachments: bool = True) -> None:
        """
        Initialize the normalizer.

        Args:
            normalize_attachments: Whether to normalize IAM attachments
        """
        self.normalize_attachments = normalize_attachments
        self._attachments_created = 0
        self._policies_extracted = 0

    def transform(self, graph: GraphEngineAdapter) -> GraphEngineAdapter:
        """
        Normalize IAM attachments to standalone resources.

        Args:
            graph: The graph to transform

        Returns:
            The transformed graph
        """
        if not self.normalize_attachments:
            logger.debug("IamAttachmentNormalizer: normalization disabled")
            return graph

        self._attachments_created = 0
        self._policies_extracted = 0
        new_resources: list[ResourceNode] = []

        for resource in graph.iter_resources():
            resource_type = str(resource.resource_type)

            if resource_type == "aws_iam_role":
                new_resources.extend(self._normalize_role(resource))
            elif resource_type == "aws_iam_user":
                new_resources.extend(self._normalize_user(resource))
            elif resource_type == "aws_iam_group":
                new_resources.extend(self._normalize_group(resource))

        # Add all new resources to graph
        for new_resource in new_resources:
            graph.add_resource(new_resource)

        if self._attachments_created > 0 or self._policies_extracted > 0:
            logger.info(
                f"IamAttachmentNormalizer: created {self._attachments_created} attachments, "
                f"extracted {self._policies_extracted} inline policies"
            )

        return graph

    def _normalize_role(self, role: ResourceNode) -> list[ResourceNode]:
        """Normalize IAM role attachments."""
        new_resources: list[ResourceNode] = []
        config = role.config or {}

        role_name = config.get("RoleName", role.terraform_name)

        # Extract managed_policy_arns → aws_iam_role_policy_attachment
        managed_arns = config.pop("ManagedPolicyArns", [])
        for arn in managed_arns:
            attachment = self._create_role_policy_attachment(role, role_name, arn)
            new_resources.append(attachment)
            self._attachments_created += 1

        # Extract AttachedPolicies → aws_iam_role_policy_attachment
        attached_policies = config.pop("AttachedPolicies", [])
        for policy in attached_policies:
            arn = policy.get("PolicyArn")
            if arn:
                attachment = self._create_role_policy_attachment(role, role_name, arn)
                new_resources.append(attachment)
                self._attachments_created += 1

        # Extract inline_policy → aws_iam_role_policy (standalone)
        inline_policies = config.pop("RolePolicyList", [])
        for policy in inline_policies:
            policy_resource = self._create_role_policy(role, role_name, policy)
            if policy_resource:
                new_resources.append(policy_resource)
                self._policies_extracted += 1

        return new_resources

    def _normalize_user(self, user: ResourceNode) -> list[ResourceNode]:
        """Normalize IAM user attachments."""
        new_resources: list[ResourceNode] = []
        config = user.config or {}

        user_name = config.get("UserName", user.terraform_name)

        # Extract AttachedPolicies → aws_iam_user_policy_attachment
        attached_policies = config.pop("AttachedManagedPolicies", [])
        for policy in attached_policies:
            arn = policy.get("PolicyArn")
            if arn:
                attachment = self._create_user_policy_attachment(user, user_name, arn)
                new_resources.append(attachment)
                self._attachments_created += 1

        # Extract inline policies → aws_iam_user_policy (standalone)
        inline_policies = config.pop("UserPolicyList", [])
        for policy in inline_policies:
            policy_resource = self._create_user_policy(user, user_name, policy)
            if policy_resource:
                new_resources.append(policy_resource)
                self._policies_extracted += 1

        return new_resources

    def _normalize_group(self, group: ResourceNode) -> list[ResourceNode]:
        """Normalize IAM group attachments."""
        new_resources: list[ResourceNode] = []
        config = group.config or {}

        group_name = config.get("GroupName", group.terraform_name)

        # Extract AttachedPolicies → aws_iam_group_policy_attachment
        attached_policies = config.pop("AttachedManagedPolicies", [])
        for policy in attached_policies:
            arn = policy.get("PolicyArn")
            if arn:
                attachment = self._create_group_policy_attachment(
                    group, group_name, arn
                )
                new_resources.append(attachment)
                self._attachments_created += 1

        # Extract inline policies → aws_iam_group_policy (standalone)
        inline_policies = config.pop("GroupPolicyList", [])
        for policy in inline_policies:
            policy_resource = self._create_group_policy(group, group_name, policy)
            if policy_resource:
                new_resources.append(policy_resource)
                self._policies_extracted += 1

        return new_resources

    def _create_role_policy_attachment(
        self, role: ResourceNode, role_name: str, policy_arn: str
    ) -> ResourceNode:
        """Create a standalone role policy attachment resource."""
        # Extract policy name from ARN for naming
        policy_name = policy_arn.split("/")[-1] if "/" in policy_arn else policy_arn
        tf_name = f"{role.terraform_name}_{self._sanitize_name(policy_name)}"

        return ResourceNode(
            id=f"role-attach-{uuid.uuid4().hex[:12]}",
            resource_type=ResourceType.UNKNOWN,  # aws_iam_role_policy_attachment
            region=role.region,
            config={
                "role": role_name,
                "policy_arn": policy_arn,
                "_terraform_type": "aws_iam_role_policy_attachment",
                "_parent_role_name": role.terraform_name,
            },
            terraform_name=tf_name,
            original_name=tf_name,
        )

    def _create_user_policy_attachment(
        self, user: ResourceNode, user_name: str, policy_arn: str
    ) -> ResourceNode:
        """Create a standalone user policy attachment resource."""
        policy_name = policy_arn.split("/")[-1] if "/" in policy_arn else policy_arn
        tf_name = f"{user.terraform_name}_{self._sanitize_name(policy_name)}"

        return ResourceNode(
            id=f"user-attach-{uuid.uuid4().hex[:12]}",
            resource_type=ResourceType.UNKNOWN,  # aws_iam_user_policy_attachment
            region=user.region,
            config={
                "user": user_name,
                "policy_arn": policy_arn,
                "_terraform_type": "aws_iam_user_policy_attachment",
                "_parent_user_name": user.terraform_name,
            },
            terraform_name=tf_name,
            original_name=tf_name,
        )

    def _create_group_policy_attachment(
        self, group: ResourceNode, group_name: str, policy_arn: str
    ) -> ResourceNode:
        """Create a standalone group policy attachment resource."""
        policy_name = policy_arn.split("/")[-1] if "/" in policy_arn else policy_arn
        tf_name = f"{group.terraform_name}_{self._sanitize_name(policy_name)}"

        return ResourceNode(
            id=f"group-attach-{uuid.uuid4().hex[:12]}",
            resource_type=ResourceType.UNKNOWN,  # aws_iam_group_policy_attachment
            region=group.region,
            config={
                "group": group_name,
                "policy_arn": policy_arn,
                "_terraform_type": "aws_iam_group_policy_attachment",
                "_parent_group_name": group.terraform_name,
            },
            terraform_name=tf_name,
            original_name=tf_name,
        )

    def _create_role_policy(
        self, role: ResourceNode, role_name: str, policy: dict[str, Any]
    ) -> ResourceNode | None:
        """Create a standalone inline role policy resource."""
        policy_name = policy.get("PolicyName")
        policy_doc = policy.get("PolicyDocument")

        if not policy_name or not policy_doc:
            return None

        # Convert policy document to JSON string if needed
        if isinstance(policy_doc, dict):
            policy_doc = json.dumps(policy_doc, indent=2)

        tf_name = f"{role.terraform_name}_{self._sanitize_name(policy_name)}"

        return ResourceNode(
            id=f"role-policy-{uuid.uuid4().hex[:12]}",
            resource_type=ResourceType.UNKNOWN,  # aws_iam_role_policy
            region=role.region,
            config={
                "role": role_name,
                "name": policy_name,
                "policy": policy_doc,
                "_terraform_type": "aws_iam_role_policy",
                "_parent_role_name": role.terraform_name,
            },
            terraform_name=tf_name,
            original_name=tf_name,
        )

    def _create_user_policy(
        self, user: ResourceNode, user_name: str, policy: dict[str, Any]
    ) -> ResourceNode | None:
        """Create a standalone inline user policy resource."""
        policy_name = policy.get("PolicyName")
        policy_doc = policy.get("PolicyDocument")

        if not policy_name or not policy_doc:
            return None

        if isinstance(policy_doc, dict):
            policy_doc = json.dumps(policy_doc, indent=2)

        tf_name = f"{user.terraform_name}_{self._sanitize_name(policy_name)}"

        return ResourceNode(
            id=f"user-policy-{uuid.uuid4().hex[:12]}",
            resource_type=ResourceType.UNKNOWN,  # aws_iam_user_policy
            region=user.region,
            config={
                "user": user_name,
                "name": policy_name,
                "policy": policy_doc,
                "_terraform_type": "aws_iam_user_policy",
                "_parent_user_name": user.terraform_name,
            },
            terraform_name=tf_name,
            original_name=tf_name,
        )

    def _create_group_policy(
        self, group: ResourceNode, group_name: str, policy: dict[str, Any]
    ) -> ResourceNode | None:
        """Create a standalone inline group policy resource."""
        policy_name = policy.get("PolicyName")
        policy_doc = policy.get("PolicyDocument")

        if not policy_name or not policy_doc:
            return None

        if isinstance(policy_doc, dict):
            policy_doc = json.dumps(policy_doc, indent=2)

        tf_name = f"{group.terraform_name}_{self._sanitize_name(policy_name)}"

        return ResourceNode(
            id=f"group-policy-{uuid.uuid4().hex[:12]}",
            resource_type=ResourceType.UNKNOWN,  # aws_iam_group_policy
            region=group.region,
            config={
                "group": group_name,
                "name": policy_name,
                "policy": policy_doc,
                "_terraform_type": "aws_iam_group_policy",
                "_parent_group_name": group.terraform_name,
            },
            terraform_name=tf_name,
            original_name=tf_name,
        )

    def _sanitize_name(self, name: str) -> str:
        """Sanitize a name for use in Terraform resource names."""
        result = ""
        for char in name:
            if char.isalnum() or char in "_-":
                result += char
            else:
                result += "_"
        return result.lower()

    @property
    def attachments_created(self) -> int:
        """Return the number of attachment resources created."""
        return self._attachments_created

    @property
    def policies_extracted(self) -> int:
        """Return the number of inline policies extracted."""
        return self._policies_extracted
