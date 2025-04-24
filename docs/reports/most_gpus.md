# Jobs with the Most GPUs

This report shows the jobs with the most allocated GPUs. Only one job per user is shown. Pending jobs are ignored.

## Usage

```
$ job_defense_shield --most-gpus

                 Jobs with the Most GPUs (1 Job per User)                  
--------------------------------------------------------------------------
 JobID     User  Cluster  GPUs Nodes  Cores  State Partition Hours GPU-Eff
--------------------------------------------------------------------------
63072881  u12345  della    64    8     392      F     pli-c   1.3     0%  
63002445  u24197  della    32    4      64      F     pli-c   0.1    15%  
62925866  u43975  della    16    2      64    CLD     pli-c    35    90%  
62985649  u85040  della    16    2      32      F     pli-c   0.0     --  
62998072  u51822  della    16    2      16      F     pli-c   0.2     0%  
63057136  u65612  della    16    2      16      F       pli   0.2     8%  
  634429  u77353  tiger    12    3      12    COM       gpu    10    71%  
63017225  u79904  della     8    1      48    COM    pli-lc     3    13%  
63027060  u32309  della     8    1       8      F     pli-c   0.0     --  
63036518  u72188  della     8    1       1      F     pli-c   0.4     0%  
--------------------------------------------------------------------------
     Start: Sun Mar 16, 2025 at 08:19 PM
       End: Sun Mar 23, 2025 at 08:19 PM
```

## Configuration File

There are no settings for this report.
