import pandas as pd
from src.job_defense_shield.alert.multinode_cpu_fragmentation import MultinodeCpuFragmentation

def test_zero_cpu_utilization():
    n_jobs = 5
    wallclock_secs = 36000
    wallclock_hrs = wallclock_secs / 3600
    # job1 using 12 nodes but only needed 3
    job1 = {
    "gpus": 0,
    "nodes": {
        "della-r3c1n1": {
            "cpus": 8,
            "total_memory": 34359738368,
            "total_time": 3069743.0,
            "used_memory": 2254557184
        },
        "della-r3c1n10": {
            "cpus": 8,
            "total_memory": 34359738368,
            "total_time": 3068821.6,
            "used_memory": 2255003648
        },
        "della-r3c1n11": {
            "cpus": 8,
            "total_memory": 34359738368,
            "total_time": 3070090.7,
            "used_memory": 2268618752
        },
        "della-r3c1n13": {
            "cpus": 8,
            "total_memory": 34359738368,
            "total_time": 3070005.1,
            "used_memory": 2242101248
        },
        "della-r3c1n14": {
            "cpus": 8,
            "total_memory": 34359738368,
            "total_time": 3071471.4,
            "used_memory": 2248933376
        },
        "della-r3c1n2": {
            "cpus": 8,
            "total_memory": 34359738368,
            "total_time": 3070831.9,
            "used_memory": 2252320768
        },
        "della-r3c1n3": {
            "cpus": 8,
            "total_memory": 34359738368,
            "total_time": 3070803.3,
            "used_memory": 2251907072
        },
        "della-r3c1n4": {
            "cpus": 8,
            "total_memory": 34359738368,
            "total_time": 3069166.8,
            "used_memory": 2242482176
        },
        "della-r3c1n5": {
            "cpus": 8,
            "total_memory": 34359738368,
            "total_time": 3071824.9,
            "used_memory": 2243297280
        },
        "della-r3c1n6": {
            "cpus": 8,
            "total_memory": 34359738368,
            "total_time": 3068581.2,
            "used_memory": 2252861440
        },
        "della-r3c1n7": {
            "cpus": 8,
            "total_memory": 34359738368,
            "total_time": 3070968.1,
            "used_memory": 2245701632
        },
        "della-r3c1n9": {
            "cpus": 8,
            "total_memory": 34359738368,
            "total_time": 3068686.2,
            "used_memory": 2243059712
        }
    },
    "total_time": 385350}
    # job2 used 5 nodes but only needed 2
    job2 = {
    "gpus": 0,
    "nodes": {
        "della-r1c3n1": {
            "cpus": 15,
            "total_memory": 48318382080,
            "total_time": 30228.2,
            "used_memory": 34616541184
        },
        "della-r1c3n3": {
            "cpus": 4,
            "total_memory": 12884901888,
            "total_time": 7957.8,
            "used_memory": 9180938240
        },
        "della-r1c3n4": {
            "cpus": 21,
            "total_memory": 67645734912,
            "total_time": 41854.6,
            "used_memory": 43962712064
        },
        "della-r1c3n5": {
            "cpus": 5,
            "total_memory": 16106127360,
            "total_time": 10034.0,
            "used_memory": 11322843136
        },
        "della-r1c3n6": {
            "cpus": 5,
            "total_memory": 16106127360,
            "total_time": 9975.2,
            "used_memory": 11565367296
        }
    },
    "total_time": 2128}
    # job3 used 4 nodes but only needed 3
    job3 = {
    "gpus": 0,
    "nodes": {
        "della-k07n1": {
            "cpus": 15,
            "total_memory": 188316480000,
            "total_time": 102891.8,
            "used_memory": 16010821632
        },
        "della-k08n13": {
            "cpus": 15,
            "total_memory": 188316480000,
            "total_time": 103767.0,
            "used_memory": 15985602560
        },
        "della-k08n15": {
            "cpus": 15,
            "total_memory": 188316480000,
            "total_time": 102738.4,
            "used_memory": 15996280832
        },
        "della-k08n16": {
            "cpus": 15,
            "total_memory": 188316480000,
            "total_time": 102978.1,
            "used_memory": 15978323968
        }
    },
    "total_time": 1814}
    # job needed both nodes due to memory so should be ignored
    job4 = {
    "gpus": 0,
    "nodes": {
        "stellar-k07n2": {
            "cpus": 30,
            "total_memory": 786432000000,
            "total_time": 3243997.8,
            "used_memory": 595096285184
        },
        "stellar-k07n3": {
            "cpus": 30,
            "total_memory": 786432000000,
            "total_time": 3242042.3,
            "used_memory": 595858452480
        }
    },
    "total_time": 109591}
    # job has 0% cpu utilization so should be ignored
    job5 = {
    "gpus": 0,
    "nodes": {
        "della-r2c4n1": {
            "cpus": 12,
            "total_memory": 51539607552,
            "total_time": 261687.6,
            "used_memory": 162549760
        },
        "della-r2c4n2": {
            "cpus": 20,
            "total_memory": 85899345920,
            "total_time": 0.0,
            "used_memory": 245760
        },
        "della-r2c4n3": {
            "cpus": 30,
            "total_memory": 128849018880,
            "total_time": 0.0,
            "used_memory": 249856
        },
        "della-r2c4n4": {
            "cpus": 2,
            "total_memory": 8589934592,
            "total_time": 0.0,
            "used_memory": 241664
        }
    },
    "total_time": 21913}

    df = pd.DataFrame({"jobid":["1234567"] * n_jobs,
                       "user":["user1", "user1", "user2", "user3", "user2"],
                       "admincomment":[job1, job2, job3, job4, job5],
                       "cluster":["della"] * n_jobs,
                       "jobname":["myjob"] * n_jobs,
                       "nodes":[12, 5, 4, 2, 4],
                       "cores":[96, 50, 60, 60, 64],
                       "state":["COMPLETED"] * n_jobs,
                       "gpus":[0] * n_jobs,
                       "partition":["cpu"] * n_jobs,
                       "elapsed-hours":[round(wallclock_hrs)] * n_jobs})
    cpu_frag = MultinodeCpuFragmentation(df,
                                         0,
                                         "",
                                         "",
                                         cluster="della",
                                         partitions=["cpu"],
                                         min_run_time=0,
                                         cores_per_node=32,
                                         cores_fraction=0.8,
                                         mem_per_node=190,
                                         safety_fraction=0.2)
    actual = cpu_frag.df[["user", "cluster", "nodes", "min-nodes"]]
    expected = pd.DataFrame({"user":["user1", "user1", "user2"],
                             "cluster":["della", "della", "della"],
                             "nodes":[12, 5, 4],
                             "min-nodes":[3, 2, 2]})
    pd.testing.assert_frame_equal(actual.reset_index(drop=True), expected)
