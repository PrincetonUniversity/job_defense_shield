# job_defense_shield

The general version is coming. Please see the version that is specific to [our institution](https://github.com/jdh4/job_defense_shield).

## Sample Emails

#### Running GPUs with Zero GPU Utilization

```
Hi Alan,

You have GPU jobs that have been running for more than 1 hour but they appear to
not be using the GPU(s):

      JobID    NetID  Cluster  GPUs-Allocated  GPUs-Unused GPU-Unused-Util  Hours
     46177950 aturing  della         2             2              0%        3.9  
     46177951 aturing  della         2             2              0%        3.9  

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


#### Low GPU Utilization

```
Hi Ahmet,

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


#### Recommending MIG GPUs for certain jobs

```
Hi Alan,

Below are jobs that ran on an A100 GPU on Della in the past 10 days:

   JobID   NetID  GPU-Util GPU-Mem-Used CPU-Mem-Used  Hours
  45933239 aturing  10%        3 GB         3 GB       50  
  45933241 aturing   9%        3 GB         3 GB       50  
  45942078 aturing  10%        3 GB         3 GB       55  
  45942079 aturing  11%        3 GB         3 GB       70  
  45942080 aturing  11%        3 GB         3 GB       70  
  45942081 aturing  12%        3 GB         3 GB       70  
  45948433 aturing  10%        2 GB         2 GB       55  
  45948435 aturing   8%        2 GB         2 GB       82  
  45948439 aturing  11%        2 GB         2 GB       85  
  45948440 aturing  11%        2 GB         2 GB       83  

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

Replying to this email will open a support ticket with CSES. Let us know if we
can be of help.
```
