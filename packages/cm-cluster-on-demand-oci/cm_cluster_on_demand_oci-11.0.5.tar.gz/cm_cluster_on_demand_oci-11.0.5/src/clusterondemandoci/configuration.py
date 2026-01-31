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

import clusterondemand.configuration
from clusterondemandconfig import ConfigLoadError, ConfigNamespace, may_not_equal_none
from clusterondemandconfig.configuration.configuration_view import ConfigurationView
from clusterondemandconfig.parameter import Parameter

ocicredentials_ns = ConfigNamespace("oci.credentials", help_section="OCI credentials")
# FIXME These parameters are just guesses based on the AWS code plus the
# FIXME the OCI docs. This may well need to get tweaked.
# FIXME Required params: https://docs.oracle.com/en-us/iaas/Content/API/Concepts/sdkconfig.htm
ocicredentials_ns.add_parameter(
    "oci_user",
    help="User OCID",
    help_varname="USER_OCID",
    env="OCI_USER",
    validation=may_not_equal_none
)
ocicredentials_ns.add_parameter(
    "oci_fingerprint",
    help="OCI Public Key Fingerprint",
    help_varname="FINGERPRINT",
    env="OCI_FINGERPRINT",
    validation=may_not_equal_none
)
# These next two are mutually exclusive.
ocicredentials_ns.add_parameter(
    "oci_key_file",
    help="OCI Key File",
    help_varname="PATH_TO_KEY_FILE",
    env="OCI_KEY_FILE",
    validation=lambda p, c: need_oci_key_content_or_file(p, c),
)
# We need to support passing the key content via an env var for convenience in CI.
ocicredentials_ns.add_parameter(
    "oci_key_content",
    help="OCI Secret Key",
    help_varname="KEY_CONTENTS",
    env="OCI_KEY_CONTENT",
    secret=True,
    validation=lambda p, c: need_oci_key_content_or_file(p, c),
    advanced=True,
)
#
# XXX There are security concerns with this.
ocicredentials_ns.add_parameter(
    "oci_pass_phrase",
    # default=None,
    help="OCI Secret Key Passphrase",
    help_varname="PASS_PHRASE",
    env="OCI_PASS_PHRASE",
    secret=True,
    # validation=may_not_equal_none
)
ocicredentials_ns.add_parameter(
    "oci_tenancy",
    help="Tenancy OCID",
    env="OCI_TENANCY",
    validation=may_not_equal_none
)
ocicredentials_ns.add_parameter(
    "oci_region",
    default="us-sanjose-1",
    help="Name of the OCI region to use for the operation.",
    env="OCI_REGION",
    validation=may_not_equal_none
)

ociclustercommon_ns = ConfigNamespace("oci.cluster.common")

ociclustercommon_ns.add_parameter(
    "oci_compartment_id",
    advanced=True,
    default=None,
    help="OCID of the compartment to be used as default for all resources.",
    validation=may_not_equal_none,
    #
    # XXX This may be better validation long-term, but '=none' is better than nothing for now
)
ociclustercommon_ns.add_parameter(
    "compute_compartment_id",
    advanced=True,
    default=None,
    help="OCID of the compartment to be used for compute resources.",
)
ociclustercommon_ns.add_parameter(
    "networking_compartment_id",
    advanced=True,
    default=None,
    help="OCID of the compartment to be used for network resources.",
)

ocicommon_ns = ConfigNamespace("oci.common")
ocicommon_ns.import_namespace(clusterondemand.configuration.common_ns)
ocicommon_ns.remove_imported_parameter("version")
ocicommon_ns.import_namespace(ocicredentials_ns)


def need_oci_key_content_or_file(_: Parameter, configuration: ConfigurationView) -> None:
    if not configuration["oci_key_content"] and not configuration["oci_key_file"]:
        raise ConfigLoadError(
            "Either 'oci_key_file' or 'oci_key_content' must be set")
    # Should we also enforce that only one of the parameters is set?
