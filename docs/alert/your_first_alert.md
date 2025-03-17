# Your First Alert

Here we demonstrate how to setup an alert that sends emails to users for excessive run time limits (e.g., requesting 3 days but only using 3 hours).

## Step 1: Add the Alert to the Configuration File

First, add the following to your `config.yaml` with the appropriate changes to `cluster` and `partiions`:

```yaml
########################
## EXCESS TIME LIMITS ##
########################
excessive-time-1:
  cluster: della
  partitions:
    - cpu
  absolute_thres_hours: 0       # unused cpu-hours
  overall_ratio_threshold: 1.0  # [0.0, 1.0]
  num_top_users: 10
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

CPU-Hours (Unused) is the product of the number of CPU-cores and run time limit minus the elapsed time (summed over all jobs). The table is sorted by this quantity. Ratio Overall is CPU-Hours (Used) divided by CPU-Hours (unused) plus CPU-Hours (used). CPU-Rank is the rank of the user by CPU-Hours (used). The user that has consumed the most CPU-hours has a rank of 1.

Looking at the data in the table above, we can decide on the threshold values to use for the alert. The following choices look like good starting values:

```yaml
excessive-time-1:
  cluster: della
  partitions:
    - cpu
  absolute_thres_hours: 100000  # cpu-hours
  overall_ratio_threshold: 0.2  # [0.0, 1.0]
  num_top_users: 10
```

The settings above will only include users that have more than 100,000 unused (allocated) CPU-hours and a ratio of used to total of 0.2 or less.

Let's run the alert again to check the filtering:

```
$ python job_defense_shield.py --excessive-time

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


Next, let's add the `email_file` to the alert:

```yaml
excessive-time-1:
  cluster: della
  partitions:
    - cpu
  min_run_time: 61              # minutes
  absolute_thres_hours: 100000  # unused cpu-hours
  overall_ratio_threshold: 0.2  # [0.0, 1.0]
  num_top_users: 10 
  num_jobs_display: 10
  email_file: "excessive_time.txt"
  admin_emails:
    - admin@institution.edu
```

We also added a few of the optional settings which are covered in [Excessive Run Time Limits](time_limits.md). If you are wondering about GPU partitions, one can use `mode: gpu` to do the same for GPU-hours.

Make sure you set `email-files-path` in the global settings of `config.yaml` to the directory containing `excessive_time.txt`

## Step 3: Testing the Emails

Before running the live alert, let's run a test by including `--email` with `--no-emails-to-users`:

```
$ python job_defense_shield.py --excessive-time --email --no-emails-to-users
```

The command above will only send emails to the addresses in `admin_emails`.

## Step 4: Send the Emails to Users

When you are happy with the settings in `config.yaml` and the email message, run the alert to send emails to the offending users:

```
$ python job_defense_shield.py --excessive-time --email
```

Once again, those in `admin_emails` will receive copies of the emails.

## Step 5: Examining the Violation Files

Note that if you run the same command again it will not send any emails. This is because a user can only receive an email for a given alert once per week.

Take a look at the violation files that were written:

```
$ ls /path/to/violations/excessive_time_limits/
u18587.csv
u45521.csv
```

!!! warning "Changing partitions"
    When deciding if a user should receive an email, the software first filters the violation file by `Cluster` and `Alert-Partitions`. If you add or remove a partition to an alert this will change `Alert-Partitions` which may cause the user to receive a second email in less than seven days. After adding or removing a partition, it is best to turn the alert off for a week to avoid this.

## Step 6: Add Additional Alerts

Add as many alerts to the configuration file as you need to cover your partitions and clusters. Be sure to give them different names:

```yaml
excessive-time-1:
  cluster: della
  ...

excessive-time-2:
  cluster: stellar
  ...
```

## Step 7: Update `crontab`

Finally, add the appropriate command to crontab. Something like:

```
0  9 * * 1-5 /path/to/python path/to/job_defense_shield.py --excessive-time --email -M della -r cpu > /path/to/log/excessive_time.log 2>&1
```

Because our alert only needs data for the `cpu` partition of the `della` cluster, we used `-M della -r cpu`. This is not necessary but by default the data for all clusters and all partitions is requested from the Slurm database.

To receive a report to `report-emails` add the `--report` flag.

## Continue by Adding More Alerts

Take a look at the various alerts and add what you like to your configuration file.

- [Automatically Cancel GPU Jobs with 0% Utilization](cancel_gpu_jobs.md)
- [Low GPU Efficiency](low_gpu_util.md)
