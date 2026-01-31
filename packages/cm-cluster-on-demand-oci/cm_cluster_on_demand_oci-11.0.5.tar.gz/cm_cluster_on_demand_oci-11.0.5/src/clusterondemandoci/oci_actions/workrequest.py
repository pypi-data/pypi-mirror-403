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
import time

import oci.pagination
import oci.work_requests.models
from oci.work_requests import WorkRequestClient
from oci.work_requests.models import WorkRequest

from clusterondemand.exceptions import CODException
from clusterondemandoci.client_base import OCIClientBase

log = logging.getLogger("cluster-on-demand")

RETRY_TIMES = 1
ENQUEUE_TIMEOUT = 120


class OCIClientWorkRequest(OCIClientBase):
    """
    Provides methods for interacting with the OCI WorkRequest endpoints
    """
    def __init__(self, config, **kwargs):
        super().__init__(config, **kwargs)

        self._workrequest = WorkRequestClient(config, **self._kwargs)

    def wait_for_work_to_complete(self, work_request_id: str, opc_request_id: str) -> None:
        retries = RETRY_TIMES
        while retries > 0:
            start_time = time.time()
            status = None
            retries -= 1
            counter = 15
            while status is None or status == WorkRequest.STATUS_IN_PROGRESS or status == WorkRequest.STATUS_ACCEPTED:
                response = self._workrequest.get_work_request(
                    work_request_id=work_request_id,
                    opc_request_id=opc_request_id,
                )

                status = response.data.status
                percent = response.data.percent_complete

                log.info("    Enqueuing status: [%s] %s%% (Attempt %s of %s)",
                         status, percent, RETRY_TIMES - retries, RETRY_TIMES
                         )
                time.sleep(10)

                if time.time() - start_time >= ENQUEUE_TIMEOUT:
                    if counter > 0:
                        counter -= 1
                    else:
                        log.error(
                            "Waiting for work request id '%s' took more than %s seconds. Retry.",
                            work_request_id,
                            ENQUEUE_TIMEOUT,
                        )
                    break

        if status != WorkRequest.STATUS_SUCCEEDED:
            raise CODException("Failed to enqueue instance deletion")

    def get_work_request_logs(self, work_request_id: str) -> list[oci.work_requests.models.WorkRequestLogEntry]:
        work_request_logs_response = oci.pagination.list_call_get_all_results(
            self._workrequest.list_work_request_logs,
            work_request_id,
        )

        return list(reversed(work_request_logs_response.data))

    def get_work_request_errors(self, work_request_id: str) -> list[oci.work_requests.models.WorkRequestError]:
        work_request_errors_response = oci.pagination.list_call_get_all_results(
            self._workrequest.list_work_request_errors,
            work_request_id,
        )

        return list(reversed(work_request_errors_response.data))

    def get_work_request_logs_and_errors(
        self,
        work_request_id: str,
    ) -> dict[str, list[oci.work_requests.models.WorkRequestLogEntry | oci.work_requests.models.WorkRequestError]]:

        return {
            "logs": self.get_work_request_logs(work_request_id),
            "errors": self.get_work_request_errors(work_request_id),
        }

    def log_all_work_request_logs(self, work_request_id: str) -> None:
        all_work_request_logs = self.get_work_request_logs_and_errors(work_request_id)
        for log_entry in all_work_request_logs["logs"]:
            log.info(f"[WORK_REQUEST_LOG] - {log_entry.timestamp} - {log_entry.message}")

        if all_work_request_logs["errors"]:
            for error_entry in all_work_request_logs["errors"]:
                log.error(f"[WORK_REQUEST_ERROR] - {error_entry.timestamp} - {error_entry.message}")
        else:
            log.info(f"No error logs for work request {work_request_id}")
