import pandas as pd
from src.job_defense_shield.alert.zero_cpu_utilization import ZeroCPU

def test_zero_cpu_utilization():
    n_jobs = 5
    wallclock_secs = 36000
    wallclock_hrs = wallclock_secs / 3600
    # job1 has 3 unused nodes
    job1 = {
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
    "total_time": -1}
    # job2 has 1 unused node
    job2 = {
    "gpus": 0,
    "nodes": {
        "della-r2c2n1": {
            "cpus": 22,
            "total_memory": 94489280512,
            "total_time": 479803.9,
            "used_memory": 192434176
        },
        "della-r2c2n8": {
            "cpus": 10,
            "total_memory": 42949672960,
            "total_time": 0.0,
            "used_memory": 253952
        }
    },
    "total_time": -1}
    # job3 has 0 unused nodes
    job3 = {
    "gpus": 0,
    "nodes": {
        "stellar-i01n7": {
            "cpus": 64,
            "total_memory": 503316480000,
            "total_time": 1466860.0,
            "used_memory": 20648779776
        },
        "stellar-i05n15": {
            "cpus": 96,
            "total_memory": 754974720000,
            "total_time": 2196739.0,
            "used_memory": 30826430464
        },
        "stellar-i07n3": {
            "cpus": 96,
            "total_memory": 754974720000,
            "total_time": 2200431.5,
            "used_memory": 30853967872
        }
    },
    "total_time": -1}
    df = pd.DataFrame({"jobid":["1234567"] * n_jobs,
                       "user":["user1", "user1", "user2", "user1", "user2"],
                       "admincomment":[job1, job2, job3, job2, job1],
                       "cluster":["della"] * n_jobs,
                       "jobname":["myjob"] * n_jobs,
                       "nodes":[4, 2, 3, 2, 4],
                       "cores":[42] * n_jobs,
                       "state":["COMPLETED"] * n_jobs,
                       "partition":["cpu"] * n_jobs,
                       "elapsed-hours":[round(wallclock_hrs)] * n_jobs})
    zero_cpu = ZeroCPU(df,
                       0,
                       "",
                       "",
                       cluster="della",
                       partitions=["cpu"],
                       min_run_time=0,
                       include_running_jobs=False)
    actual = zero_cpu.df[["User", "Nodes", "Nodes-Unused"]]
    expected = pd.DataFrame({"User":["user1", "user1", "user1", "user2"],
                             "Nodes":[4, 2, 2, 4],
                             "Nodes-Unused":[3, 1, 1, 3]})
    pd.testing.assert_frame_equal(actual.reset_index(drop=True), expected)
