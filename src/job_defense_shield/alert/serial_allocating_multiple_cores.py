import pandas as pd
from ..base import Alert
from ..utils import add_dividers
from ..utils import MINUTES_PER_HOUR as mph
from ..efficiency import cpu_efficiency
from ..greeting import GreetingFactory
from ..email_translator import EmailTranslator


class SerialAllocatingMultipleCores(Alert):

    """Find serial codes that have been allocated multiple CPU-Cores."""

    def __init__(self, df, days_between_emails, violation, vpath, **kwargs):
        super().__init__(df, days_between_emails, violation, vpath, **kwargs)

    def _add_required_fields(self):
        if not hasattr(self, "email_subject"):
            self.email_subject = "Serial Jobs Allocating Multiple CPU-Cores"
        if not hasattr(self, "report_title"):
            self.report_title = "Serial Jobs Allocating Multiple CPU-Cores"
        if not hasattr(self, "max_num_jobid_admin"):
            self.max_num_jobid_admin = 3
        if not hasattr(self, "num_jobs_display"):
            self.num_jobs_display = 10
        if not hasattr(self, "num_top_users"):
            self.num_top_users = 5

    def _filter_and_add_new_fields(self):
        self.df = self.df[(self.df.cluster == self.cluster) &
                          (self.df.partition.isin(self.partitions)) &
                          (self.df.nodes == 1) &
                          (self.df.cores > 1) &
                          (~self.df.user.isin(self.excluded_users)) &
                          (self.df["elapsed-hours"] >= self.min_run_time / mph)].copy()
        if not self.df.empty and self.include_running_jobs:
            self.df.admincomment = self.get_admincomment_for_running_jobs()
        self.df = self.df[self.df.admincomment != {}]
        if not self.df.empty and hasattr(self, "nodelist"):
            self.df = self.filter_by_nodelist(self.df)
        self.gp = pd.DataFrame({"User":[]})
        if not self.df.empty:
            # add new fields
            self.df["cpu-eff-tpl"] = self.df.apply(lambda row:
                                                   cpu_efficiency(row["admincomment"],
                                                                  row["elapsedraw"],
                                                                  row["jobid"],
                                                                  row["cluster"],
                                                                  single=True,
                                                                  precision=1),
                                                                  axis="columns")
            self.df["error-code"] = self.df["cpu-eff-tpl"].apply(lambda tpl: tpl[1])
            # drop jobs with non-zero error codes
            self.df = self.df[self.df["error-code"] == 0]
            self.df["cpu-eff"] = self.df["cpu-eff-tpl"].apply(lambda tpl: tpl[0])
            # ignore jobs at 0% CPU-eff (also avoids division by zero later)
            self.df = self.df[self.df["cpu-eff"] > 0]
            # max efficiency if serial is 100% / cores
            self.df["inverse-cores"] = 100 / self.df["cores"]
            self.df["inverse-cores"] = self.df["inverse-cores"].apply(lambda x: round(x, 1))
            self.df["ratio"] = self.df["cpu-eff"] / self.df["inverse-cores"]
            self.df = self.df[(self.df["ratio"] <= 1) &
                              (self.df["ratio"] > self.lower_ratio)]
            renamings = {"elapsed-hours":"Hours",
                         "jobid":"JobID",
                         "user":"User",
                         "partition":"Partition",
                         "cores":"CPU-Cores",
                         "cpu-eff":"CPU-Util",
                         "inverse-cores":"100%/CPU-Cores"}
            self.df = self.df.rename(columns=renamings)
            self.df = self.df[["JobID",
                               "User",
                               "Partition",
                               "CPU-Cores",
                               "CPU-Util",
                               "100%/CPU-Cores",
                               "Hours"]]
            self.df = self.df.sort_values(by=["User", "JobID"])
            self.df["100%/CPU-Cores"] = self.df["100%/CPU-Cores"].apply(lambda x: f"{x}%")
            self.df["CPU-Util"] = self.df["CPU-Util"].apply(lambda x: f"{x}%")
            self.df["cores-minus-1"] = self.df["CPU-Cores"] - 1
            self.df["CPU-Hours-Wasted"] = self.df["Hours"] * self.df["cores-minus-1"]
            def jobid_list(series):
                ellipsis = "+" if len(series) > self.max_num_jobid_admin else ""
                return ",".join(series[:self.max_num_jobid_admin]) + ellipsis
            d = {"CPU-Hours-Wasted":"sum",
                 "User":"size",
                 "CPU-Cores":"mean",
                 "JobID":jobid_list}
            self.gp = self.df.groupby("User").agg(d).rename(columns={"User":"Jobs"})
            self.gp.reset_index(drop=False, inplace=True)
            self.gp = self.gp[self.gp["CPU-Hours-Wasted"] > self.cpu_hours_threshold]
            self.gp = self.gp.head(self.num_top_users)

    def create_emails(self, method):
        g = GreetingFactory().create_greeting(method)
        for user in self.gp.User.unique():
            vfile = f"{self.vpath}/{self.violation}/{user}.csv"
            if self.has_sufficient_time_passed_since_last_email(vfile):
                usr = self.df[self.df.User == user].copy()
                cpu_hours_wasted = round(usr["CPU-Hours-Wasted"].sum())
                #cpu_hours_wasted = self.gp[self.gp.User == user]["CPU-Hours-Wasted"].values[0]
                usr = usr.drop(columns=["User", "cores-minus-1", "CPU-Hours-Wasted"])
                usr["Hours"] = usr["Hours"].apply(lambda hrs: round(hrs, 1))
                num_disp = self.num_jobs_display
                total_jobs = usr.shape[0]
                case = f"{num_disp} of your {total_jobs} jobs" if total_jobs > num_disp else "your jobs"
                # CHANGE NEXT
                if hasattr(self, "cores_per_node"):
                    hours_per_week = 24 * self.days_between_emails
                    num_wasted_nodes = round(cpu_hours_wasted / self.cores_per_node / hours_per_week)
                # create new tag which is two sentences
                # if cores_per_node:
                #Your jobs allocated <CPU-HOURS> CPU-hours that were never used. This is equivalent to
                #making <NUM-NODES> nodes unavailable to all users (including yourself) for 1 week!
                indent = 4 * " "
                # ADDED num_disp but no sort before this
                tbl = usr.head(num_disp).to_string(index=False, justify="center").split("\n")
                tags = {}
                tags["<GREETING>"] = g.greeting(user)
                tags["<CASE>"] = case
                tags["<CLUSTER>"] = self.cluster
                tags["<PARTITIONS>"] = ",".join(sorted(set(usr.Partition)))
                tags["<DAYS>"] = str(self.days_between_emails)
                tags["<NUM-JOBS>"] = str(total_jobs)
                tags["<TABLE>"] = "\n".join([indent + row for row in tbl])
                tags["<JOBSTATS>"] = f"{indent}$ jobstats {usr.JobID.values[0]}"
                tags["<CPU-HOURS>"] = str(cpu_hours_wasted)
                if hasattr(self, "cores_per_node"):
                    tags["<NUM-NODES>"] = str(num_wasted_nodes)
                translator = EmailTranslator(self.email_files_path,
                                             self.email_file,
                                             tags)
                email = translator.replace_tags()
                usr["Cluster"] = self.cluster
                usr["Alert-Partitions"] = ",".join(sorted(set(self.partitions)))
                usr["User"] = user
                usr = usr[["User",
                           "Cluster",
                           "Alert-Partitions",
                           "JobID",
                           "Partition",
                           "CPU-Cores",
                           "CPU-Util",
                           "Hours"]]
                usr["CPU-Cores"] = usr["CPU-Cores"].astype("int64")
                usr["CPU-Util"] = usr["CPU-Util"].apply(lambda x: x.replace("%", ""))
                self.emails.append((user, email, usr))

    def generate_report_for_admins(self, keep_index: bool=False) -> str:
        if self.gp.empty:
            column_names = ["User",
                            "CPU-Hours-Wasted",
                            "AvgCores",
                            "Jobs",
                            "JobID",
                            "Emails"]
            self.gp = pd.DataFrame(columns=column_names)
            return add_dividers(self.create_empty_report(self.gp), self.report_title)
        self.gp["CPU-Hours-Wasted"] = self.gp["CPU-Hours-Wasted"].apply(round)
        self.gp["CPU-Cores"] = self.gp["CPU-Cores"].apply(lambda x:
                                                    str(round(x, 1)).replace(".0", ""))
        self.gp = self.gp.rename(columns={"CPU-Cores":"AvgCores"})
        self.gp.reset_index(drop=False, inplace=True)
        self.gp["Emails"] = self.gp.User.apply(lambda user:
                                 self.get_emails_sent_count(user, self.violation))
        self.gp.Emails = self.format_email_counts(self.gp.Emails)
        cols = ["User", "CPU-Hours-Wasted", "AvgCores", "Jobs", "JobID", "Emails"]
        self.gp = self.gp[cols]
        self.gp = self.gp.sort_values(by="CPU-Hours-Wasted", ascending=False)
        self.gp.reset_index(drop=True, inplace=True)
        self.gp.index += 1
        report_str = self.gp.to_string(index=keep_index, justify="center")
        return add_dividers(report_str, self.report_title)
