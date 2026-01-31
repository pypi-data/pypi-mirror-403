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
from functools import cached_property, lru_cache

import oci.core
import oci.exceptions
import oci.pagination
#
# Explictly import these either because the names are very long or we're using class constants.
from oci.core.models import (
    Instance,
    InstanceConfigurationLaunchInstanceShapeConfigDetails,
    InstancePool,
    LaunchInstanceShapeConfigDetails
)
from oci.work_requests.models import WorkRequest

from clusterondemand.exceptions import CODException
from clusterondemandoci.client_base import OCIClientBase
from clusterondemandoci.oci_actions.workrequest import OCIClientWorkRequest

log = logging.getLogger("cluster-on-demand")


class OCIClientCompute(OCIClientBase):
    def __init__(self, config: dict, **kwargs):
        super().__init__(config, **kwargs)

        compute_client = oci.core.ComputeClient(config, **self._kwargs)
        compute_management_client = oci.core.ComputeManagementClient(config, **self._kwargs)

        self._compute = compute_client
        self._computemanagement = compute_management_client
        self._computecomposite = oci.core.ComputeClientCompositeOperations(compute_client)
        self._computemanagementcomposite = oci.core.ComputeManagementClientCompositeOperations(
            compute_management_client,
        )

    @cached_property
    def compute_client(self):
        return self._compute

    def get_instance(self, instance_ocid: str) -> oci.core.models.Instance:
        """
        Gets a single OCI instance by OCID

        :param instance_ocid: OCID of the instance to fetch

        :return: A :class:`~oci.core.models.Instance` object for the requested instance.
        """
        return self._compute.get_instance(instance_ocid)

    def get_instance_by_name(
        self,
        instance_name: str,
        compartment_id: str,
        lifecycle_state: str = Instance.LIFECYCLE_STATE_RUNNING,
    ) -> oci.core.models.Instance:
        """
        Gets a single OCI instance by instance name

        :param instance_name: Name of instance to get
        :param compartment_id: OCID of compartment in which to search for the instance
        :param lifecycle_state: Valid instance lifecycle state; should be one of the LIFECYCLE_STATE_* class
            constats defined in :class:`oci.core.models.instance.Instance`
        :return: A :class:`~oci.core.models.Instance` object for the requested instance.

        :raises: :class:`~clusterondemand.exceptions.CODException` if no instance of the requested name is found
            in the requested ``compartment_id`` with the reqeuested ``lifecycle_state``
        """
        instances_list_response = self._compute.list_instances(
            compartment_id,
            display_name=instance_name,
            lifecycle_state=lifecycle_state,
        )

        instance_list = instances_list_response.data

        if not instance_list:
            raise CODException(f"No instance named '{instance_name}' found")

        return instance_list[0]

    def list_instances(self, compartment_id: str, **kwargs: str) -> list[oci.core.models.Instance]:
        list_instances_response = oci.pagination.list_call_get_all_results(
            self._compute.list_instances,
            compartment_id,
            **kwargs,
        )

        return list_instances_response.data

    # TODO: Test this
    def launch_instance(
        self,
        instance_details: oci.core.models.LaunchInstanceDetails
    ) -> oci.core.models.Instance:

        wait_for_states = [Instance.LIFECYCLE_STATE_RUNNING]

        launch_instance_response = self._computecomposite.launch_instance_and_wait_for_state(
            instance_details,
            wait_for_states=wait_for_states,
        )

        instance = launch_instance_response.data

        return instance

    # TODO: Test this
    def terminate_instance(
        self,
        instance_id: str,
    ) -> oci.core.models.Instance:
        """
        Terminate an OCI instance

        :param instance_id: OCID of instance to terminate
        """

        terminate_instance_response = self._computecomposite.terminate_instance_and_wait_for_state(
            instance_id,
            wait_for_states=[Instance.LIFECYCLE_STATE_TERMINATED]
        )

        terminated_instance = terminate_instance_response.data

        return terminated_instance

    def instance_action(
            self,
            instance_id: str,
            action: str,
            wait_for_states: list[str] | None = None
    ) -> oci.core.models.Instance:
        """
        Call an instance action on an OCI instance

        :param instance_id: OCID of the instance to perform the action on
        :param action: The action to perform on the instance
        :param wait_for_states: An array of states to wait on
        """
        modified_instance = self._computecomposite.instance_action_and_wait_for_state(
            instance_id,
            action,
            wait_for_states=wait_for_states,
        )

        return modified_instance

    def start_instance(
            self,
            instance_id: str,
            wait_for_states: list[str] | None = None
    ) -> oci.core.models.Instance:
        """
        Start an OCI instance

        :param instance_id: OCID of the instance to start
        :param wait_for_states: An array of states to wait on; defaults to `RUNNING`; `[]` to don't wait for any state
        """
        if wait_for_states is None:
            wait_for_states = [Instance.LIFECYCLE_STATE_RUNNING]

        return self.instance_action(
            instance_id,
            "START",
            wait_for_states=wait_for_states,
        )

    def stop_instance(
            self,
            instance_id: str,
            wait_for_states: list[str] | None = None,
            force: bool = False,
    ) -> oci.core.models.Instance:
        """
        Stop an OCI instance.

        :param instance_id: OCID of the instance to stop
        :param wait_for_states: An array of states to wait on; defaults to `STOPPED`; `[]` to not wait for any state
        :param force: Whether to do a graceful or forceful stop; defaults to graceful
        """
        if wait_for_states is None:
            wait_for_states = [Instance.LIFECYCLE_STATE_STOPPED]

        return self.instance_action(
            instance_id,
            "STOP" if force else "SOFTSTOP",
            wait_for_states=wait_for_states,
        )

    def get_image(self, image_id: str) -> oci.core.models.Image:
        return self._compute.get_image(image_id).data

    def get_image_by_name(self, image_name: str, compartment_id: str) -> oci.core.models.Image:
        """
        Searches for image that matches image_name in the provided compartment_id
        """
        image_list = oci.pagination.list_call_get_all_results(
            self._compute.list_images,
            compartment_id=compartment_id
        ).data
        if not image_list:
            raise CODException(f"No images named {image_name} were found in this compartment")

        image = None
        for img in image_list:
            if img.display_name == image_name:
                image = img
                break

        return image

    def list_images(self, compartment_id: str, **kwargs: str) -> list[oci.core.models.Image]:
        list_images_response = oci.pagination.list_call_get_all_results(
            self._compute.list_images,
            compartment_id,
            **kwargs,
        )

        return list_images_response.data

    @lru_cache
    def get_shapes(
        self,
        availability_domain_name: str,
        compartment_id: str
    ) -> [oci.core.models.Shape]:
        """
        Get all shapes from OCI

        :param availability_domain_name: Name of the availability domain in which to
            search for the shape
        :param compartment_id: OCID of the compartment in which to search for the shape
        """
        try:
            list_shapes_response = oci.pagination.list_call_get_all_results(
                self._compute.list_shapes,
                compartment_id,
                availability_domain=availability_domain_name
            )
        except oci.exceptions.ServiceError as exc:
            raise CODException(exc.message) from exc

        shape_list = list_shapes_response.data

        if not shape_list:
            raise CODException("No shapes were found in this compartment+availability domain")

        return shape_list

    def get_shape(
        self,
        shape_name: str,
        availability_domain_name: str,
        compartment_id: str
    ) -> oci.core.models.Shape:
        """
        Get a shape object from OCI

        :param shape_name: Name of shape to get
        :param availability_domain_name: Name of the availability domain in which to
            search for the shape
        :param compartment_id: OCID of the compartment in which to search for the shape
        """
        shape_list = self.get_shapes(availability_domain_name, compartment_id)

        #
        # XXX Possibly overly naive; in theory we can only have one shape
        # XXX named 'foo' in a compartment but this has not been tested.
        shape = next((x for x in shape_list if x.shape == shape_name), None)

        if shape is None:
            raise CODException(f"No shape '{shape_name}' exists in this compartment+availability domain")

        return shape

    def get_shape_config(
        self,
        shape_memory_size_gb: int,
        shape_number_cpus: int,
        object_type: str = 'instance',
    ) -> LaunchInstanceShapeConfigDetails | InstanceConfigurationLaunchInstanceShapeConfigDetails:
        """
        Returns a shape config details object suitable to being passed to an instance launch.

        :param shape_memory_size_gb: Memory of instance, in GB
        :param shape_number_cpus: Number of CPUs for instance
        :param object_type: The type of object for which the shape config is being generated; valid values are
            the dictionary keys used in ``shape_class_by_type``

        :return: An instance of a shape config details object suitable for use with the
            requested ``object_type``. The class of the object is determined by looking up ``object_type`` in
            the ``shape_class_by_type`` dictionary.
        """
        shape_class_by_type = {
            'instance': oci.core.models.LaunchInstanceShapeConfigDetails,
            'instanceconfiguration': oci.core.models.InstanceConfigurationLaunchInstanceShapeConfigDetails,
        }
        shape_class = shape_class_by_type.get(object_type)
        if shape_class is None:
            raise CODException(
                "Invalid object type for instance_configuration_options; got '{object_type}', "
                "expected one of '{list(shape_class_by_type.keys())}'"
            )

        return shape_class(
            memory_in_gbs=float(shape_memory_size_gb),
            ocpus=shape_number_cpus,
        )

    def get_vnic_attachments(self, instance: oci.core.models.Instance) -> list[oci.core.models.VnicAttachment]:
        """
        Return all instance VNIC attachments

        :param instance:
            instance object from which attachments are to be extracted

        :return: A list of :class:`~oci.core.models.VnicAttachment`
        """
        if instance is None:
            return []

        try:
            return oci.pagination.list_call_get_all_results(
                self._compute.list_vnic_attachments,
                compartment_id=instance.compartment_id,
                instance_id=instance.id
            ).data

        except oci.exceptions.ServiceError as error:
            raise CODException(error.message) from error

    def delete_cluster_network(self, cluster_network_id: str) -> None:
        """
        Delete a cluster network

        :param cluster_network_id:
            OCID of cluster network to delete
        """

        work_request = self._computemanagementcomposite.terminate_cluster_network_and_wait_for_work_request(
            cluster_network_id,
        ).data

        if work_request.status != WorkRequest.STATUS_SUCCEEDED:
            work_client = OCIClientWorkRequest(self._config)
            work_client.log_all_work_request_logs(work_request.id)
            raise CODException(
                f"Failed to delete cluster network '{cluster_network_id}' (work request id: {work_request.id})"
            )

    def delete_instance_pool(self, instance_pool_id: str) -> None:
        """
        Delete an instance pool from the cluster

        :param instance_pool_id::
            OCID of instance pool to delete
        """

        return self._computemanagementcomposite.terminate_instance_pool_and_wait_for_state(
            instance_pool_id,
            wait_for_states=[InstancePool.LIFECYCLE_STATE_TERMINATED],
        )

    def stop_instance_pool(self, instance_pool_id: str, wait_for_states: list[str] | None = None) -> None:
        """
        Stops all instances in an instance pool from the cluster

        :param instance_pool_id: OCID of instance pool to stop
        :param wait_for_states: An array of states to wait on; defaults to `STOPPED`; `[]` to don't wait for any state
        """
        if wait_for_states is None:
            wait_for_states = [InstancePool.LIFECYCLE_STATE_STOPPED]
        return self._computemanagementcomposite.stop_instance_pool_and_wait_for_state(
            instance_pool_id,
            wait_for_states=wait_for_states,
        )

    def delete_instance_configuration(self, instance_configuration_id: str) -> None:
        """
        Deletes an instance configuration

        :param instance_configuration:
        """

        return self._computemanagement.delete_instance_configuration(instance_configuration_id)
