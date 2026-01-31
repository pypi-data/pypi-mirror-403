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
from .configuration import awscommon_ns, wait_timeout_ns

log = logging.getLogger("cluster-on-demand")


def run_command() -> None:
    ClusterDelete().run()


config_ns = ConfigNamespace("aws.cluster.delete", "cluster delete parameters")
config_ns.import_namespace(awscommon_ns)
config_ns.import_namespace(clusterprefix_ns)
config_ns.import_namespace(confirm_ns)
config_ns.add_repeating_positional_parameter(
    "filters",
    require_value=True,
    help="Cluster names or patterns. Wildcards are supported (e.g: \\*)",
)
config_ns.import_namespace(wait_timeout_ns)


class ClusterDelete(ClusterCommandBase):
    def run(self) -> None:
        names = [ensure_cod_prefix(name) for name in config["filters"]]
        clusters = list(Cluster.find(names))

        if not clusters:
            log_no_clusters_found("delete")
            return

        for c in clusters:
            if c.efs_id:
                log.warning(
                    f"Cluster '{c.name}' is using a High-Availability EFS (FileSystemId={c.efs_id}). "
                    "This file system and all its data will be permanently deleted!"
                )

        if not confirm(f"This will destroy resources associated with clusters: "
                       f"{', '.join([f'{c.name!r}' for c in clusters])}. "
                       f"Would you like to continue?"):
            return

        multithread_run(lambda cluster: cluster.destroy(), clusters, config["max_threads"])
