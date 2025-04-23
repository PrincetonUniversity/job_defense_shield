import pandas as pd
from src.job_defense_shield.alert.jobs_overview import JobsOverview

def test_jobs_overview():
    n_jobs = 6
    num_cores = 16
    num_gpus = 4
    wall_secs = 36000
    secs_per_hour = 60 * 60
    df = pd.DataFrame({"jobid":["1234567"] * n_jobs,
                       "user":["user1", "user2", "user1", "user1", "user2", "user1"],
                       "cluster":["della"] * n_jobs,
                       "state":["COMPLETED", "COMPLETED", "COMPLETED", "COMPLETED", "COMPLETED", "CANCELLED"],
                       "partition":["cpu", "cpu", "cpu", "cpu", "serial", "gpu"],
                       "cpu-seconds":[wall_secs * num_cores] * n_jobs,
                       "gpu-seconds":[0, 0, 0, 0, 0, num_gpus * wall_secs],
                       "gpus":[0, 0, 0, 0, 0, num_gpus],
                       "elapsedraw":[wall_secs, wall_secs, 0, wall_secs, wall_secs, wall_secs]})
    jobs = JobsOverview(df, 7, "", "")
    actual = jobs.gp[["User", "Jobs", "CPU", "GPU", "COM", "CLD", "CPU-Hrs", "GPU-Hrs", "Partitions"]]
    expected = pd.DataFrame({"User":["user1", "user2"],
                             "Jobs":[3, 2],
                             "CPU":[2, 2],
                             "GPU":[1, 0],
                             "COM":[2, 2],
                             "CLD":[1, 0],
                             "CPU-Hrs":[3 * num_cores * wall_secs / secs_per_hour,
                                          2 * num_cores * wall_secs / secs_per_hour],
                             "GPU-Hrs":[num_gpus * wall_secs / 3600, 0],
                             "Partitions":["cpu,gpu", "cpu,serial"]})
    expected["CPU-Hrs"] = expected["CPU-Hrs"].apply(round)
    expected["GPU-Hrs"] = expected["GPU-Hrs"].apply(round)
    pd.testing.assert_frame_equal(actual.reset_index(drop=True), expected)
