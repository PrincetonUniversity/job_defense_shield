import pandas as pd
from src.job_defense_shield.alert.most_gpus import MostGPUs

def test_most_gpus():
    n_jobs = 6
    secs_per_hour = 60 * 60
    elap_hours = [10.1, 0.7, 0.0, 8.0, 1.7, 24.5]
    ss = {"nodes":{"node1":{"gpu_used_memory": {0: 950},
                            "gpu_total_memory": {0: 1000},
                            "gpu_utilization": {0: 95}}}}
    df = pd.DataFrame({"jobid":["1234567"] * n_jobs,
                       "user":["user1", "user2", "user1", "user3", "user2", "user1"],
                       "cluster":["della"] * n_jobs,
                       "gpus":[1, 16, 32, 64, 0, 8],
                       "nodes":[1] * n_jobs,
                       "cores":[4] * n_jobs,
                       "state":["COMPLETED"] * n_jobs,
                       "partition":["gpu"] * n_jobs,
                       "elapsed-hours":elap_hours,
                       "admincomment":[ss, {}, ss, ss, ss, ss],
                       "elapsedraw":[secs_per_hour * eh for eh in elap_hours]})
    days_between = 7
    mg = MostGPUs(df, days_between, "", "", verbose=False)
    actual = mg.gp[["User", "GPUs", "Hours", "GPU-Eff"]]
    expected = pd.DataFrame({"User":["user3", "user2", "user1"],
                             "GPUs":[64, 16, 8],
                             "Hours":["8", "0.7", "24"],
                             "GPU-Eff":["95%", "--", "95%"]})
    pd.testing.assert_frame_equal(actual.reset_index(drop=True), expected)
