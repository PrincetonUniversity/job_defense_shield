import pandas as pd
from src.job_defense_shield.alert.too_many_cores_per_gpu import TooManyCoresPerGpu

def test_too_many_cores_per_gpu():
    n_jobs = 5
    wallclock_secs = 36000
    wallclock_hrs = wallclock_secs / 3600
    ss = {"nodes":{"node1":{"total_time":424242, "cpus":8}}}
    df = pd.DataFrame({"jobid":["1234567"] * n_jobs,
                       "user":["user1", "user2", "user3", "user4", "user5"],
                       "cluster":["della", "della", "stellar", "della", "della"],
                       "cores":[96, 20, 96, 8, 64],
                       "gpus":[3, 1, 3, 4, 2],
                       "partition":["pli"] * n_jobs,
                       "state":["COMPLETED"] * n_jobs,
                       "admincomment":[ss] * n_jobs,
                       "elapsedraw":[424242] * n_jobs,
                       "elapsed-hours":[round(wallclock_hrs)] * n_jobs})
    target = 12
    cpg = TooManyCoresPerGpu(df,
                             0,
                             "",
                             "",
                             cluster="della",
                             partitions=["pli"],
                             cluster_name="Della (PLI)",
                             cores_per_node=96,
                             gpus_per_node=8,
                             cores_per_gpu_target=target,
                             cores_per_gpu_limit=16,
                             min_run_time=30,
                             include_running_jobs=False,
                             excluded_users=["aturing", "einstein"])
    actual = cpg.df[["User",
                     "Cores-per-GPU",
                     "Cores-per-GPU-Target"]]
    expected = pd.DataFrame({"User":["user1", "user2", "user5"],
                             "Cores-per-GPU":["32", "20", "32"],
                             "Cores-per-GPU-Target":[target, target, target]})
    pd.testing.assert_frame_equal(actual.reset_index(drop=True), expected)
