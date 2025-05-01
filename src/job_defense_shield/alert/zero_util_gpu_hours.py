import pandas as pd
from ..base import Alert
from ..utils import add_dividers
from ..utils import MINUTES_PER_HOUR as mph
from ..efficiency import num_gpus_with_zero_util
from ..greeting import GreetingFactory
from ..email_translator import EmailTranslator


class ZeroUtilGPUHours(Alert):

    """Identify users with many GPU-hours at 0% utilization."""

    def __init__(self, df, days_between_emails, violation, vpath, **kwargs):
        super().__init__(df, days_between_emails, violation, vpath, **kwargs)

    def _add_required_fields(self):
        if not hasattr(self, "email_subject"):
            self.email_subject = "GPU-hours at 0% Utilization"
        if not hasattr(self, "report_title"):
            self.report_title = "GPU-hours at 0% Utilization"
        if not hasattr(self, "max_num_jobid_admin"):
            self.max_num_jobid_admin = 4

    def _filter_and_add_new_fields(self):
        self.df = self.df[(self.df.cluster == self.cluster) &
                          (self.df.partition.isin(self.partitions)) &
                          (self.df.gpus > 0) &
                          (~self.df.user.isin(self.excluded_users)) &
                          (self.df["elapsed-hours"] >= self.min_run_time / mph)].copy()
        if not self.df.empty and self.include_running_jobs:
            self.df.admincomment = self.get_admincomment_for_running_jobs()
        self.df = self.df[self.df.admincomment != {}]
        if not self.df.empty and hasattr(self, "nodelist"):
            self.df = self.filter_by_nodelist(self.df)
        self.gp = pd.DataFrame({"User":[]})
        self.admin = pd.DataFrame()
        # add new fields
        if not self.df.empty:
            self.df["zero-tuple"] = self.df.apply(lambda row:
                                    num_gpus_with_zero_util(row["admincomment"],
                                                            row["jobid"],
                                                            row["cluster"]),
                                                            axis="columns")
            cols = ["GPUs-Unused", "error_code"]
            self.df[cols] = pd.DataFrame(self.df["zero-tuple"].tolist(), index=self.df.index)
            self.df = self.df[(self.df["error_code"] == 0) & (self.df["GPUs-Unused"] > 0)]
            self.df["GPU-Hours-At-0%"] = self.df["GPUs-Unused"] * self.df["elapsed-hours"]
            self.df["GPU-Unused-Util"] = "0%"
            cols = ["jobid",
                    "user",
                    "partition",
                    "gpus",
                    "GPUs-Unused",
                    "GPU-Unused-Util",
                    "GPU-Hours-At-0%"]
            self.df = self.df[cols]
            renamings = {"jobid":"JobID",
                         "user":"User",
                         "partition":"Partition",
                         "gpus":"GPUs"}
            self.df = self.df.rename(columns=renamings)
            def jobid_list(series):
                ellipsis = "+" if len(series) > self.max_num_jobid_admin else ""
                return ",".join(series[:self.max_num_jobid_admin]) + ellipsis
            # for each user sum the number of GPU-hours with zero GPU utilization
            self.gp = self.df.groupby("User").agg({"GPU-Hours-At-0%":"sum",
                                                   "User":"size",
                                                   "JobID":jobid_list})
            self.gp = self.gp.rename(columns={"User":"Jobs"})
            self.gp.reset_index(drop=False, inplace=True)
            self.admin = self.gp[self.gp["GPU-Hours-At-0%"] >= self.gpu_hours_threshold_admin].copy()
            # apply a threshold to focus on the heaviest offenders
            self.gp = self.gp[self.gp["GPU-Hours-At-0%"] >= self.gpu_hours_threshold_user]
            self.df["GPU-Hours-At-0%"] = self.df["GPU-Hours-At-0%"].apply(lambda x:
                                                                          round(x, 1))

    def create_emails(self, method):
        # self.gp is not needed here (could use df)
        g = GreetingFactory().create_greeting(method)
        for user in self.gp.User.unique():
            vfile = f"{self.vpath}/{self.violation}/{user}.csv"
            if self.has_sufficient_time_passed_since_last_email(vfile):
                usr = self.df[self.df.User == user].copy()
                zero_hours = round(self.gp[self.gp.User == user]["GPU-Hours-At-0%"].values[0])
                indent = 4 * " "
                tags = {}
                tags["<GREETING>"] = g.greeting(user)
                tags["<GPU-HOURS>"] = str(zero_hours)
                tags["<DAYS>"] = str(self.days_between_emails)
                tags["<CLUSTER>"] = self.cluster
                tags["<PARTITIONS>"] = ",".join(sorted(set(usr.Partition)))
                tbl = usr.drop(columns=["User", "Partition"]).copy()
                tags["<NUM-JOBS>"] = str(len(usr))
                table = tbl.to_string(index=False, justify="center").split("\n")
                tags["<TABLE>"] = "\n".join([indent + row for row in table])
                tags["<JOBSTATS>"] = f"{indent}$ jobstats {usr.JobID.values[0]}"
                translator = EmailTranslator(self.email_files_path,
                                             self.email_file,
                                             tags)
                email = translator.replace_tags()
                usr["Cluster"] = self.cluster
                usr["Alert-Partitions"] = ",".join(sorted(set(self.partitions)))
                usr["GPU-Hours-At-0%"] = usr["GPU-Hours-At-0%"].apply(lambda x:
                                                                      str(round(x, 1))
                                                                      if x < 5 else
                                                                      str(round(x)))
                usr = usr[["User",
                           "Cluster",
                           "Alert-Partitions",
                           "JobID",
                           "Partition",
                           "GPUs",
                           "GPUs-Unused",
                           "GPU-Hours-At-0%"]]
                self.emails.append((user, email, usr))

    def generate_report_for_admins(self, keep_index: bool=False) -> str:
        if self.admin.empty:
            column_names = ["User",
                            "GPU-Hours-At-0%",
                            "Jobs",
                            "JobID",
                            "Emails"]
            self.admin = pd.DataFrame(columns=column_names)
            return add_dividers(self.create_empty_report(self.admin), self.report_title)
        self.admin["Emails"] = self.admin.User.apply(lambda user:
                                    self.get_emails_sent_count(user, self.violation))
        self.admin.Emails = self.format_email_counts(self.admin.Emails)
        self.admin = self.admin.sort_values(by="GPU-Hours-At-0%", ascending=False)
        self.admin["GPU-Hours-At-0%"] = self.admin["GPU-Hours-At-0%"].apply(round)
        self.admin.reset_index(drop=True, inplace=True)
        self.admin.index += 1
        report_str = self.admin.to_string(index=keep_index, justify="center")
        return add_dividers(report_str, self.report_title)
