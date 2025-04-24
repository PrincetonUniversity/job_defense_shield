# Usage Overview

This report shows the usage by cluster as well as by cluster and partition. Two tables are displayed.

## Usage

```
$ job_defense_shield --usage-overview

        Usage Overview by Cluster
-----------------------------------------
cluster   users   cpu-hours    gpu-hours
-----------------------------------------
   della  464   1285938 (16%) 91714 (65%)
 stellar  149   6745324 (82%)  1926  (1%)
traverse    1    189987  (2%) 47497 (34%)
-----------------------------------------



       Usage Overview by Cluster and Partition
------------------------------------------------------
cluster  partition   users   cpu-hours     gpu-hours
------------------------------------------------------
   della        cpu  311    874114  (68%)     0   (0%)
   della      pli-c   28    115406   (9%) 25838  (28%)
   della gpu-shared   98     83617   (7%) 30083  (33%)
   della    datasci   31     80954   (6%)     0   (0%)
   della        gpu   51     47475   (4%) 16503  (18%)
   della        pli   20     35814   (3%)  6249   (7%)
   della     cryoem   17     20897   (2%)  4110   (4%)
   della    physics    5     12968   (1%)     0   (0%)
   della        mig   41      7169   (1%)  7169   (8%)
   della     pli-lc    5      3107   (0%)  1081   (1%)
   della    gputest   99      1948   (0%)   647   (1%)
   della        all    1      1280   (0%)     0   (0%)
   della      donia    4      1003   (0%)     0   (0%)
   della     gpu-ee    2       173   (0%)    23   (0%)
   della      grace    1        11   (0%)    11   (0%)
   della      malik    1         2   (0%)     0   (0%)
 stellar      cimes   21   2941001  (44%)     0   (0%)
 stellar         pu   56   2426873  (36%)     0   (0%)
 stellar       pppl   33   1340776  (20%)     0   (0%)
 stellar     serial   41     13187   (0%)     0   (0%)
 stellar        all   48     12377   (0%)     0   (0%)
 stellar        gpu   20     11044   (0%)  1926 (100%)
 stellar     bigmem    1        66   (0%)     0   (0%)
traverse        all    1    189987 (100%) 47497 (100%)
------------------------------------------------------
     Start: Fri Mar 07, 2025 at 11:27 AM
       End: Fri Mar 14, 2025 at 11:27 AM
```

## Configuration File

There are no settings for this report.
