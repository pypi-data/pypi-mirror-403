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

import re
import typing

from .awsconnection import create_aws_service_client
from .clientutils import list_availability_zones
from .instancetype import get_available_instance_types

if typing.TYPE_CHECKING:
    from mypy_boto3_ec2.client import EC2Client

ACCOUNT_ID_REGEX = r"^[0-9]{12}$"
ACCESS_KEY_ID_REGEX = r"^[0-9A-Z]{16,128}$"


class AWSParamValidator:

    @staticmethod
    def validate_availability_zone(availability_zone: str, region: str, aws_key_id: str, aws_secret: str) -> bool:
        return availability_zone in list_availability_zones(
            region, aws_key_id, aws_secret
        )

    @classmethod
    def validate_instance_type(cls, region: str, instance_type: str) -> bool:
        return instance_type in get_available_instance_types(region)

    @staticmethod
    def validate_access_key_id_format(access_key_id: str) -> bool:
        return isinstance(access_key_id, str) and bool(re.match(ACCESS_KEY_ID_REGEX, access_key_id))

    @staticmethod
    def validate_secret_key_format(secret_key: str) -> bool:
        return isinstance(secret_key, str) and len(secret_key) == 40

    @staticmethod
    def validate_ssh_key_pair(key_pair_name: str, region: str, aws_key_id: str, aws_secret: str) -> bool:
        ec2_client: EC2Client = create_aws_service_client(
            service_name="ec2",
            region_name=region,
        )
        try:
            ec2_client.describe_key_pairs(KeyNames=[key_pair_name])
        except Exception:
            return False
        return True

    @staticmethod
    def get_instance_type_availability_zones(instance_type: str, region: str) -> list[str]:
        """Return a list of availability zones where the instance type is available."""
        ec2_client: EC2Client = create_aws_service_client(
            service_name="ec2",
            region_name=region,
        )
        response = ec2_client.describe_instance_type_offerings(
            LocationType="availability-zone",
            Filters=[{"Name": "instance-type", "Values": [instance_type]}],
        )
        return [offering["Location"] for offering in response.get("InstanceTypeOfferings", [])]

    @classmethod
    def get_instance_type_az_availability(
        cls, instance_type: str, availability_zone: str, region: str
    ) -> tuple[bool, list[str]]:
        """Check if an instance type is available in a specific availability zone.

        Returns a tuple of (is_available, available_zones) where available_zones is the list
        of zones where the instance type is available (useful for error messages).
        """
        available_zones = cls.get_instance_type_availability_zones(instance_type, region)
        return (availability_zone in available_zones, available_zones)
