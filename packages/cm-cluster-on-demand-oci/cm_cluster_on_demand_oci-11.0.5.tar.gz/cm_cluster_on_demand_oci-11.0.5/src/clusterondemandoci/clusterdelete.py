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
import time

#
# XXX MAYBE MOVE
import oci.resource_search.models
from oci.core.models import (
    ClusterNetwork,
    Instance,
    InternetGateway,
    NatGateway,
    PublicIp,
    RouteTable,
    Subnet,
    Vcn,
    Volume
)
from oci.exceptions import TransientServiceError
from oci.file_storage.models import FileSystem, MountTarget

from clusterondemand.clusternameprefix import clusterprefix_ns
from clusterondemand.exceptions import CODException
from clusterondemand.utils import confirm, confirm_ns, log_no_clusters_found, multithread_run
from clusterondemandconfig import ConfigNamespace, config  # , may_not_equal_none
from clusterondemandoci.base import ClusterCommand
from clusterondemandoci.cluster import Cluster
from clusterondemandoci.const import CLUSTER_NAME_TAG

from .configuration import ociclustercommon_ns, ocicommon_ns

log = logging.getLogger("cluster-on-demand")

config_ns = ConfigNamespace("oci.cluster.delete", "cluster delete parameter")
config_ns.import_namespace(ocicommon_ns)
config_ns.import_namespace(ociclustercommon_ns)
config_ns.import_namespace(clusterprefix_ns)
config_ns.import_namespace(confirm_ns)

config_ns.add_switch_parameter(
    "dry_run",
    help="Do not actually delete the resources."
)
config_ns.add_repeating_positional_parameter(
    "filters",
    require_value=True,
    help="Cluster names or patterns. Wildcards are supported (e.g: \\*)",
)
config_ns.add_parameter(
    "delete_timeout",
    env="COD_DELETE_TIMEOUT",
    default=600,
    advanced=True,
    help="Timeout for resources deletion operations in seconds. Default 600.",
    validation=lambda x, c: c[x.key] is not None and c[x.key] > 0,
    type=int
)


def run_command():
    ClusterDelete().run()


