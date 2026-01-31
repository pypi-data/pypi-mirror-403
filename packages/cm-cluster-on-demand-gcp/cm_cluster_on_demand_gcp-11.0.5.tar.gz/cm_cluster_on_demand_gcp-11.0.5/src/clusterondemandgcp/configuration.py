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

import clusterondemand.configuration
from clusterondemandconfig import ConfigNamespace, may_not_equal_none
from clusterondemandconfig.configuration.configuration_view import ConfigurationView
from clusterondemandconfig.exceptions import ConfigLoadError
from clusterondemandconfig.parameter import Parameter

gcpcredentials_ns = ConfigNamespace("gcp.credentials", help_section="GCP credentials")
# TBD:
# gcpcredentials_ns.add_parameter(
#     "gcp_api_key",
#     help="GCP API Key",
#     help_varname="API_KEY",
# )
# ...

gcpcommon_ns = ConfigNamespace("gcp.common")
gcpcommon_ns.import_namespace(clusterondemand.configuration.common_ns)
gcpcommon_ns.remove_imported_parameter("version")
gcpcommon_ns.import_namespace(gcpcredentials_ns)
gcpcommon_ns.add_parameter(
    "project_id",
    help="Id of the GCP project to use",
    validation=may_not_equal_none
)


def gs_uri_validation(param: Parameter, config: ConfigurationView) -> None:
    uri = config[param.key]
    if not uri.startswith("gs://"):
        raise ConfigLoadError(f"{param.key}: Google Cloud Storage URI '{uri}' missing gs:// provider")


gcpcommon_ns.add_parameter(
    "image_blob_uri",
    help="Cloud Storage directory URI containing image blobs: 'gs://<bucket_name>[/dir]'.",
    advanced=True,
    default="gs://nv-bcm-images",
    validation=gs_uri_validation,
)
