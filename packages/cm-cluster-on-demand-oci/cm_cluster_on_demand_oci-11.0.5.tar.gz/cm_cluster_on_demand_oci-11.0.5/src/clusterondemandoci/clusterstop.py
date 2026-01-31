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
from oci.exceptions import ServiceError

from clusterondemand.clusternameprefix import clusterprefix_ns
from clusterondemand.ssh import clusterssh_ns
from clusterondemand.utils import confirm, confirm_ns, log_no_clusters_found, multithread_run
from clusterondemandconfig import ConfigNamespace, config
from clusterondemandoci.base import ClusterCommand
from clusterondemandoci.cluster import Cluster
from clusterondemandoci.const import CLUSTER_NAME_TAG

from .configuration import ociclustercommon_ns, ocicommon_ns

log = logging.getLogger("cluster-on-demand")


def run_command() -> None:
    return ClusterStop().run()


config_ns = ConfigNamespace("oci.cluster.stop")
config_ns.import_namespace(ocicommon_ns)
config_ns.import_namespace(ociclustercommon_ns)
config_ns.import_namespace(clusterprefix_ns)
config_ns.import_namespace(confirm_ns)
config_ns.import_namespace(clusterssh_ns)
config_ns.add_repeating_positional_parameter(
    "filters",
    require_value=True,
    help="Cluster names or patterns. Wildcards are supported (e.g: \\*)",
)


class ClusterStop(ClusterCommand):
    def _validate_params(self):
        self._validate_access_credentials()

    def run(self) -> None:
        self._validate_params()

        clusters = Cluster.fetch_clusters()
        if not clusters:
            log_no_clusters_found("stop")
            return

        if not confirm(
            "This will stop cluster(s) '{}', continue?".format(
                "', '".join([cluster.cluster_name for cluster in clusters]))
        ):
            return

        log.info("Stopping the cluster(s) '%s'", "', '".join([cluster.cluster_name for cluster in clusters]))

        multithread_run(
            self._stop_cluster,
            clusters,
            config["max_threads"]
        )

    def _stop_cluster(
        self,
        cluster: Cluster,
        wait_for_state_timeout: int = 60,
    ):
        """
        Stop all nodes in a cluster.

        :param cluster: Cluster object
        :param wait_for_state_timeout: timeout to wait for the nodes to reach some stable state,
        in which they can be stopped
        """
        cluster_name = cluster.cluster_name

        compute_nodes = [
            node
            for node in self.client.compute.list_instances(self.compute_cid)
            if node.freeform_tags.get(CLUSTER_NAME_TAG) == cluster_name
            and not node.freeform_tags.get("BCM_Type") == "Head Node"
        ]
        compute_node_ids = [instance.id for instance in compute_nodes]

        # No need to try stopping instances in those states
        ignore_states = [
            Instance.LIFECYCLE_STATE_STOPPING,
            Instance.LIFECYCLE_STATE_STOPPED,
            Instance.LIFECYCLE_STATE_TERMINATING,
            Instance.LIFECYCLE_STATE_TERMINATED,
        ]

        # In various cases, instance can be in a transitory state, such as "starting", "provisioning, etc.
        # It makes sense to wait for the instance to reach a "final" state, automatic change of which is unexpected.
        stable_states = [
            Instance.LIFECYCLE_STATE_STOPPED,
            Instance.LIFECYCLE_STATE_RUNNING,
            Instance.LIFECYCLE_STATE_TERMINATED,
        ]

        stable_instances: list[Instance] = multithread_run(
            lambda instance_id: self._wait_for_instance_states(
                instance_id=instance_id, states=stable_states, max_wait_seconds=wait_for_state_timeout
            ),
            compute_node_ids,
            max_threads=config["max_threads"]
        )
        stable_instances = [instance for instance in stable_instances if instance]

        instance_ids_to_stop = [
            instance.id for instance in stable_instances if instance.lifecycle_state not in ignore_states
        ]

        if instance_ids_to_stop:
            log.info(f"Stopping compute node(s) for '{cluster_name}'")
            multithread_run(
                lambda instance_id: self._stop_instance_via_oci_api(
                    instance_id=instance_id, is_headnode=False
                ),
                instance_ids_to_stop,
                max_threads=config["max_threads"]
            )
        else:
            log.info("No compute node(s) for '%s' to stop", cluster_name)

        if cluster.is_ha:
            for vnic in [cluster.primary_head_node_vnic, cluster.secondary_head_node_vnic]:
                if vnic:
                    _, shared_public_ip = self._get_vnic_shared_ips(vnic.id)
                    if shared_public_ip:
                        log.info(
                            f"Deleting shared public IP {shared_public_ip.ip_address} "
                            f"from head node {vnic.display_name}")
                        self.client.network.delete_public_ip(shared_public_ip.id)

        # Stop head node and wait for it to finish
        log.info("Stopping head node(s) for '%s'", cluster_name)
        if cluster.secondary_head_node:
            self._stop_instance_via_oci_api(instance_id=cluster.secondary_head_node.id, is_headnode=True)
        if cluster.primary_head_node:
            self._stop_instance_via_oci_api(instance_id=cluster.primary_head_node.id, is_headnode=True)

        log.info("Cluster '%s' stopped", cluster_name)

    # Currently not used
    def _stop_cluster_instance_pools(self, cluster_name, compartment_id):
        instance_pools_to_stop_summary_list = self.client.search.query_items_by_freeform_tag(
            "instancePool",
            CLUSTER_NAME_TAG,
            cluster_name,
            f"compartmentId = '{compartment_id}'"
            f" && lifeCycleState = '{Instance.LIFECYCLE_STATE_RUNNING}'"
        )
        for instance_pool_summary in instance_pools_to_stop_summary_list:
            self.client.compute.stop_instance_pool(instance_pool_summary.identifier, wait_for_states=[])

    def _stop_instance_via_oci_api(self, instance_id: str, is_headnode: bool = True) -> None:
        # We stop instances with "SOFTSTOP":
        # https://docs.oracle.com/en-us/iaas/tools/python/2.106.0/api/core/client/oci.core.ComputeClient.html?#oci.core.ComputeClient.instance_action
        # Once instance is in "STOPPING" state, OCI will eventually stop it (max 15 min). No need to wait for "STOPPED"
        wait_for_states = [
            Instance.LIFECYCLE_STATE_STOPPED,
        ]
        if not is_headnode:
            wait_for_states.append(Instance.LIFECYCLE_STATE_STOPPING)
        try:
            log.debug(f"Stopping instance {instance_id}")
            # force=False does "SOFTSTOP"
            self.client.compute.stop_instance(instance_id=instance_id,
                                              wait_for_states=wait_for_states,
                                              force=False)
        except ServiceError as se:
            if se.status == 409 and se.code == 'IncorrectState':
                log.debug(f"Instance {instance_id} is in a state that does not support 'STOP' action")
