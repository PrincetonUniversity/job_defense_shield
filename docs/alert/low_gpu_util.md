# Low GPU Utilization

This alert finds jobs with low GPU utilization. It ignores jobs with GPUs at
0% utilization since the zero GPU utiliation alert catching those cases.

This alert is important because it enables system administrators to identify users on the cluster that are using a large amounts of GPU-hours at low utilization.

Here is an example of the report:

```
$ python job_defense_shield.py --low-gpu-efficiency

                                       Low GPU Efficiencies                                      
-------------------------------------------------------------------------------------------------
    user  cluster partition  gpu-hours  proportion(%)  eff(%)  jobs  interactive  cores  coverage
-------------------------------------------------------------------------------------------------
1  u76174   della     gpu      3791          20          29     58        0        1.2      1.0  
3  u64732   della     gpu      3201          17          50     43        0        1.0      1.0  
4  u13301   della     gpu      2281          12          43     35        0        8.0      1.0  
```


The table lists users from the most GPU-hours to the least. The GPU efficiency is
listed.

## Configuration File

Below is an example entry for `config.yaml`:

Minimal configuration for generating reports only (not sending emails to users):

```yaml
low-gpu-efficiency-1:
  cluster: della
  partitions:
    - gpu
```

This configuration can be used for reports and sending emails:


```yaml
low-gpu-efficiency-1:
  cluster: della
  partitions:
    - gpu
  eff_thres_pct: 15         # percent
  absolute_thres_hours: 50  # gpu-hours
  eff_target_pct: 50        # percent
  email_file: "email/low_gpu_efficiency.txt"
  admin_emails:
    - admin@university.edu
    - admin@princeton.edu
    - sysadmin@princeton.edu
```

The parameters are explained below:

- `cluster`: Specify the cluster name as it appears in the Slurm database. One cluster name
per alert. Use multiple `zero-util-gpu-hours` alerts for multiple clusters.

- `partitions`: Specify one or more Slurm partitions. The number of GPU-hours is summed over all partitions. It most cases it is better to create a separate alert for each partition.

- `eff_thres_pct`: Efficiency threshold percentage. Users with a `eff_thres_pct` os less than or equal to this value will receive an email. plus more

- `absolute_thres_hours`: A user must have allocated more than this number of GPU-hours to be considered to receive an email.

- `eff_target_pct`: The target value for GPU utilization that users should strive for. It is only used in emails. This value can be referenced as the tag `<TARGET>` in email messages (see `email/low_gpu_efficiencies.txt`).

- `email_file`: The file used as a email body. This file must be found in the `email-files-path` setting in `config.yaml`. Learn more about writing custom emails.

Below is a full set of parameters:

```yaml
low-gpu-efficiency-1:
  cluster: della
  partitions:
    - gpu
  eff_thres_pct: 15         # percent
  proportion_thres_pct: 2   # percent
  absolute_thres_hours: 50  # gpu-hours
  eff_target_pct: 50        # percent
  num_top_users: 15         # count
  min_run_time: 30          # minutes
  email_file: "email/low_gpu_efficiency.txt"
  excluded_users:
    - aturing
    - einstein
  admin_emails:
    - alerts-jobs-aaaalegbihhpknikkw2fkdx6gi@princetonrc.slack.com
    - halverson@princeton.edu
    - msbc@princeton.edu
```

- `num_top_users`: After sorting all users by GPU-hours, only consider the top `num_top_users` for all remaining calculations and emails. This is used to limit the number of users that receive emails and appear in reports.

- `min_run_time`: (Optional) The number of minutes that a job must have ran to be considered. This can be used to exclude test jobs and experimental jobs. The default is 0.

- `proportion_thres_pct`: A user must being using this proportion of the total GPU-hours (as a percentage) in order to be sent an email. For example, setting this to 2 will excluded all users that are using less than 2% of the total GPU-hours.

- `excluded_users`: (Optional) List of users to exclude from receiving emails. These users will still appear
in reports for system administrators when `--report` is used.

- `user_emails_bcc`: (Optional) The emails sent to users will also be sent to these administator emails. This applies
when the `--email` option is used.

- `report_emails`: (Optional) Reports will be sent to these administator emails. This applies
when the `--report` option is used.

## How to Write the Email File

Below is the email message that is generated by the template in `email/low_gpu_efficiencies.txt`:

```
Dear Alan,

You have a loew gpu efficy.
```

You can modified the file as you like. The tags that can be used in the email message are:

- `<GREETING>`: The greeting that will be generated based on the choice of `greeting_method` in `config.yaml`. An example is "Hello Alan (aturing),".
- `<CLUSTER>`: The name of the cluster as defined in `config.yaml`.
- `<PARTITIONS>`: A comma-separated list of partitions as defined for the alert in `config.yaml`.
- `<TABLE>`: A table of jobs for the user.
- `<JOBSTATS>`: A line showing how to run the `jobstats` command on one of the jobs of the user. An example is `$ jobstats 1234567`.

## Usage

Generate a report of the top users are their GPU efficiencies:

```
$ python job_defense_shield.py --low-gpu-efficiencies
```

Same as above but over the past month:

```
$ python job_defense_shield.py --low-gpu-efficiencies --days=30
```

Send emails to users with low GPU efficiencies over the past 7 days:

```
$ python job_defense_shield.py --low-gpu-efficiencies --email
```

Same as above but only pull data for a specific cluster and partition:

```
$ python job_defense_shield.py --low-gpu-efficiencies --email -M traverse -r gpu
```


## cron

It is recommended to run this alert with a time window of 7 days:

```bash
PY=/home/sysadmin/.conda/envs/jds-env/bin
JDS=/homem/sysadmin/bin/job_defense_shield
MYLOG=${JDS}/log

0 9 * * * ${PY}/python ${JDS}/job_defense_shield.py --low-gpu-efficiencices --email > ${MYLOG}/low_gpu_efficiencies.log 2>&1
```

## Troubleshooting

You must have a `low-gpu-efficiencies` entry in `config.yaml` for this alert to work.

## Related Alerts

See [low CPU utilization](low_cpu_util.md)
