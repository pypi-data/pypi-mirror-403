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
import typing

import clusterondemand.configuration
import clusterondemand.inbound_traffic_rule as inbound_traffic_rule
from clusterondemand import utils
from clusterondemand.cidr import cidr, must_be_within_cidr
from clusterondemand.clustercreate import validate_inbound_rules
from clusterondemand.clusternameprefix import must_start_with_cod_prefix
from clusterondemand.exceptions import CODException
from clusterondemand.node_definition import NodeDefinition
from clusterondemand.ssh_key import validate_ssh_pub_key
from clusterondemand.summary import SummaryType
from clusterondemand.tags import tags_ns
from clusterondemand.wait_helpers import clusterwaiters_ns, wait_for_cluster
from clusterondemandaws.base import ClusterCommandBase
from clusterondemandaws.summary import AwsSummaryGenerator
from clusterondemandaws.vpc import get_aws_tag
from clusterondemandconfig import ConfigNamespace, config
from clusterondemandconfig.configuration_validation import (
    if_disabled_require_other_paramaters_to_be_disabled,
    if_not_set_requires_other_parameters_to_be_set,
    may_not_equal_none,
    requires_other_parameters_to_be_set
)

from .awsconnection import create_aws_service_resource
from .cluster import Cluster
from .configuration import awscommon_ns, wait_timeout_ns
from .images import AWSImageSource, findimages_ns
from .vpc import create_in_existing_vpc, create_vpc

if typing.TYPE_CHECKING:
    from typing import Callable

    from mypy_boto3_ec2.service_resource import EC2ServiceResource

    from clusterondemandconfig.configuration import ConfigurationView
    from clusterondemandconfig.parameter import Parameter

log = logging.getLogger("cluster-on-demand")

DEFAULT_DISK_SETUP = """
<diskSetup xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance'>
  <device>
    <blockdev>/dev/vdb</blockdev>
    <blockdev>/dev/sda</blockdev>
    <blockdev mode='cloud'>/dev/sdb</blockdev>
    <blockdev mode='cloud'>/dev/hdb</blockdev>
    <blockdev mode='cloud'>/dev/vdb</blockdev>
    <blockdev mode='cloud'>/dev/xvdb</blockdev>
    <blockdev mode='cloud'>/dev/xvdf</blockdev>
    <blockdev mode='cloud'>/dev/nvme1n1</blockdev>
    <partition id='a2'>
      <size>max</size>
      <type>linux</type>
      <filesystem>xfs</filesystem>
      <mountPoint>/</mountPoint>
      <mountOptions>defaults,noatime,nodiratime</mountOptions>
    </partition>
  </device>
</diskSetup>
"""

DEFAULT_DISK_SETUP_10_AND_ABOVE = """
<diskSetup xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance'>
  <device>
    <blockdev>/dev/vdb</blockdev>
    <blockdev>/dev/sda</blockdev>
    <blockdev mode='cloud'>/dev/sdb</blockdev>
    <blockdev mode='cloud'>/dev/hdb</blockdev>
    <blockdev mode='cloud'>/dev/vdb</blockdev>
    <blockdev mode='cloud'>/dev/xvdf</blockdev>
    <partition id='a2'>
      <size>max</size>
      <type>linux</type>
      <filesystem>xfs</filesystem>
      <mountPoint>/</mountPoint>
      <mountOptions>defaults,noatime,nodiratime</mountOptions>
    </partition>
  </device>
</diskSetup>
"""

config_ns = ConfigNamespace("aws.cluster.create", "cluster creation parameters")
config_ns.import_namespace(awscommon_ns)
config_ns.import_namespace(findimages_ns)
config_ns.import_namespace(clusterwaiters_ns)
config_ns.override_imported_parameter("version", default="11.0")
config_ns.import_namespace(clusterondemand.configuration.clustercreate_ns)
config_ns.import_namespace(clusterondemand.configuration.clustercreatename_ns)
config_ns.import_namespace(clusterondemand.configuration.cmd_debug_ns)
config_ns.import_namespace(clusterondemand.configuration.timezone_ns)
config_ns.import_namespace(wait_timeout_ns)
config_ns.import_namespace(tags_ns)
config_ns.override_imported_parameter(
    "head_node_type",
    default="t3.medium",
    help="The instance type must exist in the region you use.")
