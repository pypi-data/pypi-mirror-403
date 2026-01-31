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

import clusterondemand.configuration
from clusterondemand.clusternameprefix import clusterprefix_ns
from clusterondemand.codoutput.sortingutils import ClusterIPs, SortableData
from clusterondemand.utils import log_no_clusters_found
from clusterondemandconfig import ConfigNamespace, config
from clusterondemandoci.base import ClusterCommand
from clusterondemandoci.cluster import Cluster
from clusterondemandoci.const import IMAGE_CREATED_TIME_TAG, IMAGE_NAME_TAG

from .configuration import ociclustercommon_ns, ocicommon_ns

log = logging.getLogger("cluster-on-demand")

#
# XXX These columns are just a guess.
ALL_COLUMNS = [
    ("cluster_name", "Cluster Name"),
    ("vcn_name", "VCN Name"),
    ("oci_region", "Region"),
    ("head_node_name", "Head node name"),
    ("head_node_id", "Head node ID"),
    ("cluster_ip", "Cluster IP"),
    ("state", "State"),
    ("shape", "Shape"),
    ("head_node_cpu", "Head node CPU cores"),
    ("head_node_ram", "Head node RAM (mb)"),
    ("image_name", "Image Name"),
    ("created", "Image Created"),
]


DEFAULT_COLUMNS = [
    ("cluster_name", "Cluster Name"),
    ("vcn_name", "VCN Name"),
    ("cluster_ip", "Cluster IP"),
    ("state", "State"),
    ("shape", "Shape"),
    ("image_name", "Image Name"),
    ("created", "Image Created"),
]


def run_command() -> None:
    return ClusterList().run()


config_ns = ConfigNamespace("oci.cluster.list", "list output parameters")
config_ns.import_namespace(ocicommon_ns)
config_ns.import_namespace(ociclustercommon_ns)
config_ns.import_namespace(clusterprefix_ns)
config_ns.import_namespace(clusterondemand.configuration.clusterlist_ns)
config_ns.add_enumeration_parameter(
    "sort",
    default=["oci_region", "created"],
    choices=[column[0] for column in ALL_COLUMNS],
    help="Sort results by one (or two) of the columns"
)
config_ns.add_enumeration_parameter(
    "columns",
    choices=[column[0] for column in ALL_COLUMNS],
    help="Provide space separated set of columns to be displayed"
)
config_ns.add_repeating_positional_parameter(
    "filters",
    default=["*"],
    require_value=True,
    help="Cluster names or patterns to be listed. Default: all clusters. Wildcards are supported (e.g: \\*)",
)
config_ns.add_switch_parameter(
    "all_regions",
    default=False,
    help="List clusters in all subscribed infrastructure regions",
)


