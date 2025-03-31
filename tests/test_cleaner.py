from datetime import datetime
from cleaner import SacctCleaner
import pandas as pd

def test_field_renamings():
    fields = ["jobid",
              "user",
              "cluster",
              "account",
              "partition",
              "cputimeraw",
              "elapsedraw",
              "timelimitraw",
              "nnodes",
              "ncpus",
              "alloctres",
              "submit",
              "eligible",
              "start",
              "end",
              "qos",
              "state",
              "admincomment",
              "jobname"]

    n_jobs = 3
    jobid = ["100001", "100002", "100003"]
    user = ["u1000", "u1001", "u1002"]
    cluster = ["tiger"] * n_jobs
    account = ["bio"] * n_jobs
    partition = ["cpu"] * n_jobs
    cputimeraw = [1000] * n_jobs
    elapsedraw = [2000] * n_jobs
    timelimitraw = [3000] * n_jobs
    nnodes = [1] * n_jobs
    ncpus = [32] * n_jobs
    alloctres = ["billing=8,cpu=1,mem=16G,node=1"] * n_jobs
    submit = [123456789] * n_jobs
    eligible = [234567890] * n_jobs
    start = [234567890] * n_jobs
    end = [300000000] * n_jobs
    qos = ["short"] * n_jobs
    state = ["RUNNING", "PENDING", "COMPLETED"]
    admincomment = ["JS1:None"] * n_jobs
    jobname = ["myjob"] * n_jobs

    raw = pd.DataFrame({"jobid":jobid,
                        "user":user,
                        "cluster":cluster,
                        "account":account,
                        "partition":partition,
                        "cputimeraw":cputimeraw,
                        "elapsedraw":elapsedraw,
                        "timelimitraw":timelimitraw,
                        "nnodes":nnodes,
                        "ncpus":ncpus,
                        "alloctres":alloctres,
                        "submit":submit,
                        "eligible":eligible,
                        "start":start,
                        "end":end,
                        "qos":qos,
                        "state":state,
                        "admincomment":admincomment,
                        "jobname":jobname})

    field_renamings = {"cputimeraw":"cpu-seconds",
                       "nnodes":"nodes",
                       "ncpus":"cores",
                       "timelimitraw":"limit-minutes"}
    partition_renamings = {}
    s = SacctCleaner(raw, field_renamings, partition_renamings)
    s.raw = s.rename_columns()
    expected = [field_renamings[field] if field in field_renamings else field for field in fields]
    expected = pd.Index(expected)
    pd.testing.assert_index_equal(s.raw.columns, expected, check_names=False)


def test_renamings():
    raw = pd.DataFrame({"jobid":[1, 2],
                        "user":["aturing", "einstein"],
                        "cluster":["blackstar", "blackstar"]})
    field_renamings = {"user":"User"}
    partition_renamings = {}
    df = SacctCleaner(raw, field_renamings, partition_renamings).rename_columns()
    expected = pd.Index(["jobid", "User", "cluster"])
    pd.testing.assert_index_equal(df.columns, expected, check_names=False)


def test_remove_comma_partitions():
    raw = pd.DataFrame({"jobid":[1, 2, 3],
                        "cpu-seconds":["1000", "1000", "1000"],
                        "partition":["gpu", "cpu,all", "physics"]})
    field_renamings = {}
    partition_renamings = {}
    s = SacctCleaner(raw, field_renamings, partition_renamings)
    s.raw = s.remove_comma_partitions()
    expected = pd.Series(["gpu", "physics"])
    pd.testing.assert_series_equal(s.raw.partition,
                                   expected,
                                   check_names=False,
                                   check_index=False)


def test_rename_partitions():
    raw = pd.DataFrame({"jobid":[1, 2, 3],
                        "partition":["datascience", "gpu", "datascience"]})
    field_renamings = {}
    partition_renamings = {"datascience":"ds"}
    series = SacctCleaner(raw, field_renamings, partition_renamings).rename_partitions()
    expected = pd.Series(["ds", "gpu", "ds"])
    pd.testing.assert_series_equal(series, expected, check_names=False)


def test_unify_cancel_state():
    raw = pd.DataFrame({"jobid":[1, 2],
                        "state":["CANCELLED by 352864", "RUNNING"]})
    field_renamings = {}
    partition_renamings = {}
    s = SacctCleaner(raw, field_renamings, partition_renamings)
    s.raw.state = s.unify_cancel_state()
    expected = pd.Series(["CANCELLED", "RUNNING"])
    pd.testing.assert_series_equal(s.raw.state, expected, check_names=False)


def test_unlimited_time_limits():
    # can fail if now_secs is different in main code due to slow execution
    jobid = [1, 2, 3, 4]
    state = ["COMPLETED", "COMPLETED", "RUNNING", "PENDING"]
    limit_minutes = ["100", "UNLIMITED", "UNLIMITED", "UNLIMITED"]
    now_secs = int(datetime.now().timestamp())
    start = ["0", "0", str(now_secs - 50), "0"]
    end = ["100", "100", "42", "-1"]
    raw = pd.DataFrame({"jobid":jobid,
                        "state":state,
                        "limit-minutes":limit_minutes,
                        "start":start,
                        "end":end})
    field_renamings = {}
    partition_renamings = {}
    s = SacctCleaner(raw, field_renamings, partition_renamings)
    s.raw = s.unlimited_time_limits()
    expected = pd.Series(["100", 100, 50, -1])
    pd.testing.assert_series_equal(s.raw["limit-minutes"], expected, check_names=False)
