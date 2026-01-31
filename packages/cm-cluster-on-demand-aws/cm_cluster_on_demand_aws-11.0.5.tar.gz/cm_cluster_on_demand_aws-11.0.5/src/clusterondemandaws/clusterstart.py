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

from clusterondemand.clusternameprefix import clusterprefix_ns, ensure_cod_prefix
from clusterondemand.utils import confirm, confirm_ns, log_no_clusters_found, multithread_run
from clusterondemandaws.base import ClusterCommandBase
from clusterondemandconfig import ConfigNamespace, config

from .cluster import Cluster
from .configuration import awscommon_ns

log = logging.getLogger("cluster-on-demand")


def run_command() -> None:
    ClusterStart().run()


config_ns = ConfigNamespace("aws.cluster.start")
config_ns.import_namespace(awscommon_ns)
config_ns.import_namespace(clusterprefix_ns)
config_ns.import_namespace(confirm_ns)
config_ns.add_repeating_positional_parameter(
    "filters",
    require_value=True,
    help="Cluster names or patterns. Wildcards are supported (e.g: \\*)",
)


class ClusterStart(ClusterCommandBase):
    def run(self) -> None:
        names = [ensure_cod_prefix(name) for name in config["filters"]]
        clusters = list(Cluster.find(names))

        if not clusters:
            log_no_clusters_found("start")
            return

        if not confirm(f"This will start clusters {' '.join([c.name for c in clusters])} continue?"):
            return

        log.info(f"Starting head nodes for clusters {' '.join(c.name for c in clusters)}.")
        multithread_run(lambda cluster: cluster.start(), clusters, config["max_threads"])
