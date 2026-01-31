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

import datetime
import json
import logging
import re
import urllib.request
from urllib.error import HTTPError, URLError

import dateutil
import requests
import tenacity
from oci.core.models.image import Image as OCIImage
from oci.exceptions import ServiceError

from clusterondemand.exceptions import CODException
from clusterondemand.images.find import CODImage, ImageSource
from clusterondemand.images.find import findimages_ns as common_findimages_ns
from clusterondemandconfig import ConfigLoadError, ConfigNamespace, config
from clusterondemandconfig.configuration.configuration_view import ConfigurationView
from clusterondemandconfig.parameter import Parameter
from clusterondemandoci.client import OCIClient
from clusterondemandoci.utils import get_oci_config

log = logging.getLogger("cluster-on-demand")


def _validate_bucket_url(param: Parameter, configuration: ConfigurationView) -> None:
    """
    Validate that bucket URL is fetchable and returns valid OCI bucket index JSON.
    If URL doesn't work, it tries fixing it by adding /o/ suffix.
    """
    if not (bucket_url := configuration[param.name]):
        return

    @tenacity.retry(
        retry=tenacity.retry_if_exception_type(requests.exceptions.ConnectionError),
        wait=tenacity.wait_fixed(2),
        stop=tenacity.stop_after_attempt(5),
        before_sleep=tenacity.before_sleep_log(log, logging.DEBUG),
        reraise=True,
    )
    def fetch_bucket_index_json(bucket_listing_url: str) -> list[str]:
        response = requests.get(bucket_listing_url, timeout=30)
        response.raise_for_status()
        for obj in response.json()["objects"]:
            _ = obj["name"]  # just check if output format is correct

    urls = [bucket_url]
    if not bucket_url.rstrip("/").endswith("/o"):
        urls.append(bucket_url.rstrip("/") + "/o/")

    first_error: Exception | None = None
    for url in urls:
        try:
            log.debug(f"Trying to fetch bucket index JSON: {url}...")
            fetch_bucket_index_json(url)
            return  # validation passed
        except Exception as e:
            log.debug(f"Fetching failed: {e}")
            if first_error is None:
                first_error = e

    raise ConfigLoadError(f"Please check {param.name}: {bucket_url}, got error: {first_error}")


findimages_ns = ConfigNamespace("oci.images.find", help_section="image filter parameters")
findimages_ns.import_namespace(common_findimages_ns)
findimages_ns.override_imported_parameter("cloud_type", default="oci")

findimages_ns.add_parameter(
    "image_compartment_id",
    help="OCID of the compartment containing the head node image(s)."
)

findimages_ns.add_parameter(
    "community_applications_url",
    help="The community applications url to list images from.",
    # The URL is a Pre-Authenticated Request to "community-application" bucket with very long expiration date.
    # The bucket is located in nvidiamain tenant, eu-amsterdam-1 region, bcm compartment.
    # URL to web UI: https://cloud.oracle.com/object-storage/buckets/axvrabcwoa8f/community-application/details?region=eu-amsterdam-1  # noqa: E501
    default="https://axvrabcwoa8f.objectstorage.eu-amsterdam-1.oci.customer-oci.com/p/-WWxiTlRRZ9YFdc_AAoroPPm3kFHN4RntNxj4dVlUI66fSq0875hgigneyDkRy3B/n/axvrabcwoa8f/b/community-application"  # noqa: E501
)
findimages_ns.add_parameter(
    "netboot_images_bucket_url",
    help="The OCI Object Storage bucket URL containing netboot images.",
    # TODO: Create a bucket for release images in nvidimain tenant and move URL with dev images to krusty.ini.
    # The bucket is located in nvidiangcnonprd tenant, eu-amsterdam-1 region, bcmnonprod compartment.
    # URL to web UI: https://cloud.oracle.com/object-storage/buckets/axb4hmgfhjxh/bright-images-ci/details?region=eu-amsterdam-1  # noqa: E501
    default="https://axb4hmgfhjxh.objectstorage.eu-amsterdam-1.oci.customer-oci.com/p/jwy11SWyjMa3BW14zzl4t_qQfZn3b793_T-gBvBYYTDWZrmys2qSLSEqCgFSQjhx/n/axb4hmgfhjxh/b/bright-images-ci/o/",  # noqa: E501
    validation=_validate_bucket_url,
)

#
# Additional parameters
#
IMAGE_NAME_REGEX_OCI = r"^(bcmh|bcni)-([^-]+)-([^-]+(?:-dev)?)-(\d+)(?:-([^-]+))?$"
IMAGE_API_HASH_TAG = "BCM_API_HASH"
IMAGE_OPERATING_SYSTEM = "BCM Custom Linux"

