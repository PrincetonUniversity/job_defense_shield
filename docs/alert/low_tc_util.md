# Low Tensor Core Utilization

This alert identifies users whose jobs exhibit low Tensor Core utilization.

Tensor Cores are specialized execution units designed to accelerate matrix operations, which are fundamental to deep learning and scientific computing workloads. Tensor Core utilization is the percentage of time that the Tensor Cores are active. When a workload can take advantage of mixed-precision or matrix operations (such as FP16, BF16, TF32, or FP8), utilizing Tensor Cores can provide a substantial speedup compared to standard CUDA cores.

This alert is useful for clusters or partitions that are devoted to AI codes which should almost always use the Tensor Cores.

!!! note

    Jobstats 1.1.0+ with [detailed GPU metrics](https://princetonuniversity.github.io/jobstats/setup/detailed_gpu_metrics/) enabled is required for this alert. The alert expects to find `any_tensor_util_percent_avg`.

## Configuration File

Below is an example entry for `config.yaml`:

```yaml
low-tc-utilization-1:
  cluster: della
  partitions:
    - gpu
    - llm
  util_thres_pct:         70  # percent
  tc_thres_pct:            0  # percent
  gpu_hours_thres_user:  100  # gpu-hours
  gpu_hours_thres_admin: 100  # gpu-hours
  email_file: "low_tc_utilization.txt"
  admin_emails:
    - admin@institution.edu
```

The available settings are listed below:

- `cluster`: Specify the cluster name as it appears in the Slurm database. One cluster name per alert.

- `partitions`: Specify one or more Slurm partitions. Use `"*"` to include all partitions (i.e., `partitions: ["*"]`). The number of GPU-hours is summed over all partitions.

- `email_file`: The text file to be used as the email message to users.

- `util_thres_pct`: Consider jobs where the GPU utilization is greater than or equal to this value.

- `tc_thres_pct`: Consider jobs where the Tensor Core utilization is less than or equal to this value.

- `gpu_hours_thres_user`: Only users with greater than or equal to this threshold number of GPU-hours will receive an email.

- `gpu_hours_thres_admin`: Only users with greater than or equal to this threshold number of GPU-hours will appear in the report for administrators.

- `min_run_time`: (Optional) Minimum run time in minutes for a job to be included in the calculation. For example, if `min_run_time: 30` is used then jobs that ran for less than 30 minutes are ignored. Default: 0

- `num_top_users`: (Optional) Only consider the number of users equal to this value after filtering and then sorting by GPU-hours. Default: 15

- `show_all_users`: (Optional) Flag to show all of the top users in the report. Default: False

- `num_jobs_display`: (Optional) Maximum number of jobs to display in the email message to users. Default: 4

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
$ job_defense_shield --low-tc-utilization

                   Low Tensor Core Utilization  
------------------------------------------------------------------
 User   GPU-Hours GPU-Util TC-Util  Jobs       JobID        Emails
------------------------------------------------------------------
u12345    777       80%       0%    224  16219160,16219161+   0  
u32756    152       73%       0%    112  16149263,16149264+   0  
------------------------------------------------------------------
   Cluster: della
Partitions: gpu,llm
     Start: Mon Oct 26, 2026 at 09:46 AM
       End: Mon Nov 02, 2026 at 09:46 AM
```

## Email Message to Users

Below is an example email message:

```
Hi Alan (u12345),

Below are 5 of your 224 jobs that ran on della in the past 7 days:

     JobID   Cluster Partition  GPU-Hours GPU-Util TC-Util
    16492937  della    pli-c       24       89%       0%  
    16488173  della    pli-c       24       89%       0%  
    16493478  della    pli-c       22       90%       0%  
    16499763  della    pli-c       20       99%       0%  
    16323186  della    pli-c       23       83%       0%  

For the 224 jobs, which consumed 777 GPU-hours, your mean Tensor Core
utilization was 0%. See the definition of this metric:
https://princetonuniversity.github.io/jobstats/setup/detailed_gpu_metrics/

Can changes be made to improve the Tensor Core utilization? For
assistance, please attend an in-person Research Computing help session.
```

### Placeholders

The following placeholders can be used in the email file:

- `<GREETING>`: The greeting generated by `greeting-method`.
- `<DAYS>`: Number of days in the time window (default is 7).
- `<CASE>`: Helper text relating to the number of jobs.
- `<CLUSTER>`: The cluster specified for the alert (i.e., `cluster`).
- `<PARTITIONS>`: A comma-separated list of partitions used by the user.
- `<GPU-HOURS>`: Total GPU-hours of the jobs.
- `<GPU-UTIL>`: Mean GPU utilization.
- `<TC-UTIL>`: Mean Tensor Core utilization.
- `<NUM-JOBS>`: Total number of jobs with low Tensor Core utilization.
- `<TABLE>`: Table of job data.
- `<JOBSTATS>`: The `jobstats` command for the first job of the user.

## Usage

Generate a report of the users with low Tensor Core utilization:

```
$ job_defense_shield --low-tc-utilization
```

Send emails to the offending users:

```
$ job_defense_shield --low-tc-utilization --email
```

See which users have received emails and when they were sent:

```
$ job_defense_shield --low-tc-utilization --check
```

## cron

Below is an example entry for `crontab`:

```
0 9 * * 1-5 /path/to/job_defense_shield --low-tc-utilization --email > /path/to/log/low_tc_utilization.log 2>&1
```
