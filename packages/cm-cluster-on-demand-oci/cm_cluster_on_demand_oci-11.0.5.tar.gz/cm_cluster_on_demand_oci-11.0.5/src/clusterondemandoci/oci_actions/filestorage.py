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

from oci.file_storage import FileStorageClient, FileStorageClientCompositeOperations
from oci.file_storage.models import FileSystem, MountTarget

from clusterondemandoci.client_base import OCIClientBase


class OCIClientFileStorage(OCIClientBase):
    def __init__(self, config: dict, **kwargs: str):
        super().__init__(config, **kwargs)

        file_storage_client = FileStorageClient(config, **self._kwargs)
        self._filestorage = file_storage_client
        self._filestoragecomposite = FileStorageClientCompositeOperations(file_storage_client, **self._kwargs)

    def delete_file_system_and_wait_for_state(self, file_system_id: str) -> None:
        """
        Calls delete_file_system() and waits for the FileSystem acted upon to enter the given state(s).

        :param file_system_id:
            See
            https://docs.oracle.com/en-us/iaas/tools/python/2.104.1/api/file_storage/client/oci.file_storage.FileStorageClientCompositeOperations.html#oci.file_storage.FileStorageClientCompositeOperations.delete_file_system_and_wait_for_state
        """
        self._filestoragecomposite.delete_file_system_and_wait_for_state(
            file_system_id=file_system_id,
            wait_for_states=[FileSystem.LIFECYCLE_STATE_DELETED, FileSystem.LIFECYCLE_STATE_DELETING],
            operation_kwargs={
                "retry_strategy": self._get_retry_strategy(service_error_retry_config={429: [], 404: [], 409: []}),
            }
        )

    def delete_mount_target_and_wait_for_state(self, mount_target_id: str) -> None:
        """
        Calls delete_mount_target() and waits for the MountTarget acted upon to enter the given state(s).
        :param mount_target_id:
            See
            https://docs.oracle.com/en-us/iaas/tools/python/2.104.1/api/file_storage/client/oci.file_storage.FileStorageClientCompositeOperations.html#oci.file_storage.FileStorageClientCompositeOperations.delete_mount_target_and_wait_for_state
        """
        self._filestoragecomposite.delete_mount_target_and_wait_for_state(
            mount_target_id=mount_target_id,
            wait_for_states=[MountTarget.LIFECYCLE_STATE_DELETED, MountTarget.LIFECYCLE_STATE_DELETING],
            operation_kwargs={
                "retry_strategy": self._get_retry_strategy(service_error_retry_config={429: [], 404: [], 409: []}),
            }
        )