#
# XXX Some notes on what needs to be extracted from the real image name
#
# Azure: name, version, distribution, revision = match.groups()
#
#         if not distribution:
#            distribution = "centos"
#
#        additional_params = {
#            "name": name,
#            "version": version,
#            "distro": distribution,
#            "revision": int(revision),
#            "id": f"{distribution}-{version}",
#        }

# AWS: version, distribution, revision = match.groups()
#         additional_params = {
#            "version": version,
#            "distro": distribution,
#            "revision": int(revision),
#            "id": f"{distribution}-{version}",
#        }
# https://cloud.oracle.com/compute/images/ocid1.image.oc1.us-sanjose-1.aaaaaaaanypljfcdl4wj7wfqcfradpzgzazdbvpntl36zk3bcktoqyzcf4ma


class CannotParseImageName(Exception):
    pass


class OCIImageSource(ImageSource):
    @classmethod
    #
    # XXX This function definition was copied from AWS but may be problematic; 'config'
    # XXX stomps on the 'config' imported from clusterondemandconfig
    def from_config(cls, config_DISABLED, ids=None):
        ids_to_use = ids if ids is not None else config["ids"]
        ImageSource.print_cloud_agnostic_information(config, ids)
        log.info(
            f"OCI compartment id: {config['image_compartment_id']}, "
            f"community applications URL: {config['community_applications_url']}"
        )
        return OCIImageSource(
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

    def _get_available_regions(self):
        community_applications_index_url = config["community_applications_url"] + "/o/"
        try:
            content = urllib.request.urlopen(community_applications_index_url)
            region_entries = json.load(content)
            if "objects" not in region_entries:
                log.debug(f"The link {community_applications_index_url} is valid querying available regions"
                          ", but 'objects' is not returned.")
                return []
            regions = set()
            for entry in region_entries["objects"]:
                if "manifest.json" in entry["name"]:
                    regions.add(entry["name"].split("/")[0])
            return regions

        except Exception as e:
            log.debug(f"When querying available regions in {community_applications_index_url}, caught {e}")

    def _get_community_application_images(self):
        community_applications_region_url = config["community_applications_url"] + "/o/" + \
            config['oci_region'] + "/manifest.json"
        log.debug(f"Trying to get community applications manifest from {community_applications_region_url}")
        try:
            for attempt in tenacity.Retrying(
                retry=tenacity.retry_if_exception_type(URLError),
                wait=tenacity.wait_fixed(wait=1),
                stop=tenacity.stop_after_attempt(5),
                before_sleep=tenacity.before_sleep_log(log, logging.DEBUG),
                after=tenacity.after_log(log, logging.DEBUG),
                reraise=True
            ):
                with attempt:
                    content = urllib.request.urlopen(community_applications_region_url)
                    return json.load(content)
        except HTTPError as e:
            if e.code == 401:
                raise CODException("Unauthorized: You don't have permission to access "
                                   f"{config['community_applications_url']}.")
            if e.code == 404:
                error_message = f"No images found in region '{config['oci_region']}'."
                available_regions = self._get_available_regions()
                if available_regions:
                    formatted_available_regions = '\n'.join(available_regions)
                    error_message += f" Available regions:\n{formatted_available_regions}"
                raise CODException(error_message)
            raise CODException(f"Please check community-applications-url: {config['community_applications_url']}, "
                  f"got HTTP Error ({e.code}): {e.reason}")
        except Exception as e:
            raise CODException(f"An error occurred when finding images using community-applications-url: {e}")

    def _iter_from_source(self):
        oci_client = OCIClient(get_oci_config())

        if self.uuids:
            for image_id in self.uuids:
                try:
                    yield make_cod_image_from_ocid(oci_client, image_id, allow_custom_images=True)
                except ServiceError as e:
                    log.error(f"Failed to get information about image {image_id}: {e.message}")
            return

        public_image_ids = set()
        if config["community_applications_url"]:
            community_application_images = self._get_community_application_images()

            for community_application_image in community_application_images:
                try:
                    cod_image = make_cod_image_from_oci_community_application(community_application_image)
                except CannotParseImageName as exc:
                    # This is parsing names of public images, someone could even upload some bogus name
                    # to break our code. So we just ignore if we can't parse it
                    # Other exception can blow up
                    log.debug(exc)
                else:
                    public_image_ids.add(cod_image.custom_image_id)
                    yield cod_image
        else:
            log.warning("No public images listed. Set community_applications_url to list public images")

        if compartment_id := config['image_compartment_id']:
            try:
                log.debug(f"Listing images in image_compartment_id={compartment_id}")
                images = oci_client.compute.list_images(compartment_id, operating_system=IMAGE_OPERATING_SYSTEM)
            except ServiceError as error:
                if error.code == "NotAuthorizedOrNotFound":
                    raise CODException(
                        f"Unable to get image by the image-compartment-id {config['image_compartment_id']}."
                        f" OCI error message: {error.message}"
                    ) from error

                raise CODException(error.message) from error

            for image in images:
                # Skip custom images that have an associated community image, as they are already listed
                # as public images.
                if image.id in public_image_ids:
                    continue

                try:
                    cod_image = make_cod_image_from_oci_custom_image(image)
                except CannotParseImageName as exc:
                    # This is parsing names of public images, someone could even upload some bogus name
                    # to break our code. So we just ignore if we can't parse it
                    # Other exception can blow up
                    log.debug(exc)
                else:
                    yield cod_image
        else:
            log.warning("No image compartment ID specified. Set with 'image_compartment_id' parameter.")


class CommunityAppImage(CODImage):

    def __init__(self, app_id: str, image_id: str, image_name: str, created_at: datetime,
                 bcm_api_hash: str, allow_custom_images: bool) -> None:
        super().__init__(
            name=image_name,
            uuid=app_id,
            created_at=created_at,
            image_visibility="public",
            cloud_type="oci",
            bcm_api_hash=bcm_api_hash,
            **_parse_image_name(image_name, allow_custom_images),
        )
        self.custom_image_id = image_id


def _parse_image_name(image_name: str, allow_custom_images: bool) -> dict[str, str | int]:
    if match := re.match(IMAGE_NAME_REGEX_OCI, image_name):
        prefix, distribution, version, revision, arch = match.groups()
        return {
            "type": {"bcmh": "headnode", "bcni": "node-installer"}[prefix],
            "version": version,
            "distro": distribution,
            "revision": int(revision),
            "id": f"{distribution}-{version}",
            "arch": arch or "x86_64",
        }
    if allow_custom_images:
        return {}

    raise CannotParseImageName(f"Cannot parse image name {image_name}")


def make_cod_image_from_oci_custom_image(image: OCIImage, allow_custom_images: bool = False) -> CODImage:
    """
    Convert OCI image object to COD image object

    :param image: OCI image object
    :param allow_custom_images: allow non-Bright images
    :return: CODImage object for specified image
    """
    return CODImage(
        name=image.display_name,
        uuid=image.id,
        created_at=image.time_created,
        image_visibility="private",
        cloud_type="oci",
        bcm_api_hash=image.freeform_tags.get(IMAGE_API_HASH_TAG, ""),
        **_parse_image_name(image.display_name, allow_custom_images),
    )


def make_cod_image_from_oci_community_application(community_app_info: dict[str, str],
                                                  allow_custom_images: bool = False) -> CommunityAppImage:
    """
    Convert OCI community application dict to COD image object

    :param community_app_info: OCI community application dict
    :param allow_custom_images: allow non-Bright images
    :return: CODImage object for specified image
    """
    return CommunityAppImage(
        app_id=community_app_info["id"],
        image_id=community_app_info["image_id"],
        image_name=community_app_info["display_name"],
        created_at=dateutil.parser.parse(community_app_info["time_created"]),
        bcm_api_hash=community_app_info["bcm_api_hash"],
        allow_custom_images=allow_custom_images,
    )


def make_cod_image_from_ocid(oci_client: OCIClient, image_id: str, allow_custom_images: bool = False) -> CODImage:
    if image_id.startswith("ocid1.image"):
        image = oci_client.compute.get_image(image_id)
        return make_cod_image_from_oci_custom_image(image, allow_custom_images)

    if image_id.startswith("ocid1.marketplacecommunitylisting"):
        publication = oci_client.marketplace.get_image_publication(image_id)
        app = oci_client.marketplace.get_image(image_id)
        return CommunityAppImage(
            app_id=app.listing_id,
            image_id=app.image_id,
            image_name=publication.name,
            created_at=app.time_created,
            bcm_api_hash=publication.freeform_tags.get(IMAGE_API_HASH_TAG, ""),
            allow_custom_images=allow_custom_images,
        )

    raise CODException(
        "Unsupported image ID format. Expected ocid1.image* or ocid1.marketplacecommunitylisting*"
    )
