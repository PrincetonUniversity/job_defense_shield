# Automatically Cancel GPU Jobs at 0% Utilization

This alert cancels GPU jobs at 0% utilization.

!!! note "Elevated Privileges"
    This alert is different than the others in that it must be ran as
    a user with sufficient privileges to call `scancel`.

The software can be configured to cancel jobs based on GPU utilization during the first N minutes of a job (see `cancel_minutes`) and/or during the last N minutes (see `sliding_cancel_minutes`). Warning emails can be sent to the users before cancellation.

The ability to automatically cancel GPU jobs is one of the most popular features of [Jobstats](https://github.com/PrincetonUniversity/jobstats).

## Configuration File

Below is an example entry for the configuration file:

```yaml
cancel-zero-gpu-jobs-1:
  cluster: della
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
  sliding_warning_minutes: 240  # minutes
  sliding_cancel_minutes:  300  # minutes
  email_file_sliding_warning: "cancel_gpu_jobs_sliding_warning.txt"
  email_file_sliding_cancel:  "cancel_gpu_jobs_sliding_cancel.txt"
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

- `partitions`: Specify one or more Slurm partitions.

- `sampling_period_minutes`: Number of minutes between executions of this alert. This number must be equal to the time between `cron` jobs for this alert (see [cron](#cron) section below). One reasonable choice for this setting is 15 minutes.

- `first_warning_minutes`: (Optional) Send a warning email for 0% GPU utilization after this number of minutes from the start of the job.

- `second_warning_minutes`: (Optional) Send a second warning email for 0% GPU utilization after this number of minutes from the start of the job.

- `cancel_minutes`: (Optional/Required) Cancel jobs with 0% GPU utilization after this number of minutes from the start of the job. One must set `cancel_minutes` and/or `sliding_cancel_minutes`.

- `email_file_first_warning`: (Optional) File to be used for the first warning email.

- `email_file_second_warning`: (Optional) File to be used for the second warning email.

- `email_file_cancel`: (Optional/Required) File to be used for the cancellation email. If `cancel_minutes` is set then this file is required.

- `sliding_warning_minutes`: (Optional/Required) Send a warning email for jobs found with 0% GPU utilization during a sliding time window of this number of minutes. This setting is required if `sliding_cancel_minutes` is used. If `cancel_minutes` and `sliding_cancel_minutes` are both used then a job must run for `cancel_minutes` plus `sliding_warning_minutes` before a warning can be sent using the sliding window approach.

- `sliding_cancel_minutes`: (Optional/Required) Cancel jobs found with 0% GPU utilization during a sliding time window of this number of minutes. This setting uses a sliding time window whereas `cancel_minutes` uses a fixed time window over the start of job. If `cancel_minutes` is also set then a job must run for `cancel_minutes` plus `sliding_cancel_minutes` before it can be cancelled by the sliding window approach. Users are guaranteed to receive a warning email before cancellation. One must set `cancel_minutes` and/or `sliding_cancel_minutes`.

- `email_file_sliding_warning`: (Optional/Required) File to be used for the warning email. If `sliding_cancel_minutes` is set then this setting and `sliding_warning_minutes` are required.

- `email_file_sliding_cancel`: (Optional/Required) File to be used for the cancellation email. This setting is required if `sliding_cancel_minutes` is set.

- `email_subject`: (Optional) Subject of the email message to users.

- `jobid_cache_path`: (Optional/Required) Path to a writable directory to store hidden cache files. Caching decreases the load on the Prometheus server. This setting is required if `sliding_cancel_minutes` is set. Use `ls -a` to see the hidden files.

- `max_interactive_hours`: (Optional) An interactive job will only be cancelled if the run time limit is greater than `max_interactive_hours` and the number of allocated GPUs is less than or equal to `max_interactive_gpus`. Remove these lines if interactive jobs should not receive special treatment. An interactive job is one with a `jobname` that starts with either `interactive` or `sys/dashboard`. If `max_interactive_hours` is specified then `max_interactive_gpus` is required.

- `max_interactive_gpus`: (Optional) See `max_interactive_hours` above.

- `gpu_frac_threshold`: (Optional) For a given job, let `g` be the ratio of the number of GPUs with non-zero utilization to the number of allocated GPUs. Jobs with `g` greater than or equal to  `gpu_frac_threshold` will be excluded. For example, if a job uses 7 of the 8 allocated GPUs and `gpu_frac_threshold` is 0.8 then it will be excluded from cancellation since 7/8 > 0.8. This quantity varies between 0 and 1. Default: 1.0

- `fraction_of_period`: (Optional) Fraction of the sampling period that can be used for querying the Prometheus server. The sampling period or `sampling_period_minutes` is the time between `cron` jobs for this alert. This setting imposes a limit on the amount of time spent on querying the server so that the code finishes before the next `cron` job. This quantity varies between 0 and 1. If output such as `INFO: Only cached 42 of 100 jobs. Will try again on next call.` is seen then consider increasing `fraction_of_period` and/or `sampling_period_minutes`. If there are multiple entries for this alert then use a maximum value for this setting of 1 divided by the number of entries. Default: 0.5

- `warning_frac`: (Optional) Fraction of `sliding_warning_minutes` that must pass before a job that was previously found to be using the GPUs will be re-examined for idle GPUs. This quantity varies between 0 and 1. The default value of 1.0 minimizes the load on the Prometheus server but it can allow jobs with idle GPUs to run for longer than necessary. To cancel jobs sooner, at the expense of more calls to Prometheus, use a smaller value such as 0.5. Default: 1.0

- `nodelist`: (Optional) Only apply this alert to jobs that ran on the specified nodes. See [example](../nodelist.md).

- `excluded_users`: (Optional) List of usernames to exclude from this alert.

- `do_not_cancel`: (Optional) If `True` then `scancel` will not be called. This is useful for testing only. In this case, one should call the alert with `--email --no-emails-to-users`. Default: `False`

- `warnings_to_admin`: (Optional) If `False` then warning emails will not be sent to `admin_emails`. Only cancellation emails will be sent. Default: `True`

- `admin_emails`: (Optional) List of administrator email addresses that should receive the warning and cancellation emails that are sent to users.

!!! note "Times are Not Exact"
    Jobs are not cancelled after exactly `cancel_minutes` or `sliding_cancel_minutes` since Slurm jobs can start at any time and the alert is only called every N minutes via cron or another scheduler. The same is true for warning emails.

In Jobstats, a GPU is said to have 0% utilization if all of the measurements made by the NVIDIA exporter over a given time window are zero. Measurements are typically made every 30 seconds or so. For the actual value at your institution see `SAMPLING_PERIOD` in `config.py` for [Jobstats](https://github.com/PrincetonUniversity/jobstats).

### Example Configurations

Jobs with GPUs that are idle for the first 2 hours (120 minutes) will be cancelled:

```yaml
cancel-zero-gpu-jobs-1:
  cluster:
    - della
  partitions:
    - gpu
    - llm
  sampling_period_minutes: 15  # minutes
  first_warning_minutes:   60  # minutes
  scond_warning_minutes:  105  # minutes
  cancel_minutes:         120  # minutes
  email_file_first_warning:  "cancel_gpu_jobs_warning_1.txt"
  email_file_second_warning: "cancel_gpu_jobs_warning_2.txt"
  email_file_cancel:         "cancel_gpu_jobs_scancel_3.txt"
  jobid_cache_path: /path/to/writable/directory/
  admin_emails:
    - admin@institution.edu
```

The configuration above will send warning emails after 60 and 105 minutes.

The example below is the same as that above except only one warning email will be sent:

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

Cancel jobs that are found to have 0% GPU utilization over any time period of 5 hours (300 minutes):

```yaml
cancel-zero-gpu-jobs-1:
  cluster:
    - della
  partitions:
    - gpu
    - llm
  sampling_period_minutes:  15  # minutes
  sliding_warning_minutes: 240  # minutes
  sliding_cancel_minutes:  300  # minutes
  email_file_sliding_warning: "cancel_gpu_jobs_sliding_warning.txt"
  email_file_sliding_cancel:  "cancel_gpu_jobs_sliding_cancel.txt"
  jobid_cache_path: /path/to/writable/directory/
  admin_emails:
    - admin@institution.edu
```

For the entry above, the user would receive a warning email after 4 hours (240 minutes).

The example that follows uses both cancellation methods. Jobs with GPUs that are idle for the first 2 hours (120 minutes) will be cancelled. After this period, jobs with an idle GPU for 5 hours (300 minutes) will be cancelled.

```yaml
cancel-zero-gpu-jobs-1:
  cluster: della
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
  sliding_warning_minutes: 240  # minutes
  sliding_cancel_minutes:  300  # minutes
  email_file_sliding_warning: "cancel_gpu_jobs_sliding_warning.txt"
  email_file_sliding_cancel:  "cancel_gpu_jobs_sliding_cancel.txt"
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

## First Warning Email (Fixed Window at Start of Job)

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
- `<CLUSTER>`: The cluster specified for the alert.
- `<PARTITIONS>`: The partitions listed for the alert.
- `<SAMPLING>`: The sampling period in minutes (`sampling_period_minutes`).
- `<MINUTES-1ST>`: Number of minutes before the first warning is sent (`first_warning_minutes`).
- `<HOURS-1ST>`: Number of hours before the first warning is sent.
- `<CANCEL-MIN>`: Number of minutes a job must run for before being cancelled (`cancel_minutes`).
- `<CANCEL-HRS>`: Number of hours a job must run for before being cancelled.
- `<TABLE>`: Table of job data.
- `<JOBSTATS>`: `jobstats` command for the first JobID (`$ jobstats 12345678`).
- `<SCANCEL>`: `scancel` command for the first JobID (`$ scancel 12345678`).

## Second Warning Email (Fixed Window at Start of Job)

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
- `<CLUSTER>`: The cluster specified for the alert.
- `<PARTITIONS>`: The partitions listed for the alert.
- `<SAMPLING>`: The sampling period in minutes (`sampling_period_minutes`).
- `<MINUTES-1ST>`: Number of minutes before the first warning is sent (`first_warning_minutes`).
- `<MINUTES-2ND>`: Number of minutes before the second warning is sent (`second_warning_minutes`).
- `<CANCEL-MIN>`: Number of minutes a job must run for before being cancelled (`cancel_minutes`).
- `<CANCEL-HRS>`: Number of hours a job must run for before being cancelled.
- `<TABLE>`: Table of job data.
- `<JOBSTATS>`: `jobstats` command for the first JobID (`$ jobstats 12345678`).
- `<SCANCEL>`: `scancel` command for the first JobID (`$ scancel 12345678`).

## Cancellation Email (Fixed Window at Start of Job)

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
- `<CLUSTER>`: The cluster specified for the alert.
- `<PARTITIONS>`: The partitions listed for the alert.
- `<SAMPLING>`: The sampling period in minutes (`sampling_period_minutes`).
- `<CANCEL-MIN>`: Number of minutes a job must run for before being cancelled (`cancel_minutes`).
- `<CANCEL-HRS>`: Number of hours a job must run for before being cancelled (`cancel_minutes`/60).
- `<TABLE>`: Table of job data.
- `<JOBSTATS>`: `jobstats` command for the first JobID (`$ jobstats 12345678`).
- `<SCANCEL>`: `scancel` command for the first JobID (`$ scancel 12345678`).

## Warning Email (Sliding Window Over Last N Minutes)

Below is an example email for the warning (see `email/cancel_gpu_sliding_warning.txt`):

```
Hi Alan (aturing),

You have job(s) that have not used the GPU(s) for the last 3 hours:

     JobID   Cluster  Partition  State   GPUs GPUs-Unused GPU-Util  Hours
   60131148   della      gpu    RUNNING    4       4         0%       3

Your jobs will be AUTOMATICALLY CANCELLED if they are found to not be using the
GPUs for a period of 4 hours.

Please consider cancelling the job(s) listed above by using the "scancel"
command:

   $ scancel 60131148

Replying to this automated email will open a support ticket with Research
Computing.
```

### Placeholders

The following placeholders can be used in the email file:

- `<GREETING>`: The greeting generated by `greeting-method`.
- `<CLUSTER>`: The cluster specified for the alert.
- `<PARTITIONS>`: The partitions listed for the alert.
- `<SAMPLING>`: The sampling period in minutes (`sampling_period_minutes`).
- `<WARNING-MIN>`: Number of minutes before the warning email is sent (`sliding_warning_minutes`).
- `<WARNING-HRS>`: Number of hours before the warning email is sent (`sliding_warning_minutes`/60).
- `<CANCEL-MIN>`: Time period in minutes with 0% GPU utilization for a job to be cancelled (`sliding_cancel_minutes`).
- `<CANCEL-HRS>`: Time period in hours with 0% GPU utilization for a job to be cancelled (`sliding_cancel_minutes`/60).
- `<TABLE>`: Table of job data.
- `<JOBSTATS>`: `jobstats` command for the first JobID (`$ jobstats 12345678`).
- `<SCANCEL>`: `scancel` command for the first JobID (`$ scancel 12345678`).

## Cancellation Email (Sliding Window Over Last N Minutes)

Below is an example email (see `email/cancel_gpu_jobs_sliding_cancel.txt`):

```
Hi Alan (aturing),

The jobs below have been cancelled because they did not use the GPU(s) for the
last 4 hours:

     JobID  Cluster  Partition   State    GPUs  GPUs-Unused  GPU-Util  Hours
   60131148  della      gpu    CANCELLED    4        4          0%       4

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
- `<CANCEL-MIN>`: Time period in minutes with 0% GPU utilization for a job to be cancelled (`sliding_cancel_minutes`).
- `<CANCEL-HRS>`: Time period in hours with 0% GPU utilization for a job to be cancelled (`sliding_cancel_minutes`/60).
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
