With Cluster on Demand for Azure you can spin up a cluster running NVIDIA Base
Command Manager inside of Azure.

# Installation

```
pip install cm-cluster-on-demand-azure
```

# Usage

To get started, execute the following command:

```
cm-cod-azure --help
```

Example, To start a NVIDIA Base Command Manager Cluster with 5 nodes and 1
headnode in Azure:

```
cm-cod-azure cluster create --on-error 'cleanup' $REGION$' --wlm 'slurm' --nodes '5' $AZURE CREDENTIALS$ --cluster-password '...'  --license-product-key '...' --name mycluster
```

Don't forget to fill in the '...' blanks, and change the other parameters to
the values that match your use-case and organization. All documentation for
setting up and running a NVIDIA Base Command Manager cluster using Cluster
On Demand on Azure can be found in the
[Cloudbursting Manual](https://docs.nvidia.com/base-command-manager/#product-manuals).
