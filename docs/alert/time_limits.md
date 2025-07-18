# Excessive Run Time Limits for CPU Jobs

This alert identifies users with excessive run time limits for CPU jobs (e.g., requesting 3 days but only needing 3 hours).

## Configuration File

Below is an example entry for `config.yaml`:

```yaml
excessive-time-cpu-1:
  cluster: della
  partitions:
    - cpu
  min_run_time:             61  # minutes
  absolute_thres_hours: 100000  # unused cpu-hours
  overall_ratio_threshold: 0.2  # [0.0, 1.0]
  mean_ratio_threshold:    0.2  # [0.0, 1.0]
  median_ratio_threshold:  0.2  # [0.0, 1.0]
  num_top_users:            10  # count
  num_jobs_display:         10  # count
  email_file: "excessive_time.txt"
  admin_emails:
    - admin@institution.edu
```

The parameters are explained below:

- `cluster`: Specify the cluster name as it appears in the Slurm database.

- `partitions`: Specify one or more Slurm partitions.

- `absolute_thres_hours`: Minimum number of unused CPU-hours for the user to be included.

- `overall_ratio_threshold`: Total used CPU-hours divided by total allocated CPU-hours.

- `email_file`: The text file to be used for the email message to users.

- `mean_ratio_threshold`: (Optional) Mean of the per job ratio of used CPU-hours to allocated CPU-hours. Default: 1

- `median_ratio_threshold`: (Optional) Same as above but for the median instead of the mean. Default: 1

- `min_run_time`: (Optional) Minimum run time of a job in units of minutes. If `min_run_time: 61` then jobs that ran for an hour or less are ignored. Default: 0

- `num_top_users`: (Optional) Only consider the number of users equal to this value after sorting by unused CPU-hours. Default: 10

- `show_all_users`: (Optional) Flag to show all of the top users in the report instead of only the top users with low time efficiency. Default: False

- `num_jobs_display`: (Optional) Number of jobs to display in the email message to users. Default: 10

- `nodelist`: (Optional) Only apply this alert to jobs that ran on the specified nodes. See [example](../nodelist.md).

- `excluded_users`: (Optional) List of usernames to exclude from the alert.

- `admin_emails`: (Optional) List of administrator email addresses that should receive copies of the emails that are sent to users.

- `email_subject`: (Optional) Subject of the email message to users.

- `report_title`: (Optional) Title of the report to system administrators.

## Report for System Administrators

Below is an example report:

```
$ job_defense_shield --excessive-time-cpu

                         Excessive Time Limits                          
-------------------------------------------------------------------------
  User   CPU-Hours  CPU-Hours  Ratio  Ratio   Ratio CPU-Rank Jobs  Emails
          (Unused)    (Used)  Overall  Mean  Median
-------------------------------------------------------------------------
  u18587   495341      13716    0.03   0.03   0.02     10     643   1 (4)
  u81279   105666      80061    0.43   0.43   0.38      2      41   0
  u45521   105509      21595    0.17   0.17   0.13      8     109   2 (1)
  u73275    89469       8475    0.09   0.14   0.09     16      86   0
  u43409    88689     125583    0.59   0.59   0.59      1     279   0
-------------------------------------------------------------------------
   Cluster: della
Partitions: cpu
     Start: Mon Mar 10, 2025 at 06:23 PM
       End: Mon Mar 17, 2025 at 06:23 PM

```

`CPU-Rank` is the rank of the user by used CPU-hours.

## Email Message to Users

Below is an example email (see `email/excessive_time.txt`):

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

Replying to this automated email will open a support ticket with Research
Computing.
```

### Placeholders

The following placeholders can be used in the email file:

- `<GREETING>`: Greeting generated by `greeting-method`.
- `<CLUSTER>`: Name of the cluster.
- `<PARTITIONS>`: A comma-separated list of partitions used by the user.
- `<DAYS>`: Number of days in the time window (default is 7).
- `<MODE-UPPER>`: Equal to "CPU".
- `<AVERAGE>`: Mean of the per-job CPU-hours used divided by CPU-hours allocated.
- `<NUM-JOBS>`: Total number of jobs.
- `<NUM-JOBS-DISPLAY>`: Number of jobs to list in the table.
- `<TABLE>`: Table of job data.
- `<UNUSED-HOURS>`: Total number of unused CPU-hours.

## Usage

Generate a report for system administrators:

```
$ job_defense_shield --excessive-time-cpu
```

Send emails to the offending users:

```
$ job_defense_shield --excessive-time-cpu --email
```

See which users have received emails and when:

```
$ job_defense_shield --excessive-time-cpu --check
```

## cron

Below is an example `crontab` entry:

```
0 9 * * 1-5 /path/to/job_defense_shield --excessive-time-cpu --email > /path/to/log/excessive_time_cpu.log 2>&1
```
