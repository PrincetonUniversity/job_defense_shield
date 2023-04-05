# Job Defense Shield

The general version is coming. Please see the version that is specific to [our institution](https://github.com/jdh4/job_defense_shield) in the meantime.

Job Defense Shield is simple Python code for sending automated email alerts to users and for creating reports for system administrators. It is part of the [Jobstats platform](https://github.com/PrincetonUniversity/jobstats) which is based on Slurm and Prometheus.

## About

The software in this repo creates a report of problem users and problem jobs. The software identifies the following:

+ actively running jobs where a GPU has zero utilization  
+ the heaviest users with low CPU or GPU utilization  
+ jobs that use the large-memory nodes but do not need them  
+ jobs that could have been run on MIG GPUs instead of full A100 GPUs  
+ multinode CPU jobs where one or more nodes have zero utilization  
+ users that have been over-allocating CPU or GPU time  
+ jobs with CPU or GPU fragmentation (e.g., 1 GPU per node over 4 nodes)  
+ jobs with the most CPU-cores and jobs with the most GPUs  
+ pending jobs with the longest queue times  
+ jobs that request more than the default memory but do not use it  

The script does not identify:
+ abuses of file storage or I/O  

## How to Use

The following example show how to check for zero GPU utilization of actively running jobs:

```
$ ./job_defense_shield.py --email \
                          --days=1 \
                          --zero-gpu-utilization \
                          --files /nfs/.shield/violations
```

The example below runs several alerts at once:

```
$ ./job_defense_shield.py --email \
                          --days=7 \
                          --zero-util-gpu-hours \
                          --gpu-fragmentation \
                          --mig \
                          --low-xpu-efficiency \
                          --low-time-efficiency \
                          --datascience \
                          --longest-queued   
```

## Installation

The Job Defense Shield is written in Python. The requirements are:

- Python 3.7+
- Pandas
- [jobstats](https://github.com/PrincetonUniversity/jobstats) (if looking to send emails about actively running jobs)  

## Sample Emails

### Actively Running Jobs with Zero GPU Utilization

```
Hi Alan,

You have GPU jobs that have been running for more than 1 hour but they appear to
not be using the GPU(s):

      JobID    NetID  Cluster  GPUs-Allocated  GPUs-Unused GPU-Unused-Util  Hours
     46177950 aturing  della         2             2              0%        3.0  
     46177951 aturing  della         1             1              0%        1.5  

We measure the utilization of each allocated GPU every 30 seconds. All
measurements for at least one of the GPUs used in each job above have been
reported as 0%. You can see this by running the "jobstats" command, for example:

     $ jobstats 46177950

Follow the link at the bottom of the "jobstats" output for more detailed
information.

If the GPU(s) are not being used then you need to take action now to resolve
this issue. Wasting resources prevents other users from getting their work done
and it causes your subsequent jobs to have a lower priority. Users that
continually underutilize the GPUs risk having their accounts suspended.

Toward resolving this issue please consult the documentation for the code that
you are running. Is it GPU-enabled?

For general information about GPU computing and Slurm job statistics:

     https://researchcomputing.princeton.edu/support/knowledge-base/gpu-computing
     https://researchcomputing.princeton.edu/support/knowledge-base/job-stats

Please consider canceling the jobs listed above by using the "scancel" command,
for example:

     $ scancel 46177950

Add the following lines to your Slurm scripts to receive an email report with
GPU utilization information after each job finishes:

     #SBATCH --mail-type=end
     #SBATCH --mail-user=aturing@princeton.edu

Replying to this email will open a support ticket with CSES. Let us know if we
can be of help in resolving this matter.
```

### Low GPU Utilization

```
Hi Alan,

Over the last 8 days you have used the 10th most GPU-hours on Della (GPU) but
your mean GPU efficiency is only 12%:

      NetID  Partition(s)  Jobs  GPU-hours GPU-rank Efficiency
     aturing     gpu       1670    1902     10/118     12%    

Please investigate the reason(s) for the low efficiency. Common reasons for low
GPU efficiency include:

  1. Misconfigured application scripts. Be sure to read the documentation of the
     software to make sure that you are using it properly. This includes creating
     the appropriate software environment. For a general overview of GPU computing:
     https://researchcomputing.princeton.edu/support/knowledge-base/gpu-computing

  2. Using an A100 GPU when a MIG GPU would be sufficient. Some codes do not have
     enough work to keep an A100 GPU busy. If you encounter this on the Della
     cluster then consider using a MIG GPU:
     https://researchcomputing.princeton.edu/systems/della#gpus

  3. Training deep learning models while only using a single CPU-core. Codes such as
     PyTorch and TensorFlow show performance benefits when multiple CPU-cores are
     used for the data loading. For PyTorch see:
     https://researchcomputing.princeton.edu/support/knowledge-base/pytorch#multi

  4. Using too many GPUs for a job. You can find the optimal number of GPUs and
     CPU-cores by performing a scaling analysis:
     https://researchcomputing.princeton.edu/support/knowledge-base/scaling-analysis

  5. Writing job output to the /tigress or /projects storage systems. Actively
     running jobs should be writing output files to /scratch/gpfs/aduzgun which is
     a much faster filesystem. For more information:
     https://researchcomputing.princeton.edu/support/knowledge-base/data-storage

Consult the documentation or write to the mailing list of the software that you
are using for additional reasons for low GPU efficiency and for potential
solutions. You may also consider attending a Research Computing help session:

     https://researchcomputing.princeton.edu/support/help-sessions

Add the following lines to your Slurm scripts to receive an email report with GPU
efficiency information after each job finishes:

     #SBATCH --mail-type=end
     #SBATCH --mail-user=aturing@princeton.edu

You can check the efficiency of completed and actively running jobs by using the
'jobstats' command:

     https://researchcomputing.princeton.edu/support/knowledge-base/job-stats

Replying to this email will open a support ticket with CSES. Let us know if we
can be of help.
```

### Low CPU Utilization

```
Hi Alan,

Over the last 8 days you have used the 11th most CPU-hours on TigerCPU but
your mean CPU efficiency is only 47%:

     NetID    Partition(s)   Jobs  CPU-hours CPU-rank Efficiency
     aturing cpu,ext,serial   11    52876     11/63      47%    

Please investigate the reason(s) for the low efficiency. Common reasons for low
CPU efficiency include:

  1. Running a serial code using multiple CPU-cores. Make sure that your code is
     written to run in parallel before using multiple CPU-cores. Learn more:
     https://researchcomputing.princeton.edu/support/knowledge-base/parallel-code

  2. Using too many CPU-cores for parallel jobs. You can find the optimal number
     of CPU-cores by performing a scaling analysis:
     https://researchcomputing.princeton.edu/support/knowledge-base/scaling-analysis

  3. Writing job output to the /tigress or /projects storage systems. Actively
     running jobs should be writing output files to /scratch/gpfs/hm2524 which is
     a much faster filesystem. For more information:
     https://researchcomputing.princeton.edu/support/knowledge-base/data-storage

  4. Using the MPICH library instead of an MPI library that was built for our
     clusters. Some software installed using 'conda' is built against an MPI
     library that is not optimized for our systems. Run 'conda list' after
     activating the environment and look for 'mpich' to see if you are using this
     library.

  5. Using 'mpirun' instead of 'srun' for parallel codes. Please use 'srun'.

Consult the documentation or write to the mailing list of the software that you
are using for additional reasons for low CPU efficiency and for potential
solutions. You may also consider attending a Research Computing help session:

     https://researchcomputing.princeton.edu/support/help-sessions

Add the following lines to your Slurm scripts to receive an email report with CPU
efficiency information after each job finishes:

     #SBATCH --mail-type=end
     #SBATCH --mail-user=aturing@princeton.edu

You can check the efficiency of completed and actively running jobs by using the
"jobstats" command:

     https://researchcomputing.princeton.edu/support/knowledge-base/job-stats

Replying to this email will open a support ticket with CSES. Let us know if we
can be of help.
```

### Recommending MIG GPUs

```
Hi Alan,

Below are jobs that ran on an A100 GPU on Della in the past 10 days:

   JobID   NetID  GPU-Util GPU-Mem-Used CPU-Mem-Used  Hours
  45933239 aturing  10%        3 GB         3 GB       50  
  45933241 aturing   9%        3 GB         3 GB       50  
  45948433 aturing  10%        2 GB         2 GB       55  
  45948435 aturing   8%        2 GB         2 GB       82

The jobs above have a low GPU utilization and they use less than 10 GB of GPU
memory and less than 32 GB of CPU memory. Such jobs could be run on the MIG
GPUs. A MIG GPU is essentially a small A100 GPU with 1/7th the performance and
memory of an A100. To run on a MIG GPU, add the "partition" directive to your
Slurm script:

  #SBATCH --nodes=1
  #SBATCH --ntasks=1
  #SBATCH --cpus-per-task=1
  #SBATCH --gres=gpu:1
  #SBATCH --partition=mig

For interactive sessions use, for example:

  $ salloc --nodes=1 --ntasks=1 --time=1:00:00 --gres=gpu:1 --partition=mig

If you are using Jupyter OnDemand then set the "Custom partition" to "mig" when
creating the session.

A job can use a MIG GPU when the following constraints are satisfied:

  1. The required number of GPUs is 1
  2. The required number of CPU-cores is 1
  3. The required GPU memory is less than 10 GB
  4. The required CPU memory is less than 32 GB

All MIG jobs are automatically allocated 32 GB of CPU memory and 10 GB of GPU
memory.

By running future jobs on the MIG GPUs you will experience shorter queue
times and you will help keep A100 GPUs free for jobs that need them. Since
your jobs satisfy the above constraints, please use the MIG GPUs. For more:

  https://researchcomputing.princeton.edu/systems/della#gpus

As an alternative to MIG, you may consider trying to improve the GPU
utilization of your code. A good place to start is the mailing list of
the software you are using.

Add the following lines to your Slurm scripts to receive an email report with
memory usage information after each job finishes:

   #SBATCH --mail-type=end
   #SBATCH --mail-user=aturing@princeton.edu

Replying to this email will open a support ticket with CSES. Let us know if we
can be of help.
```

### Underutilization of the Large-Memory Nodes

```
Hi Alan,

Below are jobs that ran on the large-memory (datascience) nodes on Della in the 
past 7 days:

    JobID     NetID  Memory-Used Memory-Allocated Large-Memory-Needed?  Hours
   46171956  aturing    105 GB        300 GB               No             8   
   46236937  aturing    104 GB        300 GB               No             3   
   46247483  aturing     72 GB        300 GB               No             2   

The large-memory nodes should only be used for jobs that require 190 GB or more.
It appears that none of the jobs above needed one of these nodes. For future jobs,
please lower the value of the --mem-per-cpu or --mem Slurm directive so that the
overall memory requirement of each job is less than 190 GB. You should use the
smallest value possible but include an extra 20% for safety.

For more information on the large-memory nodes and allocating CPU memory:

   https://researchcomputing.princeton.edu/systems/della#large_memory
   https://researchcomputing.princeton.edu/support/knowledge-base/memory

Users that continually run jobs on the large-memory nodes without justification
risk losing access to these nodes since it prevents others from getting their
work done.

Add the following lines to your Slurm scripts to receive an email report with
GPU utilization information after each job finishes:

   #SBATCH --mail-type=end
   #SBATCH --mail-user=aturing@princeton.edu

One can also see memory usage information by using the following command:

   $ jobstats 46171956

Replying to this email will open a support ticket with CSES. Let us know if we
can be of help.
```

## How to Create a New Alert

A new alert is made by creating a new Python class that derives from the `Alert` base class. One then has to write the `_filter_and_add_new_fields` method and the `send_emails_to_users` method. There are several examples of this procedure in the `alert` directory.
