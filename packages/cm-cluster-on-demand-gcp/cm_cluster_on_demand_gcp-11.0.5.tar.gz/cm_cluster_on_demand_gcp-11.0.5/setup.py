#!/usr/bin/env python
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

from setuptools import setup
from setuptools_scm import get_version

__version__ = get_version(root="..", relative_to=__file__)

setup(
    install_requires=[
        "cm-cluster-on-demand==" + __version__,
        "cm-cluster-on-demand-config==" + __version__,
        "google-api-core>=2.24.2",
        "google-cloud-asset>=3.30.1",
        "google-cloud-compute>=1.30.0",
        "google-cloud-filestore>=1.13.1",
        "google-cloud-iam>=2.19.0",
        "google-cloud-quotas>=0.1.17",
        "google-cloud-resource-manager>=1.14.2",
        "google-cloud-storage>=3.1.0",
        "passlib>=1.7.4",
    ]
)
