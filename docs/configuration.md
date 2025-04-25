# Configuration

Job Defense Shield is configured using a YAML file, which specifies global settings as well as the individual alerts to run.

Below is a minimal configuration file (`config.yaml`) with one alert:

```yaml
%YAML 1.1
---
#####################
## GLOBAL SETTINGS ##
#####################
jobstats-module-path: /path/to/jobstats/module/
jobstats-config-path: /path/to/jobstats/config/
violation-logs-path:  /path/to/violations/
email-files-path:     /path/to/email/
email-domain-name: "@institution.edu"
sender:   support@institution.edu
reply-to: support@institution.edu
greeting-method: getent
workday-method: file
holidays-file: /path/to/holidays.txt
report-emails:
  - admin1@institution.edu
  - admin2@institution.edu


##################################
## ZERO CPU UTILIZATION (ALERT) ##
##################################
zero-cpu-utilization-1:
  cluster: stellar
  partitions:
    - cpu
    - bigmem
  min_run_time: 61 # minutes
  email_file: "zero_cpu_utilization.txt"
  admin_emails:
    - job-alerts-aaaalegbihhpknikkw2fkdx6gi@institution.slack.com
    - admin@institution.edu
```

Each line of the global settings is explained below. See [example.yaml](https://github.com/jdh4/job_defense_shield/blob/main/example.yaml) in the GitHub repository for a full configuration file example.

## Global Settings

### Jobstats Module and Config Paths

These paths are only needed for addressing the underutilization of actively running jobs:

```yaml
jobstats-module-path: /path/to/jobstats/module/  # jobstats.py
jobstats-config-path: /path/to/jobstats/config/  # config.py
```

If you are only interested in completed jobs then you do not need this feature. In this case, remove these lines from `config.yaml`.

Here is an example for a particular system:

```yaml
jobstats-module-path: /usr/local/jobstats/
jobstats-config-path: /etc/jobstats/
```

The value of `PROM_SERVER` is taken from `config.py`.

### Violation Logs

One must specify the path to a writable directory to store the underutilization history of each user:

```yaml
violation-logs-path: /path/to/violations/
```

If the path does not exist then the software will try to make it.

The files stored in this directory are read when deciding whether or not sufficient time has passed to send the user another email. These files are important and we recommend maintaining a backup.

### Email Settings

Set the path to your email files. A set of example files is found in the `email` directory of the `job_defense_shield` GitHub repository. It is recommended to copy the example email files to another directory outside of `job_defense_shield` and put that under version control. As you will learn, placeholders like `<GREETING>` are replaced by the actual values as computed in the Python code.

```yaml
email-files-path: /path/to/email/
```

Specify the email domain for your institution:

```yaml
email-domain-name: "@institution.edu"
```

Usernames will be concatenated with the email domain to make user email addresses.

Specify the `sender` and `reply-to` values for sending emails:

```yaml
sender: support@institution.edu
reply-to: support@institution.edu
```

!!! tip
    By using a `reply-to` that is different from `sender`, one can prevent auto-reply or out-of-office emails from creating new support tickets.

Use the `greeting-method` to determine the first line of the email that users receive:

```yaml
greeting-method: getent
```

The `getent` method will call `getent passwd` on the username to find the first name of the user in producing a greeting such as:

```
Hello Alan (u12345),
```

A choice of `basic` will produce:

```
Hello u12345,
```

There is also `ldap` which calls `ldapsearch`. Our recommendation is `getent`. If you find that `getent` is not working properly during testing then use `basic`.

Lastly, one can create multiple reports and have those sent to administrators by email when the `--report` flag is used:

```yaml
report-emails:
  - admin1@institution.edu
  - admin2@institution.edu
```

### Workdays

Email alerts are only sent to users on workdays. Pick a method to distinguish the workdays from weekends and holidays. The most flexible method is `file`:

```yaml
workday-method: file
holidays-file: /path/to/holidays.txt
```

The file `holidays.txt` should be a list of dates with the format YYYY-MM-DD:

```
$ cat holidays.txt
2025-05-26
2025-06-19
2025-07-04
```

If you only want to avoid weekends and U.S. Federal holidays then use:

```yaml
workday-method: usa
```

If every day is a workday then:

```yaml
workday-method: always
```

The `cron` setting can be used to avoid weekends so really this section is about dealing with holidays.

### Other Settings

Partition names can be renamed:

```yaml
partition-renamings:
  datascience: datasci
```

If a partition is renamed then the new name must be used throughout the configuration file.

For users that do not use their institutional email address, one can specify external addresses:

```yaml
external-emails:
  u12345: alan.turing@gmail.com
  u23456: einstein@yahoo.com
```

## Specifying a Custom Configuration File

By default the software will look for `config.yaml` in the same directory as `job_defense_shield.py`. One can override this behavior by using the `--config-file` option:

```
$ job_defense_shield --config-file=/path/to/myconfig.yaml --low-gpu-efficiency
```

The ability to use different configuration files provides additional flexibility. For instance, for some institutions it may make sense to have a different configuration file for each cluster or for different alerts.

## Each Alert Must Have a Different Name

Consider the following two alerts (pay attention to the alert names):

```yaml
zero-cpu-utilization-1:
  cluster: stellar
  partitions:
    - cpu
  email_file: "zero_cpu_utilization.txt"
  admin_emails:
    - admin@institution.edu

zero-cpu-utilization-1:
  cluster: della
  partitions:
    - physics
  email_file: "zero_cpu_utilization.txt"
  admin_emails:
    - admin@institution.edu
```

While the two alerts above are written for different clusters, only the second one will run since both alerts have the same name (`zero-cpu-utilization-1`).

!!! warning

    Make sure each alert name has a different number at the end. An alert with the same name as one previously defined will override the previous alert.

The corrected version would be:

```yaml
zero-cpu-utilization-1:
  cluster: stellar
  partitions:
    - cpu
  email_file: "zero_cpu_utilization.txt"
  admin_emails:
    - admin@institution.edu

zero-cpu-utilization-2:
  cluster: della      
  partitions:
    - physics
  email_file: "zero_cpu_utilization.txt"
  admin_emails:
    - admin@institution.edu
```

The second alert now has the name `zero-cpu-utilization-2`.

## Include or Fully Remove a Setting

There are many optional settings for each alert. If you do not want to use an optional setting then fully remove the line.

The following is **incorrect** for `min_run_time`:

```yaml
zero-cpu-utilization-1:
  cluster: stellar
  partitions:
    - cpu
  min_run_time:
  email_file: "zero_cpu_utilization.txt"
  admin_emails:
    - admin@institution.edu
```

If the default value for `min_run_time` should be used then completely remove the line. Here is the **corrected** entry:

```yaml
zero-cpu-utilization-1:
  cluster: stellar
  partitions:
    - cpu
  email_file: "zero_cpu_utilization.txt"
  admin_emails:
    - admin@institution.edu
```

Another **correct** way is to specify the value:

```yaml
zero-cpu-utilization-1:
  cluster: stellar
  partitions:
    - cpu
  min_run_time: 0  # minutes
  email_file: "zero_cpu_utilization.txt"
  admin_emails:
    - admin@institution.edu
```

## Full Example Configuration File

For more examples see [example.yaml](https://github.com/jdh4/job_defense_shield/blob/main/example.yaml) in the GitHub repository.

## Writing and Testing Custom Emails

See the [next section](emails.md) to learn about sending custom emails to your users.
