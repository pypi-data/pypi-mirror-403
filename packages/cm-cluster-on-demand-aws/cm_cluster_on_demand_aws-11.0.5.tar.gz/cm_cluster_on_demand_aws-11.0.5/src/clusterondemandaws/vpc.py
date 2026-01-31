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
import re
import shlex
import time
import typing

import tenacity
import yaml
from botocore.exceptions import ClientError
from passlib.hash import sha512_crypt

from clusterondemand.bcm_version import BcmVersion
from clusterondemand.cloudconfig.headcommands import get_ssh_auth_key_commands
from clusterondemand.clustercreate import enable_cmd_debug_commands
from clusterondemand.exceptions import CODException
from clusterondemand.inbound_traffic_rule import (
    EPHEMERAL_PORTS_ACL_RULE_NUM,
    RESERVED_NETWORK_ACL_RULE_NUM,
    InboundTrafficRule,
    RuleType
)
from clusterondemandaws.cluster import BCM_TYPE_HEAD_NODE, construct_bright_tags
from clusterondemandconfig import config

from .brightsetup import generate_bright_setup

if typing.TYPE_CHECKING:
    from typing import Any

    from mypy_boto3_ec2.client import EC2Client
    from mypy_boto3_ec2.service_resource import (
        EC2ServiceResource,
        Instance,
        InternetGateway,
        NetworkAcl,
        RouteTable,
        Subnet,
        Vpc
    )
    from mypy_boto3_ec2.type_defs import NatGatewayTypeDef, PortRangeTypeDef, TagTypeDef

    from .cluster import Cluster

log = logging.getLogger("cluster-on-demand")


def get_vpc_name_for_cluster(cluster_name: str) -> str:
    return config["fixed_cluster_prefix"] + cluster_name  # type: ignore[no-any-return]


def create_in_existing_vpc(cluster: Cluster) -> None:
    """Create a cluster in a pre-existing (user-managed) VPC """

    ec2 = cluster.ec2
    vpc = ec2.Vpc(config["existing_vpc_id"])
    vpc.load()

    cluster.vpc = vpc

    # when using pre-existing VPC,   cluster_name != actual vpc name
    vpc.cluster_name = cluster.name  # type: ignore[attr-defined]

    if config["configure_igw_in_existing_vpc"]:
        assert config["i_know_configuring_igw_is_risky"]
        internet_gateway = _create_internet_gateway(cluster.vpc, ec2)
        _set_default_gateway_vpc(cluster.vpc, internet_gateway)
    else:
        log.info("Not configuring the Internet gateway in the VPC "
                 "(use --configure-igw-in-existing-vpc to change this).")

    # determine public subnet
    head_node_subnet_id = config["existing_subnet_id"][0]
    head_node_subnet = next(
        (subnet for subnet in vpc.subnets.all() if subnet.id == head_node_subnet_id),
        None)
    assert head_node_subnet, f"Head node subnet {head_node_subnet_id} not found in VPC {vpc.id}"

    log.info(f"Setting up VPC in {config['aws_region']}, zone: {head_node_subnet.availability_zone}")

    if config["head_node_sg_id"] and config["node_sg_id"]:
        head_node_sg_id = config["head_node_sg_id"]
        node_sg_id = config["node_sg_id"]
    else:
        head_node_sg_id, node_sg_id = _create_security_groups(cluster.vpc, config["ingress_icmp"])

    placement_group_name = config["head_node_pg_name"] or f"{cluster.name}-head-node-pg"
    if not config["head_node_pg_name"]:
        _create_placement_group(cluster, placement_group_name)

    head_node_hostname = cluster.name
    cluster.primary_head_node = _create_head_node(
        ec2, cluster.vpc, head_node_hostname, head_node_subnet, cluster.head_node_image, head_node_sg_id, node_sg_id,
        placement_group_name)

    _retry_not_found(_disable_source_dest_check, cluster.primary_head_node)

    log.info("Waiting for head node to be running")
    cluster.primary_head_node.wait_until_running()  # must be running for being usable as gateway

    log.info(f"Done setting up VPC for {cluster.name} in {config['aws_region']}, "
             f"zone: {head_node_subnet.availability_zone}")


