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
from typing import TYPE_CHECKING

from azure.storage.blob import ContainerClient

if TYPE_CHECKING:
    from collections.abc import Generator
    from azure.storage.blob import BlobProperties
    from clusterondemandconfig.configuration import ConfigurationView
    from clusterondemandconfig.parameter.parameter import Parameter

from clusterondemand.exceptions import CODException
from clusterondemand.images.find import CODImage, ImageSource
from clusterondemand.images.find import findimages_ns as common_findimages_ns
from clusterondemandconfig import ConfigNamespace, config

from .azure_actions.storage import StorageAction
from .azure_actions.throttle import unt

log = logging.getLogger("cluster-on-demand")


def must_be_valid_container_url(parameter: Parameter, configuration: ConfigurationView) -> None:
    """Validation that raises an error when the container url does not match the proper format"""
    container_urls = configuration[parameter.key]
    for container_url in container_urls:
        if not re.match(CONTAINER_URL_REGEX, container_url):
            raise CODException("Invalid image container URI: %s; must match: %s" % (container_url, CONTAINER_URL_REGEX))


findimages_ns = ConfigNamespace("azure.images.find", help_section="image filter parameters")
findimages_ns.import_namespace(common_findimages_ns)
findimages_ns.override_imported_parameter("cloud_type", default="azure")
findimages_ns.add_enumeration_parameter(
    "container_url",
    default=["https://brightimages.blob.core.windows.net/images/"],
    help="One or several azure container urls to list images from",
    validation=must_be_valid_container_url
)

# This regex can match both,
# blob.name: bcm-cod-image-10.0-ubuntu2004-20.04-1.vhd
# cod image name: bcm-cod-image-10.0-ubuntu2004-20.04-1
IMAGE_NAME_REGEX_AZURE = r"^((?:bcm-cod-image-)([^-]+(?:-dev)?)(?:-([^-]+))?-(.*?))(?:\.vhd)?$"
CONTAINER_URL_REGEX = r"(http|https)://(?P<storage_account>[^\.]+).blob.core.windows.net/(?P<container>.+)"


class CannotParseImageName(Exception):
    pass


class AzureImageSource(ImageSource):
    @classmethod
    def from_config(cls, config: ConfigurationView, ids: list[str] | None = None) -> AzureImageSource:
        ids_to_use = ids or config["ids"]
        ImageSource.print_cloud_agnostic_information(config, ids)
        return AzureImageSource(
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

    def _iter_from_source(self) -> Generator[CODImage]:
        if self.uuids:
            for vhd_url in self.uuids:  # In case of COD-Azure, UUID is a URL
                blob = StorageAction.get_blob_properties(vhd_url)
                log.info(f"Azure vhd url: {vhd_url}")
                yield make_cod_image_from_azure(blob, vhd_url, allow_custom_images=True)
        else:
            for url in config["container_url"]:
                log.info(f"Azure container url: '{url}'")
                container_client = ContainerClient.from_container_url(url)
                for blob in unt(container_client.list_blobs):
                    try:
                        cod_image = make_cod_image_from_azure(blob, url + blob.name)
                    except Exception as e:
                        # This is parsing names of public images, someone could even upload some bogus name
                        # to break our code. So we just ignore if we can't parse it
                        # Other exception can blow up
                        log.debug(e)
                    else:
                        yield cod_image


def parse_image_or_blob_name(name: str, allow_custom_images: bool = False) -> dict[str, str | int]:
    match = re.match(IMAGE_NAME_REGEX_AZURE, name)
    if match:
        name, version, distribution, revision = match.groups()
        # Prior to CM-35092, we didn't have the distro in the image name
        # So some of them don't have it.
        # We just set as "centos" without specifying version
        if not distribution:
            distribution = "centos"

        properties_from_name = {
            "name": name,
            "version": version,
            "distro": distribution,
            "revision": int(revision),
            "id": f"{distribution}-{version}",
        }
    elif not allow_custom_images:
        raise CannotParseImageName(f"Cannot parse image name {name}")

    return properties_from_name


def make_cod_image_from_azure(blob: BlobProperties, vhd_url: str, allow_custom_images: bool = False) -> CODImage:
    """
    Convert Azure's image information to COD image object

    :param blob: Azure's blob properties
    :param vhd_url: url to vhd image
    :param allow_custom_images: allow non-Bright images
    :return: CODImage object for specified image
    """
    additional_params = parse_image_or_blob_name(blob.name, allow_custom_images)

    return CODImage(
        uuid=vhd_url,
        size=blob.size,
        created_at=blob.creation_time,
        image_visibility="N/A",
        type="headnode",
        cloud_type="azure",
        name=str(additional_params["name"]),
        version=str(additional_params["version"]),
        distro=str(additional_params["distro"]),
        revision=int(additional_params["revision"]),
        id=str(additional_params["id"]),
    )
