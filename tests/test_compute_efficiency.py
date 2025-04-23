import pandas as pd
from src.job_defense_shield.alert.compute_efficiency import LowEfficiencyCPU

def test_low_efficiency():
    n_jobs = 4
    wallclock_secs = 15235
    num_cores = 14
    # job1 has 80% efficiency (170632/(14 * 15235))
    job1 = {
    "gpus": 0,
    "nodes": {
        "della-r2c2n12": {
            "cpus": num_cores,
            "total_memory": -1,
            "total_time": 170632.0,
            "used_memory": -1
        }
    },
    "total_time": -1}
    # job2 has 40% efficiency (85316/(14 * 15235))
    job2 = {
    "gpus": 0,
    "nodes": {
        "della-r2c2n12": {
            "cpus": num_cores,
            "total_memory": -1,
            "total_time": 85316.0,
            "used_memory": -1
        }
    },
    "total_time": -1}
    # job3 has 20% efficiency (42658/(14 * 15235))
    job3 = {
    "gpus": 0,
    "nodes": {
        "della-r2c2n12": {
            "cpus": num_cores,
            "total_memory": -1,
            "total_time": 42658.0,
            "used_memory": -1
        }
    },
    "total_time": -1}
    # job4 has 90% efficiency (191961/(14 * 15235))
    job4 = {
    "gpus": 0,
    "nodes": {
        "della-r2c2n12": {
            "cpus": num_cores,
            "total_memory": -1,
            "total_time": 191961.0,
            "used_memory": -1
        }
    },
    "total_time": -1}
    df = pd.DataFrame({"jobid":["1234567"] * n_jobs,
                       "user":["user1", "user1", "user1", "user2"],
                       "admincomment":[job1, job2, job3, job4],
                       "cluster":["della"] * n_jobs,
                       "jobname":["myjob"] * n_jobs,
                       "cores":[14] * n_jobs,
                       "partition":["cpu"] * n_jobs,
                       "cpu-seconds":[num_cores * wallclock_secs] * n_jobs,
                       "elapsedraw":[wallclock_secs] * n_jobs})
    low_eff = LowEfficiencyCPU(df,
                               days_between_emails=0,
                               violation="",
                               vpath="",
                               cluster="della",
                               partitions=["cpu"],
                               eff_thres_pct=60,
                               eff_target_pct=90,
                               proportion_thres_pct=2,
                               absolute_thres_hours=1,
                               num_top_users=15,
                               min_run_time=0,
                               excluded_users=["aturing"])
    actual = low_eff.ce[["user", "partition", "cpu-hours", "proportion(%)", "eff(%)", "jobs"]]
    expected = pd.DataFrame({"user":["user1"],
                             "partition":["cpu"],
                             "cpu-hours":[round(3 * num_cores * wallclock_secs / 3600)],
                             "proportion(%)":[75],
                             "eff(%)":[47],
                             "jobs":[3]})
    pd.testing.assert_frame_equal(actual.reset_index(drop=True), expected)
