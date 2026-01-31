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

import hashlib
import logging
import re
import typing
from datetime import datetime
from enum import Enum, auto
from functools import cached_property, lru_cache
from typing import Any, Literal

import tenacity

from clusterondemand import utils
from clusterondemand.exceptions import CODException
from clusterondemand.images.find import CODImage
from clusterondemandaws.awsconnection import create_aws_service_client, create_aws_service_resource
from clusterondemandconfig import config

from . import efs

if typing.TYPE_CHECKING:
    from mypy_boto3_ec2.client import EC2Client
    from mypy_boto3_ec2.service_resource import EC2ServiceResource, Instance, RouteTable, Subnet, Vpc
    from mypy_boto3_ec2.type_defs import (
        AllocateAddressResultTypeDef,
        FilterTypeDef,
        NatGatewayTypeDef,
        NetworkInterfacePrivateIpAddressTypeDef,
        TagTypeDef
    )
    from mypy_boto3_ec2.waiter import NatGatewayAvailableWaiter, NatGatewayDeletedWaiter
    from mypy_boto3_efs.client import EFSClient

    # Helper class for convenient and safe usage of resources with common properties.
    class _ResourceProtocol(typing.Protocol):
        @property
        def tags(self) -> list[TagTypeDef] | None:
            ...

    class _ResourceWithIdProtocol(_ResourceProtocol, typing.Protocol):
        @property
        def id(self) -> str:
            ...

log = logging.getLogger("cluster-on-demand")
BCM_TYPE_HEAD_NODE = "Head node"
BCM_TAG_NO_PUBLIC_IP = "BCM No public IP"
# For backward compatibility. The one with underscores should be eventually phased out.
BCM_CLUSTER_NAME_TAGS = ["BCM Cluster", "BCM_Cluster"]


def construct_bright_tags(cluster_name: str, obj_name: str, bcm_type: str | None = None) -> list[TagTypeDef]:
    tags_dict: dict[str, str] = {
        "BCM Created at": datetime.utcnow().isoformat() + "Z",  # fix missing timezone
        "BCM Created by": utils.get_user_at_fqdn_hostname(),
        "BCM Cluster": cluster_name,
        "BCM Bursting": "on-demand",
        # This one has to follow a slightly different naming convention (i.e. no "BCM"
        # prefix), because this tag has a special meaning for AWS.
        "Name": obj_name
    }
    if bcm_type:
        tags_dict["BCM Type"] = bcm_type
        if bcm_type == BCM_TYPE_HEAD_NODE and not config.get("head_node_assign_public_ip", True):
            tags_dict[BCM_TAG_NO_PUBLIC_IP] = ""

    tags_dict.update({str(k): str(v) for k, v in config.get("cluster_tags", [])})
    tags: list[TagTypeDef] = [{"Key": key, "Value": value} for key, value in tags_dict.items()]
    return tags