config_ns.override_imported_parameter(
    "head_node_root_volume_size",
    default=42,
    help="Head node root disk size in GB. Should be bigger than the AMI size.")
config_ns.add_switch_parameter(
    "validate_parameters",
    default=True,
    help=(
        "Validate parameters before creation. This involves doing API calls to the AWS API. "
        "It can be disabled with --no-validate-parameters (use with care)"
    )
)
config_ns.remove_imported_parameter("name")
config_ns.add_parameter(
    "name",
    help="Name of the cluster to create",
    validation=[may_not_equal_none, must_start_with_cod_prefix]
)
config_ns.override_imported_parameter("on_error", default="cleanup")

config_ns.add_parameter(
    "store_head_node_ip",
    help_varname="PATH_TO_FILE",
    help=("Once the cluster has been created, store the IP of the headnode in a file."
          " Useful for automation.")
)
config_ns.add_parameter(
    "store_head_node_id",
    help_varname="PATH_TO_FILE",
    help=("Once the cluster has been created, store the instance-id of the headnode in a file."
          " Useful for automation.")
)
config_ns.add_parameter(
    "ssh_key_pair",
    help=("Name of the AWS key pair used to access the headnode; must exist in your "
          "AWS account in the used region."),
    help_section=clusterondemand.configuration.clustercreatepassword_ns.help_section,
    help_varname="NAME",
)
config_ns.override_imported_parameter(
    "ingress_icmp",
    help="CIDR from which to allow ingress ICMP traffic to the head node."
         "Specify 'none' to disable ICMP altogether. Note that you also need to specify "
         "the ICMP rule in the --inbound-network-acl-rule parameter.",
)
config_ns.add_parameter(
    "head_node_image",
    help=("ID of the AMI to use. This value is determined automatically to latest, if"
          " not specified."),
    help_varname="ID"
)
config_ns.add_parameter(
    "head_node_root_volume_type",
    default="gp2",
    help="Head node root volume type"
)
config_ns.add_parameter(
    "head_node_root_volume_iops",
    default=1000,
    help=("IOPS for head node root volume. Should only be used when requesting io1 or io2 volume. AWS can impose a"
          " maximum based on the volume size. Also affects AWS pricing.")
)
config_ns.override_imported_parameter("node_type", default="t3.medium")
config_ns.override_imported_parameter(
    "ssh_pub_key_path", validation=lambda p, c: validate_ssh_pub_key(p, c, allowed_types=None)
)
config_ns.add_parameter(
    "vpc_cidr",
    advanced=True,
    default=cidr("10.0.0.0/16"),
    help=("CIDR range of the VPC. The VPC Subnets must fall within this range. "
          "The widest allowed range is /16."),
    help_varname="CIDR",
    parser=cidr
)
config_ns.add_parameter(
    "public_subnet_cidr",
    advanced=True,
    default=cidr("10.0.0.0/17"),
    help="Must be within the range of 'vpc_cidr'",
    help_varname="CIDR",
    parser=cidr,
    validation=must_be_within_cidr("vpc_cidr")
)
config_ns.add_parameter(
    "private_subnet_cidr",
    advanced=True,
    default=cidr("10.0.128.0/17"),
    help="Must be within the range of 'vpc-cidr'",
    help_varname="CIDR",
    parser=cidr,
    validation=must_be_within_cidr("vpc_cidr")
)
config_ns.add_parameter(
    "node_disk_setup",
    default=DEFAULT_DISK_SETUP)
