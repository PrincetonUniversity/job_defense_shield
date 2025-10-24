"""Functions for calculating CPU/GPU efficiencies and CPU/GPU memory usage."""

import json
import gzip
import base64
from typing import Tuple
from typing import Set
from typing import Optional
from typing import Union
from functools import partial
import pandas as pd


def get_stats_dict(ss64: Optional[str]) -> dict:
    """Convert the base64-encoded summary statistics to JSON."""
    if (not ss64) or pd.isna(ss64) or ss64 == "JS1:Short" or ss64 == "JS1:None":
        return {}
    return json.loads(gzip.decompress(base64.b64decode(ss64[4:])))


def cpu_efficiency(ss: dict,
                   elapsedraw: int,
                   jobid: str,
                   cluster: str,
                   single: bool=False,
                   precision: int=1,
                   verbose: bool=True) -> Union[Tuple[Union[int, float], int],
                                                Tuple[int, int, int]]:
    """Return a (CPU time used, CPU time allocated, error code)-tuple for a given job.
       If single=True then return a (CPU time used / CPU time allocated, error code)-tuple.
       The error code is needed since the summary statistics (ss) may be malformed."""
    if 'nodes' not in ss:
        if verbose:
            msg = "Warning: nodes not in ss for cpu_efficiency."
            print(msg, jobid, cluster)
        error_code = 1
        return (-1, error_code) if single else (-1, -1, error_code)
    total = 0
    total_used = 0
    error_code = 0
    for node in ss['nodes']:
        try:
            used  = ss['nodes'][node]['total_time']
            cores = ss['nodes'][node]['cpus']
        except Exception as e:
            if verbose:
                msg = f"Warning: JSON probably missing keys in cpu_efficiency ({e})."
                print(msg, jobid, cluster)
            error_code = 2
            return (-1, error_code) if single else (-1, -1, error_code)
        else:
            alloc = elapsedraw * cores  # equal to cputimeraw
            total += alloc
            total_used += used
    if total_used > total:
        error_code = 3
        if verbose:
            msg = "Warning: total_used > total in cpu_efficiency:"
            print(msg, jobid, cluster, total_used, total)
    if single:
        if total == 0:
            error_code = 4
            return (-1, error_code)
        return (round(100 * total_used / total, precision), error_code)
    return (total_used, total, error_code)


def gpu_efficiency(ss: dict,
                   elapsedraw: int,
                   jobid: str,
                   cluster: str,
                   single: bool=False,
                   precision: int=1,
                   verbose: bool=True) -> Union[Tuple[Union[int, float], int],
                                                Tuple[Union[int, float], int, int]]:
    """Return a (GPU time used, GPU time allocated, error code)-tuple for a given job.
       If single=True then return a (GPU time used / GPU time allocated, error code)-tuple.
       The error code is needed since the summary statistics (ss) may be malformed."""
    if 'nodes' not in ss:
        if verbose:
            msg = "Warning: nodes not in ss for gpu_efficiency."
            print(msg, jobid, cluster)
        error_code = 1
        return (-1, error_code) if single else (-1, -1, error_code)
    total = 0
    total_used = 0
    error_code = 0
    for node in ss['nodes']:
        try:
            gpus = list(ss['nodes'][node]['gpu_utilization'].keys())
        except Exception as e:
            if verbose:
                msg = f"Warning: probably missing keys in gpu_efficiency ({e})."
                print(msg, jobid, cluster)
            error_code = 2
            return (-1, error_code) if single else (-1, -1, error_code)
        else:
            for gpu in gpus:
                util = ss['nodes'][node]['gpu_utilization'][gpu]
                total      += elapsedraw
                total_used += elapsedraw * (float(util) / 100)
    if total_used > total:
        error_code = 3
        if verbose:
            msg = "Warning: total_used > total in gpu_efficiency."
            print(msg, jobid, cluster, total_used, total)
    if single:
        if total == 0:
            error_code = 4
            return (-1, error_code)
        return (round(100 * total_used / total, precision), error_code)
    return (total_used, total, error_code)


