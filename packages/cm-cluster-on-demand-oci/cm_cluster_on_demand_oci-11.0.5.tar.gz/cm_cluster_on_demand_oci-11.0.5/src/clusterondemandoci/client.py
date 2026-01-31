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

import functools
import logging

from clusterondemandoci.oci_actions.blockstorage import OCIClientBlockstorage
from clusterondemandoci.oci_actions.compute import OCIClientCompute
from clusterondemandoci.oci_actions.filestorage import OCIClientFileStorage
from clusterondemandoci.oci_actions.identity import OCIClientIdentity
from clusterondemandoci.oci_actions.marketplace import OCIClientMarketplace
from clusterondemandoci.oci_actions.search import OCIClientSearch
from clusterondemandoci.oci_actions.virtual_network import OCIClientVCN
from clusterondemandoci.oci_actions.workrequest import OCIClientWorkRequest

log = logging.getLogger("cluster-on-demand")


class OCIClient:
    def __init__(self, config: dict, **kwargs: str):
        """
        Main OCI client class; provides access to other OCI per-service clients. For details
        on arguments, see :py:class:`~clusterondemandoci.client_base.OCIClientBase`
        """
        self._config = config
        self._kwargs = kwargs

    @functools.cached_property
    def network(self) -> OCIClientVCN:
        """
        Property which provides access to an instantiated instance
        of the :py:class:`~clusterondemandoci.oci_actions.vcn.OCIClientVCN` class
        """
        return OCIClientVCN(self._config, **self._kwargs)

    @functools.cached_property
    def compute(self) -> OCIClientCompute:
        """
        Property which provides access to an instantiated instance
        of the :py:class:`~clusterondemandoci.oci_actions.compute.OCIClientCompute` class
        """
        return OCIClientCompute(self._config, **self._kwargs)

    @functools.cached_property
    def marketplace(self) -> OCIClientMarketplace:
        """
        Property which provides access to an instantiated instance
        of the :py:class:`~clusterondemandoci.oci_actions.marketplace.OCIClientMarketplace` class
        """
        return OCIClientMarketplace(self._config, **self._kwargs)

    @functools.cached_property
    def identity(self) -> OCIClientIdentity:
        """
        Property which provides access to an instantiated instance
        of the :py:class:`~clusterondemandoci.oci_actions.identity.OCIClientIdentity` class
        """
        return OCIClientIdentity(self._config, **self._kwargs)

    @functools.cached_property
    def search(self) -> OCIClientSearch:
        """
        Property which provides access to an instantiated instance
        of the :py:class:`~clusterondemandoci.oci_actions.identity.OCIClientSearch` class
        """
        return OCIClientSearch(self._config, **self._kwargs)

    @functools.cached_property
    def work_request(self) -> OCIClientWorkRequest:
        """
        Property which provides access to an instantiated instance
        of the :py:class:`~clusterondemandoci.oci_actions.identity.OCIClientWorkRequest` class
        """
        return OCIClientWorkRequest(self._config, **self._kwargs)

    @functools.cached_property
    def block_storage(self) -> OCIClientBlockstorage:
        """
        Property which provides access to block storage
        of the :py:class:`~clusterondemandoci.oci_actions.vcn.OCIClientBlockstorage` class
        """
        return OCIClientBlockstorage(self._config, **self._kwargs)

    @functools.cached_property
    def file_storage(self) -> OCIClientFileStorage:
        """
        Property which provides access to file storage
        of the :py:class:`~clusterondemandoci.oci_actions.filestorage.OCIClientFileStorage` class
        """
        return OCIClientFileStorage(self._config, **self._kwargs)
