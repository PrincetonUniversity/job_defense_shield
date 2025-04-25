# Reports for System Administrators

Any of the previously discussed GPU or CPU alerts can be turned into a report. This is done by simply adding the `--report` flag.

```
$ job_defense_shield --excess-cpu-memory --report
```

The `--report` flag will cause the report to be sent by email to the addresses in `report-emails` in `config.yaml`.

One can also combine an email alert with the generation of a report:

```
$ job_defense_shield --excess-cpu-memory --email --report
```

The command above will email users for over-allocating CPU memory and send the report to system administrators.

Below is a script for creating a comprehensive report. Such a report allows one to see all of the instances of underutilization and which users are scheduled to receive an email.

```
$ cat clusters_report.sh

#!/bin/bash
JDS="/home/admin/sw/jds-env"
CFG="${JDS}/config.yaml"
${JDS}/bin/job_defense_shield --report \
                              --config-file=${CFG} \
                              --zero-util-gpu-hours \
                              --low-gpu-efficiency \
                              --too-much-cpu-mem-per-gpu \
                              --too-many-cores-per-gpu \
                              --gpu-model-too-powerful \
                              --multinode-gpu-fragmentation \
                              --excessive-time-gpu \
                              --zero-cpu-utilization \
                              --excess-cpu-memory \
                              --low-cpu-efficiency \
                              --serial-allocating-multiple \
                              --multinode-cpu-fragmentation \
                              --excessive-time-cpu \
                              --usage-overview \
                              --longest-queued \
                              --most-gpus \
                              --most-cores \
                              --jobs-overview \
                              > ${JDS}/log/report.log 2>&1
```
