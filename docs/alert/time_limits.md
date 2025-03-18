# Excessive Run Time Limits

This alert identifies users that are using excessive run time limits for their jobs (e.g., requesting 3 days but only needing 3 hours).

## Configuration File

Below is an example entry for `config.yaml`:

```yaml
excessive-time-1:
  cluster: della
  partitions:
    - cpu
  min_run_time: 61              # minutes
  mode: cpu                     # cpu or gpu
  absolute_thres_hours: 100000  # used cpu-hours/gpu-hours
  overall_ratio_threshold: 0.2  # [0.0, 1.0]
  mean_ratio_threshold: 0.2     # [0.0, 1.0]
  median_ratio_threshold: 0.2   # [0.0, 1.0]
  num_top_users: 10
  num_jobs_display: 10
  email_file: "excessive_time.txt"
  admin_emails:
    - admin@institution.edu
```

The parameters are explained below:

- `cluster`: Specify the cluster name as it appears in the Slurm database. One cluster name
per alert.

- `partitions`: Specify one or more Slurm partitions.

- `min_run_time`: (Optional) Minimum run time in minutes for a job to be included in the calculation. For example, if `min_run_time: 30` is used then jobs that ran for less than 30 minutes are ignored. Default: 0

- `mode`: Either `cpu` or `gpu`. Default: `cpu`

- `absolute_thres_hours`: (Required) Minimum number of unused CPU-cores for the user to be included. If `mode` is `gpu` then this is the number of GPU-hours.

- `overall_ratio_threshold`: (Required) Used CPU/GPU-hours divided by total allocated CPU/GPU-hours.

- `mean_ratio_threshold`: (Optional) Mean of the per job ratio of used CPU/GPU-hours to allocated CPU/GPU-hours.

- `median_ratio_threshold`: (Optional) Same as above but for the median instead of the mean.

- `email_file`: The text file to be used for the email message.

- `email_subject`: Subject of the email message to users.

- `include_running_jobs`: (Optional) If `True` then jobs in a state of `RUNNING` will be included in the calculation. The Prometheus server must be queried for each running job, which can be an expensive operation. Default: False

- `nodelist`: (Optional) Only apply this alert to jobs that ran on the specified nodes. See [example](../nodelist.md).

- `excluded_users`: (Optional) List of users to exclude from receiving emails. These users will still appear
in reports for system administrators when `--report` is used.

- `admin_emails`: (Optional) The emails sent to users will also be sent to these administator emails. This applies
when the `--email` option is used.

## Report

Below is an example report:

```
$ python job_defense_shield.py --excessive-time

                         Excessive Time Limits                          
------------------------------------------------------------------------
  User   CPU-Hours  CPU-Hours  Ratio  Ratio   Ratio CPU-Rank Jobs Emails
          (Unused)    (Used)  Overall  Mean  Median
------------------------------------------------------------------------
  u18587   495341      13716    0.03   0.03   0.02     10     643   0
  u81279   105666      80061    0.43   0.43   0.38      2      41   0
  u45521   105509      21595    0.17   0.17   0.13      8     109   0
  u73275    89469       8475    0.09   0.14   0.09     16      86   0
  u43409    88689     125583    0.59   0.59   0.59      1     279   0
  u39889    81659       1002    0.01   0.01   0.01     46    1718   0
  u42091    74348      52606    0.41   0.33   0.31      3    1437   0
  u75621    63365      21265    0.25   0.22   0.21      9    3741   0
  u60876    53043      31705    0.37   0.38   0.35      6    4425   0
  u41590    51491       9565    0.16   0.16   0.15     15     318   0
------------------------------------------------------------------------
   Cluster: della
Partitions: cpu
     Start: Mon Mar 10, 2025 at 06:23 PM
       End: Mon Mar 17, 2025 at 06:23 PM

```

## Email

For an example see `email/excessive_time.txt`:

```
Hello Alan (u18587),

Below are 5 of your 643 jobs that ran on della (cpu) in the past 7 days:

     JobID   Time-Used Time-Allocated Percent-Used  CPU-Cores
    62776009  01:36:11   2-00:00:00        3%          32    
    62776014  01:32:11   2-00:00:00        3%          32    
    62776016  01:22:41   2-00:00:00        3%          32    
    62776019  01:17:48   2-00:00:00        3%          32    
    62776020  01:29:20   2-00:00:00        3%          32    

It appears that you are requesting too much time for your jobs since you are
only using on average 3% of the allocated time (for the 643 jobs). This has
resulted in 495341 CPU-hours that you scheduled but did not use (it was made
available to other jobs, however).

Please request less time by modifying the --time Slurm directive. This will
lower your queue times and allow the Slurm job scheduler to work more
effectively for all users.

Time-Used is the time (wallclock) that the job needed. The total time allocated
for the job is Time-Allocated. The format is DD-HH:MM:SS where DD is days,
HH is hours, MM is minutes and SS is seconds. Percent-Used is Time-Used
divided by Time-Allocated.

Replying to this automated email will open a support ticket with Research
Computing.
```

### Tags

The following tags can be used in the email file:

- `<GREETING>`: The greeting generated by `greeting-method`.
- `<CLUSTER>`: The cluster specified for the alert (i.e., `cluster`).
- `<PARTITIONS>`: The partitions listed for the alert (i.e., `partitions`).
- `<MODE-UPPER>`: Mode in upper case (i.e., CPU or GPU).
- `<AVERAGE>`: Mean of per job CPU/GPU-hours used divided by allocated.
- `<DAYS>`: Number of days in the time window (default is 7).
- `<NUM-JOBS>`: Total number of jobs with at least one idle GPU.
- `<NUM-JOBS-DISPLAY>`: Number of jobs to list in table in email to user.
- `<TABLE>`: Table of job data.
- `<UNUSED-HOURS>`: Total number of unused CPU/GPU-hours.

## Usage

Send emails to offending users:

```
$ python job_defense_shield.py --excessive-time --email
```
