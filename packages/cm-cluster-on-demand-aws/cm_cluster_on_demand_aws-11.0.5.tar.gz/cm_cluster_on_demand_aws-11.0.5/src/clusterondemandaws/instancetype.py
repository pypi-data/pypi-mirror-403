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
from functools import cache

from clusterondemandaws.awsconnection import create_aws_service_client
from clusterondemandconfig import config

if typing.TYPE_CHECKING:
    from mypy_boto3_ec2.client import EC2Client
    from mypy_boto3_ec2.type_defs import FilterTypeDef, InstanceTypeInfoTypeDef

log = logging.getLogger("cluster-on-demand")


PRODUCTS_FILTER = [
    {"Type": "TERM_MATCH", "Field": "operatingSystem", "Value": "Linux"},
    {"Type": "TERM_MATCH", "Field": "preInstalledSw", "Value": "NA"},
    {"Type": "TERM_MATCH", "Field": "tenancy", "Value": "Shared"},
]

PRODUCT_FAMILIES = [
    {"Type": "TERM_MATCH", "Field": "productFamily", "Value": "Compute Instance"}
]


def list_regions() -> list[str]:
    """Return a list of available regions in an AWS subscription."""
    ec2_client: EC2Client = create_aws_service_client(
        service_name="ec2",
        region_name=config["aws_region"],
    )
    regions = ec2_client.describe_regions()["Regions"]
    region_names = [region["RegionName"] for region in regions]
    return region_names


@cache
def get_available_instance_types(region: str) -> dict[str, InstanceTypeInfoTypeDef]:
    ec2_client: EC2Client = create_aws_service_client(
        service_name="ec2",
        region_name=region,
    )

    log.debug(f"Finding instance types for region: {region}")
    instance_types: dict[str, InstanceTypeInfoTypeDef] = {}
    paginator = ec2_client.get_paginator("describe_instance_types")
    filters: list[FilterTypeDef] = [{"Name": "supported-virtualization-type", "Values": ["hvm"]}]
    for page in paginator.paginate(Filters=filters):
        for instance_type_definition in page.get("InstanceTypes", []):
            if type_name := instance_type_definition.get("InstanceType"):
                instance_types[type_name] = instance_type_definition

    return instance_types
