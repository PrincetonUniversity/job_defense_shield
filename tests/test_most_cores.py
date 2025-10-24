import pandas as pd
from src.job_defense_shield.alert.most_cores import MostCores

def test_most_cores():
    n_jobs = 6
    secs_per_hour = 60 * 60
    elap_hours = [10.1, 0.7, 0.0, 8.0, 1.7, 24.5]
    ss1 = {
    "gpus": 0,
    "nodes": {
        "della-r2c2n12": {
            "cpus": 1,
            "total_memory": -1,
            "total_time": 36360,
            "used_memory": -1
        }
    },
    "total_time": -1}
    num_cores = 32
    ss2 = {
    "gpus": 0,
    "nodes": {
        "della-r2c2n12": {
            "cpus": num_cores,
            "total_memory": -1,
            "total_time": 0.25 * num_cores * 2520,
            "used_memory": -1
        }
    },
    "total_time": -1}
    ss3 = {
    "gpus": 0,
    "nodes": {
        "della-r2c2n12": {
            "cpus": 32,
            "total_memory": -1,
            "total_time": 0,
            "used_memory": -1
        }
    },
    "total_time": -1}
    num_cores = 64
    ss4 = {
    "gpus": 0,
    "nodes": {
        "della-r2c2n12": {
            "cpus": num_cores,
            "total_memory": -1,
            "total_time": 0.95 * num_cores * 28800,
            "used_memory": -1
        }
    },
    "total_time": -1}
    ss5 = {
    "gpus": 0,
    "nodes": {
        "della-r2c2n12": {
            "cpus": 0,
            "total_memory": -1,
            "total_time": 6120,
            "used_memory": -1
        }
    },
    "total_time": -1}
    num_cores = 8
    ss6 = {
    "gpus": 0,
    "nodes": {
        "della-r2c2n12": {
            "cpus": num_cores,
            "total_memory": -1,
            "total_time": 0.65 * num_cores * 88200,
            "used_memory": -1
        }
    },
    "total_time": -1}

    df = pd.DataFrame({"jobid":["1234567"] * n_jobs,
                       "user":["user1", "user2", "user1", "user3", "user2", "user1"],
                       "cluster":["della"] * n_jobs,
                       "cores":[1, 16, 2, 64, 0, 8],
                       "nodes":[1] * n_jobs,
                       "gpus":[0] * n_jobs,
                       "state":["COMPLETED"] * n_jobs,
                       "partition":["cpu"] * n_jobs,
                       "elapsed-hours":elap_hours,
                       "admincomment":[ss1, ss2, ss3, ss4, ss5, {}],
                       "elapsedraw":[secs_per_hour * eh for eh in elap_hours]})
    days_between = 7
    mg = MostCores(df, days_between, "", "", verbose=False)
    actual = mg.gp[["User", "Cores", "Hours", "CPU-Eff"]]
    expected = pd.DataFrame({"User":["user3", "user2", "user1"],
                             "Cores":[64, 16, 8],
                             "Hours":["8", "0.7", "24"],
                             "CPU-Eff":["95%", "25%", "--"]})
    pd.testing.assert_frame_equal(actual.reset_index(drop=True), expected)
