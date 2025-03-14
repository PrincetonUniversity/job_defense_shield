# Defend the Hardware

**Job Defense Shield** is a software tool for sending automated email alerts to HPC users and for creating reports for system administrators. It is a component of the [Jobstats](https://github.com/PrincetonUniversity/jobstats) job monitoring platform.

Automated email alerts to users are available for these cases:

- Automatically cancel jobs at 0% GPU utilization
- CPU jobs with 0% utilization
- Top users with low mean CPU or GPU efficiency
- Jobs that allocate excess CPU memory
- Jobs that allocate too many CPU-cores per GPU
- Jobs that allocate too much CPU memory per GPU
- Serial jobs that allocate multiple CPU-cores
- Users that routinely run with excessive time limits
- Jobs that could have used a smaller number of nodes
- Jobs that could have used less powerful GPUs
- Jobs thar ran on specialized nodes but did not need to

All of the instances in the list above can be formulated as a report
for system administrators. The most popular reports for system
administrators are:

- A list of users with the most GPU-hours at 0% utilization
- A list of the top users with low CPU/GPU utilization
- A list of users that are over-allocating the most CPU memory

The Python code is written using object-oriented programming techniques which makes it easy to create new alerts and reports.

## Example Reports

Which users have wasted the most GPU-hours?

```
                         GPU-Hours at 0% Utilization                          
---------------------------------------------------------------------
    User   GPU-Hours-At-0%  Jobs             JobID             Emails
---------------------------------------------------------------------
1  u12998        308         39   62285369,62303767,62317153+   1 (7)
2  u9l487         84         14   62301737,62301738,62301742+   0     
3  u39635         25          2            62184669,62187323    2 (4)     
4  u24074         24         13   62303182,62303183,62303184+   0      
---------------------------------------------------------------------
   Cluster: della
Partitions: gpu, pli-c, pli-p, pli, pli-lc
     Start: Wed Feb 12, 2025 at 09:50 AM
       End: Wed Feb 19, 2025 at 09:50 AM
```

Which users are wasting the most CPU memory?

```
                        Users Allocating Excess CPU Memory                 
----------------------------------------------------------------------------
    User    Unused    Used    Ratio   Ratio  Ratio   CPU-Hrs  Jobs   Emails
           (TB-Hrs) (TB-Hrs) Overall  Mean   Median                        
----------------------------------------------------------------------------
1  u93714    127       10      0.07   0.08   0.07     82976    12      0  
2  u44210     17       81      0.82   0.38   0.26      1082    20      0  
3  u61098     10        4      0.02   0.02   0.02        90     4      2 (8)
4  u13158      4        1      0.03   0.03   0.03        61     2      0  
----------------------------------------------------------------------------
   Cluster: tiger
Partitions: cpu
     Start: Wed Feb 12, 2025 at 09:50 AM
       End: Wed Feb 19, 2025 at 09:50 AM
```


## Example Emails

Below is an example email for the automatic cancellation of a GPU job with 0% utilization:

```
Hi Alan (u12345),

The jobs below have been cancelled because they ran for nearly 2 hours at 0% GPU
utilization:

     JobID    Cluster  Partition    State    GPUs-Allocated GPU-Util  Hours
    60131148   della      llm     CANCELLED         4          0%      2.0  
    60131741   della      llm     CANCELLED         4          0%      1.9  

See our GPU Computing webpage for three common reasons for encountering zero GPU
utilization:

    https://your-institution.edu/knowledge-base/gpu-computing

Replying to this automated email will open a support ticket with Research
Computing.
```

Below is an example email to a user that is requesting too much CPU memory:

```
Hi Alan (u12345),

Below are your jobs that ran on BioCluster in the past 7 days:

     JobID   Memory-Used  Memory-Allocated  Percent-Used  Cores  Hours
    5761066      2 GB          100 GB            2%         1     48
    5761091      4 GB          100 GB            4%         1     48
    5761092      3 GB          100 GB            3%         1     48

It appears that you are requesting too much CPU memory for your jobs since
you are only using on average 3% of the allocated memory. For help on
allocating CPU memory with Slurm, please see:

    https://your-institution.edu/knowledge-base/memory

Replying to this automated email will open a support ticket with Research
Computing. 
```

## Usage

Emails to users are most effective when sent sparingly. For this reason, there is a command-line parameter `--days` to specify the amount of time that must pass before the user can receive another email of the same nature.

The example below shows how to send emails to the top users with low GPU efficiencies over the last week:

```
$ python job_defense_shield.py --low-gpu-efficiency --email
```

A configuration entry is needed for each alert. This is covered later.


## How does it work?

Summary statistics for each completed job are stored in a compressed format in the `AdminComment` field in the Slurm database. The software described here works by calling the Slurm `sacct` command while requesting several fields including `AdminComment`. The `sacct` output is stored in a `pandas` dataframe for processing. For running jobs the Prometheus database must be queried.
