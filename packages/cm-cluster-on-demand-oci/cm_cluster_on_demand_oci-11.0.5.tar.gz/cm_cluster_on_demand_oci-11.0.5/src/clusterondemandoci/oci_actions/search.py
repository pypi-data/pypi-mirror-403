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
from typing import List, Optional

import oci.pagination
from oci.exceptions import ServiceError
from oci.resource_search import ResourceSearchClient
from oci.resource_search.models import ResourceSummary, SearchDetails, StructuredSearchDetails

from clusterondemand.exceptions import CODException
from clusterondemandoci.client_base import OCIClientBase

log = logging.getLogger("cluster-on-demand")


class OCIClientSearch(OCIClientBase):
    """
    Provides methods for interacting with the OCI Search endpoints
    """

    def __init__(self, config, **kwargs):
        super().__init__(config, **kwargs)

        self._search = ResourceSearchClient(config, **self._kwargs)

    def run_structured_query(self, query: str) -> List[ResourceSummary]:
        clean_query = ' '.join(query.split())
        # log.debug("Running query [%s]", clean_query)
        structured_search = StructuredSearchDetails(
            query=clean_query,
            type='Structured',
            matching_context_type=SearchDetails.MATCHING_CONTEXT_TYPE_NONE
        )

        try:
            matching_items = oci.pagination.list_call_get_all_results(
                self._search.search_resources,
                structured_search,
            )
        except ServiceError as error:
            if error.code == 'CannotParseRequest':
                raise CODException(
                    f"Failed to parse query [{query}]; ({error.message})"
                )

            raise CODException(error.message) from error

        return matching_items.data

    def query_items_by_freeform_tag(
        self,
        object_type: str,
        tag_key: str,
        tag_value: str,
        where_clause: Optional[str] = None
    ) -> List[ResourceSummary]:
        """
        Queries OCI for all resources of a particular type where a particular key has a particular value.

        :param object_type: Type of object for which to query. Should be a valid OCI type; details on how
            to get a list of types from OCI is available at :
            https://docs.oracle.com/en-us/iaas/Content/Search/Tasks/queryingresources.htm
        :param tag_key: Name of tag for which to check for a given value
        :param tag_value: The value of the tag
        :where_clause: [optional] Additional items to pass to the WHERE clause
        """
        query = (
            f"QUERY {object_type} resources WHERE"
            f" (freeformTags.key = '{tag_key}' && freeformTags.value = '{tag_value}')"
        )
        if where_clause:
            query += f" && {where_clause}"

        return self.run_structured_query(query)
