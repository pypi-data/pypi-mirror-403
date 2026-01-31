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
import re

import netaddr
import tenacity
import yaml
from google.api_core.exceptions import AlreadyExists, Conflict
from google.cloud import compute_v1

import clusterondemand.clustercreate
import clusterondemand.configuration
import clusterondemand.copyfile
from clusterondemand.cidr import cidr
from clusterondemand.cloudconfig import build_cloud_config
from clusterondemand.clustercreate import validate_inbound_rules
from clusterondemand.clusternameprefix import must_start_with_cod_prefix
from clusterondemand.exceptions import CODException, ValidationException
from clusterondemand.images.find import CODImage
from clusterondemand.images.find import pickimages_ns as common_pickimages_ns
from clusterondemand.inbound_traffic_rule import InboundTrafficRule
from clusterondemand.node_definition import NodeDefinition
from clusterondemand.paramvalidation import ParamValidator
from clusterondemand.ssh import clusterssh_ns
from clusterondemand.summary import SummaryType
from clusterondemand.tags import tags_ns
from clusterondemand.utils import cod_log
from clusterondemand.wait_helpers import clusterwaiters_ns, wait_for_cluster
from clusterondemandconfig import (
    ConfigNamespace,
    config,
    may_not_equal_none,
    number_greater_equal,
    number_must_be_between,
    requires_other_parameter_to_be_set
)
from clusterondemandconfig.configuration import ConfigurationView
from clusterondemandconfig.parameter import Parameter
from clusterondemandgcp.clusterlist import HEAD_A_SUFFIX
from clusterondemandgcp.images import IMAGE_NAME_REGEX_GCP, GCPImageSource

from . import clientutils
from .brightsetup import generate_bright_setup
from .clientutils import (
    BCM_EXTERNAL_ADDRESS_SUFFIX,
    BCM_INTERNAL_ADDRESS_SUFFIX,
    BCM_LABEL_CLUSTER,
    BCM_LABEL_HEAD_NODE,
    BCM_SUBNET_SUFFIX
)
from .configuration import gcpcommon_ns
from .summary import GCPSummaryGenerator

log = logging.getLogger("cluster-on-demand")

NODE_DISK_SETUP = """
<?xml version='1.0' encoding='ISO-8859-1'?>
<!-- COD GCP specific disksetup -->
<!-- Just a single xfs partition -->
<diskSetup xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance'>
  <device>
    <blockdev>/dev/disk/by-id/google-persistent-disk-1</blockdev>
    <partition id='a2'>
      <size>max</size>
      <type>linux</type>
      <filesystem>xfs</filesystem>
      <mountPoint>/</mountPoint>
      <mountOptions>defaults,noatime,nodiratime</mountOptions>
    </partition>
  </device>
</diskSetup>
"""


def _region_to_multiregion(region: str) -> str:
    """
    Determines the multiregion which 'region' belongs to, according to the GCP bucket locations described in
    https://cloud.google.com/storage/docs/locations#location-dr. If the region does not match a multi-region,
    it is returned unchanged.
    """
    if region is None:
        return None
    multiregions = ('asia', 'eu', 'us')
    for mr in multiregions:
        if region.lower().startswith(mr):
            return mr
    return region


def _validate_headnode_image(parameter: Parameter, config: ConfigurationView) -> None:
    value = config[parameter.key]
    if (
        not value
        or re.fullmatch(IMAGE_NAME_REGEX_GCP, value)
        or clientutils.is_blob_url(value)
        or clientutils.is_resource_url(value)
    ):
        return

    raise ValidationException(
        f"'{value}' does not seem to be a valid head node image. "
        "Expected image name with format bcmh-<distro>-<bcm version>-<n>-<arch>, e.g. "
        "'bcmh-ubuntu2204-trunk-113-x86-64' OR image UUID with format "
        "'https://www.googleapis.com/storage/v1/b/<bucket-name>/o/bcmh-ubuntu2204-trunk-113-x86-64."
        "tar.gz' OR 'https://www.googleapis.com/compute/v1/projects/<project-id>/global/images/"
        "bcmh-ubuntu2204-trunk-113-x86-64'"
    )


