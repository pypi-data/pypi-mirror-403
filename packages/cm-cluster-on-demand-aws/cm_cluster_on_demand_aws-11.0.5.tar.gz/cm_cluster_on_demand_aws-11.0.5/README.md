With Cluster on Demand for AWS you can spin up a cluster running NVIDIA Base
Command Manager inside of AWS.

# Installation

```
pip install cm-cluster-on-demand-aws
```

# Usage

To get started, execute the following command:

```
cm-cod-aws --help
```

Example, To start a NVIDIA Base Command Manager Cluster with 5 nodes and 1 headnode in AWS:

```
cm-cod-aws cluster create --on-error 'cleanup' --aws-region 'us-east-1' --wlm 'slurm' --nodes '5' --aws-access-key-id '...' --aws-secret-key '...' --cluster-password '...'  --license-product-key '...' --name mycluster
```

Don't forget to fill in the '...' blanks, and change the other parameters to
the values that match your use-case and organization. All documentation for
setting up and running a NVIDIA Base Command Manager cluster using Cluster
On Demand on AWS can be found in the
[Cloudbursting Manual](https://docs.nvidia.com/base-command-manager/#product-manuals).
