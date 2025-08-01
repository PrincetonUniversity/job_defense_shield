from efficiency import get_stats_dict
from efficiency import cpu_efficiency
from efficiency import gpu_efficiency
from efficiency import cpu_memory_usage
from efficiency import gpu_memory_usage_eff_tuples
from efficiency import gpu_memory_usage_max
from efficiency import gpu_memory_usage_max_pct
from efficiency import gpu_memory_usage_mean
from efficiency import gpu_memory_usage_mean_pct
from efficiency import max_cpu_memory_used_per_node
from efficiency import num_gpus_with_zero_util
from efficiency import cpu_nodes_with_zero_util
from efficiency import get_nodelist
import numpy as np


def test_null_summary_statistics():
    x = None
    assert get_stats_dict(x) == {}
    x = np.nan
    assert get_stats_dict(x) == {}
    x = ""
    assert get_stats_dict(x) == {}
    x = "JS1:Short"
    assert get_stats_dict(x) == {}
    x = "JS1:None"
    assert get_stats_dict(x) == {}


def test_summary_statistics():
    x = ("H4sIAO5E8GYC/1XNwQqDMBAE0H/Zc5TETdZNfqYUXVQwRjQeiuTfKwqFXufNMCcsqZcdw"
         "gl5GmSrxoY6s/AdpPyeX1Fi2j4Q0KLzLTISKzh26X9iuLEWvdP6kmeUpygQyPvWmpoUdO"
         "txfXAp/wVmJqdguFWXL6wSiAONAAAA")
    x = f"JS1:{x}"
    actual = get_stats_dict(x)
    expected = {"gpus": 0,
                "nodes": {"tiger-h26c1n8":
                                         {"cpus": 8,
                                          "total_memory": 34359738368,
                                          "total_time": 699741.6,
                                          "used_memory": 18244395008}},
                "total_time": 88865}
    assert actual == expected


def test_malformed_cpu_efficiency():
    # empty summary statistics
    ss = {}
    assert cpu_efficiency(ss, 100, 12345, "c1", verbose=False) == (-1, -1, 1)
    # missing cpus key
    ss = {"nodes":{"node1":{"total_time":42}}}
    assert cpu_efficiency(ss, 100, 12345, "c1", verbose=False) == (-1, -1, 2)
    # efficiency greater than 100%
    ss = {"nodes":{"node1":{"total_time":4200, "cpus":8}}}
    assert cpu_efficiency(ss, 100, 12345, "c1", verbose=False) == (4200, 100 * 8, 3)


def test_cpu_efficiency():
    ss = {"nodes":{"node1":{"total_time":42, "cpus":8}}}
    assert cpu_efficiency(ss, 100, 12345, "c1", verbose=False) == (42, 100 * 8, 0)
    ss = {"nodes":{"node1":{"total_time":42, "cpus":8},
                   "node2":{"total_time":42, "cpus":8}}}
    assert cpu_efficiency(ss, 100, 12345, "c1", verbose=False) == (42 + 42, 2 * 100 * 8, 0)
    eff = round(100 * 42 / 100 / 8, 1)
    assert cpu_efficiency(ss, 100, 12345, "c1", single=True, verbose=False) == (eff, 0)
 

def test_malformed_gpu_efficiency():
    # empty summary statistics
    ss = {}
    assert gpu_efficiency(ss, 100, 12345, "c1", verbose=False) == (-1, -1, 1)
    # missing gpu_utilization key
    ss = {"nodes":{"node1":{"total_time": 42}}}
    assert gpu_efficiency(ss, 100, 12345, "c1", single=True, verbose=False) == (-1, 2)
    # efficiency greather than 100%
    ss = {"nodes":{"node1":{"gpu_utilization":{0: 101}}}}
    assert gpu_efficiency(ss, 100, 12345, "c1", verbose=False) == (101, 100, 3)


