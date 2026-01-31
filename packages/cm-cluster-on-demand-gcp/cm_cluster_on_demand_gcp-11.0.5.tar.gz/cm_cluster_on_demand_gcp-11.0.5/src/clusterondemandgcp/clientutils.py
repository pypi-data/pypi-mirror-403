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

import contextlib
import ipaddress
import logging
import re
import time
import urllib.parse
from collections.abc import Callable
from concurrent.futures import Executor, ThreadPoolExecutor
from dataclasses import dataclass, field
from functools import cache, cached_property, wraps
from typing import Any, Generator, Iterable, List, Optional, TypeVar, Union, cast  # noqa: F401

import google.auth
import tenacity
from google.api_core.client_options import ClientOptions
from google.api_core.exceptions import (
    Aborted,
    AlreadyExists,
    FailedPrecondition,
    InvalidArgument,
    NotFound,
    PermissionDenied,
    PreconditionFailed
)
from google.api_core.extended_operation import ExtendedOperation
from google.api_core.operation import Operation
from google.auth.exceptions import DefaultCredentialsError, RefreshError
from google.cloud import storage  # type: ignore[attr-defined]
from google.cloud import asset_v1, compute_v1, filestore_v1, iam_admin_v1, resourcemanager_v3
from google.cloud.compute_v1.services.instances.pagers import AggregatedListPager
from google.cloud.iam_admin_v1 import ServiceAccount
from google.cloud.resourcemanager_v3.services.tag_bindings.pagers import ListEffectiveTagsPager
from google.iam.v1 import iam_policy_pb2, options_pb2, policy_pb2  # type: ignore[import-untyped]

import clusterondemand.utils as utils
from clusterondemand.exceptions import CODException
from clusterondemand.inbound_traffic_rule import InboundTrafficRule
from clusterondemandconfig import config

T = TypeVar('T')
U = TypeVar('U')

GCP_COMPUTE_SERVICE = "compute.googleapis.com"
GCP_FILE_SERVICE = "file.googleapis.com"

__all__ = ['Callable']
log = logging.getLogger("cluster-on-demand")

# Label keys must start with a lowercase character, can only contain lowercase letters, numeric
# characters, underscores and dashes. The key can be at most 63 characters long. International
# characters are allowed.
BCM_LABEL_CLUSTER = "bcm-cluster"
BCM_LABEL_HEAD_NODE = "bcm-head-node"
BCM_INTERNAL_ADDRESS_SUFFIX = "-int"
BCM_EXTERNAL_ADDRESS_SUFFIX = "-ext"
BCM_GATEWAY_SUFFIX = "-bcm"
BCM_NETWORKTAG_HEADNODE = "bcm-head-node"
BCM_NETWORK_SUFFIX = "-bcm"
BCM_SUBNET_SUFFIX = "-bcm"
BCM_ROUTER_SUFFIX = "-bcm"
BCM_TAG_CLUSTER = "BCM_Cluster"
BCM_TAG_RETRIES = 300
BCM_TAG_RETRYTIME = 1
BCM_HEAD_SA_DISPLAY_NAME = "BCM head node service account"
BCM_NODE_SA_DISPLAY_NAME = "BCM node service account"

BCM_TAG_LIST = [BCM_TAG_CLUSTER]


def strip_prefix(s: str, prefix: str) -> str | None:
    if s.startswith(prefix):
        return s[len(prefix):]
    return None


def self_link_with_id(resource: Any) -> str:
    """
    Constructs the server-defined URL of a compute resource with the resource id.

    This function mimics the `self_link_with_id` field provided by some compute resource types in
    the V1 API, which is not always available.
    """
    assert resource.id
    assert resource.self_link
    return f"{resource.self_link[:resource.self_link.rindex('/')]}/{resource.id}"


# https://google.aip.dev/122
def compute_uri_to_relative_name(uri: str) -> str:
    if relative := strip_prefix(uri, "https://www.googleapis.com/compute/v1/"):
        return relative
    else:
        raise ValueError("invalid compute URI")


# https://google.aip.dev/122
def compute_uri_to_full_name(uri: str) -> str:
    return f"//{GCP_COMPUTE_SERVICE}/{compute_uri_to_relative_name(uri)}"


# https://cloud.google.com/iam/docs/full-resource-names
def compute_resource_full_name_with_id(resource: Any) -> str:
    return compute_uri_to_full_name(self_link_with_id(resource))


_GCP_SERVICE_ACCOUNT_REGEX = re.compile(
    r"//iam\.googleapis\.com/projects/([^/]+)/serviceAccounts/([^/]+)"
)


def try_parse_service_account_resource_name(resource_name: str) -> tuple[str, str] | None:
    if m := _GCP_SERVICE_ACCOUNT_REGEX.fullmatch(resource_name):
        return m.group(1), m.group(2)
    return None


class InstanceIpAddresses:
    """
    Class for representing different types of IP addresses for an instance.

    Example:
        >>> ip_type = InstanceIpAddresses(InstanceIpAddresses.from_list(["203.0.113.1"]))
        >>> ip_type.internal_ips()
        [IPv4Address('203.0.113.1')]
    """

    def __init__(self,
                 addresses: Union[List[Union[ipaddress.IPv4Address, ipaddress.IPv6Address]], None]):
        self.addresses = addresses

    @classmethod
    def ipv4_network_to_wildcard(self, network: str) -> str:
        """
            Convert an IP network address with CIDR notation to a wildcard format.

            This function converts a given IP network address in CIDR notation (e.g., '10.147.0.0/17')
            to a format where network segments are represented with wildcard characters '*'.

            Args:
                network (str): The IP network address in CIDR notation, e.g., '10.147.0.0/17'.

            Returns:
                str: The IP network address in wildcard format. For example, '10.147.*.*' for a /17 network.
        """
        if not ipaddress.IPv4Network(network, strict=False):
            raise ValueError(f"Invalid IP network address: {network!r}")

        parsed_network = ipaddress.IPv4Network(network, strict=False)
        network_address = parsed_network.network_address

        prefix_len = parsed_network.prefixlen

        wildcard_pattern = []

        bits_per_octet = 8

        for i in range(4):
            if prefix_len >= bits_per_octet:
                wildcard_pattern.append(str(network_address.packed[i]))
                prefix_len -= bits_per_octet
            else:
                wildcard_pattern.append('*')
                prefix_len = 0
        return '.'.join(wildcard_pattern)

    def first_usable_ip(self) -> Union[ipaddress.IPv4Address, ipaddress.IPv6Address]:
        """
        Retrieve the first usable IP address from the available instance IP addresses.
        If an instance has a public IP address, it is returned; otherwise, the first
        private IP address is returned.

        Returns:
            Union[ipaddress.IPv4Address, ipaddress.IPv6Address]: The first usable IP address.
        """
        return self.external_ips()[0] if self.external_ips() else self.internal_ips()[0]

    def external_ips(self) -> List[Union[ipaddress.IPv4Address, ipaddress.IPv6Address]]:
        """
        Retrieve a list of external (public) IP addresses from the instance's addresses.

        This method filters the instance's IP addresses to return only those that are
        considered external (i.e., not private). If the `addresses` attribute is `None`,
        it returns an empty list.

        Returns:
            List[Union[ipaddress.IPv4Address, ipaddress.IPv6Address]]: A list of IP addresses
            that are external (public). Each address is an instance of `IPv4Address` or
            `IPv6Address`.

        Example:
            >>> ip_addresses = InstanceIpAddresses([ipaddress.IPv4Address('192.168.1.1'),
            ...                                  ipaddress.IPv4Address('8.8.8.8')])
            >>> ip_addresses.external_ips()
            [IPv4Address('8.8.8.8')]
        """
        if self.addresses is None:
            return []
        return [address for address in self.addresses if not address.is_private]

    def internal_ips(self) -> List[Union[ipaddress.IPv4Address, ipaddress.IPv6Address]]:
        """
        Retrieve a list of internal (private) IP addresses from the instance's addresses.

        This method filters the instance's IP addresses to return only those that are
        considered private (i.e., private). If the `addresses` attribute is `None`,
        it returns an empty list.

        Returns:
            List[Union[ipaddress.IPv4Address, ipaddress.IPv6Address]]: A list of IP addresses
            that are external (public). Each address is an instance of `IPv4Address` or
            `IPv6Address`.

        Example:
            >>> ip_addresses = InstanceIpAddresses([ipaddress.IPv4Address('192.168.1.1'),
            ...                                  ipaddress.IPv4Address('8.8.8.8')])
            >>> ip_addresses.internal_ips()
            [IPv4Address('192.168.1.1')]
        """
        if self.addresses is None:
            return []
        return [address for address in self.addresses if address.is_private]

    @classmethod
    def from_str(cls, ip_str: str) -> Union[ipaddress.IPv4Address, ipaddress.IPv6Address]:
        return ipaddress.ip_address(ip_str)

    @classmethod
    def from_list(cls, ip_list: List[str]) -> List[Union[ipaddress.IPv4Address, ipaddress.IPv6Address]]:
        return [ipaddress.ip_address(ip_str) for ip_str in ip_list]


@dataclass
class GCPResource:  # FIXME: Better name for a class representing a parsed GCP resource URL?
    name: str = ""
    zone: str = ""
    region: str = ""
    project: str = ""
    klass: str = ""
    url: str = ""

    def __hash__(self) -> int:
        return hash(self.url)


def catch_notfound_return_emptylist(f):
    # type: (Callable[..., Any]) -> Callable[..., Any]
    @wraps(f)
    def wrapper(*args, **kwargs):
        # type: (*Any, **Any) -> Any
        try:
            return f(*args, **kwargs)
        except NotFound:
            return []
    return wrapper


def catch_notfound_return_none(f):
    # type: (Callable[..., Any]) -> Callable[..., Any]
    @wraps(f)
    def wrapper(*args, **kwargs):
        # type: (*Any, **Any) -> Any
        try:
            return f(*args, **kwargs)
        except NotFound:
            return None
    return wrapper


def parse_service_account_email(email: str) -> tuple[str, str]:
    pattern = (
        r"([a-zA-Z][a-zA-Z\d\-]{4,28}[a-zA-Z\d])@"  # Name
        r"([a-zA-Z][a-zA-Z\d\-]*[a-zA-Z\d])"  # Project ID
        r"\.iam\.gserviceaccount\.com"
    )
    if match := re.fullmatch(pattern, email):
        return match.group(1), match.group(2)
    raise ValueError(
        "Service account email must be in the format <name>@<project>.iam.gserviceaccount.com. "
        "The name must start with a lower or upper case letter, can only contain lower or upper "
        "case letters, numbers and hyphens and cannot end with a hyphen and be between 6 and 30 "
        "characters."
    )


