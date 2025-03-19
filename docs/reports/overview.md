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
                                               --gpu-model-too-powerful \
                                               --low-cpu-efficiency \
                                               --low-gpu-efficiency \
                                               --zero-cpu-utilization \
                                               --multinode-cpu-fragmentation \
                                               --multinode-gpu-fragmentation \
                                               --excessive-time \
                                               --excess-cpu-memory \
                                               --serial-allocating-multiple \
                                               --longest-queued \
                                               --jobs-overview \
                                               --utilization-overview \
                                               --most-gpus \
                                               --most-cores > ${BASE}/log/report.log 2>&1
```
