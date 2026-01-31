#
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

import functools
import logging
from typing import TYPE_CHECKING

import requests.exceptions  # requests is a dependency of azure
import tenacity
from azure.core.exceptions import HttpResponseError
from azure.identity import ClientSecretCredential
from azure.mgmt.authorization import AuthorizationManagementClient
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.marketplaceordering import MarketplaceOrderingAgreements
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.privatedns import PrivateDnsManagementClient
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.resource.subscriptions import SubscriptionClient
from azure.mgmt.storage import StorageManagementClient
from msrest.exceptions import AuthenticationError
from msrestazure.azure_exceptions import CloudError

if TYPE_CHECKING:
    from clusterondemandconfig.configuration import ConfigurationView

log = logging.getLogger("cluster-on-demand")


class AzureApiHelper:
    def __init__(self, client_id: str, client_secret: str, tenant_id: str, subscription_id: str) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant_id = tenant_id
        self.subscription_id = str(subscription_id)

        self._silence_http_logs()

    @staticmethod
    @functools.lru_cache
    def _silence_http_logs() -> None:
        logging.getLogger("msrest").setLevel(logging.WARNING)
        logging.getLogger("azure").setLevel(logging.WARNING)
        logging.getLogger("requests_oauthlib").setLevel(logging.WARNING)

    @classmethod
    def from_config(cls, config: ConfigurationView) -> AzureApiHelper:
        return cls(
            client_id=config["azure_client_id"],
            client_secret=config["azure_client_secret"],
            tenant_id=config["azure_tenant_id"],
            subscription_id=config["azure_subscription_id"],
        )

    @functools.cached_property
    def storage_client(self) -> StorageManagementClient:
        return StorageManagementClient(
            self.get_credential(),
            self.subscription_id,
        )

    @functools.cached_property
    def network_client(self) -> NetworkManagementClient:
        return NetworkManagementClient(
            self.get_credential(),
            self.subscription_id,
        )

    @functools.cached_property
    def privdns_management_client(self) -> PrivateDnsManagementClient:
        return PrivateDnsManagementClient(
            self.get_credential(),
            self.subscription_id,
        )

    @functools.cached_property
    def resource_client(self) -> ResourceManagementClient:
        return ResourceManagementClient(
            self.get_credential(),
            self.subscription_id,
        )

    @functools.cached_property
    def compute_client(self) -> ComputeManagementClient:
        return ComputeManagementClient(
            self.get_credential(),
            self.subscription_id,
        )

    @functools.cached_property
    def subscription_client(self) -> SubscriptionClient:
        return SubscriptionClient(
            self.get_credential(),
        )

    @functools.cached_property
    def agreements_client(self) -> MarketplaceOrderingAgreements:
        return MarketplaceOrderingAgreements(
            self.get_credential(),
            self.subscription_id
        )

    @functools.cached_property
    def authorization_management_client(self) -> AuthorizationManagementClient:
        return AuthorizationManagementClient(
            self.get_credential(),
            self.subscription_id
        )

    @functools.lru_cache
    @tenacity.retry(
        wait=tenacity.wait_exponential(),
        stop=tenacity.stop_after_delay(60),
        retry=tenacity.retry_if_exception(
            lambda e: (
                isinstance(e, (requests.exceptions.ConnectionError, requests.exceptions.SSLError))
                or (
                    isinstance(e, AuthenticationError)
                    and isinstance(e.inner_exception, requests.exceptions.ConnectionError)  # pylint: disable=no-member
                )
            )
        ),
        reraise=True,
        before_sleep=tenacity.before_sleep_log(log, logging.DEBUG),
    )
    def get_credential(self) -> ClientSecretCredential:
        return ClientSecretCredential(
            client_id=self.client_id,
            client_secret=self.client_secret,
            tenant_id=self.tenant_id,
        )

    def log_deployment_error(self, azure_ex: Exception, resource_group: str, deployment_name: str) -> bool:
        details_found = False
        if "DeploymentFailed" in str(azure_ex) and resource_group and deployment_name:
            try:
                for operation in self.resource_client.deployment_operations.list(
                    resource_group_name=resource_group, deployment_name=deployment_name
                ):
                    if operation.properties.status_code.upper() != "OK" and operation.properties.status_message:
                        resource_name = operation.properties.target_resource.resource_name
                        error_code = operation.properties.status_message.error.code
                        error_message = operation.properties.status_message.error.message
                        log.error(f"Deployment error for resource {resource_name}: ({error_code}) {error_message}")
                        details_found = True
            except Exception as ex:
                log.error(f"Error while diagnosing deployment failure: {ex}")
        return details_found

    @staticmethod
    def log_error_details(
        azure_ex: CloudError | HttpResponseError,
        *,
        azure_api: AzureApiHelper | None = None,
        resource_group: str | None = None,
        deployment_name: str | None = None,
    ) -> None:
        if (azure_api and resource_group and deployment_name and
                azure_api.log_deployment_error(azure_ex, resource_group, deployment_name)):
            return  # We've successfully logged interesting details, so no need for extra debug logging

        details = None
        if isinstance(azure_ex, CloudError):
            details = azure_ex.error.details if azure_ex.error else None
        elif isinstance(azure_ex, HttpResponseError):
            details = azure_ex.error.message_details() if azure_ex.error else None
        if details:
            log.debug(f"Error details: {details}")
