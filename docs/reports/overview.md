# Reports for System Administrators

The general idea to generate a report is to simply add the `--report` option to an alert.
Here is an example:

```
$ job_defense_shield --zero-gpu-util --days=7 --report
```

With the appropriate entry in `config.yaml`:

```
zero-gpu-utilization:
  file: alert/zero_util_gpu_hours.py
  clusters:
    - della
  partitions:
    - gpu
  excluded_users:
    - aturing
    - einstein
```

Here is an entire report:

```
$ cat clusters_report.sh

#!/bin/bash
PY="/home/jdh4/bin/jds-env/bin"
BASE="/tigress/jdh4/utilities/job_defense_shield"
CFG="${BASE}/config.yaml"
${PY}/python -uB ${BASE}/job_defense_shield.py --days=7 \
                                               --config-file=${CFG} \
                                               --report \
                                               --zero-util-gpu-hours \
                                               --mig \
                                               --low-xpu-efficiency \
                                               --zero-cpu-utilization \
                                               --cpu-fragmentation \
                                               --gpu-fragmentation \
                                               --excessive-time \
                                               --excess-cpu-memory \
                                               --serial-using-multiple \
                                               --longest-queued \
                                               --jobs-overview \
                                               --utilization-overview \
                                               --most-gpus \
                                               --most-cores > ${BASE}/log/report.log 2>&1
```