class GCPClient:
    def __init__(
        self,
        project_id: str | None = None,
    ) -> None:
        self._project_id = project_id

        try:
            credentials, _ = google.auth.default(
                scopes=(
                    "https://www.googleapis.com/auth/cloud-platform",
                )
            )
        except DefaultCredentialsError as e:
            raise CODException(message=str(e))

        try:
            credentials.refresh(
                google.auth.transport.requests.Request()  # type: ignore[no-untyped-call]
            )
            self._credentials = credentials
        except RefreshError as e:
            # Beautify cryptic invalid grant errors (BCM-32050).
            if e.args and isinstance(e.args[0], str) and e.args[0].startswith("invalid_grant:"):
                raise CODException(
                    f"There was a problem refreshing your current auth tokens: {e}. "
                    "Please run `gcloud auth application-default login` to obtain new credentials."
                )
            raise CODException(message=f"{type(e).__name__}: {e}")

    @classmethod
    def from_config(cls) -> GCPClient:
        return cls(
            project_id=config["project_id"],
        )

    @cached_property
    def addresses_client(self) -> compute_v1.AddressesClient:
        return compute_v1.AddressesClient(credentials=self._credentials)

    @cached_property
    def global_addresses_client(self) -> compute_v1.GlobalAddressesClient:
        return compute_v1.GlobalAddressesClient(credentials=self._credentials)

    @cached_property
    def asset_service_client(self) -> asset_v1.AssetServiceClient:
        return asset_v1.AssetServiceClient(credentials=self._credentials)

    @cached_property
    def disks_client(self) -> compute_v1.DisksClient:
        return compute_v1.DisksClient(credentials=self._credentials)

    @cached_property
    def filestore_manager_client(self) -> filestore_v1.CloudFilestoreManagerClient:
        return filestore_v1.CloudFilestoreManagerClient(credentials=self._credentials)

    @cached_property
    def firewalls_client(self) -> compute_v1.FirewallsClient:
        return compute_v1.FirewallsClient(credentials=self._credentials)

    @cached_property
    def forwarding_rules_client(self) -> compute_v1.ForwardingRulesClient:
        return compute_v1.ForwardingRulesClient(credentials=self._credentials)

    @cached_property
    def global_forwarding_rules_client(self) -> compute_v1.GlobalForwardingRulesClient:
        return compute_v1.GlobalForwardingRulesClient(credentials=self._credentials)

    @cached_property
    def iam_client(self) -> iam_admin_v1.IAMClient:
        return iam_admin_v1.IAMClient(credentials=self._credentials)

    @cached_property
    def images_client(self) -> compute_v1.ImagesClient:
        return compute_v1.ImagesClient(credentials=self._credentials)

    @cached_property
    def instances_client(self) -> compute_v1.InstancesClient:
        return compute_v1.InstancesClient(credentials=self._credentials)

    @cached_property
    def machine_types_client(self) -> compute_v1.MachineTypesClient:
        return compute_v1.MachineTypesClient(credentials=self._credentials)

    @cached_property
    def networks_client(self) -> compute_v1.NetworksClient:
        return compute_v1.NetworksClient(credentials=self._credentials)

    @cached_property
    def projects_client(self) -> resourcemanager_v3.ProjectsClient:
        return resourcemanager_v3.ProjectsClient(credentials=self._credentials)

    @cached_property
    def routers_client(self) -> compute_v1.RoutersClient:
        return compute_v1.RoutersClient(credentials=self._credentials)

    @cached_property
    def snapshots_client(self) -> compute_v1.SnapshotsClient:
        return compute_v1.SnapshotsClient(credentials=self._credentials)

    @cached_property
    def storage_client(self) -> storage.Client:
        return storage.Client(project=self._project_id, credentials=self._credentials)

    @cached_property
    def subnetworks_client(self) -> compute_v1.SubnetworksClient:
        return compute_v1.SubnetworksClient(credentials=self._credentials)

    @cached_property
    def tag_bindings_client(self) -> resourcemanager_v3.TagBindingsClient:
        return resourcemanager_v3.TagBindingsClient(credentials=self._credentials)

    @cached_property
    def tag_keys_client(self) -> resourcemanager_v3.TagKeysClient:
        return resourcemanager_v3.TagKeysClient(credentials=self._credentials)

    @cached_property
    def tag_values_client(self) -> resourcemanager_v3.TagValuesClient:
        return resourcemanager_v3.TagValuesClient(credentials=self._credentials)

    @cached_property
    def target_instances_client(self) -> compute_v1.TargetInstancesClient:
        return compute_v1.TargetInstancesClient(credentials=self._credentials)

    def validate_instance_types_arch(self, zone: str, machine_type: str, arch: str, node_type: str) -> str:
        """
        Validate that the machine type and selected architecture match.
        If no architecture is specified in the config, use the machine type's architecture.
        Return the machine type's architecture.
        """

        # This list was compiled from:
        # [for mt in compute_v1.MachineTypesClient().list(project=project, zone=<all-gcp-zones>) if not mt.architecture]
        # As of May 2025, all of the machines in the list are x86-64, but their architecture field is not populated. We
        # can safely assume that future machine types will have a proper architecture set, but we print a warning in the
        # unlikely case that this assumption is violated.
        known_x86_64_mts = {"a2", "c2", "c2d", "e2", "f1", "g1", "m1", "m2", "n1", "n2", "n2d"}

        def get_cod_machine_arch(machine_type: compute_v1.MachineType) -> str | None:
            machine_arch = machine_type.architecture or (
                "X86_64" if machine_type.name.split("-")[0] in known_x86_64_mts else None
            )
            gcp_to_cod: dict[str | None, str] = {"ARM64": "aarch64", "X86_64": "x86_64"}
            return gcp_to_cod.get(machine_arch, machine_arch)

        machine_arch = get_cod_machine_arch(
            self.machine_types_client.get(
                project=self._project_id, zone=zone, machine_type=machine_type
            )
        )

        return utils.validate_arch_vs_machine_arch(arch, machine_arch, machine_type, node_type)

    def create_instance(
        self,
        project: str,
        region: str,
        zone: str,
        name: str,
        instance_type: str,
        metadata: compute_v1.Metadata,
        sa_email: str,
        image_uri: str,
        disk_provisioned_iops: int,
        disk_provisioned_throughput: int,
        disk_size: int,
        disk_type: str,
        hostname: str,
        network_interfaces: list[compute_v1.NetworkInterface],
        arch: str,
        tagpairs: dict[tuple[str, str], tuple[str, str]],
        labels: dict[str, str],
    ) -> compute_v1.Instance:
        disk = compute_v1.AttachedDisk(
            boot=True,
            auto_delete=True,
            disk_size_gb=disk_size,
            initialize_params=compute_v1.AttachedDiskInitializeParams(
                disk_type=f"zones/{zone}/diskTypes/{disk_type}" if disk_type else None,
                provisioned_iops=disk_provisioned_iops,
                provisioned_throughput=disk_provisioned_throughput,
                source_image=image_uri,
            ),
        )
        disk.guest_os_features = [
            # Otherwise subnet mask is /32 in DHCP responses.
            compute_v1.GuestOsFeature(
                type_=compute_v1.GuestOsFeature.Type.MULTI_IP_SUBNET.name),  # type: ignore[attr-defined]
            compute_v1.GuestOsFeature(
                type_=compute_v1.GuestOsFeature.Type.GVNIC.name),  # type: ignore[attr-defined]
        ]
        if arch == "aarch64":
            disk.guest_os_features += [
                compute_v1.GuestOsFeature(
                    type_=compute_v1.GuestOsFeature.Type.UEFI_COMPATIBLE.name),  # type: ignore[attr-defined]
            ]

        service_account = compute_v1.ServiceAccount(
            email=sa_email,
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )

        instance = compute_v1.Instance()
        # The specified hostname must be RFC1035 compliant. The default hostname is
        # `[INSTANCE_NAME].[ZONE].c.[PROJECT_ID].internal` when using zonal DNS.
        instance.hostname = f"{hostname}.{zone}.c.{project}.internal"
        instance.labels = labels
        instance.network_interfaces = network_interfaces
        instance.name = name
        instance.disks = [disk]
        # TOOD: Check whether the instance type exists in the zone?
        instance.machine_type = f"zones/{zone}/machineTypes/{instance_type}"
        if arch != "aarch64":  # ARM64 instances don't support display devices
            instance.display_device = compute_v1.DisplayDevice(enable_display=True)

        # Instances with guest accelerators do not support live migration.
        machine_type = self.machine_types_client.get(
            project=project, zone=zone, machine_type=instance_type
        )
        if machine_type.accelerators:
            instance.scheduling = compute_v1.Scheduling(on_host_maintenance="TERMINATE")

        instance.tags = compute_v1.Tags(
            items=[BCM_NETWORKTAG_HEADNODE]  # for the firewall, this is a network tag, not a resource tag
        )
        instance.metadata = metadata
        instance.service_accounts = [service_account]
        tagpair_ids_dict = dict(tagpairs.values())

        instance.params = compute_v1.InstanceParams(resource_manager_tags=tagpair_ids_dict)

        log.info(f"Creating instance {name!r} in zone {zone!r}")
        wait_for_extended_operation(
            self.instances_client.insert(
                zone=zone,
                project=project,
                instance_resource=instance,
            ),
            ignore_warning_codes=["DISK_SIZE_LARGER_THAN_IMAGE_SIZE"]
        )
        return self.instances_client.get(project=project, zone=zone, instance=name)

    @tenacity.retry(
        retry=tenacity.retry_if_exception_type(AlreadyExists),
        wait=tenacity.wait_random(min=0, max=2),
        stop=tenacity.stop_after_attempt(5),
        before_sleep=tenacity.before_sleep_log(log, logging.DEBUG),
        reraise=True,
    )
    def resolve_and_create_missing_tags(
        self,
        tags: dict[str, set[str]],
        project: str,
    ) -> dict[tuple[str, str], tuple[str, str]]:
        """
        Converts collection of tags (key name -> set of possible values names) to corresponding tag key id/value id.
        If any key or value is missing, it creates one.

        Example:
        - Input: {"BCM_Cluster": {"cluster1", "cluster2"}}
        - Output: {("BCM_Cluster", "cluster1"): ("tagKeys/123", "tagValues/456"),
                   ("BCM_Cluster", "cluster2"): ("tagKeys/123", "tagValues/789")}

        Note: GCP has confusing terminology:
        - In SDK tag key/value ID is stored in the "name" field, while name is stored in the "short_name" field.
        - In web interface they are called as expected: tag key ID and tag value ID.

        Retries:
        It's possible, that the function fails with AlreadyExists error because of a race condition with
        other tags creator (other script or manual tag creation by user).
        In such a case, let's retry the entire function just for simplicity.
        """

        @dataclass
        class _GCPTag:
            key_id: str
            values_name_to_id: dict[str, str] = field(default_factory=dict)  # value name -> value ID
            is_new: bool = False

        # Find existing tag keys.
        gcp_tags: dict[str, _GCPTag] = {
            tag_key.short_name: _GCPTag(key_id=tag_key.name)
            for tag_key in self.tag_keys_client.list_tag_keys(parent=f"projects/{project}")
            if tag_key.short_name in tags
        }

        # Create missing tag keys.
        for tag_key_name in tags.keys() - gcp_tags.keys():
            tag_key: resourcemanager_v3.TagKey
            tag_key = resourcemanager_v3.TagKey(short_name=tag_key_name, parent=f"projects/{project}")
            log.info(f"Creating tag key {tag_key_name!r}")
            tag_key = self.tag_keys_client.create_tag_key(tag_key=tag_key).result()  # type: ignore[no-untyped-call]
            gcp_tags[tag_key_name] = _GCPTag(key_id=tag_key.name, is_new=True)

        # Resolve tag values.
        for tag_key_name, tag_values_names in tags.items():
            gcp_tag = gcp_tags[tag_key_name]

            # Find existing key values.
            gcp_tag.values_name_to_id = {
                tag_val.short_name: tag_val.name
                for tag_val in self.tag_values_client.list_tag_values(parent=gcp_tag.key_id)
            } if not gcp_tag.is_new else {}  # no need to list values for new tags

            # Create missing tag values.
            for tag_value_name in tag_values_names - gcp_tag.values_name_to_id.keys():
                log.info(f"Creating tag value '{tag_key_name}={tag_value_name}'")
                tag_value: resourcemanager_v3.TagValue
                tag_value = resourcemanager_v3.TagValue(short_name=tag_value_name, parent=gcp_tag.key_id)
                tag_value = self.tag_values_client.create_tag_value(
                    tag_value=tag_value).result()  # type: ignore[no-untyped-call]
                gcp_tag.values_name_to_id[tag_value_name] = tag_value.name

        return {
            (tag_key_name, tag_value_name):
            (
                (gcp_tag := gcp_tags[tag_key_name]).key_id,
                gcp_tag.values_name_to_id[tag_value_name],
            )
            for tag_key_name, tag_values in tags.items()
            for tag_value_name in tag_values
        }

    def tag_service_account(self, project: str, sa_id: str, sa_name: str,
                            tagpairs: dict[tuple[str, str], tuple[str, str]]) -> str:
        resource_id = build_sa_idurl(project=project, sa_id=sa_id)
        self.tag_resource(project=project, endpoint="", resource_id=resource_id, tagpairs=tagpairs)
        return build_sa_nameurl(project=project, sa_name=sa_name)

    def untag_service_account(self, project: str, sa_email: str, sa_id: str) -> None:
        log.debug(f"Untagging service account {sa_email}")
        resource_id = build_sa_idurl(project=project, sa_id=sa_id)
        self.untag_resource(endpoint="", resource_id=resource_id)

    def get_service_account_tags(self, project: str,
                                 sa_id: str) -> ListEffectiveTagsPager:
        resource_id = build_sa_idurl(project=project, sa_id=sa_id)
        return self.get_resource_tags(endpoint="", resource_id=resource_id)

    def get_disk_tags(
        self, project: str, zone: str, _id: int
    ) -> ListEffectiveTagsPager:
        endpoint = get_zone_api_endpoint(zone)
        resource_id = build_disk_idurl(project=project, zone=zone, _id=_id)
        return self.get_resource_tags(endpoint=endpoint, resource_id=resource_id)

    def get_instance_tags(self, project: str, zone: str, instance_id: int
                          ) -> ListEffectiveTagsPager:
        endpoint = get_zone_api_endpoint(zone)
        resource_id = build_instance_idurl(project=project, zone=zone, instance_id=instance_id)
        return self.get_resource_tags(endpoint=endpoint, resource_id=resource_id)

    def get_firewall_tags(self, project: str, firewall_id: int
                          ) -> ListEffectiveTagsPager:
        resource_id = build_firewall_idurl(project=project, firewall_id=firewall_id)
        return self.get_resource_tags(endpoint="", resource_id=resource_id)

    def get_router_tags(
        self, project: str, region: str, _id: int
    ) -> ListEffectiveTagsPager:
        endpoint = get_region_api_endpoint(region)
        resource_id = build_nat_gateway_idurl(project=project, region=region, nat_gateway_id=_id)
        return self.get_resource_tags(endpoint=endpoint, resource_id=resource_id)

    def get_snapshot_tags(
        self, project: str, _id: int
    ) -> ListEffectiveTagsPager:
        resource_id = build_snapshot_idurl(project=project, _id=_id)
        return self.get_resource_tags(endpoint="", resource_id=resource_id)

    def get_subnetwork_tags(self, project: str, region: str, subnetwork_id: int
                            ) -> ListEffectiveTagsPager:
        endpoint = get_region_api_endpoint(region)
        resource_id = build_subnetwork_idurl(project=project, region=region, subnetwork_id=subnetwork_id)
        return self.get_resource_tags(endpoint=endpoint, resource_id=resource_id)

    def get_network_tags(self, project: str, network_id: int
                         ) -> ListEffectiveTagsPager:
        resource_id = build_network_idurl(project=project, network_id=network_id)
        return self.get_resource_tags(endpoint="", resource_id=resource_id)

    def get_target_instance_tags(
        self, project: str, zone: str, _id: int
    ) -> ListEffectiveTagsPager:
        endpoint = get_zone_api_endpoint(zone)
        resource_id = build_target_instance_idurl(project=project, zone=zone, _id=_id)
        return self.get_resource_tags(endpoint=endpoint, resource_id=resource_id)

    def delete_tag_binding_asset(self, tag_binding: asset_v1.Asset) -> None:
        assert tag_binding.asset_type == "cloudresourcemanager.googleapis.com/TagBinding"
        assert tag_binding.resource.version == "v3"
        name = tag_binding.resource.data["name"]
        log.debug(f"Deleting {name}")
        try:
            self.tag_bindings_client.delete_tag_binding(name=name)
        except NotFound as e:
            log.debug(e)

    def delete_tag_values(self, tag_values: list[resourcemanager_v3.TagValue]) -> None:
        """
        Delete tag values, assuming they are not used anymore.
        """
        log.debug("Cleaning up tag values")
        ops = {}
        undeletable_tagvalues: set[str] = set()
        for tag_value in tag_values:
            tag_key_name, tag_value_name = tag_value.namespaced_name.split("/")[-2:]
            log.info(f"Deleting tag value '{tag_key_name}={tag_value_name}'")
            try:
                ops[f"{tag_key_name}={tag_value_name}"] = self.delete_tagvalue_by_id_async(tagvalueid=tag_value.name)
            except (PermissionDenied, NotFound) as e:  # This normally means the tag doesn't exist.
                log.debug(f"Tag value {tag_key_name}={tag_value_name} does not exist ({e})")

        for tag_value_desc, op in ops.items():
            log.info(f"Awaiting tag value {tag_value_desc} deletion")
            try:
                op.result()  # type: ignore[no-untyped-call]
            except FailedPrecondition as e:
                undeletable_tagvalues.add(tag_value_desc)
                log.error(f"Error awaiting tag value {tag_value_desc} deletion: {e.message!r}")

        if undeletable_tagvalues:
            raise CODException(f"The following tag values could not be deleted: {','.join(undeletable_tagvalues)}")

    def tag_network(self, project: str, network_id: int, network_name: str,
                    tagpairs: dict[tuple[str, str], tuple[str, str]]) -> str:
        resource_id = build_network_idurl(project=project, network_id=network_id)
        self.tag_resource(project=project, endpoint="", resource_id=resource_id, tagpairs=tagpairs)
        return build_network_nameurl(project=project, network_name=network_name)

    def tag_firewalls(
        self,
        project: str,
        firewalls: list[compute_v1.Firewall],
        tagpairs: dict[tuple[str, str], tuple[str, str]]
    ) -> list[str]:
        return [self.tag_firewall(project=project, firewall_id=fw.id, firewall_name=fw.name, tagpairs=tagpairs)
                for fw in firewalls]

    def tag_firewall(self, project: str, firewall_id: int, firewall_name: str,
                     tagpairs: dict[tuple[str, str], tuple[str, str]]) -> str:
        resource_id = build_firewall_idurl(project=project, firewall_id=firewall_id)
        self.tag_resource(project=project, endpoint="", resource_id=resource_id, tagpairs=tagpairs)
        return build_firewall_nameurl(project=project, firewall_name=firewall_name)

    def tag_subnet(self, project: str, subnet_id: int, subnet_name: str, region: str,
                   tagpairs: dict[tuple[str, str], tuple[str, str]]) -> str:
        endpoint = get_region_api_endpoint(region)
        resource_id = build_subnetwork_idurl(project=project, region=region, subnetwork_id=subnet_id)
        self.tag_resource(project=project, endpoint=endpoint, resource_id=resource_id, tagpairs=tagpairs)
        return build_subnetwork_nameurl(project=project, region=region, subnetwork_name=subnet_name)

    def tag_nat_gateway(self, project: str, nat_gateway_id: int, nat_gateway_name: str, region: str,
                        tagpairs: dict[tuple[str, str], tuple[str, str]]) -> str:
        endpoint = get_region_api_endpoint(region)
        resource_id = build_nat_gateway_idurl(project=project, region=region, nat_gateway_id=nat_gateway_id)
        self.tag_resource(project=project, endpoint=endpoint, resource_id=resource_id, tagpairs=tagpairs)
        return build_nat_gateway_nameurl(project=project, region=region, nat_gateway_name=nat_gateway_name)

    def wait_for_tags(self, project: str, query: str, expected: list[str]) -> None:
        log.info("Waiting for tags on created resources to be visible")
        attempts = BCM_TAG_RETRIES
        while attempts > 0:
            assetlist = self.list_tagged_resources(project=project, query=query)
            log.debug(f"{len(assetlist)} of {len(expected)} cluster resources have been tagged (attempt {attempts})")
            found = 0
            for asset in expected:
                found += 1 if asset in assetlist else 0
            if found == len(expected):
                break
            attempts -= 1
            time.sleep(BCM_TAG_RETRYTIME)
        if attempts == 0:
            raise RuntimeError(f"Only found {found} resources with our tag, expected {len(expected)}")

    def list_tag_binding_assets(self, project: str) -> list[asset_v1.Asset]:
        return list(
            self.asset_service_client.list_assets(
                request=asset_v1.ListAssetsRequest(
                    parent=f"projects/{project}",
                    asset_types=["cloudresourcemanager.googleapis.com/TagBinding"],
                    content_type=asset_v1.ContentType.RESOURCE,
                )
            )
        )

    def list_tagged_resources(self, project: str, query: str) -> list[str]:
        resources = self.asset_service_client.search_all_resources(scope=f"projects/{project}", query=query)
        return [resource.name for resource in resources]

    def list_project_instances(self, project: str) -> AggregatedListPager:
        return self.instances_client.aggregated_list(project=project)

    def delete_instance(self, project: str, instance: compute_v1.Instance) -> ExtendedOperation:
        zone = instance.zone.split("/")[-1]
        log.info("Deleting instance %r in zone %r", instance.name, zone)
        return self.instances_client.delete(project=project, zone=zone, instance=instance.name)

    def delete_filestore(self, filestore: filestore_v1.Instance) -> Operation:
        log.info(f"Deleting filestore {filestore.name}")
        return self.filestore_manager_client.delete_instance(name=filestore.name)

    def get_filestore_tags(
        self, name: str
    ) -> ListEffectiveTagsPager:
        m = re.fullmatch(r"projects/[^/]+/locations/([^/]+)/instances/[^/]+", name)
        assert m
        endpoint = get_zone_api_endpoint(m.group(1))
        resource_id = build_filestore_idurl(name=name)
        return self.get_resource_tags(endpoint=endpoint, resource_id=resource_id)

    def create_nat_gateway(self, project: str, region: str, network: compute_v1.Network,
                           cluster_name: str) -> compute_v1.Router:
        router_name = cluster_name_to_router_name(cluster_name)
        nat_gateway_name = cluster_name_to_gateway_name(cluster_name)
        log.info(f"Creating cloud router {router_name!r} and NAT gateway {nat_gateway_name!r}")

        # Configure NAT
        nat_config = compute_v1.RouterNat(
            name=nat_gateway_name,
            nat_ip_allocate_option="AUTO_ONLY",
            source_subnetwork_ip_ranges_to_nat="ALL_SUBNETWORKS_ALL_IP_RANGES"
        )

        router = compute_v1.Router(
            name=router_name,
            network=network.self_link,
            nats=[nat_config]
        )
        operation = self.routers_client.insert(project=project, region=region, router_resource=router)
        operation.result()  # type: ignore[no-untyped-call]

        return self.get_nat_gateway(project=project, region=region, nat_gateway_name=router_name)

    def delete_router(self, project: str, router: compute_v1.Router) -> ExtendedOperation:
        log.info("Deleting NAT gateway %r", router.name)
        return self.routers_client.delete(
            project=project,
            region=router.region.split("/")[-1],
            router=router.name,
        )

    def create_network(self, project: str, network_name: str, mtu: int) -> compute_v1.Network:
        log.info(f"Creating network {network_name!r}")
        network = compute_v1.Network(
            auto_create_subnetworks=False,
            name=network_name,
            mtu=mtu,
        )
        wait_for_extended_operation(
            self.networks_client.insert(project=project, network_resource=network)
        )
        return self.networks_client.get(project=project, network=network_name)

    def list_networks(self, project: str) -> list[compute_v1.Network]:
        return list(self.networks_client.list(project=project))

    def get_network(self, project: str, network_name: str) -> compute_v1.Network:
        return self.networks_client.get(project=project, network=network_name)

    @catch_notfound_return_none
    def get_firewall(self, project: str, firewall_name: str) -> compute_v1.Firewall:
        return self.firewalls_client.get(project=project, firewall=firewall_name)

    def get_subnet(self, project: str, region: str, subnet_name: str) -> compute_v1.Subnetwork:
        return self.subnetworks_client.get(project=project, region=region, subnetwork=subnet_name)

    def get_nat_gateway(self, project: str, region: str, nat_gateway_name: str) -> compute_v1.Router:
        return self.routers_client.get(project=project, region=region, router=nat_gateway_name)

    def get_service_account(self, project: str, account: str) -> ServiceAccount:
        try:
            return self.iam_client.get_service_account(
                name=f"projects/{project}/serviceAccounts/{account}"
            )
        except NotFound:
            raise RuntimeError(f"Service account {account} does not exist")

    def get_instance(self, project: str, instance_name: str, zone: str) -> compute_v1.Instance:
        return self.instances_client.get(project=project, zone=zone, instance=instance_name)

    def cluster_exists(self, project_id: str, cluster_name: str) -> bool:
        return cluster_name in self.list_cluster_names(project_id)

    def validate_cluster_name(self, cluster_name: str) -> bool:
        # GCP resources must start with a lower-case character, can only contain lower-case letters, numbers and
        # hyphens and cannot end with a hyphen. Max resource name length is 63 characters.
        # See: https://cloud.google.com/compute/docs/naming-resources
        verify_pattern = r'^[a-z]([a-z0-9-]*[a-z0-9])?$'
        return bool(re.match(verify_pattern, cluster_name))

    def list_bcm_tag_keys_and_values(
        self, project: str
    ) -> list[tuple[resourcemanager_v3.TagKey, list[resourcemanager_v3.TagValue]]]:
        return [
            (tag_key, self.list_tag_values(tag_key.name))
            for tag_key in self.tag_keys_client.list_tag_keys(parent=f"projects/{project}")
            if tag_key.short_name == BCM_TAG_CLUSTER
        ]

    def list_cluster_tagvalues(self, project_id: str) -> list[resourcemanager_v3.TagValue]:
        if tag_key := self.get_tagkey_id(project_id, BCM_TAG_CLUSTER):
            return self.list_tag_values(tag_key)
        return []

    def list_cluster_names(self, project_id: str) -> list[str]:
        if tag_key := self.get_tagkey_id(project_id, BCM_TAG_CLUSTER):
            return [tagvalue.short_name for tagvalue in self.list_tag_values(tag_key)]
        return []

    def delete_disk(self, project: str, disk: compute_v1.Disk) -> None:
        zone = disk.zone.split("/")[-1]
        log.info("Deleting disk %r in zone %r", disk.name, zone)
        self.disks_client.delete(project=project, zone=zone, disk=disk.name)

    def list_disks(self, project: str) -> list[compute_v1.Disk]:
        return [
            disk
            for _, response in self.disks_client.aggregated_list(
                request=compute_v1.AggregatedListDisksRequest(
                    include_all_scopes=True,
                    project=project,
                    return_partial_success=True,
                )
            )
            for disk in response.disks
        ]

    def list_filestores(self, project: str) -> list[filestore_v1.Instance]:
        return list(
            self.filestore_manager_client.list_instances(parent=f"projects/{project}/locations/-")
        )

    def list_firewalls(self, project: str) -> list[compute_v1.Firewall]:
        return list(self.firewalls_client.list(project=project))

    def list_forwarding_rules(self, project: str) -> list[compute_v1.ForwardingRule]:
        return [
            forwarding_rule
            for _, response in self.forwarding_rules_client.aggregated_list(
                request=compute_v1.AggregatedListForwardingRulesRequest(
                    include_all_scopes=True,
                    project=project,
                    return_partial_success=True,
                )
            )
            for forwarding_rule in response.forwarding_rules
        ]

    def list_head_nodes(self, project: str) -> list[compute_v1.Instance]:
        # TODO(kal): Use head-node label for server-side filtering.
        return [
            instance
            for _, response in self.instances_client.aggregated_list(
                request=compute_v1.AggregatedListInstancesRequest(
                    include_all_scopes=True,
                    project=project,
                    return_partial_success=True,
                )
            )
            for instance in response.instances
            if (
                BCM_LABEL_HEAD_NODE in instance.labels
                or BCM_NETWORKTAG_HEADNODE in instance.tags.items
            )
        ]

    def list_images(self, project: str) -> list[compute_v1.Image]:
        return list(self.images_client.list(project=project))

    def list_instances(self, project: str) -> list[compute_v1.Instance]:
        return [
            instance
            for _, response in self.instances_client.aggregated_list(
                request=compute_v1.AggregatedListInstancesRequest(
                    include_all_scopes=True,
                    project=project,
                    return_partial_success=True,
                )
            )
            for instance in response.instances
        ]

    def list_routers(self, project: str) -> list[compute_v1.Router]:
        return [
            router
            for _, response in self.routers_client.aggregated_list(
                request=compute_v1.AggregatedListRoutersRequest(
                    include_all_scopes=True,
                    project=project,
                    return_partial_success=True,
                )
            )
            for router in response.routers
        ]

    def list_service_accounts(self, project: str) -> list[compute_v1.ServiceAccount]:
        return list(self.iam_client.list_service_accounts(name=f"projects/{project}"))

    def delete_snapshot(self, project: str, snapshot: compute_v1.Snapshot) -> None:
        log.info("Deleting snapshot %r", snapshot.name)
        self.snapshots_client.delete(project=project, snapshot=snapshot.name)

    def list_snapshots(self, project: str) -> list[compute_v1.Snapshot]:
        return list(self.snapshots_client.list(project=project))

    def list_subnetworks(self, project: str) -> list[compute_v1.Subnetwork]:
        return [
            subnetwork
            for _, response in self.subnetworks_client.aggregated_list(
                request=compute_v1.AggregatedListSubnetworksRequest(
                    include_all_scopes=True,
                    project=project,
                    return_partial_success=True,
                )
            )
            for subnetwork in response.subnetworks
        ]

    def list_target_instances(self, project: str) -> list[compute_v1.TargetInstance]:
        return [
            target_instance
            for _, response in self.target_instances_client.aggregated_list(
                request=compute_v1.AggregatedListTargetInstancesRequest(
                    include_all_scopes=True,
                    project=project,
                    return_partial_success=True,
                )
            )
            for target_instance in response.target_instances
        ]

    def get_instance_by_name(self, project: str, instance_name: str, zone: str) -> compute_v1.Instance | None:
        try:
            return self.get_instance(project=project, instance_name=instance_name,
                                     zone=zone)
        except NotFound:
            log.debug(f"{instance_name!r} in zone {zone!r} not found -- perhaps deleted?")
            return None

    @cache
    def get_disk_image(self, image_name: str, project: str) -> compute_v1.Image | None:
        return self.get_disk_image_uncached(image_name, project)

    def get_disk_image_uncached(self, image_name: str, project: str) -> compute_v1.Image | None:
        try:
            return self.images_client.get(image=image_name, project=project)
        except NotFound:
            return None

    def list_blobs(self, path: str) -> Iterable[storage.blob.Blob]:
        m = re.fullmatch("gs://([^/]+)/?(.+)?", path)
        assert m
        bucket_name, prefix = m.groups()
        return self.storage_client.list_blobs(  # type: ignore[no-any-return]
            bucket_name,
            prefix=prefix,
        )

    def get_blob_by_name(self, bucket_name: str, blob_path: str) -> storage.blob.Blob:
        bucket = storage.bucket.Bucket(self.storage_client, bucket_name)
        return bucket.get_blob(blob_path)

    def get_blob_by_url(self, blob_url: str) -> storage.blob.Blob:
        bucket_name, blob_path = _parse_blob_url(blob_url)
        assert bucket_name and blob_path
        return self.get_blob_by_name(bucket_name, blob_path)

    def create_image(
        self,
        project_id: str,
        image_name: str,
        blob_url: str,
        labels: dict[str, str],
        location: str,
        arch: str,
    ) -> compute_v1.Image:
        image = compute_v1.Image()
        image.name = image_name
        image.kind = "compute#image"
        image.raw_disk = compute_v1.RawDisk()
        image.raw_disk.source = blob_url
        image.architecture = {
            "x86_64": "X86_64",
            "aarch64": "ARM64",
        }[arch]
        image.labels = labels
        image.storage_locations = [location]
        image.guest_os_features = [
            # We also specify the feature during instance creation, so we don't really need to set it here.
            # But it might be useful for instance creation using gcloud CLI.
            compute_v1.GuestOsFeature(
                type_=compute_v1.GuestOsFeature.Type.MULTI_IP_SUBNET.name,   # type: ignore[attr-defined]
            ),
        ]
        wait_for_extended_operation(
            self.images_client.insert(
                request=compute_v1.InsertImageRequest(project=project_id, image_resource=image)
            ),
            timeout=600,
        )
        return self.images_client.get(project=project_id, image=image_name)

    def delete_network(self, project: str, network: compute_v1.Network) -> ExtendedOperation:
        log.info("Deleting network %r", network.name)
        return self.networks_client.delete(project=project, network=network.name)

    def create_fws(
        self,
        project: str,
        fw_nameprefix: str,
        network: compute_v1.Network,
        target_tags: list[str],
        inbound_rules: list[InboundTrafficRule],
        ingress_icmp: list[str],
    ) -> list[compute_v1.Firewall]:

        operations: list[ExtendedOperation] = []
        created_name_list: list[str] = []
        suffix = 0
        src_cidrs: set[str] = set()

        if inbound_rules:
            src_cidrs.update(set([r.src_cidr for r in inbound_rules if r.src_cidr != "*"]))
        if ingress_icmp:
            src_cidrs.update(set(ingress_icmp))

        for src_cidr in src_cidrs:
            fw_name = f"{fw_nameprefix}-{suffix}"
            suffix += 1
            log.info(f"Creating firewall {fw_name!r}")
            fw = compute_v1.Firewall(name=fw_name, network=network.self_link,
                                     description=f"{network.name}-{src_cidr}-firewall",
                                     direction="INGRESS", allowed=[], source_ranges=[src_cidr])
            if target_tags:
                fw.target_tags = target_tags

            for r in inbound_rules:
                if r.src_cidr == src_cidr:
                    log.debug(f"Inbound rule: {r}")
                    log.debug(f"Creating firewall rule: src={src_cidr!r}, dst={r.dst_port!r}:{r.protocol!r}")
                    fw.allowed.append(compute_v1.Allowed(I_p_protocol=r.protocol, ports=[r.dst_port]))

            if src_cidr in ingress_icmp:
                log.debug("Inbound rule: %r:icmp", src_cidr)
                log.debug(f"Creating firewall rule: src={src_cidr!r}, proto=icmp")
                fw.allowed.append(compute_v1.Allowed(I_p_protocol="icmp"))

            operations.append(self.firewalls_client.insert(project=project, firewall_resource=fw))
            created_name_list.append(fw_name)

        if operations:
            log.info("Awaiting creation of %d firewall(s) to complete", len(operations))
            for op in operations:
                wait_for_extended_operation(op)

        return [self.firewalls_client.get(project=project, firewall=fw_name) for fw_name in created_name_list]

    def delete_firewall(self, project: str, firewall: compute_v1.Firewall) -> ExtendedOperation:
        log.info("Deleting firewall %r", firewall.name)
        return self.firewalls_client.delete(project=project, firewall=firewall.name)

    def create_subnet(
        self,
        project: str,
        region: str,
        network: compute_v1.Network,
        subnet_name: str,
        subnet_cidr: str,
    ) -> compute_v1.Subnetwork:
        log.info(f"Creating subnet {subnet_name!r} in region {region!r}")
        subnet = compute_v1.Subnetwork(
            name=subnet_name,
            network=network.self_link,
            ip_cidr_range=subnet_cidr,
            # secondary_ip_ranges="" TODO,
            # stack_type=IPV4_IPV6 TODO,
        )
        op = self.subnetworks_client.insert(project=project, region=region, subnetwork_resource=subnet)
        wait_for_extended_operation(op)

        return self.subnetworks_client.get(project=project, region=region, subnetwork=subnet_name)

    def delete_subnetwork(self, project: str, subnetwork: compute_v1.Subnetwork) -> ExtendedOperation:
        region = subnetwork.region.split("/")[-1]
        log.info("Deleting subnetwork %r in region %r", subnetwork.name, region)
        return self.subnetworks_client.delete(
            project=project,
            region=region,
            subnetwork=subnetwork.name,
        )

    def delete_target_instance(
        self, project: str, target_instance: compute_v1.TargetInstance
    ) -> ExtendedOperation:
        log.info(f"Deleting target instance {target_instance.name}")
        return self.target_instances_client.delete(
            project=project,
            zone=target_instance.zone.split("/")[-1],
            target_instance=target_instance.name,
        )

    def ensure_tagkeys_exist(self, project: str) -> None:
        current_tags = [tag.short_name for tag in self.tag_keys_client.list_tag_keys(parent="projects/" + project)]
        for tagname in BCM_TAG_LIST:
            self.create_tagkey(tagname, project) if tagname not in current_tags else None

    def create_tagkey(self, tagname: str, project: str) -> resourcemanager_v3.TagKey | None:
        newtag = resourcemanager_v3.TagKey(short_name=tagname, parent=f"projects/{project}")
        op = self.tag_keys_client.create_tag_key(tag_key=newtag)
        res: resourcemanager_v3.TagKey = op.result()  # type: ignore[no-untyped-call]
        return res

    def get_tagkey(self, project: str, tagkey: str) -> resourcemanager_v3.TagKey | None:
        try:
            response = self.tag_keys_client.get_namespaced_tag_key(name=f"{project}/{tagkey}")
        except PermissionDenied:
            return None
        return response

    def get_tagvalue(self, project: str, tagkey: str, tagvalue: str) -> resourcemanager_v3.TagValue | None:
        try:
            response = self.tag_values_client.get_namespaced_tag_value(name=f"{project}/{tagkey}/{tagvalue}")
        except PermissionDenied:
            return None
        return response

    def get_tagkey_id(self, project: str, tagkey: str) -> str | None:
        res = self.get_tagkey(project, tagkey)
        return res.name if res else None

    # FIXME: Unused?
    def get_tagvalue_id(self, project: str, tagkey: str, tagvalue: str) -> str | None:
        res = self.get_tagvalue(project, tagkey, tagvalue)
        return res.name if res else None

    def list_tag_values(self, tagkey: str) -> list[resourcemanager_v3.TagValue]:
        request = resourcemanager_v3.ListTagValuesRequest(parent=tagkey)
        page_result = self.tag_values_client.list_tag_values(request=request)
        return [response for response in page_result]

    def list_tag_short_names(self, tagkey: str) -> list[str]:
        return [tagvalue.short_name for tagvalue in self.list_tag_values(tagkey)]

    def delete_tagvalue_by_id_async(self, tagvalueid: str) -> Operation:
        return self.tag_values_client.delete_tag_value(name=tagvalueid)

    def delete_tagvalue_by_id(self, tagvalueid: str) -> None:
        op = self.delete_tagvalue_by_id_async(tagvalueid)
        op.result()  # type: ignore[no-untyped-call]

    def tag_resource(self, project: str, endpoint: str, resource_id: str,
                     tagpairs: dict[tuple[str, str], tuple[str, str]]) -> None:
        log.debug(f"Tagging resource {resource_id} with {dict(tagpairs.keys())}")
        binding_client = resourcemanager_v3.TagBindingsClient(
            credentials=self._credentials,
            client_options=ClientOptions(api_endpoint=endpoint or None),
        )

        @tenacity.retry(
            retry=tenacity.retry_if_exception_type(FailedPrecondition),  # the resource has not finished creation?
            wait=tenacity.wait_exponential(min=1, max=30),
            stop=tenacity.stop_after_delay(300),
            before_sleep=tenacity.before_sleep_log(log, logging.DEBUG),
            reraise=True,
        )
        def create_tag_binding(request: resourcemanager_v3.CreateTagBindingRequest) -> Operation:
            return binding_client.create_tag_binding(request=request)

        for tagval in [value[1] for _, value in tagpairs.items()]:
            tag_binding = resourcemanager_v3.TagBinding(tag_value=tagval, parent=resource_id)
            req = resourcemanager_v3.CreateTagBindingRequest(tag_binding=tag_binding)
            op = create_tag_binding(request=req)
            op.result()  # type: ignore[no-untyped-call]

    def untag_resource(self, endpoint: str, resource_id: str) -> None:
        binding_client = resourcemanager_v3.TagBindingsClient(
            credentials=self._credentials,
            client_options=ClientOptions(api_endpoint=endpoint or None),
        )
        request = resourcemanager_v3.ListTagBindingsRequest(parent=resource_id)
        for tag_binding in binding_client.list_tag_bindings(request=request):
            op = binding_client.delete_tag_binding(name=tag_binding.name)
            op.result()  # type: ignore[no-untyped-call]

    def get_resource_tags(self, endpoint: str, resource_id: str
                          ) -> ListEffectiveTagsPager:
        binding_client = resourcemanager_v3.TagBindingsClient(
            credentials=self._credentials,
            client_options=ClientOptions(api_endpoint=endpoint or None),
        )
        return binding_client.list_effective_tags(parent=resource_id)

    def get_resources_for_cluster(self, project: str, cluster_name: str) -> list[GCPResource]:
        resources = []
        query = f"tagValues={project}/{BCM_TAG_CLUSTER}/{cluster_name}"
        tagged_resources = self.list_tagged_resources(project=project, query=query)
        for tagged_resource in tagged_resources:
            resources += [parse_resourcepath(tagged_resource)]
        return resources

    def list_cluster_addresses(self, project: str, cluster_name: str = "*") -> list[compute_v1.Address]:
        return [
            address
            for _, response in self.addresses_client.aggregated_list(
                request=compute_v1.AggregatedListAddressesRequest(
                    filter=f"labels.{BCM_LABEL_CLUSTER}:{cluster_name}",
                    include_all_scopes=True,
                    project=project,
                    return_partial_success=True,
                )
            )
            for address in response.addresses
        ]

    def list_cluster_forwarding_rules(self, project: str, cluster_name: str = "*") -> list[compute_v1.ForwardingRule]:
        return [
            forwarding_rule
            for _, response in self.forwarding_rules_client.aggregated_list(
                request=compute_v1.AggregatedListForwardingRulesRequest(
                    filter=f"labels.{BCM_LABEL_CLUSTER}:{cluster_name}",
                    include_all_scopes=True,
                    project=project,
                    return_partial_success=True,
                )
            )
            for forwarding_rule in response.forwarding_rules
        ]

    @catch_notfound_return_emptylist
    def get_res_instances(self, reslist: list[GCPResource]) -> list[compute_v1.Instance]:
        return [self.get_instance(project=res.project, instance_name=res.name, zone=res.zone)
                for res in reslist if res.klass == "instances"]

    @catch_notfound_return_emptylist
    def get_res_subnetworks(self, reslist: list[GCPResource]) -> list[compute_v1.Subnetwork]:
        return [self.get_subnet(project=res.project, subnet_name=res.name, region=res.region)
                for res in reslist if res.klass == "subnetworks"]

    @catch_notfound_return_emptylist
    def get_res_networks(self, reslist: list[GCPResource]) -> list[compute_v1.Network]:
        return [self.get_network(project=res.project, network_name=res.name)
                for res in reslist if res.klass == "networks"]

    @catch_notfound_return_emptylist
    def get_res_nat_gateways(self, reslist: list[GCPResource]) -> list[compute_v1.Router]:
        return [self.get_nat_gateway(project=res.project, region=res.region, nat_gateway_name=res.name)
                for res in reslist if res.klass == "routers"]

    def get_res_firewalls(self, reslist: list[GCPResource]) -> list[compute_v1.Firewall]:
        return [fw for fw in (self.get_firewall(project=res.project, firewall_name=res.name)
                for res in reslist if res.klass == "firewalls") if fw is not None]

    @catch_notfound_return_emptylist
    def get_res_service_accounts(self, reslist: list[GCPResource]) -> list[ServiceAccount]:
        return [self.get_service_account(project=res.project, account=res.name)
                for res in reslist if res.klass == "serviceAccounts"]

    def list_all_clusters(self, project: str) -> list[str]:
        tag_key = self.get_tagkey_id(project=project, tagkey=BCM_TAG_CLUSTER)
        if tag_key is None:
            raise ValueError("Expected a tag key, got None")
        return self.list_tag_short_names(tag_key)

    def filter_cluster_list(self, cluster_list: list[str], regexlist: list[str]) -> list[str]:
        return [cluster for cluster in cluster_list
                if any(re.match(regex, cluster) for regex in regexlist)]

    def start_instances(self, instances: list[GCPResource]) -> None:
        operations: list[ExtendedOperation] = []
        for instance in instances:
            try:
                op = self.instances_client.start(project=instance.project, zone=instance.zone, instance=instance.name)
            except NotFound:
                log.debug(f"Instance {instance.name!r} does not exist")
            else:
                operations.append(op)
        if operations:
            log.info("Waiting for %d instance(s) to start", len(operations))
            for op in operations:
                wait_for_extended_operation(op)

    def stop_instances(self, instances: list[GCPResource]) -> None:
        operations: list[ExtendedOperation] = []
        for instance in instances:
            try:
                op = self.instances_client.stop(project=instance.project, zone=instance.zone, instance=instance.name)
            except NotFound:
                log.debug(f"Instance {instance.name!r} does not exist")
            else:
                operations.append(op)
        if operations:
            log.info("Waiting for %d instance(s) to stop", len(operations))
            for op in operations:
                wait_for_extended_operation(op)

    def create_head_node_service_account(
        self, project: str, account_id: str, display_name: str | None = None
    ) -> ServiceAccount:
        service_account = self.create_service_account(
            project=project,
            account_id=account_id,
            service_account=ServiceAccount(display_name=display_name),
        )
        try:
            self.assign_service_account_roles(
                project=project,
                head_sa_email=service_account.email,
                resource=f"projects/{project}",
                client=self.projects_client,
                roles=[
                    "roles/cloudasset.viewer",
                    "roles/compute.admin",
                    "roles/file.editor",
                    "roles/resourcemanager.tagAdmin",
                    "roles/resourcemanager.tagUser",
                    "roles/storage.objectViewer",
                ],
            )
            self.assign_service_account_roles(
                project=project,
                head_sa_email=service_account.email,
                resource=f"projects/{project}/serviceAccounts/{service_account.email}",
                client=self.iam_client,
                roles=["roles/iam.serviceAccountUser"],
            )
        except Exception:
            self.delete_service_account(project=project, service_account=service_account)
            raise RuntimeError("Error assigning roles to service account, service account has been deleted")
        return service_account

    def create_service_account(
        self, project: str, account_id: str, service_account: ServiceAccount
    ) -> ServiceAccount:
        log.info(f"Creating service account '{account_id}@{project}.iam.gserviceaccount.com'")
        return self.iam_client.create_service_account(
            name=f"projects/{project}", account_id=account_id, service_account=service_account
        )

    def delete_service_account(self, project: str, service_account: ServiceAccount) -> None:
        log.info(f"Deleting service account {service_account.email}")
        self.remove_roles_from_sa(project, service_account.email)
        self.remove_roles_from_project(project, service_account.email)
        self.iam_client.delete_service_account(
            name=f"projects/{project}/serviceAccounts/{service_account.unique_id}"
        )

    def untag_and_delete_service_account(self, project: str, service_account: ServiceAccount) -> None:
        self.delete_service_account(project, service_account)
        self.untag_service_account(project, service_account.email, service_account.unique_id)

    @tenacity.retry(
        retry=tenacity.retry_if_exception_type(InvalidArgument),
        wait=tenacity.wait_random(min=0, max=2),
        stop=tenacity.stop_after_attempt(5),
        before_sleep=tenacity.before_sleep_log(log, logging.DEBUG),
        reraise=True,
    )
    @tenacity.retry(
        retry=tenacity.retry_if_exception_type(Aborted),
        wait=tenacity.wait_exponential(multiplier=1, min=1, max=10),
        stop=tenacity.stop_after_attempt(5),
        before_sleep=tenacity.before_sleep_log(log, logging.DEBUG),
        reraise=True,
    )
    def assign_service_account_roles(
        self,
        project: str,
        head_sa_email: str,
        resource: str,
        client: Union[iam_admin_v1.IAMClient, resourcemanager_v3.ProjectsClient],
        roles: list[str],
    ) -> None:
        """
        Assign roles to a service account at the project and service account level.

        Args:
            project_id: The ID of the project
            head_sa_email: The email of the head node service account
            resource: f"projects/{project}/serviceAccounts/{head_sa_email}" or f"projects/{project}"
            client: self.iam_client or self.projects_client
            roles: List of roles to assign to the service account
        """
        if isinstance(client, iam_admin_v1.IAMClient):
            log.debug(f"Assigning service account {head_sa_email} roles on service account {head_sa_email}: {roles}")
        else:  # project level
            log.debug(f"Assigning service account {head_sa_email} roles on project {project}: {roles}")

        options = options_pb2.GetPolicyOptions(requested_policy_version=3)
        request = iam_policy_pb2.GetIamPolicyRequest(
            resource=resource,
            options=options
        )
        current_policy = client.get_iam_policy(request=request)

        member = f"serviceAccount:{head_sa_email}"
        for role in roles:
            binding = policy_pb2.Binding(role=role, members=[member])
            current_policy.bindings.append(binding)
            log.debug(f"Adding role binding: {role} for {head_sa_email}")

        current_policy.version = 3
        set_policy_request = iam_policy_pb2.SetIamPolicyRequest(
            resource=resource,
            policy=current_policy
        )
        client.set_iam_policy(request=set_policy_request)

    def remove_roles_from_sa(self, project: str, service_account_email: str) -> None:
        """
        Remove service account roles from service account

        Args:
            project: The ID of the project
            service_account_email: The email of the primary service account
        """
        resource = f"projects/{project}/serviceAccounts/{service_account_email}"
        client = self.iam_client
        log.debug(f"Removing roles from service account: {service_account_email}")

        options = options_pb2.GetPolicyOptions(requested_policy_version=3)
        request = iam_policy_pb2.GetIamPolicyRequest(resource=resource, options=options)
        current_policy = client.get_iam_policy(request=request)

        while current_policy.bindings:
            current_policy.bindings.pop()
        current_policy.version = 3
        set_policy_request = iam_policy_pb2.SetIamPolicyRequest(
            resource=resource,
            policy=current_policy
        )
        client.set_iam_policy(request=set_policy_request)

    def remove_roles_from_project(self, project: str, service_account_email: str) -> None:
        """
        Remove service account roles from project

        Args:
            project: The ID of the project
            service_account_email: The email of the primary service account
        """
        resource = f"projects/{project}"
        client = self.projects_client
        log.debug(f"Removing {service_account_email} roles from project: {project}")

        options = options_pb2.GetPolicyOptions(requested_policy_version=3)
        request = iam_policy_pb2.GetIamPolicyRequest(resource=resource, options=options)
        current_policy = client.get_iam_policy(request=request)

        for bind in current_policy.bindings:
            if f"serviceAccount:{service_account_email}" in bind.members:
                bind.members.remove(f"serviceAccount:{service_account_email}")
        current_policy.version = 3
        set_policy_request = iam_policy_pb2.SetIamPolicyRequest(
            resource=resource,
            policy=current_policy
        )
        client.set_iam_policy(request=set_policy_request)

    def create_address(
        self, project: str, region: str, address: compute_v1.Address, labels: dict[str, str]
    ) -> compute_v1.Address:
        wait_for_extended_operation(
            self.addresses_client.insert(
                project=project,
                region=region,
                address_resource=address,
            )
        )
        address = self.addresses_client.get(project=project, region=region, address=address.name)
        try:
            log.info(f"Reserved {address.address_type} address {address.name} ({address.address})")
            return self.add_address_labels(
                project=project, region=region, address=address, labels=labels
            )
        except Exception:
            with contextlib.suppress(Exception):
                self.addresses_client.delete(project=project, region=region, address=address.name)
            raise

    def get_address(self, project: str, region: str, address_resource_name: str) -> compute_v1.Address:
        return self.addresses_client.get(
            project=project, region=region, address=address_resource_name
        )

    def delete_address(self, project: str, address: compute_v1.Address) -> ExtendedOperation:
        log.info(f"Deleting address {address.name} ({address.address})")
        return self.addresses_client.delete(
            project=project, region=address.region.split("/")[-1], address=address.name
        ) if address.region else self.global_addresses_client.delete(project=project, address=address.name)

    def add_address_labels(
        self, project: str, region: str, address: compute_v1.Address, labels: dict[str, str]
    ) -> compute_v1.Address:
        while True:
            try:
                wait_for_extended_operation(
                    self.addresses_client.set_labels(
                        project=project,
                        region=region,
                        region_set_labels_request_resource=compute_v1.RegionSetLabelsRequest(
                            label_fingerprint=address.label_fingerprint,
                            labels=dict(address.labels) | labels,
                        ),
                        resource=address.name,
                    )
                )
                return self.addresses_client.get(
                    project=project, region=region, address=address.name
                )
            except PreconditionFailed as e:
                if (
                    e.errors[0]["message"]
                    == "Labels fingerprint either invalid or resource labels have changed"
                ):
                    assert len(e.errors) == 1
                    # The label fingerprint is stale. Get the newest fingerprint and retry the
                    # request.
                    address = self.addresses_client.get(
                        project=project, region=region, address=address.name
                    )
                else:
                    raise

    def delete_forwarding_rule(
        self, project: str, forwarding_rule: compute_v1.ForwardingRule
    ) -> ExtendedOperation:
        log.info(f"Deleting forwarding rule {forwarding_rule.name}")
        return (
            self.forwarding_rules_client.delete(
                project=project,
                region=forwarding_rule.region.split("/")[-1],
                forwarding_rule=forwarding_rule.name,
            )
            if forwarding_rule.region
            else self.global_forwarding_rules_client.delete(
                project=project, forwarding_rule=forwarding_rule.name
            )
        )

    def get_forwarding_rule_tags(
        self, project: str, region: str, forwarding_rule_id: int
    ) -> ListEffectiveTagsPager:
        endpoint = get_region_api_endpoint(region)
        resource_id = build_forwarding_rule_idurl(
            project=project,
            region=region,
            forwarding_rule_id=forwarding_rule_id,
        )
        return self.get_resource_tags(endpoint=endpoint, resource_id=resource_id)

    def delete_cluster_resources(
        self,
        project: str,
        addresses: list[compute_v1.Address],
        disks: list[compute_v1.Disk],
        filestores: list[filestore_v1.Instance],
        firewalls: list[compute_v1.Firewall],
        forwarding_rules: list[compute_v1.ForwardingRule],
        instances: list[compute_v1.Instance],
        routers: list[compute_v1.Router],
        networks: list[compute_v1.Network],
        service_accounts: list[compute_v1.ServiceAccount],
        snapshots: list[compute_v1.Snapshot],
        subnetworks: list[compute_v1.Subnetwork],
        target_instances: list[compute_v1.TargetInstance],
    ) -> None:
        def delete_all(
            resources: Iterable[T], delete_fn: Callable[[T], U], executor: Executor
        ) -> Iterable[U | None]:
            def ignore_not_found(fn: Callable[[], U]) -> U | None:
                try:
                    return fn()
                except NotFound as e:
                    log.info(e)
                    return None

            return executor.map(lambda r: ignore_not_found(lambda: delete_fn(r)), resources)

        def wait_for_delete_operations(
            operations: Iterable[T | None], wait_fn: Callable[[T], None]
        ) -> None:
            operations = cast(list[T], list(filter(None, operations)))
            if len(operations) > 1:
                log.info(f"Waiting for {len(operations)} delete operations to complete")
            for operation in operations:
                wait_fn(operation)

        with ThreadPoolExecutor(max_workers=10) as executor:
            wait_for_delete_operations(
                delete_all(
                    forwarding_rules,
                    lambda forwarding_rule: self.delete_forwarding_rule(
                        project=project, forwarding_rule=forwarding_rule
                    ),
                    executor,
                ),
                lambda op: wait_for_extended_operation(op),
            )
            wait_for_delete_operations(
                delete_all(
                    target_instances,
                    lambda target_instance: self.delete_target_instance(
                        project=project, target_instance=target_instance
                    ),
                    executor,
                ),
                lambda op: wait_for_extended_operation(op),
            )
            wait_for_delete_operations(
                delete_all(
                    instances,
                    lambda instance: self.delete_instance(project=project, instance=instance),
                    executor,
                ),
                lambda op: wait_for_extended_operation(op),
            )
            wait_for_delete_operations(
                delete_all(
                    disks,
                    lambda disk: self.delete_disk(project=project, disk=disk),
                    executor,
                ),
                lambda op: wait_for_extended_operation(op),
            )
            wait_for_delete_operations(
                delete_all(
                    filestores,
                    lambda filestore: self.delete_filestore(filestore=filestore),
                    executor,
                ),
                lambda op: op.result(),  # type: ignore[no-untyped-call]
            )
            wait_for_delete_operations(
                delete_all(
                    firewalls,
                    lambda firewall: self.delete_firewall(project=project, firewall=firewall),
                    executor,
                ),
                lambda op: wait_for_extended_operation(op),
            )
            wait_for_delete_operations(
                delete_all(
                    routers,
                    lambda router: self.delete_router(project=project, router=router),
                    executor,
                ),
                lambda op: wait_for_extended_operation(op),
            )
            wait_for_delete_operations(
                delete_all(
                    snapshots,
                    lambda snapshot: self.delete_snapshot(project=project, snapshot=snapshot),
                    executor,
                ),
                lambda op: wait_for_extended_operation(op),
            )
            wait_for_delete_operations(
                delete_all(
                    addresses,
                    lambda address: self.delete_address(project=project, address=address),
                    executor,
                ),
                lambda op: wait_for_extended_operation(op),
            )
            wait_for_delete_operations(
                delete_all(
                    subnetworks,
                    lambda subnetwork: self.delete_subnetwork(
                        project=project, subnetwork=subnetwork
                    ),
                    executor,
                ),
                lambda op: wait_for_extended_operation(op),
            )
            wait_for_delete_operations(
                delete_all(
                    networks,
                    lambda network: self.delete_network(project=project, network=network),
                    executor,
                ),
                lambda op: wait_for_extended_operation(op),
            )
            delete_all(
                service_accounts,
                lambda service_account: self.untag_and_delete_service_account(
                    project=project, service_account=service_account
                ),
                executor,
            )


