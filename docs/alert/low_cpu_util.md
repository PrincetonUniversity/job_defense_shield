# Low CPU Utilization

This alert identifies users with low CPU efficiency.

## Configuration File

Below is an example entry for `config.yaml`:

```yaml
low-cpu-efficiency-1:
  cluster: della
  partitions:
    - cpu
  eff_thres_pct: 60          # percent
  absolute_thres_hours: 100  # cpu-hours
  eff_target_pct: 90         # percent
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

- `email_file`: The file used as a email body. This file must be found in the `email-files-path` setting in `config.yaml`. Learn more about writing custom emails.

- `num_top_users`: After sorting all users by CPU-hours, only consider the top `num_top_users` for all remaining calculations and emails. This is used to limit the number of users that receive emails and appear in reports.

- `min_run_time`: (Optional) The number of minutes that a job must have ran to be considered. This can be used to exclude test jobs and experimental jobs. The default is 0.

- `proportion_thres_pct`: A user must being using this proportion of the total CPU-hours (as a percentage) in order to be sent an email. For example, setting this to 2 will excluded all users that are using less than 2% of the total CPU-hours.

- `excluded_users`: (Optional) List of users to exclude from receiving emails.

- `admin_emails`: (Optional) The emails sent to users will also be sent to these administator emails. This applies
when the `--email` option is used.

!!! info "How is CPU efficiency calculated?"
    The CPU efficiency is weighted by the number of CPU-cores per job. Jobs with 0% utilization on a node are ignored since they are captured by another alert.

## Report for System Administrators

Here is an example report:

```
$ python job_defense_shield.py --low-cpu-efficiency

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

The table lists users from the most CPU-hours to the least. The CPU efficiency is
listed.

## Email Message to Users

Below is an example email message (see `email/low_cpu_efficiency.txt`):

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

- `<GREETING>`: The greeting that will be generated based on the choice of `greeting-method`.
- `<CLUSTER>`: The name of the cluster in the Slurm database.
- `<PARTITIONS>`: A comma-separated list of partitions as defined for the alert in `config.yaml`.
- `<EFFICIENCY>`: Mean efficiency for the user (e.g., 23%).
- `<TARGET>`: Minimum target value for the mean efficiency.
- `<DAYS>`: Number of days in the time window (default is 7 days).
- `<TABLE>`: A table of jobs for the user.
- `<JOBSTATS>`: A line showing how to run the `jobstats` command on one of the jobs of the user. An example is `$ jobstats 1234567`.

## Usage

Generate a report for this alert:

```
$ python job_defense_shield.py --low-cpu-efficiency
```

Same as above but over the past month:

```
$ python job_defense_shield.py --low-cpu-efficiency --days=30
```

Send emails to users with low CPU efficiencies over the past 7 days:

```
$ python job_defense_shield.py --low-cpu-efficiency --email
```

Same as above but only pull data for a specific cluster and partition:

```
$ python job_defense_shield.py --low-cpu-efficiency --email -M traverse -r cpu
```

See which users have received emails and when:

```
$ python job_defense_shield.py --low-cpu-efficiency --check
```

## cron

Below is an example `crontab` entry:

```bash
0 9 * * * /path/to/python /path/to/job_defense_shield.py --low-cpu-efficiency --email > /path/to/log/low_cpu_efficiency.log 2>&1
```

## Related Alerts

See [low GPU utilization](low_gpu_util.md)
