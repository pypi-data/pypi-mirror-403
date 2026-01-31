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

# import logging

from oci.core import BlockstorageClient, BlockstorageClientCompositeOperations
from oci.core.models import Volume

from clusterondemandoci.client_base import OCIClientBase

# log = logging.getLogger("cluster-on-demand")


class OCIClientBlockstorage(OCIClientBase):
    def __init__(self, config: dict, **kwargs: str):
        super().__init__(config, **kwargs)

        self._blockstorage = BlockstorageClient(config, **self._kwargs)
        self._blockstoragecomposite = BlockstorageClientCompositeOperations(self._blockstorage)

    def create_volume(self, create_volume_details):
        """
        Creates a volume and waits until it becomes ready.

        :param create_volumes_details:
            See
            https://docs.oracle.com/en-us/iaas/tools/python/2.93.0/api/core/models/oci.core.models.CreateVolumeDetails.html

        :return: The data about created volume
        """
        response = self._blockstoragecomposite.create_volume_and_wait_for_state(
            create_volume_details=create_volume_details,
            wait_for_states=[Volume.LIFECYCLE_STATE_AVAILABLE],
            operation_kwargs={
                'retry_strategy': self._get_retry_strategy(service_error_retry_config={429: [], 404: [], 409: []}),
            }
        )
        return response.data

    def get_volume(self, bs_id: str):
        """
        Returns the volume by id

        :param bs_id: (str): volume id

        :return: The data about the volume
        """
        response = self._blockstorage.get_volume(bs_id)
        return response.data

    def list_volumes(self, **kwargs):
        """
        Returns the information about all volumes, limited by following optional parameters:

        - availability_domain (str) - The name of the availability domain.
        - compartment_id (str) - The OCID of the compartment.
        - limit (int) - For list pagination. The maximum number of results per page, or items to return in
            a paginated "List" call. For important details about how pagination works, see List Pagination.
        - page (str) - For list pagination. The value of the opc-next-page response header from the previous
            "List" call. For important details about how pagination works, see List Pagination.
        - display_name (str) - A filter to return only resources that match the given display name exactly.
        - sort_by (str) - The field to sort by. You can provide one sort order (sortOrder).
            Default order for TIMECREATED is descending. Default order for DISPLAYNAME is ascending.
            The DISPLAYNAME sort order is case sensitive. Allowed values are: "TIMECREATED", "DISPLAYNAME"
        - sort_order (str) - The sort order to use, either ascending (ASC) or descending (DESC).
            The DISPLAYNAME sort order is case sensitive.    Allowed values are: "ASC", "DESC"
        - volume_group_id (str) - The OCID of the volume group.
        - lifecycle_state (str) - A filter to only return resources that match the given lifecycle state.
            The state value is case-insensitive. Allowed values are: "PROVISIONING", "RESTORING", "AVAILABLE",
            "TERMINATING", "TERMINATED", "FAULTY"
        - retry_strategy (obj) - A retry strategy to apply to this specific operation/call. This will override
            any retry strategy set at the client-level.
        - allow_control_chars (bool) - allow_control_chars is a boolean to indicate whether or not this request
            should allow control characters in the response object. By default, the response will not allow
            control characters in strings

        :return: The data of the volume list
        """
        response = self._blockstorage.list_volumes(**kwargs)
        return response.data

    def delete_volume(self, vol_id: str) -> None:
        """
        Deletes a volume.
        Volume should not be attached to any active instance,
        otherwise it will be tried to delete for ~10 minutes and finally failed.
        Please, detach the volume or terminate the instance beforehand.

        :param vol_id: (str) volume id
        """

        self._blockstoragecomposite.delete_volume_and_wait_for_state(
            vol_id,
            wait_for_states=[Volume.LIFECYCLE_STATE_TERMINATED, Volume.LIFECYCLE_STATE_TERMINATING],
            operation_kwargs={
                'retry_strategy': self._get_retry_strategy(service_error_retry_config={429: [], 404: [], 409: []}),
            }
        )