def parse_url(url: str) -> GCPResource:
    global_resource_regex = r"^https://www.googleapis.com/compute/v1/projects/([^/]+)/global/([^/]+)/([^/]+)$"
    region_resource_regex = r"^https://www.googleapis.com/compute/v1/projects/([^/]+)/regions/([^/]+)/([^/]+)/([^/]+)$"
    zone_resource_regex = r"^https://www.googleapis.com/compute/v1/projects/([^/]+)/zones/([^/]+)/([^/]+)/([^/]+)$"
    zone_regex = r"^https://www.googleapis.com/compute/v1/projects/([^/]+)/(zones)/([^/]+)$"
    region_regex = r"^https://www.googleapis.com/compute/v1/projects/([^/]+)/(regions)/([^/]+)$"
    service_account_regex = r"^https://www.googleapis.com/iam/v1/projects/([^/]+)/(serviceAccounts)/([^/]+)$"
    filestore_regex = r"^https://file.googleapis.com/projects/([^/]+)/locations/([^/]+)/instances/([^/]+)$"
    res = GCPResource()
    res.url = url
    if match := re.match(global_resource_regex, url):
        res.project, res.klass, res.name = match.groups()
    elif match := re.match(region_resource_regex, url):
        res.project, res.region, res.klass, res.name = match.groups()
    elif match := re.match(zone_resource_regex, url):
        res.project, res.zone, res.klass, res.name = match.groups()
    elif match := re.match(zone_regex, url):
        res.project, res.klass, res.name = match.groups()
    elif match := re.match(region_regex, url):
        res.project, res.klass, res.name = match.groups()
    elif match := re.match(service_account_regex, url):
        res.project, res.klass, res.name = match.groups()
    elif match := re.match(filestore_regex, url):
        res.project, res.region, res.name = match.groups()
        res.klass = "filestores"
    else:
        raise RuntimeError(f"Invalid GCP resource URI: {url!r}")
    return res