class Cluster:
    # AWS eIP assignment failures occur rarely and can be worked around
    # by retrying for 2.5+ minutes (see CM-9991).
    # Let's make it 5 minutes to make sure we don't leave an eIP allocation unassigned,
    # which costs money.
    IP_ASSIGNMENT_RETRY_DELAY = 10
    IP_ASSIGNMENT_RETRIES = 30

    def __init__(
        self,
        name: str,
        head_node_image: CODImage | None = None,
        vpc: Vpc | None = None,
        head_nodes: list[Instance] | None = None,
    ) -> None:

        self.ec2: EC2ServiceResource = create_aws_service_resource(service_name="ec2")
        self.ec2c: EC2Client = create_aws_service_client(service_name="ec2", api_version="2016-11-15")
        self.efs_client: EFSClient = create_aws_service_client(service_name="efs")
        self.name = name
        self.head_node_image = head_node_image
        self.vpc = vpc
        self.primary_head_node: Instance | None = None
        self.secondary_head_node: Instance | None = None
        self.active_head_node: Instance | None = None
        self.passive_head_node: Instance | None = None
        self.set_primary_secondary_head_nodes(head_nodes)
        self.is_ha = bool(self.secondary_head_node)
        self.set_active_passive_head_nodes()
        self.error_message: str | None = None

    @cached_property
    def efs_id(self) -> str | None:
        return self.get_efs_id()

    @classmethod
    def get_tag_value(cls, tags: list[TagTypeDef] | None, tag_key: str, default: str | None = None) -> str:
        try:
            return next(tag["Value"] for tag in tags or [] if tag["Key"] == tag_key)
        except StopIteration:
            if default is None:
                raise CODException(f"No {tag_key} tag found")
            return default

    @classmethod
    def get_resource_name(cls, resource: _ResourceProtocol, default: str | None = None) -> str:
        return cls.get_tag_value(resource.tags, "Name", default=default)

    @classmethod
    def get_resource_name_or_id(cls, resource: _ResourceWithIdProtocol, default: str | None = None) -> str:
        try:
            return cls.get_tag_value(resource.tags, "Name", default=default)
        except Exception:
            return resource.id

    @classmethod
    def find(cls, names: list[str]) -> typing.Iterator[Cluster]:
        ec2: EC2ServiceResource = create_aws_service_resource(service_name="ec2")

        # Find clusters which VPCs were created by COD-AWS. This is the default use case for COD-AWS.
        log.debug(f"Searching for VPCs with cluster name patterns: {names}")
        cluster_name_filter: FilterTypeDef = {"Name": "tag:BCM Cluster", "Values": list(names)}
        for vpc in ec2.vpcs.filter(Filters=[cluster_name_filter]):
            cluster_name = cls.get_cluster_name(vpc)
            yield cls(cluster_name, vpc=vpc)

        # Find clusters by head nodes created by COD-AWS.
        # This way we handle clusters created in existing VPC (using --exising-vpc=...)
        #
        # First of all, let's find all head nodes and group them by cluster name.
        # This is needed, because HA clusters have multiple head nodes.
        log.debug(f"Searching for head nodes with cluster name patterns: {names}")
        headnodes_filters: list[FilterTypeDef] = [
            cluster_name_filter,
            {"Name": "tag:BCM Type", "Values": ["Head node"]},
            # All possible instance states except for terminated.
            # Instance states: https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_InstanceState.html
            {"Name": "instance-state-name", "Values": ["pending", "running", "shutting-down", "stopping", "stopped"]},
        ]
        cluster_name_to_head_nodes: dict[str, list[Instance]] = {}
        for head_node in ec2.instances.filter(Filters=headnodes_filters):
            if not head_node.vpc:
                log.debug("Skipping head node %r as having no VPC (being deleted?)",
                          cls.get_resource_name_or_id(head_node))
                continue

            head_node_cluster_name = cls.get_cluster_name(head_node)
            vpc_cluster_name = cls.get_cluster_name(head_node.vpc, default="")

            if head_node_cluster_name == vpc_cluster_name:  # already listed above
                log.debug(
                    "Skipping head node %r as already listed for VPC %r",
                    cls.get_resource_name_or_id(head_node),
                    cls.get_resource_name_or_id(head_node.vpc),
                )
                continue

            cluster_name = head_node_cluster_name
            cluster_name_to_head_nodes.setdefault(cluster_name, [])
            cluster_name_to_head_nodes[cluster_name].append(head_node)

        # Now return the clusters.
        for cluster_name, head_nodes in cluster_name_to_head_nodes.items():
            # We assume that one cluster has only one VPC associated with it.
            # Thus, let's skip the cases when multiple head nodes have different VPC somehow.
            if len(set(h.vpc.id for h in head_nodes)) != 1:
                head_nodes_info = ", ".join(f"{h.id} ({cls.get_resource_name(h)})" for h in head_nodes)
                log.warning(f"Inconsistent cluster found: exactly one VPC is expected. Skipping. "
                            f"Cluster name: {cluster_name}, "
                            f"Head Nodes: {head_nodes_info}")
                continue
            yield cls(cluster_name, vpc=head_nodes[0].vpc, head_nodes=head_nodes)

    def __unicode__(self) -> str:
        return "{} {!r} {!r} {}".format(self.name,
                                        self.vpc,
                                        self.primary_head_node,
                                        self.primary_head_node and self.primary_head_node.state["Name"])

    def is_created_by_us(self, tags: list[TagTypeDef] | None) -> bool:
        def has_cluster_name_tag(tags: list[TagTypeDef] | None) -> bool:
            return any(
                self.get_tag_value(tags, cluster_name_tag, default="") == self.name
                for cluster_name_tag in BCM_CLUSTER_NAME_TAGS
            )

        # If VPC is created by us, then let's consider all resources as created by us.
        # This will help to handle old clusters (e.g. BCM 9.2) which may have untagged resources.
        return has_cluster_name_tag(tags) or (self.vpc is not None and has_cluster_name_tag(self.vpc.tags))

    @classmethod
    def get_cluster_name(cls, resource: _ResourceWithIdProtocol, default: str | None = None) -> str:
        cluster_name = next(
            (
                cluster_name
                for cluster_name_tag in BCM_CLUSTER_NAME_TAGS
                if (cluster_name := cls.get_tag_value(resource.tags, cluster_name_tag, default=""))
            ),
            None
        )
        if not cluster_name and default is None:
            raise CODException(f"No cluster name tag found in {cls.get_resource_name_or_id(resource)}")
        return cluster_name or typing.cast(str, default)

    def find_head_nodes(self) -> list[Instance] | None:
        if not self.vpc:
            return None

        instances = list(self.vpc.instances.filter(Filters=[
            {"Name": "tag:BCM Type", "Values": [BCM_TYPE_HEAD_NODE]},
            {"Name": "instance-state-name",
             "Values": ["pending", "running", "shutting-down", "stopping", "stopped"]},
        ]))

        # Filter out head nodes belonging to other clusters (if any).
        # (We do it on the client side to account for different cluster name tags as EC2 API doesn't seem to support
        # the OR operator. Once "BCM_Cluster" is deprecated, the filtering can moved to the server side.)
        instances = [i for i in instances if self.is_created_by_us(i.tags)]

        if not instances:
            return None

        return instances

    def set_primary_secondary_head_nodes(self, head_nodes: list[Instance] | None = None) -> None:
        if head_nodes is None:
            head_nodes = self.find_head_nodes()
        if not head_nodes:
            return

        try:
            if len(head_nodes) == 1:
                self.primary_head_node, self.secondary_head_node = head_nodes[0], None
            elif len(head_nodes) == 2:
                first_hn_ha_tag = next((tag["Value"] for tag in head_nodes[0].tags if tag.get("Key") == "BCM HA"), None)
                # Without a proper tag we can't be sure which headnode is primary
                if not first_hn_ha_tag:
                    raise CODException(f"Expected tag 'BCM HA' not found for cluster {self.name}, cannot determine "
                                       f"primary and secondary head nodes")

                if first_hn_ha_tag not in ["Primary", "Secondary"]:
                    raise CODException(f"Expected values for 'BCM HA' tag not found for cluster {self.name}, "
                                       f"cannot determine primary and secondary head nodes")

                if first_hn_ha_tag == "Secondary":
                    head_nodes.reverse()
                self.primary_head_node, self.secondary_head_node = head_nodes
            else:
                raise CODException(f"More than two head nodes found for cluster {self.name} (vpc: {self.vpc})")
        except CODException as e:
            log.warning(f"Unable to determine primary/secondary headnodes for cluster {self.name}: {e}")

    def set_active_passive_head_nodes(self) -> None:
        if not self.is_ha:
            self.active_head_node = self.primary_head_node
            return

        if len(self.map_head_node_type_to_address(self.primary_head_node)) == 2:
            self.active_head_node = self.primary_head_node
            self.passive_head_node = self.secondary_head_node
        elif len(self.map_head_node_type_to_address(self.secondary_head_node)) == 2:
            self.active_head_node = self.secondary_head_node
            self.passive_head_node = self.primary_head_node
        else:
            log.warning(f"Unable to determine active headnode for cluster {self.name}, neither of the head "
                        f"nodes has HA ip address assigned.")

    @lru_cache
    def map_head_node_type_to_address(
        self, instance: Instance
    ) -> dict[Cluster.IpType, NetworkInterfacePrivateIpAddressTypeDef]:
        """
        This function extracts private_ip_addresses from an instance object and determines which private_ip_address is
        A, B or HA. private_ip_addresses is a list of: [private_ip_address, private_ip_address]

        :param: instance: boto3.resources.factory.ec2.Instance
        :return: {self.IpType.A: {private_ip_address}, ...}
        """
        assert self.primary_head_node
        instance.reload()
        if not instance.network_interfaces:
            return {}
        network_interface = instance.network_interfaces[0]  # We only use the first interface
        network_interface.reload()
        private_ip_addresses = network_interface.private_ip_addresses
        log.debug(f"Instance {instance.id} has following IP addresses attached: {private_ip_addresses}")

        head_node_type_to_address_map = {}
        for private_ip_address in private_ip_addresses:
            if not private_ip_address["Primary"]:
                # HA address is always 'Primary': False
                head_node_type_to_address_map[self.IpType.HA] = private_ip_address
            elif instance.id == self.primary_head_node.id:
                head_node_type_to_address_map[self.IpType.A] = private_ip_address
            else:
                head_node_type_to_address_map[self.IpType.B] = private_ip_address
        return head_node_type_to_address_map

    class IpType(Enum):
        A = auto()
        B = auto()
        HA = auto()

    def tag_eip(self, ip_type: Cluster.IpType, epialloc_id: str | None) -> None:
        if not epialloc_id:
            return

        tags = {
            "Name": {
                self.IpType.A: f"{self.name}-a public IP",
                self.IpType.B: f"{self.name}-b public IP",
                self.IpType.HA: f"{self.name} HA public IP",
            }[ip_type],
        }
        # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.NetworkInterface.create_tags
        self.ec2.create_tags(
            Resources=[epialloc_id],
            Tags=[{"Key": k, "Value": v} for k, v in tags.items()],
        )

    def allocate_address_in_vpc(self, name: str | None = None) -> AllocateAddressResultTypeDef:
        allocate_address_name = f"{self.name}-{name} public IP"
        return self.ec2c.allocate_address(Domain="vpc",
                                          TagSpecifications=[{
                                              "ResourceType": "elastic-ip",
                                              "Tags": construct_bright_tags(self.name, allocate_address_name)
                                          }]
                                          )

    def create_nat_gateway(self, subnet: Subnet, allocation_id: str | None = None) -> NatGatewayTypeDef:
        kwargs: dict[str, Any] = {"SubnetId": subnet.id}
        nat_gateway_name = f"{self.name} NAT Gateway"
        kwargs["TagSpecifications"] = [{"ResourceType": "natgateway",
                                        "Tags": construct_bright_tags(self.name, nat_gateway_name)}]
        if allocation_id:
            kwargs["AllocationId"] = allocation_id

        response = self.ec2c.create_nat_gateway(**kwargs)

        if 'NatGateway' not in response:
            raise CODException("Broken response, 'NatGateway' not included when creating NAT gateway")
        if 'FailureCode' in response['NatGateway']:
            raise CODException(f"NAT gateway creation failed, {response['NatGateway']['FailureCode']}: "
                               f"{response['NatGateway']['FailureMessage']}")

        log.debug(
            f"Creating NAT gateway {subnet.name} "  # type: ignore[attr-defined]
            "NAT gateway with property: {response['NatGateway']}"
        )
        return response['NatGateway']

    def wait_nat_gateway_state(self, nat_gateway_id: str, state: str) -> None:
        log.info(f"Waiting NAT gateway {nat_gateway_id} to become {state}...")
        waiter: NatGatewayAvailableWaiter | NatGatewayDeletedWaiter
        if state == 'available':
            waiter = self.ec2c.get_waiter('nat_gateway_available')
        elif state == 'deleted':
            waiter = self.ec2c.get_waiter('nat_gateway_deleted')
        else:
            assert ("Not supported NAT gateway status poll")

        waiter.wait(
            Filters=[{
                'Name': 'state',
                'Values': [state]
            }],
            NatGatewayIds=[nat_gateway_id]
        )

    def allocate_and_associate_head_node_eips(self, instance: Instance) -> list[tuple[Cluster.IpType, str, str]]:
        """
        Sometimes the instance does not have a public EIP attached to a private ip address (E.g. creating or starting),
        This function will allocate an EIP, then associate it for every private ip address of the instance.
        If the interface already has public IP, it will be returned, instead of (re)attaching a new one.

        :param: instance: boto3.resources.factory.ec2.Instance
        :return: private_ip_addresses: [(ip_type, allocation_id, allocation_ip)]
        """
        @tenacity.retry(
            wait=tenacity.wait_exponential(multiplier=1, max=self.IP_ASSIGNMENT_RETRY_DELAY),
            stop=tenacity.stop_after_attempt(self.IP_ASSIGNMENT_RETRIES),
            before_sleep=tenacity.before_sleep_log(log, logging.DEBUG),
            after=tenacity.after_log(log, logging.DEBUG),
            reraise=True,
        )
        def associate_address(allocation_id: str, instance_id: str, private_ip: str) -> None:
            # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.associate_address
            self.ec2c.associate_address(
                AllocationId=allocation_id,
                InstanceId=instance_id,
                PrivateIpAddress=private_ip,
            )

        ip_types_and_allocations: list[tuple[Cluster.IpType, str, str]] = []
        private_ip_addresses = self.map_head_node_type_to_address(instance)

        for ip_type, private_ip_address in private_ip_addresses.items():
            association = private_ip_address.get("Association")
            if association:  # A public EIP is bound to the private_ip_address
                allocation_id = association["AllocationId"]
                allocation_ip = association["PublicIp"]
                ip_types_and_allocations.append((ip_type, allocation_id, allocation_ip))
                log.debug(f"Public IP {allocation_ip} is already used as address '{ip_type.name}', "
                          f"skipping allocation and association")
                continue

            allocation = self.allocate_address_in_vpc(name="headnode")
            allocation_id = allocation["AllocationId"]
            allocation_ip = allocation["PublicIp"]
            private_ip = private_ip_address["PrivateIpAddress"]
            log.debug(f"Allocated public IP {allocation_ip} with allocation_id: {allocation_id}.")

            try:
                associate_address(allocation_id, instance.id, private_ip)
                self.tag_eip(ip_type, allocation_id)
                ip_types_and_allocations.append((ip_type, allocation_id, allocation_ip))
                instance.reload()  # Need to reload after EIP assignment, or instance.public_ip_address will be empty
                log.debug(f"Associated public IP {allocation_ip} with instance {instance.id} as address "
                          f"'{ip_type.name}'.")
            except Exception as associate_error:
                self.ec2c.release_address(AllocationId=allocation_id)
                log.error(f"Error associating IP {allocation_ip} as {ip_type.name} address to {instance.id}.")
                raise CODException("Error associating IP", caused_by=associate_error)

        return ip_types_and_allocations

    def attach_eips_to_head_nodes(self) -> None:
        assert self.primary_head_node is not None
        if any(tag["Key"] == BCM_TAG_NO_PUBLIC_IP for tag in self.primary_head_node.tags):
            log.info(f"Head node has {BCM_TAG_NO_PUBLIC_IP!r} tag, so no public IPs will not be allocated")
            return

        if not self.is_ha:
            ip_types_and_allocations = self.allocate_and_associate_head_node_eips(self.primary_head_node)
            log.info(f"Cluster {self.name} IP: {ip_types_and_allocations[0][2]}")
        else:
            assert self.secondary_head_node is not None
            ip_types_and_allocations = self.allocate_and_associate_head_node_eips(self.primary_head_node) + \
                self.allocate_and_associate_head_node_eips(self.secondary_head_node)

            log.info(f"Cluster {self.name} IPs: "
                     f"{', '.join([i[2] + ' ' + f'({i[0].name})' for i in ip_types_and_allocations])}")

    def disassociate_and_release_head_node_eips(self, instance: Instance) -> None:
        """
        If public EIP is attached to the private IP address of the instance, disassociate and then release it. Used when
        stopping or terminating the instance
        :param: instance: boto3.resources.factory.ec2.Instance
        :return:
        """
        instance_private_addresses = self.map_head_node_type_to_address(instance)
        for private_ip_address in instance_private_addresses.values():
            private_ip_assoc = private_ip_address.get("Association")
            if not private_ip_assoc:  # A public EIP is not bound to the private_ip_address
                log.debug(f"Private IP address {private_ip_address['PrivateIpAddress']} on {instance.id} has "
                          f"no Elastic IP associated, nothing to release")
                continue
            assoc_id = private_ip_assoc.get('AssociationId')
            allocation_id = private_ip_assoc.get('AllocationId')
            public_ip = private_ip_assoc.get('PublicIp')

            if assoc_id:
                # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.disassociate_address
                log.debug(f"Disassociating AssociationId: {assoc_id} (EIP: {public_ip})")
                self.ec2c.disassociate_address(AssociationId=assoc_id)

            if allocation_id:
                vpc_addr = self.ec2.VpcAddress(allocation_id)
                eip_bcm_name_re = fr"^{re.escape(self.name)}(-a|-b| HA)? public IP$"
                if (
                    self.is_created_by_us(vpc_addr.tags) or
                    re.match(eip_bcm_name_re, self.get_resource_name(vpc_addr, default=""))
                ):
                    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.release_address
                    log.debug(f"Releasing IP allocation {allocation_id} for public IP: {public_ip})")
                    self.ec2c.release_address(AllocationId=allocation_id)

                    log.debug(f"Elastic IP {public_ip} was detached from instance {instance.id}")
                else:
                    log.debug(f"IP allocation {allocation_id} for public IP {public_ip}) "
                              "wasn't created by us and won't be released")

    def remove_orphaned_interfaces(self) -> None:
        assert self.vpc is not None
        # Interfaces left behind after the parent head node was terminated (bad case, should not happen intentionally)
        filter: list[FilterTypeDef] = [
            {"Name": "vpc-id", "Values": [self.vpc.id]},
            {"Name": f"tag:{BCM_CLUSTER_NAME_TAGS[0]}", "Values": [self.name]}
        ]
        interfaces = self.ec2c.describe_network_interfaces(
            Filters=filter
        )["NetworkInterfaces"]
        orphaned_interfaces = [eni for eni in interfaces if not eni.get('Attachment')]
        for eni in orphaned_interfaces:
            log.info(
                f"Deleting orphaned network interface with ID: {eni['NetworkInterfaceId']}, "
                f"and description: {eni['Description']}"
            )
            self.ec2c.delete_network_interface(NetworkInterfaceId=eni["NetworkInterfaceId"])

    def detach_eips_from_head_nodes(self) -> None:
        if self.primary_head_node is not None:
            self.disassociate_and_release_head_node_eips(self.primary_head_node)
        if self.is_ha and self.secondary_head_node is not None:
            self.disassociate_and_release_head_node_eips(self.secondary_head_node)

    @tenacity.retry(
        wait=tenacity.wait_random_exponential(multiplier=5, max=60),
        stop=tenacity.stop_after_attempt(5),
        reraise=True,
    )
    def get_efs_id(self) -> str | None:
        # The creation token is originally generated by cm-cloud-ha (see cluster-tools repo)
        # To be backward compatible, we check using both the old format and the new format
        old_efs_creation_token = f"bcm-ha-efs-{self.name}"
        efs_creation_token = hashlib.sha256(f"bcm-ha-efs-{self.name}".encode()).hexdigest()

        response = efs.describe_fs(self.efs_client, token=efs_creation_token)
        if response:
            return str(response["FileSystemId"])

        if len(old_efs_creation_token) <= 64:
            response = efs.describe_fs(self.efs_client, token=old_efs_creation_token)
            return str(response["FileSystemId"]) if response else None

        return None

    def try_delete_efs(self) -> None:
        if not self.efs_id:
            return

        log.info(f"Deleting EFS {self.efs_id}...")
        response = efs.describe_mount_target(self.efs_client, fs_id=self.efs_id)
        if response:
            efs.delete_mount_target(self.efs_client, str(response["MountTargetId"]))
        efs.delete_fs(self.efs_client, self.efs_id)

    def terminate_instances_for_vpc(self) -> None:
        assert self.vpc is not None
        vpc_name = self.get_resource_name_or_id(self.vpc)
        log.info(f"Finding instances for cluster {self.name!r}...")
        instances: list[Instance] = []
        for instance in self.vpc.instances.all():
            if not self.is_created_by_us(instance.tags):
                log.debug(f"Instance {self.get_resource_name_or_id(instance)} "
                          "wasn't created by us and won't be deleted")
                continue

            instances.append(instance)

        if not instances:
            log.info(f"No instances to be deleted found in VPC {vpc_name!r}")
            return

        def _terminate_instance_with_interface_cleanup(instance: Instance) -> None:
            # set DeleteOnTermination": True, so that termination also removes the interface
            eni = instance.network_interfaces[0]  # always 0
            self.ec2c.modify_network_interface_attribute(
                NetworkInterfaceId=eni.id,
                Attachment={
                    "AttachmentId": eni.attachment["AttachmentId"],
                    "DeleteOnTermination": True,
                },
            )

            instance.terminate()
            log.debug(f"Terminated instance {self.get_resource_name_or_id(instance)}")

        log.info(f"Issuing termination requests for {len(instances)} instances for cluster {self.name!r}...")
        utils.multithread_run(_terminate_instance_with_interface_cleanup, instances, config["max_threads"])

        def ceildiv(n: int, d: int) -> int:
            # NB: ceil(x) = -floor(-x)
            return -(n // -d)

        terminate_timeout: int = config["terminate_timeout"]
        log.info(f"Waiting until instances of cluster {self.name!r} are terminated "
                 f"(timeout: {terminate_timeout} seconds)...")
        terminate_delay = min(15, terminate_timeout)
        # Round up the timeout to the next multiple of "Delay".
        # 1+ since the first attempt happens immediately.
        waiter_max_attempts = 1 + ceildiv(terminate_timeout, terminate_delay) if terminate_delay > 0 else 0
        self.ec2c.get_waiter("instance_terminated").wait(
            InstanceIds=[instance.id for instance in instances],
            WaiterConfig={"Delay": terminate_delay, "MaxAttempts": waiter_max_attempts},
        )

    def destroy_resources_in_vpc(self) -> None:
        assert self.vpc is not None
        vpc_name = self.get_resource_name_or_id(self.vpc)
        cluster_in_vpc_msg = f"cluster {self.name!r} in VPC {vpc_name!r}"
        log.info(f"Destroying resources of {cluster_in_vpc_msg}")

        #
        # Delete subnets.
        #
        subnets_to_delete = []
        for subnet in self.vpc.subnets.all():
            if not self.is_created_by_us(subnet.tags):
                log.debug(
                    f"Subnet {self.get_resource_name_or_id(subnet)} "
                    "wasn't created by us and won't be deleted"
                )
                continue
            subnets_to_delete.append(subnet)

        if subnets_to_delete:
            log.info(f"Deleting subnets of {cluster_in_vpc_msg}")
            for subnet in subnets_to_delete:
                subnet.delete()

        #
        # Delete route tables.
        #
        route_tables_to_delete = []
        for route_table in self.vpc.route_tables.all():
            if self._is_main_routing_table(route_table):
                continue
            if not self.is_created_by_us(route_table.tags):
                log.debug(f"Route table {self.get_resource_name_or_id(route_table)} "
                          "wasn't created by us and won't be deleted")
                continue
            route_tables_to_delete.append(route_table)

        if route_tables_to_delete:
            log.info(f"Deleting route tables of {cluster_in_vpc_msg}")
            for route_table in route_tables_to_delete:
                route_table.delete()

        #
        # Delete internet gateways.
        #
        gateways_to_delete = []
        for gateway in self.vpc.internet_gateways.all():
            if not self.is_created_by_us(gateway.tags):
                log.debug(f"Internet gateway {self.get_resource_name_or_id(gateway)} "
                          "wasn't created by us and won't be deleted")
                continue
            gateways_to_delete.append(gateway)

        if gateways_to_delete:
            log.info(f"Detaching and deleting gateways of {cluster_in_vpc_msg}")
            for gateway in gateways_to_delete:
                if self.is_created_by_us(self.vpc.tags):
                    # We need to clean up routes in pre-existing VPC. "our" VPCs are removed anyway so we don't care
                    self._remove_routes_to_gateway(gateway.id)
                self.vpc.detach_internet_gateway(InternetGatewayId=gateway.id)
                gateway.delete()

        #
        # Delete security groups.
        #
        sgs_to_delete = []
        for sg in self.vpc.security_groups.all():
            if sg.group_name == "default":
                continue

            # Previously security groups didn't have tags, but they had pretty-specific names.
            # So, if there're no BCM tags, let's fall back to checking by name.
            sg_bcm_names = {f"Bright {self.name}-headnode", f"Bright {self.name}-node"}
            if not self.is_created_by_us(sg.tags) and sg.group_name not in sg_bcm_names:
                log.debug(f"Security group {self.get_resource_name_or_id(sg)} "
                          "wasn't created by us and won't be deleted")
                continue

            sgs_to_delete.append(sg)

        if sgs_to_delete:
            # Flush all permissions, because if they refer to security group,
            # that security group won't be deleted
            log.info(f"Flushing permissions of security groups of {cluster_in_vpc_msg}")
            for sg in sgs_to_delete:
                if sg.ip_permissions:
                    sg.revoke_ingress(IpPermissions=sg.ip_permissions)
                if sg.ip_permissions_egress:
                    sg.revoke_egress(IpPermissions=sg.ip_permissions_egress)

            # Delete security groups themselves
            log.info(f"Deleting security groups of {cluster_in_vpc_msg}")
            for sg in sgs_to_delete:
                sg.delete()

        #
        # Delete network ACLs.
        #
        network_acls_to_delete = []
        for network_acl in self.vpc.network_acls.all():
            # AWS always creates an undeleteable default ACL per VPC.
            if network_acl.is_default:
                continue
            if not self.is_created_by_us(network_acl.tags):
                log.debug(f"Network ACL {self.get_resource_name_or_id(network_acl)} "
                          "wasn't created by us and won't be deleted")
                continue
            network_acls_to_delete.append(network_acl)

        if network_acls_to_delete:
            log.info(f"Deleting Network ACLs of {cluster_in_vpc_msg}")
            for network_acl in network_acls_to_delete:
                network_acl.delete()

        #
        # Delete VPC.
        #
        if self.is_created_by_us(self.vpc.tags):
            log.info(f"Deleting VPC {self.name!r}...")
            self.vpc.delete()
        else:
            log.debug(
                f"VPC {self.get_resource_name_or_id(self.vpc)} "
                "wasn't created by us and won't be deleted"
            )

        log.info(f"Done destroying cluster {self.name!r} resources in VPC {vpc_name!r}")

    def destroy_nat_gateways(self) -> None:
        assert self.vpc is not None
        response = self.ec2c.describe_nat_gateways(
            Filters=[
                {
                    'Name': 'vpc-id',
                    'Values': [self.vpc.id]
                }
            ]
        )
        nat_gateways = response['NatGateways']
        for nat_gateway in nat_gateways:
            if nat_gateway['State'] in ['deleting', 'deleted']:
                continue

            nat_gateway_id = nat_gateway['NatGatewayId']
            nat_gateway_tags = nat_gateway['Tags']
            if (
                not self.is_created_by_us(nat_gateway_tags) and
                # Handle legacy NAT gateways without BCM tag by checking BCM-specific name:
                self.get_tag_value(nat_gateway_tags, "Name", default="") != f"{self.name} NAT Gateway"
            ):
                log.debug(f"NAT Gateway {nat_gateway_id} wasn't created by us and won't be deleted")
                continue

            self.ec2c.delete_nat_gateway(NatGatewayId=nat_gateway_id)
            self.wait_nat_gateway_state(nat_gateway_id, 'deleted')
            # Extract the Elastic IP allocation ID from the response and release
            for nat_gateway_addr in nat_gateway['NatGatewayAddresses']:
                allocation_id = nat_gateway_addr['AllocationId']
                self.ec2c.release_address(AllocationId=allocation_id)

    def destroy_placement_groups(self) -> None:
        """
        Destroy placement groups created by this cluster.
        """
        assert self.vpc is not None
        log.info(f"Destroying placement groups for cluster {self.name!r} in VPC {self.vpc.vpc_id}...")
        tag_filter_string = 'tag:' + 'BCM Cluster'
        response = self.ec2c.describe_placement_groups(
            Filters=[
                {
                    'Name': tag_filter_string,
                    'Values': [self.name]
                }
            ]
        )
        if not response or 'PlacementGroups' not in response:
            log.info(f"No placement groups found for cluster {self.name!r} in VPC {self.vpc.vpc_id}")
            return
        placement_groups = response['PlacementGroups']
        for pg in placement_groups:
            if pg['State'] in ['deleting', 'deleted']:
                continue
            log.info(f"Deleting placement group {pg['GroupName']}")
            self.ec2c.delete_placement_group(GroupName=pg['GroupName'])

    def create_placement_group(self, placement_group_name: str) -> None:
        """Create a placement group for the cluster."""
        ec2 = self.ec2

        log.info(f"Creating placement group {placement_group_name} for the cluster {self.name}")
        strategy: Literal['cluster', 'partition', 'spread'] = "spread"
        spread_level: Literal['host', 'rack'] = "rack"
        try:
            ec2.create_placement_group(
                GroupName=placement_group_name,
                Strategy=strategy,
                TagSpecifications=[{
                    "ResourceType": "placement-group",
                    "Tags": construct_bright_tags(self.name, placement_group_name)
                }],
                SpreadLevel=spread_level
            )
            log.info(f"Placement group created. Group strategy: {strategy}, spread level: {spread_level}")
        except Exception as e:
            raise CODException(f"Failed to create placement group: {e}")

    def destroy(self) -> None:
        self.try_delete_efs()
        if self.vpc:
            self.detach_eips_from_head_nodes()
            self.remove_orphaned_interfaces()
            self.terminate_instances_for_vpc()
            self.destroy_nat_gateways()
            self.destroy_placement_groups()
            self.destroy_resources_in_vpc()

        self.vpc = None
        self.primary_head_node = None

    def stop(self, release_eip: bool) -> None:
        """
        We will try to stop the instance only if it's in "running" or "pending" state.
        Instance states: https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_InstanceState.html
        """
        assert self.vpc is not None
        vpc_running_instances = [
            instance for instance in self.vpc.instances.all() if instance.state["Name"] in ["pending", "running"]
        ]
        cluster_running_instances = [
            instance for instance in vpc_running_instances if
            any(self.get_tag_value(instance.tags, tag, "") == self.name for tag in BCM_CLUSTER_NAME_TAGS)
        ]

        if not cluster_running_instances:
            log.info(f"No running instances found for cluster {self.name}")
            return

        if release_eip:
            self.detach_eips_from_head_nodes()

        log.info(f"Issuing stop requests for cluster {self.name}...")
        for instance in cluster_running_instances:
            log.debug(f"Stopping instance {self.get_tag_value(instance.tags, 'Name')}")
            instance.stop()

        log.info(f"Waiting for instances of {self.name} until stopped...")
        for instance in cluster_running_instances:
            instance.wait_until_stopped()

    def start(self) -> None:
        """
        We will try to start the instance only if it's not in "running" or "pending" state.
        Instance states: https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_InstanceState.html
        """
        def start_head_node(instance: Instance | None, head_node_type: str, cluster_name: str) -> None:
            assert instance is not None
            if instance.state["Name"] in ["pending", "running"]:
                log.info(f"{head_node_type} of cluster {cluster_name} is already running, not attempting to start")
                return

            log.info(f"Starting {head_node_type} node of {cluster_name}...")
            instance.start()
            log.info(f"Waiting until {head_node_type} of {cluster_name} is running...")
            instance.wait_until_running()

        start_head_node(self.primary_head_node, "primary head node", self.name)
        if self.is_ha:
            start_head_node(self.secondary_head_node, "secondary head node", self.name)

        self.attach_eips_to_head_nodes()

    @classmethod
    def _is_main_routing_table(cls, route_table: RouteTable) -> bool:
        for association in route_table.associations_attribute:
            if association.get("Main"):
                return True
        return False

    def _remove_routes_to_gateway(self, gateway_id: str) -> None:
        """
        Before removing an internet gateway, we should remove routes that point to it, to prevent blackhole routes.
        Important when working with pre-existing VPCs where we only delete gateways we created,
        but routes might still reference them.
        """
        log.debug(f"Checking for routes pointing to gateway {gateway_id}")

        assert self.vpc, "Cluster VPC not found, cannot remove routes"

        for route_table in self.vpc.route_tables.all():
            for route in route_table.routes_attribute:
                if route and route["GatewayId"] != gateway_id:
                    continue

                log.debug(
                    f"Deleting route {route["DestinationCidrBlock"]} -> {gateway_id} "
                    f"from route table {route_table.id}"
                )

                self.ec2c.delete_route(
                    RouteTableId=route_table.id,
                    DestinationCidrBlock=route["DestinationCidrBlock"]
                )