def create_vpc(cluster: Cluster) -> None:
    """Create an AWS VPC with the given name.

    This VPC contains a single head node, two subnets, an internal gateway and one routing table.
    """
    ec2 = cluster.ec2

    head_node_hostname = cluster.name
    vpc_name = get_vpc_name_for_cluster(cluster.name)

    if _vpc_with_name_exists(vpc_name, ec2):
        raise CODException("VPC for this cluster already exists")

    log.info("Setting up VPC")

    cluster.vpc = _create_vpc(cluster.name, vpc_name, ec2)
    # TODO: We shouldn't be setting these attributes here, submitted BCM-32940 to fix this
    cluster.vpc.name = vpc_name  # type: ignore[attr-defined]
    cluster.vpc.cluster_name = cluster.name  # type: ignore[attr-defined]

    if config["configure_igw"]:
        internet_gateway = _create_internet_gateway(cluster.vpc, ec2)
        _set_default_gateway_vpc(cluster.vpc, internet_gateway)
    else:
        log.debug("Not configuring the internet gateway in the VPC (set --configure-igw to change this)")

    public_subnet = _create_public_subnet(cluster.vpc, ec2)
    private_subnet = _create_private_subnet(cluster.vpc, ec2)

    if config["inbound_network_acl_rule"]:
        _create_network_acls(cluster.vpc, public_subnet, private_subnet, cluster.ec2c)

    if config["head_node_sg_id"] and config["node_sg_id"]:
        head_node_sg_id = config["head_node_sg_id"]
        node_sg_id = config["node_sg_id"]
    else:
        head_node_sg_id, node_sg_id = _create_security_groups(cluster.vpc, config["ingress_icmp"])

    placement_group_name = config["head_node_pg_name"] or f"{cluster.name}-head-node-pg"
    if not config["head_node_pg_name"]:
        _create_placement_group(cluster, placement_group_name)

    cluster.primary_head_node = _create_head_node(
        ec2, cluster.vpc, head_node_hostname, public_subnet, cluster.head_node_image, head_node_sg_id, node_sg_id,
        placement_group_name)

    _retry_not_found(_disable_source_dest_check, cluster.primary_head_node)

    log.info("Waiting for head node to be running")
    cluster.primary_head_node.wait_until_running()  # must be running for being usable as gateway

    if cluster.is_ha or config["configure_nat_gateway"]:
        allocation_id = cluster.allocate_address_in_vpc(name="NAT Gateway")["AllocationId"]
        nat_gateway = cluster.create_nat_gateway(public_subnet, allocation_id=allocation_id)
        cluster.wait_nat_gateway_state(nat_gateway['NatGatewayId'], 'available')
        _set_default_gateway_subnet(cluster.vpc, private_subnet, nat_gateway=nat_gateway)
    else:
        _set_default_gateway_subnet(cluster.vpc, private_subnet, head_node_instance=cluster.primary_head_node)

    log.info(f"Done setting up VPC for {vpc_name} in {config['aws_region']}, "
             f"zone: {public_subnet.availability_zone}")


