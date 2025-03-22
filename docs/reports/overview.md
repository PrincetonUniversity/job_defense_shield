# Reports for System Administrators

The general idea to generate a report is to simply add the `--report` option to an alert. Here is an entire report:

```
$ cat clusters_report.sh

#!/bin/bash
PY="/home/admin/bin/jds-env/bin"
BASE="/home/admin/sw/job_defense_shield"
CFG="${BASE}/config.yaml"
${PY}/python -uB ${BASE}/job_defense_shield.py --days=7 \
                                               --config-file=${CFG} \
                                               --report \
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
                                               --longest-queued \
                                               --jobs-overview \
                                               --utilization-overview \
                                               --most-gpus \
                                               --most-cores > ${BASE}/log/report.log 2>&1
```
