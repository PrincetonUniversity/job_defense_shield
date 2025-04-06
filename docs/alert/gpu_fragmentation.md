# Multinode GPU Fragmentation

This alert identifies GPU jobs that are using too many nodes or too few GPUs per node.

Consider a cluster with 4 GPUs per node. A user can run a job
with 8 GPUs by either (1) allocating 4 GPUs on 2 nodes
or (2) allocating 1 GPU on 8 nodes. The former is in general
strongly preferred. This alert catches jobs doing the latter,
i.e., multinode jobs that allocate less than the
number of available GPUs per node (e.g., 1 GPU on 8 nodes).

Jobs with a GPU at 0% utilization are ignored since they will
be captured by the `--zero-gpu-utilization` alert.

## Configuration File

Below is an example entry for `config.yaml`:

```yaml
multinode-gpu-fragmentation-1:
  cluster: della
  partitions:
    - llm
  gpus_per_node: 8  # count
  min_run_time: 61  # minutes
  email_file: "multinode_gpu_fragmentation.txt"
  admin_emails:
    - admin@institution.edu
```

The parameters are explained below:

- `cluster`: Specify the cluster name as it appears in the Slurm database. One cluster name per alert.

- `partitions`: Specify one or more Slurm partitions.

- `gpus_per_node`: The number of GPUs per node.

- `email_file`: The file used as a email body. This file must be found in the `email-files-path` setting in `config.yaml`. Learn more about writing custom emails.

- `min_run_time`: (Optional) The number of minutes that a job must have ran to be considered. This can be used to exclude test jobs and experimental jobs. Default: 0

- `include_running_jobs`: (Optional) If `True` then jobs in a state of `RUNNING` will be included in the calculation. The Prometheus server must be queried for each running job, which can be an expensive operation. Default: False

- `nodelist`: (Optional) Only apply this alert to jobs that ran on the specified nodes. See [example](../nodelist.md).

- `excluded_users`: (Optional) List of usernames to exclude from receiving emails.

- `admin_emails`: (Optional) The emails sent to users will also be sent to these administator emails. This applies
when the `--email` option is used.

## Report for System Administrators

Below is an example report for system administrators:

```
$ python job_defense_shield.py --multinode-gpu-fragmentation

             Multinode GPU Jobs with Fragmentation              
----------------------------------------------------------------
 JobID     User   GPUs  Nodes GPUs-per-Node Hours GPU-Eff Emails
----------------------------------------------------------------
62666282  u42994   8     2          4          7    98%    0   
62666283  u42994   8     2          4          6    98%    0   
62666284  u42994   8     2          4          6    99%    0   
62666285  u42994   8     2          4          7    98%    0   
62666286  u42994   8     2          4          6    98%    0   
62666287  u42994   8     2          4          6    98%    0   
62666288  u42994   8     2          4          7    98%    0   
62666289  u42994   8     2          4          7    99%    0   
62666290  u42994   8     2          4          7    98%    0   
62666291  u42994   8     2          4          7    98%    0   
62816261  u18375   4     2          2        1.1    10%    1 (5)   
----------------------------------------------------------------
   Cluster: della
Partitions: llm
     Start: Mon Mar 12, 2025 at 11:18 AM
       End: Wed Mar 19, 2025 at 11:18 AM
```

## Email

Below is an example email message to a user (see `email/multinode_gpu_fragmentation.txt`):

```
Hello Alan (u42994),

Below are jobs that ran on Della in the past 7 days that used 1 GPU per node
over multiple nodes:

     JobID     User   GPUs  Nodes GPUs-per-Node  Hours State GPU-eff
    60969293 aturing   4     2          2          24    TO     0%  

The GPU nodes on Della have 8 GPUs per node. For future jobs, please try to
use as few nodes as possible by allocating more GPUs per node. This is done
by modifying the --gres Slurm directive.

Replying to this automated email will open a support ticket with Research
Computing.
```

### Placeholders

The following placeholders can be used to create a custom email message:

- `<GREETING>`: The greeting that will be generated based on the choice of `greeting_method` in `config.yaml`. An example is "Hello Alan (aturing),".
- `<CLUSTER>`: The name of the cluster as defined in `config.yaml`.
- `<PARTITIONS>`: A comma-separated list of partitions as defined for the alert in `config.yaml`.
- `<GPUS-PER-NODE>`: The number of GPUs per node (i.e., `gpus_per_node`).
- `<TABLE>`: A table of jobs for the user.
- `<DAYS>`: The number of days in the time window (default is 7 days).

## Usage

Send emails to the offending users:

```
$ python job_defense_shield.py --multinode-gpu-fragmentation --email
```

See which users have received emails and when:

```
$ python job_defense_shield.py --multinode-gpu-fragmentation --check
```

## cron

Below is an example entry for `crontab`:

```
0 9 * * 1-5 /path/to/python path/to/job_defense_shield.py --multinode-gpu-fragmentation --email -M della -r llm > /path/to/log/gpu_fragmentation.log 2>&1
```
