With Cluster on Demand for OCI you can spin up a cluster running NVIDIA Base
Command Manager Cluster inside of OCI.

# Installation

```
pip install cm-cluster-on-demand-oci
```

# Usage

To get started, execute the following command:

```
cm-cod-oci --help
```

Example, To start a NVIDIA Base Command Manager Cluster with 5 nodes and
1 headnode in OCI:

```
cm-cod-oci cluster create --on-error 'cleanup' --oci-region 'eu-amsterdam-1' --wlm 'slurm' --nodes '5' --oci-tenancy '...' --oci-user '...' --oci-fingerprint '...' --oci-key-file '...' --cluster-password '...'  --license-product-key '...' --name mycluster
```

Don't forget to fill in the '...' blanks, and change the other parameters to
the values that match your use-case and organization. All documentation for
setting up and running a NVIDIA Base Command Manager cluster using Cluster
On Demand on OCI can be found in the
[Cloudbursting Manual](https://docs.nvidia.com/base-command-manager/#product-manuals).