config_ns.add_parameter(
    "aws_availability_zone",
    env="AWS_AVAILABILITY_ZONE",
    help=("Name of the AWS availability zone in which the subnet, and all of the VMs,"
          " will be created. When not specified, a random availability zone will be used."
          " Useful when your chosen VM type is not available in all availability zones.")
)
config_ns.add_enumeration_parameter(
    "inbound_network_acl_rule",
    help=("One or several inbound network acl rules for the cluster's head node in one of the following format: "
          f"[src_cidr,]dst_port:{inbound_traffic_rule.TRANSPORT_PROTOCOL},{inbound_traffic_rule.RULE_ACTION},rule_num' "
          f"or '[src_cidr,]{inbound_traffic_rule.ICMP_AND_ALL_PROTOCOL},{inbound_traffic_rule.RULE_ACTION},rule_num', "
          "where port can be a single port or a dash separated range. Supported rule_num: 1 to 32766, "
          f"but {inbound_traffic_rule.RESERVED_NETWORK_ACL_RULE_NUM} is reserved for communication inside a VPC. "
          f"Note: a special variable {inbound_traffic_rule.CLIENT_IP} can be used to substitute src_cidr, in which "
          "case COD client's public IP will be detected and used. Examples: '11.0.0.0/24,20-23:TCP,ALLOW,100' "
          "'443:TCP,ALLOW,200' 'ICMP,ALLOW,500' '10.0.0.0/16,ALL,ALLOW,500' {CLIENT_IP},22:tcp,ALLOW,101 "
          "Empty src_cidr is replaced by 0.0.0.0/0. A DENY all traffic is always existed at the end of all rules. "
          "It is recommended to allow ports 22:TCP, 80:TCP, 443:TCP, 8081:TCP, as well as ephemeral 32768-65535:tcp"),
    type=[inbound_traffic_rule.InboundNetworkACLRule],
)


#################################################################
# Extra documentation for the 'existing-vpc' scenario:
#################################################################
# Some scenarios we're attempting to cover here:
#
# A) Create cluster in a new VPC, and configure internet connectivity in that vpc:
#    this is the traditional cod-aws scenario - creating everything from scratch.
# B) Create cluster in a new VPC, but don't configure Internet connectivity:
#    The user will use e.g. Direct Connect to access the VPC, and doesn't want us
#    to mess with networking (or does not have policy permissions).
#
# C) Create cluster in an **EXISTING** VPC, don't configure the Internet connectivity.
#    The user already has a VPC they want to use. In such case, they typically also already have
#    some sort of connectivity into that VPC, and they don't want us to mess with it.
# D) Create cluster in an **EXISTING** VPC, and configure Internet connectivity in that VPC.
#    Theoretical use case: someone having AWS credentials, the security policy of which which allows them to
#    do anything they want with a VPC they've been allocated by their cloud networking team, EXCEPT for allowing them
#    to create new VPCs.
#    Except for the use case above, it's pretty hard to imagine someone already having
#    a production VPC they want to create a cluster in, but at the same time allowing cod-aws to tweak
#    Internet Connectivity of that VPC.
#    Since this scenario is risky, we have an extra flag user must use to confirm this is what they want.
#
# In all of the above described scenarios "configure Internet connectivity" can be further
# broken down into the following two:
#  - creating and configuring IGW in the VPC (and altering the routes)
#  - assigning the public IP to the head node
# In most cases, both will be either enabled, or disabled, but to cover all the bases, we allow to switch those
# separately.

config_ns.add_parameter(
    "existing_vpc_id",
    advanced=True,
    help="AWS VPC ID of an already existing VPC (format: 'vpc-....'). "
         "When specified, the COD-AWS cluster will be created within this VPC. "
         "Must be used in conjunction with '--existing-subnet-id' flag "
         "(the tool will not be creating any VPC subnets). "
         "Related flags: --existing-subnet-id, --head-node-assign-public-ip, "
         "--configure-igw-in-existing-vpc ",
    help_varname="VPC_ID",
    validation=requires_other_parameters_to_be_set(["existing_subnet_id"])
)

