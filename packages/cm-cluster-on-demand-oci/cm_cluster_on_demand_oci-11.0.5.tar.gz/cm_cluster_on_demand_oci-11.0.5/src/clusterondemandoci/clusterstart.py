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

from oci.core.models import Instance

from clusterondemand.clusternameprefix import clusterprefix_ns
from clusterondemand.utils import confirm, confirm_ns, log_no_clusters_found, multithread_run
from clusterondemandconfig import ConfigNamespace, config
from clusterondemandoci.base import ClusterCommand
from clusterondemandoci.cluster import Cluster

from .configuration import ociclustercommon_ns, ocicommon_ns

log = logging.getLogger("cluster-on-demand")


def run_command() -> None:
    return ClusterStart().run()


config_ns = ConfigNamespace("oci.cluster.start")
config_ns.import_namespace(ocicommon_ns)
config_ns.import_namespace(ociclustercommon_ns)
config_ns.import_namespace(clusterprefix_ns)
config_ns.import_namespace(confirm_ns)
config_ns.add_repeating_positional_parameter(
    "filters",
    require_value=True,
    help="Cluster names or patterns. Wildcards are supported (e.g: \\*)",
)


class ClusterStart(ClusterCommand):
    def _validate_params(self):
        self._validate_access_credentials()

    def run(self) -> None:
        self._validate_params()

        clusters = Cluster.fetch_clusters()
        if not clusters:
            log_no_clusters_found("start")
            return

        if not confirm("This will start cluster(s) '{}', continue?".format(
            "', '".join([cluster.cluster_name for cluster in clusters]))
        ):
            return

        log.info("Starting cluster(s) '{}'".format("', '".join([cluster.cluster_name for cluster in clusters])))

        multithread_run(
            function=self._start_cluster,
            args_list=clusters,
            max_threads=config["max_threads"]
        )

    def _create_public_ips(self, head_node: Instance, vnic_id: str) -> None:
        shared_private_ip = next(
            (ip for ip in self.client.network.list_private_ips(vnic_id=vnic_id)
             if not ip.is_primary and ip.freeform_tags.get(
                "BCM_Type") == "Shared Private IP"),
            None
        )
        if shared_private_ip:
            log.debug(f"Creating public IP for the headnode {head_node.display_name}")
            self._create_shared_public_ip(head_node=head_node, private_ip=shared_private_ip)

    def _start_cluster(self, cluster: Cluster) -> None:
        log.info(f"Starting head node(s) for cluster {cluster.cluster_name}")
        if cluster.primary_head_node:
            self.client.compute.start_instance(cluster.primary_head_node.id)
            if cluster.primary_head_node_vnic:
                self._create_public_ips(cluster.primary_head_node, cluster.primary_head_node_vnic.id)
            else:
                log.error(f"VNIC is missing for {cluster.primary_head_node.display_name}, unable to create public "
                          f"shared IP")

        if cluster.secondary_head_node:
            self.client.compute.start_instance(cluster.secondary_head_node.id)
            if cluster.secondary_head_node_vnic:
                self._create_public_ips(cluster.secondary_head_node, cluster.secondary_head_node_vnic.id)
            else:
                log.error(f"VNIC is missing for {cluster.secondary_head_node.display_name}, unable to create public "
                          f"shared IP")
