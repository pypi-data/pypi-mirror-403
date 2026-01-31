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

from prettytable import PrettyTable

from clusterondemand.summary import SummaryGenerator, SummaryType


class OCISummaryGenerator(SummaryGenerator):
    """Generate the summary for creation of OCI clusters and nodes."""

    def __init__(self,
                 config,
                 summary_type,
                 region=None,
                 head_node_definition=None,
                 node_definition=None,
                 head_image=None,
                 node_image=None,
                 head_image_id=None,
                 node_image_id=None,
                 public_ip=None,
                 instance_id=None,
                 compartment_name=None,
                 availability_domain_name=None,
                 number_of_availability_domains_in_region=None):

        super().__init__(config["name"], region=region, config=config, summary_type=summary_type,
                         primary_head_node_definition=head_node_definition, head_image=head_image,
                         node_definitions=[node_definition], node_image=node_image)
        self._node_image = node_image
        self._head_image = head_image
        self._node_image_id = node_image_id
        self._head_image_id = head_image_id
        self._instance_id = instance_id
        self._public_ip = public_ip
        self._compartment_name = compartment_name
        self.config = config
        self._availability_domain_name = availability_domain_name
        self._number_of_availablity_domains_in_region = number_of_availability_domains_in_region
        self._use_instance_profile = config["use_principal_authentication"]

    def _add_rows(self, table: PrettyTable):
        if self._type == SummaryType.Proposal:
            # self._add_resource_group(table)
            self._add_region(table)
            self._add_availability_domain(table)
            self._add_number_of_availability_domains_in_region(table)
            self._add_compartment(table)
            self._add_access_info(table)
            self._add_credentials_message(table)
            self._add_custom_image(table)

        if self._type == SummaryType.Overview:
            self._add_deployment_details(table)

    def _add_header(self, table):
        self._add_separator(table)
        self._add_cluster_names(table)
        self._add_separator(table)

    def _add_cluster_names(self, table):
        table.add_row(["Cluster:", self.config["name"]])

    def _add_availability_domain(self, table):
        table.add_row(["Availability domain (AD):", self._availability_domain_name])

    def _add_number_of_availability_domains_in_region(self, table):
        table.add_row(["Nr. of ADs in region:", self._number_of_availablity_domains_in_region])

    def _add_deployment_details(self, table: PrettyTable):
        table.add_row(["Head node ID:", self._instance_id])
        table.add_row(["Public IP:", self._public_ip])

    def _add_credentials_message(self, table):
        if self._use_instance_profile:
            table.add_row(
                [
                    "Cloud authentication:",
                    "Head node will use instance principal authentication for cloud authentication",
                ]
            )
        else:
            table.add_row(["Cloud authentication:", "Head node will inherit COD credentials for cloud authentication"])

    def _add_custom_image(self, table):
        if not self._head_image:
            table.add_row(["Custom Head Image:", self._head_image_id])
        if not self._node_image and self._node_image_id:
            table.add_row(["Custom Node Image:", self._node_image_id])

    def _add_compartment(self, table):
        if self._compartment_name:
            table.add_row(["Compartment:", self._compartment_name])

    # def _add_resource_group(self, table):
    #     table.add_row(["Resource Group:", self._config["resource_group"]])
