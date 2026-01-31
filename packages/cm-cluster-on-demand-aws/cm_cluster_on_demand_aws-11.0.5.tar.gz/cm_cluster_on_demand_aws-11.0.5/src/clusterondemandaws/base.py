# Copyright (c) 2004-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

import logging
import socket
import typing

import netaddr

from clusterondemand.clustercreate import check_client_ssh_access
from clusterondemand.exceptions import CODException, ValidationException
from clusterondemand.inbound_traffic_rule import ALL_PROTOCOL_NUMBER, InboundNetworkACLRule
from clusterondemand.paramvalidation import ParamValidator
from clusterondemand.utils import validate_arch_vs_machine_arch
from clusterondemandaws.instancetype import get_available_instance_types
from clusterondemandaws.paramvalidation import AWSParamValidator
from clusterondemandaws.vpc import get_aws_tag
from clusterondemandconfig import config

from .clientutils import list_volume_types

if typing.TYPE_CHECKING:
    from mypy_boto3_ec2.service_resource import EC2ServiceResource

log = logging.getLogger("cluster-on-demand")


class ClusterCommandBase:
    """Base class for all AWS cluster commands.

    This class only contains non-public validator methods that are intended to be used by
    descendant classes to validate user input. The general contract for all these methods is
    to perform various input sanitization checks, raising an Exception in the case of a failed
    check. If the check passes the _validate_xxx methods will simply return control to the
    caller with no return value.
    """
    def _validate_cluster_names_len_and_regex(self, names: list[str]) -> None:
        validate_max_name_len = config["validate_max_cluster_name_length"]
        for name in names:
            ParamValidator.validate_cluster_name(name, validate_max_name_len)

    def _validate_ssh_key_pair(self) -> None:
        if ("ssh_key_pair" in config and config["ssh_key_pair"] and not
            AWSParamValidator.validate_ssh_key_pair(
                config["ssh_key_pair"],
                config["aws_region"],
                config["aws_access_key_id"],
                config["aws_secret_key"])):
            raise ValidationException(
                "SSH Key pair '{keypair}' does not exist in region '{region}'".format(
                    keypair=config["ssh_key_pair"],
                    region=config["aws_region"]))

    def _validate_availability_zone(self) -> None:
        if ("aws_availability_zone" in config and config["aws_availability_zone"] and not
                AWSParamValidator.validate_availability_zone(
                    config["aws_availability_zone"],
                    config["aws_region"],
                    config["aws_access_key_id"],
                    config["aws_secret_key"])):
            raise ValidationException(
                "Availability zone '{zone}' does not exist in region '{region}'".format(
                    zone=config["aws_availability_zone"],
                    region=config["aws_region"]))

    def _validate_instance_types(self) -> None:
        if not AWSParamValidator.validate_instance_type(
                config["aws_region"],
                config["head_node_type"]):
            raise CODException(
                "Instance type '{itype}' does not exist in region '{region}'".format(
                    itype=config["head_node_type"],
                    region=config["aws_region"]))

        if not AWSParamValidator.validate_instance_type(
                config["aws_region"],
                config["node_type"]):
            raise CODException(
                "Instance type '{itype}' does not exist in region '{region}'" .format(
                    itype=config["node_type"],
                    region=config["aws_region"]))

    def _validate_instance_types_in_az(self) -> None:
        """Validate that the specified instance types are available in the specified AZ."""
        if not config.get("aws_availability_zone"):
            return  # No AZ specified, nothing to validate

        az = config["aws_availability_zone"]
        region = config["aws_region"]

        for instance_type in [config["head_node_type"], config["node_type"]]:
            is_available, available_zones = AWSParamValidator.get_instance_type_az_availability(
                instance_type, az, region
            )
            if not is_available:
                zones_str = ", ".join(available_zones) if available_zones else "none"
                raise ValidationException(
                    f"Instance type '{instance_type}' is not available in availability zone '{az}'. "
                    f"Available zones for this instance type: {zones_str}"
                )

    def _validate_instance_types_arch(self) -> None:
        def get_supported_archs(instance_type: str) -> str:
            instance_types = get_available_instance_types(config["aws_region"])
            archs = instance_types[instance_type].get("ProcessorInfo", {}).get("SupportedArchitectures", [])
            supported_archs = set()
            if "x86_64" in archs:
                supported_archs.add("x86_64")
            if "arm64" in archs:
                supported_archs.add("aarch64")
            if not supported_archs:
                raise CODException(
                    f"Instance type {instance_type!r} CPU architectures are not supported: " +
                    f"{', '.join(archs)}. Expected: x86_64, arm64"
                )
            assert len(supported_archs) == 1, (
                f"Instance type {instance_type!r} supports multiple architectures: {', '.join(archs)}. "
                "This is not supported by BCM."
            )
            return supported_archs.pop()

        head_type = config["head_node_type"]
        head_node_arch = get_supported_archs(head_type)
        node_type = config["node_type"]
        node_arch = get_supported_archs(node_type)

        config["arch"] = validate_arch_vs_machine_arch(config["arch"], head_node_arch, head_type, "head node")
        validate_arch_vs_machine_arch(config["arch"], node_arch, node_type, "compute node")

    @staticmethod
    def _validate_volume_types() -> None:
        volume_types = list_volume_types(
            region=config["aws_region"],
            aws_key_id=config["aws_access_key_id"],
            aws_secret=config["aws_secret_key"],
        )

        if config["head_node_root_volume_type"] not in volume_types:
            raise ValidationException(f"Requested root volume type {config['head_node_root_volume_type']!r} does not "
                                      f"exist in the region {config['aws_region']}. Please choose a valid volume type "
                                      f"from the following options: {', '.join(volume_types)}")

    @staticmethod
    def _validate_inbound_network_acl_rule(
        inbound_acl_rules: list[InboundNetworkACLRule] | None, configure_acl_rules: bool
    ) -> None:
        message = (
            "Cluster is created in a dedicated VPC and requires network ACL rules to be accessed, but "
            "insufficient ACL rules were requested. Cluster cannot be managed from the internet after creation. "
            "Please configure ACL rules to allow TCP port 22 or 8081 from at least one public CIDR block. "
            "Refer to '--inbound-network-acl-rule' help for examples and more information"
        )
        if configure_acl_rules:
            if inbound_acl_rules:
                if not check_client_ssh_access(inbound_acl_rules):
                    log.warning(
                        "SSH access is not allowed from the client IP address due to missing inbound network ACL "
                        "rules. Cluster creation will proceed, but waiting for SSH access is disabled "
                        "(wait_ssh set to 0)."
                    )
                    config["wait_ssh"] = 0
                else:
                    return

                access_ports = [22, 8081]
                for rule in inbound_acl_rules:
                    if rule.protocol_number == ALL_PROTOCOL_NUMBER:
                        return

                    # At least ssh or Base view ports should be open.
                    if (
                        rule.protocol_number == socket.IPPROTO_TCP and (
                            int(rule.dst_first_port) <= access_ports[0] <= int(rule.dst_last_port)
                            or int(rule.dst_first_port) <= access_ports[1] <= int(rule.dst_last_port)
                        )
                    ):
                        return

            raise CODException(message)

    @staticmethod
    def _validate_head_node_ip_in_cidr(ip_orig: str, cidr: str) -> None:
        """
        ref: https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Subnets.html
        """
        net = netaddr.IPNetwork(cidr)
        ip = netaddr.IPAddress(ip_orig)

        if (ip == net.broadcast) or (ip == net.network):
            raise CODException(
                "The head node's IP address can be neither the network address nor the broadcast address."
            )

        reserved_ips = net[1:4]  # In AWS, those IPs are reserved and cannot be used
        if ip in reserved_ips:
            raise CODException(f"The first 3 usable IPs (in this case"
                               f" {", ".join(map(str, reserved_ips))}) of every subnet "
                               f"are reserved by AWS, and cannot be used as a head node IP.")

        if ip not in net:
            raise CODException(f"The specified head node IP {ip_orig} is not within the {cidr} CIDR.")

    def _validate_params_existing_vpc(self, ec2: EC2ServiceResource) -> None:
        log.debug(f"Reusing existing VPC {config['existing_vpc_id']} - validating parameters")

        if not config["existing_vpc_id"]:
            raise CODException("existing_vpc_id is required but not provided")

        vpc = ec2.Vpc(config["existing_vpc_id"])
        try:
            vpc.load()
        except Exception:
            raise CODException(
                f"Failed to find VPC {config['existing_vpc_id']} in region {config['aws_region']}")

        vpc_name = get_aws_tag(vpc.tags, "Name", "<name not set>")
        log.debug(f"VPC '{config['existing_vpc_id']}' found. Name: '{vpc_name}'")

        # Confirm that specified subnets exist in the vpc
        if not config["existing_subnet_id"]:
            raise CODException("existing_subnet_id is required but not provided")

        log.debug(f"Validating {len(config['existing_subnet_id'])} specified subnets exist in VPC")

        vpc_subnets = list(vpc.subnets.all())
        vpc_subnet_ids = {subnet.id for subnet in vpc_subnets}

        for subnet_id in config["existing_subnet_id"]:
            if subnet_id not in vpc_subnet_ids:
                raise CODException(f"User specified subnet '{subnet_id}' was not found in "
                                   f"VPC '{config['existing_vpc_id']}' in region '{config['aws_region']}'")

        log.debug(f"All specified subnets {config['existing_subnet_id']} validated in VPC {config['existing_vpc_id']}")

        if config["head_node_internal_ip"]:
            head_node_subnet_id = config["existing_subnet_id"][0]
            log.debug(f"Validating head node IP {config['head_node_internal_ip']} is valid "
                      f"for subnet {head_node_subnet_id}")

            try:
                head_node_subnet = next(subnet for subnet in vpc_subnets if subnet.id == head_node_subnet_id)
            except StopIteration:
                raise CODException(f"Head node subnet {head_node_subnet_id} not found in "
                                   f"VPC {config['existing_vpc_id']}")

            self._validate_head_node_ip_in_cidr(config["head_node_internal_ip"], head_node_subnet.cidr_block)
