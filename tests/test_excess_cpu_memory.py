import pandas as pd
from src.job_defense_shield.alert.excess_cpu_memory import ExcessCPUMemory

def test_excess_cpu_memory():
    n_jobs = 5
    wallclock_secs = 3600000
    wallclock_hrs = wallclock_secs / 3600
    # job 1: used=1GB, total=100GB, 1000 hours, 99 TB-hours-unused
    job1 = {
    "gpus": 0,
    "nodes": {
        "della-r2c1n5": {
            "cpus": -1,
            "total_memory": 100 * 1024**3,
            "total_time": -1,
            "used_memory": 1 * 1024**3
        }
    },
    "total_time": -1}
    # job 2: used=2GB, total=100GB, 1000 hours, 95 TB-hours-unused
    job2 = {
    "gpus": 0,
    "nodes": {
        "della-r2c1n6": {
            "cpus": -1,
            "total_memory": 100 * 1024**3,
            "total_time": -1,
            "used_memory": 5 * 1024**3 
        }
    },
    "total_time": -1}
    # job 3: used=90GB, total=100GB, 1000 hours, 90 TB-hours-unused
    job3 = {
    "gpus": 0,
    "nodes": {
        "della-r2c1n6": {
            "cpus": -1,
            "total_memory": 100 * 1024**3,
            "total_time": -1,
            "used_memory": 10 * 1024**3
        }
    },
    "total_time": -1}
    num_cores = 13
    df = pd.DataFrame({"jobid":["1234567"] * n_jobs,
                       "user":["user1", "user1", "user2", "user1", "user2"],
                       "admincomment":[job1, job2, job3, job3, job1],
                       "cluster":["della"] * n_jobs,
                       "account":["cbe"] * n_jobs,
                       "jobname":["myjob"] * n_jobs,
                       "cpu-hours":[wallclock_hrs * num_cores] * n_jobs,
                       "nodes":[1] * n_jobs,
                       "cores":[num_cores] * n_jobs,
                       "state":["COMPLETED"] * n_jobs,
                       "partition":["cpu"] * n_jobs,
                       "elapsed-hours":[round(wallclock_hrs)] * n_jobs})
    xmem = ExcessCPUMemory(df,
                           0,
                           "",
                           "",
                           cluster="della",
                           partitions=["cpu"],
                           min_run_time=0,
                           cores_per_node=32,
                           cores_fraction=0.8,
                           mem_per_node=190,
                           tb_hours_threshold=65,
                           ratio_threshold=0.2,
                           mean_ratio_threshold=0.2,
                           median_ratio_threshold=0.2,
                           num_top_users=10,
                           num_jobs_display=10)
    actual = xmem.gp[["User", "Ratio", "mean-ratio", "median-ratio", "Mem-Hrs-Unused"]]
    expected = pd.DataFrame({"User":["user1", "user2"],
                             "Ratio":[(1+5+10)/(3*100), (10+1)/(2*100)],
                             "mean-ratio":[(1/100+5/100+10/100)/3,(10/100+1/100)/2],
                             "median-ratio":[5/100, (10/100+1/100)/2],
                             "Mem-Hrs-Unused":[99+95+90, 90+99]})
    cols = ["Ratio", "mean-ratio", "median-ratio"]
    expected[cols] = expected[cols].apply(lambda x: round(x, 2))
    pd.testing.assert_frame_equal(actual.reset_index(drop=True), expected)
