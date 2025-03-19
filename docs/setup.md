# Installation

We assume that the [Jobstats platform](https://github.com/PrincetonUniversity/jobstats) is available and working.

!!! info "Cancelling Jobs at 0% GPU Utilization"
    To automatically cancel actively running jobs, the software must be ran as a user with sufficient privileges to call `scancel`. This may inform your decision of where to install the software. All of the other alerts can be ran as a regular user.

The installation requirements for Job Defense Shield are `pandas` and `pyyaml`. The `requests` module is needed only if one wants to address the underutilization of actively running jobs. In this case, the Prometheus server must be queried.

Python 3.6+ and pandas 1.2+ are the minimum required versions. We recommend using newer versions such as Python 3.10+ and pandas 2.1+.

Here are some ways the requirements can be installed:

=== "Ubuntu"

    ```bash
    $ apt-get install python3-pandas python3-yaml python3-requests
    ```

=== "conda"

    ```bash
    $ conda create --name jds-env pandas pyarrow pyyaml requests -c conda-forge
    $ conda activate jds-env
    ```

=== "pip"

    ```bash
    $ python3 -m venv jds-env
    $ source jds-env/bin/activate
    (jds-env) $ pip3 install pandas pyarrow pyyaml requests
    ``` 

Next, pull down the repository:

```
$ git clone https://github.com/PrincetonUniversity/job_defense_shield
$ cd job_defense_shield
```

## Testing the Installation

The simplest test is to run the help menu:

```
$ python job_defense_shield.py --help
```

Try running a simple informational alert. First, make a trivial configuration file called `config.yaml` in the same directory as `job_defense_shield.py`:

```
$ cat config.yaml
```
```yaml
%YAML 1.1
---
#####################
## GLOBAL SETTINGS ##
#####################
jobstats-module-path: /tmp
violation-logs-path: /tmp
email-files-path: /tmp
email-domain-name: "@institution.edu"
sender: support@institution.edu
reply-to: support@institution.edu
report-emails:
  - admin@institution.edu
```

!!! tip
    If the path that you use for `violation-logs-path` does not exist then the software will try to make it. If `/tmp` does not exist then use something else like `/scratch`.

Be sure to replace `email-domain-name`, `sender`, `reply-to` and `report-emails` with your values.

To test the software, run this command (which does not send any emails):

```
$ python job_defense_shield.py --utilization-overview
```

The command above will show an overview of the number of CPU-hours and GPU-hours
across all clusters and partitions in the Slurm database over the past 7 days.

Here is an example output:

```
$ python job_defense_shield.py --utilization-overview

           Utilization Overview          
-----------------------------------------
cluster   users   cpu-hours    gpu-hours 
-----------------------------------------
   della  464   1285938 (16%) 91714 (65%)
 stellar  149   6745324 (82%)  1926  (1%)
traverse    1    189987  (2%) 47497 (34%)
-----------------------------------------



          Utilization Overview by Partition           
------------------------------------------------------
cluster  partition   users   cpu-hours     gpu-hours  
------------------------------------------------------
   della        cpu  311    874114  (68%)     0   (0%)
   della      pli-c   28    115406   (9%) 25838  (28%)
   della gpu-shared   98     83617   (7%) 30083  (33%)
   della    datasci   31     80954   (6%)     0   (0%)
   della        gpu   51     47475   (4%) 16503  (18%)
   della        pli   20     35814   (3%)  6249   (7%)
   della     cryoem   17     20897   (2%)  4110   (4%)
   della    physics    5     12968   (1%)     0   (0%)
   della        mig   41      7169   (1%)  7169   (8%)
   della     pli-lc    5      3107   (0%)  1081   (1%)
   della    gputest   99      1948   (0%)   647   (1%)
   della        all    1      1280   (0%)     0   (0%)
   della      donia    4      1003   (0%)     0   (0%)
   della     gpu-ee    2       173   (0%)    23   (0%)
   della      grace    1        11   (0%)    11   (0%)
   della      malik    1         2   (0%)     0   (0%)
 stellar      cimes   21   2941001  (44%)     0   (0%)
 stellar         pu   56   2426873  (36%)     0   (0%)
 stellar       pppl   33   1340776  (20%)     0   (0%)
 stellar     serial   41     13187   (0%)     0   (0%)
 stellar        all   48     12377   (0%)     0   (0%)
 stellar        gpu   20     11044   (0%)  1926 (100%)
 stellar     bigmem    1        66   (0%)     0   (0%)
traverse        all    1    189987 (100%) 47497 (100%)
------------------------------------------------------
     Start: Fri Mar 07, 2025 at 11:27 AM
       End: Fri Mar 14, 2025 at 11:27 AM
```

You can go further back in time by using the `--days` option:

```
$ python job_defense_shield.py --utilization-overview --days=14
```

!!! info
    Using a large value for the `--days` option can cause the Slurm database to fail to produce the data. The default is 7 days.

One can only include data from specific clusters or partitions using the `-M` and `-r` options from `sacct`:

```
$ python job_defense_shield.py --utilization-overview -M della -r cpu,gpu
```
Or equivalently:

```
$ python job_defense_shield.py --utilization-overview --clusters=della --partition=cpu,gpu
```

The `-M` and `-r` options (or `--clusters` and `--partition`) can be used to reduce the load on the database server when an alert only applies to a particular cluster or particular partitions. These options are passed through to `sacct`. See `man sacct` for more information.

## Email Test

By having your email address in `report-emails` in `config.yaml`, the `--report` flag can be used to send the output to administrators by email:

```
$ python job_defense_shield.py --utilization-overview --report
```

This feature is useful when combined with `cron`. That is, one can receive a daily report showing all of the instances of underutilization across all of the systems. This is shown later.

## Troubleshooting the Installation

Make sure you are using the right `python`. All three commands below should run successfully:

```
$ python -c "import sys; print(sys.version)"
$ python -c "import pandas; print(pandas.__version__)"
$ python -c "import pyyaml; print(pyyaml.__version__)"
```

If the configuration file is not found then try specifying the full path:

```
$ python job_defense_shield.py --config-file=/path/to/config.yaml --utilization-overview --report
```
 
## Creating a Configuration File for Production

See the [next section](configuration.md) to learn how to write a proper configuration file.
