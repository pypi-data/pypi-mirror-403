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
from functools import cache
from typing import Any

from boto3.session import Session
from botocore.exceptions import ClientError, EndpointConnectionError

from clusterondemand.exceptions import CODException
from clusterondemandconfig import config

log = logging.getLogger("cluster-on-demand")


@cache
def _establish_connection_to_aws() -> Session:
    log.debug("Establish session with AWS region '%s'" % config["aws_region"])
    if config["aws_profile"]:
        log.debug(
            "Using AWS profile name '%s', ignoring other credentials" % config["aws_profile"]
        )
        return Session(
            profile_name=config["aws_profile"],
            region_name=config["aws_region"],
        )

    return Session(
        config["aws_access_key_id"],
        config["aws_secret_key"],
        config["aws_session_token"],
        region_name=config["aws_region"],
    )


@cache
def create_aws_service_resource(
        service_name: str,
        api_version: str = "2016-11-15",
        **kwargs: Any
) -> Any:
    """Create an AWS service resource.

    Note: Returns Any due to boto3's dynamic service type system with a lot of overloads.
    Callers should annotate the return type at the call site when needed.
    """
    # TODO: api_version is set to 2016-11-15, for backwards compatibility.
    # Need to investigate if we need to hardcode it, or if we can use the latest one.
    session = _establish_connection_to_aws()
    _validate_credentials_and_region(session=session)

    return session.resource(  # type: ignore[call-overload]
        **kwargs, service_name=service_name, api_version=api_version
    )


@cache
def create_aws_service_client(
        service_name: str,
        **kwargs: Any
) -> Any:
    """Create an AWS service client.

    Note: Returns Any due to boto3's dynamic service type system with a lot of overloads.
    Callers should annotate the return type at the call site when needed.
    """
    session = _establish_connection_to_aws()
    _validate_credentials_and_region(session=session)

    return session.client(**kwargs, service_name=service_name)  # type: ignore[call-overload]


def _validate_credentials_and_region(session: Session) -> None:
    # We make a lightweight API call to validate the credentials.
    # Since region is mandatory for various service clients, we validate it in the same functions
    ec2_client = session.client(
        service_name="ec2",
    )
    try:
        ec2_client.describe_regions()
    except ClientError as e:
        if e.response["Error"]["Code"] == "AuthFailure":
            raise CODException("The provided AWS credentials are invalid.")
        raise CODException(f"Unable to connect to AWS, check your credentials or region configuration. {e}")
    except EndpointConnectionError:
        raise CODException(
            f"Could not connect to the endpoint {ec2_client._endpoint.host}. "  # type: ignore[attr-defined]
            "Please check the configured AWS region name"
        )
