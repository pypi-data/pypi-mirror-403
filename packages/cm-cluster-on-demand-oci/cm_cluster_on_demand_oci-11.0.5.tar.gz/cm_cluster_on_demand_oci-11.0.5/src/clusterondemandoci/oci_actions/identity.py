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
from functools import lru_cache

import oci.identity
import oci.pagination
from oci.identity.models import Compartment, CreateCompartmentDetails

from clusterondemand.exceptions import CODException
from clusterondemandoci.client_base import OCIClientBase

log = logging.getLogger("cluster-on-demand")


class OCIClientIdentity(OCIClientBase):
    """
    Provides methods for interacting with the OCI Identity endpoints
    """

    def __init__(self, config, **kwargs):
        super().__init__(config, **kwargs)

        self._identity = oci.identity.IdentityClient(config, **self._kwargs)
        self._identitycomposite = oci.identity.IdentityClientCompositeOperations(self._identity)
        self.endpoint = self._identity.base_client.endpoint

    @lru_cache
    def list_region_subscriptions(self) -> list[oci.identity.models.RegionSubscription]:
        """
        Lists the region subscriptions for the tenancy.
        :return:
            RegionSubscription list
        """
        region_subscriptions = oci.pagination.list_call_get_all_results(
            self._identity.list_region_subscriptions,
            self._config["tenancy"],
        ).data
        return region_subscriptions

    def list_tag_namespaces(
            self, compartment_id: str, include_subcompartments: bool
    ) -> list[oci.identity.models.TagNamespace]:
        """
        Lists tag namespaces for the given compartment.

        :param compartment_id:
            OCID of the compartment in which to search for the availability domain
        :param include_subcompartments:
            Whether list tag namespaces of the sub-compartments of a given compartment id.
        :return:
            TagNamespace list
        """
        tag_namespaces = oci.pagination.list_call_get_all_results(
            self._identity.list_tag_namespaces,
            compartment_id=compartment_id, include_subcompartments=include_subcompartments
        ).data
        return tag_namespaces

    def list_tags(self, tag_namespace_id: str) -> list[oci.identity.models.TagNamespaceSummary]:
        """
        Lists defined tags in a specified namespace.

        :param tag_namespace_id:
            OCI ID of the tag namespace in which we're listing defined tags.
        :return:
            TagNamespaceSummary list
        """
        tags = oci.pagination.list_call_get_all_results(
            self._identity.list_tags,
            tag_namespace_id=tag_namespace_id
        ).data
        return tags

    def get_availability_domains(self, compartment_id: str) -> list[oci.identity.models.AvailabilityDomain]:
        """
        Fetches all availability domains available in a given compartment

        :param compartment_id:
            OCID of the compartment in which to search for the availability domain
        :return:
            AvailabilityDomain list
        """
        response = self._identity.list_availability_domains(compartment_id)
        return response.data

    def get_availability_domain(
            self,
            availability_domain_name: str,
            compartment_id: str) -> oci.identity.models.availability_domain.AvailabilityDomain:
        """
        Fetches an availability domain object from a compartment

        :param availability_domain_name
            Name of the availability domain to fetch
        :param compartment_id:
            OCID of the compartment in which to search for the availability domain
        """

        list_availability_domains_response = oci.pagination.list_call_get_all_results(
            self._identity.list_availability_domains,
            compartment_id,
        )

        availability_domain_list = list_availability_domains_response.data
        availability_domain = next((x for x in availability_domain_list if x.name == availability_domain_name), None)

        return availability_domain

    def get_user(self, user_id: str) -> oci.identity.models.User:
        """
        Fetches user metadata from OCI

        :param user_id: OCI user Id
        :return: A :class:`~oci.identity.models.User` object
        """
        response = self._identity.get_user(user_id)
        return response.data

    def create_compartment(self, compartment_details: CreateCompartmentDetails) -> Compartment:
        """
        Creates new compartment

        :param compartment_details:
        :return:
        """

        response = self._identitycomposite.create_compartment_and_wait_for_state(
            compartment_details,
            wait_for_states=[Compartment.LIFECYCLE_STATE_ACTIVE])

        return response.data

    def get_compartment(self, compartment_id: str) -> Compartment:
        """
        Fetches compartment from OCI

        :param compartment_id: OCI compartment Id
        :return: A :class:`~oci.identity.models.Compartment` object
        """
        return self._identity.get_compartment(compartment_id).data

    def bulk_terminate_instances(self, instances: list) -> dict:
        # OCI bulk operation version
        compartment_id = instances[0].compartment_id
        num_instances_to_terminate = len(instances)
        log.debug("Enqueuing bulk terminate of %s instance(s)", num_instances_to_terminate)

        bulk_delete_response = self._identitycomposite.bulk_delete_resources_and_wait_for_state(
            compartment_id=compartment_id,
            bulk_delete_resources_details=oci.identity.models.BulkDeleteResourcesDetails(
                resources=[
                    oci.identity.models.BulkActionResource(
                        identifier=instance.identifier,
                        entity_type="Instance",
                    )
                    for instance in instances
                ]
            ),
        )

        if bulk_delete_response.status == 202:
            return bulk_delete_response.headers

        raise CODException(
            f"Got back unexpected response {bulk_delete_response.status}; server"
            f" returned {bulk_delete_response.headers}"
        )
