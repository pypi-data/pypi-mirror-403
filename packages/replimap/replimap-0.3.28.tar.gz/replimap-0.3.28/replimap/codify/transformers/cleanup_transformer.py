"""
Final Cleanup Transformer - Removes dirty fields before Terraform rendering.

VERSION: 3.7.20
STATUS: Production Ready

This transformer runs LAST in the pipeline to clean up:
1. Internal fields that leaked from earlier stages (e.g., SecurityGroupSplitter)
2. Fields that Terraform doesn't support for specific resource types
3. Temporary processing markers (fields starting with '_')
4. None/null values that would cause Terraform errors
5. Reserved name handling (e.g., "default" → "default-imported")
6. List unwrapping for singular blocks (e.g., default_action)
7. NUCLEAR OPTION: aws_network_acl ingress/egress removal
8. NUCLEAR OPTION: aws_lb_target_group matcher block → string (v3.7.9)
9. SQS type conversion safety net (v3.7.9)
10. SQS conflict resolution: kms_master_key_id vs sqs_managed_sse_enabled (v3.7.10)
11. SQS read-only fields removal: url, queue_url, queue_arn (v3.7.10)
12. SQS max_message_size capping to 262144 (AWS hard limit) (v3.7.11)
13. Case-insensitive key lookup for matcher handling (v3.7.11)
14. aws_instance dirty fields cleanup (asg_name, block_device_mappings, etc.) (v3.7.12)
15. aws_instance iam_instance_profile dict-to-string conversion (v3.7.13)
16. aws_autoscaling_group cleanup (launch_template, target_group_arns) (v3.7.13)

CRITICAL: This transformer must be the LAST stage in the codify pipeline.

v3.7.17 FIX: CRITICAL - 124 Terraform plan errors fixed:
             - aws_lb_target_group matcher: Scanner puts matcher INSIDE health_check!
               config["health_check"]["matcher"] = {"HttpCode": "200"}
               Now flattens to: health_check { matcher = "200" }
             - aws_lb_listener forward block: Transform target_group items
               AWS returns: { "TargetGroupArn": "...", "Weight": 1 }
               Must transform to: { "arn": "...", "weight": 1 }
v3.7.16 FIX: aws_lb_listener forward block fix (target_group, stickiness_config)
             aws_db_instance enabled_cloudwatch_logs_exports filter (invalid "instance")
v3.7.15 FIX: aws_instance root_block_device removal (unconfigurable attribute)
v3.7.14 FIX: aws_instance vpc_id removal (TF derives from subnet_id)
             aws_instance security_group_ids → vpc_security_group_ids rename
v3.7.13 FIX: aws_instance iam_instance_profile dict-to-string (extracts Arn/Id/Name)
             aws_autoscaling_group cleanup for complex blocks
v3.7.12 FIX: aws_instance cleanup - remove internal markers and API-native complex structures
             (asg_name, is_asg_managed, block_device_mappings, network_interfaces, etc.)
v3.7.11 FIX: SQS max_message_size capping to 262144 (AWS hard limit)
             Case-insensitive key lookup for matcher handling
v3.7.10 FIX: SQS conflict resolution - kms_master_key_id vs sqs_managed_sse_enabled
             SQS read-only fields removal (url, queue_url, queue_arn)
v3.7.9 FIX: NUCLEAR matcher fix - more aggressive handling of all matcher variations
            SQS type conversion safety net for fields that escaped schema mapper
v3.7.8 FIX: Version sync with transforms.py and schema_rules.yaml
v3.7.7 FIX: Version sync with transforms.py and schema_rules.yaml
v3.7.6 FIX: NUCLEAR OPTION for aws_network_acl (fixes 281 TF plan errors)
            AWS API returns incomplete ingress/egress rules (missing to_port,
            from_port, action fields). Rather than trying to fix incomplete
            rules, we remove ALL ingress/egress blocks. User imports an
            "empty shell" NACL and manages rules manually after import.
            This is safe and standard practice for Brownfield migration.
v3.7.5 FIX: Added aws_db_subnet_group default name handling
            Added aws_lb_listener default_action list unwrapping
            Enhanced aws_network_acl cleanup for all API-native fields
v3.7.4 FIX: Added aws_network_acl cleanup for API-native entry fields
            Added aws_lb_target_group matcher dict-to-string conversion
v3.7.2 FIX: Uses _get_terraform_type() to correctly identify resource types,
including dynamically typed resources like aws_security_group_rule.
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING, Any

from .base import BaseCodifyTransformer

if TYPE_CHECKING:
    from replimap.core.unified_storage import GraphEngineAdapter

logger = logging.getLogger(__name__)


class FinalCleanupTransformer(BaseCodifyTransformer):
    """
    Clean up dirty fields before Terraform code generation.

    This is the final safety net that removes:
    - Internal processing markers (fields starting with '_')
    - Resource-specific invalid fields (e.g., 'security_groups' in aws_security_group)
    - Any other fields that would cause terraform plan to fail

    MUST be the last transformer in the pipeline.
    """

    name = "FinalCleanupTransformer"

    # Fields to remove from specific resource types
    # These are fields that either:
    # - Leaked from earlier processing stages
    # - Are valid for other resource types but not this one
    # - Would cause terraform plan errors
    RESOURCE_CLEANUP_RULES: dict[str, set[str]] = {
        # security_groups is valid for aws_lb, but NOT for aws_security_group
        # It may leak from SecurityGroupSplitter or cross-type confusion
        "aws_security_group": {
            "security_groups",
            "ip_permissions",
            "ip_permissions_egress",
        },
        # aws_security_group_rule should not have these
        "aws_security_group_rule": {
            "security_groups",
        },
        # aws_lb_target_group: targets are managed separately
        "aws_lb_target_group": {
            "targets",
            "target_health_descriptions",
        },
        # v3.7.5: aws_lb_listener - Clean up API-native fields
        # Terraform expects default_action (singular), not default_actions (plural)
        "aws_lb_listener": {
            "default_actions",  # Should have been renamed to default_action
            "DefaultActions",
            # Read-only fields that shouldn't be in config
            "listener_arn",
            "ListenerArn",
        },
        # v3.7.6 NUCLEAR OPTION: aws_network_acl - Remove ALL ingress/egress blocks
        # AWS API returns incomplete rules (missing to_port, from_port, action).
        # Rather than try to fix incomplete rules, we remove ALL of them.
        # User imports an "empty shell" NACL and manages rules manually after import.
        # This is safe and standard practice for Brownfield migration.
        "aws_network_acl": {
            # 🚨 v3.7.20 FIX: Remove is_default AFTER DefaultResourceFilter uses it
            # The field is needed for filtering (Stage 1) but not valid TF attribute
            "is_default",
            "IsDefault",
            # NUCLEAR: Remove ALL rule blocks (they're incomplete from API)
            "ingress",
            "egress",
            "Ingress",
            "Egress",
            # Remove raw entries array
            "entries",
            "Entries",
            # Remove individual entry fields that may have leaked
            "rule_number",
            "rule_action",
            "protocol",
            "cidr_block",
            "ipv6_cidr_block",
            "icmp_type_code",
            "port_range",
            "from_port",
            "to_port",
            "action",
            # Also PascalCase variants
            "RuleNumber",
            "RuleAction",
            "Protocol",
            "CidrBlock",
            "Ipv6CidrBlock",
            "IcmpTypeCode",
            "PortRange",
            "FromPort",
            "ToPort",
            "Action",
        },
        # v3.7.4: aws_vpc_endpoint - policy_document should be policy
        "aws_vpc_endpoint": {
            "policy_document",
            "PolicyDocument",
        },
        # v3.7.15: aws_instance - Remove internal markers and API-native complex structures
        # These fields cause "Unsupported block type" or "Unsupported argument" errors
        # Terraform uses different block names (e.g., ebs_block_device, network_interface)
        "aws_instance": {
            # Internal Codify markers (must never reach Terraform)
            "asg_name",
            "is_asg_managed",
            # 🚨 v3.7.14: vpc_id must be removed - TF derives VPC from subnet_id
            "vpc_id",
            "VpcId",
            # API-native complex structures (Terraform uses different block names)
            "block_device_mappings",  # TF uses ebs_block_device, root_block_device
            "BlockDeviceMappings",
            "network_interfaces",  # TF uses network_interface (singular)
            "NetworkInterfaces",
            # 🚨 v3.7.19: root_block_device is now KEPT (not removed!)
            # We clean up problematic fields inside it (device_name) separately
            # Removing it entirely caused "must be replaced" errors (34 instances!)
            # Fields that often cause conflicts with Terraform defaults
            "capacity_reservation_specification",
            "CapacityReservationSpecification",
            "cpu_options",  # Often conflicts with instance_type defaults
            "CpuOptions",
            "metadata_options",  # Often conflicts with defaults
            "MetadataOptions",
            "enclave_options",
            "EnclaveOptions",
            "hibernation_options",
            "HibernationOptions",
            "maintenance_options",
            "MaintenanceOptions",
            "private_dns_name_options",
            "PrivateDnsNameOptions",
            # Read-only/computed fields
            "state",
            "State",
            "state_reason",
            "StateReason",
            "launch_time",
            "LaunchTime",
            "placement",  # Complex structure, use individual placement_* args
            "Placement",
            "monitoring",  # Use monitoring = true/false instead
            "Monitoring",
            "security_groups",  # Use vpc_security_group_ids instead
            "SecurityGroups",
        },
        # v3.7.13: aws_autoscaling_group - Remove complex blocks and read-only fields
        "aws_autoscaling_group": {
            # Complex structures that cause "Unsupported block type"
            "instances",
            "Instances",
            "suspended_processes",
            "SuspendedProcesses",
            "enabled_metrics",
            "EnabledMetrics",
            # Read-only/computed fields
            "auto_scaling_group_arn",
            "AutoScalingGroupARN",
            "status",
            "Status",
            "created_time",
            "CreatedTime",
            "default_cooldown",
            "DefaultCooldown",
            # Fields managed elsewhere
            "load_balancer_names",
            "LoadBalancerNames",
        },
    }

    # Fields that are always internal and should never appear in output
    ALWAYS_REMOVE_FIELDS: set[str] = {
        # Internal markers from SecurityGroupSplitter
        "_parent_sg_id",
        "_parent_sg_name",
    }

    def __init__(self) -> None:
        """Initialize the cleanup transformer."""
        self._fields_cleaned = 0
        self._resources_cleaned = 0
        self._graph: GraphEngineAdapter | None = None  # Set during transform()

    def _get_terraform_type(self, resource: Any) -> str:
        """
        Get the Terraform type for a resource.

        v3.7.2 FIX: Some resources (like aws_security_group_rule, aws_iam_*_policy_attachment)
        have their Terraform type stored in config["_terraform_type"] because they're
        dynamically created by transformers like SecurityGroupSplitter or IamNormalizer.
        """
        config = resource.config or {}
        if "_terraform_type" in config:
            return config["_terraform_type"]
        return str(resource.resource_type)

    def transform(self, graph: GraphEngineAdapter) -> GraphEngineAdapter:
        """
        Clean up all resources before rendering.

        Args:
            graph: The graph to transform

        Returns:
            The cleaned graph
        """
        self._fields_cleaned = 0
        self._resources_cleaned = 0
        self._graph = graph  # Store for EBS volume lookup in _cleanup_config

        for resource in graph.iter_resources():
            if not resource.config:
                continue

            resource_type = self._get_terraform_type(resource)
            cleaned = self._cleanup_config(resource.config, resource_type)

            if cleaned:
                self._resources_cleaned += 1

        if self._fields_cleaned > 0:
            logger.info(
                f"FinalCleanupTransformer: cleaned {self._fields_cleaned} fields "
                f"from {self._resources_cleaned} resources"
            )

        return graph

    def _cleanup_config(self, config: dict[str, Any], resource_type: str) -> bool:
        """
        Clean up a single resource config.

        Args:
            config: Resource configuration dict
            resource_type: Terraform resource type

        Returns:
            True if any fields were cleaned
        """
        cleaned = False

        # 0a. v3.7.17 NUCLEAR: aws_lb_target_group matcher (with case-insensitive key lookup)
        # Error: Blocks of type "matcher" are not expected here
        # Terraform expects matcher = "200", not matcher { http_code = "200" }
        # This fix aggressively converts ANY matcher to a simple string
        #
        # v3.7.17 FIX: AWS API sometimes returns NESTED Matcher structure:
        #   { "Matcher": { "HttpCode": "200" } }  <- Top-level Matcher wrapping nested dict
        # After schema mapper renames, this becomes:
        #   { "matcher": { "HttpCode": "200" } }  <- Still a nested dict!
        # We must flatten this to: matcher = "200"
        #
        # CRITICAL: The scanner puts matcher INSIDE health_check block:
        #   config["health_check"]["matcher"] = {"HttpCode": "200"}
        # We need to flatten it there AND at top level (in case it was moved)
        if resource_type == "aws_lb_target_group":
            # Check for matcher inside health_check block (most common case from scanner)
            hc_key = self._get_case_insensitive_key(config, "health_check")
            if hc_key and isinstance(config[hc_key], dict):
                hc = config[hc_key]
                matcher_key = self._get_case_insensitive_key(hc, "matcher")
                if matcher_key:
                    matcher_val = hc[matcher_key]
                    final_matcher = self._nuclear_flatten_matcher(matcher_val)
                    del hc[matcher_key]
                    if final_matcher:
                        hc["matcher"] = final_matcher
                        cleaned = True
                        logger.debug(
                            f"NUCLEAR: Flattened health_check.{matcher_key} to 'matcher' = '{final_matcher}'"
                        )
                    else:
                        cleaned = True
                        logger.debug(
                            f"NUCLEAR: Removed invalid health_check.{matcher_key} (will use default)"
                        )

            # Also check for matcher at top level (in case schema mapper moved it)
            matcher_key = self._get_case_insensitive_key(config, "matcher")
            if matcher_key:
                matcher_val = config[matcher_key]
                final_matcher = self._nuclear_flatten_matcher(matcher_val)
                # Remove the original key (might be "Matcher" or "matcher")
                del config[matcher_key]
                if final_matcher:
                    # Always use lowercase "matcher" for Terraform
                    config["matcher"] = final_matcher
                    cleaned = True
                    logger.debug(
                        f"NUCLEAR: Flattened {matcher_key} to 'matcher' = '{final_matcher}'"
                    )
                else:
                    # If we can't extract a value, just remove it
                    # Terraform will use the default "200"
                    cleaned = True
                    logger.debug(
                        f"NUCLEAR: Removed invalid {matcher_key} (will use default)"
                    )

        # 0b. v3.7.20: Removed db_subnet_group "default" name handling
        # DefaultResourceFilter now skips "default" db_subnet_group entirely
        # (AWS-managed, can't be changed without forcing replacement)

        # 0c. v3.7.11: SQS fixes - type conversion, conflicts, read-only fields, and capping
        # AWS API returns numeric fields as strings, Terraform expects integers
        # Also fixes: kms_master_key_id conflicts with sqs_managed_sse_enabled
        # And removes read-only fields like url
        # v3.7.11: Cap max_message_size to 262144 (AWS hard limit)
        if resource_type == "aws_sqs_queue":
            # Remove read-only fields
            read_only_fields = ["url", "queue_url", "queue_arn"]
            for field in read_only_fields:
                if field in config:
                    del config[field]
                    cleaned = True
                    logger.debug(f"SQS: Removed read-only field '{field}'")

            # Fix conflict: kms_master_key_id vs sqs_managed_sse_enabled
            # Terraform doesn't allow both to be set
            if "kms_master_key_id" in config and config["kms_master_key_id"]:
                if "sqs_managed_sse_enabled" in config:
                    del config["sqs_managed_sse_enabled"]
                    cleaned = True
                    logger.debug(
                        "SQS: Removed sqs_managed_sse_enabled (conflicts with kms_master_key_id)"
                    )

            # Type conversion safety net
            sqs_int_fields = [
                "delay_seconds",
                "max_message_size",
                "message_retention_seconds",
                "receive_wait_time_seconds",
                "visibility_timeout_seconds",
                "kms_data_key_reuse_period_seconds",
            ]
            for field in sqs_int_fields:
                if field in config and config[field] is not None:
                    try:
                        original = config[field]
                        config[field] = int(config[field])
                        if str(original) != str(config[field]):
                            cleaned = True
                            logger.debug(f"SQS: Converted {field} to int")
                    except (ValueError, TypeError):
                        # If conversion fails, leave as-is
                        pass

            # v3.7.11: Cap max_message_size to AWS hard limit (262144 bytes)
            # Error: expected max_message_size to be in the range (1024 - 262144), got 1048576
            # Some AWS API responses return values exceeding the actual limit
            if "max_message_size" in config and config["max_message_size"] is not None:
                try:
                    current_size = int(config["max_message_size"])
                    if current_size > 262144:
                        config["max_message_size"] = 262144
                        cleaned = True
                        logger.debug(
                            f"SQS: Capped max_message_size from {current_size} to 262144 (AWS limit)"
                        )
                except (ValueError, TypeError):
                    # If conversion fails, leave as-is
                    pass

        # 0d. v3.7.18: aws_elasticache_cluster engine_version format fix
        # Error: engine_version: 7.1.0 is invalid. For Redis v6 or higher, use <major>.<minor>.
        # AWS API returns full version like "7.1.0" but Terraform requires "7.1" for Redis v6+
        if resource_type == "aws_elasticache_cluster":
            engine_key = self._get_case_insensitive_key(config, "engine")
            version_key = self._get_case_insensitive_key(config, "engine_version")

            if version_key and config.get(version_key):
                version_str = str(config[version_key])
                engine = config.get(engine_key, "").lower() if engine_key else ""

                # For Redis v6+ and Memcached v1.6+, use major.minor format only
                # Split version into parts: "7.1.0" -> ["7", "1", "0"]
                parts = version_str.split(".")
                if len(parts) >= 2:
                    try:
                        major = int(parts[0])
                        # Redis v6+ requires major.minor format
                        # Memcached v1.6+ also uses major.minor format
                        if engine == "redis" and major >= 6:
                            new_version = f"{parts[0]}.{parts[1]}"
                            if new_version != version_str:
                                config[version_key] = new_version
                                cleaned = True
                                logger.debug(
                                    f"ElastiCache: Converted engine_version from '{version_str}' "
                                    f"to '{new_version}' (Redis v6+ requires major.minor)"
                                )
                        elif engine == "memcached" and major >= 1 and len(parts) > 2:
                            # Memcached 1.6+ also uses major.minor
                            minor = int(parts[1]) if len(parts) > 1 else 0
                            if major > 1 or (major == 1 and minor >= 6):
                                new_version = f"{parts[0]}.{parts[1]}"
                                if new_version != version_str:
                                    config[version_key] = new_version
                                    cleaned = True
                                    logger.debug(
                                        f"ElastiCache: Converted engine_version from '{version_str}' "
                                        f"to '{new_version}' (Memcached v1.6+ requires major.minor)"
                                    )
                    except (ValueError, TypeError):
                        # If version parsing fails, leave as-is
                        pass

        # 0e. v3.7.14: aws_instance fixes
        # Error: iam_instance_profile is a Block but Terraform expects a string (ARN or Name)
        # Error: vpc_id is not supported - Terraform derives VPC from subnet_id
        # Error: security_group_ids needs to be vpc_security_group_ids
        if resource_type == "aws_instance":
            # v3.7.14: Remove vpc_id (TF derives VPC from subnet_id)
            vpc_key = self._get_case_insensitive_key(config, "vpc_id")
            if vpc_key:
                del config[vpc_key]
                cleaned = True
                logger.debug(f"EC2: Removed {vpc_key} (TF derives from subnet_id)")

            # v3.7.14: Rename security_group_ids → vpc_security_group_ids
            sg_key = self._get_case_insensitive_key(config, "security_group_ids")
            if sg_key:
                sg_val = config[sg_key]
                del config[sg_key]
                config["vpc_security_group_ids"] = sg_val
                cleaned = True
                logger.debug(f"EC2: Renamed {sg_key} to vpc_security_group_ids")

            # Fix iam_instance_profile: flatten dict to string
            iam_key = self._get_case_insensitive_key(config, "iam_instance_profile")
            if iam_key:
                iam_val = config[iam_key]
                if isinstance(iam_val, dict):
                    # Extract ARN, Name, or Id (priority order)
                    flattened = (
                        iam_val.get("Arn")
                        or iam_val.get("arn")
                        or iam_val.get("Name")
                        or iam_val.get("name")
                        or iam_val.get("Id")
                        or iam_val.get("id")
                    )
                    if flattened:
                        del config[iam_key]
                        config["iam_instance_profile"] = flattened
                        cleaned = True
                        logger.debug(
                            f"EC2: Flattened {iam_key} dict to string: {flattened}"
                        )
                    else:
                        # If no usable value, remove it
                        del config[iam_key]
                        cleaned = True
                        logger.debug(f"EC2: Removed invalid {iam_key} (no ARN/Name/Id)")
                elif iam_key != "iam_instance_profile":
                    # Normalize key name to lowercase
                    val = config[iam_key]
                    del config[iam_key]
                    config["iam_instance_profile"] = val
                    cleaned = True

            # 🚨 v3.7.20: Enrich and clean up root_block_device
            # Previous fixes (v3.7.19) kept root_block_device but only had delete_on_termination.
            # Without volume_size, Terraform uses AMI default → "must be replaced" errors.
            # Now we:
            # 1. Look up the EBS volume using volume_id to get volume_size/volume_type
            # 2. Remove problematic fields (device_name, encrypted, volume_id)
            # 3. Keep volume_size, volume_type, delete_on_termination
            rbd_key = self._get_case_insensitive_key(config, "root_block_device")
            if rbd_key and config.get(rbd_key):
                rbd_val = config[rbd_key]
                # Handle both list and dict formats
                blocks_to_process = rbd_val if isinstance(rbd_val, list) else [rbd_val]
                for block in blocks_to_process:
                    if not isinstance(block, dict):
                        continue

                    # 🚨 v3.7.20: Enrich with EBS volume data
                    volume_id = block.get("volume_id") or block.get("VolumeId")

                    # 🚨 v3.7.20 FIX: RefTransformer converts volume_id to Terraform reference
                    # e.g., "vol-123" → "${aws_ebs_volume.vol-123.id}"
                    # Extract the actual volume ID from the reference for graph lookup
                    actual_volume_id = volume_id
                    if volume_id and volume_id.startswith("${aws_ebs_volume."):
                        # Parse: ${aws_ebs_volume.TERRAFORM_NAME.id} → TERRAFORM_NAME
                        # The terraform_name is often the volume ID (e.g., vol-0d732bace618b2599)
                        match = re.match(
                            r"\$\{aws_ebs_volume\.([^.]+)\.id\}", volume_id
                        )
                        if match:
                            actual_volume_id = match.group(1)
                            logger.debug(
                                f"EC2: Extracted volume ID '{actual_volume_id}' from "
                                f"Terraform reference '{volume_id}'"
                            )

                    if actual_volume_id and self._graph:
                        # Try direct lookup by ID first
                        ebs_resource = self._graph.get_resource(actual_volume_id)

                        # 🚨 v3.7.20 FIX: Verify we got an EBS volume, not a different resource
                        # with the same ID/terraform_name (e.g., CloudWatch Log Group)
                        if (
                            ebs_resource
                            and str(ebs_resource.resource_type) != "aws_ebs_volume"
                        ):
                            logger.debug(
                                f"EC2: Found resource '{actual_volume_id}' but it's "
                                f"{ebs_resource.resource_type}, not aws_ebs_volume"
                            )
                            ebs_resource = None

                        # If not found, try finding by terraform_name
                        # (RefTransformer may use terraform_name like "test_elements" instead of ID)
                        if not ebs_resource:
                            for res in self._graph.iter_resources():
                                if (
                                    str(res.resource_type) == "aws_ebs_volume"
                                    and res.terraform_name == actual_volume_id
                                ):
                                    ebs_resource = res
                                    logger.debug(
                                        f"EC2: Found EBS volume by terraform_name "
                                        f"'{actual_volume_id}' (id={res.id})"
                                    )
                                    break

                        if ebs_resource and ebs_resource.config:
                            ebs_config = ebs_resource.config
                            # Copy volume_size and volume_type from EBS volume
                            # NOTE: Schema mapper renames volume_size→size, volume_type→type
                            # So we look for "size" and "type" in EBS config
                            if "size" in ebs_config and "volume_size" not in block:
                                block["volume_size"] = ebs_config["size"]
                                logger.debug(
                                    f"EC2: Enriched root_block_device with "
                                    f"volume_size={ebs_config['size']} from EBS {volume_id}"
                                )
                            else:
                                logger.warning(
                                    f"EC2: EBS volume {volume_id} has no 'size' field, "
                                    f"available keys: {list(ebs_config.keys())}"
                                )
                            # 🚨 v3.7.20 FIX: Look for "type" not "volume_type"
                            # Schema mapper renames volume_type → type for aws_ebs_volume
                            if "type" in ebs_config and "volume_type" not in block:
                                block["volume_type"] = ebs_config["type"]
                                logger.debug(
                                    f"EC2: Enriched root_block_device with "
                                    f"volume_type={ebs_config['type']} from EBS {volume_id}"
                                )
                        else:
                            logger.warning(
                                f"EC2: EBS volume '{actual_volume_id}' not found in graph "
                                f"(root_block_device enrichment skipped)"
                            )
                    elif actual_volume_id and not self._graph:
                        logger.warning(
                            f"EC2: Graph not available for EBS lookup of {actual_volume_id}"
                        )
                    elif not actual_volume_id:
                        logger.debug(
                            f"EC2: No volume_id in root_block_device, "
                            f"block keys: {list(block.keys())}"
                        )

                    # Remove problematic fields that cause TF errors
                    for bad_field in [
                        "device_name",
                        "DeviceName",
                        "encrypted",
                        "Encrypted",
                        "volume_id",  # Internal field for EBS lookup
                        "VolumeId",
                    ]:
                        if bad_field in block:
                            del block[bad_field]
                            cleaned = True
                            logger.debug(
                                f"EC2: Removed {bad_field} from root_block_device"
                            )

                # Normalize key to lowercase
                if rbd_key != "root_block_device":
                    config["root_block_device"] = config.pop(rbd_key)
                    cleaned = True

        # 0f. v3.7.13: aws_autoscaling_group fixes
        # Error: launch_template is a complex block, target_group_arns conflicts
        if resource_type == "aws_autoscaling_group":
            # Remove complex blocks that Terraform handles differently
            asg_remove_fields = [
                # Complex structures that cause "Unsupported block type"
                "instances",
                "Instances",
                "load_balancer_names",  # Use target_group_arns instead
                "LoadBalancerNames",
                "suspended_processes",
                "SuspendedProcesses",
                "enabled_metrics",
                "EnabledMetrics",
                # Read-only fields
                "auto_scaling_group_arn",
                "AutoScalingGroupARN",
                "status",
                "Status",
                "created_time",
                "CreatedTime",
            ]
            for field in asg_remove_fields:
                if field in config:
                    del config[field]
                    cleaned = True
                    logger.debug(f"ASG: Removed field '{field}'")

            # Fix launch_template if it's a complex dict
            lt_key = self._get_case_insensitive_key(config, "launch_template")
            if lt_key and isinstance(config[lt_key], dict):
                lt = config[lt_key]
                # Terraform expects: launch_template { id = "..." version = "..." }
                # AWS API returns: LaunchTemplate { LaunchTemplateId = "..." Version = "1" }
                clean_lt = {}
                # Extract id
                lt_id = (
                    lt.get("LaunchTemplateId")
                    or lt.get("launch_template_id")
                    or lt.get("id")
                )
                if lt_id:
                    clean_lt["id"] = lt_id
                # Extract version
                lt_version = lt.get("Version") or lt.get("version")
                if lt_version:
                    clean_lt["version"] = str(lt_version)
                # Replace with clean structure
                if clean_lt:
                    del config[lt_key]
                    config["launch_template"] = clean_lt
                    cleaned = True
                    logger.debug("ASG: Cleaned launch_template structure")

        # 0f. v3.7.17: Special handling for aws_lb_listener default_action
        # AWS API returns DefaultActions as a list, Terraform expects single block
        # The list needs to be unwrapped since terraform wants default_action (singular)
        #
        # v3.7.17 FIX: Forward block target_group items need transformation:
        #   AWS returns: { "TargetGroupArn": "arn:...", "Weight": 1 }
        #   Terraform expects: { "arn": "arn:...", "weight": 1 }
        #
        # CRITICAL: Check BOTH default_action (after rename) AND default_actions (before)
        da_key = None
        if "default_action" in config:
            da_key = "default_action"
        elif "default_actions" in config:
            da_key = "default_actions"

        if resource_type == "aws_lb_listener" and da_key:
            default_action = config[da_key]
            if isinstance(default_action, list) and default_action:
                # Unwrap list - Terraform expects singular block (repeated for multiple)
                # For now, we keep the list but ensure each item has lowercase keys
                unwrapped = []
                for action in default_action:
                    if isinstance(action, dict):
                        # Ensure keys are lowercase snake_case
                        clean_action = {}
                        for k, v in action.items():
                            # Convert PascalCase to snake_case
                            new_key = self._to_snake_case(k)
                            clean_action[new_key] = v

                        # v3.7.17: Fix forward block structure
                        # Error: Insufficient target_group blocks / target_group_stickiness_config
                        forward_key = None
                        for fk in ["forward", "forward_config"]:
                            if fk in clean_action:
                                forward_key = fk
                                break

                        if forward_key:
                            forward = clean_action[forward_key]
                            if isinstance(forward, dict):
                                # Remove unsupported fields
                                forward.pop("target_group_stickiness_config", None)
                                forward.pop("TargetGroupStickinessConfig", None)

                                # Get target_groups from various possible keys
                                tgs = None
                                for tg_key in [
                                    "target_groups",
                                    "TargetGroups",
                                    "target_group",
                                ]:
                                    if tg_key in forward:
                                        tgs = forward.pop(tg_key)
                                        break

                                # v3.7.17 CRITICAL: Transform target_group items
                                # AWS: {"TargetGroupArn": "...", "Weight": 1}
                                # TF:  {"arn": "...", "weight": 1}
                                if isinstance(tgs, list) and tgs:
                                    clean_tgs = []
                                    for tg in tgs:
                                        if isinstance(tg, dict):
                                            clean_tg = {}
                                            # Map AWS keys to Terraform keys
                                            arn = (
                                                tg.get("TargetGroupArn")
                                                or tg.get("target_group_arn")
                                                or tg.get("arn")
                                            )
                                            weight = tg.get("Weight") or tg.get(
                                                "weight"
                                            )
                                            if arn:
                                                clean_tg["arn"] = arn
                                            if weight is not None:
                                                clean_tg["weight"] = int(weight)
                                            if clean_tg:
                                                clean_tgs.append(clean_tg)
                                        else:
                                            clean_tgs.append(tg)
                                    if clean_tgs:
                                        forward["target_group"] = clean_tgs
                                        # Normalize to "forward" key
                                        if forward_key != "forward":
                                            del clean_action[forward_key]
                                        clean_action["forward"] = forward
                                else:
                                    # No target_groups found - remove empty forward block
                                    # Fall back to target_group_arn if present
                                    del clean_action[forward_key]
                                    logger.debug(
                                        "LB Listener: Removed empty forward block"
                                    )
                            else:
                                # forward is not a dict - remove it
                                del clean_action[forward_key]
                        unwrapped.append(clean_action)
                    else:
                        unwrapped.append(action)
                # Always use lowercase singular key
                if da_key != "default_action":
                    del config[da_key]
                config["default_action"] = unwrapped
                cleaned = True
                logger.debug("Cleaned aws_lb_listener default_action list")

        # 0g. v3.7.16: Fix aws_db_instance enabled_cloudwatch_logs_exports
        # Error: expected enabled_cloudwatch_logs_exports to be one of valid values
        # Invalid values like "instance" need to be filtered out
        if resource_type == "aws_db_instance":
            logs_key = self._get_case_insensitive_key(
                config, "enabled_cloudwatch_logs_exports"
            )
            if logs_key and isinstance(config[logs_key], list):
                # Valid values for different RDS engines
                valid_logs = {
                    "agent",
                    "alert",
                    "audit",
                    "diag.log",
                    "error",
                    "general",
                    "iam-db-auth-error",
                    "listener",
                    "notify.log",
                    "oemagent",
                    "postgresql",
                    "slowquery",
                    "trace",
                    "upgrade",
                }
                original = config[logs_key]
                filtered = [v for v in original if v in valid_logs]
                if len(filtered) != len(original):
                    removed = set(original) - set(filtered)
                    config[logs_key] = filtered
                    cleaned = True
                    logger.debug(f"RDS: Filtered invalid logs exports: {removed}")

        # 1. Remove internal markers (fields starting with '_')
        # 🚨 v3.7.18 FIX: Preserve _import_id and _terraform_type - these are needed by:
        # - ImportGenerator: uses _import_id for terraform import blocks
        # - HCL Generator: uses _terraform_type for dynamically-typed resources
        PRESERVE_INTERNAL_FIELDS = {"_import_id", "_terraform_type"}
        internal_fields = [
            k
            for k in config.keys()
            if k.startswith("_") and k not in PRESERVE_INTERNAL_FIELDS
        ]
        for field in internal_fields:
            del config[field]
            self._fields_cleaned += 1
            cleaned = True
            logger.debug(f"Removed internal field '{field}' from {resource_type}")

        # 1b. Remove None/null values (Terraform doesn't like explicit nulls)
        # This prevents errors like: Invalid value for "value" parameter
        null_fields = [k for k, v in config.items() if v is None]
        for field in null_fields:
            del config[field]
            self._fields_cleaned += 1
            cleaned = True
            logger.debug(f"Removed null field '{field}' from {resource_type}")

        # 2. Remove always-remove fields
        for field in self.ALWAYS_REMOVE_FIELDS:
            if field in config:
                del config[field]
                self._fields_cleaned += 1
                cleaned = True
                logger.debug(
                    f"Removed always-remove field '{field}' from {resource_type}"
                )

        # 3. Remove resource-specific invalid fields
        invalid_fields = self.RESOURCE_CLEANUP_RULES.get(resource_type, set())
        for field in invalid_fields:
            if field in config:
                del config[field]
                self._fields_cleaned += 1
                cleaned = True
                logger.debug(f"Removed invalid field '{field}' from {resource_type}")

        # 4. Recursively clean nested structures
        for _key, value in list(config.items()):
            if isinstance(value, dict):
                nested_cleaned = self._cleanup_nested(value)
                if nested_cleaned:
                    cleaned = True
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        nested_cleaned = self._cleanup_nested(item)
                        if nested_cleaned:
                            cleaned = True

        return cleaned

    def _cleanup_nested(self, nested: dict[str, Any]) -> bool:
        """
        Clean up internal fields from nested structures.

        Args:
            nested: Nested dict to clean

        Returns:
            True if any fields were cleaned
        """
        cleaned = False

        # Remove internal markers (but preserve _import_id and _terraform_type)
        # v3.7.20 FIX: Consistent with top-level cleanup
        PRESERVE_INTERNAL_FIELDS = {"_import_id", "_terraform_type"}
        internal_fields = [
            k
            for k in nested.keys()
            if k.startswith("_") and k not in PRESERVE_INTERNAL_FIELDS
        ]
        for field in internal_fields:
            del nested[field]
            self._fields_cleaned += 1
            cleaned = True

        return cleaned

    @staticmethod
    def _to_snake_case(name: str) -> str:
        """
        Convert PascalCase/camelCase to snake_case.

        Examples:
            Type → type
            TargetGroupArn → target_group_arn
            ForwardConfig → forward_config
        """
        import re

        # Handle acronyms (2+ uppercase) followed by word start
        s1 = re.sub(r"([A-Z]{2,})([A-Z][a-z])", r"\1_\2", name)
        # Handle camelCase - insert _ between lower/digit and upper
        s2 = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1)
        return s2.lower()

    @staticmethod
    def _get_case_insensitive_key(config: dict[str, Any], key: str) -> str | None:
        """
        v3.7.11: Get the actual key from config using case-insensitive matching.

        This handles cases where the key might be "Matcher", "matcher", "MATCHER", etc.

        Args:
            config: The configuration dict to search
            key: The key to find (case-insensitive)

        Returns:
            The actual key from config if found, None otherwise
        """
        key_lower = key.lower()
        for k in config.keys():
            if k.lower() == key_lower:
                return k
        return None

    @staticmethod
    def _nuclear_flatten_matcher(value: Any, depth: int = 0) -> str | None:
        """
        v3.7.17 NUCLEAR: Aggressively flatten matcher to a simple string.

        Handles all possible variations of matcher structure:
        - "200" → "200"
        - {"HttpCode": "200"} → "200"
        - [{"HttpCode": "200"}] → "200"
        - {"http_code": "200"} → "200"
        - {"GrpcCode": "0"} → "0"
        - {"Matcher": {"HttpCode": "200"}} → "200"
        - {"matcher": {"http_code": "200"}} → "200"

        v3.7.17 FIX: Added depth limit to prevent infinite recursion
        and improved handling of nested structures.

        Returns:
            The extracted code string, or None if extraction fails
        """
        # Prevent infinite recursion
        if depth > 5:
            return None

        # Already a simple string - we're done
        if isinstance(value, str):
            # If it's a string with a dash (like "200-299"), it's a valid range
            return value

        # Handle numeric values
        if isinstance(value, (int, float)):
            return str(int(value))

        # Unwrap list
        if isinstance(value, list):
            if not value:
                return None
            value = value[0]
            # Recurse with unwrapped value
            return FinalCleanupTransformer._nuclear_flatten_matcher(value, depth + 1)

        # Should be a dict now
        if not isinstance(value, dict):
            return None

        # First priority: Check for nested Matcher key (double-wrapped)
        # This is the most common case causing the 76 errors
        for matcher_key in ["Matcher", "matcher", "MATCHER"]:
            if matcher_key in value:
                nested = value[matcher_key]
                result = FinalCleanupTransformer._nuclear_flatten_matcher(
                    nested, depth + 1
                )
                if result:
                    return result

        # Try all known key variations for HTTP/GRPC codes
        code_keys = [
            "HttpCode",
            "http_code",
            "httpcode",
            "GrpcCode",
            "grpc_code",
            "grpccode",
            "Code",
            "code",
        ]

        for key in code_keys:
            if key in value:
                extracted = value[key]
                if isinstance(extracted, str):
                    return extracted
                if isinstance(extracted, (int, float)):
                    return str(int(extracted))

        # Last resort: take the first value if it looks like a code
        for v in value.values():
            if isinstance(v, str):
                # Check if it's a numeric string or a range like "200-299"
                if v.replace("-", "").isdigit():
                    return v
            if isinstance(v, (int, float)):
                return str(int(v))
            # If value is a nested dict, recurse
            if isinstance(v, dict):
                result = FinalCleanupTransformer._nuclear_flatten_matcher(v, depth + 1)
                if result:
                    return result

        # Nothing found
        return None

    @property
    def fields_cleaned(self) -> int:
        """Return the number of fields cleaned."""
        return self._fields_cleaned

    @property
    def resources_cleaned(self) -> int:
        """Return the number of resources cleaned."""
        return self._resources_cleaned
