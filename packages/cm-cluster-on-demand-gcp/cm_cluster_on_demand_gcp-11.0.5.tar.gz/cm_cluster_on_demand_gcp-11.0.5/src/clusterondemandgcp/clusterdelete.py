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
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable, TypeVar

from google.cloud import asset_v1, compute_v1, filestore_v1, iam_admin_v1, resourcemanager_v3

from clusterondemand.clusternameprefix import clusterprefix_ns, ensure_cod_prefix
from clusterondemand.utils import confirm, confirm_ns, log_no_clusters_found
from clusterondemandconfig import ConfigNamespace, config

from . import clientutils
from .clientutils import (
    BCM_LABEL_CLUSTER,
    BCM_TAG_CLUSTER,
    build_filestore_idurl,
    build_sa_idurl,
    compute_resource_full_name_with_id,
    compute_uri_to_relative_name,
    try_parse_service_account_resource_name
)
from .configuration import gcpcommon_ns

T = TypeVar('T')
U = TypeVar('U')

BCM_MAX_LIST_INSTANCES = 8

log = logging.getLogger("cluster-on-demand")


config_ns = ConfigNamespace("gcp.cluster.delete", help_section="cluster delete parameters")
config_ns.import_namespace(gcpcommon_ns)
config_ns.import_namespace(clusterprefix_ns)
config_ns.import_namespace(confirm_ns)

config_ns.add_switch_parameter(
    "dry_run",
    help="Do not actually delete the resources."
)
config_ns.add_repeating_positional_parameter(
    "filters",
    require_value=True,
    help="Cluster names or patterns. Wildcards are supported (e.g: \\*)",
)


def flatten(resources_map: dict[str, list[T]]) -> list[T]:
    return [resource for resources in resources_map.values() for resource in resources]


def multidict(items: Iterable[tuple[T, U]]) -> dict[T, list[U]]:
    result: dict[T, list[U]] = {}
    for key, value in items:
        result.setdefault(key, []).append(value)
    return result


def filestore_network_uri(
    filestore: filestore_v1.Instance, network_config: filestore_v1.NetworkConfig
) -> str:
    m = re.fullmatch(r"projects/([^/]+)/locations/([^/]+)/instances/([^/]+)", filestore.name)
    assert m
    project = m.group(1)
    network = network_config.network
    return f"https://www.googleapis.com/compute/v1/projects/{project}/global/networks/{network}"


