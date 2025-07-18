# Low CPU Utilization

This alert identifies users with low CPU efficiency.

## Configuration File

Below is an example entry for `config.yaml`:

```yaml
low-cpu-efficiency-1:
  cluster: della
  partitions:
    - cpu
  eff_thres_pct:         60  # percent
  absolute_thres_hours: 100  # cpu-hours
  eff_target_pct:        90  # percent
  num_top_users:         15  # count
  email_file: "low_cpu_efficiency.txt"
  admin_emails:
    - admin@institution.edu
```

The parameters are explained below:

- `cluster`: Specify the cluster name as it appears in the Slurm database. One cluster name
per alert.

- `partitions`: Specify one or more Slurm partitions.

- `eff_thres_pct`: Efficiency threshold percentage. Users with a `eff_thres_pct` os less than or equal to this value will receive an email. plus more

- `absolute_thres_hours`: A user must have used more than this number of CPU-hours to be considered to receive an email.

- `eff_target_pct`: The target value for CPU utilization that users should strive for. It is only used in emails. This value can be referenced as the tag `<TARGET>` in email messages (see `low_cpu_efficiency.txt`).

- `email_file`: The text file to be used as the email message to users.

- `num_top_users`: (Optional) After sorting all users by CPU-hours, only consider this number of users for all remaining calculations and emails. This is used to limit the number of users that receive emails and appear in reports. Default: 15

- `show_all_users`: (Optional) Flag to show all of the top users in the report instead of only the top users with low efficiency. Default: False

- `min_run_time`: (Optional) Minimum run time of a job in units of minutes. If `min_run_time: 61` then jobs that ran for an hour or less are ignored. Default: 0

- `proportion_thres_pct`: (Optional) Proportional threshold percentage. A user must being using at least this proportion of the total CPU-hours (as a percentage) in order to be sent an email. For example, setting this to 2 will excluded all users that are using less than 2% of the total CPU-hours. Default: 0

- `nodelist`: (Optional) Only apply this alert to jobs that ran on the specified nodes. See [example](../nodelist.md).

- `excluded_users`: (Optional) List of users to exclude from receiving emails.

- `admin_emails`: (Optional) List of administrator email addresses that should receive copies of the emails that are sent to users.

- `email_subject`: (Optional) Subject of the email message to users.

- `report_title`: (Optional) Title of the report to system administrators.

!!! info "How is CPU efficiency calculated?"
    The CPU efficiency is weighted by the number of CPU-cores per job. Jobs with 0% utilization on a node are ignored since they are captured by another alert.

## Report for System Administrators

Below is an example report:

```
$ job_defense_shield --low-cpu-efficiency

                     Low CPU Efficiencies                                  
-----------------------------------------------------------------
 User   CPU-Hours  Proportion(%)  CPU-Eff  Jobs  AvgCores  Emails
-----------------------------------------------------------------
u12345    16377         4           58%     998    15.8     0   
u85632    12536         3           14%    1034    16.3     2 (6)   
u39731    10227         2           50%    2477     2.0     0   
-----------------------------------------------------------------
   Cluster: della
Partitions: cpu
     Start: Wed Mar 12, 2025 at 02:05 PM
       End: Wed Mar 19, 2025 at 02:05 PM
```

## Email Message to Users

Below is an example email (see `email/low_cpu_efficiency.txt`):

```
Hello Alan (u12345),

Over the last 7 days you have used the 3rd most CPU-hours on della (cpu) but
your mean CPU efficiency is only 23%:

     User  Partition(s)  Jobs  CPU-Hours CPU-Rank Efficiency AvgCores
    u12345     cpu        33     29062     3/250      23%       8    

A good target value for "Efficiency" is 90% and above. Please investigate the reason
for the low efficiency. Common reasons for low CPU efficiency are discussed here:

    https://your-institution.edu/KB/cpu-utilization

Replying to this automated email will open a support ticket with Research
Computing.
```

### Placeholders

The following placeholders can be used in the email file:

- `<GREETING>`: Greeting generated by `greeting-method`.
- `<CLUSTER>`: The name of the cluster.
- `<PARTITIONS>`: A comma-separated list of partitions used by the user.
- `<DAYS>`: Number of days in the time window (default is 7 days).
- `<EFFICIENCY>`: Mean CPU efficiency of the user (e.g., 23%).
- `<TARGET>`: Target value for the mean CPU efficiency.
- `<TABLE>`: A table of jobs for the user.
- `<JOBSTATS>`: The `jobstats` command for the first job of the user.

## Usage

Generate a report for system administrators:

```
$ job_defense_shield --low-cpu-efficiency
```

Send emails to the offending users:

```
$ job_defense_shield --low-cpu-efficiency --email
```

See which users have received emails and when:

```
$ job_defense_shield --low-cpu-efficiency --check
```

## cron

Below is an example `crontab` entry:

```
0 9 * * * /path/to/job_defense_shield --low-cpu-efficiency --email > /path/to/log/low_cpu_efficiency.log 2>&1
```