config_ns.add_enumeration_parameter(
    "existing_subnet_id",
    advanced=True,
    help="One or more already existing VPC subnet IDs (format: 'subnet-....'). "
         "The specified subnet(s) must exist within the VPC specified with --existing-vpc-id. "
         "The existing VPC can have one or more subnets. Of those, "
         "at least one subnet must be specified using this flag. "
         "All specified VPC subnets will be configured as Network entities within the BCM cluster "
         "(i.e. it will be possible to create cloud nodes on them). "
         "Subnets not specified at cluster-create-time can be added later on by manually "
         "creating new Network entities. "
         "The first specified VPC subnet will be the one hosting the head node (you cannot change this later). "
         "Compute nodes can be assigned to a different subnet by changing the Network entity of their NIC; this should "
         "be done before first-time powering on (creating) a compute node VM instance.",
    help_varname="SUBNET_ID",
    validation=requires_other_parameters_to_be_set(["existing_vpc_id"])
)

config_ns.add_parameter(
    # Technically, AWS calls those "Private IP". But I think in some other places (e.g. cod-os) we call those
    # internal IPs. So, maybe it makes sense to deviate from using per-provider terminology here
    "head_node_internal_ip",
    advanced=True,
    help="The internal/private IP address of the head node on the VPC subnet. "
         "If not specified, the cloud provider will pick this IP address. ",
    help_varname="HEAD_NODE_IP",
    # TODO(cloud-team): validate early that the IP is within the CIDR (otherwise it will fail later)
    #                   (a bit tricky to do when using existing VPC -- you'll have to get CIDR from existing subnet).

)


config_ns.add_switch_parameter(
    "head_node_assign_public_ip",
    default=True,
    advanced=True,
    help="Whether or not the head node will have a public IP address assigned. Enabled by default. "
         "Note that with this flag disabled, it will not be possible out of the box to reach the head node "
         "over the Internet. "
         "Therefore, this flag should only be disabled if there exists some other means to reach "
         "the head node, e.g. via a dedicated "
         "link into the VPC which can be used to access the head node via its internal/private IP address. "
         "Assigning the public IP is not required for the cluster creation to be successful, but not assigning it "
         "in some cases might cause the COD client to time out when waiting for cloud-init to finish. Thus, consider "
         "using '--wait-ssh=0' when disabling this flag. "
         "Related flags: --configure-igw-in-existing-vpc, --configure-igw, --wait-ssh, --wait-cmdaemon"
)


def _validate_user_confirmed_igw() -> Callable[[Parameter, ConfigurationView], None]:
    def validate(parameter: Parameter, configuration: ConfigurationView) -> None:
        item = configuration.get_item_for_key(parameter.name)
        if item.value and not configuration.get_item_for_key("i_know_configuring_igw_is_risky").value:
            raise CODException(
                "ATTENTION: Selected configuration asks for creating and configuring an Internet Gateway in an "
                "already existing VPC! This is risky and can break networking in the existing VPC. "
                "E.g. it will alter the routes in the existing VPC, which is rarely desirable. "
                "If you know what you're doing, and you're sure you want to proceed "
                "regardless, please add '--i-know-configuring-igw-is-risky' flag to the CLI. "
                "Alternatively, to not configure the IGW in the existing VPC, make sure that "
                "--configure-igw-in-existing-vpc is not set.")
    return validate


config_ns.add_switch_parameter(
    "configure_igw_in_existing_vpc",
    default=False,
    advanced=True,
    # not adding 'i_know_configuring_igw_is_risky' into the "requires_other..." validation so that we can print more
    # using a custom validation instead
    validation=[
        requires_other_parameters_to_be_set(["existing_vpc_id"]),
        _validate_user_confirmed_igw(),  # we want a dedicated error message here
    ],
    help="By default, when creating the cluster in an existing VPC, the cod-aws tool will "
         "not attempt to configure the Internet access in that VPC by creating and configuring an IGW. "
         "This flag can be used to change this behavior. It may only be used in conjunction with '--existing-vpc-id'. "
)

