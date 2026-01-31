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

import fnmatch
import logging

import clusterondemand.configuration
from clusterondemand.clusternameprefix import clusterprefix_ns, ensure_cod_prefix
from clusterondemand.utils import confirm, confirm_ns
from clusterondemandconfig import ConfigNamespace, config

from . import clientutils
from .configuration import gcpcommon_ns

log = logging.getLogger("cluster-on-demand")

config_ns = ConfigNamespace("gcp.cluster.stop")
config_ns.import_namespace(gcpcommon_ns)
config_ns.import_namespace(clusterprefix_ns)
config_ns.import_namespace(clusterondemand.configuration.clusterlist_ns)
config_ns.import_namespace(confirm_ns)
config_ns.add_repeating_positional_parameter(
    "filters",
    default=["*"],
    require_value=True,
    help="Cluster names or patterns to be stopped. Wildcards are supported (e.g: \\*)",
)


def run_command() -> None:
    cluster_name_patterns = [ensure_cod_prefix(name) for name in config["filters"]]
    cluster_name_regexes = [fnmatch.translate(pattern) for pattern in cluster_name_patterns]
    client = clientutils.GCPClient.from_config()

    full_cluster_list = client.list_all_clusters(project=config["project_id"])
    my_cluster_list = client.filter_cluster_list(cluster_list=full_cluster_list, regexlist=cluster_name_regexes)
    if not my_cluster_list:
        log.info("No clusters found")
        return

    if not confirm("This will stop cluster(s) '{}', continue?".format("', '".join(my_cluster_list))):
        return

    stop_list: list[clientutils.GCPResource] = []
    for cluster in my_cluster_list:
        log.info(f"Stopping cluster {cluster}")
        resources = client.get_resources_for_cluster(project=config["project_id"], cluster_name=cluster)
        gcpr_instance_list = [resource for resource in resources if resource.klass == "instances"]
        for gcpr_instance in gcpr_instance_list:
            instance = client.get_instance(project=gcpr_instance.project, instance_name=gcpr_instance.name,
                                           zone=gcpr_instance.zone)
            if instance.status == "TERMINATED":
                log.info(f" - Skipping {instance.name}, it is already stopped")
            else:
                log.info(f" - Stopping {instance.name}")
                stop_list.append(gcpr_instance)
    if stop_list:
        client.stop_instances(instances=stop_list)
    log.info("Done")
