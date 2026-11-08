import pandas as pd
from job_defense_shield.alert.high_util_but_low_sm import HighUtilButLowSM

def test_high_util_but_low_sm():
    n_jobs = 6
    # job1: GPU util is 96, SM util is 14, 100 GPU-hours
    job1 = {
        "gpus": 1,
        "nodes": {
            "della-l05g2": {
                "cpus": 1,
                "gpu_utilization": {
                    "0": 96.0
                },
                "sm_util_percent_avg": {
                    "0": 0.14
                },
                "total_memory": -1,
                "total_time": -1,
                "used_memory": -1
            }
        },
        "total_time": -1
    }
    # job2 will be excluded because 88 - 50 < 50
    job2 = {
        "gpus": 1,
        "nodes": {
            "della-l05g2": {
                "cpus": 1,
                "gpu_total_memory": {
                    "0": -1
                },
                "gpu_used_memory": {
                    "0": -1
                },
                "gpu_utilization": {
                    "0": 88.0
                },
                "sm_util_percent_avg": {
                    "0": 0.5
                },
                "total_memory": -1,
                "total_time": -1,
                "used_memory": -1
            }
        },
        "total_time": -1
    }
    # job3: GPU util is 94, SM util is 10, 100 GPU-hours
    job3 = {
        "gpus": 1,
        "nodes": {
            "della-l05g2": {
                "cpus": 1,
                "gpu_total_memory": {
                    "0": -1
                },
                "gpu_used_memory": {
                    "0": -1
                },
                "gpu_utilization": {
                    "0": 94.0
                },
                "sm_util_percent_avg": {
                    "0": 0.1
                },
                "total_memory": -1,
                "total_time": -1,
                "used_memory": -1
            }
        },
        "total_time": -1
    }
    # job4: GPU util is 90, SM util is 10, 300 GPU-hours
    job4 = {
        "gpus": 3,
        "nodes": {
            "della-k12g2": {
                "cpus": 6,
                "gpu_utilization": {
                    "0": 95.0,
                    "1": 85.0,
                    "2": 90.0
                },
                "sm_util_percent_avg": {
                    "0": 0.1,
                    "1": 0.1,
                    "2": 0.1
                },
                "total_memory": -1,
                "total_time": -1,
                "used_memory": -1
            }
        },
        "total_time": -1
    }
    # job5 is intentionally missing sm_util_percent_avg so excluded
    job5 = {
        "gpus": 2,
        "nodes": {
            "della-k12g2": {
                "cpus": 6,
                "gpu_total_memory": {
                    "0": 85520809984,
                    "1": 85520809984
                },
                "gpu_used_memory": {
                    "0": 1_000_000_000,
                    "1": 2_000_000_000
                },
                "gpu_utilization": {
                    "0": 95.0,
                    "1": 85.0
                },
                "total_memory": -1,
                "total_time": -1,
                "used_memory": -1
            }
        },
        "total_time": -1
    }
    # job6 will be excluded since GPU util is too low
    job6 = {
        "gpus": 2,
        "nodes": {
            "della-k12g2": {
                "cpus": 6,
                "gpu_total_memory": {
                    "0": 85520809984,
                    "1": 85520809984
                },
                "gpu_used_memory": {
                    "0": 1_000_000_000,
                    "1": 2_000_000_000
                },
                "gpu_utilization": {
                    "0": 65.0,
                    "1": 55.0
                },
                "sm_util_percent_avg": {
                    "0": 0.05,
                    "1": 0.05
                },
                "total_memory": -1,
                "total_time": -1,
                "used_memory": -1
            }
        },
        "total_time": -1
    }

    df = pd.DataFrame({"jobid": ["1", "2", "3", "4", "5", "6"],
                       "user": ["user1", "user2", "user1", "user2", "user1", "user3"],
                       "admincomment": [job1, job2, job3, job4, job5, job6],
                       "cluster": ["della"] * n_jobs,
                       "gpus":  [1, 1, 1, 3, 2, 2],
                       "state": ["COMPLETED"] * n_jobs,
                       "partition": ["gpu"] * n_jobs,
                       "elapsedraw": [360000] * n_jobs,
                       "qos": ["short"] * n_jobs,
                       "elapsed-hours": [100] * n_jobs})
    low_sm = HighUtilButLowSM(df,
                              0,
                              "",
                              "",
                              cluster="della",
                              partitions=["gpu"],
                              min_run_time=0,
                              gpu_hours_thres_user=0,
                              gpu_hours_thres_admin=0,
                              util_thres_pct=70,
                              util_minus_sm_pct=50,
                              sm_thres_pct=15,
                              verbose=False,
                              excluded_users=["aturing"])
    actual = low_sm.admin
    expected = pd.DataFrame({"User": ["user2", "user1"],
                             "GPU-Hours": [300, 200],
                             "GPU-Util": [90, 95],
                             "SM-Util": [10, 12],
                             "Jobs": [1, 2],
                             "JobID": ["4", "3,1"]})
    pd.testing.assert_frame_equal(actual.reset_index(drop=True), expected)
