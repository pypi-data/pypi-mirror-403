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

import clusterondemand.configuration
from clusterondemandconfig import DEFAULT_HELP_SECTION, ConfigNamespace, may_not_equal_none
from clusterondemandconfig.configuration.configuration_view import ConfigurationView
from clusterondemandconfig.configuration_validation import must_be_nonnegative, requires_other_parameters_to_be_set
from clusterondemandconfig.exceptions import ConfigLoadError
from clusterondemandconfig.parameter import Parameter

ACCESS_KEY_ID_REGEX = r"^[0-9A-Z]{16,128}$"


def validate_aws_credential_format(parameter: Parameter, configuration: ConfigurationView) -> None:
    item = configuration.get_item_for_key(parameter.name)
    if item.value:
        if parameter.name == "aws_access_key_id":
            if not re.match(ACCESS_KEY_ID_REGEX, item.value):
                raise ConfigLoadError("Malformed AWS access key id")
        elif parameter.name == "aws_secret_key":
            if len(item.value) != 40:
                raise ConfigLoadError("Malformed AWS secret key")
        else:
            raise Exception(f"Internal error, can't validate {parameter.name}")


awscredentials_ns = ConfigNamespace("aws.credentials", help_section="AWS credentials")
awscredentials_ns.add_parameter(
    "aws_access_key_id",
    help="AWS Access Key ID (generate it in AWS dashboard).",
    help_varname="ID",
    env="AWS_ACCESS_KEY_ID",
    validation=[validate_aws_credential_format, requires_other_parameters_to_be_set(["aws_secret_key"])]
)
awscredentials_ns.add_parameter(
    "aws_secret_key",
    help="AWS Secret Key (generate it in AWS dashboard).",
    help_varname="KEY",
    env="AWS_SECRET_ACCESS_KEY",
    secret=True,
    validation=[validate_aws_credential_format, requires_other_parameters_to_be_set(["aws_access_key_id"])]
)
awscredentials_ns.add_parameter(
    "aws_session_token",
    help="AWS session token, necessary authenticating with AWS Security Token Service (STS).",
    help_varname="TOKEN",
    env="AWS_SESSION_TOKEN",
    secret=True,
    validation=[
        requires_other_parameters_to_be_set(["aws_access_key_id", "aws_secret_key"])]
)
awscredentials_ns.add_parameter(
    "aws_profile",
    help=(
        "Name of the profile configured for AWS CLI. "
        "By default found in ~/.aws/credentials. "
        "Overrides aws_access_key_id, aws_secret_key and aws_session_token, even if they are also supplied."
    ),
    help_varname="PROFILE",
    env="AWS_PROFILE",
    secret=False,
)
awscredentials_ns.add_parameter(
    "aws_region",
    default="eu-central-1",
    help="Name of the AWS region to use for the operation.",
    env="AWS_REGION",
    validation=may_not_equal_none
)


awscommon_ns = ConfigNamespace("aws.common")
awscommon_ns.import_namespace(clusterondemand.configuration.common_ns)
awscommon_ns.remove_imported_parameter("version")
awscommon_ns.import_namespace(awscredentials_ns)
awscommon_ns.add_parameter(
    "fixed_cluster_prefix",
    advanced=True,
    default="on-demand ",  # space is intentional
    help="This prefix is used for creating and finding new cluster in AWS.",
    help_section=DEFAULT_HELP_SECTION
)
wait_timeout_ns = ConfigNamespace("aws")
wait_timeout_ns.add_parameter(
    "terminate_timeout",
    advanced=True,
    default=600,
    help="Timeout in seconds for instances to be terminated.",
    validation=must_be_nonnegative,
)
