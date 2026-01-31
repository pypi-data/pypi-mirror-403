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
import typing

from .awsconnection import create_aws_service_client

if typing.TYPE_CHECKING:
    from mypy_boto3_ec2.client import EC2Client
    from mypy_boto3_pricing.client import PricingClient


def list_volume_types(region: str, aws_key_id: str, aws_secret: str) -> set[str]:
    # Pricing API has 3 endpoints, so we can't dynamically populate region_name, instead eu-central-1 is hardcoded
    # https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/using-the-aws-price-list-bulk-api.html
    client: PricingClient = create_aws_service_client(
        service_name='pricing',
        region_name='eu-central-1'
    )
    response = client.get_products(
        ServiceCode='AmazonEC2',
        Filters=[
            {
                'Type': 'TERM_MATCH',
                'Field': 'productFamily',
                'Value': 'Storage'
            },
            {
                "Type": "TERM_MATCH",
                "Field": "regionCode",
                "Value": region,
            }
        ],
    )
    volume_types = {
        json.loads(price_item)['product']['attributes']['volumeApiName']
        for price_item in response['PriceList']
        if 'volumeApiName' in json.loads(price_item)['product']['attributes']
    }

    return volume_types


def list_availability_zones(region: str, aws_key_id: str, aws_secret: str) -> list[str]:
    """Return a list of availabilityzones in an AWS subscription."""
    ec2_client: EC2Client = create_aws_service_client(
        service_name="ec2",
        region_name=region,
    )
    azs = ec2_client.describe_availability_zones()
    az_names = [az["ZoneName"] for az in azs["AvailabilityZones"]]
    return az_names