config_ns = ConfigNamespace("gcp.cluster.create", "cluster creation parameters")
config_ns.import_namespace(gcpcommon_ns)
config_ns.import_namespace(clusterondemand.configuration.clustercreate_ns)
config_ns.override_imported_parameter(name="healthchecks_to_disable", default=["defaultgateway"])
config_ns.import_namespace(clusterondemand.configuration.clustercreatename_ns)
config_ns.import_namespace(clusterondemand.configuration.node_disk_setup_ns)
config_ns.import_namespace(clusterssh_ns)
config_ns.import_namespace(clusterwaiters_ns)
config_ns.import_namespace(clusterondemand.configuration.append_to_bashrc_ns)
config_ns.import_namespace(clusterondemand.configuration.resolve_hostnames_ns)
config_ns.import_namespace(clusterondemand.configuration.cmd_debug_ns)
config_ns.import_namespace(clusterondemand.copyfile.copyfile_ns)
config_ns.import_namespace(clusterondemand.configuration.timezone_ns)
config_ns.import_namespace(clusterondemand.configuration.sshconfig_ns)
config_ns.import_namespace(tags_ns)

config_ns.remove_imported_parameter("name")
config_ns.add_parameter(
    "name",
    help="Name of the cluster to create",
    validation=[may_not_equal_none, must_start_with_cod_prefix]
)
config_ns.add_parameter(
    "subnet_cidr",
    default=cidr("10.142.0.0/17"),
    help="CIDR range of the subnet; only used when COD is creating a subnet.",
    parser=cidr,
)
config_ns.add_parameter(
    "mtu",
    default=1460,
    help="MTU size to be configured for a new VPC Network. This does NOT apply to existing VPCs.",
    help_varname="MTU",
    type=int,
    validation=[number_must_be_between(1300, 8896)],  # the limits are taken from compute_v1.Network description
)
config_ns.override_imported_parameter(
    "head_node_type",
    help="Instance type for the head node",
    validation=may_not_equal_none,
)
config_ns.override_imported_parameter(
    "node_type",
    help="Instance type for compute nodes",
    validation=may_not_equal_none,
)
config_ns.override_imported_parameter(
    "head_node_root_volume_size",
    # Limits reference: https://cloud.google.com/compute/docs/disks
    validation=[may_not_equal_none, number_must_be_between(10, 65536)],
)
config_ns.add_parameter(
    "node_disk_provisioned_iops",
    help="I/O operations per second that node disks can handle.",
    default=None,
    type=int,
    advanced=False,
)
config_ns.add_parameter(
    "node_disk_provisioned_throughput",
    help="Throughput (in MB/s) that node disks can handle.",
    default=None,
    type=int,
    advanced=False,
    validation=number_greater_equal(1),
)
config_ns.add_parameter(
    "node_disk_type",
    help="Disk type to use for cnodes (e.g. 'hyperdisk-balanced').",
    default=None,
    advanced=False,
)
config_ns.add_parameter(
    "node_root_volume_size",
    default=50,
    help="Node root disk size in GB.",
    help_varname="SIZE_IN_GB",
    type=int,
    validation=[may_not_equal_none, number_must_be_between(10, 65536)],
)
config_ns.override_imported_parameter(
    "node_disk_setup",
    default=NODE_DISK_SETUP,
)
config_ns.add_parameter(
    "node_service_account",
    help="Email of the service account to attach to cnodes.",
    validation=requires_other_parameter_to_be_set("head_node_service_account")
)
config_ns.add_parameter(
    "network_name",
    help="Name of the existing GCP network to create the cluster in. Network resources from other "
    "projects may be specified in the format: projects/{project}/global/networks/{network}.",
    advanced=False,
)
config_ns.add_parameter(
    "head_node_nic_type",
    help="The type of network interface to use for the head node.",
    default="GVNIC",
    advanced=False,
    choices=["GVNIC", "VIRTIO_NET"],
)
config_ns.add_parameter(
    "head_node_disk_provisioned_iops",
    help="I/O operations per second that head node disks can handle.",
    default=None,
    type=int,
    advanced=False,
)
config_ns.add_parameter(
    "head_node_disk_provisioned_throughput",
    help="Throughput (in MB/s) that head node disks can handle.",
    default=None,
    type=int,
    advanced=False,
    validation=number_greater_equal(1),
)
config_ns.add_parameter(
    "head_node_disk_type",
    help="Disk type to use for head nodes (e.g. 'hyperdisk-balanced').",
    default=None,
    advanced=False,
)
config_ns.add_parameter(
    "head_node_service_account",
    help="Email of the service account to attach to head nodes.",
)
config_ns.add_parameter(
    "head_node_zone",
    default=None,
    help="Name of the zone for the head node (e.g. 'europe-west4-c').",
    validation=may_not_equal_none
)
config_ns.add_parameter(
    "image_storage_location",
    help="Storage location of new images (e.g. 'eu', 'us' or a region name). "
    "If unset, the multi-region near the head node region is used (e.g. 'us' for 'us-west4'). "
    "If no multi-region can be inferred, the head node region is used.",
    default=lambda _, configuration: _region_to_multiregion(
        clientutils.zone_to_region(configuration["head_node_zone"])
        if configuration["head_node_zone"]
        else ""
    ),
    validation=may_not_equal_none,
)
config_ns.add_parameter(
    "subnet_name",
    help="Name of the existing GCP subnet to create the cluster in. Subnet resources from other "
    "projects may be specified in the format: projects/{project}/regions/{region}/subnetworks/{subnet}.",
    advanced=False,
    validation=requires_other_parameter_to_be_set("network_name"),
)
config_ns.add_switch_parameter(
    "create_public_ip",
    advanced=True,
    default=True,
    help="Create a public IP for the head node.  Use --no-create-public-ip to skip creating one. In that case, to "
         "have access to the cluster, a jumpbox will need to be created in the same network as the head node."
)
config_ns.override_imported_parameter("on_error", default="cleanup")

