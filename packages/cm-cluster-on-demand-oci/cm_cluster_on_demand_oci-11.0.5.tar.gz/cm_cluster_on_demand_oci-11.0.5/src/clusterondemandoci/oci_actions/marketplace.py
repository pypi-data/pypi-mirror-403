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

import logging

import oci.marketplace

from clusterondemandoci.client_base import OCIClientBase

log = logging.getLogger("cluster-on-demand")

DEFAULT_PACKAGE_VERSION = "empty-version"


class OCIClientMarketplace(OCIClientBase):
    """
    Provides methods for interacting with the OCI marketplace endpoints
    """

    def __init__(self, config, **kwargs):
        super().__init__(config, **kwargs)
        self._marketplace = oci.marketplace.MarketplaceClient(config, **self._kwargs)

    def get_image(self, publication_id: str) -> oci.marketplace.models.ImageListingPackage:
        return self._marketplace.get_package(publication_id, DEFAULT_PACKAGE_VERSION).data

    def get_image_publication(self, publication_id: str) -> oci.marketplace.models.Publication:
        return self._marketplace.get_publication(publication_id).data

    def get_image_agreements_to_accept(
        self,
        publication_id: str,
        compartment_id: str
    ) -> list[oci.marketplace.models.AgreementSummary]:
        accepted_agreements: list[oci.marketplace.models.AcceptedAgreementSummary]
        accepted_agreements = {
            accepted.agreement_id
            for accepted in self._marketplace.list_accepted_agreements(compartment_id,
                                                                       listing_id=publication_id,
                                                                       package_version=DEFAULT_PACKAGE_VERSION).data
        }
        return [
            agreement
            for agreement in self._marketplace.list_agreements(publication_id, DEFAULT_PACKAGE_VERSION).data
            if agreement.id not in accepted_agreements
        ]

    def accept_image_agreements(
        self,
        compartment_id: str,
        publication_id: str,
        agreement_ids: list[str],
    ) -> None:
        for agreement_id in agreement_ids:
            agreement: oci.marketplace.models.Agreement
            agreement = self._marketplace.get_agreement(publication_id, DEFAULT_PACKAGE_VERSION, agreement_id).data
            self._marketplace.create_accepted_agreement(
                oci.marketplace.models.CreateAcceptedAgreementDetails(
                    compartment_id=compartment_id,
                    listing_id=publication_id,
                    package_version=DEFAULT_PACKAGE_VERSION,
                    agreement_id=agreement.id,
                    signature=agreement.signature,
                )
            )