def parse_resourcepath(path: str) -> GCPResource:
    if match := re.match(r"^.*\/iam.googleapis.com(/projects\/.*)", path):
        return parse_url("https://www.googleapis.com/iam/v1" + match.group(1))
    elif match := re.match(r"^.*\/file.googleapis.com(/projects\/.*)", path):
        return parse_url("https://file.googleapis.com" + match.group(1))
    elif match := re.match(r"^.*(\/projects\/.*)", path):
        return parse_url("https://www.googleapis.com/compute/v1" + match.group(1))
    elif path.startswith("projects/"):
        # FIXME(kal): Should not assume "compute".
        return parse_url("https://www.googleapis.com/compute/v1/" + path)
    else:
        raise RuntimeError(f"Invalid GCP resource path: {path}")


def wait_for_extended_operation(operation: ExtendedOperation, timeout: int = 300,
                                ignore_warning_codes: Optional[List[str]] = None) -> Any:
    result = operation.result(timeout=timeout)  # type: ignore[no-untyped-call]
    if operation.error_code:
        log.error(f"Operation: [Code: {operation.error_code}]: {operation.error_message}")
        log.error(f"Operation ID: {operation.name}")
        raise operation.exception() or RuntimeError(  # type: ignore[no-untyped-call]
            operation.error_message
        )

    if operation.warnings:
        for warning in operation.warnings:
            if ignore_warning_codes:
                if warning.code not in ignore_warning_codes:
                    log.warning(f"Operation: [Code: {warning.code}]: {warning.message}")
    return result


