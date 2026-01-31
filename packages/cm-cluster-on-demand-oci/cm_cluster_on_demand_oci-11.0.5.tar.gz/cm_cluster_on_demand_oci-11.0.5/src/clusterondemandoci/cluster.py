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
from collections import defaultdict
from functools import cached_property

from oci.core.models import Instance, Vcn, Vnic

from clusterondemandconfig import config
from clusterondemandoci.const import BCM_HA_TAG, CLUSTER_NAME_TAG
from clusterondemandoci.utils import (
    get_compute_cid,
    get_head_node_list,
    get_instance_vnic_info,
    get_oci_api_client,
    get_public_ip_list,
    get_vcn_for_instance_vnic,
    get_vcn_list
)

log = logging.getLogger("cluster-on-demand")


class Cluster:
    """
    A Cluster is a collection of various resources
    Properly tagged head node and/or the VCN is a proof that the cluster exists
    The most common case is a cluster deployed in its own VCN, in which case the Cluster object will have both,
    head node(s) and VCN
    If the cluster was deployed in pre-existing VCN, then having a head node is enough to initialize Cluster and its
    VCN will be found later, using _set_vcn()
    We also consider scenarios when the cluster is broken, E.g. head node(s) missing. Such cases are handled as well
    """
    def __init__(self, cluster_name: str, head_nodes: list[Instance] = None, vcn: Vcn = None, oci_region: str = None):
        self.cluster_name: str = cluster_name
        self.head_nodes: list[Instance] = head_nodes if head_nodes else []
        self.cluster_vcn: Vcn = vcn

        self.primary_head_node: Instance | None = None
        self.secondary_head_node: Instance | None = None
        self._set_primary_secondary_head_nodes()
        self.is_ha: bool = bool(self.secondary_head_node)

        self.oci_region: str = oci_region
        self.client = get_oci_api_client(oci_region=oci_region)

        # If cluster_vcn is not set, the cluster is deployed in an existing VCN, we'll find it from the headnode
        if not self.cluster_vcn:
            self._set_vcn()

    @cached_property
    def primary_head_node_vnic(self) -> Vnic | None:
        primary_head_node_vnic = None
        if self.primary_head_node:
            log.debug(f"Finding vnic of the primary head node {self.primary_head_node.display_name}")
            # Assuming the first VCN is ours. SO far, this is the only use-case
            primary_head_node_vnic = get_instance_vnic_info(instance=self.primary_head_node, client=self.client)[0]
        return primary_head_node_vnic

    @cached_property
    def secondary_head_node_vnic(self) -> Vnic | None:
        secondary_head_node_vnic = None
        if self.secondary_head_node:
            log.debug(f"Finding vnic of the secondary head node {self.secondary_head_node.display_name}")
            # Assuming the first VCN is ours. So far, this is the only use-case
            secondary_head_node_vnic = get_instance_vnic_info(instance=self.secondary_head_node, client=self.client)[0]
        return secondary_head_node_vnic

    @classmethod
    def fetch_clusters(cls, oci_region: str | None = None) -> list[Cluster]:
        client = get_oci_api_client(oci_region=oci_region)
        compute_cid = get_compute_cid()

        head_nodes = [
            node for node in get_head_node_list(client=client, compute_cid=compute_cid, filtered=True)
            if node.lifecycle_state != Instance.LIFECYCLE_STATE_TERMINATED
        ]
        vcns = get_vcn_list(client=client, compute_cid=compute_cid, filters=config["filters"])

        public_ips = get_public_ip_list(client=client, compute_cid=compute_cid, filters=config["filters"])

        # We unite cluster names from both sources, head_node(s), vcn(s), etc.
        cluster_names = {head_node.freeform_tags.get(CLUSTER_NAME_TAG) for head_node in head_nodes} | \
                        {vcn.freeform_tags.get(CLUSTER_NAME_TAG) for vcn in vcns} | \
                        {public_ip.freeform_tags.get(CLUSTER_NAME_TAG) for public_ip in public_ips}
        # Filter out None names as we don't handle them elsewhere
        cluster_names = {cluster_name for cluster_name in cluster_names if cluster_name is not None}

        cluster_names_to_head_nodes: dict[str, list[Instance | None]] = defaultdict(list)
        cluster_names_to_vcn: dict[str, Vcn | None] = defaultdict(lambda: None)

        for head_node in head_nodes:
            cluster_names_to_head_nodes[head_node.freeform_tags[CLUSTER_NAME_TAG]].append(head_node)
        for vcn in vcns:
            if CLUSTER_NAME_TAG in vcn.freeform_tags:
                cluster_names_to_vcn[vcn.freeform_tags[CLUSTER_NAME_TAG]] = vcn
            else:
                log.debug(f"Skipping VCN because of missing {CLUSTER_NAME_TAG} tag: {vcn.display_name}")

        clusters: list[Cluster] = []

        for cluster_name in cluster_names:
            cluster_head_nodes = cluster_names_to_head_nodes.get(cluster_name, [])
            cluster_vcn = cluster_names_to_vcn.get(cluster_name, None)
            clusters.append(Cluster(cluster_name=cluster_name,
                                    head_nodes=cluster_head_nodes,
                                    vcn=cluster_vcn,
                                    oci_region=oci_region)
                            )

        return clusters

    def _set_primary_secondary_head_nodes(self) -> None:
        primary_head_node: Instance | None = None
        secondary_head_node: Instance | None = None

        if len(self.head_nodes) > 2:  # noqa: R506
            head_node_names = ", ".join([i.display_name for i in self.head_nodes])
            log.warning(f"Found more than two head nodes for the cluster {self.cluster_name}."
                        f"This is typically caused by incorrect tagging. Offending instances are: "
                        f"{head_node_names}")
        elif len(self.head_nodes) == 2:  # noqa: R506
            try:
                primary_head_node = next(head_node for head_node in self.head_nodes
                                         if head_node.freeform_tags.get(BCM_HA_TAG) == "Primary")
                secondary_head_node = next(head_node for head_node in self.head_nodes
                                           if head_node.freeform_tags.get(BCM_HA_TAG) == "Secondary")
            except StopIteration:
                log.warning(f"Cannot determine the primary and secondary head nodes for the "
                            f"'{self.cluster_name}' cluster based on the tags")
        elif len(self.head_nodes) == 1:
            head_node = self.head_nodes[0]
            if head_node.freeform_tags.get(BCM_HA_TAG) == "Secondary":
                secondary_head_node = head_node
            else:
                # Non-HA clusters don't have BCM_HA_TAG. It is set by cm-setup during the cluster creation.
                primary_head_node = head_node

        self.primary_head_node = primary_head_node
        self.secondary_head_node = secondary_head_node

    def _set_vcn(self) -> None:
        vcn: Vcn | None = None
        if self.primary_head_node_vnic:
            vcn = get_vcn_for_instance_vnic(client=self.client, vnic=self.primary_head_node_vnic)
        elif self.secondary_head_node_vnic:
            vcn = get_vcn_for_instance_vnic(client=self.client, vnic=self.secondary_head_node_vnic)

        self.cluster_vcn = vcn
