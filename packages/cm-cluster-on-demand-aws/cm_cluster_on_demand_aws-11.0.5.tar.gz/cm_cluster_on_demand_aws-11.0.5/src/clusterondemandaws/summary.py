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

import typing

from clusterondemand.summary import SummaryGenerator, SummaryType

if typing.TYPE_CHECKING:
    from prettytable import PrettyTable

    from clusterondemand.images.find import CODImage
    from clusterondemand.node_definition import NodeDefinition
    from clusterondemandconfig.configuration import ConfigurationView

    from .cluster import Cluster


class AwsSummaryGenerator(SummaryGenerator):
    """Generate the summary for creation of AWS clusters and nodes."""

    def __init__(self,
                 cluster: Cluster,
                 config: ConfigurationView,
                 summary_type: SummaryType | None = None,
                 head_node_definition: NodeDefinition | None = None,
                 head_image: CODImage | None = None,
                 node_definition: NodeDefinition | None = None,
                 vpc_name: str | None = None,
                 vpc_id: str | None = None,
                 vpc_cidr_block: str | None = None,
                 subnet_texts: list[str] | None = None,
                 ip: str | None = None,
                 ssh_string: str | None = None,
                 region: str | None = None,
                 availability_zone: str | None = None) -> None:
        # Initialise the parent with the cluster name.
        super().__init__(
            # We hijack parent's "head_name" argument, because names in AWS are weird, name is actually a tag.
            # Also, head node's name tag =/= cluster_name.
            head_name=cluster.name,
            region=region or (config["aws_region"] if config else None),
            config=config,
            head_image=head_image,
            primary_head_node_definition=head_node_definition,
            node_definitions=[node_definition] if node_definition else None,
            summary_type=summary_type,
            ip=ip,
            ssh_string=ssh_string,
        )
        self._cluster = cluster
        self._config = config
        self._vpc_name = vpc_name
        self._vpc_id = vpc_id
        self._vpc_cidr = vpc_cidr_block
        self._subnet_texts = subnet_texts if subnet_texts else []
        self._use_instance_profile = config["headnode_instance_profile"] if config else False
        self._availability_zone = availability_zone

    def _add_rows(self, table: PrettyTable) -> None:
        self._add_credentials_message(table)
        if self._config and self._config["existing_vpc_id"]:
            self._add_existing_vpc(table)

        self._add_region(table)
        self._add_availability_zone(table)

    def _add_availability_zone(self, table: PrettyTable) -> None:
        if self._availability_zone:
            table.add_row(["Availability zone:", self._availability_zone])

    def _add_header(self, table: PrettyTable) -> None:
        self._add_separator(table)
        self._add_cluster_name(table)
        self._add_separator(table)

    def _add_cluster_name(self, table: PrettyTable) -> None:
        table.add_row(["Cluster:", self._cluster.name])

    def _add_credentials_message(self, table: PrettyTable) -> None:
        if self._use_instance_profile:
            table.add_row(["Cloud authentication:", "Head node will use instance profile for cloud authentication"])
        else:
            table.add_row(["Cloud authentication:", "Head node will inherit COD credentials for cloud authentication"])

    def _add_existing_vpc(self, table: PrettyTable) -> None:
        table.add_row(["Existing VPC:", f"{self._vpc_name} ({self._vpc_id}, {self._vpc_cidr})"])
        if self._config and not self._config["head_node_assign_public_ip"]:
            table.add_row(["", "Head node will NOT have a public IP assigned."])
        table.add_row(["", "All subnets currently present in this VPC:"])
        for text in self._subnet_texts:
            table.add_row(["-", text])
        table.add_row(["", "(Subnets marked with '*' will get defined as Networks within the BCM cluster)"])
        self._add_separator(table)
