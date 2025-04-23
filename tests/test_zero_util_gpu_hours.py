import pandas as pd
from src.job_defense_shield.alert.zero_util_gpu_hours import ZeroUtilGPUHours

def test_zero_util_gpu_hours():
    n_jobs = 5
    wallclock_hrs = 1000000 / 3600
    # job 1 (8555322 on tiger2)
    job1 = {
    "gpus": 4,
    "nodes": {
        "tiger-i20g9": {
            "cpus": 4,
            "gpu_total_memory": {
                "0": 17071734784,
                "1": 17071734784,
                "2": 17071734784,
                "3": 17071734784
            },
            "gpu_used_memory": {
                "0": 16663052288,
                "1": 414318592,
                "2": 414318592,
                "3": 414318592
            },
            "gpu_utilization": {
                "0": 92.6,
                "1": 0,
                "2": 0,
                "3": 0
            },
            "total_memory": 214748364800,
            "total_time": -1,
            "used_memory": 9181413376
        }
    },
    "total_time": -1}
    # job 2 (46915114 on della)
    job2 = {
    "gpus": 1,
    "nodes": {
        "della-l04g11": {
            "cpus": 1,
            "gpu_total_memory": {
                "2": 85899345920
            },
            "gpu_used_memory": {
                "2": 728170496
            },
            "gpu_utilization": {
                "2": 0
            },
            "total_memory": 268435456000,
            "total_time": -1,
            "used_memory": 10614919168
        }
    },
    "total_time": -1}
    # job 3 (48128061 on della)
    job3 = {
    "gpus": 2,
    "nodes": {
        "della-l03g7": {
            "cpus": 32,
            "gpu_total_memory": {
                "2": 85899345920,
                "3": 85899345920
            },
            "gpu_used_memory": {
                "2": 57101713408,
                "3": 57099616256
            },
            "gpu_utilization": {
                "2": 98.6,
                "3": 98.6
            },
            "total_memory": 137438953472,
            "total_time": -1,
            "used_memory": 18622492672
        }
    },
    "total_time": -1}
    df = pd.DataFrame({"jobid":["12345", "12346", "12347", "12348", "12349"],
                       "user":["user1", "user1", "user2", "user1", "user2"],
                       "admincomment":[job1, job2, job3, job2, job1],
                       "cluster":["della"] * n_jobs,
                       "gpus":[4, 1, 2, 1, 4],
                       "partition":["gpu"] * n_jobs,
                       "elapsed-hours":[wallclock_hrs] * n_jobs})
    zero = ZeroUtilGPUHours(df,
                            0,
                            "",
                            "",
                            cluster="della",
                            partitions=["gpu"],
                            excluded_users=[],
                            min_run_time=15,
                            gpu_hours_threshold_user=0,
                            gpu_hours_threshold_admin=0,
                            include_running_jobs=False,
                            max_num_jobid_admin=3)
    actual = zero.gp[["User", "GPU-Hours-At-0%", "Jobs", "JobID"]]
    expected = pd.DataFrame({"User":["user1", "user2"],
                             "GPU-Hours-At-0%":[(3 + 1 + 1) * wallclock_hrs,
                                                    3 * wallclock_hrs],
                             "Jobs":[3, 1],
                             "JobID":["12345,12346,12348", "12349"]})
    pd.testing.assert_frame_equal(actual.reset_index(drop=True), expected)