def _retry_not_found(func: typing.Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    retry_wrapper = tenacity.Retrying(
        retry=tenacity.retry_if_exception_message(match=".*NotFound.*"),
        wait=tenacity.wait_exponential(multiplier=1, max=60),
        stop=tenacity.stop_after_delay(300),
        before_sleep=tenacity.before_sleep_log(log, logging.DEBUG),
        after=tenacity.after_log(log, logging.DEBUG),
        reraise=True,
    )
    return retry_wrapper(func, *args, **kwargs)


def _create_vpc(cluster_name: str, vpc_name: str, ec2: EC2ServiceResource) -> Vpc:
    log.info(f"Creating VPC for {vpc_name} in {config['aws_region']}...")

    # https://aws.amazon.com/about-aws/whats-new/2020/07/amazon-vpc-resources-support-tag-on-create/
    tags = construct_bright_tags(cluster_name, vpc_name)
    kwargs: dict[str, Any] = {"CidrBlock": str(config["vpc_cidr"]),
                              "TagSpecifications": [{"ResourceType": "vpc", "Tags": tags}]}

    vpc = ec2.create_vpc(**kwargs)
    # Make sure the VPC has finished creation before using it.
    vpc.wait_until_exists()
    _retry_not_found(vpc.wait_until_available)
    log.debug("VPC was successfully created, id: %s", vpc.id)

    return vpc


def _create_internet_gateway(vpc: Vpc, ec2: EC2ServiceResource) -> InternetGateway:
    log.info("Adding internet connectivity...")

    internet_gateway_name = vpc.cluster_name  # type: ignore[attr-defined]
    tags = construct_bright_tags(vpc.cluster_name, internet_gateway_name)  # type: ignore[attr-defined]
    kwargs: dict[str, Any] = {"TagSpecifications": [{"ResourceType": "internet-gateway", "Tags": tags}]}

    internet_gateway = ec2.create_internet_gateway(**kwargs)
    time.sleep(0.5)

    internet_gateway.name = internet_gateway_name  # type: ignore[attr-defined]

    vpc.attach_internet_gateway(InternetGatewayId=internet_gateway.id)
    return internet_gateway


def _create_public_subnet(vpc: Vpc, ec2: EC2ServiceResource) -> Subnet:
    log.info("Creating public subnet...")
    kwargs: dict[str, Any] = {"CidrBlock": str(config["public_subnet_cidr"])}

    if config["aws_availability_zone"]:
        kwargs["AvailabilityZone"] = config["aws_availability_zone"]

    public_subnet_name = vpc.cluster_name + " public"  # type: ignore[attr-defined]
    tags = construct_bright_tags(vpc.cluster_name, public_subnet_name, BCM_TYPE_HEAD_NODE)  # type: ignore[attr-defined]
    kwargs["TagSpecifications"] = [{"ResourceType": "subnet", "Tags": tags}]

    public_subnet = vpc.create_subnet(**kwargs)
    time.sleep(0.5)
    public_subnet.name = public_subnet_name  # type: ignore[attr-defined]

    return public_subnet


def _create_private_subnet(vpc: Vpc, ec2: EC2ServiceResource) -> Subnet:
    log.info("Creating private subnet...")

    kwargs: dict[str, Any] = {"CidrBlock": str(config["private_subnet_cidr"])}

    if config["aws_availability_zone"]:
        kwargs["AvailabilityZone"] = config["aws_availability_zone"]

    private_subnet_name = vpc.cluster_name + " private"  # type: ignore[attr-defined]
    tags = construct_bright_tags(
        vpc.cluster_name, private_subnet_name, BCM_TYPE_HEAD_NODE  # type: ignore[attr-defined]
    )
    kwargs["TagSpecifications"] = [{"ResourceType": "subnet", "Tags": tags}]

    private_subnet = vpc.create_subnet(**kwargs)
    time.sleep(0.5)
    private_subnet.name = private_subnet_name  # type: ignore[attr-defined]

    return private_subnet


def _set_default_gateway_vpc(vpc: Vpc, internet_gateway: InternetGateway) -> None:
    main_route_table = _find_main_route_table(vpc)
    main_route_table.create_route(DestinationCidrBlock="0.0.0.0/0", GatewayId=internet_gateway.id)


# When the default gateway of the subnet is an ec2 instance the ec2 instance must be in
# the running state. Even though we make sure to check that an instance is running before
# we set the gateway, we can still encounter incorrect instance state errors.
@tenacity.retry(
    retry=tenacity.retry_if_exception_message(match=".*IncorrectInstanceState.*"),
    wait=tenacity.wait_exponential(multiplier=1, max=60),
    stop=tenacity.stop_after_delay(300),
    before_sleep=tenacity.before_sleep_log(log, logging.DEBUG),
    after=tenacity.after_log(log, logging.DEBUG),
    reraise=True
)
def _set_default_gateway_subnet(
    vpc: Vpc,
    subnet: Subnet,
    head_node_instance: Instance | None = None,
    nat_gateway: NatGatewayTypeDef | None = None
) -> None:
    assert bool(head_node_instance) != bool(nat_gateway), \
        "The default gateway for the cluster must be either a head node instance or a NAT gateway." \
        " Not both and not neither."

    route_table_name = subnet.name + " route table"  # type: ignore[attr-defined]
    tags = construct_bright_tags(vpc.cluster_name, route_table_name)  # type: ignore[attr-defined]
    rt_kwargs: dict[str, Any] = {"TagSpecifications": [{"ResourceType": "route-table", "Tags": tags}]}

    route_table = vpc.create_route_table(**rt_kwargs)

    route_table.name = route_table_name  # type: ignore[attr-defined]

    route_table.associate_with_subnet(SubnetId=subnet.id)

    kwargs: dict[str, Any] = {"DestinationCidrBlock": "0.0.0.0/0"}
    if head_node_instance:
        kwargs["InstanceId"] = head_node_instance.id
    else:
        kwargs["NatGatewayId"] = nat_gateway['NatGatewayId']  # type: ignore[index]
    route_table.create_route(**kwargs)


def _create_head_node(
    ec2_client: EC2ServiceResource,
    vpc: Vpc,
    hostname: str,
    public_subnet: Subnet,
    head_node_image: Any,
    head_node_sg_id: str,
    node_sg_id: str,
    placement_group_name: str,
) -> Instance:
    assert placement_group_name, "Placement group name must be specified"
    log.info(f"Creating head node ({config["head_node_type"]})...")
    bdm = None
    if config["head_node_root_volume_size"]:
        bdm = [
            {
                "DeviceName": "/dev/sda1",
                "Ebs": {
                    "VolumeSize": config["head_node_root_volume_size"],
                    "VolumeType": config["head_node_root_volume_type"],
                    "DeleteOnTermination": True
                }
            }
        ]
        if config["head_node_root_volume_type"] in ["io1", "io2"]:
            bdm[0]["Ebs"]["Iops"] = config["head_node_root_volume_iops"]  # type: ignore[index]

    bright_setup = generate_bright_setup(
        hostname=hostname,
        head_node_image=head_node_image,
        head_node_sg_id=head_node_sg_id,
        node_sg_id=node_sg_id,
        existing_subnet_ids=config["existing_subnet_id"] if config["existing_subnet_id"] else None)

    cloud_init_script = """#!/bin/sh
        mkdir -p /root/cm
        echo '%s' > /root/cm/cm-bright-setup.conf
    """ % yaml.dump(bright_setup, default_flow_style=False).replace("'", '"')

    from .clustercreate import DEFAULT_DISK_SETUP, DEFAULT_DISK_SETUP_10_AND_ABOVE  # avoid circular import

    if config["node_disk_setup"] is not DEFAULT_DISK_SETUP:  # user-supplied disk setup
        disk_setup = config["node_disk_setup"]
    elif head_node_image.version and BcmVersion(head_node_image.version) >= BcmVersion("10.0"):
        disk_setup = DEFAULT_DISK_SETUP_10_AND_ABOVE
    else:
        disk_setup = DEFAULT_DISK_SETUP

    cloud_init_script += """
        echo "%s" > /root/cm/node-disk-setup.xml
    """ % disk_setup

    # FIXME: Remove this. The changes have been incorporated into cm-bright-setup as of May 2024.
    # The code below the code that is getting patched here still support only 1 or 2 subnets. And that's fine.
    # At this point we simply want to enable creating a cluster in a env with more than 2 subnets (while allowing the
    # user to specify only 1 or 2 of those).
    if config["existing_subnet_id"]:
        # if  "config["existing_subnet_id"]" is not set, we must not patch.
        cloud_init_script += \
            "sed -i 's/subnets = list(self.head_node_instance.vpc.subnets.all())/" \
            "subnets = [subnet for subnet in list(self.head_node_instance.vpc.subnets.all()) " \
            "if subnet.id in self.config[\"amazon\"][\"existing_subnet_ids\"]]/g' " \
            "/cm/local/apps/cm-setup/lib/python3.12/site-packages/cmsetup/plugins/brightsetup/stages.py\n"
        # This code also has a check
        # if len(subnets) > 2:
        #    raise Exception('VPCs with more than one subnets are not supported')
        # we don't need to remove it, as with the patch above, the num of subnets there will be limited to
        # the subnets specified with --existing-subnet-id,  which on the clientside will ensure this is 1 or 2,

    kwargs = {
        "ImageId": head_node_image.uuid,
        "MinCount": 1,
        "MaxCount": 1,
        "InstanceType": config["head_node_type"],
        "BlockDeviceMappings": bdm,
    }
    if config["head_node_internal_ip"]:
        kwargs["PrivateIpAddress"] = config["head_node_internal_ip"]

    if config["ssh_key_pair"]:
        log.info("Key pair specified")
        kwargs["KeyName"] = config["ssh_key_pair"]

    auth_key_commands = get_ssh_auth_key_commands()
    if auth_key_commands:
        log.info("Public key specified")
        cloud_init_script += "mkdir -p /root/.ssh/\n"
        cloud_init_script += "\n".join(auth_key_commands)
        cloud_init_script += "\n"

    encrypted_root_password = sha512_crypt.hash(config["cluster_password"])
    cloud_init_script += """
        echo %s | chpasswd -e
        """ % shlex.quote("root:" + encrypted_root_password)

    if config["ssh_password_authentication"]:
        cloud_init_script += """
        sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/g' /etc/ssh/sshd_config
        if ! systemctl try-reload-or-restart sshd; then
          echo 'Old systemd, using different reload command.'
          systemctl reload-or-try-restart sshd
        fi
        """
        log.info("Enabling ssh password authentication")

    if config["cmd_debug"]:
        subsystems = config["cmd_debug_subsystems"]
        log.debug(f"Setting debug mode on CMDaemon for subsystems: '{subsystems}'")
        for command in enable_cmd_debug_commands(subsystems):
            cloud_init_script += command + "\n"

    if config["run_cm_bright_setup"]:
        if config["prebs"]:
            cloud_init_script += "\n".join(["echo 'Starting custom prebs commands'", *config["prebs"], ""])

        if BcmVersion(config["version"]) < "8.2":
            cloud_init_script += "/cm/local/apps/cluster-tools/bin/cm-bright-setup " \
                                 "-c /root/cm/cm-bright-setup.conf --on-error-action abort\n"
        else:
            cloud_init_script += "/cm/local/apps/cm-setup/bin/cm-bright-setup " \
                                 "-c /root/cm/cm-bright-setup.conf --on-error-action abort\n"

        if config["postbs"]:
            cloud_init_script += "\n".join(["echo 'Starting custom postbs commands'", *config["postbs"], ""])
    else:
        log.info("Not Running cm-bright-setup")

    kwargs["Placement"] = {"GroupName": placement_group_name}

    kwargs["UserData"] = cloud_init_script

    log.info("Creating the head node VM instance")

    head_node_instance_and_ebs_name = (
        f"{vpc.cluster_name} (Bright COD-AWS {config['version']} head node)"  # type: ignore[attr-defined]
    )

    headnode_tags = construct_bright_tags(
        vpc.cluster_name, head_node_instance_and_ebs_name, BCM_TYPE_HEAD_NODE  # type: ignore[attr-defined]
    )
    # Append any head node tags which the user specified
    headnode_tags += [{"Key": key, "Value": value} for key, value in config['head_node_tags']]

    headnode_ebs_tags = construct_bright_tags(
        vpc.cluster_name, head_node_instance_and_ebs_name  # type: ignore[attr-defined]
    )

    headnode_eni_tags = construct_bright_tags(
        cluster_name=vpc.cluster_name,  # type: ignore[attr-defined]
        obj_name=f"{vpc.cluster_name}-a network interface",  # type: ignore[attr-defined]
        bcm_type="Network Interface",
    )
    kwargs["TagSpecifications"] = [
        {"ResourceType": "instance", "Tags": headnode_tags},
        {"ResourceType": "volume", "Tags": headnode_ebs_tags},
        {"ResourceType": "network-interface", "Tags": headnode_eni_tags},
    ]

    network_interface = {
        "DeviceIndex": 0,
        "SubnetId": public_subnet.id,
        "Groups": [head_node_sg_id],
        "DeleteOnTermination": False,
        "Description": "Primary Head Node NIC",
    }
    kwargs["NetworkInterfaces"] = [network_interface]

    if config["headnode_instance_profile"]:
        if re.match(r"arn:aws:iam::(\d+):instance-profile/(\w+)", config["headnode_instance_profile"]):
            field = "Arn"
        else:
            field = "Name"

        kwargs["IamInstanceProfile"] = {
            field: config["headnode_instance_profile"]
        }

    instances = ec2_client.create_instances(**kwargs)
    head_node_instance = instances[0]
    log.info(f"Created VM {head_node_instance.id}")

    log.debug("Waiting for VM to exist so that we can assign tags")
    _retry_not_found(head_node_instance.wait_until_exists)

    log.debug("Applying tags to the head node VM instance")
    return head_node_instance


def _create_network_acls(vpc: Vpc, public_subnet: Subnet, private_subnet: Subnet, ec2_client: EC2Client) -> None:
    def _replace_subnet_acl(subnet: Subnet, network_acl: NetworkAcl, ec2_client: EC2Client) -> None:
        response = ec2_client.describe_network_acls(Filters=[{'Name': 'association.subnet-id', 'Values': [subnet.id]}])
        # The response is a description of ACL, so it may contain multiple associations even we filtered by subnet.id
        # Find out the real association of the subnet, every subnet is guaranteed to associate with exactly one ACL
        association_id = next((association['NetworkAclAssociationId']
                               for association in response['NetworkAcls'][0]['Associations']
                               if association['SubnetId'] == subnet.id), None
                              )
        assert association_id, "Association ID not found"
        ec2_client.replace_network_acl_association(
            AssociationId=association_id,
            NetworkAclId=network_acl.id
        )

    def _allow_basic_traffic(vpc: Vpc, network_acl: NetworkAcl) -> None:
        # All outbound traffic
        network_acl.create_entry(
            CidrBlock="0.0.0.0/0",
            Egress=True,
            Protocol=str(-1),
            RuleAction="allow",
            RuleNumber=100
        )
        # All inbound traffic originating from own VPC
        network_acl.create_entry(
            CidrBlock=vpc.cidr_block,
            Egress=False,
            Protocol=str(-1),
            RuleAction="allow",
            RuleNumber=RESERVED_NETWORK_ACL_RULE_NUM
        )
        # Ephemeral ports
        if config["head_node_assign_public_ip"]:
            # Cluster with public IP is useless unless ephemeral ports are open for the public ACL.
            # Ports to be opened is decided based on "Ephemeral Ports" documentatation here:
            # https://docs.aws.amazon.com/vpc/latest/userguide/custom-network-acl.html
            # Ephemeral port range should be reviewed during the HA setup, as NAT gateway is deployed there,
            # Altering the required range
            ephemeral_port_range: PortRangeTypeDef = {
                "From": 1024 if config["configure_nat_gateway"] else 32768,
                "To": 65535
            }
            network_acl.create_entry(
                CidrBlock="0.0.0.0/0",
                Egress=False,
                PortRange=ephemeral_port_range,
                Protocol=str(6),  # TCP
                RuleAction="allow",
                RuleNumber=EPHEMERAL_PORTS_ACL_RULE_NUM
            )

    log.info(f"Creating public and private Network ACLs for {vpc.cluster_name}")  # type: ignore[attr-defined]

    # Setup public subnet's ACL rule
    public_network_acl_name = vpc.cluster_name + " public network acl"  # type: ignore[attr-defined]
    public_tags = construct_bright_tags(vpc.cluster_name, public_network_acl_name)  # type: ignore[attr-defined]
    public_network_acl = vpc.create_network_acl(
        TagSpecifications=[{"ResourceType": "network-acl", "Tags": public_tags}]
    )
    log.info(f"Created public network ACL: {public_network_acl.id}")
    _allow_basic_traffic(vpc, public_network_acl)
    for network_acl_rule in config["inbound_network_acl_rule"]:
        log.debug(f"Adding ACL rule {network_acl_rule.network_acl_rule!r}")
        # [SRC_CIDR,]DST_PORT_OR_PORT_RANGE:TCP|UDP,ALLOW|DENY,RULE_NUM
        if network_acl_rule.rule_type == RuleType.TCP_OR_UDP:
            public_network_acl.create_entry(
                CidrBlock=network_acl_rule.src_cidr,
                Egress=False,
                PortRange={
                    'From': int(network_acl_rule.dst_first_port),
                    'To': int(network_acl_rule.dst_last_port)
                },
                Protocol=network_acl_rule.protocol_numeric_str,
                RuleAction=network_acl_rule.rule_action,
                RuleNumber=network_acl_rule.rule_number
            )
        # [SRC_CIDR,]ICMP|ALL,ALLOW|DENY,RULE_NUM
        elif network_acl_rule.rule_type == RuleType.ICMP_OR_ALL:
            public_network_acl.create_entry(
                CidrBlock=network_acl_rule.src_cidr,
                Egress=False,
                IcmpTypeCode={
                    'Code': -1,
                    'Type': -1
                },
                Protocol=network_acl_rule.protocol_numeric_str,
                RuleAction=network_acl_rule.rule_action,
                RuleNumber=network_acl_rule.rule_number
            )
        else:
            raise CODException("Unrecongized Network ACL Type, please check 'inbound_network_acl_rule' config syntax.")
    _replace_subnet_acl(public_subnet, public_network_acl, ec2_client)

    # Setup private subnet's ACL rule
    private_network_acl_name = vpc.cluster_name + " private network acl"  # type: ignore[attr-defined]
    private_tags = construct_bright_tags(vpc.cluster_name, private_network_acl_name)  # type: ignore[attr-defined]
    private_network_acl = vpc.create_network_acl(
        TagSpecifications=[{"ResourceType": "network-acl", "Tags": private_tags}]
    )
    log.info(f"Created private network ACL: {private_network_acl.id}")
    _allow_basic_traffic(vpc, private_network_acl)

    # Private subnet is unconfigurable at this stage, so allow ICMP and ephemeral ports from anywhere
    private_network_acl.create_entry(
        CidrBlock="0.0.0.0/0",
        Egress=False,
        IcmpTypeCode={
            'Code': -1,
            'Type': -1
        },
        Protocol=str(1),  # ICMP
        RuleAction="allow",
        RuleNumber=100
    )

    _replace_subnet_acl(private_subnet, private_network_acl, ec2_client)


def _create_security_groups(vpc: Vpc, ingress_icmp_cidr: list[str] | None) -> tuple[str, str]:
    head_sg_name = f"BCM {vpc.cluster_name}-headnode"  # type: ignore[attr-defined]
    head_sg_tags = construct_bright_tags(vpc.cluster_name, head_sg_name)  # type: ignore[attr-defined]
    head_sg = vpc.create_security_group(
        GroupName=head_sg_name,
        Description=(
            f"Security group for head node in BCM COD-AWS cluster {vpc.cluster_name}"  # type: ignore[attr-defined]
        ),
        TagSpecifications=[{"ResourceType": "security-group", "Tags": head_sg_tags}],
    )
    log.info(f"Created security group for the head node: {head_sg.id}")

    node_sg_name = f"BCM {vpc.cluster_name}-node"  # type: ignore[attr-defined]
    node_sg_tags = construct_bright_tags(vpc.cluster_name, node_sg_name)  # type: ignore[attr-defined]
    node_sg = vpc.create_security_group(
        GroupName=node_sg_name,
        Description=(
            f"Security group for compute nodes in BCM COD-AWS cluster {vpc.cluster_name}"  # type: ignore[attr-defined]
        ),
        TagSpecifications=[{"ResourceType": "security-group", "Tags": node_sg_tags}],
    )
    log.info(f"Created security group for the compute node: {node_sg.id}")

    log.debug("Configuring the security groups")
    # Configure head node sec group
    for inbound_rule in InboundTrafficRule.process_inbound_rules(config["inbound_rule"]):
        log.debug(f"Allowing incoming {inbound_rule.protocol} traffic to head node from {inbound_rule.src_cidr}")
        try:
            head_sg.authorize_ingress(
                IpProtocol=inbound_rule.protocol,
                FromPort=int(inbound_rule.dst_first_port),
                ToPort=int(inbound_rule.dst_last_port),
                CidrIp=inbound_rule.src_cidr,
            )
        except ClientError as e:
            if e.response['Error']['Code'] == 'InvalidPermission.Duplicate':
                log.debug(f"Duplicate {inbound_rule.protocol} inbound rule for {inbound_rule.src_cidr} detected. "
                          "Ignoring.")
            else:
                raise e

    # Enable node to head access
    head_sg.authorize_ingress(
        IpPermissions=[{"IpProtocol": "-1", "UserIdGroupPairs": [{"GroupId": node_sg.id}]}]
    )

    # Allow incoming ICMP to head
    if ingress_icmp_cidr is not None:
        for ingress_rule in ingress_icmp_cidr:
            try:
                log.debug(f"Allowing incoming ICMP traffic to head node from {str(ingress_rule)}")
                head_sg.authorize_ingress(
                    IpProtocol="icmp",
                    FromPort=-1,
                    ToPort=-1,
                    CidrIp=str(ingress_rule),
                )
            except ClientError as e:
                if e.response['Error']['Code'] == 'InvalidPermission.Duplicate':
                    log.debug(f"Duplicate ICMP ingress rule for {str(ingress_rule)} detected. Ignoring.")
                else:
                    raise e

    # Allow for node to node, and head to node.
    node_sg.authorize_ingress(
        IpPermissions=[
            {
                "IpProtocol": "-1",
                "UserIdGroupPairs": [
                    {"GroupId": head_sg.id},
                    {"GroupId": node_sg.id},
                ],
            }
        ]
    )
    return head_sg.id, node_sg.id


def _create_placement_group(cluster: Cluster, placement_group_name: str) -> None:
    cluster.create_placement_group(placement_group_name)


def _disable_source_dest_check(head_node_instance: Instance) -> None:
    head_node_instance.modify_attribute(SourceDestCheck={"Value": False})


def _vpc_with_name_exists(vpc_name: str, ec2: EC2ServiceResource) -> bool:
    vpcs = list(ec2.vpcs.filter(Filters=[{
        "Name": "tag:Name",
        "Values": [vpc_name]
    }]))

    return True if vpcs else False


def _find_main_route_table(vpc: Vpc) -> RouteTable:
    route_tables = list(vpc.route_tables.filter(
        Filters=[{
            "Name": "association.main",
            "Values": ["true"]
        }]
    ))
    assert 1 == len(route_tables)
    return route_tables[0]


def get_aws_tag(tags: list[TagTypeDef], name: str, default: str | None = None) -> str:
    """
    For some mysterious reason, boto3 stores tags as a list of dictionaries:
    [{'Key': 'Name', 'Value': 'my-value-foo'}].
    This function retrieves the value
    """

    if tags is not None:
        for tag in tags:
            if tag["Key"] == name:
                return tag["Value"]

    if default is not None:
        return default

    raise CODException(f"The AWS tag '{name}' was not found within {len(tags)} tags.")
