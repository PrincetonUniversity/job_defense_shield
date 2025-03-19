# Excess CPU Memory

This alert sends emails to users that are allocating excess CPU memory.
For example, jobs that use 1 GB but allocate 100 GB.

## Configuration File


```yaml
excess-cpu-memory:
  clusters:
    - della
  partition:
    - cpu
  tb_hours_threshold: 100       # terabyte-hours
  ratio_threshold: 0.35         # [0.0, 1.0]
  mean_ratio_threshold: 0.35    # [0.0, 1.0]
  median_ratio_threshold: 0.35  # [0.0, 1.0]
  num_top_users: 5
  admin_emails:
    - admin@institution.edu
```

Each configuration parameter is explained below:

- `cluster`: Specify the cluster name as it appears in the Slurm database. One cluster name
per alert.

- `partitions`: Specify one or more Slurm partitions.
      
- `min_run_time`: (Optional) Minimum run time in minutes for a job to be included in the calculation. For example, if `min_run_time: 30` is used then jobs that ran for less than 30 minutes are ignored. Default: 0

- `tb_hours_threshold`: The threshold for TB-hours per day. This value
is multiplied by `--days` to determine the threshold of TB-hours for
the user to receive an email message.

- `ratio_threshold`: This quantity is the sum of CPU memory used divded
by the total memory allocated for all jobs of a given user in the specified
time window. This quantity varies between 0 and 1.

- `median_ratio_threshold`: This is median value of memory used divided by
memory allocated for the individual jobs of the user.

- `mean_ratio_threshold`: The mean value of the memory used divided by the
memory allocated per job for a given user. This quantity varies between 0
and 1.

- `cores_per_node`: (Optional) Number of CPU-cores per node.

- `mem_per_node`: (Optional) CPU memory per node in GB.

- `cores_fraction`: (Optional) Fraction of the cores per node that will cause the job to be ignored. For instance, with `cores_fraction: 0.8` if a node has 32 cores and the job allocates 30 of them then the job will be ignored since 30/32 > 0.8.

- `num_top_users``: (Optional) Only consider the number of users equal to `num_top_users` as sorted by "wasted CPU-hours".

- `include_running_jobs`: (Optional) If `True` then jobs in a state of `RUNNING` will be included in the calculation. The Prometheus server must be queried for each running job, which can be an expensive operation. Default: False

- `nodelist`: (Optional) Only apply this alert to jobs that ran on the specified nodes. See [example](../nodelist.md).

- `excluded_users`: (Optional) List of users to exclude from receiving emails. These users will still appear
in reports for system administrators when `--report` is used.

- `email_file`: The text file to be used for the email message.

- `admin_emails`: (Optional) The emails sent to users will also be sent to these administator emails. This applies
when the `--email` option is used.

## Report

Below is a sample report:

```
$ python job_defense_shield.py --excess-cpu-memory

                         Users Allocating Excess CPU Memory                         
------------------------------------------------------------------------------
 User   Unused    Used    Ratio  Ratio   Ratio Proportion CPU-Hrs  Jobs Emails
       (TB-Hrs) (TB-Hrs) Overall  Mean  Median                                
------------------------------------------------------------------------------
u34981    164      163     0.50   0.50   0.54     0.19      8370    310    0  
u76237    135        0     0.00   0.00   0.00     0.08      5628    243    0  
u63098     90        1     0.02   0.02   0.02     0.05       730     22    0  
u26174     71      189     0.73   0.72   0.71     0.15      7425    551    0  
u89812     51       83     0.62   0.61   0.62     0.08      4023   2040    0  
------------------------------------------------------------------------------
   Cluster: della
Partitions: cpu
     Start: Tue Mar 11, 2025 at 11:45 AM
       End: Tue Mar 18, 2025 at 11:45 AM
```

## Email

Below is an example email message to a user (see `email/excess_cpu_memory.txt`):

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

### Tags

These tags can be used to generate custom emails:

- `<GREETING>`: The greeting generated by `greeting-method`.
- `<CLUSTER>`: The cluster specified for the alert (i.e., `cluster`).
- `<PARTITIONS>`: The partitions listed for the alert (i.e., `partitions`).
- `<CASE>`: The rank of the user (see email file).
- `<DAYS>`: Time window of the alert in days.
- `<NUM-JOBS>`: Total number of jobs with at least one idle GPU.
- `<UNUSED>`: Memory-hours that were unused.
- `<PCT>`: Mean memory efficiency or average ratio of used CPU memory to allocated.
- `<TABLE>`: Table of job data.
- `<JOBSTATS>`: `jobstats` command for the first JobID (`$ jobstats 12345678`).

## Usage

Send emails to users:

```
$ python job_defense_shield.py --excess-cpu-memory --email
```
