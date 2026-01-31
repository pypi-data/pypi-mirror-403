With Cluster on Demand for GCP you can spin up a cluster running NVIDIA Base
Command Manager Cluster inside of GCP.

# Installation

```
pip install cm-cluster-on-demand-gcp
```

# Usage

To get started, execute the following command:

```
cm-cod-gcp --help
```

Example, To start a NVIDIA Base Command Manager Cluster with 5 nodes and
1 headnode in GCP:

```
cm-cod-gcp cluster create --on-error 'cleanup' --head-node-zone 'europe-west4-c' --wlm 'slurm' --nodes '5' --project-id '...' --cluster-password '...'  --license-product-key '...' --name mycluster
```

Don't forget to fill in the '...' blanks, and change the other parameters to
the values that match your use-case and organization. All documentation for
setting up and running a NVIDIA Base Command Manager cluster using Cluster
On Demand on GCP can be found in the
[Cloudbursting Manual](https://docs.nvidia.com/base-command-manager/#product-manuals).
