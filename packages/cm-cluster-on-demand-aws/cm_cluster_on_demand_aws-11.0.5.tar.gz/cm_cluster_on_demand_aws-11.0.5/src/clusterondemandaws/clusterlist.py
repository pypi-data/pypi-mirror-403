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
from clusterondemand.clusternameprefix import clusterprefix_ns, ensure_cod_prefix
from clusterondemand.codoutput.sortingutils import ClusterIPs, SortableData
from clusterondemand.utils import log_no_clusters_found
from clusterondemandaws.base import ClusterCommandBase
from clusterondemandconfig import ConfigNamespace, config

from .awsconnection import create_aws_service_resource
from .cluster import Cluster
from .configuration import awscommon_ns

if typing.TYPE_CHECKING:
    from mypy_boto3_ec2.service_resource import EC2ServiceResource, Image, Instance

log = logging.getLogger("cluster-on-demand")

ALL_COLUMNS = [
    ("cluster_name", "Cluster Name"),
    ("vpc_id", "VPC ID"),
    ("head_node_id", "Head node ID (* = active)"),
    ("cluster_ip", "Cluster IP"),
    ("state", "State"),
    ("type", "Type"),
    ("image_name", "Image Name"),
    ("created", "Image Created"),
]


def run_command() -> None:
    ClusterList().run()


config_ns = ConfigNamespace("aws.cluster.list", "list output parameters")
config_ns.import_namespace(awscommon_ns)
config_ns.import_namespace(clusterprefix_ns)
config_ns.import_namespace(clusterondemand.configuration.clusterlist_ns)
config_ns.add_enumeration_parameter(
    "sort",
    default=["created"],
    choices=[column[0] for column in ALL_COLUMNS],
    help="Sort results by one (or two) of the columns"
)
config_ns.add_enumeration_parameter(
    "columns",
    choices=[column[0] for column in ALL_COLUMNS],
    help="Provide space separated set of columns to be displayed"
)
config_ns.add_repeating_positional_parameter(
    "filters",
    default=["*"],
    require_value=True,
    help="Cluster names or patterns to be listed. Default: all clusters. Wildcards are supported (e.g: \\*)",
)


class ClusterList(ClusterCommandBase):
    def run(self) -> None:
        ec2: EC2ServiceResource = create_aws_service_resource(service_name="ec2")
        log.info("Listing clusters in region %s" % config["aws_region"])

        names = [ensure_cod_prefix(name) for name in config["filters"]]
        clusters = list(Cluster.find(names))

        if not clusters:
            log_no_clusters_found("list")
            return

        rows = []
        for cluster in clusters:
            head_node = cluster.primary_head_node

            row: list[str | ClusterIPs] = []
            row += [cluster.name]
            row += [cluster.vpc.id if cluster.vpc else ""]

            if cluster.is_ha:
                head_node_type_to_address_map = cluster.map_head_node_type_to_address(cluster.primary_head_node)
                head_node_type_to_address_map.update(cluster.map_head_node_type_to_address(cluster.secondary_head_node))

                primary_private_address = head_node_type_to_address_map.get(Cluster.IpType.A)
                primary_public_ip = primary_private_address["Association"]["PublicIp"] if \
                    primary_private_address and primary_private_address.get("Association") else None

                secondary_private_address = head_node_type_to_address_map.get(Cluster.IpType.B)
                secondary_public_ip = secondary_private_address["Association"]["PublicIp"] if \
                    secondary_private_address and secondary_private_address.get("Association") else None

                ha_private_address = head_node_type_to_address_map.get(Cluster.IpType.HA)
                ha_public_ip = ha_private_address["Association"].get("PublicIp") if \
                    ha_private_address and ha_private_address.get("Association") else None

                def is_active_headnode(head_node: Instance | None) -> bool:
                    return head_node == cluster.active_head_node

                row += ["\n".join(
                    [
                        (cluster.primary_head_node.id + " (A)" if cluster.primary_head_node else "missing")
                        + (" *" if is_active_headnode(cluster.primary_head_node) else "")
                    ]
                    +
                    [
                        (cluster.secondary_head_node.id + " (B)" if cluster.secondary_head_node else "missing")
                        + (" *" if is_active_headnode(cluster.secondary_head_node) else "")
                    ]
                )]
                row += [
                    ClusterIPs(
                        primary_public_ip, secondary_public_ip, ha_public_ip,
                        primary_private_ip=(
                            primary_private_address["PrivateIpAddress"] if primary_private_address else ""
                        ),
                        secondary_private_ip=(
                            secondary_private_address["PrivateIpAddress"] if secondary_private_address else ""
                        ),
                    )
                ]
            else:
                row += [(cluster.primary_head_node.id if cluster.primary_head_node else "missing") + " *"]
                row += [
                    ClusterIPs(
                        cluster.primary_head_node.public_ip_address or None,
                        primary_private_ip=cluster.primary_head_node.private_ip_address or None,
                    ) if cluster.primary_head_node else ClusterIPs()
                ]

            row += [cluster.active_head_node.state["Name"] if cluster.active_head_node else ""]
            row += [cluster.active_head_node.instance_type if cluster.active_head_node else ""]

            img = None
            if head_node and head_node.image_id:
                img = ec2.Image(head_node.image_id)
            row += [_safe_image_name(img) if img else "none"]
            row += [_safe_image_creation_date(img) if img else "none"]

            rows.append(row)

        cols_id = config["columns"]
        if not cols_id:
            cols_id = [column[0] for column in ALL_COLUMNS]
        table = SortableData(all_headers=ALL_COLUMNS, requested_headers=cols_id, rows=rows)
        table.sort(*config["sort"])

        print(table.output(output_format=config["output_format"]))


def _safe_image_name(img: Image) -> str:
    try:
        return img.name
    except AttributeError:
        return "<unknown>"


def _safe_image_creation_date(img: Image) -> str:
    try:
        return img.creation_date
    except AttributeError:
        return "<unknown>"
