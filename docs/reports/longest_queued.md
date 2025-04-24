# Longest Queued Jobs

This report shows the jobs that have been queued for the longest. Note that some jobs may be dependencies. Some jobs may be pending due to a QOS limit. Array jobs are ignored. Only one job per user is shown.

## Usage

```
$ job_defense_shield --longest-queued

     Longest Queue Times (1 job per user, ignoring job arrays)     
-------------------------------------------------------------------
 JobID    User  Cluster Nodes    QOS     Partition  Submit Eligible
                                                    (Days)  (Days) 
-------------------------------------------------------------------
62932214 u31448  della    1   gpu-medium        gpu   7       7    
62948029 u35047  della    1   gpu-medium        gpu   6       6    
62963093 u96241  della    2    gpu-short gpu-shared   6       6    
62965916 u10786  della    1   gpu-medium        gpu   6       6    
62964820 u25452  della    1    gpu-short gpu-shared   6       6    
62979761 u88810  della    1   gpu-medium        gpu   5       5    
62986554 u33030  della    4      pli-low        pli   5       5    
63012946 u29346  della    1     gpu-long        gpu   4       4    
62999688 u23026  della    1   gpu-medium        gpu   4       4    
62998454 u87234  della    1    gpu-short gpu-shared   4       4    
-------------------------------------------------------------------
     Start: Sun Mar 16, 2025 at 09:13 PM
       End: Sun Mar 23, 2025 at 09:13 PM
```

## Configuration File

There are no settings for this report.
