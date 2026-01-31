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
from typing import Any, Iterator

from dateutil import parser
from google.cloud import storage  # type: ignore
from google.cloud.compute_v1.types import Image

from clusterondemand.images.find import CODImage, ImageSource
from clusterondemand.images.find import findimages_ns as common_findimages_ns
from clusterondemandconfig import ConfigNamespace, config
from clusterondemandconfig.configuration import ConfigurationView
from clusterondemandgcp import clientutils
from clusterondemandgcp.clientutils import GCPClient

log = logging.getLogger("cluster-on-demand")

findimages_ns = ConfigNamespace("gcp.images.find", help_section="image filter parameters")
findimages_ns.import_namespace(common_findimages_ns)
findimages_ns.override_imported_parameter("cloud_type", default="gcp")

# bcmh-ubuntu2204-trunk-41 (DEPRECATED)
# bcmh-ubuntu2204-trunk-42-x86-64
# bcmh-ubuntu2204-trunk-42-aarch64
# bcmh-ubuntu2204-11-0-dev-737 (DEPRECATED)
# bcmh-ubuntu2204-11-0-dev-738-x86-64
# bcmh-ubuntu2204-11-0-dev-738-aarch64
IMAGE_NAME_PREFIX = "bcmh-"
IMAGE_NAME_REGEX_GCP = r"bcmh-([^-]+)-(.+?)-(\d+)(?:-(aarch64|x86-64))?"


class CannotParseImageName(Exception):
    pass


class GCPImageSource(ImageSource):
    @classmethod
    def from_config(cls, config: ConfigurationView, ids: list[str] | None = None) -> GCPImageSource:
        ids_to_use = ids if ids is not None else config["ids"]
        ImageSource.print_cloud_agnostic_information(config, ids_to_use)
        log.info(f"GCP project id: '{config['project_id']}', image URI: '{config['image_blob_uri']}'")
        return GCPImageSource(
            ids=ids_to_use,
            version=config["version"],
            arch=config["arch"],
            distro=config["distro"],
            revision=config["revision"],
            status=config["status"],
            advanced=True,
            image_visibility=config["image_visibility"],
            cloud_type=config["cloud_type"],
        )

    def _iter_from_source(self) -> Iterator[CODImage]:
        client = GCPClient()
        if self.uuids:
            for uuid in self.uuids:
                try:
                    if clientutils.is_blob_url(uuid):  # Cloud Storage blob
                        if not (blob := client.get_blob_by_url(uuid)):
                            raise Exception("Unable to find requested image blob")
                        yield make_cod_image_from_blob(blob, allow_custom_images=True)
                    else:  # Compute Engine image
                        gcp_resource_path = clientutils.parse_url(uuid)
                        gcp_image = client.get_disk_image(gcp_resource_path.name, project=gcp_resource_path.project)
                        if not gcp_image:
                            raise Exception("Unable to find requested GCE image")
                        yield make_cod_image_from_gcp(gcp_image, allow_custom_images=True)
                except Exception as e:
                    log.error(f"Failed to get information about image {uuid}: {e}")
        else:
            # Compute Engine Images
            gcp_image_names: set[str] = set()
            for gcp_image in client.list_images(project=config["project_id"]):
                try:
                    log.debug(f"Found image: {gcp_image.self_link}")
                    image = make_cod_image_from_gcp(gcp_image)
                except Exception as e:
                    log.debug(f"Failed to parse image {gcp_image.name}: {e}")
                else:
                    gcp_image_names.add(image.name)
                    yield image

            # Image blobs in a Cloud Storage bucket
            image_blob_prefix = config["image_blob_uri"].removesuffix("/")
            image_blob_prefix = "/".join((image_blob_prefix, IMAGE_NAME_PREFIX))
            for blob in client.list_blobs(image_blob_prefix):
                if blob.name and not blob.name.endswith(".tar.gz"):
                    log.debug(f"Skipping blob {blob.self_link!r}: unrecognized suffix")
                    continue

                log.debug(f"Found blob: {blob.self_link}")
                try:
                    image = make_cod_image_from_blob(blob)
                except Exception as e:
                    log.debug(f"Failed to parse blob name {blob.name!r}: {e}")
                else:
                    # If we have a blob and a GCE image with the same name, use the image, ignore the blob.
                    if image.name in gcp_image_names:
                        log.debug(f"Skipping blob {blob.self_link!r}: a GCE image with the same name already exists")
                    else:
                        yield image


class CODImageBlob(CODImage):
    """
    Represents an image blob in a Cloud Storage bucket.
    """
    def __init__(self, blob: storage.blob.Blob, allow_custom_images: bool) -> None:
        if not (image_name := blob.name.split("/")[-1]):  # basename
            raise AssertionError("Empty image blob name")

        # Strip the "tar.gz" suffix mandatory for image source blobs.
        image_name = image_name.removesuffix(".tar.gz")

        super().__init__(
            uuid=blob.self_link,
            size=blob.size,
            created_at=blob.time_created,
            image_visibility="public",
            type="headnode",
            cloud_type="gcp",
            **_parse_image_name(image_name, allow_custom_images),
        )


def _parse_image_name(image_name: str, allow_custom_images: bool) -> dict[str, Any]:
    if match := re.fullmatch(IMAGE_NAME_REGEX_GCP, image_name):
        distro, version, revision, arch = match.groups()
        version = version.replace('-', '.', 1)
        return {
            "name": image_name,
            "version": version,
            "distro": distro,
            "revision": int(revision),
            "arch": arch.replace('-', '_') if arch else "x86_64",
            "id": f"{distro}-{version}",
        }

    if allow_custom_images:
        return {}

    raise CannotParseImageName(f"Cannot parse image name {image_name}")


def make_cod_image_from_gcp(gcp_image: Image, allow_custom_images: bool = False) -> CODImage:
    resource = clientutils.parse_resourcepath(gcp_image.self_link)
    additional_params = {
        "name": resource.name,
    } | _parse_image_name(gcp_image.name, allow_custom_images)
    return CODImage(
        uuid=resource.url,
        size=gcp_image.disk_size_gb * 2**30,
        created_at=parser.parse(gcp_image.creation_timestamp),
        image_visibility="private",
        type="headnode",
        cloud_type="gcp",
        **additional_params,
    )


def make_cod_image_from_blob(blob: storage.blob.Blob, allow_custom_images: bool = False) -> CODImage:
    return CODImageBlob(blob, allow_custom_images)
