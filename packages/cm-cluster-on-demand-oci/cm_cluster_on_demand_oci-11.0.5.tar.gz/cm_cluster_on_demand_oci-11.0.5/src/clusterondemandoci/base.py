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
from collections import defaultdict
from collections.abc import Collection
from datetime import datetime
from functools import cached_property, lru_cache

import netaddr
import requests
from oci import wait_until
from oci.core.models import CreatePublicIpDetails, Instance, PrivateIp, PublicIp, Shape, Subnet, Vcn
from oci.exceptions import MaximumWaitTimeExceeded, ServiceError

from clusterondemand.exceptions import CODException
from clusterondemand.paramvalidation import ParamValidator
from clusterondemand.utils import validate_arch_vs_machine_arch
from clusterondemandconfig import config
from clusterondemandoci.const import CLUSTER_NAME_TAG
from clusterondemandoci.utils import get_compute_cid, get_instance_vnic_info, get_networking_cid, get_oci_api_client

log = logging.getLogger("cluster-on-demand")


class ClusterCommand:
    def __init__(self):
        self.client = get_oci_api_client()
        self.compute_cid = get_compute_cid()
        self.networking_cid = get_networking_cid()

    @cached_property
    def availability_domains(self):
        """Return the availability domains for the compartment ID"""
        return self.client.identity.get_availability_domains(self.compute_cid)

    @property
    def availability_domain_name(self):
        availability_domain_name = config["oci_availability_domain"]
        # If no availability domain was specified, use the first one in the list of available
        # availability domains. This was an arbitrary decision; we needed to use something and
        # this seemed like as good a starting point as any.

        if not availability_domain_name:
            availability_domain_name = config["oci_availability_domain"] = self.availability_domains[0].name
            log.debug(
                "No availability domain configured; selected '%s' from those in the configured compartment",
                availability_domain_name,
            )
        return availability_domain_name

    @staticmethod
    def _validate_cluster_name():
        ParamValidator.validate_cluster_name(config["name"], config["validate_max_cluster_name_length"])

    def _validate_region(self):
        try:
            # We have new/experimental regions that are not present in the OCI SDK. So we try to connect to the endpoint
            # We care only about the connection to the endpoint, not the response.
            # If there is no endpoint, we can't authenticate, can't execute any API calls, therefere
            # region can be considered invalid.
            requests.head(self.client.identity.endpoint, timeout=10)
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            raise CODException(f"Region validation failed: Unable to connect to {config['oci_region']} api endpoint.")

    def _validate_access_credentials(self):
        self._validate_region()
        try:
            self.client.identity.list_region_subscriptions()
        except ServiceError as e:
            if e.status == 401:
                raise CODException("OCI API Authentication failed: provided credentials are invalid.")

    def _validate_availability_domain(self):
        if all(domain.name != self.availability_domain_name for domain in self.availability_domains):
            raise CODException(
                f"Availability domain {self.availability_domain_name} is not valid"
                " for the provided compartment, please provide an availability domain"
                " or skip parameter to use a random availability domain")

    def _validate_defined_tags(self):
        if not config.get("head_node_defined_tags"):
            return

        try:
            # OCI allows compartments to nest up to six levels. Resources can have defined tags from their own, parent,
            # or peer compartments. This code fetches tag namespaces from all compartments under the root
            # (tenant ID matches root compartment ID).
            available_namespaces = {
                namespace.name: namespace.id for namespace in self.client.identity.list_tag_namespaces(
                    compartment_id=config["oci_tenancy"], include_subcompartments=True)
            }

            # Validate each tag namespace and defined tag provided by the user
            for namespace, tag_key, tag_value in config["head_node_defined_tags"]:
                if namespace not in available_namespaces:
                    available_namespaces = ', '.join(available_namespaces.keys())
                    raise CODException(f"Provided tag namespace '{namespace}' not found. "
                                       f"Available tag namespaces are: {available_namespaces}")

                # Fetch tags for the requested namespaces only
                available_tag_keys = {
                    tag.name for tag in self.client.identity.list_tags(
                        tag_namespace_id=available_namespaces[namespace]
                    )
                }

                if tag_key not in available_tag_keys:
                    raise CODException(
                        f"Provided tag '{tag_key}' from '{namespace}' namespace not found. "
                        f"Available tags in '{namespace}' namespace are: {', '.join(available_tag_keys)}"
                    )

        except ServiceError as se:
            raise CODException(f"OCI Service error: {se.message}")
        except CODException as ure:
            raise ure
        except Exception as e:
            raise CODException(f"Unexpected error: {str(e)}")

    def _generate_freeform_tags_for(self, object_type: str, cluster_name=None) -> dict[str, str]:
        if not cluster_name:
            cluster_name = config["name"]
        cur_time_str = datetime.utcnow().isoformat(timespec="milliseconds") + "Z"  # same as oci portal
        self._default_freeform_tags = {
            "BCM_Type": None,
            "BCM_Resource": "True",
            "BCM_Cluster": cluster_name,
            "BCM_Created_by": config["oci_user"],
            "BCM_Bursting": "on-demand",
            "BCM_Created_at": cur_time_str,  # "2023-07-03T09:04:52.555Z" (Z for UTC)
        }

        valid_object_types = [
            "Compute Node",
            "Head Node",
            "Internet Gateway",
            "NAT Gateway",
            "NSG",
            "Public IP",
            "Route Table",
            "Shared Public IP",
            "Subnet",
            "Virtual Cloud Network",
        ]
        if object_type not in valid_object_types:
            raise CODException(f"Unsupported object type '{object_type}'")

        return {**self._default_freeform_tags, "BCM_Type": object_type}

    @classmethod
    def _generate_defined_tags(cls):
        if not config["head_node_defined_tags"]:
            return {}

        merged_dict = defaultdict(dict)
        for namespace, tag_key, tag_value in config["head_node_defined_tags"]:
            merged_dict[namespace].update({tag_key: tag_value})

        return merged_dict

    def _validate_shape_architecture(self, instance_shape: Shape, instance_type: str) -> str:
        # oci.core.models.Shape does not have an attribute that directly points to the architecture. We infer it
        # Based on the processor description, assuming that all Intel and AMD processors are x86_64 and all
        # Ampere processors are aarch64.
        # https://docs.oracle.com/en-us/iaas/tools/python/2.152.0/api/core/models/oci.core.models.Shape.html
        shape_arch = None
        has_processor_desc = True

        try:
            assert instance_shape.processor_description
        except (AttributeError, AssertionError):
            has_processor_desc = False

        if has_processor_desc:
            if any(arch in instance_shape.processor_description.lower() for arch in ["amd", "intel"]):
                shape_arch = "x86_64"
            elif any(arch in instance_shape.processor_description.lower() for arch in ["arm", "ampere"]):
                shape_arch = "aarch64"

        return validate_arch_vs_machine_arch(config["arch"], shape_arch, instance_shape.shape, instance_type)

    def _validate_shape(self):
        # Wrong shape raises CODException from get_shape()
        head_shape = self.client.compute.get_shape(config["head_node_shape"],
                                                   self.availability_domain_name, self.compute_cid)
        node_shape = self.client.compute.get_shape(config["node_shape"],
                                                   self.availability_domain_name, self.compute_cid)
        config["arch"] = self._validate_shape_architecture(head_shape, "head node")
        self._validate_shape_architecture(node_shape, "compute node")

        if config["node_use_cluster_network"] and not node_shape.rdma_ports:
            raise CODException(f"The instance shape {config['node_shape']} does not support cluster "
                  "networks. See https://docs.oracle.com/en-us/iaas/api/#/en/iaas/20160918/Shape/ for more details.")

        # TODO(CM-45973): Remove the validation when BM shapes are supported.
        if head_shape.shape.startswith("BM."):
            raise CODException("Bare metal shapes are not supported yet for head node.")

        # TODO(CM-45942): Remove the validation when such shapes are supported.
        if node_shape.shape.startswith("BM.") and node_shape.local_disks == 0:
            raise CODException(
                f"Bare metal shape {node_shape.shape!r} has no local disks. "
                "Such shapes are not supported yet for compute nodes."
            )

    @lru_cache
    def _get_vcn(self, vcn_id: str) -> Vcn:
        try:
            return self.client.network.get_vcn(vcn_id)

        except ServiceError as error:
            if error.code == "NotAuthorizedOrNotFound":
                raise CODException(
                    f"Unable to retrieve VCN {vcn_id}."
                    f" Either the provided vcn_id doesn't exist or user permissions are not sufficient."
                    f" OCI error message: {error.message}"
                ) from error

            raise CODException(error.message) from error

    @lru_cache
    def _get_subnet(self, subnet_id: str) -> Subnet:
        try:
            return self.client.network.get_subnet(subnet_id)

        except ServiceError as error:
            if error.code == "NotAuthorizedOrNotFound":
                raise CODException(
                    f"Unable to retrieve subnet {subnet_id}."
                    f" Either the provided subnet_id doesn't exist or user permissions are not sufficient."
                    f" OCI error message: {error.message}"
                ) from error

            raise CODException(error.message) from error

    def _validate_head_node_ip(self):
        if not (head_node_ip := config["head_node_ip"]):
            return

        if config["existing_subnet_id"]:
            subnet = self._get_subnet(config["existing_subnet_id"][0])
            subnet_cidr = netaddr.IPNetwork(subnet.cidr_block)
        else:
            subnet_cidr = config["subnet_cidr"]

        if head_node_ip not in subnet_cidr:
            raise CODException(
                f"Head Node IP must be within the subnet CIDR: {head_node_ip} not in {subnet_cidr}"
            )
        self.client.compute.get_shape(config["head_node_shape"], self.availability_domain_name, self.compute_cid)
        self.client.compute.get_shape(config["node_shape"], self.availability_domain_name, self.compute_cid)

    def _get_instance_primary_ip(self, instance: Instance) -> str:
        """
        Returns the ip attached to the primary VNIC of the instance.

        :param instance: OCI instance object for the node
        :return: The public IP attached to the VNIC if present, otherwise the private IP
        """
        try:
            ip_address = next(
                (
                    vnic.public_ip or vnic.private_ip
                    for vnic in get_instance_vnic_info(instance=instance, client=self.client)
                )
            )
        except StopIteration:
            #
            # It may not actually be possible get here since every instance should have a VNIC. Just in case, however.
            raise CODException(f"Failed to get VNIC for {instance.display_name}")

        return ip_address

    def _get_vnic_shared_ips(self, vnic_id: str) -> tuple[PrivateIp | None, PublicIp | None]:
        log.debug(f"Finding shared IPs for vnic {vnic_id}")
        shared_public_ip = None
        private_ips = self.client.network.list_private_ips(vnic_id=vnic_id)
        shared_private_ip = next((private_ip for private_ip in private_ips
                                  if not private_ip.is_primary
                                  and private_ip.freeform_tags.get("BCM_Type") == "Shared Private IP"), None)

        if not shared_private_ip:
            log.debug("Shared private IP not found, not looking for shared public IP")
            return shared_private_ip, shared_public_ip

        compartment_public_ips = self.client.network.list_public_ips(
            compartment_id=self.compute_cid,
            scope="REGION",
            lifetime="RESERVED",
        )

        try:
            shared_public_ip = next(ip for ip in compartment_public_ips if ip.private_ip_id == shared_private_ip.id)
        except StopIteration:
            log.debug("Shared public IP not found, proceeding without it")

        return shared_private_ip, shared_public_ip

    def _create_shared_public_ip(self, head_node: Instance, private_ip: PrivateIp) -> PublicIp | None:

        cluster_name = head_node.freeform_tags.get(CLUSTER_NAME_TAG)
        try:
            create_public_ip_details = CreatePublicIpDetails(
                display_name=head_node.display_name + " shared public IP",
                compartment_id=self.compute_cid,
                private_ip_id=private_ip.id,
                lifetime="RESERVED",
                freeform_tags=self._generate_freeform_tags_for(
                    object_type="Shared Public IP",
                    cluster_name=cluster_name,
                ),
            )
            shared_public_ip = self.client.network.create_public_ip(
                create_public_ip_details=create_public_ip_details)
            log.info(f"Created Shared Public IP {shared_public_ip.ip_address} for head node {head_node.display_name}")
            return shared_public_ip

        except ServiceError as error:
            if error.code != "NotAuthorizedOrNotFound":
                raise
            log.warning("Failed to allocate shared public IP due to missing permissions")

    def _wait_for_instance_states(self,
                                  instance_id: str,
                                  states: Collection[str],
                                  max_wait_seconds: int = 1200,  # Default for oci.wait_until()
                                  ) -> Instance | None:

        compute_client = self.client.compute.compute_client

        # Wait for terminating states in addition to the target state, as OCI may terminate
        # the instance if something goes wrong.
        additional_states: list[str] = []
        if Instance.LIFECYCLE_STATE_TERMINATED not in states:
            additional_states = [
                Instance.LIFECYCLE_STATE_TERMINATED,
                Instance.LIFECYCLE_STATE_TERMINATING,
            ]
        try:
            log.debug(f"Waiting for instance {instance_id} to reach one of the following states: " + ', '.join(states))
            instance: Instance = wait_until(
                compute_client,
                compute_client.get_instance(instance_id),
                'lifecycle_state',
                tuple([*states, *additional_states]),
                max_wait_seconds=max_wait_seconds,
            ).data
        except MaximumWaitTimeExceeded:
            log.warning(f"Timed out waiting for instance {instance_id} to reach one of the following states: " +
                        ', '.join(states))
            return None

        if instance.lifecycle_state not in states:
            log.warning(f"Instance {instance.display_name} ({instance_id}) is not in expected state:"
                        f" {instance.lifecycle_state}. Expected state(s): {', '.join(states)}")
            return None

        return instance
