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

from prettytable import PrettyTable

from clusterondemand import utils
from clusterondemand.images.find import CODImage
from clusterondemand.node_definition import NodeDefinition
from clusterondemand.summary import SummaryGenerator, SummaryType
from clusterondemandconfig.configuration import ConfigurationView


class GCPSummaryGenerator(SummaryGenerator):
    """Generate the summary for creation of GCP clusters and nodes."""

    def __init__(
        self,
        head_name: str,
        project: str | None = None,
        region: str | None = None,
        zone: str | None = None,
        serviceaccount: str | None = None,
        image: CODImage | None = None,
        summary_type: SummaryType | None = None,
        config: ConfigurationView | None = None,
        head_node_definition: NodeDefinition | None = None,
        head_image: CODImage | None = None,
        node_definition: NodeDefinition | None = None,
        node_image: CODImage | None = None,
        ssh_string: str | None = None,
        ip: str | None = None,
        network: str | None = None,
    ) -> None:
        super().__init__(
            head_name=head_name,
            config=config,
            summary_type=summary_type,
            primary_head_node_definition=head_node_definition,
            head_image=head_image,
            node_definitions=[node_definition] if node_definition else None,
            node_image=node_image,
            ip=ip,
            ssh_string=ssh_string,
            region=region,
        )
        self._project = project
        self._zone = zone
        self._serviceaccount = serviceaccount
        self._image = image
        self._network = network

    def _add_rows(self, table: PrettyTable) -> None:
        if self._image:
            self._add_image(table=table)
        if self._project:
            self._add_project(table=table)
        if self._region:
            self._add_region(table=table)
        if self._zone:
            self._add_zone(table=table)
        if self._serviceaccount:
            self._add_service_account(table=table)
        if self._network:
            self._add_network(table=table)

    def _add_image(self, table: PrettyTable) -> None:
        if self._image:
            image_age = utils.get_time_ago(self._image.created_at)  # type: ignore[arg-type]
            image_type = "Compute Engine Image" if self._image.image_visibility == "private" else "Cloud Storage Blob"
            table.add_row(["Image name:", f"{self._image.name} ({self._image.id}:{self._image.revision})"])
            table.add_row(["Image date:", f"{self._image.created_at} ({image_age})"])
            table.add_row(["Image type:", image_type])

    def _add_zone(self, table: PrettyTable) -> None:
        table.add_row(["Zone:", self._zone])

    def _add_project(self, table: PrettyTable) -> None:
        table.add_row(["Project:", self._project])

    def _add_service_account(self, table: PrettyTable) -> None:
        table.add_row(["Head node service account:", self._serviceaccount])

    def _add_network(self, table: PrettyTable) -> None:
        table.add_row(["Network:", self._network])
