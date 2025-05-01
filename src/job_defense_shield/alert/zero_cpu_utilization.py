import pandas as pd
from ..base import Alert
from ..utils import add_dividers
from ..utils import MINUTES_PER_HOUR as mph
from ..efficiency import cpu_nodes_with_zero_util
from ..greeting import GreetingFactory
from ..email_translator import EmailTranslator


class ZeroCPU(Alert):

    """CPU jobs with zero utilization on one or more nodes."""

    def __init__(self, df, days_between_emails, violation, vpath, **kwargs):
        super().__init__(df, days_between_emails, violation, vpath, **kwargs)

    def _add_required_fields(self):
        if not hasattr(self, "email_subject"):
            self.email_subject = "Jobs with Zero CPU Utilization"
        if not hasattr(self, "report_title"):
            self.report_title = "Jobs with Zero CPU Utilization"
        if not hasattr(self, "cpu_hours_threshold"):
            self.cpu_hours_threshold = None

    def _filter_and_add_new_fields(self):
        self.df = self.df[(self.df.cluster == self.cluster) &
                          (self.df.partition.isin(self.partitions)) &
                          (~self.df.user.isin(self.excluded_users)) &
                          (self.df["elapsed-hours"] >= self.min_run_time / mph)].copy()
        if not self.df.empty and self.include_running_jobs:
            self.df.admincomment = self.get_admincomment_for_running_jobs()
        self.df = self.df[self.df.admincomment != {}]
        if not self.df.empty and hasattr(self, "nodelist"):
            self.df = self.filter_by_nodelist(self.df)
        self.df.rename(columns={"user":"User"}, inplace=True)
        # add new fields
        if not self.df.empty:
            self.df["nodes-tuple"] = self.df.apply(lambda row:
                                     cpu_nodes_with_zero_util(row["admincomment"],
                                                              row["jobid"],
                                                              row["cluster"]),
                                                              axis="columns")
            cols = ["nodes-unused", "error_code"]
            self.df[cols] = pd.DataFrame(self.df["nodes-tuple"].tolist(), index=self.df.index)
            self.df = self.df[(self.df["error_code"] == 0) & (self.df["nodes-unused"] > 0)]
            def is_interactive(jobname):
                if jobname.startswith("sys/dashboard") or jobname.startswith("interactive"):
                    return True
                return False
            self.df["interactive"] = self.df["jobname"].apply(is_interactive)
            self.df["CPU-Util-Unused"] = "0%"
            if self.cpu_hours_threshold is not None:
                # remove users within insufficient cpu-hours at 0%
                self.df["cpu-hours-at-0%"] = (self.df.cores / self.df.nodes) * \
                                             self.df["nodes-unused"] * self.df["elapsed-hours"]
                total_hrs = self.df.groupby("User").agg({"cpu-hours-at-0%":"sum"}).reset_index()
                total_hrs = total_hrs[total_hrs["cpu-hours-at-0%"] >= self.cpu_hours_threshold]
                self.df = self.df[self.df.User.isin(total_hrs.User)]
                del total_hrs
            cols = ["jobid",
                    "User",
                    "partition",
                    "cluster",
                    "nodes",
                    "nodes-unused",
                    "CPU-Util-Unused",
                    "cores",
                    "elapsed-hours"]
            self.df = self.df[cols]
            renamings = {"jobid":"JobID",
                         "cluster":"Cluster",
                         "partition":"Partition",
                         "nodes":"Nodes",
                         "nodes-unused":"Nodes-Unused",
                         "cores":"Cores",
                         "elapsed-hours":"Hours"}
            self.df = self.df.rename(columns=renamings)
            self.df["Hours"] = self.df["Hours"].apply(lambda x: str(round(x, 1))
                                                      if x < 5 else str(round(x)))

    def create_emails(self, method):
        g = GreetingFactory().create_greeting(method)
        for user in self.df.User.unique():
            vfile = f"{self.vpath}/{self.violation}/{user}.csv"
            if self.has_sufficient_time_passed_since_last_email(vfile):
                usr = self.df[self.df.User == user].copy()
                if len(usr) == 1 and \
                   usr.Nodes.values[0] == 1 and \
                   usr.Cores.values[0] < 4:
                    continue
                tbl = usr.drop(columns=["User", "Partition"]).copy()
                indent = 4 * " "
                table = tbl.to_string(index=False, justify="center").split("\n")
                tags = {}
                tags["<GREETING>"] = g.greeting(user)
                tags["<DAYS>"] = str(self.days_between_emails)
                tags["<CLUSTER>"] = self.cluster
                tags["<PARTITIONS>"] = ",".join(sorted(set(self.partitions)))
                tags["<NUM-JOBS>"] = str(len(usr))
                tags["<TABLE>"] = "\n".join([indent + row for row in table])
                tags["<JOBSTATS>"] = f"{indent}$ jobstats {usr.JobID.values[0]}"
                translator = EmailTranslator(self.email_files_path,
                                             self.email_file,
                                             tags)
                email = translator.replace_tags()
                usr["Cluster"] = self.cluster
                usr["Alert-Partitions"] = ",".join(sorted(set(self.partitions)))
                usr = usr[["User",
                           "Cluster",
                           "Alert-Partitions",
                           "JobID",
                           "Partition",
                           "Nodes",
                           "Nodes-Unused",
                           "Hours"]]
                self.emails.append((user, email, usr))

    def generate_report_for_admins(self, keep_index: bool=False) -> str:
        """Rename some of the columns."""
        if self.df.empty:
            column_names = ["JobID",
                            "User",
                            "Nodes",
                            "Nodes-Unused",
                            "CPU-Util-Unused",
                            "Cores",
                            "Hours",
                            "Emails"]
            self.df = pd.DataFrame(columns=column_names)
            return add_dividers(self.create_empty_report(self.df), self.report_title)
        self.df = self.df.drop(columns=["Cluster"])
        self.df = self.df.sort_values(["User", "JobID"])
        self.df["Emails"] = self.df.User.apply(lambda user:
                                 self.get_emails_sent_count(user, self.violation))
        self.df.Emails = self.format_email_counts(self.df.Emails)
        report_str = self.df.to_string(index=keep_index, justify="center")
        return add_dividers(report_str, self.report_title)