config_ns.add_switch_parameter(
    "i_know_configuring_igw_is_risky",
    default=False,
    advanced=True,
    validation=requires_other_parameters_to_be_set(["existing_vpc_id", "configure_igw_in_existing_vpc"]),
    help="This flag should be used with caution. "
         "Can only be used with '--existing-vpc-id'. "
         "Must be used with '--configure-igw-in-existing-vpc' to confirm that the user is aware that "
         "allowing cod-aws client to create and configure IGW in "
         "an existing VPC is risky can cause issues. Configuring IGW might result in altering the routes in the VPC, "
         "potentially breaking existing networking connectivity in the VPC, and affecting other existing resources. "
)

config_ns.add_switch_parameter(
    "configure_igw",
    default=True,
    advanced=True,
    help="By default, when creating the cluster in a new VPC, the cod-aws tool will "
         "configure the Internet access in that VPC by creating and configuring an IGW. "
         "Disabling this flag will change this behavior by not creating/configuring any IGW. "
         "The flag should be only be disabled if there exist some other means of accessing the head node's "
         "private IP, e.g. a VPN or a Direct Connect link. "
         "The value of this flag has no effect when creating the cluster in an existing VPC. "
         "Must be used along with '--no-head-node-assign-public-ip'.",
    # There's no point in trying to assign a public IP if we know for a fact there won't be any IGW.
    # Thus, we require the user to explicitly acknowledge that no public IP will be assigned
    validation=if_disabled_require_other_paramaters_to_be_disabled(["head_node_assign_public_ip"])
)

config_ns.add_switch_parameter(
    "configure_nat_gateway",
    default=False,
    advanced=True,
    help="By default, HA clusters will create and route traffic through a NAT gateway for the private subnet. "
         "However, non-HA clusters will use their head node as the gateway for the private subnet. Enabling this "
         "option will require non-HA clusters to also create and route traffic through a NAT gateway for the private"
         " subnet."
)

config_ns.add_parameter(
    "head_node_sg_id",
    advanced=True,
    help_varname="HEAD_NODE_SEC_GROUP_ID",
    help="By default the security group for the head node is created by cod-aws tool. "
         "This optional parameter can be used to change this behavior by providing a pre-created security group ID. "
         "When specifying it, make sure to allow bidirectional access between the head node's SG and node's SG. "
         "If you want to tweak the sec. groups created by the cod-aws tool, use --ingress-rules. "
         "Related parameters: --node-sg-id, --wait-ssh, --wait-cmdaemon",
    validation=requires_other_parameters_to_be_set(["node_sg_id"])
)

config_ns.add_parameter(
    "node_sg_id",
    advanced=True,
    help_varname="NODE_SEC_GROUP_ID",
    help="By default the security group for the compute nodes is created by cm-cod-aws tool. "
         "This optional parameter can be used to change this behavior by providing a pre-created security group ID. "
         "Make sure to allow bidirectional access between the head node's SG and node's SG. "
         "Related parameter: --head-node-sg-id",
    validation=requires_other_parameters_to_be_set(["node_sg_id"])
)
config_ns.add_parameter(
    "head_node_pg_name",
    advanced=True,
    help="Name of the placement group for the head node."
)
config_ns.add_parameter(
    "headnode_instance_profile",
    help_varname="PROFILE",
    help="Instance profile to assign to the head node. Can be specified as short name or full ARN. The cluster will be "
         "configured to obtain credentials from the meta-data endpoint. The values of the --aws-access-key-id and "
         "--aws-secret-key settings will not be used by the head node CMDaemon.",
    validation=if_not_set_requires_other_parameters_to_be_set(["aws_access_key_id", "aws_secret_key"]),
)


