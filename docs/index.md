# Defend the Hardware

Job Defense Shield is a software tool for identifying and reducing instances of underutilization by the users of high-performance computing systems. The software sends automated email alerts to users and creates reports for system administrators. Job Defense Shield is a component of the [Jobstats](https://github.com/PrincetonUniversity/jobstats) job monitoring platform.

Most popular feature:

- **automatically cancel GPU jobs at 0% utilization**

Automated email alerts and reports are available for:

- low GPU utilization
- too many allocated CPU-cores per GPU
- too much allocated CPU memory per GPU
- GPU model was too powerful (i.e., use MIG instead)
- multinode GPU fragmentation
- excessive run time limits for GPU jobs
- over-allocating CPU memory
- low CPU utilization
- serial jobs allocating multiple CPU-cores
- multinode CPU fragmentation
- excessive run time limits for CPU jobs

## Example Reports

Which users have wasted the most GPU-hours?

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

Which users are over-allocating the most CPU memory?

```
                        Users Allocating Excess CPU Memory                 
----------------------------------------------------------------------------
    User    Unused    Used    Ratio   Ratio  Ratio   CPU-Hrs  Jobs   Emails
           (TB-Hrs) (TB-Hrs) Overall  Mean   Median                        
----------------------------------------------------------------------------
1  u93714    127       10      0.07   0.08   0.07     42976    12      2 (6)  
2  u44210     17       81      0.83   0.84   0.79     31082    20      0  
3  u61098     10        4      0.71   0.71   0.65      6790     4      0
4  u13158      4        1      0.20   0.20   0.20      3961     2      0  
----------------------------------------------------------------------------
   Cluster: tiger
Partitions: cpu
     Start: Wed Feb 12, 2025 at 09:50 AM
       End: Wed Feb 19, 2025 at 09:50 AM
```

## Example Emails

Below is an example email to a user for the automatic cancellation of GPU jobs:

```
Hi Alan (u12345),

The jobs below have been cancelled because they ran for 2 hours at 0% GPU
utilization:

     JobID    Cluster  Partition    State    GPUs-Allocated GPU-Util  Hours
    60131148   della      gpu     CANCELLED         4          0%       2  
    60131741   della      gpu     CANCELLED         4          0%       2  

See our GPU Computing webpage for three common reasons for encountering zero GPU
utilization:

    https://your-institution.edu/KB/gpu-computing

Replying to this automated email will open a support ticket with Research
Computing.
```

Below is an example email to a user that is allocating too much CPU memory:

```
Hi Alan (u12345),

Below are your jobs that ran on Stellar in the past 7 days:

     JobID   Memory-Used  Memory-Allocated  Percent-Used  Cores  Hours
    5761066      2 GB          100 GB            2%         1     48
    5761091      4 GB          100 GB            4%         1     48
    5761092      3 GB          100 GB            3%         1     48

It appears that you are requesting too much CPU memory for your jobs since
you are only using on average 3% of the allocated memory. For help on
allocating CPU memory with Slurm, please see:

    https://your-institution.edu/KB/cpu-memory

Replying to this automated email will open a support ticket with Research
Computing.
```

## Example Usage

Send emails to users that are over-allocating CPU memory:

```
$ job_defense_shield --excess-cpu-memory --email
```

If you think that Job Defense Shield is a fit for your institution then continue to the [Installation](setup.md) page.
