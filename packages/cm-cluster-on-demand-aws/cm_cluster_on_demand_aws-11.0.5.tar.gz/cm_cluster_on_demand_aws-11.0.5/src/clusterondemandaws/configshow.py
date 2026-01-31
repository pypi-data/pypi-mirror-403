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

import clusterondemand.configshow
from clusterondemand.configuration import get_enforcing_config_files, get_system_config_files
from clusterondemandconfig import ConfigNamespace, config, load_configuration_for_parameters
from clusterondemandconfig.config_dump import human_readable_config_dump

COMMAND_HELP_TEXT = clusterondemand.configshow.COMMAND_HELP_TEXT

config_ns = ConfigNamespace("aws.config.show")
config_ns.import_namespace(clusterondemand.configuration.common_ns)


def run_command() -> None:
    from .cli import aws_commands

    config_to_dump = load_configuration_for_parameters(
        aws_commands.parameters(),
        system_config_files=get_system_config_files(),
        enforcing_config_files=get_enforcing_config_files()
    )
    print(human_readable_config_dump(config_to_dump, show_secrets=config["show_secrets"]))  # type: ignore[arg-type]
