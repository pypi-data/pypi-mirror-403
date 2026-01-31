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
import re
import typing
from concurrent.futures import ThreadPoolExecutor

from google.cloud import compute_v1, resourcemanager_v3

import clusterondemand.clustercreate
import clusterondemand.configuration
from clusterondemand.clusternameprefix import clusterprefix_ns, ensure_cod_prefix
from clusterondemand.codoutput.sortingutils import ClusterIPs, SortableData
from clusterondemandconfig import ConfigNamespace, config

from . import clientutils
from .clientutils import BCM_LABEL_CLUSTER, BCM_TAG_CLUSTER
from .configuration import gcpcommon_ns

log = logging.getLogger("cluster-on-demand")

ALL_COLUMNS = [
    ("cluster_name", "Cluster Name"),
    ("head_node_name", "Head node name"),
    ("network_name", "Network Name"),
    ("subnet_name", "Subnet Name"),
    ("cluster_ip", "Cluster IP"),
    ("created", "Cluster Created (Age)"),
    ("status", "State"),
    ("image_name", "Image Name"),
    ("image_age", "Image Age"),
]

DEFAULT_COLUMNS = [
    "cluster_name",
    "head_node_name",
    "network_name",
    "subnet_name",
    "cluster_ip",
    "created",
    "status",
    "image_name",
    "image_age",
]

assert all(col in [column[0] for column in ALL_COLUMNS] for col in DEFAULT_COLUMNS)

config_ns = ConfigNamespace("gcp.cluster.list", "list output parameters")
config_ns.import_namespace(gcpcommon_ns)
config_ns.import_namespace(clusterprefix_ns)
config_ns.import_namespace(clusterondemand.configuration.clusterlist_ns)
config_ns.add_enumeration_parameter(
    "sort",
    default=["created"],
    choices=[column[0] for column in ALL_COLUMNS],
    help="Sort results by one (or two) of the columns"
)
config_ns.add_enumeration_parameter(
    "columns",
    choices=[column[0] for column in ALL_COLUMNS],
    default=DEFAULT_COLUMNS,
    help="Provide space separated set of columns to be displayed"
)
config_ns.add_repeating_positional_parameter(
    "filters",
    default=["*"],
    require_value=True,
    help="Cluster names or patterns to be listed. Default: all clusters. Wildcards are supported (e.g: \\*)",
)

HEAD_A_SUFFIX = "-head-a"
HEAD_B_SUFFIX = "-head-b"


def get_image_properties(
    client: clientutils.GCPClient,
    project: str,
    head_node: compute_v1.Instance,
    all_disks: list[compute_v1.Disk],
    all_images: list[compute_v1.Image],
) -> tuple[str | None, str | None]:
    image_name = None
    image_age = None

    if disk := next(
        (disk for disk in all_disks if disk.self_link == head_node.disks[0].source), None
    ):
        if disk.source_image:
            image_name = disk.source_image.split("/")[-1]
            if image := next(
                (image for image in all_images if image.self_link == disk.source_image), None
            ):
                image_age = clusterondemand.utils.get_time_ago_from_iso(image.creation_timestamp)
    return image_name, image_age


