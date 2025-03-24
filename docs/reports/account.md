# Usage by Slurm Account

This report shows the usage breakdown by cluster, partition, and Slurm account. Two tables are displayed.

## Usage

The command below will generate the report:

```
$ python job_defense_shield.py --usage-by-slurm-account
```

One can produce the report for just one cluster:

```
$ python job_defense_shield.py --usage-by-slurm-account -M stellar
```

## Configuration File

There are no settings for this report.
