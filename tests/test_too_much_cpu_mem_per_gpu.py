import pandas as pd
from src.job_defense_shield.alert.too_much_cpu_mem_per_gpu import TooMuchCpuMemPerGpu

def test_too_much_cpu_mem_per_gpu():
    """Job 1 only allocates 100 GB so it is excluded. Job 3 has
       two GPUs so 640/2 = 320 GB. Job 4 is ignored since it uses 90%
       of the allocated memory, which greater than mem_eff_thres.
       Job 6 is ignored because not in nodelist."""
    n_jobs = 6
    wallclock_secs = 36000
    wallclock_hrs = wallclock_secs / 3600
    ss1 = {
        "gpus": 1,
        "nodes": {
            "della-l03g12": {
                "cpus": 1,
                "gpu_total_memory": {
                    "2": 85899345920
                },
                "gpu_used_memory": {
                    "2": 4577296384
                },
                "gpu_utilization": {
                    "2": 91.9
                },
                "total_memory": 107374182400,
                "total_time": 80613.8,
                "used_memory": 0.5 * 107374182400
            }
        },
        "total_time": 81315
    }
    ss2 = {
        "gpus": 1,
        "nodes": {
            "della-l01g15": {
                "cpus": 1,
                "gpu_total_memory": {
                    "1": 85899345920
                },
                "gpu_used_memory": {
                    "1": 85810479104
                },
                "gpu_utilization": {
                    "1": 94.8
                },
                "total_memory": 536870912000,
                "total_time": 84517.3,
                "used_memory": 18197135360
            }
        },
        "total_time": 84913
    }
    ss3 = {
        "gpus": 2,
        "nodes": {
            "della-l04g5": {
                "cpus": 8,
                "gpu_total_memory": {
                    "0": 85899345920,
                    "3": 85899345920
                },
                "gpu_used_memory": {
                    "0": 44089737216,
                    "3": 43731124224
                },
                "gpu_utilization": {
                    "0": 31.1,
                    "3": 30.5
                },
                "total_memory": 687194767360,
                "total_time": 1350005.5,
                "used_memory": 542147788800
            }
        },
        "total_time": 173113
    }
    ss4 = {
        "gpus": 1,
        "nodes": {
            "della-l04g14": {
                "cpus": 8,
                "gpu_total_memory": {
                    "1": 85899345920
                },
                "gpu_used_memory": {
                    "1": 19662110720
                },
                "gpu_utilization": {
                    "1": 61.1
                },
                "total_memory": 274877906944,
                "total_time": 249954.3,
                "used_memory": 0.9 * 274877906944
            }
        },
        "total_time": 72359
    }
    ss5 = {
        "gpus": 1,
        "nodes": {
            "della-l04g14": {
                "cpus": 8,
                "gpu_total_memory": {
                    "1": 85899345920
                },
                "gpu_used_memory": {
                    "1": 19662110720
                },
                "gpu_utilization": {
                    "1": 61.1
                },
                "total_memory": 274877906944,
                "total_time": 249954.3,
                "used_memory": 38747418624
            }
        },
        "total_time": 72359
    }
    ss6 = {
        "gpus": 1,
        "nodes": {
            "della-l01g1": {
                "cpus": 8,
                "gpu_total_memory": {
                    "1": 85899345920
                },
                "gpu_used_memory": {
                    "1": 19662110720
                },
                "gpu_utilization": {
                    "1": 61.1
                },
                "total_memory": 274877906944,
                "total_time": 249954.3,
                "used_memory": 38747418624
            }
        },
        "total_time": 72359
    }

    df = pd.DataFrame({"jobid":["1234567"] * n_jobs,
                       "user":["user1", "user1", "user2", "user3", "user4", "user5"],
                       "cluster":["della"] * n_jobs,
                       "cores":[12] * n_jobs,
                       "gpus":[1, 1, 2, 1, 1, 1],
                       "partition":["pli"] * n_jobs,
                       "state":["COMPLETED"] * n_jobs,
                       "admincomment":[ss1, ss2, ss3, ss4, ss5, ss6],
                       "elapsedraw":[424242] * n_jobs,
                       "elapsed-hours":[round(wallclock_hrs)] * n_jobs})
    target = 115
    nodelist = ["della-l03g12",
                "della-l01g15",
                "della-l04g5",
                "della-l04g14",
                "della-l04g14"]
    cpg = TooMuchCpuMemPerGpu(df,
                              0,
                              violation="",
                              vpath="",
                              cluster="della",
                              partitions=["pli"],
                              cluster_name="Della (PLI)",
                              cores_per_node=96,
                              gpus_per_node=8,
                              cpu_mem_per_node=1000,
                              cpu_mem_per_gpu_target=target,
                              cpu_mem_per_gpu_limit=128,
                              mem_eff_thres=0.8,
                              nodelist=nodelist,
                              email_file="too_much_cpu_mem_per_gpu.txt")
    actual = cpg.df[["User",
                     "Mem-Eff",
                     "GPUs",
                     "CPU-Mem-per-GPU",
                     "CPU-Mem-per-GPU-Limit"]]
    s = 1024**3
    target = f"{target} GB"
    expected = pd.DataFrame({"User":["user1", "user2", "user4"],
                             "Mem-Eff":[round(18197135360/s) / round(536870912000/s),
                                        round(542147788800/s) / round(687194767360/s),
                                        round(38747418624/s) / round(274877906944/s)],
                             "GPUs":[1, 2, 1],
                             "CPU-Mem-per-GPU":["500 GB", "320 GB", "256 GB"],
                             "CPU-Mem-per-GPU-Limit":[target, target, target]})
    pd.testing.assert_frame_equal(actual.reset_index(drop=True), expected)
    #greeting_method = "basic"
    #cpg.email_files_path = "email/"
    #mocker.patch("base.has_sufficient_time_passed_since_last_email", return_value=True)
    #cpg.create_emails(greeting_method)
    #print(cpg.emails)
