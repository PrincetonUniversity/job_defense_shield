# High GPU Utilization but Low SM Utilization

This alert identifies users whose jobs exhibit high GPU utilization but low SM (Streaming Multiprocessor) utilization.

GPU utilization is the percentage of time, over a sampling interval, that at least one kernel is executing on the GPU. This quantity is independent of the number of threads or GPU cores being used. Consequently, GPU utilization can be high even when only a small fraction of the GPU's computational resources are being utilized.

SM utilization is the percentage of time that the Streaming Multiprocessors are actively executing one or more warps. A warp is a group of 32 threads that execute the same instruction in a SIMT (Single Instruction, Multiple Threads) fashion.

For reference, an NVIDIA B200 GPU has 148 active SMs, each containing 128 FP32 CUDA cores. SM utilization provides a more fine-grained view of GPU activity than overall GPU utilization. When a workload makes effective use of the GPU's computational resources, both GPU utilization and SM utilization are generally high.

Occupancy is a third quantity that provides additional insight into GPU utilization. It is the ratio of the number of active warps on an SM to the maximum number of warps that the SM can support. Occupancy is typically expressed as a percentage.

High occupancy allows an SM to have more warps available for execution, helping hide instruction and memory latency. Low occupancy can limit the GPU's ability to keep its execution resources busy. However, high occupancy does not necessarily translate into high performance.

## Configuration File

Below is an example entry for `config.yaml`:

```yaml
high-util-but-low-sm-1:
  cluster: della
  partitions:
    - gpu
    - llm
  min_run_time:       0  # minutes
  util_thres_pct:    60  # percent
  util_minus_sm_pct: 30  # percent
  sm_thres_pct:      30  # percent
  gpu_hours_thres_user: 24  # hours
  gpu_hours_thres_admin: 0  # hours
  email_file: "high_util_low_sm.txt"
  admin_emails:
    - admin@institution.edu
```

The available settings are listed below:

- `cluster`: Specify the cluster name as it appears in the Slurm database. One cluster name
per alert.

- `partitions`: Specify one or more Slurm partitions. Use `"*"` to include all partitions (i.e., `partitions: ["*"]`). The number of GPU-hours is summed over all partitions.

- `email_file`: The text file to be used as the email message to users.

- `gpu_hours_thres_user`: Only users with greater than or equal to this threshold number of GPU-hours will receive an email.

- `gpu_hours_thres_admin`: Only users with greater than or equal to this threshold number of GPU-hours will appear in the report for administrators.

- `util_thres_pct`: Consider jobs with a GPU utilization that is greater than or equal to this value.

- `util_minus_sm_pct`: Consider jobs where the GPU utilization minus the SM utilization is greater than or equal to this value.

- `sm_thres_pct`: (Optional) Consider jobs where the SM utilization is less than or equal to this value. Default: 100

- `min_run_time`: (Optional) Minimum run time in minutes for a job to be included in the calculation. For example, if `min_run_time: 30` is used then jobs that ran for less than 30 minutes are ignored. Default: 0

- `num_top_users`: (Optional) Only consider the number of users equal to this value after sorting by GPU-hours. Default: 10

- `show_all_users`: (Optional) Flag to show all of the top users in the report instead of only the top users with low SM utilization. Default: `False`

- `num_jobs_display`: (Optional) Maximum number of jobs to display in the email message to users. Default: 10

- `max_num_jobid_admin`: (Optional) Maximum number of JobID's to show in the report to administrators. If the number of
jobs per user is greater than this value then a "+" character is appended to the end of the list. Default: 2

- `nodelist`: (Optional) Only apply this alert to jobs that ran on the specified nodes. See [example](../nodelist.md).

- `excluded_qos`: (Optional) List of QOSes to exclude from this alert.

- `excluded_partitions`: (Optional) List of partitions to exclude from this alert. This is useful when `partitions: ["*"]` is used.

- `excluded_users`: (Optional) List of users to exclude from receiving emails.

- `admin_emails`: (Optional) The emails sent to users will also be sent to these administrator emails. This applies
when the `--email` option is used.

- `email_subject`: (Optional) Subject of the email message to users.

- `report_title`: (Optional) Title of the report to system administrators.

- `enabled`: (Optional) If `False` then the alert is ignored. Default: `True`

## Report for System Administrators

Here is an example report:

```
$ job_defense_shield --high-util-but-low-sm

           High GPU Utilization But Low SM Utilization  
------------------------------------------------------------------
 User   GPU-Hours GPU-Util SM-Util  Jobs       JobID        Emails
------------------------------------------------------------------
u39403    811       72%      27%      6  16363102,16441427+   0  
u20461    777       80%       7%    224  16219160,16219161+   0  
u67029    522       95%      20%     27  16224617,16225709+   0  
u32756    452       63%      19%    112  16149263,16149264+   0  
------------------------------------------------------------------
   Cluster: della
Partitions: gpu,llm
     Start: Mon Oct 26, 2026 at 09:46 AM
       End: Mon Nov 02, 2026 at 09:46 AM
```

The table above shows that user `u20461` consumed 777 GPU-hours at
a GPU utilization of 80% but a very low SM utilization of 7%.

## Email Message to Users

Below is an example email message:

```
Hi Alan (u12345),

Below are 5 of your 202 jobs that ran on della in the past 7 days:

     JobID   Cluster Partition  GPU-Hours GPU-Util SM-Util
    16492937  della    pli-c       24       89%       1%  
    16488173  della    pli-c       24       89%       2%  
    16493478  della    pli-c       22       90%       1%  
    16499763  della    pli-c       20       99%       1%  
    16323186  della    pli-c       23       83%       7%  

For the 202 jobs, which consumed 591 GPU-hours, your mean GPU utilization
is 80% but the mean SM utilization is only 7%. This suggests that the
GPUs are not being used effectively.

See the definitions of these two metrics:
https://princetonuniversity.github.io/jobstats/setup/detailed_gpu_metrics/

Can changes be made to improve the SM utilization? For assistance please
attend an in-person Research Computing help session.
```

### Placeholders

The following placeholders can be used in the email file:

- `<GREETING>`: The greeting generated by `greeting-method`.
- `<CLUSTER>`: The cluster specified for the alert (i.e., `cluster`).
- `<PARTITIONS>`: A comma-separated list of partitions used by the user.
- `<DAYS>`: Number of days in the time window (default is 7).
- `<CASE>`: Helper text relating to the number of jobs.
- `<NUM-JOBS>`: Total number of jobs with high GPU utilization but low SM utilization.
- `<GPU-HOURS>`: Total GPU-hours of the jobs.
- `<GPU-UTIL>`: Mean GPU utilization.
- `<SM-UTIL>`: Mean SM utilization.
- `<TABLE>`: Table of job data.
- `<JOBSTATS>`: The `jobstats` command for the first job of the user.

## Usage

Generate a report of the users with high GPU utilization but low SM utilization:

```
$ job_defense_shield --high-util-but-low-sm
```

Send emails to the offending users:

```
$ job_defense_shield --high-util-but-low-sm --email
```

See which users have received emails and when they were sent:

```
$ job_defense_shield --high-util-but-low-sm --check
```

## cron

Below is an example entry for `crontab`:

```
0 9 * * 1-5 /path/to/job_defense_shield --high-util-but-low-sm --email > /path/to/log/high_util_but_low_sm.log 2>&1
```
