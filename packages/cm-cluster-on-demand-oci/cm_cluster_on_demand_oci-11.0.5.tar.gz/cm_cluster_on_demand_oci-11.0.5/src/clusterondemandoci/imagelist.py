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

import clusterondemand.configuration
from clusterondemand.imagetable import ALL_COLUMNS, make_cod_images_table
from clusterondemandconfig import ConfigNamespace, config

from .configuration import ocicommon_ns
from .images import OCIImageSource, findimages_ns

log = logging.getLogger("cluster-on-demand")

#
# XXX These columns are just a guess.
OCI_COLUMNS = [
    ("name", "Image name"),
    ("distro", "Distro"),
    ("bcm_version", "BCM Version"),
    ("arch", "Arch"),
    ("created_at", "Created"),
    ("uuid", "UUID"),
]

#
# XXX This line isn't in the azure variant
assert all(col in ALL_COLUMNS for col in OCI_COLUMNS)


config_ns = ConfigNamespace("oci.image.list", "list output options")
config_ns.import_namespace(ocicommon_ns)
config_ns.import_namespace(findimages_ns)
config_ns.import_namespace(clusterondemand.configuration.clusterlist_ns)
config_ns.add_enumeration_parameter(
    "sort",
    default=["bcm_version", "created_at"],
    choices=[column[0] for column in OCI_COLUMNS],
    help="Sort results by one (or two) of the columns"
)
config_ns.add_enumeration_parameter(
    "columns",
    default=[column[0] for column in OCI_COLUMNS],
    choices=[column[0] for column in OCI_COLUMNS],
    help="Provide set of columns to be displayed"
)
config_ns.add_enumeration_parameter(
    "image_types",
    default=["headnode"],
    choices=["headnode", "node-installer"],
    help="Provide set of image types to be displayed",
)


def run_command():
    log.info("Listing images in region %s", config["oci_region"])

    print(make_cod_images_table(
        (image for image in OCIImageSource.find_images_using_options(config) if image.type in config["image_types"]),
        sortby=config["sort"],
        advanced=True,
        columns=config["columns"],
        output_format=config["output_format"]
    ))