def test_gpu_efficiency():
    ss = {"nodes":{"node1":{"gpu_utilization":{0: 95}}}}
    assert gpu_efficiency(ss, 100, 12345, "c1", single=True, verbose=False) == (95, 0)
    ss = {"nodes":{"node1":{"gpu_utilization":{0: 95}}}}
    assert gpu_efficiency(ss, 100, 12345, "c1", verbose=False) == (95, 100, 0)
    ss = {"nodes":{"node1":{"gpu_utilization":{0: 95, 1:65}}}}
    assert gpu_efficiency(ss, 100, 12345, "c1", single=True, verbose=False) == (80, 0)
    ss = {"nodes":{"node1":{"gpu_utilization":{0: 95, 1:65}}}}
    assert gpu_efficiency(ss, 100, 12345, "c1", verbose=False) == (95 + 65, 2 * 100, 0)


def test_malformed_cpu_memory_usage():
    # empty summary statistics
    ss = {}
    assert cpu_memory_usage(ss, 12345, "c1") == (-1, -1, 1)
    # missing total_memory key
    ss = {"nodes":{"node1":{"used_memory": 42}}}
    assert cpu_memory_usage(ss, 12345, "c1") == (-1, -1, 2)
    # memory greater than 100%
    used = 20_000_000_000
    total = 10_000_000_000
    ss = {"nodes":{"node1":{"used_memory": used,
                            "total_memory": total}}}
    fac = 1024**3
    assert cpu_memory_usage(ss, 12345, "c1") == (round(used / fac), round(total / fac), 3)
    

def test_cpu_memory_usage():
    # one node
    used = 42_000_000_000
    total = 100_000_000_000
    ss = {"nodes":{"node1":{"used_memory": used,
                            "total_memory": total}}}
    fac = 1024**3
    assert cpu_memory_usage(ss, 12345, "c1") == (round(used / fac), round(total / fac), 0)
    # two nodes
    used1 = 42_000_000_000
    used2 = 62_000_000_000
    total = 100_000_000_000
    ss = {"nodes":{"node1":{"used_memory": used1,
                            "total_memory": total},
                   "node2":{"used_memory": used2,
                            "total_memory": total}}}
    fac = 1024**3
    assert cpu_memory_usage(ss, 12345, "c1") == (round((used1 + used2) / fac),
                                                 round(2 * total / fac), 0)


def test_malformed_gpu_memory_usage_eff_tuples():
    # empty summary statistics
    ss = {}
    assert gpu_memory_usage_eff_tuples(ss, 12345, "c1", verbose=False) == ([], 1)
    # missing gpu_total_memory key
    ss = {"nodes":{"node1":{"gpu_used_memory": {1: 0},
                            "gpu_utilization": {1: 0}}}}
    assert gpu_memory_usage_eff_tuples(ss, 12345, "c1", verbose=False) == ([], 2)
    # memory usage greater than 100%
    fac = 1024**3
    ss = {"nodes":{"node1":{"gpu_used_memory": {1: 81 * fac},
                            "gpu_total_memory": {1: 80 * fac},
                            "gpu_utilization": {1: 95}}}}
    actual = gpu_memory_usage_eff_tuples(ss, 12345, "c1", verbose=False)
    expected = ([(81.0, 80.0, 95.0)], 3)
    assert actual == expected
 

def test_gpu_memory_usage_eff_tuples():
    used = 42 * 1024**3
    total = 80 * 1024**3
    ss = {"nodes":{"node1":{"gpu_used_memory": {0: used},
                            "gpu_total_memory": {0: total},
                            "gpu_utilization": {0: 95}}}}
    assert gpu_memory_usage_eff_tuples(ss, 12345, "c1") == ([(42.0, 80.0, 95.0)], 0)
    used1 = 42 * 1024**3
    used2 = 62 * 1024**3
    total = 80 * 1024**3
    ss = {"nodes":{"node1":{"gpu_used_memory": {0: used1},
                            "gpu_total_memory": {0: total},
                            "gpu_utilization": {0: 95}},
                   "node2":{"gpu_used_memory": {3: used2},
                            "gpu_total_memory": {3: total},
                            "gpu_utilization": {3: 85}}}}
    actual = gpu_memory_usage_eff_tuples(ss, 12345, "c1")
    expected = ([(42.0, 80.0, 95.0), (62.0, 80.0, 85.0)], 0)
    assert actual == expected


