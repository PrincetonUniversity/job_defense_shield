import pandas as pd
from ..base import Alert
from ..utils import add_dividers
from ..utils import MINUTES_PER_HOUR as mph
from ..efficiency import cpu_memory_usage
from ..efficiency import gpu_memory_usage_eff_tuples
from ..greeting import GreetingFactory
from ..email_translator import EmailTranslator


class GpuModelTooPowerful(Alert):

    """Find jobs that could have used a less powerful GPU model."""

    def __init__(self, df, days_between_emails, violation, vpath, **kwargs):
        super().__init__(df, days_between_emails, violation, vpath, **kwargs)

    def _add_required_fields(self):
        if not hasattr(self, "email_subject"):
            self.email_subject = "Jobs with GPU Model Too Powerful"
        if not hasattr(self, "report_title"):
            self.report_title = "GPU Model Too Powerful"
        if not hasattr(self, "max_num_jobid_admin"):
            self.max_num_jobid_admin = 3
        if not hasattr(self, "num_cores_threshold"):
            self.num_cores_threshold = 1

    def _filter_and_add_new_fields(self):
        self.df = self.df[(self.df.cluster == self.cluster) &
                          (self.df.partition.isin(self.partitions)) &
                          (self.df.cores <= self.num_cores_threshold) &
                          (self.df.gpus == 1) &
                          (~self.df.user.isin(self.excluded_users)) &
                          (self.df.state != "OUT_OF_MEMORY") &
                          (self.df["elapsed-hours"] >= self.min_run_time / mph)].copy()
        if not self.df.empty and self.include_running_jobs:
            self.df.admincomment = self.get_admincomment_for_running_jobs()
        self.df = self.df[self.df.admincomment != {}]
        if not self.df.empty and hasattr(self, "nodelist"):
            self.df = self.filter_by_nodelist(self.df)
        self.df.rename(columns={"user":"User"}, inplace=True)
        # add new fields
        if not self.df.empty:
            self.df["gpu-tuple"] = self.df.apply(lambda row:
                                   gpu_memory_usage_eff_tuples(row["admincomment"],
                                                               row["jobid"],
                                                               row["cluster"]),
                                                               axis="columns")
            self.df["error_code"] = self.df["gpu-tuple"].apply(lambda x: x[1])
            self.df = self.df[self.df["error_code"] == 0]
            # next two lines are valid since only one GPU per job
            self.df["GPU-Mem-Used"] = self.df["gpu-tuple"].apply(lambda tpl: tpl[0][0][0])
            self.df["GPU-Util"]     = self.df["gpu-tuple"].apply(lambda tpl: tpl[0][0][2])
            if not self.df.empty:
                # add CPU memory usage
                self.df["memory-tuple"] = self.df.apply(lambda row:
                                          cpu_memory_usage(row["admincomment"],
                                                           row["jobid"],
                                                           row["cluster"]),
                                                           axis="columns")
                cols = ["CPU-Mem-Used", "mem-alloc", "error_code"]
                self.df[cols] = pd.DataFrame(self.df["memory-tuple"].tolist(), index=self.df.index)
                self.df = self.df[self.df["error_code"] == 0]
                # find jobs that could have used less powerful gpus
                self.df = self.df[(self.df["GPU-Util"] <= self.gpu_util_threshold) &
                                  (self.df["GPU-Util"] != 0) &
                                  (self.df["GPU-Mem-Used"] < self.gpu_mem_threshold) &
                                  (self.df["CPU-Mem-Used"] < self.cpu_mem_threshold)]
                self.df["CPU-Mem-Used"] = self.df["CPU-Mem-Used"].apply(lambda x: f"{round(x)} GB")
                self.df["GPU-Mem-Used"] = self.df["GPU-Mem-Used"].apply(lambda x: f"{round(x)} GB")
                self.df["GPU-Util"]     = self.df["GPU-Util"].apply(lambda x: f"{round(x)}%"
                                                                    if x > 0.5 else f"{round(x, 1)}%")
                renamings = {"elapsed-hours":"Hours",
                             "jobid":"JobID",
                             "user":"User",
                             "partition":"Partition"}
                self.df = self.df.rename(columns=renamings)
                cols = ["JobID",
                        "User",
                        "Partition",
                        "GPU-Util",
                        "GPU-Mem-Used",
                        "CPU-Mem-Used",
                        "Hours"]
                self.df = self.df[cols]
                self.gp = self.df.groupby("User").agg({"Hours":"sum"}).reset_index()
                self.gp = self.gp[self.gp["Hours"] > self.gpu_hours_threshold]
                self.df = self.df[self.df.User.isin(self.gp.User)]

    def create_emails(self, method):
        g = GreetingFactory().create_greeting(method)
        for user in self.df.User.unique():
            vfile = f"{self.vpath}/{self.violation}/{user}.csv"
            if self.has_sufficient_time_passed_since_last_email(vfile):
                usr = self.df[self.df.User == user].copy()
                usr["Hours"] = usr["Hours"].apply(lambda x: str(round(x, 1))
                                                  if x < 5 else str(round(x)))
                indent = 4 * " "
                tbl = usr.drop(columns=["Partition"]).copy()
                table = tbl.to_string(index=False, justify="center").split("\n")
                tags = {}
                tags["<GREETING>"] = g.greeting(user)
                tags["<DAYS>"] = str(self.days_between_emails)
                tags["<CLUSTER>"] = self.cluster
                tags["<PARTITIONS>"] = ",".join(sorted(set(self.partitions)))
                tags["<TARGET>"] = str(self.gpu_util_target)
                tags["<NUM-JOBS>"] = str(len(usr))
                tags["<TABLE>"] = "\n".join([indent + row for row in table])
                tags["<JOBSTATS>"] = f"{indent}$ jobstats {usr.JobID.values[0]}"
                translator = EmailTranslator(self.email_files_path,
                                             self.email_file,
                                             tags)
                email = translator.replace_tags()
                usr["Cluster"] = self.cluster
                usr["Alert-Partitions"] = ",".join(sorted(set(self.partitions)))
                usr["GPU-Util"] = usr["GPU-Util"].apply(lambda x: x.replace("%", ""))
                usr["GPU-Mem-Used"] = usr["GPU-Mem-Used"].apply(lambda x: x.replace(" GB", ""))
                usr["CPU-Mem-Used"] = usr["CPU-Mem-Used"].apply(lambda x: x.replace(" GB", ""))
                usr = usr[["User",
                           "Cluster",
                           "Alert-Partitions",
                           "JobID",
                           "Partition",
                           "GPU-Util",
                           "GPU-Mem-Used",
                           "CPU-Mem-Used",
                           "Hours"]]
                self.emails.append((user, email, usr))
 
    def generate_report_for_admins(self, keep_index: bool=False) -> str:
        if self.df.empty:
            column_names = ["User",
                            "GPU-Hours",
                            "JobID",
                            "Emails"]
            self.df = pd.DataFrame(columns=column_names)
            return add_dividers(self.create_empty_report(self.df), self.report_title)
        def jobid_list(series):
            ellipsis = "+" if len(series) > self.max_num_jobid_admin else " "
            return ",".join(series[:self.max_num_jobid_admin]) + ellipsis
        d = {"Hours":"sum", "User":"size", "JobID":jobid_list}
        self.admin = self.df.groupby("User").agg(d)
        renamings = {"User":"Jobs", "Hours":"GPU-Hours"}
        self.admin = self.admin.rename(columns=renamings)
        self.admin.reset_index(drop=False, inplace=True)
        self.admin = self.admin.sort_values(by="GPU-Hours", ascending=False)
        self.admin["GPU-Hours"] = self.admin["GPU-Hours"].apply(lambda x: str(round(x, 1))
                                                                if x < 5 else str(round(x)))
        self.admin.index += 1
        self.admin["Emails"] = self.admin["User"].apply(lambda user:
                                    self.get_emails_sent_count(user, self.violation))
        self.admin.Emails = self.format_email_counts(self.admin.Emails)
        report_str = self.admin.to_string(index=keep_index, justify="center")
        return add_dividers(report_str, self.report_title)