def shorten_location_name(location: str) -> str:
    substitutions = {
        'northamerica': 'na', 'southamerica': 'sa', 'australia': 'au', 'europe': 'eu', 'central': 'c',
        'northeast': 'ne', 'southeast': 'se', 'southwest': 'sw', 'north': 'n', 'south': 's', 'east': 'e',
        'west': 'w', 'africa': 'af', 'asia': 'as', 'me': 'me'
    }

    for full, abbr in substitutions.items():
        location = location.replace(full, abbr)

    return location


def is_bcm_network(network_name: str) -> bool:
    return bool(re.search(f"{BCM_NETWORK_SUFFIX}$", network_name))


def network_name_to_cluster_name(network_name: str) -> str:
    assert is_bcm_network(network_name), f"{network_name!r} is not a BCM network"
    return re.sub(f"{BCM_NETWORK_SUFFIX}$", "", network_name)


def cluster_name_to_network_name(cluster_name: str) -> str:
    return cluster_name + BCM_NETWORK_SUFFIX


def cluster_name_to_router_name(cluster_name: str) -> str:
    return cluster_name + BCM_ROUTER_SUFFIX


def cluster_name_to_gateway_name(cluster_name: str) -> str:
    return cluster_name + BCM_GATEWAY_SUFFIX


