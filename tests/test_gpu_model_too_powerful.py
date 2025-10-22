import pandas as pd
from src.job_defense_shield.alert.gpu_model_too_powerful import GpuModelTooPowerful

def test_gpu_model_too_powerful():
    n_jobs = 6
    job1 = {
        "gpus": 1,
        "nodes": {
            "della-l05g2": {
                "cpus": 1,
                "gpu_total_memory": {
                    "0": 85899345920
                },
                "gpu_used_memory": {
                    "0": 78096302080
                },
                "gpu_utilization": {
                    "0": 80.6
                },
                "total_memory": 17179869184,
                "total_time": 42029.4,
                "used_memory": 4032090112
            }
        },
        "total_time": 42151.20111846924
    }
    job2 = {
        "gpus": 1,
        "nodes": {
            "della-l05g2": {
                "cpus": 1,
                "gpu_total_memory": {
                    "0": 85899345920
                },
                "gpu_used_memory": {
                    "0": 7809630208
                },
                "gpu_utilization": {
                    "0": 8.6
                },
                "total_memory": 17179869184,
                "total_time": 42029.4,
                "used_memory": 4032090112
            }
        },
        "total_time": 42151.20111846924
    }
    job3 = {
        "gpus": 1,
        "nodes": {
            "della-l05g2": {
                "cpus": 1,
                "gpu_total_memory": {
                    "0": 85899345920
                },
                "gpu_used_memory": {
                    "0":5368709120
                },
                "gpu_utilization": {
                    "0": 6.0
                },
                "total_memory": 17179869184,
                "total_time": 42029.4,
                "used_memory": 4032090112
            }
        },
        "total_time": 42151.20111846924
    }
    job4 = {
        "gpus": 6,
        "nodes": {
            "della-k12g2": {
                "cpus": 6,
                "gpu_total_memory": {
                    "0": 85520809984,
                    "1": 85520809984,
                    "3": 85520809984,
                    "4": 85520809984,
                    "5": 85520809984,
                    "7": 85520809984
                },
                "gpu_used_memory": {
                    "0": 1_000_000_000,
                    "1": 2_000_000_000,
                    "3": 3_000_000_000,
                    "4": 4_000_000_000,
                    "5": 5_000_000_000,
                    "7": 6_000_000_000
                },
                "gpu_utilization": {
                    "0": 4.0,
                    "1": 5.0,
                    "3": 6.0,
                    "4": 7.0,
                    "5": 8.0,
                    "7": 9.0
                },
                "total_memory": 536870912000,
                "total_time": 1307788.3,
                "used_memory": 30_000_000_000
            }
        },
        "total_time": 223308
    }

    df = pd.DataFrame({"jobid":["1234567"] * n_jobs,
                       "user":["user1", "user1", "user2", "user1", "user2", "user3"],
                       "admincomment":[job1, job2, job3, job2, job1, job4],
                       "cluster":["della"] * n_jobs,
                       "cores":[1] * n_jobs,
                       "gpus": [1, 1, 1, 1, 1, 6],
                       "state":["COMPLETED"] * n_jobs,
                       "partition":["gpu"] * n_jobs,
                       "qos":["short"] * n_jobs,
                       "elapsed-hours":[100] * n_jobs})
    too_power = GpuModelTooPowerful(df,
                                    0,
                                    "",
                                    "",
                                    cluster="della",
                                    partitions=["gpu"],
                                    min_run_time=0,
                                    num_cores_per_gpu=1,
                                    gpu_hours_threshold=24,
                                    gpu_util_threshold=15,
                                    gpu_mem_usage_max=10,
                                    cpu_mem_usage_per_gpu=32,
                                    verbose=True,
                                    excluded_users=["aturing"])
    actual = too_power.df[["User",
                           "GPU-Util",
                           "GPU-Mem-Used-Max",
                           "CPU-Mem-Used/GPU ",
                           "Hours"]]
    expected = pd.DataFrame({"User":["user1", "user2", "user1", "user3"],
                             "GPU-Util":["9%", "6%", "9%", "6%"],
                             "GPU-Mem-Used-Max":["7 GB", "5 GB", "7 GB", "6 GB"],
                             "CPU-Mem-Used/GPU ":["4 GB", "4 GB", "4 GB", "5 GB"],
                             "Hours":[100, 100, 100, 100]})
    pd.testing.assert_frame_equal(actual.reset_index(drop=True), expected)
