import pandas as pd
from src.job_defense_shield.alert.excessive_time_limits import ExcessiveTimeLimitsCPU
from src.job_defense_shield.alert.excessive_time_limits import ExcessiveTimeLimitsGPU

def test_excessive_time_limits_cpu():
    n_jobs = 6
    cpus = 10
    ss = {"nodes":{"node1":{"total_time":-1, "cpus":cpus}}}
    elapsed_hours = [ 9600, 5000, 1500, 2100, 3000,  5000]
    limit_hours   = [10000, 9000, 3000, 4200, 6100, 10000]
    df = pd.DataFrame({"user":["user3", "user1", "user1", "user2", "user1", "user2"],
                       "cluster":["della"] * n_jobs,
                       "state":["COMPLETED"] * n_jobs,
                       "cores":[cpus] * n_jobs,
                       "partition":["cpu"] * n_jobs,
                       "elapsed-hours":elapsed_hours,
                       "elapsedraw":[60 * 60 * hrs for hrs in elapsed_hours],
                       "limit-minutes":[60 * lim for lim in limit_hours],
                       "admincomment":[ss] * n_jobs,
                       "cpu-hours":[cpus * hrs for hrs in elapsed_hours]})
    limits = ExcessiveTimeLimitsCPU(
                                 df,
                                 0,
                                 "",
                                 "",
                                 cluster="della",
                                 partitions=["cpu"],
                                 min_run_time=0,
                                 num_top_users=10,
                                 absolute_thres_hours=5000,
                                 overall_ratio_threshold=1.0,
                                 mean_ratio_threshold=1.0,
                                 median_ratio_threshold=1.0)
    actual = limits.gp[["User", "CPU-Hours-Unused", "median-ratio", "rank", "jobs"]]
    expected = pd.DataFrame({"User":["user1", "user2"],
                             "CPU-Hours-Unused":[40000+15000+31000.0, 21000+50000.0],
                             "median-ratio":[0.50, 0.5],
                             "rank":[2, 3],
                             "jobs":[3, 2]})
    expected.index += 1
    pd.testing.assert_frame_equal(actual, expected)

def test_excessive_time_limits_gpu():
    n_jobs = 6
    gpus = 10
    ss = {"nodes":{"node1":{"total_time":-1, "gpus":gpus}}}
    elapsed_hours = [ 9600, 5000, 1500, 2100, 3000,  5000]
    limit_hours   = [10000, 9000, 3000, 4200, 6100, 10000]
    df = pd.DataFrame({"user":["user3", "user1", "user1", "user2", "user1", "user2"],
                       "cluster":["della"] * n_jobs,
                       "state":["COMPLETED"] * n_jobs,
                       "gpus":[gpus] * n_jobs,
                       "partition":["gpu"] * n_jobs,
                       "elapsed-hours":elapsed_hours,
                       "elapsedraw":[60 * 60 * hrs for hrs in elapsed_hours],
                       "limit-minutes":[60 * lim for lim in limit_hours],
                       "admincomment":[ss] * n_jobs,
                       "gpu-hours":[gpus * hrs for hrs in elapsed_hours]})
    limits = ExcessiveTimeLimitsGPU(
                                 df,
                                 0,
                                 "",
                                 "",
                                 cluster="della",
                                 partitions=["gpu"],
                                 min_run_time=0,
                                 num_top_users=10,
                                 absolute_thres_hours=5000,
                                 overall_ratio_threshold=1.0,
                                 mean_ratio_threshold=1.0,
                                 median_ratio_threshold=1.0)
    actual = limits.gp[["User", "GPU-Hours-Unused", "median-ratio", "rank", "jobs"]]
    expected = pd.DataFrame({"User":["user1", "user2"],
                             "GPU-Hours-Unused":[40000+15000+31000.0, 21000+50000.0],
                             "median-ratio":[0.50, 0.5],
                             "rank":[2, 3],
                             "jobs":[3, 2]})
    expected.index += 1
    pd.testing.assert_frame_equal(actual, expected)
