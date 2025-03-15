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
  absolute_thres_hours: 0       # cpu-hours
  mean_ratio_threshold: 100     # [0%, 100%]
  median_ratio_threshold: 100   # [0%, 100%]
  num_top_users: 25
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
-----------------------------------------------------------------------------------
  User    CPU-Hours-Unused  Used  Total  Mean(%)  Median(%)  CPU-Rank  Jobs  Emails
-----------------------------------------------------------------------------------
  jy8587       335001      22293 357296     6         4          6      533 1   (5)
   lfrye        97969      22224 120192    18        13          7      105 2   (9)
  jx1279        96170      72672 168850    43        39          1       38 0      
  sa3275        87511      12711 100224    13        10         11       86 0      
```

This alert works but summing the difference between the time needed and the time allocated for each job of the user. This multiplied by the number of CPU-cores.

Looking at the raw data, we can decide on the threshold values to use for the alert. The following choices look like good starting values:

```yaml
excessive-time-1:
  cluster: della
  partitions:
    - cpu
  absolute_thres_hours: 10000  # cpu-hours
  mean_ratio_threshold: 20     # [0%, 100%]
  median_ratio_threshold: 20   # [0%, 100%]
  num_top_users: 20
```

Only users with more than 10000 unused allocated CPU-hours with a mean and median ratio of used to total time will be emailed. Additionally, at most 20 users will receive the emails.

Let's run the alert again and make sure it is filtering out the right users:

```
no entries
```

## Step 2: Prepare the Email File

Next, look at your email file for this alert:

```
$ cat /path/to/email/excessive_time.txt
```

As you learned on the [Emails](../emails.md) page, you can modify this file just as you would any text file. Special tags can be used for each alert. Next, let's add the `email_file` the alert:

```yaml
excessive-time-1:
  cluster: della
  partitions:
    - cpu
  min_run_time: 61             # minutes
  absolute_thres_hours: 10000  # cpu-hours
  mean_ratio_threshold: 20     # [0%, 100%]
  median_ratio_threshold: 20   # [0%, 100%]
  num_top_users: 5
  num_jobs_display: 10
  email_file: "excessive_time.txt"
  admin_emails:
    - admin@institution.edu
```

We also added a few of the optional settings which are covered in [Excessive Run Time Limits](time_limits.md).

## Step 3: Testing the Emails

Before running the live alert, let's run a test by including `--email` with `--no-emails-to-users`:

```
$ python job_defense_shield.py --excessive-time --email --no-emails-to-users
```

## Step 4: Send the Emails to Users

The command above will send the emails to `admin_emails`. When you are happy withthe settings in `config.yaml` and the email message then run the alert:

```
$ python job_defense_shield.py --excessive-time --email
```

You have been copied on the emails.


## Step 5: Examining the Violation Files

Note that if you run the same command again it will not send any emails. This is because a user can only receive an email for a given alert once per week.

Take a look at the violation files that were written:

```
$ ls -l /path/to/violation/excessive_time/
u12345.csv
u23456.csv
```

!!! warning "Chaning partitions"
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

Finally, add command to crontab:

```
cron
```

Because our alert only needs data for the cpu partition of the della cluster, we used `-M della -r cpu`. This is not necessary but by default the data for all clusters and all partitions is requested from the Slurm database.

To receive a report to `report-emails` add the `--report` flag.

## Performance Tip

If you alerts only needs data for specific clusters and partitions then:

```
$ job_defense_shield --zero-util-gpu-hours --days=7 --clusters=della --partition=gpu,llm --email
```

The `--clusters` and `--partition` options are passed through to `sacct`. This means
that less data is queried saving time. If you do not specify these options then
everything in the Slurm database is retrieved.

You can run multiple alerts at once:

```
$ job_defense_shield --zero-util-gpu-hours --excess-cpu-memory --could-use-mig --days=7 --email
```

Note that multiple alerts are being trigger by a single call to the software.

## Continue by Adding More Alerts

Take a look at the various alerts and add what you like to your configuration file.

- [Automatically Cancel GPU Jobs with 0% Utilization](cancel_gpu_jobs.md)
- [Low GPU Efficiency](low_gpu_util.md)
