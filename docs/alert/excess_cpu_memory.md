# Over-Allocating CPU Memory

This alert identifies users that are over-allocating CPU memory.

!!! info "CPU Only"
    This alert is for CPU jobs. For GPU jobs, see [this alert](excess_cpu_mem_per_gpu.md).

## Configuration File

Below is an example entry for `config.yaml`:

```yaml
excess-cpu-memory-1:
  clusters: della
  partition:
    - cpu
  min_run_time:             61  # minutes
  tb_hours_threshold:       50  # terabyte-hours
  ratio_threshold:        0.35  # [0.0, 1.0]
  mean_ratio_threshold:   0.35  # [0.0, 1.0]
  median_ratio_threshold: 0.35  # [0.0, 1.0]
  num_top_users:            10  # count
  email_file: "excess_cpu_memory.txt"
  admin_emails:
    - admin@institution.edu
```

Each configuration parameter is explained below:

- `cluster`: Specify the cluster name as it appears in the Slurm database.

- `partitions`: Specify one or more Slurm partitions.
      
- `tb_hours_threshold`: The threshold for TB-hours per day. This value
is multiplied by `--days` to determine the threshold of TB-hours for
the user to receive an email message.

- `ratio_threshold`: This quantity is the sum of CPU memory used divded
by the total memory allocated for all jobs of a given user.
This quantity varies between 0 and 1.

- `median_ratio_threshold`: This is median value of memory used divided by
memory allocated for the individual jobs of the user. This quantity varies between 0 and 1.

- `mean_ratio_threshold`: The mean value of the memory used divided by the
memory allocated per job for a given user. This quantity varies between 0
and 1.

- `email_file`: The text file to be used for the email message to users.

- `min_run_time`: (Optional) Minimum run time of a job in units of minutes. If `min_run_time: 61` then jobs that ran for an hour or less are ignored. Default: 0

- `cores_per_node`: (Optional) Number of CPU-cores per node.

- `mem_per_node`: (Optional) CPU memory per node in units of GB.

- `cores_fraction`: (Optional) Fraction of the cores per node that will cause the job to be ignored. For instance, with `cores_fraction: 0.8` if a node has 32 cores and the job allocates 30 of them then the job will be ignored since 30/32 > 0.8. Default: 1

- `num_top_users`: (Optional) Only consider the number of users equal to this value after sorting by "unused TB-hours". Default: 15

- `num_jobs_display`: (Optional) Number of jobs to display in the email message to users. Default: 10

- `include_running_jobs`: (Optional) If `True` then jobs in a state of `RUNNING` will be included in the calculation. The Prometheus server must be queried for each running job, which can be an expensive operation. Default: False

- `nodelist`: (Optional) Only apply this alert to jobs that ran on the specified nodes. See [example](../nodelist.md).

- `excluded_users`: (Optional) List of usernames to exclude from the alert.

- `admin_emails`: (Optional) List of administrator email addresses that should receive copies of the emails that are sent to users.

- `email_subject`: (Optional) Subject of the email message to users.

- `report_title`: (Optional) Title of the report to system administrators.

!!! info
    When `cores_per_node` and `mem_per_node` are defined, only jobs using more memory per core than `mem_per_node` divided by `cores_per_node` are included. For instance, if a node provides 64 cores and 512 GB of memory, only jobs allocating more than 8 GB/core are considered.

## Report for System Administrators

Below is an example report:

```
$ job_defense_shield --excess-cpu-memory

                         Users Allocating Excess CPU Memory                         
------------------------------------------------------------------------------
 User   Unused    Used    Ratio  Ratio   Ratio Proportion CPU-Hrs  Jobs Emails
       (TB-Hrs) (TB-Hrs) Overall  Mean  Median                                
------------------------------------------------------------------------------
u34981    164      163     0.50   0.50   0.54     0.19      8370    310  0  
u76237    135        0     0.00   0.00   0.00     0.08      5628    243  1 (5)
u63098     90        1     0.02   0.02   0.02     0.05       730     22  3 (1)
u26174     71      189     0.73   0.72   0.71     0.15      7425    551  0  
u89812     51       83     0.62   0.61   0.62     0.08      4023   2040  0  
------------------------------------------------------------------------------
   Cluster: della
Partitions: cpu
     Start: Tue Mar 11, 2025 at 11:45 AM
       End: Tue Mar 18, 2025 at 11:45 AM
```

## Email Message to Users

Below is an example email (see `email/excess_cpu_memory.txt`):

```
Hello Alan (u34981),

Below are 10 of your 1725 jobs that ran on della (cpu) in the past 7 days:

     JobID   Memory-Used Memory-Allocated Percent-Used  Cores  Hours
    62623577     0 GB         20 GB            0%        1     16.4 
    62626492     1 GB         20 GB            5%        1     15.5 
    62626494     1 GB         20 GB            5%        1     15.5 
    62626495     1 GB         20 GB            5%        1     15.5 

It appears that you are requesting too much CPU memory for your jobs since you
are only using on average 3% of the allocated memory (for the 1725 jobs). This
has resulted in 161 TB-hours of unused memory which is equivalent to making
5 nodes unavailable to all users (including yourself) for one week! A TB-hour is
the allocation of 1 terabyte of memory for 1 hour.

Replying to this automated email will open a support ticket with Research
Computing.
```

### Placeholders

The following placeholders can be used in the email file:

- `<GREETING>`: The greeting generated by `greeting-method`.
- `<CLUSTER>`: The cluster specified for the alert (i.e., `cluster`).
- `<PARTITIONS>`: A comma-separated list of the partitions used by the user.
- `<DAYS>`: Time window of the alert in days (7 is default).
- `<CASE>`: The rank of the user (see email file).
- `<NUM-JOBS>`: Number of jobs that are over-allocating memory.
- `<UNUSED>`: Memory-hours that were unused.
- `<PERCENT>`: Mean memory efficiency or average ratio of used CPU memory to allocated.
- `<TABLE>`: Table of job data.
- `<JOBSTATS>`: The `jobstats` command for the first job of the user.

When `mem_per_node` and `cores_per_node` are used then one more placeholder is available:

- `<NUM-WASTED-NODES>`: The number of wasted nodes due to the wasted CPU memory. This is equal to
the number of unused TB-hours divided by the product of the CPU memory per node in TB and the number of hours in the time window (default is 168 hours or 7 days).

## Usage

Generate a report for system administrators:

```
$ job_defense_shield --excess-cpu-memory
```

Send emails to the offending users:

```
$ job_defense_shield --excess-cpu-memory --email
```

See which users have received emails and when:

```
$ job_defense_shield --excess-cpu-memory --check
```

## cron

Below is an example `crontab` entry:

```
0 9 * * 1-5 /path/to/job_defense_shield --excess-cpu-memory --email > /path/to/log/excess_cpu_memory.log 2>&1
```
