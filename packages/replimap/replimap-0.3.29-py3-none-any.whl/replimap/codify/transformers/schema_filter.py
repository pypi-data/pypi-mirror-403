"""
Schema Filter Transformer - Filter and map attributes to Terraform schema.

This transformer:
1. Removes read-only/computed attributes that Terraform doesn't accept
2. Maps AWS API field names to Terraform provider schema names
3. Handles resource-specific attribute requirements

This prevents "Unsupported argument" errors during terraform plan.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from replimap.codify.transformers.base import BaseCodifyTransformer

if TYPE_CHECKING:
    from replimap.core.models import ResourceNode
    from replimap.core.unified_storage import GraphEngineAdapter

logger = logging.getLogger(__name__)


# Global read-only attributes that should never be in Terraform config
# These are computed by AWS, not set by users
GLOBAL_BLOCKLIST = frozenset(
    {
        # State and status
        "state",
        "status",
        "Status",
        "State",
        # Timestamps
        "create_time",
        "created_at",
        "creation_date",
        "CreateTime",
        "CreatedAt",
        "CreationDate",
        "last_modified",
        "LastModified",
        "last_modified_time",
        # ARN and IDs (as attributes, not references)
        "arn",
        "Arn",
        "ARN",
        "id",  # lowercase 'id' is usually computed
        # Owner and account info
        "owner_id",
        "OwnerId",
        "account_id",
        "AccountId",
        # Association IDs (computed when associations are made)
        "association_id",
        "AssociationId",
        "attachment_id",
        "AttachmentId",
        # VPC computed attributes
        "main_route_table_id",
        "default_route_table_id",
        "default_network_acl_id",
        "default_security_group_id",
        "dhcp_options_id",
        "DhcpOptionsId",
        "MainRouteTableId",
        "DefaultRouteTableId",
        "DefaultNetworkAclId",
        "DefaultSecurityGroupId",
        # Subnet computed
        "available_ip_address_count",
        "AvailableIpAddressCount",
        # EC2 computed
        "private_ip",
        "public_ip",
        "private_dns",
        "public_dns",
        "PrivateIp",
        "PublicIp",
        "PrivateDns",
        "PublicDns",
        "instance_state",
        "InstanceState",
        # Security group computed
        "owner_group_id",
        "OwnerGroupId",
        # S3 computed
        "hosted_zone_id",
        "HostedZoneId",
        "region",  # S3 bucket region is usually computed from provider
        "bucket_domain_name",
        "bucket_regional_domain_name",
        # RDS computed
        "endpoint",
        "Endpoint",
        "address",
        "Address",
        "port",  # Usually computed from engine
        "Port",
        "hosted_zone",
        "resource_id",
        "dbi_resource_id",
        "DbInstancePort",
        # EBS computed
        "snapshot_id",  # Only for volumes created from snapshots
        "SnapshotId",
        # Load balancer computed
        "dns_name",
        "DnsName",
        "zone_id",
        "ZoneId",
        "vpc_zone_identifier",  # ASG uses this as input but it's derived
        # Lambda computed
        "invoke_arn",
        "qualified_arn",
        "version",
        "source_code_hash",
        "source_code_size",
        # IAM computed
        "unique_id",
        "UniqueId",
        "create_date",
        "CreateDate",
        # Elasticache computed
        "cache_nodes",
        "configuration_endpoint",
        "ConfigurationEndpoint",
        # Network interface computed
        "mac_address",
        "MacAddress",
        "private_ip_address",
        "PrivateIpAddress",
        "network_interface_id",
        "NetworkInterfaceId",
        # Route computed
        "origin",
        "Origin",
        # General AWS metadata
        "request_id",
        "RequestId",
        "http_status_code",
        "HttpStatusCode",
    }
)

# Resource-specific blocklists (attributes only invalid for specific resources)
RESOURCE_BLOCKLISTS: dict[str, frozenset[str]] = {
    "aws_vpc": frozenset(
        {
            "is_default",
            "IsDefault",
            "instance_tenancy",  # Only set at creation, not modifiable
        }
    ),
    "aws_subnet": frozenset(
        {
            "owner_id",
            "OwnerId",
            "state",
            "State",
        }
    ),
    "aws_security_group": frozenset(
        {
            "owner_id",
            "OwnerId",
        }
    ),
    "aws_instance": frozenset(
        {
            "primary_network_interface_id",
            "PrimaryNetworkInterfaceId",
            "instance_id",
            "InstanceId",
        }
    ),
    "aws_ebs_volume": frozenset(
        {
            "multi_attach_enabled",  # Only for io1/io2
            "outpost_arn",
        }
    ),
    "aws_lb": frozenset(
        {
            "arn_suffix",
        }
    ),
    "aws_lb_target_group": frozenset(
        {
            "arn_suffix",
            "load_balancer_arns",
        }
    ),
    "aws_db_instance": frozenset(
        {
            "status",
            "Status",
            "db_instance_status",
            "DbInstanceStatus",
            "replicas",
            "Replicas",
            "read_replica_source_db_instance_identifier",
        }
    ),
    "aws_s3_bucket": frozenset(
        {
            "bucket_prefix",  # Conflicts with bucket
        }
    ),
    "aws_iam_role": frozenset(
        {
            "arn",
            "Arn",
        }
    ),
    "aws_launch_template": frozenset(
        {
            "latest_version",
            "default_version",
            "LatestVersion",
            "DefaultVersion",
        }
    ),
    "aws_autoscaling_group": frozenset(
        {
            "arn",
            "Arn",
            "load_balancers",  # Use target_group_arns instead
            "instances",
            "Instances",
            "suspended_processes",
            "SuspendedProcesses",
            "enabled_metrics",
            "EnabledMetrics",
            "status",
            "Status",
            "warm_pool_size",
            "WarmPoolSize",
        }
    ),
    "aws_sns_topic": frozenset(
        {
            # Read-only subscription counts
            "subscriptions_confirmed",
            "SubscriptionsConfirmed",
            "subscriptions_pending",
            "SubscriptionsPending",
            "subscriptions_deleted",
            "SubscriptionsDeleted",
            # Computed effective policy
            "effective_delivery_policy",
            "EffectiveDeliveryPolicy",
            # Owner info
            "owner",
            "Owner",
            "topic_arn",
            "TopicArn",
        }
    ),
    "aws_sqs_queue": frozenset(
        {
            # Read-only queue attributes
            "arn",
            "Arn",
            "url",
            "Url",
            "QueueUrl",
            "approximate_number_of_messages",
            "ApproximateNumberOfMessages",
            "approximate_number_of_messages_not_visible",
            "ApproximateNumberOfMessagesNotVisible",
            "approximate_number_of_messages_delayed",
            "ApproximateNumberOfMessagesDelayed",
            "created_timestamp",
            "CreatedTimestamp",
            "last_modified_timestamp",
            "LastModifiedTimestamp",
        }
    ),
}

# Field name mappings: AWS API name -> Terraform schema name
# These apply globally across all resources
GLOBAL_FIELD_MAPPINGS: dict[str, str] = {
    # Common mappings
    "VpcId": "vpc_id",
    "SubnetId": "subnet_id",
    "SubnetIds": "subnet_ids",
    "SecurityGroupIds": "security_group_ids",
    "InstanceType": "instance_type",
    "ImageId": "ami",
    "KeyName": "key_name",
    "CidrBlock": "cidr_block",
    "AvailabilityZone": "availability_zone",
    "MapPublicIpOnLaunch": "map_public_ip_on_launch",
    "GroupName": "name",
    "GroupId": "id",
    "Description": "description",
    "VolumeType": "type",  # EBS volume_type -> type
    "VolumeSize": "size",  # EBS
    "Iops": "iops",
    "Throughput": "throughput",
    "Encrypted": "encrypted",
    "KmsKeyId": "kms_key_id",
    "MultiAz": "multi_az",
    "AvailabilityZones": "availability_zones",
    "StorageType": "storage_type",
    "AllocatedStorage": "allocated_storage",
    "Engine": "engine",
    "EngineVersion": "engine_version",
    "DBInstanceClass": "instance_class",
    "DBInstanceIdentifier": "identifier",
    "DBName": "db_name",
    "MasterUsername": "username",
    "MasterUserPassword": "password",
    "DBSubnetGroupName": "db_subnet_group_name",
    "VPCSecurityGroups": "vpc_security_group_ids",
    "DBParameterGroups": "parameter_group_name",
    "OptionGroupMemberships": "option_group_name",
    "PubliclyAccessible": "publicly_accessible",
    "StorageEncrypted": "storage_encrypted",
    "BackupRetentionPeriod": "backup_retention_period",
    "PreferredBackupWindow": "backup_window",
    "PreferredMaintenanceWindow": "maintenance_window",
    "AutoMinorVersionUpgrade": "auto_minor_version_upgrade",
    "LicenseModel": "license_model",
    "DeletionProtection": "deletion_protection",
    "IamDatabaseAuthenticationEnabled": "iam_database_authentication_enabled",
    "PerformanceInsightsEnabled": "performance_insights_enabled",
    "EnabledCloudwatchLogsExports": "enabled_cloudwatch_logs_exports",
    "Tags": "tags",
    # Load balancer
    "Type": "load_balancer_type",
    "Scheme": "internal",  # Needs value transformation too
    "IpAddressType": "ip_address_type",
    "SecurityGroups": "security_groups",
    "Subnets": "subnets",
    # Target group
    "TargetType": "target_type",
    "Protocol": "protocol",
    "Port": "port",
    "HealthCheckEnabled": "health_check_enabled",
    "HealthCheckIntervalSeconds": "health_check_interval",
    "HealthCheckPath": "health_check_path",
    "HealthCheckPort": "health_check_port",
    "HealthCheckProtocol": "health_check_protocol",
    "HealthCheckTimeoutSeconds": "health_check_timeout",
    "HealthyThresholdCount": "healthy_threshold",
    "UnhealthyThresholdCount": "unhealthy_threshold",
    # S3
    "Bucket": "bucket",
    "ACL": "acl",
    "VersioningConfiguration": "versioning",
    "ServerSideEncryptionConfiguration": "server_side_encryption_configuration",
    "LoggingEnabled": "logging",
    "LifecycleConfiguration": "lifecycle_rule",
    # IAM
    "RoleName": "name",
    "AssumeRolePolicyDocument": "assume_role_policy",
    "PolicyDocument": "policy",
    "PolicyName": "name",
    "PolicyArn": "policy_arn",
    # AutoScaling
    "MinSize": "min_size",
    "MaxSize": "max_size",
    "DesiredCapacity": "desired_capacity",
    "DefaultCooldown": "default_cooldown",
    "HealthCheckType": "health_check_type",
    "HealthCheckGracePeriod": "health_check_grace_period",
    "LaunchConfigurationName": "launch_configuration",
    "LaunchTemplate": "launch_template",
    "TargetGroupARNs": "target_group_arns",
    "TerminationPolicies": "termination_policies",
    "VPCZoneIdentifier": "vpc_zone_identifier",
    # Launch Template
    "LaunchTemplateName": "name",
    "LaunchTemplateData": "launch_template_data",
    "UserData": "user_data",
    "IamInstanceProfile": "iam_instance_profile",
    "Monitoring": "monitoring",
    "NetworkInterfaces": "network_interfaces",
    "BlockDeviceMappings": "block_device_mappings",
    "TagSpecifications": "tag_specifications",
    # ElastiCache
    "CacheClusterId": "cluster_id",
    "CacheNodeType": "node_type",
    "NumCacheNodes": "num_cache_nodes",
    "CacheParameterGroupName": "parameter_group_name",
    "CacheSubnetGroupName": "subnet_group_name",
    "SecurityGroupNames": "security_group_names",
    # CloudWatch
    "LogGroupName": "name",
    "RetentionInDays": "retention_in_days",
    "AlarmName": "alarm_name",
    "MetricName": "metric_name",
    "Namespace": "namespace",
    "Statistic": "statistic",
    "Period": "period",
    "EvaluationPeriods": "evaluation_periods",
    "Threshold": "threshold",
    "ComparisonOperator": "comparison_operator",
    "AlarmActions": "alarm_actions",
    "OKActions": "ok_actions",
    "InsufficientDataActions": "insufficient_data_actions",
    "Dimensions": "dimensions",
    # SQS
    "QueueName": "name",
    "DelaySeconds": "delay_seconds",
    "MaximumMessageSize": "max_message_size",
    "MessageRetentionPeriod": "message_retention_seconds",
    "ReceiveMessageWaitTimeSeconds": "receive_wait_time_seconds",
    "VisibilityTimeout": "visibility_timeout_seconds",
    # SNS
    "TopicName": "name",
    "DisplayName": "display_name",
}

# Resource-specific field mappings (override global mappings)
RESOURCE_FIELD_MAPPINGS: dict[str, dict[str, str]] = {
    "aws_launch_template": {
        # Launch template uses vpc_security_group_ids, not security_group_ids
        "SecurityGroupIds": "vpc_security_group_ids",
        "security_group_ids": "vpc_security_group_ids",
    },
    "aws_ebs_volume": {
        # EBS uses 'type' not 'volume_type'
        "volume_type": "type",
        "VolumeType": "type",
    },
    "aws_instance": {
        # EC2 instance uses different name for security groups
        "SecurityGroupIds": "vpc_security_group_ids",
    },
    "aws_lb": {
        # Load balancer 'Scheme' needs special handling
        "Scheme": "internal",  # Value also needs transformation (internet-facing -> false)
    },
    "aws_db_instance": {
        # RDS uses instance_class not db_instance_class
        "DBInstanceClass": "instance_class",
        "db_instance_class": "instance_class",
    },
    "aws_autoscaling_group": {
        # ASG uses vpc_zone_identifier for subnets, not subnet_ids
        "subnet_ids": "vpc_zone_identifier",
        "SubnetIds": "vpc_zone_identifier",
        # ASG uses protect_from_scale_in, not new_instances_protected_from_scale_in
        "new_instances_protected_from_scale_in": "protect_from_scale_in",
        "NewInstancesProtectedFromScaleIn": "protect_from_scale_in",
    },
}


class SchemaFilterTransformer(BaseCodifyTransformer):
    """
    Filter and map resource attributes to match Terraform provider schema.

    This transformer runs late in the pipeline (after reference replacement)
    to ensure generated Terraform code is valid.
    """

    name = "SchemaFilterTransformer"

    def __init__(self, enabled: bool = True) -> None:
        """
        Initialize the transformer.

        Args:
            enabled: Whether to enable the transformer
        """
        self.enabled = enabled
        self._filtered_count = 0
        self._mapped_count = 0

    def transform(self, graph: GraphEngineAdapter) -> GraphEngineAdapter:
        """
        Apply schema filtering to all resources.

        Args:
            graph: The resource graph to transform

        Returns:
            The transformed graph
        """
        if not self.enabled:
            return graph

        self._filtered_count = 0
        self._mapped_count = 0

        for resource in graph.iter_resources():
            if not resource.config:
                continue

            tf_type = self._get_terraform_type(resource)
            self._filter_and_map_config(resource, tf_type)

        logger.info(
            f"SchemaFilterTransformer: filtered {self._filtered_count} attributes, "
            f"mapped {self._mapped_count} field names"
        )

        return graph

    def _get_terraform_type(self, resource: ResourceNode) -> str:
        """Get the Terraform type for a resource."""
        if "_terraform_type" in resource.config:
            return resource.config["_terraform_type"]
        return str(resource.resource_type)

    def _filter_and_map_config(
        self,
        resource: ResourceNode,
        tf_type: str,
    ) -> None:
        """Filter and map a resource's config attributes."""
        config = resource.config
        keys_to_remove: list[str] = []
        keys_to_rename: dict[str, str] = {}

        # Get resource-specific blocklist
        resource_blocklist = RESOURCE_BLOCKLISTS.get(tf_type, frozenset())
        combined_blocklist = GLOBAL_BLOCKLIST | resource_blocklist

        # Get resource-specific field mappings
        resource_mappings = RESOURCE_FIELD_MAPPINGS.get(tf_type, {})

        for key in list(config.keys()):
            # Skip internal keys (handled by HCL renderer)
            if key.startswith("_"):
                continue

            # Check if key should be filtered
            if key in combined_blocklist:
                keys_to_remove.append(key)
                self._filtered_count += 1
                continue

            # Check for field name mapping
            # Resource-specific mapping takes precedence
            if key in resource_mappings:
                new_key = resource_mappings[key]
                if new_key != key:
                    keys_to_rename[key] = new_key
            elif key in GLOBAL_FIELD_MAPPINGS:
                new_key = GLOBAL_FIELD_MAPPINGS[key]
                if new_key != key:
                    keys_to_rename[key] = new_key

        # Apply removals
        for key in keys_to_remove:
            del config[key]

        # Apply renames
        for old_key, new_key in keys_to_rename.items():
            if old_key in config:
                # Don't overwrite if new key already exists
                if new_key not in config:
                    config[new_key] = config[old_key]
                    self._mapped_count += 1
                del config[old_key]

        # Convert policy dicts to JSON strings (for SNS, SQS, S3, IAM, etc.)
        # Terraform expects these as JSON strings, not HCL blocks
        self._convert_policy_to_json(config, tf_type)

        # Recursively process nested dicts (but not policies that are now strings)
        for key, value in config.items():
            if isinstance(value, dict) and not key.startswith("_"):
                self._filter_nested_config(value, tf_type)

    def _filter_nested_config(self, config: dict[str, Any], tf_type: str) -> None:
        """Filter nested config blocks."""
        keys_to_remove = []

        for key in config.keys():
            if key in GLOBAL_BLOCKLIST:
                keys_to_remove.append(key)
                self._filtered_count += 1

        for key in keys_to_remove:
            del config[key]

        # Recurse into nested dicts
        for _key, value in config.items():
            if isinstance(value, dict):
                self._filter_nested_config(value, tf_type)

    def _convert_policy_to_json(self, config: dict[str, Any], tf_type: str) -> None:
        """
        Convert policy dict fields to JSON strings.

        Terraform expects policy fields as JSON strings, not HCL blocks.
        This applies to SNS, SQS, S3, IAM and other resources.
        """
        import json

        # Fields that should be JSON-encoded strings, not blocks
        json_fields = {
            "policy",
            "Policy",
            "assume_role_policy",
            "AssumeRolePolicyDocument",
            "inline_policy",
            "PolicyDocument",
            "access_policy",
            "AccessPolicy",
            "key_policy",
            "KeyPolicy",
            "queue_policy",
            "QueuePolicy",
            "topic_policy",
            "TopicPolicy",
            "bucket_policy",
            "BucketPolicy",
            "delivery_policy",
            "DeliveryPolicy",
        }

        for key in list(config.keys()):
            if key in json_fields:
                value = config[key]
                # If it's already a string, leave it alone
                if isinstance(value, str):
                    continue
                # If it's a dict, convert to JSON string
                if isinstance(value, dict):
                    try:
                        config[key] = json.dumps(value, indent=2)
                    except (TypeError, ValueError):
                        # If JSON encoding fails, remove the field
                        del config[key]
                        logger.warning(
                            f"Failed to JSON-encode {key} for {tf_type}, removing"
                        )
