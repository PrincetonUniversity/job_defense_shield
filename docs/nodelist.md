# Nodelist

For systems composed of nodes with different specifications, filtering jobs by `cluster` and `partitions` can be insufficient.
To provide more control, a `nodelist` can be specified:

```yaml
too-much-cpu-mem-per-gpu-1:
  cluster: della
  partitions:
    - gpu
  cores_per_node:          48  # count
  gpus_per_node:            4  # count
  cpu_mem_per_node:      1000  # GB
  cpu_mem_per_gpu_target: 240  # GB
  cpu_mem_per_gpu_limit:  250  # GB
  email_file: "too_much_cpu_mem_per_gpu_2.txt"
  nodelist:
    - della-l01g1
    - della-l01g2
    - della-l01g3
    - della-l01g4
    - della-l01g5
    - della-l01g6
    - della-l01g7
    - della-l01g8
```

The alert above will only consider jobs that ran exclusively on one or more nodes in the `nodelist`. This makes it possible to write alerts for partitions composed of heterogeneous hardware.