def run_command() -> None:
    project = config["project_id"]

    client = clientutils.GCPClient.from_config()
    with ThreadPoolExecutor() as executor:
        (
            # Note, the project name refers to the resource name (e.g. projects/147368050893) while
            # the project ID generally refers to the readable name (e.g. nv-bcmcodgcp-20240216).
            project_name,  # E.g. projects/147368050893
            all_bcm_tag_keys_and_values,
            all_tag_binding_assets,
            all_addresses,
            all_disks,
            all_filestores,
            all_firewalls,
            all_forwarding_rules,
            all_instances,
            all_routers,
            all_networks,
            all_service_accounts,
            all_snapshots,
            all_subnetworks,
            all_target_instances,
        ) = typing.cast(
            tuple[
                str,
                list[tuple[resourcemanager_v3.TagKey, list[resourcemanager_v3.TagValue]]],
                list[asset_v1.Asset],
                list[compute_v1.Address],
                list[compute_v1.Disk],
                list[filestore_v1.Instance],
                list[compute_v1.Firewall],
                list[compute_v1.ForwardingRule],
                list[compute_v1.Instance],
                list[compute_v1.Router],
                list[compute_v1.Network],
                list[compute_v1.ServiceAccount],
                list[compute_v1.Snapshot],
                list[compute_v1.Subnetwork],
                list[compute_v1.TargetInstance],
            ],
            tuple(
                future.result()
                for future in [
                    executor.submit(request)
                    for request in (
                        lambda: client.projects_client.get_project(name=f"projects/{project}").name,
                        lambda: client.list_bcm_tag_keys_and_values(project=project),
                        lambda: client.list_tag_binding_assets(project=project),
                        lambda: client.list_cluster_addresses(project=project),
                        lambda: client.list_disks(project=project),
                        lambda: client.list_filestores(project=project),
                        lambda: client.list_firewalls(project=project),
                        lambda: client.list_forwarding_rules(project=project),
                        lambda: client.list_instances(project=project),
                        lambda: client.list_routers(project=project),
                        lambda: client.list_networks(project=project),
                        lambda: client.list_service_accounts(project=project),
                        lambda: client.list_snapshots(project=project),
                        lambda: client.list_subnetworks(project=project),
                        lambda: client.list_target_instances(project=project),
                    )
                ]
            ),
        )

    bcm_cluster_tag_key, all_cluster_tag_values = next(
        filter(lambda t: t[0].short_name == BCM_TAG_CLUSTER, all_bcm_tag_keys_and_values), (None, [])
    )
    cluster_name_patterns = [ensure_cod_prefix(name) for name in config["filters"]]
    cluster_name_regexes = [fnmatch.translate(pattern) for pattern in cluster_name_patterns]
    cluster_tag_values = [
        tag_value
        for tag_value in all_cluster_tag_values
        if any(re.match(regex, tag_value.short_name) for regex in cluster_name_regexes)
    ]

    if not bcm_cluster_tag_key or len(cluster_tag_values) == 0 and len(all_cluster_tag_values) > 0:
        log_no_clusters_found("delete")
        return

    cluster_names = {tag_value.short_name for tag_value in cluster_tag_values}

    bcm_addresses = {}
    bcm_disks = {}
    bcm_filestores = {}
    bcm_firewalls = {}
    bcm_forwarding_rules = {}
    bcm_instances = {}
    bcm_routers = {}
    bcm_networks = {}
    bcm_service_accounts = {}
    bcm_snapshots = {}
    bcm_subnetworks = {}
    bcm_target_instances = {}

    if len(cluster_tag_values) > 0:
        # Collect all matching BCM resources. First, always query tag bindings reported by the Asset
        # API which only provides eventual consistency on current data. Although almost all asset
        # updates are available in minutes, it's possible that some data updates may be missed. The
        # GCP support team has indicated that eventual consistency may take up to 24 hours in the
        # absolute worst case. Resource updates older than this may be trusted as consistent.
        asset_freshness_threshold = datetime.now(timezone.utc) - timedelta(hours=24)

        # Use the resource creation timestamp as a proxy for tag binding freshness. This works since
        # tags are only applied immediately after resource creation and never updated/removed.
        # For newly created resources where tag asset consistency is not guaranteed, fall back by
        # listing resource tag bindings using the Resource Manager API (taking care to avoid these
        # additional requests where possible).
        def compute_resource_is_recent(resource: Any) -> bool:
            assert resource.creation_timestamp
            return datetime.fromisoformat(resource.creation_timestamp) > asset_freshness_threshold

        def filestore_is_recent(filestore: filestore_v1.Instance) -> bool:
            create_time = datetime.fromisoformat(filestore.create_time.rfc3339())
            return create_time > asset_freshness_threshold

        # Map of BCM cluster tag value names to cluster names.
        # E.g. tagValues/281482196710147 => my-cluster
        tag_value_to_cluster = {tag_value.name: tag_value.short_name for tag_value in all_cluster_tag_values}
        # Map of BCM cluster tag bindings: full resource name to cluster name.
        # E.g. //compute.googleapis.com/projects/my-project/global/networks/7361627433634917682 => my-cluster
        tagged_resource_cluster = {
            tag_binding.resource.data["parent"].replace(
                project_name, f"projects/{project}", 1
            ): cluster_name
            for tag_binding in all_tag_binding_assets
            if (cluster_name := tag_value_to_cluster.get(tag_binding.resource.data["tagValue"]))
        }

        def get_cluster_name(tag_bindings: Iterable[resourcemanager_v3.TagBinding]) -> str | None:
            if names := [
                cluster_name
                for tag_binding in tag_bindings
                if (cluster_name := tag_value_to_cluster.get(tag_binding.tag_value))
            ]:
                # There can only be a single binding per tag key.
                assert len(names) == 1
                return names[0]
            return None

        def cluster_network(network: compute_v1.Network) -> tuple[str, compute_v1.Network] | None:
            cluster_name = tagged_resource_cluster.get(compute_resource_full_name_with_id(network))
            if not cluster_name and compute_resource_is_recent(network):
                cluster_name = get_cluster_name(
                    client.get_network_tags(project=project, network_id=network.id)
                )
            return (cluster_name, network) if cluster_name in cluster_names else None

        with ThreadPoolExecutor(max_workers=20) as executor:
            bcm_networks = multidict(filter(None, executor.map(cluster_network, all_networks)))
        bcm_network_uris = {
            network.self_link: cluster_name
            for cluster_name, networks in bcm_networks.items()
            for network in networks
        }
        # FIXME(kal): Include non-BCM networks (e.g. clusters created in shared VPCs).
        matching_cluster_network_uris = bcm_network_uris

        # Address resources do not support tags.
        bcm_addresses = multidict(
            [
                (cluster_name, address)
                for cluster_name in cluster_names
                for address in all_addresses
                if address.labels[BCM_LABEL_CLUSTER] == cluster_name
            ]
        )

        def cluster_instance(instance: compute_v1.Instance) -> tuple[str, compute_v1.Instance] | None:
            cluster_name = tagged_resource_cluster.get(compute_resource_full_name_with_id(instance))
            if not cluster_name and compute_resource_is_recent(instance):
                # Only request tag bindings for instances in matching cluster networks.
                if any(
                    network_interface.network in matching_cluster_network_uris
                    for network_interface in instance.network_interfaces
                ):
                    cluster_name = get_cluster_name(
                        client.get_instance_tags(
                            project=project,
                            zone=instance.zone.split("/")[-1],
                            instance_id=instance.id,
                        )
                    )
            return (cluster_name, instance) if cluster_name in cluster_names else None

        with ThreadPoolExecutor(max_workers=20) as executor:
            bcm_instances = multidict(filter(None, executor.map(cluster_instance, all_instances)))

        def cluster_disk(disk: compute_v1.Disk) -> tuple[str, compute_v1.Disk] | None:
            cluster_name = tagged_resource_cluster.get(compute_resource_full_name_with_id(disk))
            if not cluster_name and compute_resource_is_recent(disk):
                # Only request tag bindings for disks that are not attached or attached to cluster
                # instances.
                if (
                    not disk.users
                    or any(
                        instance.self_link in disk.users
                        for instances in bcm_instances.values()
                        for instance in instances
                    )
                ):
                    cluster_name = get_cluster_name(
                        client.get_disk_tags(
                            project=project, zone=disk.zone.split("/")[-1], _id=disk.id
                        )
                    )
            return (cluster_name, disk) if cluster_name in cluster_names else None

        with ThreadPoolExecutor(max_workers=20) as executor:
            bcm_disks = multidict(filter(None, executor.map(cluster_disk, all_disks)))

        def cluster_filestore(filestore: filestore_v1.Instance) -> tuple[str, filestore_v1.Instance] | None:
            cluster_name = tagged_resource_cluster.get(build_filestore_idurl(name=filestore.name))
            if not cluster_name and filestore_is_recent(filestore):
                # Only request tag bindings for filestores in matching cluster networks.
                if any(
                    filestore_network_uri(filestore, network) in matching_cluster_network_uris
                    for network in filestore.networks
                ):
                    cluster_name = get_cluster_name(client.get_filestore_tags(name=filestore.name))
            return (cluster_name, filestore) if cluster_name in cluster_names else None

        with ThreadPoolExecutor(max_workers=20) as executor:
            bcm_filestores = multidict(filter(None, executor.map(cluster_filestore, all_filestores)))

        def cluster_firewall(firewall: compute_v1.Firewall) -> tuple[str, compute_v1.Firewall] | None:
            cluster_name = tagged_resource_cluster.get(compute_resource_full_name_with_id(firewall))
            if not cluster_name and compute_resource_is_recent(firewall):
                # Only request tag bindings for firewalls in matching cluster networks.
                if firewall.network in matching_cluster_network_uris:
                    cluster_name = get_cluster_name(
                        client.get_firewall_tags(project=project, firewall_id=firewall.id)
                    )
            return (cluster_name, firewall) if cluster_name in cluster_names else None

        with ThreadPoolExecutor(max_workers=20) as executor:
            bcm_firewalls = multidict(filter(None, executor.map(cluster_firewall, all_firewalls)))

        def cluster_forwarding_rule(
            forwarding_rule: compute_v1.ForwardingRule
        ) -> tuple[str, compute_v1.ForwardingRule] | None:
            cluster_name = tagged_resource_cluster.get(compute_resource_full_name_with_id(forwarding_rule))
            if not cluster_name and compute_resource_is_recent(forwarding_rule):
                # Only request tag bindings of forwarding rules with a matching cluster label.
                if forwarding_rule.labels[BCM_LABEL_CLUSTER] in cluster_names:
                    cluster_name = get_cluster_name(
                        client.get_forwarding_rule_tags(
                            project=project,
                            region=forwarding_rule.region.split("/")[-1],
                            forwarding_rule_id=forwarding_rule.id,
                        )
                    )
            return (cluster_name, forwarding_rule) if cluster_name in cluster_names else None

        with ThreadPoolExecutor(max_workers=20) as executor:
            bcm_forwarding_rules = multidict(filter(None, executor.map(cluster_forwarding_rule, all_forwarding_rules)))

        def cluster_router(router: compute_v1.Router) -> tuple[str, compute_v1.Router] | None:
            cluster_name = tagged_resource_cluster.get(compute_resource_full_name_with_id(router))
            if not cluster_name and compute_resource_is_recent(router):
                # Only request tag bindings for routers in matching cluster networks.
                if router.network in matching_cluster_network_uris:
                    cluster_name = get_cluster_name(
                        client.get_router_tags(
                            project=project, region=router.region.split("/")[-1], _id=router.id
                        )
                    )
            return (cluster_name, router) if cluster_name in cluster_names else None

        with ThreadPoolExecutor(max_workers=20) as executor:
            bcm_routers = multidict(filter(None, executor.map(cluster_router, all_routers)))

        def cluster_snapshot(snapshot: compute_v1.Snapshot) -> tuple[str, compute_v1.Snapshot] | None:
            cluster_name = tagged_resource_cluster.get(compute_resource_full_name_with_id(snapshot))
            if not cluster_name and compute_resource_is_recent(snapshot):
                # Snapshots are only created manually during cloud HA setup.
                if not snapshot.auto_created:
                    cluster_name = get_cluster_name(
                        client.get_snapshot_tags(project=project, _id=snapshot.id)
                    )
            return (cluster_name, snapshot) if cluster_name in cluster_names else None

        with ThreadPoolExecutor(max_workers=20) as executor:
            bcm_snapshots = multidict(filter(None, executor.map(cluster_snapshot, all_snapshots)))

        def cluster_subnetwork(subnetwork: compute_v1.Subnetwork) -> tuple[str, compute_v1.Subnetwork] | None:
            cluster_name = tagged_resource_cluster.get(compute_resource_full_name_with_id(subnetwork))
            if not cluster_name:
                # Only request tag bindings for subnetworks in matching cluster networks.
                if subnetwork.network in matching_cluster_network_uris:
                    # Delete all subnetworks in BCM networks (regardless of how they are tagged).
                    # Deletion will fail if a subnetwork is still in use.
                    cluster_name = bcm_network_uris.get(subnetwork.network)
                    if not cluster_name and compute_resource_is_recent(subnetwork):
                        cluster_name = get_cluster_name(
                            client.get_subnetwork_tags(
                                project=project, region=subnetwork.region.split("/")[-1], subnetwork_id=subnetwork.id
                            )
                        )
            return (cluster_name, subnetwork) if cluster_name in cluster_names else None

        with ThreadPoolExecutor(max_workers=20) as executor:
            bcm_subnetworks = multidict(filter(None, executor.map(cluster_subnetwork, all_subnetworks)))

        def cluster_target_instance(
            target_instance: compute_v1.TargetInstance
        ) -> tuple[str, compute_v1.TargetInstance] | None:
            cluster_name = tagged_resource_cluster.get(compute_resource_full_name_with_id(target_instance))
            if not cluster_name and compute_resource_is_recent(target_instance):
                cluster_name = get_cluster_name(
                    client.get_target_instance_tags(
                        project=project, zone=target_instance.zone.split("/")[-1], _id=target_instance.id
                    )
                )
            return (cluster_name, target_instance) if cluster_name in cluster_names else None

        with ThreadPoolExecutor(max_workers=20) as executor:
            bcm_target_instances = multidict(filter(None, executor.map(cluster_target_instance, all_target_instances)))

        def cluster_service_account(
            service_account: iam_admin_v1.ServiceAccount
        ) -> tuple[str, iam_admin_v1.ServiceAccount] | None:
            cluster_name = tagged_resource_cluster.get(
                build_sa_idurl(project=service_account.project_id, sa_id=service_account.unique_id)
            )
            # Note, service accounts do not have a creation timestamp attribute.
            if not cluster_name:
                cluster_name = get_cluster_name(
                    client.get_service_account_tags(project=project, sa_id=service_account.unique_id)
                )
            return (cluster_name, service_account) if cluster_name in cluster_names else None

        with ThreadPoolExecutor(max_workers=20) as executor:
            bcm_service_accounts = multidict(filter(None, executor.map(cluster_service_account, all_service_accounts)))

        # Service account tag bindings must be deleted manually since service accounts may be undeleted
        # within 30 days.
        cluster_service_account_tag_binding_assets = [
            tag_binding
            for tag_binding in all_tag_binding_assets
            if try_parse_service_account_resource_name(tag_binding.resource.data["parent"])
            and (cluster_name := tag_value_to_cluster.get(tag_binding.resource.data["tagValue"]))
            and cluster_name in cluster_names
        ]

    log.info("The following cloud resources will be DELETED:")
    if delete_cluster_tag_key := len(cluster_tag_values) == len(all_cluster_tag_values):
        log.info(f"- Tag key: [{bcm_cluster_tag_key.namespaced_name}]")
    for tag_value in sorted(cluster_tag_values, key=lambda t: t.short_name):
        cluster_name = tag_value.short_name
        log.info(f"Cluster [{cluster_name}]:")
        log.info(f"- Tag value: [{tag_value.namespaced_name}]")
        for address in bcm_addresses.get(cluster_name, []):
            log.info(f"- Address: [{compute_uri_to_relative_name(address.self_link)}]")
        for disk in bcm_disks.get(cluster_name, []):
            log.info(f"- Disk: [{compute_uri_to_relative_name(disk.self_link)}]")
        for filestore in bcm_filestores.get(cluster_name, []):
            log.info(f"- Filestore instance: [{filestore.name}]")
        for firewall in bcm_firewalls.get(cluster_name, []):
            log.info(f"- Firewall: [{compute_uri_to_relative_name(firewall.self_link)}]")
        for forwarding_rule in bcm_forwarding_rules.get(cluster_name, []):
            log.info(f"- Forwarding rule: [{compute_uri_to_relative_name(forwarding_rule.self_link)}]")
        for instance in bcm_instances.get(cluster_name, []):
            log.info(f"- Instance: [{compute_uri_to_relative_name(instance.self_link)}]")
        for router in bcm_routers.get(cluster_name, []):
            log.info(f"- Router: [{compute_uri_to_relative_name(router.self_link)}]")
        for network in bcm_networks.get(cluster_name, []):
            log.info(f"- Network: [{compute_uri_to_relative_name(network.self_link)}]")
        for service_account in bcm_service_accounts.get(cluster_name, []):
            log.info(f"- Service account: [{service_account.name}]")
        for snapshot in bcm_snapshots.get(cluster_name, []):
            log.info(f"- Snapshot: [{compute_uri_to_relative_name(snapshot.self_link)}]")
        for subnetwork in bcm_subnetworks.get(cluster_name, []):
            log.info(f"- Subnetwork: [{compute_uri_to_relative_name(subnetwork.self_link)}]")
        for target_instance in bcm_target_instances.get(cluster_name, []):
            log.info(f"- Target instance: [{compute_uri_to_relative_name(target_instance.self_link)}]")

    matching_resource_count = (
        int(delete_cluster_tag_key)
        + len(cluster_tag_values)
        + sum(len(resources) for resources in bcm_addresses.values())
        + sum(len(resources) for resources in bcm_disks.values())
        + sum(len(resources) for resources in bcm_filestores.values())
        + sum(len(resources) for resources in bcm_firewalls.values())
        + sum(len(resources) for resources in bcm_forwarding_rules.values())
        + sum(len(resources) for resources in bcm_instances.values())
        + sum(len(resources) for resources in bcm_routers.values())
        + sum(len(resources) for resources in bcm_networks.values())
        + sum(len(resources) for resources in bcm_service_accounts.values())
        + sum(len(resources) for resources in bcm_snapshots.values())
        + sum(len(resources) for resources in bcm_subnetworks.values())
        + sum(len(resources) for resources in bcm_target_instances.values())
    )
    if not confirm(
        f"Proceed with DELETION of {len(cluster_names)} cluster(s) ({matching_resource_count} resource(s))"
    ):
        return

    client.delete_cluster_resources(
        project=project,
        addresses=flatten(bcm_addresses),
        disks=flatten(bcm_disks),
        filestores=flatten(bcm_filestores),
        firewalls=flatten(bcm_firewalls),
        forwarding_rules=flatten(bcm_forwarding_rules),
        instances=flatten(bcm_instances),
        networks=flatten(bcm_networks),
        routers=flatten(bcm_routers),
        service_accounts=flatten(bcm_service_accounts),
        snapshots=flatten(bcm_snapshots),
        subnetworks=flatten(bcm_subnetworks),
        target_instances=flatten(bcm_target_instances),
    )
    for tag_binding in cluster_service_account_tag_binding_assets:
        client.delete_tag_binding_asset(tag_binding)

    client.delete_tag_values(tag_values=cluster_tag_values)
    log.info("Done")
