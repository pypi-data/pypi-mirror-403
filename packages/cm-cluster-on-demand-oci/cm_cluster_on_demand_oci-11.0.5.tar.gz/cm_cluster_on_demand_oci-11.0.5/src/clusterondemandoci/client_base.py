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

from oci.retry import RetryStrategyBuilder


class OCIClientBase:
    """
    Base class from which other OCI client classes can inherit.

    :param config:
        Dict in the format described in the `Python OCI SDK Documentation (Configuration)`__ and
        validated using :py:meth:`~oci.config.validate_config`
    :param kwargs
        keywords which are passed directly to the various oci.* clients when they're instantiated

    __ https://docs.oracle.com/en-us/iaas/tools/python/latest/configuration.html
    """

    def __init__(self, config: dict, **kwargs: str):
        self._config = config
        self._kwargs = kwargs

        self._kwargs["retry_strategy"] = self._get_retry_strategy()

    @staticmethod
    def _get_retry_strategy(**kwargs):
        """
        Creates the retry strategy used by all clients
        :return: retry strategy
        """

        #
        # With exponential backup, 3 attempts starting @ 1s == 1 + 2 + 4 + 8 + 16 == 31 seconds
        defaults = {
            "max_attempts": 6,
            "total_elapsed_time_seconds": 300,
            "service_error_retry_on_any_5xx": True,
            "service_error_retry_config": {429: [], 404: []}
        }

        retry_config = {}
        for retry_config_key, retry_config_default_value in defaults.items():
            retry_config[retry_config_key] = kwargs.get(retry_config_key) or retry_config_default_value

        retry_strategy_builder = RetryStrategyBuilder(
            max_attempts=retry_config["max_attempts"],
            total_elapsed_time_seconds=retry_config["total_elapsed_time_seconds"],
            service_error_retry_on_any_5xx=retry_config["service_error_retry_on_any_5xx"],
            service_error_retry_config=retry_config["service_error_retry_config"],
        )

        return retry_strategy_builder.get_retry_strategy()

    def overwrite_config(self, new_attrs: dict) -> OCIClientBase:
        """
        Creates a new client with new configuration

        @param new_attrs: config parameters to be updated
        @return: new client object of the same class as the original
        """
        new_config = self._config.copy()
        new_config.update(new_attrs)
        _client_class = type(self)

        return _client_class(new_config, **self._kwargs)
