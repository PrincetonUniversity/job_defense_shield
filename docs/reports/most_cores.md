# Jobs with the Most CPU-Cores

This report shows the jobs with the most allocated CPU-cores. Only one job per user is shown. Pending jobs are ignored.

## Usage

```
$ job_defense_shield --most-cores

              Jobs with the Most CPU-Cores (1 Job per User)              
--------------------------------------------------------------------------
 JobID    User   Cluster  Cores  Nodes  GPUs State Partition Hours CPU-Eff
--------------------------------------------------------------------------
1934156  u16627  stellar  4864    38     0    COM    cimes     21     94% 
1935647  u96942  stellar  4096    43     0      F      all    0.0      -- 
1936024  u56387  stellar  3840    40     0     TO     pppl     23     99% 
1935308  u49898  stellar  3840    40     0     TO     pppl     24     98% 
1934176  u24031  stellar  2304    18     0    COM    cimes      9     89% 
1938252  u42387  stellar  1920    20     0    COM       pu     24    100% 
1933647  u95519  stellar  1536    16     0    COM     pppl     22     99% 
1934482  u36180  stellar  1536    16     0     TO     pppl     24     99% 
 634428  u17874    tiger  1456    13     0    COM      cpu      3     91% 
 634182  u15289    tiger  1344    12     0     TO      cpu     48    100% 
--------------------------------------------------------------------------
     Start: Sun Mar 16, 2025 at 07:55 PM
       End: Sun Mar 23, 2025 at 07:55 PM
```

## Configuration File

There are no settings for this report.
