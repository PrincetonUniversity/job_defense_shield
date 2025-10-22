# GPU Model Too Powerful

This alert identifies jobs that ran on GPUs that were more powerful than necessary.
For example, it can find jobs that ran on an NVIDIA B200 GPU but could have
used a less powerful GPU (e.g., A100 or [MIG](https://www.nvidia.com/en-us/technologies/multi-instance-gpu/)).
It can also find jobs that could have ran on GPUs with less memory.
Jobs can be identified based on GPU utilization, CPU/GPU memory usage, and the
number of allocated CPU-cores.

## Configuration File

Here is an example entry for `config.yaml`:

```yaml
gpu-model-too-powerful:
  clusters: della
  partitions:
    - gpu
  min_run_time:          61  # minutes
  gpu_util_threshold:    20  # percent
  gpu_mem_usage_max:     10  # GB
  num_cores_per_gpu:     12  # count
  cpu_mem_usage_per_gpu: 32  # GB
  gpu_hours_threshold:   24  # gpu-hours
  gpu_util_target:       50  # percent
  email_file: "gpu_model_too_powerful.txt"
  admin_emails:
    - admin@institution.edu
```

The available settings are listed below:

- `cluster`: Specify the cluster name as it appears in the Slurm database.

- `partitions`: Specify one or more Slurm partitions. Use `"*"` to include all partitions (i.e., `partitions: ["*"]`).

- `gpu_util_threshold`: Jobs with a mean GPU utilization of less than or equal to this value will be included.

- `email_file`: The text file to be used for the email message.

- `num_cores_per_gpu`: (Optional) This quantity is the total number of CPU-cores divided by the number of allocated GPUs. Jobs with a number of cores per GPU of less than or equal to `num_cores_per_gpu` will be selected.

- `gpu_mem_usage_max`: (Optional) Threshold for GPU memory usage in units of GB. Jobs with a GPU memory usage of less than or equal to `gpu_mem_usage_max` will be selected. For multi-GPU jobs, the maximum of the individual GPU memory usage values is used.

- `cpu_mem_usage_per_gpu`: (Optional) Threshold for CPU memory usage per GPU in units of GB. Jobs with a CPU memory usage per GPU of less than or equal to `cpu_mem_usage_per_gpu` will be selected. For multi-GPU jobs, this is calculated as total CPU memory usage of the job divided by the total number of allocated GPUs.

- `num_gpus`: (Optional) Jobs with a number of allocated GPUs of less than or equal to `num_gpus` will be selected.

- `gpu_hours_threshold`: (Optional) Minimum number of GPU-hours (summed over the jobs) for the user to be included. This setting makes it possible to ignore users that are not consuming many resources. Default: 0

- `gpu_util_target`: (Optional) The minimum acceptable GPU utilization. This must be specified for the `<TARGET>` placeholder to be available. Default: 50

- `min_run_time`: (Optional) The minimum run time of a job for it to be considered. Jobs that did not run longer
than this limit will be ignored. Default: 0

- `include_running_jobs`: (Optional) If `True` then jobs in a state of `RUNNING` will be included in the calculation. The Prometheus server must be queried for each running job, which can be an expensive operation. Default: False

- `nodelist`: (Optional) Only apply this alert to jobs that ran on the specified nodes. See [example](../nodelist.md).

- `excluded_qos`: (Optional) List of QOSes to exclude from this alert.

- `excluded_partitions`: (Optional) List of partitions to exclude from this alert. This is useful when `partitions: ["*"]` is used.

- `excluded_users`: (Optional) List of users to exclude from receiving emails.

- `admin_emails`: (Optional) List of administrator email addresses that should receive copies of the emails that are sent to users.

- `email_subject`: (Optional) Subject of the email message to users.

- `report_title`: (Optional) Title of the report to system administrators.

!!! tip "Nodelist"
    Be aware that a `nodelist` can be specified. This makes it possible to isolate jobs that ran on certain nodes within a partition.

!!! note "0% GPU Utilization"
    Jobs with 0% GPU utilization are ignored. To capture these jobs, use a different alert such as [GPU-Hours at 0% Utilization](zero_gpu_util.md).

## Report for System Administrators

```
$ job_defense_shield --gpu-model-too-powerful

                       GPU Model Too Powerful                       
------------------------------------------------------------
  User   GPU-Hours  Jobs            JobID             Emails
------------------------------------------------------------
 u23157     321      5    2567707,62567708,62567709+   0   
 u55404     108      5   62520246,62520247,62861050+   1 (2)
 u89790      55      2            62560705,62669923    0   
------------------------------------------------------------
   Cluster: della
Partitions: gpu
     Start: Tue Mar 11, 2025 at 10:50 PM
       End: Tue Mar 18, 2025 at 10:50 PM
```

## Email Message to Users

Below is an example email message (see `email/gpu_model_too_powerful.txt`):

```
Hello Alan (u23157),

Below are jobs that ran on an A100 GPU on Della in the past 7 days:

   JobID   Cores  GPUs GPU-Util GPU-Mem-Used-Max CPU-Mem-Used/GPU  Hours
  65698718   4     1      8%          4 GB             8 GB         120 
  65698719   4     1     14%          1 GB             3 GB          30 
  65698720   4     1      9%          2 GB             8 GB          90 

GPU-Mem-Used-Max is the maximum GPU memory usage of the individual allocated
GPUs while CPU-Mem-Used/GPU is the total CPU memory usage of the job divided by
the number of allocated GPUs.

The jobs above have (1) a low GPU utilization, (2) use less than 10 GB of GPU
memory, (3) use less than 32 GB of CPU memory, and (4) use 4 CPU-cores or less.
Such jobs could be run on the MIG GPUs. A MIG GPU has 1/7th the performance and
memory of an A100. To run on a MIG GPU, add the "partition" directive to your
Slurm script:

  #SBATCH --gres=gpu:1
  #SBATCH --partition=mig

For interactive sessions use, for example:

  $ salloc --nodes=1 --ntasks=<N> --time=1:00:00 --gres=gpu:1 --partition=mig

Replying to this automated email will open a support ticket with Research
Computing.
```

### Placeholders

The following placeholders can be used in the email file:

- `<GREETING>`: The greeting generated by `greeting-method`.
- `<CLUSTER>`: The cluster specified for the alert.
- `<PARTITIONS>`: A comma-separated list of partitions used by the user.
- `<DAYS>`: Number of days in the time window (default is 7).
- `<TARGET>`: The minimum acceptable GPU utilization (i.e., `gpu_util_target`).
- `<GPU-UTIL>`: Threshold value for GPU utilization (i.e., `gpu_util_threshold`). 
- `<CORES-PER-GPU>`: Number of CPU-cores per GPU (i.e., `num_cores_per_gpu`).
- `<GPU-MEM>`: Maximum GPU memory usage (i.e., `gpu_mem_usage_max`).
- `<CPU-MEM>`: CPU memory usage per GPU (i.e., `cpu_mem_usage_per_gpu`).
- `<NUM-GPUS>`: Threshold value for the number of allocated GPUs per job (i.e., `num_gpus`).
- `<NUM-JOBS>`: Number of jobs that are using GPUs that are too powerful.
- `<TABLE>`: Table of job data.
- `<JOBSTATS>`: The `jobstats` command for the first job of the user.

## Usage

Generate a report of the users that are using GPUs that are more powerful than necessary:

```
$ job_defense_shield --gpu-model-too-powerful
```

Send emails to the offending users:

```
$ job_defense_shield --gpu-model-too-powerful --email
```

See which users have received emails and when:

```
$ job_defense_shield --gpu-model-too-powerful --check
```

## cron

Below is an example entry for `crontab`:

```
0 9 * * * /path/to/job_defense_shield --gpu-model-too-powerful --email > /path/to/log/gpu_model_too_powerful.log 2>&1
```