pickimages_ns = ConfigNamespace("gcp.images.pick", help_section="image selection parameters")
pickimages_ns.import_namespace(common_pickimages_ns)
pickimages_ns.remove_imported_parameter("image")
pickimages_ns.remove_imported_parameter("node_image")
pickimages_ns.override_imported_parameter(
    "head_node_image",
    help="Image name or URL to be used for the head node",
    help_varname=None,  # default
    validation=_validate_headnode_image,
)
pickimages_ns.override_imported_parameter("cloud_type", default="gcp")
pickimages_ns.override_imported_parameter("version", default="11.0")
config_ns.import_namespace(pickimages_ns)


def _print_overview(image: CODImage) -> None:
    head_node_definition = NodeDefinition(count=1, flavor=config["head_node_type"])
    node_definition = NodeDefinition(count=config["nodes"], flavor=config["node_type"])
    network_name = config["network_name"] or clientutils.cluster_name_to_network_name(config["name"])

    generator = GCPSummaryGenerator(
        project=config["project_id"],
        region=clientutils.zone_to_region(config["head_node_zone"]),
        zone=config["head_node_zone"],
        serviceaccount=(
            config["head_node_service_account"] or
            f"{config['name']}@{config['project_id']}.iam.gserviceaccount.com"
        ),
        image=image,
        head_name=config["name"],
        summary_type=SummaryType.Proposal,
        config=config,
        head_node_definition=head_node_definition,
        head_image=None,
        node_definition=node_definition,
        network=network_name,
    )
    generator.print_summary(log.info)


def _generate_instance_metadata(
    image: CODImage,
    subnet_id: str,
    subnet_cidr: str,
    mtu: int
) -> compute_v1.Metadata:
    bright_setup = generate_bright_setup(
        cluster_name=config["name"],
        subnet_id=subnet_id,
        subnet_cidr=subnet_cidr,
        mtu=mtu,
    )

    cloud_config = build_cloud_config(
        cm_bright_setup_conf=bright_setup, version=config["version"], distro=image.distro
    )

    user_data = "#cloud-config\n" + yaml.safe_dump(cloud_config.to_dict())
    return compute_v1.Metadata(
        items=[
            compute_v1.Items(key="serial-port-enable", value="true"),
            compute_v1.Items(key="user-data", value=user_data),
            compute_v1.Items(key="vmDnsSetting", value="ZonalOnly"),
        ]
    )


