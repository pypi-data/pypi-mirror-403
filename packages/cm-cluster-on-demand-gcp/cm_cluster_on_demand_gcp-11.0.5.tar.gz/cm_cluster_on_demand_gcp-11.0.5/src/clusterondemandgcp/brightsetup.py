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
import typing

import clusterondemand.brightsetup
from clusterondemand.cloudconfig.headfiles import REMOTE_NODE_DISK_SETUP_PATH
from clusterondemand.configuration import CFG_NO_ADMIN_EMAIL, NO_WLM
from clusterondemand.images.find import CODImage
from clusterondemandconfig import config

log = logging.getLogger("cluster-on-demand")


def generate_bright_setup(cluster_name: str, subnet_id: str, subnet_cidr: str, mtu: int) -> dict[str, typing.Any]:
    # FIXME: pass head node image here.
    # For now, generate_bright_setup only needs to know the version from the image, so let's fake it.
    fake_head_node_image = CODImage(version="trunk")

    license_dict = clusterondemand.brightsetup.get_license_dict(cluster_name)
    admin_email = config["admin_email"] if config["admin_email"] != CFG_NO_ADMIN_EMAIL else None
    brightsetup = clusterondemand.brightsetup.generate_bright_setup(
        cloud_type="gcp",
        wlm=config["wlm"] if config["wlm"] != NO_WLM else "",
        hostname=cluster_name,
        head_node_image=fake_head_node_image,
        node_count=0,
        timezone=config["timezone"],
        admin_email=admin_email,
        license_dict=license_dict,
        node_kernel_modules=["virtio_net", "virtio_pci", "virtio_blk", "virtio_scsi", "8021q"],
        node_disk_setup_path=REMOTE_NODE_DISK_SETUP_PATH,
    )

    brightsetup["modules"]["brightsetup"]["gcp"] = {
        "api": {
            "project_id": config["project_id"],
            "image_storage_location": config["image_storage_location"],
        },
        "network": {
            "cidr": subnet_cidr,  # FIXME: we need common CIDR in case of multiple subnets
            "mtu": mtu,
            "subnets": [
                {
                    "cidr": subnet_cidr,
                    "cloud_subnet_id": subnet_id,
                    "name": "gcp-network",
                }
            ],
        },
        "nodes": {
            "base_name": "cnode",
            "count": config["nodes"],
            "boot_image_uri": config["image_blob_uri"],
            "machine_type": config["node_type"],
            "service_account": config["node_service_account"],
            # Create cnodes in the head node zone by default.
            # Implement --node-zone, if a separate zone is needed later.
            "zone": config["head_node_zone"],
            "storage": {
                "root-disk": config["node_root_volume_size"],
            },
            "disks": [
                {
                    "name": "root-disk",
                    "provisioned_iops": config["node_disk_provisioned_iops"],
                    "provisioned_throughput": config["node_disk_provisioned_throughput"],
                    "size": config["node_root_volume_size"],
                    "type": config["node_disk_type"],
                },
            ],
        }
    }

    return brightsetup
