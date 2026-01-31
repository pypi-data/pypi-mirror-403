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
import typing
from datetime import datetime

from clusterondemand.images.find import CODImage, ImageSource
from clusterondemand.images.find import findimages_ns as common_findimages_ns
from clusterondemandconfig import ConfigNamespace, config

from .awsconnection import create_aws_service_resource

if typing.TYPE_CHECKING:
    from typing import Any

    from mypy_boto3_ec2.service_resource import EC2ServiceResource, Image
    from mypy_boto3_ec2.type_defs import FilterTypeDef

    from clusterondemandconfig.configuration import ConfigurationView

log = logging.getLogger("cluster-on-demand")

findimages_ns = ConfigNamespace("aws.images.find", help_section="image filter parameters")
findimages_ns.import_namespace(common_findimages_ns)
findimages_ns.override_imported_parameter("cloud_type", default="aws")
findimages_ns.add_parameter(
    "image_owner",
    default="137677339600",
    help="AWS account ID of the account containing the head node image(s). "
         "Defaults to the ID of the official AWS account of the BCM team. "
         "Related parameter: --image-visibility .",
)
IMAGE_NAME_REGEX_AWS = r"^(?:bright[^-]+)-([^-]+(?:-dev)?)-([^-]+)-(hvm|[^-]+)-(\d+)$"


class CannotParseImageName(Exception):
    pass


class AWSImageSource(ImageSource):
    @classmethod
    def from_config(cls, config: ConfigurationView, ids: list[str] | None = None) -> AWSImageSource:
        ids_to_use = ids if ids is not None else config["ids"]
        ImageSource.print_cloud_agnostic_information(config, ids_to_use)
        return AWSImageSource(
            ids=ids_to_use,
            version=config["version"],
            arch=config["arch"],
            distro=config["distro"],
            revision=config["revision"],
            status=config["status"],
            advanced=True,
            image_visibility=config["image_visibility"],
            cloud_type=config["cloud_type"],
        )

    def _iter_from_source(self) -> typing.Iterator[CODImage]:
        allow_custom_images = False
        image_owners: list[str] = []
        image_ids: list[str] = []
        filters: list[FilterTypeDef] = []

        if self.uuids:
            # Find images by AMI ids. They might be non-Bright
            image_ids = self.uuids[:]
            allow_custom_images = True
        else:
            image_owners = [config["image_owner"]]

            filters = [
                {"Name": "name", "Values": ["brightheadnode-*"]},
            ]

            if config["image_visibility"] == "public":
                filters += [{"Name": "is-public", "Values": ["true"]}]
            elif config["image_visibility"] == "private":
                filters += [{"Name": "is-public", "Values": ["false"]}]
            elif config["image_visibility"] == "any":
                # not specifying a filter will result in both public and private be fetched
                pass

        ec2: EC2ServiceResource = create_aws_service_resource(service_name="ec2")
        log.info(f"AWS image owners: {[config['image_owner']]}, AMI ids: {self.uuids}")
        images = list(ec2.images.filter(Owners=image_owners, Filters=filters, ImageIds=image_ids))

        for image in images:
            try:
                cod_image = make_cod_image_from_aws(image, allow_custom_images=allow_custom_images)
            except CannotParseImageName as e:
                # This is parsing names of public images, someone could even upload some bogus name
                # to break our code. So we just ignore if we can't parse it
                # Other exception can blow up
                log.debug(e)
            else:
                yield cod_image


def make_cod_image_from_aws(amazon_image: Image, allow_custom_images: bool = False) -> CODImage:
    """
    Convert boto3's image object to COD image object

    :param amazon_image: boto3.resource image object
    :param allow_custom_images: allow non-Bright images
    :return: CODImage object for specified image
    """
    additional_params: dict[str, Any] = {}
    match = re.match(IMAGE_NAME_REGEX_AWS, amazon_image.name)
    if match:
        version, distribution, arch, revision = match.groups()

        # Previously, our images only supported the x86_64 CPU architecture and included the "-hvm-"
        # substring in their names for historical reasons. Our new images support various architectures.
        # To maintain backward compatibility with the naming scheme, we continue to use "hvm"
        # specifically for x86_64. For other architectures, we replace "hvm" with the specific
        # architecture name. This method ensures that legacy code will not recognize, and thus ignore,
        # image names for non-x86_64 architectures.
        if arch == "hvm":
            arch = "x86_64"

        additional_params = {
            "version": version,
            "distro": distribution,
            "revision": int(revision),
            "id": f"{distribution}-{version}",
            "arch": arch,
        }
    elif not allow_custom_images:
        raise CannotParseImageName(f"Cannot parse image name {amazon_image.name}")

    return CODImage(
        name=amazon_image.name,
        uuid=amazon_image.id,
        created_at=datetime.fromisoformat(amazon_image.creation_date.replace("Z", "+00:00")),
        image_visibility="public" if amazon_image.public else "private",
        type="headnode",
        cloud_type="aws",
        **additional_params,
    )