def _validate_cluster_name() -> None:
    ParamValidator.validate_cluster_name(config["name"], config["validate_max_cluster_name_length"])


def _wait_until_image_is_ready(
        client: clientutils.GCPClient,
        cod_image: CODImage,
        project: str
) -> compute_v1.Image:
    image_rsrc = clientutils.parse_url(cod_image.uuid)

    @tenacity.retry(
        retry=tenacity.retry_if_not_result(lambda image: image),
        stop=tenacity.stop_after_delay(600),
        wait=tenacity.wait_fixed(10),
        reraise=True,
    )
    def get_ready_image() -> compute_v1.Image | None:
        gcp_image = client.get_disk_image_uncached(image_rsrc.name, project=image_rsrc.project)
        if not gcp_image:
            raise RuntimeError(f"Unable to find image {cod_image.name!r}")
        if gcp_image.status == "READY":
            log.debug(f"Image {cod_image.name!r} is ready")
            return gcp_image
        elif gcp_image.status == "PENDING":
            log.debug(f"Awaiting image {cod_image.name!r} to get ready")
            return None
        raise Exception(f"Unexpected image status: {gcp_image.status!r}")

    gcp_image = get_ready_image()
    assert gcp_image  # to shut up mypy
    return gcp_image


def _create_image_from_blob(
        client: clientutils.GCPClient,
        cod_image: CODImage,
        project: str,
        image_location: str,
) -> str:
    """
    If `cod_image` refers to an image blob in a cloud storage bucket, create create a GCP image in our account from it.
    Otherwise (if `cod_image` refers to an existing GCP image) wait until it's ready (if needed).
    """
    if not clientutils.is_blob_url(cod_image.uuid):
        # Use an existing GCE image. Make sure it's ready in case if the image is being created elsewhere.
        log.info(f"Using existing image {cod_image.name!r}, awaiting it to get ready")
        _wait_until_image_is_ready(client, cod_image, project)
        return cod_image.uuid

    # Create a GCP image in our account out of the blob.
    blob_url: str = cod_image.uuid
    if not (blob := client.get_blob_by_url(blob_url)):
        raise RuntimeError(f"Unable to find image blob {blob_url!r}")
    log.info(f"Creating image {cod_image.name!r} from blob {blob_url!r} in {image_location!r}")
    try:
        gcp_image = client.create_image(
            project,
            image_name=cod_image.name,
            blob_url=blob_url,
            labels=blob.metadata,  # "bcm_api_hash", etc
            location=image_location,
            arch=cod_image.arch,
        )
    except Conflict as e:
        log.debug(f"Image creation conflict detected: {e}")  # creation has just been initiated elsewhere
        gcp_image = _wait_until_image_is_ready(client, cod_image, project)
    else:
        log.debug(f"Created image {cod_image.name!r} from blob {blob_url!r}")

    assert gcp_image
    return gcp_image.self_link


def _rollback_cluster(
        client: clientutils.GCPClient,
        project: str,
        cluster_name: str,
        tagpairs: dict[tuple[str, str], tuple[str, str]],
        bcm_addresses: list[compute_v1.Address],
        bcm_firewalls: list[compute_v1.Firewall],
        bcm_instances: list[compute_v1.Instance],
        bcm_networks: list[compute_v1.Network],
        bcm_routers: list[compute_v1.Router],
        bcm_service_accounts: list[compute_v1.ServiceAccount],
        bcm_subnetworks: list[compute_v1.Subnetwork],
) -> None:
    client.delete_cluster_resources(
        project=project,
        addresses=bcm_addresses,
        disks=[],
        filestores=[],
        firewalls=bcm_firewalls,
        forwarding_rules=[],
        instances=bcm_instances,
        networks=bcm_networks,
        routers=bcm_routers,
        service_accounts=bcm_service_accounts,
        snapshots=[],
        subnetworks=bcm_subnetworks,
        target_instances=[],
    )

    cluster_tagpair = {k: v for k, v in tagpairs.items() if k[0] == clientutils.BCM_TAG_CLUSTER}
    for _, tag_id in cluster_tagpair.values():
        client.delete_tagvalue_by_id(tag_id)
    raise RuntimeError("Cluster creation failed, please see details above.")


