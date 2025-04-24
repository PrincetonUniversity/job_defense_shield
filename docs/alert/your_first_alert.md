# Your First Alert

Here we demonstrate how to set up an alert that sends emails to users for excessive run time limits (e.g., requesting 3 days but only using 3 hours).

## Step 1: Add the Alert to the Configuration File

Add the following to your `config.yaml` with the appropriate changes to `cluster` and `partitions`:

```yaml
###############################
## EXCESSIVE RUN TIME LIMITS ##
###############################
excessive-time-cpu-1:
  cluster: della
  partitions:
    - cpu
  absolute_thres_hours:      0  # unused cpu-hours
  overall_ratio_threshold: 1.0  # [0.0, 1.0]
  num_top_users:            10  # count
```

!!! note
    One cluster per alert. Use multiple alerts for multiple clusters. Multiple partitions per alert is fine. See `example.yaml` in the [GitHub repository](https://github.com/PrincetonUniversity/job_defense_shield) to see this in practice.

Multiple partitions can be entered as a YAML list:

```yaml
  partitions:
    - cpu
    - bigmem
    - serial
```

Next, run the alert without `--email` so that no emails are sent but the output is displayed in the terminal:

```
$ job_defense_shield --excessive-time-cpu

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

CPU-Hours (Unused) is the product of the number of CPU-cores and run time limit minus the elapsed time (summed over all jobs). The table is sorted by this quantity. Ratio Overall is CPU-Hours (Used) divided by CPU-Hours (unused) plus CPU-Hours (used). CPU-Rank is the rank of the user by CPU-Hours (used). The user that has consumed the most CPU-hours has a rank of 1.

Looking at the data in the table above, we can decide on the threshold values to use for the alert. The following choices look like good starting values:

```yaml
excessive-time-cpu-1:
  cluster: della
  partitions:
    - cpu
  absolute_thres_hours: 100000  # unused cpu-hours
  overall_ratio_threshold: 0.2  # [0.0, 1.0]
  num_top_users:            10  # count
```

The settings above will only include users that have more than 100,000 unused (allocated) CPU-hours and a ratio of used to total of 0.2 or less.

Let's run the alert again to check the filtering:

```
$ job_defense_shield --excessive-time-cpu

                        Excessive Time Limits
----------------------------------------------------------------------
 User  CPU-Hours  CPU-Hours  Ratio  Ratio   Ratio CPU-Rank Jobs Emails
        (Unused)    (Used)  Overall  Mean  Median                     
----------------------------------------------------------------------
u18587   497596     13765     0.03   0.03   0.02     10    644    0   
u45521   105509     21595     0.17   0.17   0.13      8    109    0   
----------------------------------------------------------------------
   Cluster: della
Partitions: cpu
     Start: Mon Mar 10, 2025 at 06:35 PM
       End: Mon Mar 17, 2025 at 06:35 PM
```

This looks good. Only two users will receive an email.

## Step 2: Prepare the Email File

Next, look at your email file for this alert:

```
$ cat /path/to/email/excessive_time.txt
```

As you learned in the [Emails](../emails.md) section, you can modify this file just as you would any text file. Special tags can be used for each alert.

Next, let's add the `email_file` to the alert entry:

```yaml
excessive-time-cpu-1:
  cluster: della
  partitions:
    - cpu
  min_run_time:             61  # minutes
  absolute_thres_hours: 100000  # unused cpu-hours
  overall_ratio_threshold: 0.2  # [0.0, 1.0]
  num_top_users:            10  # count
  num_jobs_display:         10  # count
  email_file: "excessive_time.txt"
  admin_emails:
    - admin@institution.edu
```

We also added a few of the optional settings which are covered in [Excessive Run Time Limits](time_limits.md).

Make sure you set `email-files-path` in the global settings of `config.yaml` to the directory containing `excessive_time.txt`

## Step 3: Testing the Emails

Let's run a test by adding the `--email` flag with the `--no-emails-to-users` modifier:

```
$ job_defense_shield --excessive-time-cpu --email --no-emails-to-users
```

The command above will only send emails to the addresses in `admin_emails`. Users will not receive emails. Make changes to your email message and then run the test again to see the new version.

## Step 4: Send the Emails to Users

When you are satisfied with the settings in `config.yaml` and the email message, run the alert with only `--email` to send emails to the offending users:

```
$ job_defense_shield --excessive-time-cpu --email
```

Once again, those listed in `admin_emails` will receive copies of the emails.

## Step 5: Examining the Violation Files

Note that if you run the same command again it will not send any emails. This is because a user can only receive an email for a given alert once per week (by default).

Take a look at the violation files that were written (with the path set by `violation-logs-path`):

```
$ ls /path/to/violations/excessive_time_limits_cpu/
u18587.csv
u45521.csv

$ cat /path/to/violations/excessive_time_limits_cpu/u18587.csv
User,Cluster,Alert-Partitions,CPU-Hours-Unused,Jobs,Email-Sent
u18587,della,cpu,497596,644,03/17/2025 18:35:58
```

The violation file of a user is read when determining whether or not sufficient time has passed to send another email. This is the purpose of the `Email-Sent` column. The software is written so that users receive at most one email about any given job.

!!! warning "Changing partitions"
    When deciding if a user should receive an email, the software first filters the violation file by `Cluster` and `Alert-Partitions`. `Alert-Partitions` is a comma-seperated string of the list of partitions. If you add or remove a partition to an alert this will change `Alert-Partitions` which may cause the user to receive a second email in less than seven days. After adding or removing a partition, it is best to turn the alert off for a week to avoid this.

## Step 6: Add Additional Alerts

Add as many alerts to the configuration file as you need to cover your partitions and clusters. Be sure to give them different names:

```yaml
excessive-time-cpu-1:
  cluster: della
  ...

excessive-time-cpu-2:
  cluster: stellar
  ...
```

## Step 7: Update `crontab`

Finally, add the appropriate entry to crontab. Something like:

```
0 9 * * 1-5 /path/to/job_defense_shield --excessive-time-cpu --email -M della -r cpu > /path/to/log/excessive_time.log 2>&1
```

The `--excessive-time-cpu` flag will trigger all of the alerts of type `excessive-time-cpu`.

Because our alert only needs data for the `cpu` partition of the `della` cluster, we used `-M della -r cpu`. This is not necessary but by default the data for all clusters and all partitions is requested from the Slurm database.

To have a report sent to the addresses in `report-emails`, add the `--report` flag.

## Continue by Adding More Alerts

Take a look at the various alerts and add what you like to your configuration file. Here are three popular ones:

- [Automatically Cancel GPU Jobs with 0% Utilization](cancel_gpu_jobs.md)
- [GPU-Hours at 0% Utilization](zero_gpu_util.md)
- [Low GPU Efficiency](low_gpu_util.md)

## How does Job Defense Shield work?

Summary statistics for each completed job are stored in a compressed format in the `AdminComment` field in the Slurm database. The software described here works by calling the Slurm `sacct` command while requesting several fields including `AdminComment`. The `sacct` output is stored in a `pandas` dataframe for processing. To get the data for running jobs, the Prometheus database is queried.
