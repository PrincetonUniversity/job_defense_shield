# Multinode CPU Fragmentation

This alert identifies CPU jobs that are using too many nodes or too few CPU-cores per node.

Consider a cluster with 64 CPU-cores per node. A user can run a job
that requires 128 CPU-cores by (1) allocating 64 CPU-cores on 2 nodes
or (2) allocating 4 CPU-cores on 32 nodes. The former is in general
strongly preferred. This alert catches jobs doing the latter,
i.e., multinode jobs that allocate less than the
number of available CPU-cores per node (e.g., 4 CPU-cores on 32 nodes).
The memory usage of each job is taken into account when looking
for fragmentation.

Jobs with 0% CPU utilization on a node are ignored since those are captured
by a [another alert](zero_cpu_util.md).

## Configuration File

Below is an example alert entry for `config.yaml`:

```yaml
multinode-cpu-fragmentation-1:
  cluster: della
  partitions:
    - cpu
  min_run_time:     61  # minutes
  cores_per_node:   32  # count
  cores_fraction:  0.8  # [0.0, 1.0]
  mem_per_node:    190  # GB
  safety_fraction: 0.2  # [0.0, 1.0]
  email_file: "multinode_cpu_fragmentation.txt"
  admin_emails:
    - admin@institution.edu
```

The parameters are explained below:

- `cluster`: Specify the cluster name as it appears in the Slurm database.

- `partitions`: Specify one or more Slurm partitions.

- `cores_per_node`: CPU-cores per node.

- `cores_fraction`: The ratio of allocated CPU-cores to the product of the number of nodes and CPU-cores per node. Jobs that use greater than the value of `cores_fraction` will be ignored. This quantity varies between 0 and 1.

- `mem_per_node`: CPU memory per node in units of GB.

- `safety_frac`: The memory used by the job is multiplied by 1 + `safety_frac` and this number is compared against the product of the number of nodes and the memory per node in deciding whether or not sufficent memory was used to ignore the job independent of the number of allocated CPU-cores. The idea is to ignore jobs that are almost using all of the allocated CPU memory.

- `email_file`: The text file to be used for the email message to users.

- `min_nodes_thres`: (Optional) Minimum number of allocated nodes for a job to be considered. For instance, if `min_nodes_thres: 4` then jobs that ran on 3 nodes or less will be ignored. Default: 2

- `cores_per_node_thres`: (Optional) Only consider jobs with less than this number of cores per node. If this setting is used then the following settings will be ignored: `cores_per_node`, `mem_per_node`, and `safety_frac`. Additionally, the only placeholders that will be available are `<GREETING>`, `<DAYS>`, `<CLUSTER>`, `<PARTITIONS>`, `<TABLE>`, and `<JOBSTATS>`. The `<TABLE>` placeholder will not contain `Min-Nodes`. The `cores_per_node_thres` setting provides a simple way to address multinode CPU fragmentation on a cluster composed of hetergeneous nodes.

- `min_run_time`: (Optional) Minimum run time of a job in units of minutes. If `min_run_time: 61` then jobs that ran for an hour or less are ignored. Default: 0

- `excluded_users`: (Optional) List of usernames to exclude from the alert.

- `admin_emails`: (Optional) List of administrator email addresses that should receive copies of the emails that are sent to users.

- `email_subject`: (Optional) Subject of the email message to users.

- `report_title`: (Optional) Title of the report to system administrators.

Below is an entry appropriate for a heterogeneous cluster:

```yaml
multinode-cpu-fragmentation-1:
  cluster: della
  partitions:
    - cpu
  min_run_time:         61  # minutes
  cores_per_node_thres: 16  # count
  email_file: "multinode_cpu_fragmentation.txt"
  admin_emails:
    - admin@institution.edu
```

When `cores_per_node_thres` is used, other settings are ignored and a limited number of placeholders are available for creating the email message.

## Report for System Administrators

Below is an example report:

```
$ job_defense_shield --multinode-cpu-fragmentation

                     Multinode CPU Jobs with Fragmentation                         
-------------------------------------------------------------------------------
 JobID    User   Nodes  Cores Mem-per-Node-Used Cores-per-Node Min-Nodes Emails
-------------------------------------------------------------------------------
6286517  u45923   20     20          1 GB             1            1        0   
6286840  u45923   10     10          1 GB             1            1        0   
6287417  u45923   10     10          3 GB             1            1        0   
6288471  u45923   10     10          4 GB             1            1        0   
6289852  u45923    5     10         12 GB             2            1        0   
-------------------------------------------------------------------------------
   Cluster: della
Partitions: cpu
     Start: Wed Mar 12, 2025 at 11:44 AM
       End: Wed Mar 19, 2025 at 11:44 AM
```

The `Min-Nodes` field is calculated based on the hardware specifications and the number of CPU-cores allocated by the user. All of the jobs in the table above could have ran on one node.

## Email Message to Users

Below is an example message (see `email/multinode_cpu_fragmentation.txt`):

```
Hello Alan (u45923),

Below are your jobs over the past 7 days on Della which appear to be using
more nodes than necessary:

     JobID   Nodes  Mem-per-Node  Cores-per-Node  Hours  Nodes-Needed
    62862517   20        1 GB            1         2.2        1      
    62869840   10        1 GB            1         2.9        1      
    62874417   10        3 GB            1          12        1      
    62886471   10        4 GB            1          12        1      
    62892852    5       12 GB            2          22        1      

The "Nodes" column shows the number of nodes used to run the job. The
"Nodes-Needed" column shows the minimum number of nodes needed to run the
job (these values are calculated based on the number of requested CPU-cores
while taking into account the CPU memory usage of the job). "Mem-per-Node"
is the mean CPU memory used per node.

Replying to this automated email will open a support ticket with Research
Computing.
```

### Placeholders

The following placeholders can be used in the email file:

- `<GREETING>`: Greeting generated by `greeting_method`.
- `<CLUSTER>`: The name of the cluster.
- `<PARTITIONS>`: A comma-separated list of partitions used by the user.
- `<DAYS>`: Number of days in the time window (default is 7).
- `<CPN>`: Number of CPU-cores per node (i.e., `cores_per_node`).
- `<MPN>`: CPU memory per node (i.e., `mem_per_node`).
- `<TABLE>`: A table of jobs of the user.
- `<NUM-CORES>`: Product of minimum number of nodes needed and the number CPU-cores per node.

Note that if `cores_per_node_thres` is defined then only a limited number of placeholders are available.

## Usage

Generate a report for system administrators:

```
$ job_defense_shield --multinode-cpu-fragmentation --email
```

Send emails to the offending users:

```
$ job_defense_shield --multinode-cpu-fragmentation --email
```

See which users have received emails and when:

```
$ job_defense_shield --multinode-cpu-fragmentation --check
```

## cron

```
0 9 * * 1-5 /path/to/job_defense_shield --multinode-cpu-fragmentation --email -M della -r cpu > /path/to/log/cpu_fragmentation.log 2>&1
```