def run_command() -> None:
    ClusterCreate().run()


def _cleanup_cluster(cluster: Cluster) -> None:
    """Clean up AWS resources when cluster creation fails."""
    log.info("Cleaning up AWS resources...")
    try:
        cluster.destroy()
        log.info("AWS resources cleaned up successfully.")
    except Exception as e:
        log.error(f"Error during cleanup: {e}")
        log.warning("Some AWS resources may need to be cleaned up manually.")


class ClusterCreate(ClusterCommandBase):

    def _validate_params(self, names: list[str], ec2: EC2ServiceResource) -> None:
        if config["validate_parameters"]:
            if config["head_node_assign_public_ip"] and not config["head_node_sg_id"]:
                validate_inbound_rules(inbound_rules=config["inbound_rule"])
            self._validate_inbound_network_acl_rule(
                inbound_acl_rules=config["inbound_network_acl_rule"],
                configure_acl_rules=not config["existing_vpc_id"] and config["head_node_assign_public_ip"]
            )
            self._validate_cluster_names_len_and_regex(names)
            self._validate_ssh_key_pair()
            self._validate_availability_zone()
            self._validate_instance_types()
            self._validate_instance_types_in_az()
            self._validate_instance_types_arch()
            self._validate_volume_types()
        else:
            log.warning("Ignoring parameter validation. Use --validate-parameters to enable it.")

        # We do NOT want this validation to be gated by 'config["validate_parameters"]'
        # The validation here is too important for this (code is touching existing/production VPCs of the customer).
        if config["existing_vpc_id"]:
            self._validate_params_existing_vpc(ec2)

    def _get_existing_vpc_details(
        self, ec2: EC2ServiceResource
    ) -> tuple[str | None, str | None, str | None, list[str]]:
        """Get information necessary for displaying information about existing VPCs"""
        if not config["existing_vpc_id"]:
            return (None, None, None, [])

        vpc = ec2.Vpc(config["existing_vpc_id"])
        vpc.load()

        head_node_subnet_id = config["existing_subnet_id"][0]
        head_node_subnet = next(
            (subnet for subnet in vpc.subnets.all() if subnet.id == head_node_subnet_id),
            None)

        vpc_name = get_aws_tag(vpc.tags, "Name", "<name not set>")
        vpc_id = config["existing_vpc_id"]
        vpc_cidr_block = vpc.cidr_block
        all_subnets_texts: list[str] = []

        for subnet in vpc.subnets.all():
            all_subnets_texts += [
                f"CIDR: {subnet.cidr_block}, "
                f"name: {get_aws_tag(subnet.tags, 'Name', '<name not set>')}, "
                f"AZ: {subnet.availability_zone}, ID: {subnet.id}"]
            if head_node_subnet and subnet.id == head_node_subnet.id:
                all_subnets_texts[-1] = all_subnets_texts[-1] + " <Head node>"
            if subnet.id in config["existing_subnet_id"]:
                all_subnets_texts[-1] = all_subnets_texts[-1] + " (*)"

        return (vpc_name, vpc_id, vpc_cidr_block, all_subnets_texts)

    def run(self) -> None:
        ec2: EC2ServiceResource = create_aws_service_resource(service_name="ec2")
        cluster_name = config["name"]
        self._validate_params([cluster_name], ec2)

        head_node_image = AWSImageSource.pick_head_node_image_using_options(config)
        if not head_node_image.version and config["run_cm_bright_setup"]:
            log.warning(
                f"Using custom image: {head_node_image.uuid} with parameter run_cm_bright_setup set to 'yes'."
                f" Probably it was set by mistake because a custom image might not have necessary files"
                f" to run cm-bright-setup. Consider using --run-cm-bright-setup=no to "
            )

        def _print_overview(cluster: Cluster) -> None:
            vpc_name, vpc_id, vpc_cidr_block, subnet_texts = self._get_existing_vpc_details(ec2)
            head_node_definition = NodeDefinition(1, config["head_node_type"])
            node_definition = NodeDefinition(config["nodes"], config["node_type"])
            generator = AwsSummaryGenerator(
                cluster=cluster,
                config=config,
                summary_type=SummaryType.Proposal,
                head_node_definition=head_node_definition,
                head_image=head_node_image,
                node_definition=node_definition,
                vpc_name=vpc_name,
                vpc_id=vpc_id,
                vpc_cidr_block=vpc_cidr_block,
                subnet_texts=subnet_texts,
                availability_zone=config["aws_availability_zone"],
            )
            generator.print_summary(log.info)

        cluster = Cluster(cluster_name, head_node_image)
        _print_overview(cluster)

        if config["ask_to_confirm_cluster_creation"]:
            utils.confirm_cluster_creation()

        # Run cluster creation
        log.debug("Running Cluster creation")

        ip = None
        try:
            # cluster.vpc and cluster.primary_head_node will be written in this call
            if config["existing_vpc_id"]:
                create_in_existing_vpc(cluster)
            else:
                create_vpc(cluster)

            ip = _setup_head_node_ip(cluster)

        except Exception as e:
            log.error(f"The following error occurred while creating the cluster: {e}")
            if config["on_error"] == "cleanup":
                _cleanup_cluster(cluster)
            else:
                log.info("Failed environment was kept and will have to be deleted manually.")
            raise

        log.info("Deployment finished successfully.")

        wait_for_cluster(
            config=config,
            host=ip,
        )

        ssh_string = f"ssh root@{ip}"

        generator = AwsSummaryGenerator(
            cluster=cluster,
            config=config,
            summary_type=SummaryType.Overview,
            ip=ip,
            ssh_string=ssh_string,
            region=config["aws_region"],
            availability_zone=config["aws_availability_zone"],
        )
        generator.print_summary(log.info)

        # Store outputs if requested
        _store_cluster_outputs(cluster, ip)