class ClusterList(ClusterCommand):
    def _validate_params(self):
        self._validate_access_credentials()

    def run(self) -> None:
        self._validate_params()

        region_names = [config["oci_region"]]
        if config["all_regions"]:
            region_names = [region.region_name for region in self.client.identity.list_region_subscriptions()]

        log.info(f"Listing clusters in region(s): {', '.join(region_names)}")
        clusters = [
            cluster for region_name in region_names for cluster in Cluster.fetch_clusters(oci_region=region_name)
        ]

        if not clusters:
            log_no_clusters_found("list")
            return

        log.debug(f"Building data for {len(clusters)} clusters")

        rows = []

        for cluster in clusters:
            row = self._build_table_row_from_cluster(cluster=cluster)
            rows.append(row)

        cols_id = config["columns"]
        if not cols_id:
            cols_id = [column[0] for column in DEFAULT_COLUMNS]
            if config["all_regions"]:
                cols_id.insert(2, "oci_region")

        table = SortableData(
            all_headers=ALL_COLUMNS,
            requested_headers=cols_id,
            rows=rows
        )
        table.sort(*config["sort"])

        print(table.output(output_format=config["output_format"]))

    def _build_table_row_from_cluster(self, cluster: Cluster):
        row = []
        row += [cluster.cluster_name]

        row += [cluster.cluster_vcn.display_name if cluster.cluster_vcn else "N/A"]
        row += [cluster.oci_region]

        if cluster.is_ha:
            if cluster.primary_head_node_vnic:
                primary_shared_private_ip, primary_shared_public_ip = self._get_vnic_shared_ips(
                    cluster.primary_head_node_vnic.id)
            else:
                primary_shared_private_ip, primary_shared_public_ip = None, None

            if cluster.secondary_head_node_vnic:
                secondary_shared_private_ip, secondary_shared_public_ip = self._get_vnic_shared_ips(
                    cluster.secondary_head_node_vnic.id)
            else:
                secondary_shared_private_ip, secondary_shared_public_ip = None, None

            if primary_shared_private_ip:
                ha_private_ip = primary_shared_private_ip
                ha_public_ip = primary_shared_public_ip
            elif secondary_shared_private_ip:
                ha_private_ip = secondary_shared_private_ip
                ha_public_ip = secondary_shared_public_ip
            else:
                ha_private_ip = None
                ha_public_ip = None

            row += ["\n".join(
                [cluster.primary_head_node.display_name + " (A)" if cluster.primary_head_node else "missing"]
                + [cluster.secondary_head_node.display_name + " (B)" if cluster.secondary_head_node else "missing"]
            )]

            row += ["\n".join(
                [cluster.primary_head_node.id + " (A)" if cluster.primary_head_node else "missing"] +
                [cluster.secondary_head_node.id + " (B)" if cluster.secondary_head_node else "missing"]
            )]

            row += [
                ClusterIPs(
                    primary_ip=cluster.primary_head_node_vnic.public_ip if cluster.primary_head_node_vnic else None,
                    secondary_ip=cluster.secondary_head_node_vnic.public_ip
                    if cluster.secondary_head_node_vnic else None,
                    shared_ip=ha_public_ip.ip_address if ha_public_ip else None,
                    primary_private_ip=cluster.primary_head_node_vnic.private_ip
                    if cluster.primary_head_node_vnic else None,
                    secondary_private_ip=cluster.secondary_head_node_vnic.private_ip
                    if cluster.secondary_head_node else None,
                    shared_private_ip=ha_private_ip.ip_address if ha_private_ip else None
                ),
            ]

            row += ["\n".join([cluster.primary_head_node.lifecycle_state if cluster.primary_head_node else "N/A"] +
                              [cluster.secondary_head_node.lifecycle_state if cluster.secondary_head_node else "N/A"])]
            row += ["\n".join([cluster.primary_head_node.shape if cluster.primary_head_node else "N/A"] +
                              [cluster.secondary_head_node.shape if cluster.secondary_head_node else "N/A"])]
            row += ["\n".join(["{:.0f}".format(cluster.primary_head_node.shape_config.ocpus)
                               if cluster.primary_head_node else "N/A"] +
                              ["{:.0f}".format(cluster.secondary_head_node.shape_config.ocpus)
                               if cluster.secondary_head_node else "N/A"])]
            row += [
                "\n".join(
                    ["{:.0f}".format(cluster.primary_head_node.shape_config.memory_in_gbs * 1024)
                     if cluster.primary_head_node else "N/A"]
                    + ["{:.0f}".format(cluster.secondary_head_node.shape_config.memory_in_gbs * 1024)
                       if cluster.secondary_head_node else "N/A"]
                )
            ]

        else:
            row += [cluster.primary_head_node.display_name if cluster.primary_head_node else "missing"]
            row += [cluster.primary_head_node.id if cluster.primary_head_node else "missing"]
            row += [ClusterIPs(primary_ip=cluster.primary_head_node_vnic.public_ip
                               if cluster.primary_head_node_vnic else None,
                               primary_private_ip=cluster.primary_head_node_vnic.private_ip
                               if cluster.primary_head_node_vnic else None)]
            row += [cluster.primary_head_node.lifecycle_state if cluster.primary_head_node else "N/A"]
            row += [cluster.primary_head_node.shape if cluster.primary_head_node else "N/A"]
            row += [int(cluster.primary_head_node.shape_config.ocpus) if cluster.primary_head_node else "N/A"]
            row += [int(cluster.primary_head_node.shape_config.memory_in_gbs * 1024)
                    if cluster.primary_head_node else "N/A"]

        #
        # Assumed the image name and created time do not change, because the image may be deleted due to limited quota,
        # thus unable to fetch the images's info.
        image_display_name = cluster.primary_head_node.freeform_tags.get(IMAGE_NAME_TAG) \
            if cluster.primary_head_node else "N/A"
        image_time_created = cluster.primary_head_node.freeform_tags.get(IMAGE_CREATED_TIME_TAG) \
            if cluster.primary_head_node else "N/A"

        row += [image_display_name]
        row += [image_time_created]

        return row
