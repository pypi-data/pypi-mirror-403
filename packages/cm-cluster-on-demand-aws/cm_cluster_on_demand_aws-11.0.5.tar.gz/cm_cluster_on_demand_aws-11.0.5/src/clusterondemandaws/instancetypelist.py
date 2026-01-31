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

import json
import logging

import clusterondemand.configuration
from clusterondemand.codoutput.sortingutils import SortableData
from clusterondemandconfig import ConfigNamespace, config

from .configuration import awscommon_ns
from .instancetype import get_available_instance_types, list_regions

columns = [
    ("region", "Region"),
    ("instancetype", "Instance Type"),
    ("vcpus", "vCPUs"),
    ("memory", "Memory (GiB)"),
]
log = logging.getLogger("cluster-on-demand")


HR = "---------------------------------------------------------------------"

config_ns = ConfigNamespace("aws.instancetype.list", "list output parameters")
config_ns.import_namespace(awscommon_ns)
config_ns.import_namespace(clusterondemand.configuration.clusterlist_ns)
config_ns.add_enumeration_parameter(
    "sort",
    default=["region", "instancetype", "vcpus", "memory"],
    choices=[col[0] for col in columns],
    help="Column according to which the table should be sorted (asc order).",
)
config_ns.add_switch_parameter(
    "all_regions",
    default=False,
    help="List instance types in all available regions",
)
config_ns.override_imported_parameter(
    "output_format",
    choices=["table", "json"],
    help_varname=None,
)

PRODUCTS_FILTER = [
    {"Type": "TERM_MATCH", "Field": "operatingSystem", "Value": "Linux"},
    {"Type": "TERM_MATCH", "Field": "preInstalledSw", "Value": "NA"},
    {"Type": "TERM_MATCH", "Field": "tenancy", "Value": "Shared"},
]

PRODUCT_FAMILIES = [
    {"Type": "TERM_MATCH", "Field": "productFamily", "Value": "Compute Instance"}
]


def run_command() -> None:
    return InstanceTypesList().run()


class InstanceTypesList:
    @classmethod
    def map_regions_to_instance_types(
        cls, chosen_region: str | None = None
    ) -> dict[str, list[dict[str, str | int | float]]]:
        regions = [chosen_region] if chosen_region else list_regions()
        region_to_instance_data: dict[str, list[dict[str, str | int | float]]] = {}
        for region in regions:
            region_to_instance_data[region] = []
            for instance_name, instance_info in get_available_instance_types(
                region
            ).items():
                vcpus = instance_info.get("VCpuInfo", {}).get("DefaultVCpus", 0)
                memory_mib = instance_info.get("MemoryInfo", {}).get("SizeInMiB", 0)
                memory_gib = round(memory_mib / 1024, 2) if memory_mib else 0
                region_to_instance_data[region].append(
                    {"name": instance_name, "vcpus": vcpus, "memory": memory_gib}
                )
        return region_to_instance_data

    def output_json_file(self) -> None:
        """Print out all mappings in JSON format."""
        print(
            json.dumps(
                {
                    "regions": {
                        region: sorted(
                            [
                                {
                                    "name": inst["name"],
                                    "vcpus": inst["vcpus"],
                                    "memory_gib": inst["memory"],
                                }
                                for inst in instances_data
                            ],
                            key=lambda x: x["name"],
                        )
                        for region, instances_data in self.mapping.items()
                    }
                },
                indent=4,
                sort_keys=True,
            )
        )

    def output_prettytable(self, all_columns: list[tuple[str, str]]) -> None:
        """Print all mappings in a Table."""
        region_to_instancetype = []
        for region, instances in self.mapping.items():
            for inst in instances:
                region_to_instancetype.append(
                    [region, inst["name"], inst["vcpus"], inst["memory"]]
                )
        cols_id = [column[0] for column in all_columns]
        table = SortableData(
            all_headers=all_columns,
            requested_headers=cols_id,
            rows=region_to_instancetype,
        )
        table.sort(*config["sort"])
        print(table.output(output_format=config["output_format"]))

    def run(self) -> None:
        region = None
        if not config["all_regions"]:
            region = config["aws_region"]
        self.mapping = self.map_regions_to_instance_types(chosen_region=region)

        if config["output_format"] == "json":
            self.output_json_file()
        elif config["output_format"] == "table":
            self.output_prettytable(columns)
