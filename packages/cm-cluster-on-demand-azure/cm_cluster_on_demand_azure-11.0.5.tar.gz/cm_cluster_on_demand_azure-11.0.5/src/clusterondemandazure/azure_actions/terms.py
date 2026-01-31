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

import json
import logging
import urllib.error
import urllib.request
from typing import Any

from clusterondemand.bcm_version import BcmVersion
from clusterondemandconfig.configuration import CommandConfiguration

from .credentials import AzureApiHelper

log = logging.getLogger("cluster-on-demand")


class MarketplaceTerms:
    def __init__(self, config: CommandConfiguration):
        self._api_helper = AzureApiHelper.from_config(config)
        self._bcm_version = BcmVersion(config["version"])
        self._publisher = "brightcomputing"

        # Only bright version in paid_image_versions have a paid marketplace images. They don't exist since 10.0
        PAID_IMAGE_VERSIONS = [(9, 0), (9, 1), (9, 2)]
        self._offer_ids = [
            f"bcmni-azure-{self._bcm_version.major}-{self._bcm_version.minor}-free"
        ]  # aka product
        self._plan_ids = [
            f"bcm-ni-azure-{self._bcm_version.major}-{self._bcm_version.minor}-free-v1",
            f"bcm-ni-azure-{self._bcm_version.major}-{self._bcm_version.minor}-free-v2",
        ]  # aka sku
        if self._bcm_version.release in PAID_IMAGE_VERSIONS:
            self._offer_ids.append(f"bcmni-azure-{self._bcm_version.major}-{self._bcm_version.minor}")
            self._plan_ids += [f"bcm-ni-azure-{self._bcm_version.major}-{self._bcm_version.minor}-v1",
                               f"bcm-ni-azure-{self._bcm_version.major}-{self._bcm_version.minor}-v2"]

        self._terms_of_interest = [("license_text_link", "License"),
                                   ("privacy_policy_link", "Privacy Policy"),
                                   ("marketplace_terms_link", "Marketplace Terms")]
        self._terms: dict[str, Any] = {}

    @property
    def accepted(self) -> bool:
        """
        Has the user already accepted the terms?
        """
        accepted = []
        for (offer_id, plan_id) in zip(self._offer_ids, self._plan_ids):
            resp = self._api_helper.agreements_client.marketplace_agreements.get(
                "virtualmachine", self._publisher, offer_id, plan_id
            )
            log.debug(f"azure marketplace agreements get {offer_id}:{plan_id} => {resp}")
            accepted.append(resp.accepted)
            self._terms[f"{offer_id}:{plan_id}"] = resp
        return all(accepted)

    @property
    def terms(self) -> dict[str, str]:
        """
        Return a dictionary of (agreement name) -> (link to agreement).
        """
        terms = {}
        for (offer_id, plan_id) in zip(self._offer_ids, self._plan_ids):
            resp = self._api_helper.agreements_client.marketplace_agreements.get(
                "virtualmachine", self._publisher, offer_id, plan_id
            )
            log.debug(f"azure marketplace agreements get {offer_id}:{plan_id} => {resp}")
            for (attr_name, display_name) in self._terms_of_interest:
                if hasattr(resp, attr_name):
                    if attr_name == "license_text_link":
                        # special handling for license links since they have 2 levels of indirection
                        try:
                            with urllib.request.urlopen(getattr(resp, attr_name)) as blob:
                                blob = blob.read().decode("utf-8")
                            parsed = json.loads(blob)
                            license_link = urllib.request.urlopen(parsed["LicenseTextLink"]).url  # resolve redirect
                            terms[f"{display_name} ({offer_id}:{plan_id})"] = license_link
                        except KeyError as e:
                            log.debug(f"Unexpected content behind license_text_link"
                                      f" ({getattr(resp, attr_name)}): {e} not found\n"
                                      f"Original response: {blob}")
                        except UnicodeError as e:
                            log.debug(f"Unexpected content behind license_text_link"
                                      f" ({getattr(resp, attr_name)}): {e}")
                        except json.JSONDecodeError as e:
                            log.debug(f"Unexpected content behind license_text_link"
                                      f" ({getattr(resp, attr_name)}): {e}\n"
                                      f"Original response: {blob}")
                        except urllib.error.URLError as e:
                            log.debug(f"Failed to resolve license_text_link ({getattr(resp, attr_name)}): {e}")
                        # if we failed to eliminate indirection, just present the link as-is
                        terms.setdefault(f"{display_name} ({offer_id}:{plan_id})", getattr(resp, attr_name))
                    else:
                        terms[f"{display_name} ({offer_id}:{plan_id})"] = getattr(resp, attr_name)
                else:
                    log.warning(f"{attr_name} does not exist for {offer_id}:{plan_id}")
        return terms

    def accept(self) -> None:
        """
        Accept the terms.
        """
        for (offer_id, plan_id) in zip(self._offer_ids, self._plan_ids):
            terms = self._terms[f"{offer_id}:{plan_id}"]
            terms.accepted = True
            resp = self._api_helper.agreements_client.marketplace_agreements.create(
                "virtualmachine", self._publisher, offer_id, plan_id, terms
            )
            log.debug(f"azure marketplace agreements create (i.e. accept) {offer_id}:{plan_id} => {resp}")