def run_command() -> None:
    log.info("Listing clusters...")

    client = clientutils.GCPClient.from_config()
    project = config["project_id"]

    with ThreadPoolExecutor() as executor:
        all_cluster_tag_values, all_head_nodes, all_disks, all_images, all_forwarding_rules = (
            typing.cast(
                tuple[
                    list[resourcemanager_v3.TagValue],
                    list[compute_v1.Instance],
                    list[compute_v1.Disk],
                    list[compute_v1.Image],
                    list[compute_v1.ForwardingRule],
                ],
                tuple(
                    future.result()
                    for future in [
                        executor.submit(request)
                        for request in (
                            lambda: client.list_cluster_tagvalues(project_id=project),
                            lambda: client.list_head_nodes(project=project),
                            lambda: client.list_disks(project=project),
                            lambda: client.list_images(project=project),
                            lambda: client.list_cluster_forwarding_rules(project=project),
                        )
                    ]
                ),
            )
        )
    cluster_name_patterns = [ensure_cod_prefix(name) for name in config["filters"]]
    cluster_name_regexes = [fnmatch.translate(pattern) for pattern in cluster_name_patterns]
    cluster_tag_values = [
        tag_value
        for tag_value in all_cluster_tag_values
        if any(re.match(regex, tag_value.short_name) for regex in cluster_name_regexes)
    ]
    if not cluster_tag_values:
        log.info("No clusters found")
        return

    log.info(f"Found {len(cluster_tag_values)} cluster(s):")

    # Simulate BCM cluster label on instances created with obsoleted CODs.
    for instance in all_head_nodes:
        if not instance.labels[BCM_LABEL_CLUSTER]:
            for tag in client.get_instance_tags(
                project=project, zone=instance.zone.split("/")[-1], instance_id=instance.id
            ):
                if tag.namespaced_tag_key == f"{project}/{BCM_TAG_CLUSTER}" and not tag.inherited:
                    instance.labels[BCM_LABEL_CLUSTER] = tag.namespaced_tag_value.split("/")[-1]
                    break

    rows = []
    for cluster_tag_value in cluster_tag_values:
        cluster_name = cluster_tag_value.short_name

        head_nodes = [
            instance
            for instance in all_head_nodes
            if instance.labels[BCM_LABEL_CLUSTER] == cluster_name
        ]
        if not head_nodes:
            log.warning(f"Found cluster tag {cluster_name} but no head nodes, may need manual cleanup")

        primary_head_node = next(
            (hn for hn in head_nodes if hn.name.endswith(HEAD_A_SUFFIX)), None
        )
        secondary_head_node = next(
            (hn for hn in head_nodes if hn.name.endswith(HEAD_B_SUFFIX)), None
        )
        if not primary_head_node:
            log.warning(f"Could not find primary head node for cluster {cluster_name}")

        if len(head_nodes) > 2:
            log.warning(f"Found more than 2 head nodes for cluster {cluster_name}, "
                        f"this indicates a failed deployment and may need manual cleanup")

        cluster_network: clientutils.GCPResource | None = None
        cluster_subnet: clientutils.GCPResource | None = None
        cluster_head_nodes: str = "missing"
        head_node_disk_image_name: str | None = None
        head_node_image_age: str | None = None
        primary_ip: str | None = None
        secondary_ip: str | None = None
        shared_ip: str | None = None
        status: str | None = None
        cluster_creation_date = clusterondemand.utils.format_to_local_date_time(
            cluster_tag_value.create_time.rfc3339()
        )
        cluster_age = clusterondemand.utils.get_time_ago_from_iso(
            cluster_tag_value.create_time.rfc3339()
        )
        cluster_creation_date_age = f"{cluster_creation_date} ({cluster_age})"

        for head_node in head_nodes:
            if head_node.network_interfaces:
                cluster_network = clientutils.parse_url(head_node.network_interfaces[0].network)
                cluster_subnet = clientutils.parse_url(head_node.network_interfaces[0].subnetwork)
                break

        head_node_disk_image_name = None
        head_node_image_age = None
        if primary_head_node:
            head_node_disk_image_name, head_node_image_age = get_image_properties(
                client=client,
                project=project,
                head_node=primary_head_node,
                all_disks=all_disks,
                all_images=all_images,
            )
            primary_ip = str(clientutils.get_instance_ips(primary_head_node).first_usable_ip())
            cluster_head_nodes = primary_head_node.name
            status = primary_head_node.status

        # indicates HA cluster
        if secondary_head_node:
            cluster_head_nodes = "\n".join(
                [primary_head_node.name if primary_head_node else "missing",
                 secondary_head_node.name if secondary_head_node else "missing"]
            )
            secondary_ip = str(clientutils.get_instance_ips(secondary_head_node).first_usable_ip())
            if forwarding_rules := [
                fr for fr in all_forwarding_rules if fr.labels[BCM_LABEL_CLUSTER] == cluster_name
            ]:
                shared_ip = forwarding_rules[0].I_p_address
            status = "\n".join(
                [primary_head_node.status if primary_head_node else "",
                 secondary_head_node.status if secondary_head_node else ""]
            )

        row = [
            cluster_name,
            cluster_head_nodes,
            cluster_network.name if cluster_network else "",
            cluster_subnet.name if cluster_subnet else "",
            ClusterIPs(primary_ip=primary_ip, secondary_ip=secondary_ip, shared_ip=shared_ip),
            cluster_creation_date_age,
            status,
            head_node_disk_image_name,
            head_node_image_age,
        ]
        rows.append(row)

    cols_wanted = config["columns"]
    if not cols_wanted:
        cols_wanted = DEFAULT_COLUMNS

    table = SortableData(all_headers=ALL_COLUMNS, requested_headers=cols_wanted, rows=rows)
    table.sort(*config["sort"])

    print(table.output(output_format=config["output_format"]))
