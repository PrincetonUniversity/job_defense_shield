# GPU-Hours at 0% Utilization

This alert identifies users that have consumed the most GPU-hours
at 0% utilization.

To find users with low but non-zero GPU utilization then
see [low GPU efficiency](low_gpu_util.md).
To automatically cancel GPU jobs at 0% utilization, see [Cancel 0% GPU Jobs](cancel_gpu_jobs.md).

## Configuration File

Below is an example entry for `config.yaml`:

```yaml
zero-util-gpu-hours-1:
  cluster: della
  partitions:
    - gpu
  min_run_time:              0  # minutes
  gpu_hours_threshold_user: 24  # hours
  gpu_hours_threshold_admin: 0  # hours
  max_num_jobid:             4  # count
  email_file: "zero_util_gpu_hours.txt"
  admin_emails:
    - admin@institution.edu
```

The available settings are listed below:

- `cluster`: Specify the cluster name as it appears in the Slurm database. One cluster name
per alert.

- `partitions`: Specify one or more Slurm partitions. The number of GPU-hours is summed over all partitions.

- `min_run_time`: Minimum run time in minutes for a job to be included in the calculation. For example, if `min_run_time: 30` is used then jobs that ran for less than 30 minutes are ignored. Default: 0

- `gpu_hours_threshold_user`: Only users with greater than or equal to this number of GPU-hours at 0% utilization will receive an email.

- `gpu_hours_threshold_admin`: Only users with greater than or equal to this number of GPU-hours at 0% utilization will appear in the report for administrators.

- `email_file`: The text file to be used as the email message to users.

- `max_num_jobid`: (Optional) Maximum number of JobID's to show for a given user. If the number of
jobs per user is greater than this value then a "+" character is appended to the end of the list. Default: 4

- `include_running_jobs`: (Optional) If `True` then jobs in a state of `RUNNING` will be included in the calculation. The Prometheus server must be queried for each running job, which can be an expensive operation. Default: False

- `nodelist`: (Optional) Only apply this alert to jobs that ran on the specified nodes. See [example](../nodelist.md).

- `excluded_users`: (Optional) List of users to exclude from receiving emails.

- `admin_emails`: (Optional) The emails sent to users will also be sent to these administator emails. This applies
when the `--email` option is used.

- `email_subject`: (Optional) Subject of the email message to users.

- `report_title`: (Optional) Title of the report to system administrators.

For this alert, a GPU is said to have 0% utilization if all of the measurements made by the NVIDIA exporter over the entire job are zero. Measurements are typically made every 30 seconds or so.

!!! info "Multi-GPU Jobs"
    For jobs that allocate multiple GPUs, only the GPU-hours for the GPUs at 0% utilization are included.

Below is second example entry for `config.yaml`:

```yaml
zero-util-gpu-hours:
  cluster: stellar
  partitions:
    - gpu
  min_run_time:              30  # minutes
  gpu_hours_threshold_user:  24  # hours
  gpu_hours_threshold_admin: 12  # hours
  max_num_jobid:              3  # count
  email_file: "zero_util_gpu_hours.txt"
  admin_emails:
    - admin@institution.edu
```

For the configuration above, only jobs that ran for 30 minutes or more are considered. Users will receive
an email (when `--email` is used) if they consumed 24 GPU-hours or more at 0% utilization. System
administrators will see users in the report (using `--report`) that consumed 12 GPU-hours or more.
The JobID will be shown for up to three jobs per user.

## Report for System Administrators

Here is an example report:

```
$ job_defense_shield --zero-util-gpu-hours

                           Zero Utilization GPU-Hours
------------------------------------------------------------------------
     User   GPU-Hours-At-0%  Jobs                     JobID                    
------------------------------------------------------------------------
1   u20461       397          16    60458831,60460188,60478799,60479839+
2   u99704       196           8    60552976,60552983,60552984,60552985+
3   u04204        62          39    60457297,60457395,60457408,60460181+
4   u39983        32          40    60419086,60419088,60419089,60419090+
5   u93550        22           6    60423037,60423668,60424743,60425344+
6   u92847        17           5    60516409,60516469,60516554,60516718+
7   u18225        17          17    60461780,60467419,60467445,60487739+
8   u99455         9           4    60475110,60496234,60496390,60554903
9   u30193         8           2                      60424873,60444734
10  u62696         7          13    60422906,60540828,60545878,60545878+
------------------------------------------------------------------------
   Cluster: della
Partitions: gpu, llm
     Start: Thu Sep 1, 2024 at 08:00 AM
       End: Thu Sep 8, 2024 at 08:00 AM
```

The table above shows that user `u20461` consumed 397 GPU-hours at 0% utilization.
Four of the sixteen JobID's are shown.

## Email Message to Users

Below is an example email message:

```
Hello Alan (u12345),

You have consumed 120 GPU-hours at 0% GPU utilization in the past 7 days
on the pli-c partition(s) of della:

     JobID     GPUs  GPUs-Unused GPU-Unused-Util  Zero-Util-GPU-Hours
    62399648    8          8           0%                 36         
    62399649    8          8           0%                 36          
    62400616    8          8           0%                 36          
    62402931    6          3           0%                 12          

Please address this issues before submitting new jobs. Replying to
this automated email will open a support ticket with Research
Computing.
```

### Placeholders

The following placeholders can be used in the email file:

- `<GREETING>`: The greeting generated by `greeting-method`.
- `<CLUSTER>`: The cluster specified for the alert (i.e., `cluster`).
- `<PARTITIONS>`: The partitions listed for the alert (i.e., `partitions`).
- `<DAYS>`: Number of days in the time window (default is 7).
- `<GPU-HOURS>`: Total number of GPU-hours at 0% utilization.
- `<NUM-JOBS>`: Total number of jobs with at least one idle GPU.
- `<TABLE>`: Table of job data.
- `<JOBSTATS>`: The `jobstats` command for the first job of the user.

## Usage

Generate a report of the users with the most GPU-hours at 0% utilization:

```
$ job_defense_shield --zero-util-gpu-hours
```

Send emails to the offending users:

```
$ job_defense_shield --zero-util-gpu-hours --email
```

See which users have received emails and when they were sent:

```
$ job_defense_shield --zero-util-gpu-hours --check
```

## cron

```
0 9 * * 1-5 /path/to/job_defense_shield --zero-util-gpu-hours --email > /path/to/log/zero_util_gpu_hours.log 2>&1
```
