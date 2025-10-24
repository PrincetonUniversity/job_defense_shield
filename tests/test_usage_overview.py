import pandas as pd
from src.job_defense_shield.alert.usage_overview import UsageOverview

def test_usage_overview():
    df = pd.DataFrame({"user":["user1", "user2", "user3", "user1", "user5", "user4"],
                       "cluster":["della", "stellar", "della", "della", "traverse", "traverse"],
                       "partition":["gpu", "gpu", "mig", "cli", "all", "all"],
                       "cpu-hours":[10, 20, 10, 50, 30, 10], 
                       "gpu-hours":[10, 20, 10, 50, 30, 10],
                       "elapsedraw":[1, 1, 1, 1, 1, 1]})
    util = UsageOverview(df, 7, "", "")
    actual = util.by_cluster
    expected = pd.DataFrame({"Cluster":["della", "stellar", "traverse"],
                             "Users":[2, 1, 2],
                             "CPU-Hours":["70 (54%)", "20 (15%)", "40 (31%)"],
                             "GPU-Hours":["70 (54%)", "20 (15%)", "40 (31%)"]})
    pd.testing.assert_frame_equal(actual.reset_index(drop=True), expected)
    actual = util.special
    expected = pd.DataFrame({"Cluster":["della", "della", "della", "stellar", "traverse"],
                             "Partition":["cli", "gpu", "mig", "gpu", "all"],
                             "Users":[1, 1, 1, 1, 2],
                             "CPU-Hours":["50  (71%)", "10  (14%)", "10  (14%)", "20 (100%)", "40 (100%)"],
                             "GPU-Hours":["50  (71%)", "10  (14%)", "10  (14%)", "20 (100%)", "40 (100%)"]})
    pd.testing.assert_frame_equal(actual.reset_index(drop=True), expected)

def test_usage_overview_no_gpus():
    df = pd.DataFrame({"user":["user1", "user2", "user3", "user1", "user5", "user4"],
                       "cluster":["della", "stellar", "della", "della", "traverse", "traverse"],
                       "partition":["gpu", "gpu", "mig", "cli", "all", "all"],
                       "cpu-hours":[10, 20, 10, 50, 30, 10], 
                       "gpu-hours":[0, 0, 0, 0, 0, 0],
                       "elapsedraw":[1, 1, 1, 1, 1, 1]})
    util = UsageOverview(df, 7, "", "")
    actual = util.by_cluster
    expected = pd.DataFrame({"Cluster":["della", "stellar", "traverse"],
                             "Users":[2, 1, 2],
                             "CPU-Hours":["70 (54%)", "20 (15%)", "40 (31%)"],
                             "GPU-Hours":["0 (--)", "0 (--)", "0 (--)"]})
    pd.testing.assert_frame_equal(actual.reset_index(drop=True), expected)

def test_usage_overview_no_jobs():
    df = pd.DataFrame({"user":["u12345", "u98765"],
                       "cluster":["della", "tiger"],
                       "partition":["cpu", "cpu"],
                       "cpu-hours":[0, 0],
                       "gpu-hours":[0, 0],
                       "elapsedraw":[0, 0]})
    util = UsageOverview(df, 7, "", "")
    actual = util.by_cluster
    expected = pd.DataFrame({"Cluster":[],
                             "Users":[],
                             "CPU-Hours":[],
                             "GPU-Hours":[]})
    pd.testing.assert_frame_equal(actual.reset_index(drop=True), expected)
    actual = util.special
    expected = pd.DataFrame({"Cluster":[],
                             "Partition":[],
                             "Users":[],
                             "CPU-Hours":[],
                             "GPU-Hours":[]})
    pd.testing.assert_frame_equal(actual.reset_index(drop=True), expected)

def test_usage_overview_zero_sums():
    """The cpu-hours and gpu-hours round to zero. The jobs are are not ignored
       since the elapsed time was 1 second for each."""
    one_sec_hrs = 1 / 3600
    n_jobs = 6
    df = pd.DataFrame({"user":["user1", "user2", "user3", "user1", "user5", "user4"],
                       "cluster":["della", "stellar", "della", "della", "traverse", "traverse"],
                       "partition":["gpu", "gpu", "mig", "cli", "all", "all"],
                       "cpu-hours":[1 * one_sec_hrs,
                                    2 * one_sec_hrs,
                                    3 * one_sec_hrs,
                                    4 * one_sec_hrs,
                                    5 * one_sec_hrs,
                                    6 * one_sec_hrs],
                       "gpu-hours":[1 * one_sec_hrs,
                                    2 * one_sec_hrs,
                                    3 * one_sec_hrs,
                                    4 * one_sec_hrs,
                                    5 * one_sec_hrs,
                                    6 * one_sec_hrs],
                       "elapsedraw":[1, 2, 3, 4, 5, 6]})
    util = UsageOverview(df, 7, "", "")
    actual = util.by_cluster
    expected = pd.DataFrame({"Cluster":["della", "stellar", "traverse"],
                             "Users":[2, 1, 2],
                             "CPU-Hours":["0 (--)", "0 (--)", "0 (--)"],
                             "GPU-Hours":["0 (--)", "0 (--)", "0 (--)"]})
    pd.testing.assert_frame_equal(actual.reset_index(drop=True), expected)
    actual = util.special
    expected = pd.DataFrame({"Cluster":["della", "della", "della", "stellar", "traverse"],
                             "Partition":["cli", "mig", "gpu", "gpu", "all"],
                             "Users":[1, 1, 1, 1, 2],
                             "CPU-Hours":["0 (--)", "0 (--)", "0 (--)", "0 (--)", "0 (--)"],
                             "GPU-Hours":["0 (--)", "0 (--)", "0 (--)", "0 (--)", "0 (--)"]})
    pd.testing.assert_frame_equal(actual.reset_index(drop=True), expected)