def _store_cluster_outputs(cluster: Cluster, ip: str) -> None:
    """Store cluster outputs to files if requested."""
    if config["store_head_node_ip"]:
        with open(config["store_head_node_ip"], "w") as f:
            f.write(f"{ip} {cluster.name}\n")
        log.info(f"Stored IP in {config['store_head_node_ip']}")

    if config["store_head_node_id"]:
        if cluster.primary_head_node and cluster.primary_head_node.id:
            with open(config["store_head_node_id"], "w") as f:
                f.write(cluster.primary_head_node.id + " " + cluster.name + "\n")
            log.info(f"Stored ID in {config['store_head_node_id']}")


def _setup_head_node_ip(cluster: Cluster) -> str:
    # If the head node is not found at this point, something went terribly wrong
    assert cluster.primary_head_node, f"Cannot find head node for cluster {cluster.name}"

    # Handle IP assignment
    if not config["head_node_assign_public_ip"]:
        log.info(
            "Will not assign a public IP to the head node "
            "(use '--head-node-assign-public-ip' to change this)"
        )
    else:
        log.info(
            "Assigning public IP to the head node "
            "(use '--no-head-node-assign-public-ip' to skip)"
        )
        if config["existing_vpc_id"] and not config["configure_igw_in_existing_vpc"]:
            log.info(
                "Note: Creating cluster in existing VPC without configuring an Internet Gateway. "
                "Assigning a public IP may fail unless the VPC already has internet access configured."
            )
        try:
            cluster.attach_eips_to_head_nodes()
        except Exception as e:
            cluster.error_message = str(e)
            raise CODException(f"Failed to attach Elastic IP: {str(e)}")

    # Return the appropriate IP address
    ip = (
        cluster.primary_head_node.public_ip_address
        if config["head_node_assign_public_ip"]
        else cluster.primary_head_node.private_ip_address
    )

    if not ip:
        raise CODException("Cannot find head node public or private IP")

    return ip