class ClusterDelete(ClusterCommand):
    def __init__(self):
        super().__init__()
        self.home_region = next(r for r in self.client.identity.list_region_subscriptions() if r.is_home_region)

    def run(self):
        """
        Deletes a cluster

        Instances:
            Terminates all instances with our tags. Will log warnings if instance termination
            exceeds TIMEOUT seconds and throw an exception if it takes more than 2 * TIMEOUT seconds
        """

        if config["filters"]:
            compute_cid = self.compute_cid
            networking_cid = self.networking_cid
            clusters = Cluster.fetch_clusters()
            cluster_names = [c.cluster_name for c in clusters]
        else:
            log.error("Need to specify cluster name to be deleted")
            return

        if config["dry_run"]:
            log.info("--dry-run passed; no delete operations will be performed")

        if not cluster_names:
            log_no_clusters_found("delete")
            return
        tag_values = ", ".join(cluster_names)
        if not confirm(f"This will delete all OCI resources tagged as '{tag_values}'; continue?"):
            return

        log.debug("Cluster deletion starting")
        multithread_run(self.delete_cluster,
                        [(cluster, compute_cid, networking_cid)
                         for cluster in clusters],
                        5)

        log.debug("Cluster deletion complete")

    def delete_cluster(self, cluster: Cluster, compute_cid: str, networking_cid: str):
        # Delete HA resources unconditionally to account for broken clusters (CM-50501).
        self.delete_instances(compute_cid, cluster.cluster_name)
        self.delete_public_ips(compute_cid, cluster.cluster_name)
        self.delete_volumes(compute_cid, cluster.cluster_name)
        self.delete_mount_target(compute_cid, cluster.cluster_name)
        self.delete_file_system(compute_cid, cluster.cluster_name)
        self.delete_subnets(networking_cid, cluster.cluster_name)
        self.delete_route_tables(networking_cid, cluster.cluster_name)
        self.delete_internet_gateways(networking_cid, cluster.cluster_name)
        self.delete_nat_gateways(networking_cid, cluster.cluster_name)
        self.delete_instance_configurations(compute_cid, cluster.cluster_name)
        self.delete_vcns(networking_cid, cluster.cluster_name)

    def _wait_for_instances_to_terminate(
            self,
            instances_terminating: list[oci.resource_search.models.ResourceSummary],
            tag_value: str,
            work_request_id: str,
            opc_request_id: str) -> None:
        """
        Waits for all the instances in the passed in list to enter state TERMINATED

        :param instances_terminating: List of ResourceSummary objects obtained by searching for instance nodes
        :param tag_value:
        :param work_request_id: OCID of work requesting performing instance termination
        :param opc_request_id: ID of request
        """

        compartment_id = instances_terminating[0].compartment_id

        log.debug("Waiting for instance deletion to queue...")
        for _ in range(3):
            try:
                self.client.work_request.overwrite_config({"region": self.home_region.region_name})\
                    .wait_for_work_to_complete(work_request_id, opc_request_id)
                break
            except CODException:
                pass

        log.debug("Instance deletion enqueued")
        log.debug("work-request-id: %s", work_request_id)
        log.debug("ops-request-id: %s", opc_request_id)

        num_instances_to_terminate = len(instances_terminating)
        start_time = time.time()

        where_clause = (
            f"compartmentId = '{compartment_id}'"
        )

        log.debug("Monitoring instance termination status")
        while True:
            #
            # The goal here is to monitor the state of all the instances we're terminating, and return when they've
            # all been terminated. In principle, we could just run a query like:
            #
            # query instance resources where id in (ocid_1, ocid_2, ..., ocid_N)
            #
            # There are two problems with this. Firstly, Oracle's query language doesn't support IN() constructs, so
            # we'd need to do:
            #
            # (id = ocid_1 OR id = ocid_2 OR ...)
            #
            # The second issue is that Oracle cloud has a 50k character limit on query size, so cluster size could (in
            # principle) result in queries which were too large if we queried by OCID. Instead, we get a list of all
            # the instances matching our tags and then extract the instances we care about from that list in code.

            #
            # 1. Get a list of all instances in the cluster, regardless of state
            all_current_instances = self.client.search.query_items_by_freeform_tag(
                "instance",
                CLUSTER_NAME_TAG,
                tag_value,
                where_clause,
            )

            #
            # 2. Get a list of OCIDs of the instances we're terminating
            instances_terminating_ocid_list = [instance.identifier for instance in instances_terminating]

            #
            # 3. From the list of all instances, extract the ones we care about; these are the ones we'll track
            current_terminating_instances = [
                instance for instance in all_current_instances
                if instance.identifier in instances_terminating_ocid_list
            ]

            #
            # Build some useful messaging for the logs
            terminating_instance_states = [instance.lifecycle_state for instance in current_terminating_instances]
            num_terminated_instances = sum(
                1 for state in terminating_instance_states
                if state == Instance.LIFECYCLE_STATE_TERMINATED or
                state == Instance.LIFECYCLE_STATE_TERMINATING
            )
            pct_terminated_instances = (num_terminated_instances * 100) // num_instances_to_terminate

            log.info(
                "    [%s%%] %s of %s instances terminated",
                pct_terminated_instances,
                num_terminated_instances,
                num_instances_to_terminate,
            )

            elapsed_time = time.time() - start_time

            if pct_terminated_instances == 100:
                break

            if elapsed_time > config["delete_timeout"]:
                log.warning("Instance shutdown has taken '%s' seconds", elapsed_time)
            elif elapsed_time > config["delete_timeout"] * 2:
                raise CODException("Instance time has taken too long (~{elapsed_time} seconds)")

            time.sleep(15)

    def delete_instances(self, compartment_id: str, tag_value: str) -> None:
        #
        # XXX As an optimization, we could parallelize this a bit; the compute calls in one thread  and
        # XXX the individual (i.e. head) node in another.  It would save us about a minute and a half.
        self._delete_instances_cluster_network(compartment_id, tag_value)
        self._delete_instances_instance_pool(compartment_id, tag_value)
        self._delete_instances_individual(compartment_id, tag_value)

    def _delete_instances_cluster_network(self, compartment_id: str, tag_value: str) -> None:
        start_time = time.time()
        where_clause = (
            f"compartmentId = '{compartment_id}'"
            f" && lifeCycleState != '{ClusterNetwork.LIFECYCLE_STATE_TERMINATED}'"
            f" && lifeCycleState != '{ClusterNetwork.LIFECYCLE_STATE_TERMINATING}'"
        )

        cluster_network_summary_list = self.client.search.query_items_by_freeform_tag(
            "clusternetwork",
            CLUSTER_NAME_TAG,
            tag_value,
            where_clause,
        )

        if not cluster_network_summary_list:
            log.info("Cluster %s: No cluster networks '%s=%s'; skipping", tag_value,
                     CLUSTER_NAME_TAG, tag_value)
            return

        num_cluster_networks_to_delete = len(cluster_network_summary_list)
        log.info("Cluster %s: Deleting %d cluster network(s)", tag_value, num_cluster_networks_to_delete)

        if config["dry_run"]:
            return

        for cluster_network_summary in cluster_network_summary_list:
            self.client.compute.delete_cluster_network(cluster_network_summary.identifier)

        cluster_network_delete_elapsed_time = time.time() - start_time
        log.info(
            "Cluster %s: Terminated %d cluster network(s) in %0.2f seconds",
            tag_value,
            num_cluster_networks_to_delete,
            cluster_network_delete_elapsed_time
        )

    def _delete_instances_instance_pool(self, compartment_id: str, tag_value: str) -> None:
        start_time = time.time()
        where_clause = (
            f"compartmentId = '{compartment_id}'"
            f" && lifeCycleState != '{Instance.LIFECYCLE_STATE_TERMINATED}'"
            f" && lifeCycleState != '{Instance.LIFECYCLE_STATE_TERMINATING}'"
        )

        instance_pool_summary_list = self.client.search.query_items_by_freeform_tag(
            "instancePool",
            CLUSTER_NAME_TAG,
            tag_value,
            where_clause,
        )

        if not instance_pool_summary_list:
            log.info("Cluster %s: No instance pools found matching '%s=%s'; skipping", tag_value,
                     CLUSTER_NAME_TAG, tag_value)
            return

        num_instance_pools_to_delete = len(instance_pool_summary_list)
        log.info("Cluster %s: Deleting %d instance pool(s)", tag_value, num_instance_pools_to_delete)

        if config["dry_run"]:
            return

        for instance_pool_summary in instance_pool_summary_list:
            self.client.compute.delete_instance_pool(instance_pool_summary.identifier)

        instance_pool_delete_elapsed_time = time.time() - start_time
        log.info(
            "Cluster %s: Terminated %d instance pool(s) in %0.2f seconds",
            tag_value,
            num_instance_pools_to_delete,
            instance_pool_delete_elapsed_time
        )

    def _delete_instances_individual(self, compartment_id: str, tag_value: str) -> None:
        num_instances_to_terminate = 0
        where_clause = (
            f"compartmentId = '{compartment_id}'"
            f" && lifeCycleState != '{Instance.LIFECYCLE_STATE_TERMINATED}'"
            f" && lifeCycleState != '{Instance.LIFECYCLE_STATE_TERMINATING}'"
        )

        start_time = time.time()

        instances_to_delete_summary_list = self.client.search.query_items_by_freeform_tag(
            "instance",
            CLUSTER_NAME_TAG,
            tag_value,
            where_clause
        )

        if not instances_to_delete_summary_list:
            log.info("Cluster %s: No instances found matching '%s=%s'", tag_value, CLUSTER_NAME_TAG, tag_value)
            return

        if num_instances_to_terminate == 0:
            num_instances_to_terminate = len(instances_to_delete_summary_list)

        for instance_to_delete_summary in instances_to_delete_summary_list:
            log.info(
                "Cluster %s: Terminating %s (instance state: %s)...",
                tag_value,
                instance_to_delete_summary.display_name,
                instance_to_delete_summary.lifecycle_state,
            )

        if config["dry_run"]:
            return

        #
        # If there's only one instance, terminate it the easy way. This is sometimes faster than
        # using bulk delete on a single node; reductions of up to 20 seconds were seen in testing.
        if num_instances_to_terminate == 1:
            self.client.compute.terminate_instance(instance_to_delete_summary.identifier)
            instance_delete_elapsed_time = time.time() - start_time
            log.info(
                "Cluster %s: Terminated 1 instance in %0.2f seconds",
                tag_value,
                instance_delete_elapsed_time
            )
            return

        bulk_terminate_response_headers = self.client.identity\
            .overwrite_config({"region": self.home_region.region_name})\
            .bulk_terminate_instances(instances_to_delete_summary_list)

        log.info("Cluster %s: Waiting for instance(s) to terminate...", tag_value)

        self._wait_for_instances_to_terminate(
            instances_to_delete_summary_list,
            tag_value,
            bulk_terminate_response_headers['opc-work-request-id'],
            bulk_terminate_response_headers['opc-request-id'],
        )

        instance_delete_elapsed_time = time.time() - start_time
        log.info(
            "Cluster %s: Terminated %d instance(s) in %0.2f seconds",
            tag_value,
            num_instances_to_terminate,
            instance_delete_elapsed_time
        )

    def delete_public_ips(self, compartment_id: str, tag_value: str) -> None:
        where_clause = (
            f"compartmentId = '{compartment_id}'"
            f" && lifeCycleState != '{PublicIp.LIFECYCLE_STATE_TERMINATED}'"
            f" && lifeCycleState != '{PublicIp.LIFECYCLE_STATE_TERMINATING}'"
        )

        public_ip_summary_list = self.client.search.query_items_by_freeform_tag(
            "publicip",
            CLUSTER_NAME_TAG,
            tag_value,
            where_clause
        )
        public_ip_summary_list = [
            public_ip
            for public_ip in public_ip_summary_list
            if public_ip.freeform_tags["BCM_Type"] == "Public IP"
            or public_ip.freeform_tags["BCM_Type"] == "Shared Public IP"
        ]

        if not public_ip_summary_list:
            log.info("Cluster %s: No public IPs found matching '%s=%s'; skipping",
                     tag_value,
                     CLUSTER_NAME_TAG,
                     tag_value)
            return

        for public_ip in public_ip_summary_list:
            log.info(f"Cluster {tag_value}: Deleting public IP: {public_ip.display_name}")
            if not config["dry_run"]:
                self.client.network.delete_public_ip(public_ip.identifier)

    def delete_file_system(self, compartment_id: str, tag_value: str) -> None:
        where_clause = (
            f"compartmentId = '{compartment_id}'"
            f" && lifeCycleState != '{FileSystem.LIFECYCLE_STATE_DELETED}'"
            f" && lifeCycleState != '{FileSystem.LIFECYCLE_STATE_DELETING}'"
        )

        file_system_summary_list = self.client.search.query_items_by_freeform_tag(
            "filesystem",
            CLUSTER_NAME_TAG,
            tag_value,
            where_clause
        )

        if not file_system_summary_list:
            log.info("Cluster %s: No File Systems found matching '%s=%s'; skipping",
                     tag_value,
                     CLUSTER_NAME_TAG,
                     tag_value)
            return

        for file_system_summary in file_system_summary_list:
            log.info(f"Cluster {tag_value}: Deleting File System {file_system_summary.display_name}")
            if not config["dry_run"]:
                self.client.file_storage.delete_file_system_and_wait_for_state(file_system_summary.identifier)

    def delete_mount_target(self, compartment_id: str, tag_value: str) -> None:
        where_clause = (
            f"compartmentId = '{compartment_id}'"
            f" && lifeCycleState != '{MountTarget.LIFECYCLE_STATE_DELETED}'"
            f" && lifeCycleState != '{MountTarget.LIFECYCLE_STATE_DELETING}'"
        )

        mount_target_summary_list = self.client.search.query_items_by_freeform_tag(
            "mounttarget",
            CLUSTER_NAME_TAG,
            tag_value,
            where_clause
        )

        if not mount_target_summary_list:
            log.info(f"Cluster {tag_value}: No Mount Targets found matching "
                     f"'{CLUSTER_NAME_TAG}={tag_value}'; skipping")
            return

        for mount_target_summary in mount_target_summary_list:
            log.info("Cluster %s: Deleting Mount Target %r", tag_value, mount_target_summary.display_name)
            if not config["dry_run"]:
                self.client.file_storage.delete_mount_target_and_wait_for_state(mount_target_summary.identifier)

    def delete_volumes(self, compartment_id: str, tag_value: str) -> None:
        where_clause = (
            f"compartmentId = '{compartment_id}'"
            f" && lifeCycleState != '{Volume.LIFECYCLE_STATE_TERMINATED}'"
            f" && lifeCycleState != '{Volume.LIFECYCLE_STATE_TERMINATING}'"
        )
        volumes_summary_list = self.client.search.query_items_by_freeform_tag(
            "volume",
            CLUSTER_NAME_TAG,
            tag_value,
            where_clause
        )
        if not volumes_summary_list:
            log.info("Cluster %s: No volumes found matching '%s=%s'; skipping",
                     tag_value,
                     CLUSTER_NAME_TAG,
                     tag_value)
            return

        num_volumes = len(volumes_summary_list)
        log.info("Cluster %s: Deleting %d volume(s)", tag_value, num_volumes)

        block_storage = self.client.block_storage

        for i, volumes_summary in enumerate(volumes_summary_list):
            log.info("Cluster %s: Deleting %d of %d", CLUSTER_NAME_TAG, i + 1, num_volumes)
            if not config["dry_run"]:
                block_storage.delete_volume(volumes_summary.identifier)

        # FIXME: Optional, may be useful to be sure, all data was deleted.
        # for i, volumes_summary in enumerate(volumes_summary_list):
        #     log.info("Confirming deletion of %d of %d", i + 1, num_volumes)
        #     wait_until(
        #         block_storage,
        #         block_storage.get_volume(volumes_summary.identifier),
        #         'lifecycle_state',
        #         'TERMINATED'
        #     )

    def delete_subnets(self, compartment_id: str, tag_value: str) -> None:
        where_clause = (
            f"compartmentId = '{compartment_id}'"
            f" && lifeCycleState != '{Subnet.LIFECYCLE_STATE_TERMINATED}'"
            f" && lifeCycleState != '{Subnet.LIFECYCLE_STATE_TERMINATING}'"
        )
        subnet_resource_summary_list = self.client.search.query_items_by_freeform_tag(
            'subnet',
            CLUSTER_NAME_TAG,
            tag_value,
            where_clause,
        )

        if not subnet_resource_summary_list:
            log.info(
                "Cluster %s: No subnets found matching '%s=%s'; skipping",
                tag_value,
                CLUSTER_NAME_TAG,
                tag_value
            )
            return

        for subnet_resource_summary in subnet_resource_summary_list:
            log.info("Cluster %s: Deleting subnet %r", tag_value, subnet_resource_summary.display_name)
            if not config["dry_run"]:
                self.client.network.delete_subnet(subnet_resource_summary.identifier)

    def delete_internet_gateways(self, compartment_id: str, tag_value: str) -> None:
        where_clause = (
            f"compartmentId = '{compartment_id}'"
            f" && lifeCycleState != '{InternetGateway.LIFECYCLE_STATE_TERMINATED}'"
            f" && lifeCycleState != '{InternetGateway.LIFECYCLE_STATE_TERMINATING}'"
        )
        internet_gateway_summary_list = self.client.search.query_items_by_freeform_tag(
            'internetgateway',
            CLUSTER_NAME_TAG,
            tag_value,
            where_clause,
        )

        if not internet_gateway_summary_list:
            log.info(
                "Cluster %s: No Internet Gateways found matching '%s=%s'; skipping",
                tag_value,
                CLUSTER_NAME_TAG,
                tag_value
            )
            return

        for internet_gateway_summary in internet_gateway_summary_list:
            log.info("Cluster %s: Deleting internet gateway %r", tag_value, internet_gateway_summary.display_name)
            if not config["dry_run"]:
                self.client.network.delete_internet_gateway(internet_gateway_summary.identifier)

    def delete_nat_gateways(self, compartment_id: str, tag_value: str) -> None:
        where_clause = (
            f"compartmentId = '{compartment_id}'"
            f" && lifeCycleState != '{NatGateway.LIFECYCLE_STATE_TERMINATED}'"
            f" && lifeCycleState != '{NatGateway.LIFECYCLE_STATE_TERMINATING}'"
        )
        nat_gateway_summary_list = self.client.search.query_items_by_freeform_tag(
            'natgateway',
            CLUSTER_NAME_TAG,
            tag_value,
            where_clause,
        )

        if not nat_gateway_summary_list:
            log.info(
                "Cluster %s: No NAT Gateways found matching '%s=%s'; skipping",
                tag_value,
                CLUSTER_NAME_TAG,
                tag_value
            )
            return

        for nat_gateway_summary in nat_gateway_summary_list:
            log.info("Cluster %s: Deleting NAT gateway %r", tag_value, nat_gateway_summary.display_name)
            if not config["dry_run"]:
                self.client.network.delete_nat_gateway(nat_gateway_summary.identifier)

    def delete_route_tables(self, compartment_id: str, tag_value: str) -> None:
        """
        Deletes all route tables in supplied compartment which have the supplied tag. For the default route
        table, all rules are deleted; for all other route tables, the entire table is deleted.
        """
        where_clause = (
            f"compartmentId = '{compartment_id}'"
            f" && lifeCycleState != '{RouteTable.LIFECYCLE_STATE_TERMINATED}'"
            f" && lifeCycleState != '{RouteTable.LIFECYCLE_STATE_TERMINATING}'"
        )
        route_table_summary_list = self.client.search.query_items_by_freeform_tag(
            'routetable',
            CLUSTER_NAME_TAG,
            tag_value,
            where_clause,
        )

        if not route_table_summary_list:
            log.info(
                "Cluster %s: No route tables found matching '%s=%s'; skipping",
                tag_value,
                CLUSTER_NAME_TAG,
                tag_value
            )
            return

        for route_table_summary in route_table_summary_list:
            try:
                log.info("Cluster %s: Deleting route table %r", tag_value, route_table_summary.display_name)
                if not config["dry_run"]:
                    self.client.network.delete_route_table(route_table_summary.identifier)
            except TransientServiceError as error:
                #
                # Attempting to the delete the default route table for a VCN throws an exception; it's safe
                # to ignore because as long as the table has no rules, the VCN can still be deleted.
                if error.code == 'IncorrectState' and 'is the default for VCN' in error.message:
                    self.client.network.delete_all_route_table_rules(route_table_summary.identifier)
                else:
                    raise CODException(error.message) from error

    def delete_vcns(self, compartment_id: str, tag_value: str) -> None:
        where_clause = (
            f"compartmentId = '{compartment_id}'"
            f" && lifeCycleState != '{Vcn.LIFECYCLE_STATE_TERMINATED}'"
            f" && lifeCycleState != '{Vcn.LIFECYCLE_STATE_TERMINATING}'"
        )
        vcn_summary_list = self.client.search.query_items_by_freeform_tag(
            'vcn',
            CLUSTER_NAME_TAG,
            tag_value,
            where_clause,
        )

        if not vcn_summary_list:
            log.info(
                "Cluster %s: No VCNs found matching '%s=%s'; skipping",
                tag_value,
                CLUSTER_NAME_TAG,
                tag_value
            )
            return

        for vcn_summary in vcn_summary_list:
            log.info("Cluster %s: Deleting VCN %r", tag_value, vcn_summary.display_name)
            nsg_list = self.client.network.get_nsgs_in_vcn(vcn_summary.identifier, vcn_summary.compartment_id)
            for nsg in nsg_list:
                log.debug("Cluster %s: Deleting NSG %r", tag_value, nsg.display_name)
                if not config["dry_run"]:
                    self.client.network.delete_nsg(nsg.id)

            if not config["dry_run"]:
                self.client.network.delete_vcn(vcn_summary.identifier)

    def delete_instance_configurations(self, compartment_id: str, tag_value: str) -> None:
        where_clause = (
            f"compartmentId = '{compartment_id}'"
        )

        instance_configuration_summary_list = self.client.search.query_items_by_freeform_tag(
            'instanceConfiguration',
            CLUSTER_NAME_TAG,
            tag_value,
            where_clause,
        )

        if not instance_configuration_summary_list:
            log.info(
                "Cluster %s: No Instance Configurations found matching '%s=%s'; skipping",
                tag_value,
                CLUSTER_NAME_TAG,
                tag_value
            )
            return

        num_instance_configurations_to_delete = len(instance_configuration_summary_list)
        log.info(
            "Cluster %s: Deleting %s instance configuration(s)",
            tag_value,
            num_instance_configurations_to_delete,
        )

        if config["dry_run"]:
            return

        for instance_configuration_summary in instance_configuration_summary_list:
            self.client.compute.delete_instance_configuration(instance_configuration_summary.identifier)

    # =============  helpers  ================
    def _validate_params(self):
        self._validate_access_credentials()