def get_cluster_fw_name(cluster_name: str, zone: str) -> str:
    shortened_zone = shorten_location_name(zone)
    return f"{cluster_name}-{shortened_zone}-bcm"


def get_instance_network(instance: compute_v1.Instance) -> str:
    return instance.network_interfaces[0].network


def get_instance_ips(instance: compute_v1.Instance) -> InstanceIpAddresses:
    """
    Retrieve the internal and external IP addresses of a given GCP computeinstance.

    This function examines the network interfaces of the provided GCP compute instance to determine
    its internal and external IP addresses. It returns an `InstanceIpAddressType`
    namedtuple with fields INTERNAL and EXTERNAL.

    Args:
        instance (compute_v1.Instance): The gcp compute instance whose IP addresses are to be retrieved.

    Returns:
        InstanceIpAddresses: A Class containg a list of both internal and external IP addresses.

    Example:
        >>> class MockAccessConfig:
        ...     def __init__(self, type, nat_i_p):
        ...        self.type = type
        ...        self.nat_i_p = InstanceIpAddresses.from_str(nat_i_p)

        >>> class MockNetworkInterface:
        ...     def __init__(self, network_i_p, access_configs):
        ...        self.network_i_p = InstanceIpAddresses.from_str(network_i_p)
        ...        self.access_configs = access_configs

        >>> class MockInstance:
        ...     def __init__(self, network_interfaces: List[MockNetworkInterface]):
        ...        self.network_interfaces = network_interfaces

        >>> instance = MockInstance([
        ...     MockNetworkInterface(network_i_p="10.0.0.2", access_configs=[]),
        ...     MockNetworkInterface(network_i_p="192.168.1.1", access_configs=[
        ...        MockAccessConfig('ONE_TO_ONE_NAT', "192.0.0.9"),
        ...     ])
        ... ])
        >>> ip_type = get_instance_ips(instance)
        >>> ip_type.internal_ips()
        [IPv4Address('10.0.0.2'), IPv4Address('192.168.1.1')]
        >>> ip_type.external_ips()
        [IPv4Address('192.0.0.9')]
    """

    if not instance.network_interfaces:
        return InstanceIpAddresses(None)

    private_ips = InstanceIpAddresses.from_list([nic.network_i_p for nic in instance.network_interfaces])

    public_ips = InstanceIpAddresses.from_list([config.nat_i_p for nic in instance.network_interfaces for
                                               config in nic.access_configs if config.type == "ONE_TO_ONE_NAT"
                                               and config.nat_i_p])

    all_addresses = [address for ip_list in [private_ips, public_ips] for address in ip_list]

    return InstanceIpAddresses(addresses=all_addresses)


