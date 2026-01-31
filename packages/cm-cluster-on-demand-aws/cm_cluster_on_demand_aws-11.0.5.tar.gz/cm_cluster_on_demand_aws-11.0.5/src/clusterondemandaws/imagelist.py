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

import clusterondemand.configuration
from clusterondemand.imagetable import ALL_COLUMNS, make_cod_images_table
from clusterondemandconfig import ConfigNamespace, config

from .configuration import awscommon_ns
from .images import AWSImageSource, findimages_ns

log = logging.getLogger("cluster-on-demand")

AWS_COLUMNS = [
    ("name", "Image name"),
    ("distro", "Distro"),
    ("bcm_version", "BCM Version"),
    ("arch", "Arch"),
    ("created_at", "Created"),
    ("is_public", "Public"),
    ("uuid", "UUID"),
]

assert all(col in ALL_COLUMNS for col in AWS_COLUMNS)


config_ns = ConfigNamespace("aws.image.list", "list output options")
config_ns.import_namespace(awscommon_ns)
config_ns.import_namespace(findimages_ns)
config_ns.import_namespace(clusterondemand.configuration.clusterlist_ns)
config_ns.add_enumeration_parameter(
    "sort",
    default=["bcm_version", "created_at"],
    choices=[column[0] for column in AWS_COLUMNS],
    help="Sort results by one (or two) of the columns"
)
config_ns.add_enumeration_parameter(
    "columns",
    default=[column[0] for column in AWS_COLUMNS],
    choices=[column[0] for column in AWS_COLUMNS],
    help="Provide set of columns to be displayed"
)


def run_command() -> None:
    log.info("Listing images in region %s" % config["aws_region"])

    print(make_cod_images_table(
        AWSImageSource.find_images_using_options(config),
        sortby=config["sort"],
        advanced=True,
        columns=config["columns"],
        output_format=config["output_format"]
    ))
