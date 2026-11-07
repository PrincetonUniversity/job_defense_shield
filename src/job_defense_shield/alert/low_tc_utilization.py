import os
import pandas as pd
from ..base import Alert
from ..utils import add_dividers
from ..utils import MINUTES_PER_HOUR as mph
from ..efficiency import gpu_efficiency
from ..efficiency import metric_efficiency
from ..greeting import GreetingFactory
from ..email_translator import EmailTranslator


class LowTcUtilization(Alert):

    """Identify users with low Tensor Core utilization. Jobs with a sufficient
       Tensor Core utilization are ignored."""

    def __init__(self, df, days_between_emails, violation, vpath, **kwargs):
        super().__init__(df, days_between_emails, violation, vpath, **kwargs)

    def _add_required_fields(self) -> None:
        if not hasattr(self, "email_subject"):
            self.email_subject = "Jobs with Low Tensor Core Utilization"
        if not hasattr(self, "report_title"):
            self.report_title = "Low Tensor Core Utilization"
        if not hasattr(self, "max_num_jobid_admin"):
            self.max_num_jobid_admin = 2
        if not hasattr(self, "num_top_users"):
            self.num_top_users = 15
        if not hasattr(self, "gpu_hours_thres_user"):
            self.gpu_hours_thres_user = 0
        if not hasattr(self, "gpu_hours_thres_admin"):
            self.gpu_hours_thres_admin = 0
        if not hasattr(self, "num_jobs_display"):
            self.num_jobs_display = 5

    def _filter_and_add_new_fields(self) -> None:
        self.df = self.df[(self.df["cluster"] == self.cluster) &
                          (self.df["gpus"] > 0) &
                          (~self.df["qos"].isin(self.excluded_qos)) &
                          (~self.df["partition"].isin(self.excluded_partitions)) &
                          (~self.df["user"].isin(self.excluded_users)) &
                          (self.df["admincomment"].astype(bool)) &
                          (self.df["elapsed-hours"] >= self.min_run_time / mph)].copy()
        if "*" not in self.partitions:
            self.df = self.df[self.df["partition"].isin(self.partitions)]
        if not self.df.empty and hasattr(self, "nodelist"):
            self.df = self.filter_by_nodelist(self.df)
        # handle empty dataframe case
        self.admin = pd.DataFrame({"User": []})
        # add gpu utilization
        if self.df.empty:
            return None
        self.df["gpu-tuple"] = self.df.apply(lambda row:
                                             gpu_efficiency(row["admincomment"],
                                                            row["elapsedraw"],
                                                            row["jobid"],
                                                            row["cluster"],
                                                            verbose=self.verbose),
                                                            axis="columns")
        cols = ["gpu-seconds-used", "gpu-seconds-total", "gpu-error-code"]
        self.df[cols] = pd.DataFrame(self.df["gpu-tuple"].tolist(), index=self.df.index)
        self.df = self.df[(self.df["gpu-error-code"] == 0) & (self.df["gpu-seconds-total"] > 0)]
        self.df["gpu-util"] = 100 * self.df["gpu-seconds-used"] / self.df["gpu-seconds-total"]
        self.df = self.df[self.df["gpu-util"] >= self.util_thres_pct]
        # add tc utilization
        if self.df.empty:
            return None
        self.df["tc-tuple"] = self.df.apply(lambda row:
                                            metric_efficiency(row["admincomment"],
                                                              row["elapsedraw"],
                                                              row["jobid"],
                                                              row["cluster"],
                                                              "any_tensor_util_percent_avg",
                                                              verbose=self.verbose),
                                                              axis="columns")
        cols = ["tc-seconds-used", "tc-seconds-total", "tc-error-code"]
        self.df[cols] = pd.DataFrame(self.df["tc-tuple"].tolist(), index=self.df.index)
        self.df = self.df[(self.df["tc-error-code"] == 0) & (self.df["tc-seconds-total"] > 0)]
        self.df["tc-util"] = 100 * self.df["tc-seconds-used"] / self.df["tc-seconds-total"]
        self.df = self.df[self.df["tc-util"] <= self.tc_thres_pct]
        # aggregate the results
        if self.df.empty:
            return None
        self.df["GPU-Hours"] = self.df["gpus"] * self.df["elapsed-hours"]
        self.df["waste-score"] = (100 - self.df["tc-util"]) * self.df["GPU-Hours"]
        self.df.sort_values(by=["user", "waste-score"], ascending=[True, False], inplace=True)
        def jobid_list(series):
            ellipsis = "+" if len(series) > self.max_num_jobid_admin else ""
            return ",".join(series[:self.max_num_jobid_admin]) + ellipsis
        d = {"user": "size",
             "GPU-Hours": "sum",
             "gpu-seconds-used": "sum",
             "gpu-seconds-total": "sum",
             "tc-seconds-used": "sum",
             "tc-seconds-total": "sum",
             "jobid": jobid_list}
        self.admin = self.df.groupby("user").agg(d).rename(columns={"user": "jobs"})
        self.admin.reset_index(drop=False, inplace=True)
        self.admin.sort_values(by="GPU-Hours", ascending=False, inplace=True)
        self.admin = self.admin.head(self.num_top_users)
        self.admin["gpu-util"] = 100 * self.admin["gpu-seconds-used"] / self.admin["gpu-seconds-total"]
        self.admin["tc-util"]  = 100 * self.admin["tc-seconds-used"]  / self.admin["tc-seconds-total"]
        cols = ["user",
                "GPU-Hours",
                "gpu-util",
                "tc-util",
                "jobs",
                "jobid"]
        self.admin = self.admin[cols]
        renamings = {"jobs": "Jobs",
                     "jobid": "JobID",
                     "user": "User",
                     "cluster": "Cluster",
                     "partition": "Partition",
                     "gpus": "GPUs",
                     "gpu-util": "GPU-Util",
                     "tc-util": "TC-Util"}
        self.admin = self.admin.rename(columns=renamings)
        self.df = self.df.rename(columns=renamings)
        self.admin["GPU-Util"] = self.admin["GPU-Util"].round().astype(int)
        self.admin["TC-Util"] = self.admin["TC-Util"].round().astype(int)

    def create_emails(self, method: str) -> None:
        g = GreetingFactory(self.ldap).create_greeting(method)
        for _, row in self.admin.iterrows():
            hrs_val = row["GPU-Hours"]
            if hrs_val < self.gpu_hours_thres_user:
                continue
            user = row["User"]
            vfile = os.path.join(self.vbase, f"{user}.csv")
            if self.has_sufficient_time_passed_since_last_email(vfile):
                usr = self.df[self.df["User"] == user].copy()
                num_disp = self.num_jobs_display
                total_jobs = usr.shape[0]
                case = f"{num_disp} of your {total_jobs} jobs" if total_jobs > num_disp else "your jobs"
                indent = 4 * " "
                tags = {}
                tags["<GREETING>"] = g.greeting(user)
                tags["<CASE>"] = case
                tags["<DAYS>"] = str(self.days_between_emails)
                tags["<CLUSTER>"] = self.cluster
                tags["<PARTITIONS>"] = ",".join(sorted(set(usr.Partition)))
                tags["<GPU-HOURS>"] = str(round(hrs_val))
                util_val = row["GPU-Util"]
                tags["<GPU-UTIL>"] = str(util_val)
                tc_val = row["TC-Util"]
                tags["<TC-UTIL>"] = str(tc_val)
                tags["<NUM-JOBS>"] = str(total_jobs)
                tbl = usr[["JobID", "Cluster", "Partition", "GPU-Hours", "GPU-Util", "TC-Util"]].head(num_disp).copy()
                tbl.sort_values(by="JobID", inplace=True)
                tbl["GPU-Hours"] = tbl["GPU-Hours"].apply(lambda x: f"{x:.1f}" if x < 2.5 else f"{round(x)}")
                tbl["GPU-Util"] = tbl["GPU-Util"].apply(lambda x: f"{round(x)}%")
                tbl["TC-Util"] = tbl["TC-Util"].apply(lambda x: f"{round(x)}%")
                table = tbl.to_string(index=False, justify="center").split("\n")
                tags["<TABLE>"] = "\n".join([indent + line for line in table])
                tags["<JOBSTATS>"] = f"{indent}$ jobstats {usr.JobID.values[0]}"
                translator = EmailTranslator(self.email_files_path,
                                             self.email_file,
                                             tags)
                email = translator.replace_tags()
                if "*" in self.partitions:
                    ap = "ALL-PARTITIONS"
                else:
                    ap = ",".join(sorted(set(self.partitions)))
                usr = pd.DataFrame({"User": user,
                                    "Cluster": self.cluster,
                                    "Alert-Partitions": ap,
                                    "Jobs": total_jobs,
                                    "JobID": row["JobID"],
                                    "GPU-Hours": round(hrs_val),
                                    "GPU-Util": util_val,
                                    "TC-Util": tc_val}, index=[0])
                self.emails.append((user, email, usr))

    def generate_report_for_admins(self, keep_index: bool=False) -> str:
        if not self.admin.empty and not self.show_all_users:
            filters = (self.admin["GPU-Hours"] >= self.gpu_hours_thres_admin)
            self.admin = self.admin[filters]
        if self.admin.empty:
            if not self.show_empty_reports:
                return ""
            column_names = ["User",
                            "GPU-Hours",
                            "GPU-Util",
                            "TC-Util",
                            "Jobs",
                            "JobID",
                            "Emails"]
            self.admin = pd.DataFrame(columns=column_names)
            return add_dividers(self.create_empty_report(self.admin), self.report_title)
        self.admin["Emails"] = self.admin["User"].apply(lambda user:
                                    self.get_emails_sent_count(user, self.violation))
        self.admin["Emails"] = self.format_email_counts(self.admin.Emails)
        self.admin["GPU-Hours"] = self.admin["GPU-Hours"].round().astype(int)
        self.admin["GPU-Util"] = self.admin["GPU-Util"].apply(lambda x: f"{x}%")
        self.admin["TC-Util"] = self.admin["TC-Util"].apply(lambda x: f"{x}%")
        self.admin.reset_index(drop=True, inplace=True)
        self.admin.index += 1
        report_str = self.admin.to_string(index=keep_index, justify="center")
        return add_dividers(report_str, self.report_title)