def instance_in_network(instance: compute_v1.Instance, network: compute_v1.Network) -> bool:
    return any(parse_url(nic.network).name == network.name
               for nic in instance.network_interfaces)


def instance_in_cluster(resources: list[GCPResource], instance: compute_v1.Instance) -> bool:
    return any(instance.self_link == resource.url for resource in resources)


def get_zone_api_endpoint(zone: str) -> str:
    return f"{zone}-cloudresourcemanager.googleapis.com"


def get_region_api_endpoint(region: str) -> str:
    return f"{region}-cloudresourcemanager.googleapis.com"


def zone_to_region(zone: str) -> str:
    return zone[: zone.rindex("-")]


def build_sa_idurl(project: str, sa_id: str) -> str:
    return f'//iam.googleapis.com/projects/{project}/serviceAccounts/{sa_id}'


def build_sa_nameurl(project: str, sa_name: str) -> str:
    return f'//iam.googleapis.com/projects/{project}/serviceAccounts/{sa_name}'


def build_disk_idurl(project: str, zone: str, _id: int) -> str:
    return f'//compute.googleapis.com/projects/{project}/zones/{zone}/disks/{_id}'


def build_filestore_idurl(name: str) -> str:
    return f"//{GCP_FILE_SERVICE}/{name}"