def cpu_memory_usage(ss: dict,
                     jobid: str,
                     cluster: str,
                     precision: int=0,
                     verbose: bool=True) -> Tuple[Union[int, float], Union[int, float], int]:
    """Return the total memory used and allocated."""
    if 'nodes' not in ss:
        if verbose:
            msg = "Warning: nodes not in ss for cpu_memory_usage."
            print(msg, jobid, cluster)
        error_code = 1
        return (-1, -1, error_code)
    total = 0
    total_used = 0
    error_code = 0
    for node in ss['nodes']:
        try:
            used  = ss['nodes'][node]['used_memory']
            alloc = ss['nodes'][node]['total_memory']
        except Exception as e:
            if verbose:
                msg = f"Warning: used_memory or total_memory not in ss for cpu_memory_usage ({e})."
                print(msg, jobid, cluster)
            error_code = 2
            return (-1, -1, error_code)
        else:
            total += alloc
            total_used += used
    if total_used > total:
        if verbose:
            print("CPU memory usage > 100%:", jobid, cluster, total_used, total)
        error_code = 3
    fac = 1024**3
    return (round(total_used / fac, precision), round(total / fac, precision), error_code)


def gpu_memory_usage_eff_tuples(ss: dict,
                                jobid: str,
                                cluster: str,
                                precision: int=1,
                                op: Optional[str]=None,
                                verbose: bool=True):
    '''Return a list of tuples for each GPU of the job. Each tuple contains the
       memory used, memory allocated, and GPU utilization. An error code is
       added at the end.

       The choices for the op parameter are:

         1. None: Return tuples of used, allocated, error code for each GPU.

         2. "max": Return tuple of maximum usage per GPU in units of GB and error
                   code, e.g., (42.0, 0). One can also call the specialized version:
                   gpu_memory_usage_max(ss, jobid, cluster, precision=1, verbose=True)

         3. "max-percent": Return tuple of maximum percentage usage per GPU in
                           units of GB and error code, e.g., (85.0, 0). The specialized version is:
                           gpu_memory_usage_max_pct(ss, jobid, cluster, precision=1, verbose=True)

         4. "mean": Return tuple of mean usage over the GPUs in units of GB and
                    error code, e.g., (26.8, 0). One can also call the specialized version:
                    gpu_memory_usage_mean(ss, jobid, cluster, precision=1, verbose=True)

         5. "mean-percent": Return tuple of mean usage percentage over the GPUs
                            and error code, e.g., (87.5, 0). The specialized version is:
                            gpu_memory_usage_mean_pct(ss, jobid, cluster, precision=1, verbose=True)
    '''

    if 'nodes' not in ss:
        if verbose:
            msg = "Warning: nodes not in ss for gpu_memory_usage_eff_tuples."
            print(msg, jobid, cluster)
        error_code = 1
        return ([], error_code)
    all_gpus = []
    error_code = 0
    for node in ss['nodes']:
        try:
            used  = ss['nodes'][node]['gpu_used_memory']
            alloc = ss['nodes'][node]['gpu_total_memory']
            util  = ss['nodes'][node]['gpu_utilization']
        except Exception as e:
            if verbose:
                msg = f"Warning: missing key in ss[nodes][node] for gpu_memory_usage_eff_tuples ({e})."
                print(msg, jobid, cluster)
            error_code = 2
            return ([], error_code)
        else:
            assert sorted(list(used.keys())) == sorted(list(alloc.keys())), "keys do not match"
            for g in used.keys():
                all_gpus.append((round(used[g] / 1024**3, precision),
                                 round(alloc[g] / 1024**3, precision),
                                 float(util[g])))
                if used[g] > alloc[g]:
                    if verbose:
                        print("GPU memory > 100%:", jobid, cluster, used[g], alloc[g])
                    error_code = 3
                if util[g] > 100 or util[g] < 0:
                    if verbose:
                        print("GPU util erroneous:", jobid, cluster, util[g])
                    error_code = 3
    if op == "max":
        return (max([round(item[0], precision) for item in all_gpus]), error_code)
    if op == "max-percent":
        max_pct = max([100 * item[0] / item[1] for item in all_gpus])
        return (round(max_pct, precision), error_code)
    if op == "mean":
        mean_usage = sum([item[0] for item in all_gpus]) / len(all_gpus)
        return (round(mean_usage, precision), error_code)
    if op == "mean-percent":
        mean_pct = sum([100 * item[0] / item[1] for item in all_gpus]) / len(all_gpus)
        return (round(mean_pct, precision), error_code)
    return (all_gpus, error_code)

