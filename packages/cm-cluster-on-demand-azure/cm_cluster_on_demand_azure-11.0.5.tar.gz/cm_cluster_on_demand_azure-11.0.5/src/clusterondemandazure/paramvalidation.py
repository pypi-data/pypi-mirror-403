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

import typing

from clusterondemandazure.azure_actions.storage import StorageAction

from .vmsizelist import VMSizesList

if typing.TYPE_CHECKING:
    from .azure_actions.credentials import AzureApiHelper


class AZUREParamValidator:

    @staticmethod
    def validate_location(azure_api: AzureApiHelper, location: str) -> bool:
        return VMSizesList.is_valid_location(azure_api, location)

    @staticmethod
    def validate_custom_blob(blob_url: str) -> bool:
        try:
            StorageAction.get_blob_properties(blob_url).metadata
        except Exception:
            return False
        return True

    @staticmethod
    def validate_password(password: str) -> bool:
        return len(password) >= 8
