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

import fnmatch
import functools
import getpass
import logging
import pathlib
import re

from oci.core.models import Instance, PublicIp, Vcn, Vnic
from oci.exceptions import InvalidPrivateKey, MissingPrivateKeyPassphrase, ServiceError
from oci.signer import load_private_key_from_file

from clusterondemand.clusternameprefix import ensure_cod_prefix
from clusterondemand.exceptions import CODException
from clusterondemandconfig import config
from clusterondemandoci.client import OCIClient
from clusterondemandoci.const import CLUSTER_NAME_TAG

log = logging.getLogger("cluster-on-demand")


def get_oci_config(oci_region: str | None = None) -> dict[str, str]:
    oci_config = {
        "user": config["oci_user"],
        "key_file": config["oci_key_file"],
        "pass_phrase": config["oci_pass_phrase"],
        "fingerprint": config["oci_fingerprint"],
        "tenancy": config["oci_tenancy"],
        "region": oci_region or config["oci_region"]
    }
    if config.get("oci_key_file"):
        oci_config["key_file"] = config["oci_key_file"]
    else:
        oci_config["key_content"] = config["oci_key_content"]
    return oci_config


@functools.cache
def get_oci_key_content() -> str:
    oci_config = get_oci_config()
    if (key_file_name := oci_config.get("key_file")):
        filepath = pathlib.Path(key_file_name)
        with open(filepath.expanduser().resolve(), encoding="UTF-8") as filehandle:
            key_content = filehandle.read().rstrip()
    else:
        key_content = oci_config["key_content"]
    return key_content


@functools.cache
def get_compute_cid() -> str:
    """Return the configured compute compartment ID"""
    return config["compute_compartment_id"] or config["oci_compartment_id"]


@functools.cache
def get_networking_cid() -> str:
    """Return the configured network compartment ID"""
    return config["networking_compartment_id"] or config["oci_compartment_id"]


@functools.cache
def get_oci_api_client(oci_region: str | None = None) -> OCIClient:
    cached_pass_phrases = {}
    oci_config = get_oci_config(oci_region=oci_region) | {
        "pass_phrase": config["oci_pass_phrase"] or cached_pass_phrases.get(config["oci_key_file"]),
    }

    # First check if the private key is valid; if it is but is missing a passphrase, prompt the user
    try:
        if oci_config["key_file"]:
            load_private_key_from_file(oci_config["key_file"], oci_config["pass_phrase"])
    except MissingPrivateKeyPassphrase:
        while cached_pass_phrases.get(oci_config["key_file"]) is None:
            try:
                oci_config["pass_phrase"] = getpass.getpass("OCI Key File Passphrase (empty string to abort): ")
                load_private_key_from_file(oci_config["key_file"], oci_config["pass_phrase"])
                # Passphrase valid; cache it so the user is only prompted once
                cached_pass_phrases[oci_config["key_file"]] = oci_config["pass_phrase"]
                config["oci_pass_phrase"] = oci_config["pass_phrase"]
                if "use_principal_authentication" in config:
                    config["use_principal_authentication"] = True
            except InvalidPrivateKey:  # Wrong passphrase, try again
                pass

    return OCIClient(oci_config)


def get_instance_vnic_info(instance: Instance, client: OCIClient) -> list[Vnic]:
    try:
        vnic_attachment_list = client.compute.get_vnic_attachments(instance)
        vnic_list = []
        #
        # XXX We may want to smarten this up to handle multiple VNICs / not-our VNICs
        for vnic_attachment in vnic_attachment_list:
            vnic_list.append(client.network.get_vnic(vnic_attachment.vnic_id))

        return vnic_list
    except ServiceError as error:
        raise CODException(error.message) from error


def get_vcn_for_instance_vnic(client: OCIClient, vnic: Vnic) -> Vcn:
    log.debug(f"Finding vcn from vnic {vnic.id}")
    subnet_id = vnic.subnet_id
    subnet = client.network.get_subnet(subnet_id)
    return client.network.get_vcn(subnet.vcn_id)


def get_vcn_list(client: OCIClient, compute_cid: str, filters: list[str] | None = None, ) -> list[Vcn]:
    log.debug(f"Listing vcns in compartment {compute_cid}")
    vcn_list = client.network.list_vcns(compartment_id=compute_cid)

    if filters:
        regexes = [fnmatch.translate(ensure_cod_prefix(pattern)) for pattern in filters]
        vcn_list = [
            vcn for vcn in vcn_list
            if any(re.match(regex, vcn.freeform_tags.get(CLUSTER_NAME_TAG, "")) for regex in regexes)
        ]

    return vcn_list


def get_instance_list(client: OCIClient, compute_cid: str) -> list[Instance]:
    instance_list = client.compute.list_instances(compute_cid)
    return instance_list


def get_head_node_list(client: OCIClient, compute_cid: str, filtered=False) -> list[Instance]:
    """
    Retrieve a list of all head nodes in the current compartment.

    :param filtered: whether to filter the list of head nodes using the filters in `config["filters"]`
    """
    log.debug(f"Listing instances in compartment {compute_cid}")
    head_node_list = [i for i in get_instance_list(client=client, compute_cid=compute_cid)
                      if i.freeform_tags.get("BCM_Type") == "Head Node"]

    if filtered and config["filters"]:
        regexes = [fnmatch.translate(ensure_cod_prefix(pattern)) for pattern in config["filters"]]
        head_node_list = [
            node for node in head_node_list
            if any(re.match(regex, node.freeform_tags.get(CLUSTER_NAME_TAG)) for regex in regexes)
        ]

    return head_node_list


def get_public_ip_list(client: OCIClient, compute_cid: str, filters: list[str] | None = None) -> list[PublicIp]:
    log.debug(f"Listing public IPs in compartment {compute_cid}")

    public_ips = client.network.list_public_ips(
        compartment_id=compute_cid, scope="REGION", lifetime="RESERVED"
    )

    if filters:
        regexes = [fnmatch.translate(ensure_cod_prefix(pattern)) for pattern in filters]
        public_ips = [
            public_ip for public_ip in public_ips
            if any(re.match(regex, public_ip.freeform_tags.get(CLUSTER_NAME_TAG, "")) for regex in regexes)
        ]

    return public_ips


def parse_defined_tags(s: str) -> tuple[str, str, str]:
    # Convert user input string to a dictionary early, to build configuration.
    # Postponing detailed tag validation to subsequent stages.
    expected_tag_format = "namespace.tag_key.tag_value"
    try:
        namespace, tag_key, tag_value = s.split(".", maxsplit=2)
    except Exception as e:
        raise CODException(
            f"Unable to parse provided tag.\n"
            f"Expected format: {expected_tag_format!r}, received {s!r}.\n"
            f"Error: {e}"
        )

    return namespace, tag_key, tag_value
