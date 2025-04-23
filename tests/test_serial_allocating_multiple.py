import pandas as pd
from src.job_defense_shield.alert.serial_allocating_multiple_cores import SerialAllocatingMultipleCores

def test_serial_allocating_multiple_cores():
    n_jobs = 5
    wallclock_secs = 100000
    wallclock_hrs = wallclock_secs / 3600
    # job 1
    num_used_cores = 1
    num_cores = 32
    job1 = {
    "gpus": 0,
    "nodes": {
        "della-r2c1n5": {
            "cpus": num_cores,
            "total_memory": 34359738368,
            "total_time": num_used_cores * wallclock_secs,
            "used_memory": 165367808
        }
    },
    "total_time": -1}
    # job 2
    num_used_cores = 1
    num_cores = 16
    job2 = {
    "gpus": 0,
    "nodes": {
        "della-r2c1n6": {
            "cpus": num_cores,
            "total_memory": 68719476736,
            "total_time": num_used_cores * wallclock_secs,
            "used_memory": 192299008
        }
    },
    "total_time": -1}
    # job 3 has 50% utilization for 8 cores so should be ignored
    num_used_cores = 4
    num_cores = 8
    job3 = {
    "gpus": 0,
    "nodes": {
        "della-r2c1n6": {
            "cpus": num_cores,
            "total_memory": 68719476736,
            "total_time": num_used_cores * wallclock_secs,
            "used_memory": 192299008
        }
    },
    "total_time": -1}
    df = pd.DataFrame({"jobid":["1234567"] * n_jobs,
                       "user":["user1", "user1", "user2", "user1", "user2"],
                       "admincomment":[job1, job2, job3, job2, job1],
                       "cluster":["della"] * n_jobs,
                       "nodes":[1] * n_jobs,
                       "cores":[32, 16, 8, 16, 32],
                       "partition":["cpu"] * n_jobs,
                       "elapsedraw":[wallclock_secs] * n_jobs,
                       "elapsed-hours":[round(wallclock_hrs)] * n_jobs,
                       "cpu-hours":[32 * wallclock_hrs,
                                    16 * wallclock_hrs,
                                     8 * wallclock_hrs,
                                    16 * wallclock_hrs,
                                    32 * wallclock_hrs]})
    serial = SerialAllocatingMultipleCores(df,
                                           0,
                                           "",
                                           "",
                                           cluster="della",
                                           partitions=["cpu"],
                                           cores_per_node=32,
                                           min_run_time=0,
                                           cpu_hours_threshold=0,
                                           lower_ratio=0.85,
                                           num_top_users=0,
                                           num_jobs_display=3,
                                           include_running_jobs=False,
                                           email_file="",
                                           max_num_jobid_admin=3)
    actual = serial.df[["User", "CPU-Cores", "100%/CPU-Cores", "CPU-Util", "Hours"]]
    expected = pd.DataFrame({"User":["user1", "user1", "user1", "user2"],
                             "CPU-Cores":[32, 16, 16, 32],
                             "100%/CPU-Cores":["3.1%", "6.2%", "6.2%", "3.1%"],
                             "CPU-Util":["3.1%", "6.2%", "6.2%", "3.1%"],
                             "Hours":[round(wallclock_hrs),
                                      round(wallclock_hrs),
                                      round(wallclock_hrs),
                                      round(wallclock_hrs)]})
    pd.testing.assert_frame_equal(actual.reset_index(drop=True), expected)