def test_gpu_memory_usage_max():
    used = 42 * 1024**3
    total = 80 * 1024**3
    ss = {"nodes":{"node1":{"gpu_used_memory": {0: used},
                            "gpu_total_memory": {0: total},
                            "gpu_utilization": {0: 95}}}}
    assert gpu_memory_usage_max(ss, 12345, "c1") == (42.0, 0)
    used1 = 42 * 1024**3
    used2 = 62 * 1024**3
    total = 80 * 1024**3
    ss = {"nodes":{"node1":{"gpu_used_memory": {0: used1},
                            "gpu_total_memory": {0: total},
                            "gpu_utilization": {0: 95}},
                   "node2":{"gpu_used_memory": {3: used2},
                            "gpu_total_memory": {3: total},
                            "gpu_utilization": {3: 85}}}}
    actual = gpu_memory_usage_max(ss, 12345, "c1")
    expected = (62.0, 0)
    assert actual == expected


def test_gpu_memory_usage_max_pct():
    used = 42 * 1024**3
    total = 80 * 1024**3
    ss = {"nodes":{"node1":{"gpu_used_memory": {0: used},
                            "gpu_total_memory": {0: total},
                            "gpu_utilization": {0: 95}}}}
    assert gpu_memory_usage_max_pct(ss, 12345, "c1") == (52.5, 0)
    used1 = 42 * 1024**3
    used2 = 62 * 1024**3
    total = 80 * 1024**3
    ss = {"nodes":{"node1":{"gpu_used_memory": {0: used1},
                            "gpu_total_memory": {0: total},
                            "gpu_utilization": {0: 95}},
                   "node2":{"gpu_used_memory": {3: used2},
                            "gpu_total_memory": {3: total},
                            "gpu_utilization": {3: 85}}}}
    actual = gpu_memory_usage_max_pct(ss, 12345, "c1")
    expected = (77.5, 0)
    assert actual == expected


def test_gpu_memory_usage_mean():
    used = 42 * 1024**3
    total = 80 * 1024**3
    ss = {"nodes":{"node1":{"gpu_used_memory": {0: used},
                            "gpu_total_memory": {0: total},
                            "gpu_utilization": {0: 95}}}}
    assert gpu_memory_usage_mean(ss, 12345, "c1") == (42.0, 0)
    used1 = 42 * 1024**3
    used2 = 62 * 1024**3
    total = 80 * 1024**3
    ss = {"nodes":{"node1":{"gpu_used_memory": {0: used1},
                            "gpu_total_memory": {0: total},
                            "gpu_utilization": {0: 95}},
                   "node2":{"gpu_used_memory": {3: used2},
                            "gpu_total_memory": {3: total},
                            "gpu_utilization": {3: 85}}}}
    actual = gpu_memory_usage_mean(ss, 12345, "c1")
    expected = (52.0, 0)
    assert actual == expected


def test_gpu_memory_usage_mean_pct():
    used = 42 * 1024**3
    total = 80 * 1024**3
    ss = {"nodes":{"node1":{"gpu_used_memory": {0: used},
                            "gpu_total_memory": {0: total},
                            "gpu_utilization": {0: 95}}}}
    assert gpu_memory_usage_mean_pct(ss, 12345, "c1") == (52.5, 0)
    used1 = 42 * 1024**3
    used2 = 62 * 1024**3
    total = 80 * 1024**3
    ss = {"nodes":{"node1":{"gpu_used_memory": {0: used1},
                            "gpu_total_memory": {0: total},
                            "gpu_utilization": {0: 95}},
                   "node2":{"gpu_used_memory": {3: used2},
                            "gpu_total_memory": {3: total},
                            "gpu_utilization": {3: 85}}}}
    actual = gpu_memory_usage_mean_pct(ss, 12345, "c1")
    expected = (65.0, 0)
    assert actual == expected


def test_malformed_max_cpu_memory_used_per_node():
    # empty summary statistics
    ss = {}
    assert max_cpu_memory_used_per_node(ss, 12345, "c1", verbose=False) == (-1, 1)
    # missing "used_memory" key
    ss = {"nodes":{"node1":{"cpus": 8, "total_memory": 100 * 1024**3}}}
    assert max_cpu_memory_used_per_node(ss, 12345, "c1", verbose=False) == (-1, 2)
    # used greater than total
    ss = {"nodes":{"node1":{"cpus": 8,
                            "used_memory": 100 * 1024**3,
                            "total_memory": 42 * 1024**3}}}
    assert max_cpu_memory_used_per_node(ss, 12345, "c1", verbose=False) == (100.0, 3)


