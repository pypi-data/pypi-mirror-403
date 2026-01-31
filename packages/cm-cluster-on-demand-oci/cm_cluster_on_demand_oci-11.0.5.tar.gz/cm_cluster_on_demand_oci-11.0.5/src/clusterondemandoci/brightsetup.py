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
import typing

import clusterondemand.brightsetup
from clusterondemand.bcm_version import BcmVersion
from clusterondemand.cloudconfig.headfiles import REMOTE_NODE_DISK_SETUP_PATH
from clusterondemand.configuration import CFG_NO_ADMIN_EMAIL, NO_WLM
from clusterondemand.images.find import CODImage
from clusterondemandconfig import config

log = logging.getLogger("cluster-on-demand")


def generate_bright_setup(
        cluster_name: str,
        head_node_image: CODImage,
        node_image_id: str,
        vcn_cidr: str,
        subnet_id: str,
        subnet_cidr: str,
        private_subnet_id: str,
        private_subnet_cidr: str,
        node_nsg_id: str,
        node_instance_configuration_id: str,
        auth_key_content: str
) -> dict[str, typing.Any]:
    license_dict = clusterondemand.brightsetup.get_license_dict(cluster_name)

    admin_email = config["admin_email"] if config["admin_email"] != CFG_NO_ADMIN_EMAIL else None

    brightsetup = clusterondemand.brightsetup.generate_bright_setup(
        cloud_type="oci",
        wlm=config["wlm"] if config["wlm"] != NO_WLM else "",
        hostname=cluster_name,
        head_node_image=head_node_image,
        node_count=0,
        timezone=config["timezone"],
        admin_email=admin_email,
        license_dict=license_dict,
        node_kernel_modules=["virtio_net", "virtio_pci", "virtio_blk", "virtio_scsi", "8021q"],
        node_disk_setup_path=REMOTE_NODE_DISK_SETUP_PATH,
    )

    private_subnet = {
        "name": "oci-network-private",
        "cidr": private_subnet_cidr,
        "cloud_subnet_id": private_subnet_id,
    } if private_subnet_id else None

    brightsetup["modules"]["brightsetup"]["oci"] = {
        "api": {
            "auth_user": config["oci_user"],
            "auth_key_content": auth_key_content if not config["use_principal_authentication"] else "",
            "auth_fingerprint": config["oci_fingerprint"],
            "auth_tenancy": config["oci_tenancy"],
            "availability_domain": config["oci_availability_domain"] or "",
            "region": config["oci_region"],
        },
        "network": {
            "cidr": vcn_cidr,
            "subnets": [
                {
                    "name": "oci-network",
                    "cidr": subnet_cidr,
                    "cloud_subnet_id": subnet_id,
                },
                *([private_subnet] if private_subnet else []),
            ],
        },
        "nodes": {
            "base_name": "cnode",
            "count": config["nodes"],
            "region": config["oci_region"],
            "availability_domain": config["oci_availability_domain"] or "",
            "shape": config["node_shape"],
            "image_id": node_image_id or "",
            "compartment_id": config["compute_compartment_id"] or config["oci_compartment_id"],

            # For OCPUs/Memory 0 means "don't use the value in shape config". So, shape defaults will be used.
            "ocpus": config["node_number_cpus"] or 0,
            "memory_in_gb": config["node_memory_size"] or 0,

            "storage": {
                "root-disk": config["node_root_volume_size"],
            },
            "use_cluster_network": config["node_use_cluster_network"],
            "node_nsg_id": node_nsg_id,
            "node_instance_configuration_id": node_instance_configuration_id,
            "images_compartment_id": config["image_compartment_id"] or "",
        },
    }

    version = BcmVersion(config["version"])
    if version <= "11.0":
        brightsetup["modules"]["brightsetup"]["oci"]["nodes"]["images_manifest_base_url"] = (
            config["community_applications_url"] or ""
        )
    if version > "11.0":
        brightsetup["modules"]["brightsetup"]["oci"]["nodes"]["netboot_images_bucket_url"] = (
            config["netboot_images_bucket_url"] or ""
        )

    brightsetup["modules"]["brightsetup"]["oci"]["cluster_tags"] = {
        str(k): str(v) for k, v in config["cluster_tags"]
    }

    return brightsetup