def run_command() -> None:
    project = config["project_id"]
    region = clientutils.zone_to_region(config["head_node_zone"])
    zone = config["head_node_zone"]
    cluster_name = config["name"]
    instance_name = f"{cluster_name}{HEAD_A_SUFFIX}"
    subnet_cidr = config["subnet_cidr"]
    fw_name = clientutils.get_cluster_fw_name(cluster_name, zone)
    inbound_rules = InboundTrafficRule.process_inbound_rules(config["inbound_rule"])
    ingress_icmp = [str(cidr) for cidr in config["ingress_icmp"] or []]
    instance_type = config["head_node_type"]
    create_public_ip = config['create_public_ip']
    network_interface_type = config['head_node_nic_type']
    mtu = config["mtu"]
    # TODO: Validate configuration ASAP to prevent mid-deployment failures.

    client = clientutils.GCPClient.from_config()

    if create_public_ip:
        validate_inbound_rules(inbound_rules=inbound_rules)

    # Ensure that the machine type and selected architecture match
    # We may also infer the architecture from the head node machine type if not specified in the config
    config['arch'] = client.validate_instance_types_arch(zone, config["head_node_type"], config["arch"], 'head node')
    client.validate_instance_types_arch(zone, config["node_type"], config["arch"], 'compute node')

    # Ensure name is valid and there is no existing cluster with the same name
    _validate_cluster_name()
    if not client.validate_cluster_name(cluster_name):
        raise CODException(
            "Cluster name must start with a lower case letter, contain only lowercase letters, numbers and hyphens "
            "and cannot end with a hypthen. Max length is 40 characters including COD prefix."
        )

    if client.cluster_exists(project, cluster_name):
        raise CODException(
            f"A cluster with the name '{config['name']}' already exists, please choose a different cluster name."
        )

    # Check for existing resources early before creating other resources.

    if existing_network_name := config.get("network_name"):
        try:
            if "/" in existing_network_name:
                network_path = clientutils.parse_resourcepath(existing_network_name)
                network = client.get_network(project=network_path.project, network_name=network_path.name)
            else:
                network = client.get_network(project=project, network_name=existing_network_name)
        except Exception as e:
            raise RuntimeError(f"Network '{existing_network_name}' not found: {e}")
        mtu = network.mtu

    if existing_subnet_name := config.get("subnet_name"):
        try:
            if "/" in existing_subnet_name:
                subnet_path = clientutils.parse_resourcepath(existing_subnet_name)
                subnet = client.get_subnet(
                    project=subnet_path.project, region=subnet_path.region, subnet_name=subnet_path.name
                )
                subnet_id = existing_subnet_name
            else:
                subnet = client.get_subnet(project=project, region=region, subnet_name=existing_subnet_name)
                subnet_id = clientutils.build_subnetwork_id(project, region, subnet.name)
            subnet_cidr = netaddr.IPNetwork(subnet.ip_cidr_range)
        except Exception as e:
            raise RuntimeError(f"Subnet '{existing_subnet_name}' not found: {e}")
        log.info(
            "Cluster is being created within an existing subnet; we assume that the user manages the "
            "network resources, including firewalls and public IPs."
        )
    else:
        subnet_id = clientutils.build_subnetwork_id(project, region, f"{cluster_name}{BCM_SUBNET_SUFFIX}")

    head_sa_email = config["head_node_service_account"] or f"{cluster_name}@{project}.iam.gserviceaccount.com"
    head_sa_name, head_sa_project = clientutils.parse_service_account_email(head_sa_email)

    if node_sa_email := config["node_service_account"]:
        node_sa_name, node_sa_project = clientutils.parse_service_account_email(node_sa_email)

    # If using an existing service account, check that it exists.
    if config["head_node_service_account"]:
        client.get_service_account(head_sa_project, head_sa_email)
    if node_sa_email and node_sa_email != head_sa_email:
        client.get_service_account(node_sa_project, node_sa_email)

    # If the user has specified an image, use it, or else use the newest image.
    cod_image = GCPImageSource.pick_head_node_image_using_options(config)

    instance_metadata = _generate_instance_metadata(cod_image, subnet_id, str(subnet_cidr), mtu)

    _print_overview(cod_image)
    if config["ask_to_confirm_cluster_creation"]:
        clusterondemand.utils.confirm_cluster_creation()

    # Create new resource tagkeys and values if necessary
    client.ensure_tagkeys_exist(project)  # Only needed to create BURSTING TAG. Is that really needed?
    standard_tags = {clientutils.BCM_TAG_CLUSTER: {cluster_name}}
    standard_tags_names_to_ids = client.resolve_and_create_missing_tags(standard_tags, project)

    try:
        bcm_addresses: list[compute_v1.Address] = []
        bcm_firewalls: list[compute_v1.Firewall] = []
        bcm_instances: list[compute_v1.Instance] = []
        bcm_networks: list[compute_v1.Network] = []
        bcm_routers: list[compute_v1.Router] = []
        bcm_service_accounts: list[compute_v1.ServiceAccount] = []
        bcm_subnetworks: list[compute_v1.Subnetwork] = []

        if not config["head_node_service_account"]:
            try:
                head_node_service_account = client.create_head_node_service_account(
                    project=head_sa_project,
                    account_id=head_sa_name,
                    display_name=f"{clientutils.BCM_HEAD_SA_DISPLAY_NAME} for {cluster_name}",
                )
                bcm_service_accounts.append(head_node_service_account)
                client.tag_service_account(
                    project=project,
                    sa_id=head_node_service_account.unique_id,
                    sa_name=head_sa_email,
                    tagpairs=standard_tags_names_to_ids
                )
            except AlreadyExists:
                raise RuntimeError(f"Service account '{head_sa_email}' already exists.")

        if not existing_network_name:
            # Create the network
            network = client.create_network(
                project=project, network_name=clientutils.cluster_name_to_network_name(cluster_name), mtu=mtu,
            )
            bcm_networks.append(network)
            client.tag_network(
                project=project,
                network_id=network.id,
                network_name=network.name,
                tagpairs=standard_tags_names_to_ids,
            )

        if not existing_subnet_name:
            # Create the subnet
            subnet = client.create_subnet(
                project=project,
                region=region,
                network=network,
                subnet_name=subnet_id.split("/")[-1],
                subnet_cidr=str(subnet_cidr),
            )
            bcm_subnetworks.append(subnet)
            client.tag_subnet(
                project=project,
                subnet_id=subnet.id,
                subnet_name=subnet.name,
                region=region,
                tagpairs=standard_tags_names_to_ids,
            )

            # Create cloud NAT gateway
            nat_gateway = client.create_nat_gateway(project=project, region=region, network=network,
                                                    cluster_name=cluster_name)
            bcm_routers.append(nat_gateway)
            client.tag_nat_gateway(
                project=project,
                nat_gateway_id=nat_gateway.id,
                nat_gateway_name=nat_gateway.name,
                region=region,
                tagpairs=standard_tags_names_to_ids,
            )

            # Create internal firewall
            internal_fw_rules = [InboundTrafficRule(f"{subnet_cidr},0-65535:TCP"),
                                 InboundTrafficRule(f"{subnet_cidr},0-65535:UDP")]
            internal_fw_rule_name = f"{subnet.name}-int"
            internal_firewalls = client.create_fws(
                project=project, fw_nameprefix=internal_fw_rule_name, network=network,
                target_tags=[], inbound_rules=internal_fw_rules,
                ingress_icmp=[str(subnet_cidr)]
            )
            bcm_firewalls += internal_firewalls
            client.tag_firewalls(
                project=project, firewalls=internal_firewalls, tagpairs=standard_tags_names_to_ids,
            )

            if create_public_ip:
                # Create external firewall
                external_firewalls = client.create_fws(
                    project=project,
                    fw_nameprefix=fw_name,
                    network=network,
                    target_tags=[clientutils.BCM_NETWORKTAG_HEADNODE],
                    inbound_rules=inbound_rules,
                    ingress_icmp=ingress_icmp,
                )
                bcm_firewalls += external_firewalls
                client.tag_firewalls(
                    project=project,
                    firewalls=external_firewalls,
                    tagpairs=standard_tags_names_to_ids,
                )

        # Create head node image if needed.
        image_uri = _create_image_from_blob(client, cod_image, project, config["image_storage_location"])

        cluster_label = {BCM_LABEL_CLUSTER: cluster_name}

        # Create head node private address
        internal_address = client.create_address(
            project=project,
            region=region,
            address=compute_v1.Address(
                address_type="INTERNAL",
                name=instance_name + BCM_INTERNAL_ADDRESS_SUFFIX,
                subnetwork=subnet.self_link,
            ),
            labels=cluster_label,
        )
        bcm_addresses.append(internal_address)

        # Create head node public address
        access_configs = []
        if create_public_ip:
            external_address = client.create_address(
                project=project,
                region=region,
                address=compute_v1.Address(
                    name=instance_name + BCM_EXTERNAL_ADDRESS_SUFFIX,
                    # FIXME: Make network tier configurable?
                    network_tier="STANDARD",
                ),
                labels=cluster_label,
            )
            bcm_addresses.append(external_address)
            access_configs = [
                compute_v1.AccessConfig(
                    name="External NAT",
                    nat_i_p=external_address.address,
                    network_tier=external_address.network_tier,
                )
            ]

        # Create head node instance.
        head_node_instance = client.create_instance(
            project,
            region,
            zone,
            instance_name,
            instance_type,
            instance_metadata,
            head_sa_email,
            image_uri,
            disk_provisioned_iops=config["head_node_disk_provisioned_iops"],
            disk_provisioned_throughput=config["head_node_disk_provisioned_throughput"],
            disk_size=config["head_node_root_volume_size"],
            disk_type=config["head_node_disk_type"],
            hostname=cluster_name,
            network_interfaces=[
                compute_v1.NetworkInterface(
                    access_configs=access_configs,
                    network=network.self_link,
                    network_i_p=internal_address.address,
                    nic_type=network_interface_type,
                    subnetwork=subnet.self_link,
                )
            ],
            arch=config["arch"],
            tagpairs=standard_tags_names_to_ids,
            labels=cluster_label | {BCM_LABEL_HEAD_NODE: "a"},
        )
        bcm_instances.append(head_node_instance)

        instance_ip = clientutils.get_instance_ips(head_node_instance).first_usable_ip()
        if config['create_public_ip']:
            log.info("Head node IP: %s" % instance_ip)
        else:
            log.info("Cluster was created without a public IP. COD cannot wait for cmdaemon to be ready.")
            log.info("Head node private IP: %s", instance_ip)

    except Exception as error:
        log.error("The following error occurred while creating the cluster")
        log.error(error)
        if config["on_error"] == "cleanup":
            _rollback_cluster(
                client,
                project,
                cluster_name,
                standard_tags_names_to_ids,
                bcm_addresses=bcm_addresses,
                bcm_firewalls=bcm_firewalls,
                bcm_instances=bcm_instances,
                bcm_networks=bcm_networks,
                bcm_routers=bcm_routers,
                bcm_service_accounts=bcm_service_accounts,
                bcm_subnetworks=bcm_subnetworks,
            )
        else:
            log.info("Failed environment was kept and will have to be deleted manually.")
            raise RuntimeError(error)

    try:
        if config["run_cm_bright_setup"] and config['create_public_ip']:
            wait_for_cluster(config=config, host=str(instance_ip) if not instance_ip.is_private else "N/A")
        cod_log(log, "Deployment finished successfully.", 100)
    except Exception as error:
        log.error(error)
        cod_log(log, "Deployment finished with errors.", 100)

    generator = GCPSummaryGenerator(
        head_name=cluster_name,
        config=config,
        summary_type=SummaryType.Overview,
        ip=str(instance_ip),
        ssh_string=f"root@{instance_ip}" if not instance_ip.is_private else None,
        network=network.name,
    )

    generator.print_summary(log.info)
