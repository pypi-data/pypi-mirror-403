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

from clusterondemand.configuration import common_ns
from clusterondemandconfig import ConfigNamespace, may_not_equal_none

azurecredentials_ns = ConfigNamespace(
    "azure.credentials", help_section="Azure user credentials"
)
azurecredentials_ns.add_parameter(
    "azure_subscription_id",
    env="AZURE_SUBSCRIPTION_ID",
    help="Azure Subscription ID",
    validation=may_not_equal_none)
azurecredentials_ns.add_parameter(
    "azure_tenant_id",
    env="AZURE_TENANT_ID",
    help="Azure Tenant ID",
    validation=may_not_equal_none)
azurecredentials_ns.add_parameter(
    "azure_client_id",
    env="AZURE_CLIENT_ID",
    help="Azure Client ID",
    validation=may_not_equal_none)
azurecredentials_ns.add_parameter(
    "azure_client_secret",
    env="AZURE_CLIENT_SECRET",
    help="Azure Client Secret Key",
    help_varname="SECRET",
    validation=may_not_equal_none,
    secret=True)
azurecredentials_ns.add_parameter(
    "azure_location",
    default="westeurope",
    env="AZURE_LOCATION",
    help="Name of the Azure region to use for the operation")


azurecommon_ns = ConfigNamespace("azure.common")
azurecommon_ns.import_namespace(common_ns)
azurecommon_ns.remove_imported_parameter("version")
azurecommon_ns.import_namespace(azurecredentials_ns)
