# Emails

## When Are Emails Sent?

Emails to users are most effective when sent sparingly. For this reason, there is a command-line parameter `--days` to specify the amount of time that must pass before the user can receive another email of the same nature.

By default, users can only receive an email for a particular instance of underutilization once per week. The email they receive will contain either the individual jobs or a summary for that week. This time window can be modified by the `--days` option. Note that users can received multiple emails about the same type of underutilization if there are multiple alerts covering different partitions or different clusters.

The `Email` column in the table below shows the number of emails that each user has received about this particular instance of underutilization:

```
                         GPU-Hours at 0% Utilization
---------------------------------------------------------------------
    User   GPU-Hours-At-0%  Jobs             JobID             Emails
---------------------------------------------------------------------
1  u12998        308         39   62285369,62303767,62317153+   1 (3)
2  u9l487         84         14   62301737,62301738,62301742+   0
3  u39635         25          2            62184669,62187323    2 (4)
4  u24074         24         13   62303182,62303183,62303184+   0
---------------------------------------------------------------------
   Cluster: della
Partitions: gpu, llm
     Start: Wed Feb 12, 2025 at 09:50 AM
       End: Wed Feb 19, 2025 at 09:50 AM
```

The number in parentheses is the number of days since the last email was sent. For example, `2 (4)` means that the user has received 2 previous emails with the last one being sent 4 days ago.

## Sending Custom Emails to Users

Each alert requires a text file for the `email_file`:

```yaml
##################################
## ZERO CPU UTILIZATION (ALERT) ##
##################################
zero-cpu-utilization-1:
  cluster: stellar
  partitions:
    - cpu
  email_file: "zero_cpu_utilization.txt"
  admin_emails:
    - admin@institution.edu
```

The location of the `email_file` is set in `config.yaml` by:

```yaml
email-files-path: /path/to/email/
```

Here is an example `email_file`:

```
$ cat /path/to/email/zero_cpu_utilization.txt
<GREETING>

Below are your recent jobs that did not use all of the allocated nodes:

<TABLE>

The CPU utilization was found to be 0% on each of the unused nodes. You can see
this by running the "jobstats" command, for example:

<JOBSTATS>

Please investigate the reason(s) that the code is not using all of the allocated
nodes before running additional jobs.

Replying to this automated email will open a support ticket with Research
Computing.
```

There are three "tags" in the text file above: `<GREETING>`, `<TABLE>` and `<JOBSTATS>`.
Each tag will be replaced by the corresponding value in Python when creating the email. The resulting email will appear as:

```
Hello Alan (u12345),

Below are your recent jobs that did not use all of the allocated nodes:

      JobID    Cluster  Nodes  Nodes-Unused CPU-Util-Unused  Cores  Hours
    62734245    della     4          3             0%          12    2.3 
    62734246    della     6          5             0%          12    2.4 

The CPU utilization was found to be 0% on each of the unused nodes. You can see
this by running the "jobstats" command, for example:

    $ jobstats 62734245

Please investigate the reason(s) that the code is not using all of the allocated
nodes before running additional jobs.

Replying to this automated email will open a support ticket with Research
Computing.
```

Tags can be placed anywhere in your `email_file`. For example, one can include a tag in the middle of a sentence:

```
Below are your jobs on <CLUSTER> that did not use all of the allocated nodes:
```

Each alert has a finite set of tags that may be used to generate custom emails. There are
a set of example email files in the `email` directory of the [GitHub repository](https://github.com/jdh4/job_defense_shield). It is
recommended that you copy these and modify them as you see fit. It might also be a good
idea to put them under version control along with `config.yaml` and `holidays.txt`.

## Testing the Sending of Emails to Users

If `config.yaml` exists, an administrator can see the output of an alert by running it:

```
$ python job_defense_shield.py --low-gpu-efficiency
```

One adds the `--email` flag to send emails to users:

```
$ python job_defense_shield.py --low-gpu-efficiency --email

```

For testing, one can add a second flag that will only send the emails to `admin_emails` and not the users:

```
$ python job_defense_shield.py --low-gpu-efficiency --email --no-emails-to-users
```

The `--no-emails-to-users` will also prevent violation log files from being updated. This allows administrators to test and modify the email messages as well as tune the threshold values in `config.yaml` without involving the users.

There is one alert that requires one extra step, which is [Cancel 0% GPU Jobs](alert/cancel_gpu_jobs.md). In this case, one should add the following to the alert definition:

```yaml
  do_not_cancel: True
```
