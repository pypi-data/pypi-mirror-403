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

config_ns = ConfigNamespace("gcp.cluster.start")
config_ns.import_namespace(gcpcommon_ns)
config_ns.import_namespace(clusterprefix_ns)
config_ns.import_namespace(clusterondemand.configuration.clusterlist_ns)
config_ns.import_namespace(confirm_ns)
config_ns.add_repeating_positional_parameter(
    "filters",
    default=["*"],
    require_value=True,
    help="Cluster names or patterns to be started. Wildcards are supported (e.g: \\*)",
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

    if not confirm("This will start cluster(s) '{}', continue?".format("', '".join(my_cluster_list))):
        return

    head_nodes = client.list_head_nodes(config["project_id"])

    start_list: list[clientutils.GCPResource] = []
    for cluster in my_cluster_list:
        log.info(f"Starting cluster {cluster}")
        resources = client.get_resources_for_cluster(project=config["project_id"], cluster_name=cluster)
        for head_node in head_nodes:
            if clientutils.instance_in_cluster(resources=resources, instance=head_node):
                if head_node.status == "RUNNING":
                    log.info(f" - Skipping {head_node.name}, it is already running")
                else:
                    log.info(f" - Starting {head_node.name}")
                    gcpr_instance = clientutils.parse_url(url=head_node.self_link)
                    start_list.append(gcpr_instance)

    if start_list:
        client.start_instances(instances=start_list)
        for gcpr_instance in start_list:
            instance = client.get_instance(project=gcpr_instance.project, instance_name=gcpr_instance.name,
                                           zone=gcpr_instance.zone)
            instance_ip = clientutils.get_instance_ips(instance=instance).first_usable_ip()
            log.info(f" - Started {instance.name} IP address {instance_ip}")
    log.info("Done")