gpu_memory_usage_max = partial(gpu_memory_usage_eff_tuples, op="max")
gpu_memory_usage_max_pct = partial(gpu_memory_usage_eff_tuples, op="max-percent")
gpu_memory_usage_mean = partial(gpu_memory_usage_eff_tuples, op="mean")
gpu_memory_usage_mean_pct = partial(gpu_memory_usage_eff_tuples, op="mean-percent")

def max_cpu_memory_used_per_node(ss: dict,
                                 jobid: str,
                                 cluster: str,
                                 precision: int=0,
                                 verbose: bool=True) -> Tuple[Union[int, float], int]:
    """Return the maximum of the used memory per node. The error code is needed
       since the summary statistics (ss) may be malformed."""
    if 'nodes' not in ss:
        if verbose:
            msg = "Warning: nodes not in ss for max_cpu_memory_used_per_node."
            print(msg, jobid, cluster)
        error_code = 1
        return (-1, error_code)
    total = 0
    total_used = 0
    error_code = 0
    mem_per_node = []
    for node in ss['nodes']:
        try:
            used  = ss['nodes'][node]['used_memory']
            alloc = ss['nodes'][node]['total_memory']
        except Exception as e:
            if verbose:
                msg = ("Warning: used_memory or total_memory not in ss for "
                       f"max_cpu_memory_used_per_node ({e}).")
                print(msg, jobid, cluster)
            error_code = 2
            return (-1, error_code)
        else:
            mem_per_node.append(used)
            if used > alloc:
                if verbose:
                    msg = "Warning: CPU memory used > 100% in max_cpu_memory_used_per_node."
                    print(msg, jobid, cluster, total_used, total)
                error_code = 3
    return (round(max(mem_per_node) / 1024**3, precision), error_code)


def num_gpus_with_zero_util(ss: dict,
                            jobid: str,
                            cluster: str,
                            verbose: bool=True) -> Tuple[int, int]:
    """Return the number of GPUs with zero utilization. The error code is needed
       since the summary statistics (ss) may be malformed."""
    if 'nodes' not in ss:
        if verbose:
            msg = "Warning: nodes not in ss for num_gpus_with_zero_util."
            print(msg, jobid, cluster)
        error_code = 1
        return (-1, error_code)
    ct = 0
    for node in ss['nodes']:
        try:
            gpus = list(ss['nodes'][node]['gpu_utilization'].keys())
        except Exception as e:
            if verbose:
                msg = f"gpu_utilization not found: node is {node} for num_gpus_with_zero_util ({e})."
                print(msg, jobid, cluster)
            error_code = 2
            return (-1, error_code)
        else:
            for gpu in gpus:
                util = ss['nodes'][node]['gpu_utilization'][gpu]
                if float(util) == 0:
                    ct += 1
    error_code = 0
    return (ct, error_code)


def cpu_nodes_with_zero_util(ss: dict,
                             jobid: str,
                             cluster: str,
                             verbose: bool=True) -> Tuple[int, int]:
    """Return the number of nodes with zero CPU utilization. The error code is needed
       since the summary statistics (ss) may be malformed."""
    if 'nodes' not in ss:
        if verbose:
            msg = "Warning: nodes not in ss for cpu_nodes_with_zero_util."
            print(msg, jobid, cluster)
        error_code = 1
        return (-1, error_code)
    counter = 0
    for node in ss['nodes']:
        if 'total_time' in ss['nodes'][node]:
            cpu_time = ss['nodes'][node]['total_time']
            if float(cpu_time) == 0:
                counter += 1
        else:
            if verbose:
                msg = f"total_time not found for node {node} in cpu_nodes_with_zero_util."
                print(msg)
            error_code = 2
            return (-1, error_code)
    error_code = 0
    return (counter, error_code)


def get_nodelist(ss: dict,
                 jobid: str,
                 cluster: str,
                 verbose: bool=True) -> Tuple[Set[str], int]:
    """Return a Python set of the node names used by the job."""
    if 'nodes' not in ss:
        if verbose:
            msg = "Warning: nodes not found in ss for get_nodelist."
            print(msg, jobid, cluster)
        error_code = 1
        return (set(), error_code)
    return (set(ss['nodes'].keys()), 0)
