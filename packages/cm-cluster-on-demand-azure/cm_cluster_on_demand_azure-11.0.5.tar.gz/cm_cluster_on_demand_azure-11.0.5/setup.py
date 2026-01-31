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
        "aiohttp>=3.8.3",
        "azure-identity~=1.19.0",
        "azure-mgmt-authorization~=4.0.0",
        "azure-mgmt-compute~=33.1.0",
        # Version pinned to avoid surprises (e.g. silently added agreements).
        "azure-mgmt-marketplaceordering==1.1.0",
        "azure-mgmt-network~=28.1.0",
        "azure-mgmt-privatedns~=1.2.0",
        "azure-mgmt-resource~=23.2.0",
        "azure-mgmt-storage~=21.2.1",
        "azure-storage-blob~=12.23.1",
        "msrestazure~=0.6",
        "tenacity>=8.1.0",
    ]
)
