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
from functools import lru_cache
from typing import NewType, Union

import oci.core
import oci.pagination
from oci.core.models import (
    AddNetworkSecurityGroupSecurityRulesDetails,
    AddSecurityRuleDetails,
    CreateInternetGatewayDetails,
    CreateNatGatewayDetails,
    CreateNetworkSecurityGroupDetails,
    CreatePublicIpDetails,
    CreateRouteTableDetails,
    CreateSubnetDetails,
    CreateVcnDetails,
    GetPublicIpByPrivateIpIdDetails,
    InternetGateway,
    NatGateway,
    NetworkSecurityGroup,
    PrivateIp,
    PublicIp,
    RouteRule,
    RouteTable,
    SecurityList,
    Subnet,
    UpdateSecurityListDetails,
    Vcn,
    Vnic
)

from clusterondemandoci.client_base import OCIClientBase

OCIBaseType = dict[str, Union[str, list, dict]]
OCIVirtualNetwork = NewType("OCIVirtualNetwork", OCIBaseType)

log = logging.getLogger("cluster-on-demand")


class OCIClientVCN(OCIClientBase):
    def __init__(self, config: dict, **kwargs: str):
        super().__init__(config, **kwargs)

        vcn_client = oci.core.VirtualNetworkClient(config, **self._kwargs)
        self._vcn = vcn_client
        self._vcncomposite = oci.core.VirtualNetworkClientCompositeOperations(vcn_client)

    def create_public_ip(self, create_public_ip_details: CreatePublicIpDetails) -> PublicIp:
        shared_public_ip = self._vcncomposite.create_public_ip_and_wait_for_state(
            create_public_ip_details,
            wait_for_states=[PublicIp.LIFECYCLE_STATE_AVAILABLE, PublicIp.LIFECYCLE_STATE_ASSIGNED],
        ).data
        return shared_public_ip

    def delete_public_ip(self, public_ip_id: str) -> None:
        self._vcncomposite.delete_public_ip_and_wait_for_state(
            public_ip_id=public_ip_id,
            wait_for_states=[PublicIp.LIFECYCLE_STATE_TERMINATED],
        )

    @lru_cache
    def list_public_ips(self, compartment_id: str, scope: str, lifetime: str) -> list[PrivateIp]:
        response = oci.pagination.list_call_get_all_results(
            self._vcn.list_public_ips,
            compartment_id=compartment_id,
            scope=scope,
            lifetime=lifetime,
        )
        return response.data

    def list_private_ips(self, vnic_id: str) -> list[PrivateIp]:
        response = self._vcn.list_private_ips(vnic_id=vnic_id)
        return response.data

    def get_public_ip_by_private_ip_id(self, private_ip_id: str) -> PublicIp:
        private_ip_details = GetPublicIpByPrivateIpIdDetails(private_ip_id=private_ip_id)
        response = self._vcn.get_public_ip_by_private_ip_id(private_ip_details)
        return response.data

    def get_vcn(self, vcn_id: str) -> Vcn:
        response = self._vcn.get_vcn(vcn_id)
        return response.data

    def get_subnet(self, subnet_id: str) -> Subnet:
        response = self._vcn.get_subnet(subnet_id)
        return response.data

    def get_vnic(self, vnic_id: str) -> Vnic:
        """
        Gets VNIC from API

        :param vnic_id:
            id of the VNIC

        :return: A :class:`~oci.core.models.Vnic` object
        """
        response = self._vcn.get_vnic(vnic_id)
        return response.data

    def get_nsgs_in_vcn(self, vcn_id: str, compartment_id: str) -> list[NetworkSecurityGroup]:
        return self._vcn.list_network_security_groups(
            compartment_id=compartment_id,
            vcn_id=vcn_id,
        ).data

    def get_security_list(self, security_list_id: str) -> SecurityList:
        return self._vcn.get_security_list(security_list_id=security_list_id).data

    def update_security_list(self, security_list_id: str,
                             update_security_list_details: UpdateSecurityListDetails) -> SecurityList:
        return self._vcn.update_security_list(security_list_id, update_security_list_details).data

    def create_vcn(self, vcn_details: CreateVcnDetails) -> Vcn:
        """
        Creates a new VCN using CreateVcnDetails model

        :param vcn_details: instance of CreateVcnDetails
        :return: the newly created VCN
        """

        response = self._vcncomposite.create_vcn_and_wait_for_state(
            vcn_details,
            wait_for_states=[Vcn.LIFECYCLE_STATE_AVAILABLE])

        return response.data

    def list_vcns(self, compartment_id: str, **kwargs: str) -> list[oci.core.models.Vcn]:
        response = oci.pagination.list_call_get_all_results(
            self._vcn.list_vcns,
            compartment_id,
            **kwargs,
        )
        return response.data

    def create_subnet(self, subnet_details: CreateSubnetDetails) -> Subnet:
        """
        Creates subnet using CreateSubnetDetails model

        :param subnet_details: instance of CreateSubnetDetails
        :return: the newly created Subnet
        """
        response = self._vcncomposite.create_subnet_and_wait_for_state(
            subnet_details,
            wait_for_states=[Subnet.LIFECYCLE_STATE_AVAILABLE])

        return response.data

    def create_internet_gateway(self, igw_details: CreateInternetGatewayDetails) -> InternetGateway:
        """

        :param igw_details:
        :return:
        """

        response = self._vcncomposite.create_internet_gateway_and_wait_for_state(
            igw_details,
            wait_for_states=[InternetGateway.LIFECYCLE_STATE_AVAILABLE])

        return response.data

    def create_nat_gateway(self, ngw_details: CreateNatGatewayDetails) -> NatGateway:
        response = self._vcncomposite.create_nat_gateway_and_wait_for_state(
            ngw_details,
            wait_for_states=[NatGateway.LIFECYCLE_STATE_AVAILABLE])

        return response.data

    def create_route_table(self, route_table_details: CreateRouteTableDetails) -> RouteTable:
        response = self._vcncomposite.create_route_table_and_wait_for_state(
            route_table_details,
            wait_for_states=[RouteTable.LIFECYCLE_STATE_AVAILABLE])

        return response.data

    def add_route_table_rule(self, route_table_id: str, route_rule: RouteRule) -> RouteTable:
        """
        Adds route rule to existing route table

        :param route_table_id:
        :param route_rule:
        :return:
        """
        response = self._vcn.get_route_table(route_table_id)
        route_rules = response.data.route_rules
        route_rules.append(route_rule)
        update_route_table_details = oci.core.models.UpdateRouteTableDetails(route_rules=route_rules)

        response = self._vcncomposite.update_route_table_and_wait_for_state(
            route_table_id,
            update_route_table_details,
            wait_for_states=[RouteTable.LIFECYCLE_STATE_AVAILABLE]
        )

        return response.data

    def create_security_group(
        self,
        head_nsg_details: CreateNetworkSecurityGroupDetails,
        head_rules_details: AddNetworkSecurityGroupSecurityRulesDetails,
    ) -> list[oci.core.models.NetworkSecurityGroup]:
        """
        Creates head and worker node security groups and allows for node -> head traffic

        :param head_nsg_details:
        :param head_rules_details:
        :return:
        """

        node_nsg_details = CreateNetworkSecurityGroupDetails(
            display_name=head_nsg_details.display_name.replace("-headnode", "-node"),
            compartment_id=head_nsg_details.compartment_id,
            vcn_id=head_nsg_details.vcn_id,
            freeform_tags=head_nsg_details.freeform_tags,
        )

        head_nsg = self._vcn.create_network_security_group(head_nsg_details).data
        node_nsg = self._vcn.create_network_security_group(node_nsg_details).data

        # Allow node to head access
        head_rules_details.security_rules.append(
            AddSecurityRuleDetails(
                direction=AddSecurityRuleDetails.DIRECTION_INGRESS,
                is_stateless=False,
                protocol="all",
                source=node_nsg.id,
                source_type=oci.core.models.AddSecurityRuleDetails.SOURCE_TYPE_NETWORK_SECURITY_GROUP
            )
        )

        self._vcn.add_network_security_group_security_rules(head_nsg.id, head_rules_details)

        # Allow incoming traffic from head node and other nodes.
        self._vcn.add_network_security_group_security_rules(
            node_nsg.id,
            oci.core.models.AddNetworkSecurityGroupSecurityRulesDetails(
                security_rules=[
                    AddSecurityRuleDetails(
                        direction=AddSecurityRuleDetails.DIRECTION_INGRESS,
                        is_stateless=False,
                        protocol="all",
                        source=node_nsg.id,
                        source_type=oci.core.models.AddSecurityRuleDetails.SOURCE_TYPE_NETWORK_SECURITY_GROUP
                    ),
                    AddSecurityRuleDetails(
                        direction=AddSecurityRuleDetails.DIRECTION_INGRESS,
                        is_stateless=False,
                        protocol="all",
                        source=head_nsg.id,
                        source_type=oci.core.models.AddSecurityRuleDetails.SOURCE_TYPE_NETWORK_SECURITY_GROUP
                    ),
                ]
            ),
        )

        return [head_nsg, node_nsg]

    def delete_all_route_table_rules(self, route_table_id: str) -> RouteTable:
        update_route_table_details = oci.core.models.UpdateRouteTableDetails(route_rules=[])

        response = self._vcncomposite.update_route_table_and_wait_for_state(
            route_table_id,
            update_route_table_details,
            wait_for_states=[RouteTable.LIFECYCLE_STATE_AVAILABLE]
        )

        log.debug("Deleted all rules from route table: %s", route_table_id)

        return response.data

    # Delete operations
    def delete_subnet(self, subnet_id: str) -> None:
        """
        Deletes a subnet

        :param subnet:
            An subnet element as returned from a Structured Query
        :return:
        """

        #
        # XXX This has failed at least once due to a possible race condition with instance deletion.
        #
        # {
        #   'target_service': 'virtual_network',
        #   'status': 409,
        #   'code': 'Conflict',
        #   'opc-request-id': '<REDACTED>',
        #   'message': 'The Subnet <REDACTED_OCID> references the VNIC <REDACTED_VNIC>...',
        #   ...
        # }
        #
        # The retry strategy is an effort to compensate for this.
        self._vcncomposite.delete_subnet_and_wait_for_state(
            subnet_id,
            wait_for_states=[Subnet.LIFECYCLE_STATE_TERMINATED],
            operation_kwargs={
                'retry_strategy': self._get_retry_strategy(service_error_retry_config={429: [], 404: [], 409: []}),
            }
        )

        log.debug("Deleted subnet: %s", subnet_id)

    def delete_internet_gateway(self, internet_gateway_id: str) -> None:
        """
        Deletes a internet gateway (IGW)

        :param subnet:
            An internet gateway element as returned from a Structured Query
        :return:
        """
        self._vcncomposite.delete_internet_gateway_and_wait_for_state(
            internet_gateway_id,
            wait_for_states=[InternetGateway.LIFECYCLE_STATE_TERMINATED]
        )

        log.debug("Deleted internet gateway: %s", internet_gateway_id)

    def delete_nat_gateway(self, nat_gateway_id: str) -> None:
        self._vcncomposite.delete_nat_gateway_and_wait_for_state(
            nat_gateway_id,
            wait_for_states=[NatGateway.LIFECYCLE_STATE_TERMINATED]
        )

        log.debug("Deleted NAT gateway: %s", nat_gateway_id)

    def delete_route_table(self, route_table_id: str) -> None:
        """
        Deletes a route table

        :param route_table:
            A route table element as returned from a Structured Query
        :return:
        """
        self._vcncomposite.delete_route_table_and_wait_for_state(
            route_table_id,
            wait_for_states=[RouteTable.LIFECYCLE_STATE_TERMINATED]
        )

        log.debug("Deleted route table: %s", route_table_id)

    def delete_nsg(self, nsg_id: str) -> None:
        self._vcncomposite.delete_network_security_group_and_wait_for_state(
            nsg_id,
            wait_for_states=[NetworkSecurityGroup.LIFECYCLE_STATE_TERMINATED]
        )
        log.debug("Deleted NSG: %s", nsg_id)

    def delete_vcn(self, vcn_id: str) -> None:
        self._vcncomposite.delete_vcn_and_wait_for_state(
            vcn_id,
            wait_for_states=[Vcn.LIFECYCLE_STATE_TERMINATED]
        )
        log.debug("Deleted VCN: %s", vcn_id)
