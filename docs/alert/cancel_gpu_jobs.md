# Automatically Cancel GPU Jobs at 0% Utilization

This is one of the most popular features of [Jobstats](https://github.com/PrincetonUniversity/jobstats).
This alert automatically cancels jobs with GPUs at 0% utilization.
Up to two warning emails can be sent before each job is cancelled.

!!! note "Elevated Privileges"
    This alert is different than the others in that it must be ran as
    a user with sufficient privileges to call `scancel`.

## Configuration File

Below is an example entry for the configuration file:

```yaml
cancel-zero-gpu-jobs-1:
  cluster:
    - della
  partitions:
    - gpu
    - llm
  sampling_period_minutes: 15  # minutes
  first_warning_minutes:   60  # minutes
  second_warning_minutes: 105  # minutes
  cancel_minutes:         120  # minutes
  email_file_first_warning:  "cancel_gpu_jobs_warning_1.txt"
  email_file_second_warning: "cancel_gpu_jobs_warning_2.txt"
  email_file_cancel:         "cancel_gpu_jobs_scancel_3.txt"
  jobid_cache_path: /path/to/writable/directory/
  max_interactive_hours: 8
  max_interactive_gpus: 1
  do_not_cancel: False
  warnings_to_admin: True
  admin_emails:
    - admin@institution.edu
  excluded_users:
    - u12345
    - u23456
```

The settings are explained below:

- `cluster`: Specify the cluster name as it appears in the Slurm database.
per alert.

- `partitions`: Specify one or more Slurm partitions.

- `sampling_period_minutes`: Number of minutes between executions of this alert. This number must also be the same in `cron` (see [cron](#cron) section below) or the scheduler that is used.

- `first_warning_minutes`: (Optional) Number of minutes that the job must run before the first warning email can be sent.

- `second_warning_minutes`: (Optional) Number of minutes that the job must run before the second warning email can be sent.

- `cancel_minutes`: (Required) Number of minutes that the job must run before it can be cancelled.

- `email_file_first_warning`: (Optional) File to be used for the first warning email.

- `email_file_second_warning`: (Optional) File to be used for the second warning email.

- `email_file_cancel`: (Required) File to be used for the cancellation email.

- `email_subject`: (Optional) Subject of the email message to users.

- `jobid_cache_path`: (Optional) Path to a writable directory where a cache file containing the `jobid` of each job known to be using the GPUs is stored. This is a binary file with the name `.jobid_cache.pkl`. Including this setting will eliminate redundant calls to the Prometheus server.

- `max_interactive_hours`: (Optional) An interactive job will only be cancelled if the run time limit is greater than `max_interactive_hours` and the number of allocated GPUs is less than or equal to `max_interactive_gpus`. Remove these lines if interactive jobs should not receive special treatment. An interactive job is one with a `jobname` that starts with either `interactive` or `sys/dashboard`.

- `max_interactive_gpus`: (Optional) See line above.

- `gpu_frac_threshold`: For a given job, let `g` be the ratio of the number of GPUs with non-zero utilization to the number of allocated GPUs. Jobs with `g` greater than or equal to  `gpu_frac_threshold` will be excluded. For example, if a job uses 7 of the 8 allocated GPUs and `gpu_frac_threshold` is 0.8 then it will be excluded from cancellation since 7/8 > 0.8. Default: 1.0

- `nodelist`: (Optional) Only apply this alert to jobs that ran on the specified nodes. See [example](../nodelist.md).

- `excluded_users`: (Optional) List of usernames to exclude from this alert.

- `do_not_cancel`: (Optional) If `True` then `scancel` will not be called. This is useful for testing only. In this case, one should call the alert with `--email --no-emails-to-users`. Default: `False`

- `warnings_to_admin`: (Optional) If `False` then warning emails will not be sent to `admin_emails`. Only cancellation emails will be sent. Default: `True`

- `admin_emails`: (Optional) List of administrator email addresses that should receive the warning and cancellation emails that are sent to users.

Note that jobs are not cancelled after exactly `cancel_minutes` since the alert is only called every N minutes via cron or another scheduler. The same is true for warning emails.

In Jobstats, a GPU is said to have 0% utilization if all of the measurements made by the NVIDIA exporter are zero. Measurements are typically made every 30 seconds or so. For the actual value see `SAMPLING_PERIOD` in `config.py` for [Jobstats](https://github.com/PrincetonUniversity/jobstats).

### Example Configurations

The example below will send one warning email and then cancel the jobs:

```yaml
cancel-zero-gpu-jobs-1:
  cluster:
    - della
  partitions:
    - gpu
    - llm
  sampling_period_minutes: 15  # minutes
  first_warning_minutes:   60  # minutes
  cancel_minutes:         120  # minutes
  email_file_first_warning: "cancel_gpu_jobs_warning_1.txt"
  email_file_cancel:        "cancel_gpu_jobs_scancel_3.txt"
  jobid_cache_path: /path/to/writable/directory/
  admin_emails:
    - admin@institution.edu
```

The example below will send no warnings but only cancel jobs after 120 minutes:

```yaml
cancel-zero-gpu-jobs-1:
  cluster:
    - della
  partitions:
    - gpu
    - llm
  sampling_period_minutes: 15  # minutes
  cancel_minutes:         120  # minutes
  email_file_cancel: "cancel_gpu_jobs_scancel_3.txt"
  jobid_cache_path: /path/to/writable/directory/
  admin_emails:
    - admin@institution.edu
```

## Testing

For testing, be sure to use:

```yaml
  do_not_cancel: True
```

Additionally, add the `--no-emails-to-users` flag:

```
$ job_defense_shield --cancel-zero-gpu-jobs --email --no-emails-to-users
```

Learn more about [email testing](../emails.md#testing-the-sending-of-emails-to-users).

## First Warning Email

Below is an example email for the first warning (see `email/cancel_gpu_jobs_warning_1.txt`):

```
Hi Alan (aturing),

You have GPU job(s) that have been running for nearly 1 hour but appear to not
be using the GPU(s):

     JobID    Cluster Partition  GPUs-Allocated  GPUs-Unused GPU-Util  Hours
   60131148    della     gpu            4             4         0%       1  

Your jobs will be AUTOMATICALLY CANCELLED if they are found to not be using the
GPUs for 2 hours.

Please consider cancelling the job(s) listed above by using the "scancel"
command:

   $ scancel 60131148

Replying to this automated email will open a support ticket with Research
Computing.
```

### Placeholders

The following placeholders can be used in the email file:

- `<GREETING>`: The greeting generated by `greeting-method`.
- `<CLUSTER>`: The cluster specified for the alert (i.e., `cluster`).
- `<PARTITIONS>`: The partitions listed for the alert (i.e., `partitions`).
- `<SAMPLING>`: The sampling period in minutes (`sampling_period_minutes`).
- `<MINUTES-1ST>`: Number of minutes before the first warning is sent (`first_warning_minutes`).
- `<HOURS-1ST>`: Number of hours before the first warning is sent.
- `<CANCEL-MIN>`: Number of minutes a job must run for before being cancelled (`cancel_minutes`).
- `<CANCEL-HRS>`: Number of hours a job must run for before being cancelled.
- `<TABLE>`: Table of job data.
- `<JOBSTATS>`: `jobstats` command for the first JobID (`$ jobstats 12345678`).
- `<SCANCEL>`: `scancel` command for the first JobID (`$ scancel 12345678`).

## Second Warning Email

Below is an example email for the second warning (see `email/cancel_gpu_jobs_warning_2.txt`):

```
Hi Alan (aturing),

This is a second warning. The jobs below will be cancelled in about 15 minutes
unless GPU activity is detected:

     JobID    Cluster Partition  GPUs-Allocated  GPUs-Unused GPU-Util  Hours
   60131148    della     gpu            4             4         0%      1.6  

Replying to this automated email will open a support ticket with Research
Computing.
```

### Placeholders

The following placeholders can be used in the email file:

- `<GREETING>`: The greeting generated by `greeting-method`.
- `<CLUSTER>`: The cluster specified for the alert (i.e., `cluster`).
- `<PARTITIONS>`: The partitions listed for the alert (i.e., `partitions`).
- `<SAMPLING>`: The sampling period in minutes (`sampling_period_minutes`).
- `<MINUTES-1ST>`: Number of minutes before the first warning is sent (`first_warning_minutes`).
- `<MINUTES-2ND>`: Number of minutes before the second warning is sent (`second_warning_minutes`).
- `<CANCEL-MIN>`: Number of minutes a job must run for before being cancelled (`cancel_minutes`).
- `<CANCEL-HRS>`: Number of hours a job must run for before being cancelled.
- `<TABLE>`: Table of job data.
- `<JOBSTATS>`: `jobstats` command for the first JobID (`$ jobstats 12345678`).
- `<SCANCEL>`: `scancel` command for the first JobID (`$ scancel 12345678`).

## Cancellation Email

Below is an example email (see `email/cancel_gpu_jobs_scancel_3.txt`):

```
Hi Alan (aturing),

The jobs below have been cancelled because they ran for more than 2 hours at
0% GPU utilization:

     JobID   Cluster  Partition    State    GPUs-Allocated GPU-Util  Hours
   60131148   della      gpu     CANCELLED         4          0%      2.1

See our GPU Computing webpage for three common reasons for encountering zero GPU
utilization:

    https://your-institution.edu/knowledge-base/gpu-computing

Replying to this automated email will open a support ticket with Research
Computing.
```

### Placeholders

The following placeholders can be used in the email file:

- `<GREETING>`: The greeting generated by `greeting-method`.
- `<CLUSTER>`: The cluster specified for the alert (i.e., `cluster`).
- `<PARTITIONS>`: The partitions listed for the alert (i.e., `partitions`).
- `<SAMPLING>`: The sampling period in minutes (`sampling_period_minutes`).
- `<CANCEL-MIN>`: Number of minutes a job must run for before being cancelled (`cancel_minutes`).
- `<CANCEL-HRS>`: Number of hours a job must run for before being cancelled.
- `<TABLE>`: Table of job data.
- `<JOBSTATS>`: `jobstats` command for the first JobID (`$ jobstats 12345678`).
- `<SCANCEL>`: `scancel` command for the first JobID (`$ scancel 12345678`).

## `cron`

Below is an example crontab for this alert:

```
*/15 * * * * /path/to/job_defense_shield --cancel-zero-gpu-jobs --email -M della -r gpu > /path/to/log/zero_gpu_utilization.log 2>&1
```

Note that the alert is ran every 15 minutes. This must also be the value of `sampling_period_minutes`.


## Report

There is no report for this alert. To find out which users have the most GPU-hours at 0% utilization, see [this alert](zero_gpu_util.md). If you are automatically cancelling GPU jobs then no users should be able to waste significant resources.

## Other Projects

One can also automatically cancel GPU jobs using the [HPC Dashboard](https://www.slurmdash.com/) by Arizona State University.