def build_forwarding_rule_idurl(project: str, region: str, forwarding_rule_id: int) -> str:
    return f'//compute.googleapis.com/projects/{project}/regions/{region}/forwardingRules/{forwarding_rule_id}'


def build_instance_idurl(project: str, zone: str, instance_id: int) -> str:
    return f'//compute.googleapis.com/projects/{project}/zones/{zone}/instances/{instance_id}'


def build_instance_nameurl(project: str, zone: str, instance_name: str) -> str:
    return f'//compute.googleapis.com/projects/{project}/zones/{zone}/instances/{instance_name}'


def build_network_idurl(project: str, network_id: int) -> str:
    return f'//compute.googleapis.com/projects/{project}/global/networks/{network_id}'


def build_network_nameurl(project: str, network_name: str) -> str:
    return f'//compute.googleapis.com/projects/{project}/global/networks/{network_name}'


def build_subnetwork_idurl(project: str, region: str, subnetwork_id: int) -> str:
    return f'//compute.googleapis.com/projects/{project}/regions/{region}/subnetworks/{subnetwork_id}'


def build_subnetwork_nameurl(project: str, region: str, subnetwork_name: str) -> str:
    return f'//compute.googleapis.com/projects/{project}/regions/{region}/subnetworks/{subnetwork_name}'


def build_nat_gateway_idurl(project: str, region: str, nat_gateway_id: int) -> str:
    return f'//compute.googleapis.com/projects/{project}/regions/{region}/routers/{nat_gateway_id}'


def build_nat_gateway_nameurl(project: str, region: str, nat_gateway_name: str) -> str:
    return f'//compute.googleapis.com/projects/{project}/regions/{region}/routers/{nat_gateway_name}'


def build_firewall_idurl(project: str, firewall_id: int) -> str:
    return f'//compute.googleapis.com/projects/{project}/global/firewalls/{firewall_id}'


def build_firewall_nameurl(project: str, firewall_name: str) -> str:
    return f'//compute.googleapis.com/projects/{project}/global/firewalls/{firewall_name}'


def build_snapshot_idurl(project: str, _id: int) -> str:
    return f'//compute.googleapis.com/projects/{project}/global/snapshots/{_id}'


def build_subnetwork_id(project: str, region: str, subnetwork: str) -> str:
    return f"projects/{project}/regions/{region}/subnetworks/{subnetwork}"


def build_target_instance_idurl(project: str, zone: str, _id: int) -> str:
    return f'//compute.googleapis.com/projects/{project}/zones/{zone}/targetInstances/{_id}'


def parse_filestore_url(url: str) -> str:
    FILESTORE_REGEX = r"^https://file.googleapis.com/(.+)$"
    if match := re.match(FILESTORE_REGEX, url):
        return match.group(1)
    else:
        raise RuntimeError(f"Invalid GCP Filestore URI: {url!r}")


def _parse_blob_url(url: str) -> tuple[str, str]:
    # https://storage.googleapis.com/bucket-name/images/bcmh-ubuntu2204-trunk-785
    STORAGE_BLOB_REGEX_1 = r"^https://storage.googleapis.com/([^/]+)/(\S+)$"
    # https://www.googleapis.com/storage/v1/b/bucket-name/o/bcmh-ubuntu2204-trunk-785
    STORAGE_BLOB_REGEX_2 = r"^https://www.googleapis.com/storage/v1/b/([^/]+)/o/(\S+)$"

    if match := re.match(STORAGE_BLOB_REGEX_1, url):
        bucket_name, blob_path = match.groups()
        return bucket_name, blob_path
    elif match := re.match(STORAGE_BLOB_REGEX_2, url):
        bucket_name, blob_path = match.groups()
        return bucket_name, urllib.parse.unquote(blob_path)
    else:
        return "", ""


def is_blob_url(image_url: str) -> bool:
    bucket_name, blob_path = _parse_blob_url(image_url)
    return bool(bucket_name and blob_path)


def is_resource_url(resource_url: str) -> bool:
    try:
        return bool(parse_url(resource_url))
    except RuntimeError:
        return False