def test_max_cpu_memory_used_per_node():
    # single node
    ss = {"nodes":{"node1":{"cpus": 8,
                            "used_memory": 42 * 1024**3,
                            "total_memory": 100 * 1024**3}}}
    assert max_cpu_memory_used_per_node(ss, 12345, "c1", verbose=False) == (42.0, 0)
    # multiple nodes
    ss = {"nodes":{"node1":{"cpus": 8,
                            "used_memory": 42 * 1024**3,
                            "total_memory": 100 * 1024**3},
                   "node2":{"cpus": 8,
                            "used_memory": 43 * 1024**3,
                            "total_memory": 100 * 1024**3}}}
    assert max_cpu_memory_used_per_node(ss, 12345, "c1", verbose=False) == (43.0, 0)

def test_malformed_num_gpus_with_zero_util():
    # empty summary statistics
    ss = {}
    assert num_gpus_with_zero_util(ss, 12345, "c1", verbose=False) == (-1, 1)
    # missing gpu_utilization key
    ss = {"nodes":{"node1":{"gpu_used_memory": {0: 0},
                            "gpu_total_memory": {0: 0}}}}
    assert num_gpus_with_zero_util(ss, 12345, "c1", verbose=False) == (-1, 2)


def test_num_gpus_with_zero_util():
    ss = {"nodes":{"node1":{"gpu_used_memory": {0: 0},
                            "gpu_total_memory": {0: 0},
                            "gpu_utilization": {0: 95}}}}
    assert num_gpus_with_zero_util(ss, 12345, "c1") == (0, 0)
    # three allocated gpus over two nodes
    ss = {"nodes":{"node1":{"gpu_used_memory": {0: 0},
                            "gpu_utilization": {0: 95}},
                   "node2":{"gpu_used_memory": {3: 0, 4: 0},
                            "gpu_utilization": {3: 0, 4: 0}}}}
    actual = num_gpus_with_zero_util(ss, 12345, "c1")
    expected = (2, 0)
    assert actual == expected


def test_malformed_num_cpu_nodes_with_zero_util():
    # empty summary statistics
    ss = {}
    assert cpu_nodes_with_zero_util(ss, 12345, "c1", verbose=False) == (-1, 1)
    # missing total_time key
    ss = {"nodes":{"node1":{"cpus": 8}}}
    assert cpu_nodes_with_zero_util(ss, 12345, "c1", verbose=False) == (-1, 2)


def test_num_cpu_nodes_with_zero_util():
    # one node
    ss = {"nodes":{"node1":{"total_time": 100}}}
    assert cpu_nodes_with_zero_util(ss, 12345, "c1") == (0, 0)
    # one node
    ss = {"nodes":{"node1":{"total_time": 0, "cpus": 8}}}
    assert cpu_nodes_with_zero_util(ss, 12345, "c1") == (1, 0)
    # four nodes
    ss = {"nodes":{"node1":{"total_time": 100},
                   "node2":{"total_time": 0},
                   "node3":{"total_time": 0},
                   "node4":{"total_time": 100}}}
    actual = cpu_nodes_with_zero_util(ss, 12345, "c1")
    expected = (2, 0)
    assert actual == expected


def test_get_nodelist():
    # single node without nodes
    ss = {}
    assert get_nodelist(ss, 12345, "c1", verbose=False) == (set(), 1)
    # single node
    ss = {"nodes":{"node1":{"cpus": 8,
                            "used_memory": 42 * 1024**3,
                            "total_memory": 100 * 1024**3}}}
    assert get_nodelist(ss, 12345, "c1", verbose=False) == (set(["node1"]), 0)
    # multiple nodes
    ss = {"nodes":{"node1":{"cpus": 8,
                            "used_memory": 42 * 1024**3,
                            "total_memory": 100 * 1024**3},
                   "node2":{"cpus": 8,
                            "used_memory": 43 * 1024**3,
                            "total_memory": 100 * 1024**3}}}
    assert get_nodelist(ss, 12345, "c1", verbose=False) == (set(["node1", "node2"]), 0)
