"""
Import ID Resolver - Handles the complexity of terraform import IDs.

CRITICAL: Terraform import ID is NOT always the AWS resource ID!

Examples:
  aws_instance:                  i-0abc123 (simple)
  aws_security_group_rule:       sg-xxx_ingress_tcp_22_22_0.0.0.0/0 (complex!)
  aws_route:                     rtb-xxx_0.0.0.0/0
  aws_iam_role_policy_attachment: role-name/policy-arn
  aws_db_instance:               mydb-identifier (NOT the db-xxx ID!)
  aws_autoscaling_group:         my-asg-name (name, NOT the ARN!)
  aws_sqs_queue:                 https://sqs.region.amazonaws.com/account/queue (URL!)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from .base import BaseCodifyTransformer

if TYPE_CHECKING:
    from replimap.core.models import ResourceNode
    from replimap.core.unified_storage import GraphEngineAdapter

logger = logging.getLogger(__name__)


class ImportIDResolver(BaseCodifyTransformer):
    """
    Resolve correct Terraform import IDs for each resource.

    Different resource types require different import ID formats.
    This transformer adds the correct import ID to each resource's
    config so the import generator can use it.
    """

    name = "ImportIDResolver"

    def __init__(self, resolve_ids: bool = True) -> None:
        """
        Initialize the resolver.

        Args:
            resolve_ids: Whether to resolve import IDs
        """
        self.resolve_ids = resolve_ids
        self._resolved_count = 0

    def transform(self, graph: GraphEngineAdapter) -> GraphEngineAdapter:
        """
        Add resolved import IDs to resource configs.

        Args:
            graph: The graph to transform

        Returns:
            The transformed graph
        """
        if not self.resolve_ids:
            logger.debug("ImportIDResolver: resolution disabled")
            return graph

        self._resolved_count = 0

        for resource in graph.iter_resources():
            import_id = self._resolve_import_id(resource)
            if import_id:
                resource.config["_import_id"] = import_id
                self._resolved_count += 1

        if self._resolved_count > 0:
            logger.info(f"ImportIDResolver: resolved {self._resolved_count} import IDs")

        return graph

    def _resolve_import_id(self, resource: ResourceNode) -> str | None:
        """
        Determine the correct Terraform import ID for a resource.

        Returns the import ID string, or None if using default (resource ID).
        """
        tf_type = str(resource.resource_type)
        config = resource.config or {}

        # 🚨 v3.7.20 FIX: ASG import ID must be name, not ARN!
        # Scanner stores ARN as resource.id, but Terraform import needs the name
        if tf_type == "aws_autoscaling_group":
            return (
                config.get("AutoScalingGroupName") or config.get("name") or resource.id
            )

        # Simple cases: use AWS ID directly
        simple_types = {
            "aws_vpc",
            "aws_subnet",
            "aws_security_group",
            "aws_instance",
            "aws_ebs_volume",
            "aws_internet_gateway",
            "aws_nat_gateway",
            "aws_route_table",
            "aws_network_acl",
            "aws_lb",
            "aws_lb_listener",
            "aws_lb_target_group",
            "aws_launch_template",
            "aws_elasticache_cluster",
            "aws_iam_role",
            "aws_iam_policy",
            "aws_iam_user",
            "aws_iam_group",
            "aws_cloudwatch_log_group",
            "aws_cloudwatch_metric_alarm",
            "aws_eip",
        }

        if tf_type in simple_types:
            return resource.id

        # S3 bucket: use bucket name
        if tf_type == "aws_s3_bucket":
            return config.get("bucket") or config.get("Bucket") or resource.id

        # 🚨 v3.7.18 FIX: S3 bucket policy import ID is the bucket name, not resource ID
        # The storage_scanner creates policy resources with id="{bucket_name}-policy"
        # but Terraform expects just the bucket name for import
        if tf_type == "aws_s3_bucket_policy":
            return config.get("bucket") or config.get("Bucket") or resource.id

        # RDS instance: use DB instance identifier (NOT the dbi-xxx ID)
        if tf_type == "aws_db_instance":
            return (
                config.get("DBInstanceIdentifier")
                or config.get("db_instance_identifier")
                or resource.id
            )

        # RDS cluster: use cluster identifier
        if tf_type == "aws_rds_cluster":
            return (
                config.get("DBClusterIdentifier")
                or config.get("db_cluster_identifier")
                or resource.id
            )

        # DB subnet group: use name
        if tf_type == "aws_db_subnet_group":
            return (
                config.get("DBSubnetGroupName")
                or config.get("db_subnet_group_name")
                or resource.id
            )

        # DB parameter group: use name
        if tf_type == "aws_db_parameter_group":
            return (
                config.get("DBParameterGroupName")
                or config.get("db_parameter_group_name")
                or resource.id
            )

        # ElastiCache subnet group: use name
        if tf_type == "aws_elasticache_subnet_group":
            return (
                config.get("CacheSubnetGroupName")
                or config.get("cache_subnet_group_name")
                or resource.id
            )

        # Security group rule: complex composite ID
        if (
            tf_type == "aws_security_group_rule"
            or config.get("_terraform_type") == "aws_security_group_rule"
        ):
            return self._resolve_sg_rule_id(resource)

        # Route: rtb-xxx_destination
        if tf_type == "aws_route":
            return self._resolve_route_id(resource)

        # IAM role policy attachment: role-name/policy-arn
        if (
            tf_type == "aws_iam_role_policy_attachment"
            or config.get("_terraform_type") == "aws_iam_role_policy_attachment"
        ):
            return self._resolve_role_policy_attachment_id(resource)

        # IAM user policy attachment: user-name/policy-arn
        if (
            tf_type == "aws_iam_user_policy_attachment"
            or config.get("_terraform_type") == "aws_iam_user_policy_attachment"
        ):
            return self._resolve_user_policy_attachment_id(resource)

        # IAM group policy attachment: group-name/policy-arn
        if (
            tf_type == "aws_iam_group_policy_attachment"
            or config.get("_terraform_type") == "aws_iam_group_policy_attachment"
        ):
            return self._resolve_group_policy_attachment_id(resource)

        # IAM role policy (inline): role-name:policy-name
        if (
            tf_type == "aws_iam_role_policy"
            or config.get("_terraform_type") == "aws_iam_role_policy"
        ):
            role = config.get("role", "")
            policy_name = config.get("name", "")
            if role and policy_name:
                return f"{role}:{policy_name}"
            return resource.id

        # IAM user policy (inline): user-name:policy-name
        if (
            tf_type == "aws_iam_user_policy"
            or config.get("_terraform_type") == "aws_iam_user_policy"
        ):
            user = config.get("user", "")
            policy_name = config.get("name", "")
            if user and policy_name:
                return f"{user}:{policy_name}"
            return resource.id

        # IAM group policy (inline): group-name:policy-name
        if (
            tf_type == "aws_iam_group_policy"
            or config.get("_terraform_type") == "aws_iam_group_policy"
        ):
            group = config.get("group", "")
            policy_name = config.get("name", "")
            if group and policy_name:
                return f"{group}:{policy_name}"
            return resource.id

        # IAM instance profile: name
        if tf_type == "aws_iam_instance_profile":
            return (
                config.get("InstanceProfileName")
                or config.get("instance_profile_name")
                or resource.id
            )

        # 🚨 v3.7.18 FIX: SQS queue import ID must be URL, not ARN!
        # Schema mapping removes the 'url' field, but we can derive URL from ARN.
        # ARN format: arn:aws:sqs:us-east-1:123456789012:my-queue (or arn:aws-cn, arn:aws-us-gov)
        # URL format: https://sqs.us-east-1.amazonaws.com/123456789012/my-queue
        if tf_type == "aws_sqs_queue":
            # First try config (may still have URL in some cases)
            url = config.get("QueueUrl") or config.get("url")
            if url:
                return url

            # Derive URL from ARN (resource.id is the ARN from scanner)
            # Handle all AWS partitions: aws, aws-cn, aws-us-gov
            arn = resource.id
            if arn and ":sqs:" in arn and arn.startswith("arn:"):
                # Parse ARN: arn:PARTITION:sqs:REGION:ACCOUNT:QUEUE_NAME
                parts = arn.split(":")
                if len(parts) >= 6:
                    partition = parts[1]  # aws, aws-cn, aws-us-gov
                    region = parts[3]
                    account_id = parts[4]
                    queue_name = parts[5]

                    # Determine the correct domain for the partition
                    if partition == "aws-cn":
                        domain = "amazonaws.com.cn"
                    else:
                        domain = "amazonaws.com"

                    return f"https://sqs.{region}.{domain}/{account_id}/{queue_name}"

            # Fallback to resource ID (will likely fail, but better than nothing)
            logger.warning(
                f"SQS: Could not derive URL from ARN '{resource.id}', import may fail"
            )
            return resource.id

        # SNS topic: ARN
        if tf_type == "aws_sns_topic":
            return config.get("TopicArn") or resource.arn or resource.id

        # VPC endpoint: vpce-xxx
        if tf_type == "aws_vpc_endpoint":
            return config.get("VpcEndpointId") or resource.id

        # Route53 zone: zone ID
        if tf_type == "aws_route53_zone":
            return config.get("Id") or resource.id

        # Route53 record: zone_id_record_name_type
        if tf_type == "aws_route53_record":
            zone_id = config.get("HostedZoneId", "")
            name = config.get("Name", "")
            record_type = config.get("Type", "")
            if zone_id and name and record_type:
                return f"{zone_id}_{name}_{record_type}"
            return resource.id

        # Default: use resource ID
        return resource.id

    def _resolve_sg_rule_id(self, resource: ResourceNode) -> str:
        """
        Resolve security group rule import ID.

        Format: sg-xxx_ingress_tcp_22_22_0.0.0.0/0
        """
        config = resource.config or {}

        sg_id = config.get("security_group_id", "")
        direction = config.get("type", "ingress")
        protocol = config.get("protocol", "-1")
        from_port = config.get("from_port", 0)
        to_port = config.get("to_port", 0)

        # Determine the source
        source = ""
        if config.get("cidr_blocks"):
            source = config["cidr_blocks"][0]
        elif config.get("ipv6_cidr_blocks"):
            source = config["ipv6_cidr_blocks"][0]
        elif config.get("source_security_group_id"):
            source = config["source_security_group_id"]
        elif config.get("prefix_list_ids"):
            source = config["prefix_list_ids"][0]
        else:
            source = "0.0.0.0/0"

        return f"{sg_id}_{direction}_{protocol}_{from_port}_{to_port}_{source}"

    def _resolve_route_id(self, resource: ResourceNode) -> str:
        """
        Resolve route import ID.

        Format: rtb-xxx_0.0.0.0/0 or rtb-xxx_::/0
        """
        config = resource.config or {}

        rtb_id = config.get("RouteTableId") or config.get("route_table_id", "")
        dest = (
            config.get("DestinationCidrBlock")
            or config.get("destination_cidr_block")
            or config.get("DestinationIpv6CidrBlock")
            or config.get("destination_ipv6_cidr_block")
            or "0.0.0.0/0"
        )

        return f"{rtb_id}_{dest}"

    def _resolve_role_policy_attachment_id(self, resource: ResourceNode) -> str:
        """
        Resolve IAM role policy attachment import ID.

        Format: role-name/policy-arn
        """
        config = resource.config or {}
        role = config.get("role", "")
        policy_arn = config.get("policy_arn", "")
        return f"{role}/{policy_arn}"

    def _resolve_user_policy_attachment_id(self, resource: ResourceNode) -> str:
        """
        Resolve IAM user policy attachment import ID.

        Format: user-name/policy-arn
        """
        config = resource.config or {}
        user = config.get("user", "")
        policy_arn = config.get("policy_arn", "")
        return f"{user}/{policy_arn}"

    def _resolve_group_policy_attachment_id(self, resource: ResourceNode) -> str:
        """
        Resolve IAM group policy attachment import ID.

        Format: group-name/policy-arn
        """
        config = resource.config or {}
        group = config.get("group", "")
        policy_arn = config.get("policy_arn", "")
        return f"{group}/{policy_arn}"

    @property
    def resolved_count(self) -> int:
        """Return the number of import IDs resolved."""
        return self._resolved_count
