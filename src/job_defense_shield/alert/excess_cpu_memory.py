import pandas as pd
from ..base import Alert
from ..efficiency import cpu_memory_usage
from ..utils import add_dividers
from ..utils import MINUTES_PER_HOUR as mph
from ..greeting import GreetingFactory
from ..email_translator import EmailTranslator


class ExcessCPUMemory(Alert):

    """Find users that are allocating too much CPU memory."""
 
    def __init__(self, df, days_between_emails, violation, vpath, **kwargs):
        super().__init__(df, days_between_emails, violation, vpath, **kwargs)

    def _add_required_fields(self):
        if not hasattr(self, "email_subject"):
            self.email_subject = "Jobs Requesting Too Much CPU Memory"
        if not hasattr(self, "report_title"):
            self.report_title = "Users Allocating Excess CPU Memory"
        if not hasattr(self, "combine_partitions"):
            self.combine_partitions = False
        if not hasattr(self, "num_top_users"):
            self.num_top_users = 15
        if not hasattr(self, "num_jobs_display"):
            self.num_jobs_display = 10

    def _filter_and_add_new_fields(self):
        # exclude gpu jobs?
        self.df = self.df[(self.df.cluster == self.cluster) &
                          (self.df.partition.isin(self.partitions)) &
                          (self.df.state != "OUT_OF_MEMORY") &
                          (~self.df.user.isin(self.excluded_users)) &
                          (self.df["elapsed-hours"] >= self.min_run_time / mph)].copy()
        if not self.df.empty and self.include_running_jobs:
            self.df.admincomment = self.get_admincomment_for_running_jobs()
        self.df = self.df[self.df.admincomment != {}]
        if not self.df.empty and hasattr(self, "nodelist"):
            self.df = self.filter_by_nodelist(self.df)
        if self.combine_partitions:
            self.df.partition = ",".join(sorted(set(self.partitions)))
        if hasattr(self, "cores_fraction") and hasattr(self, "cores_per_node"):
            # only consider jobs that do not use (approximately) full nodes
            thres = self.cores_fraction * self.cores_per_node
            self.df = self.df[self.df["cores"] / self.df["nodes"] <= thres]
        # initialize gp and admin in case df is empty
        self.gp = pd.DataFrame({"User":[]})
        self.admin = pd.DataFrame()
        # add new fields
        if not self.df.empty:
            self.df["memory-tuple"] = self.df.apply(lambda row:
                                                    cpu_memory_usage(row["admincomment"],
                                                                     row["jobid"],
                                                                     row["cluster"]),
                                                                     axis="columns")
            self.df["mem-used"]   = self.df["memory-tuple"].apply(lambda x: x[0])
            self.df["mem-alloc"]  = self.df["memory-tuple"].apply(lambda x: x[1])
            self.df["mem-unused"] = self.df["mem-alloc"] - self.df["mem-used"]
            # filter out jobs using approximately default memory
            self.df["GB-per-core"] = self.df["mem-alloc"] / self.df["cores"]
            if hasattr(self, "mem_per_node") and hasattr(self, "cores_per_node"):
                # ignore jobs using default memory or less?
                thres = self.mem_per_node / self.cores_per_node
                self.df = self.df[self.df["GB-per-core"] > thres]
            # IF STATEMENT
            GB_per_TB = 1000
            self.df["mem-hrs-used"]   = self.df["mem-used"] * self.df["elapsed-hours"] / GB_per_TB
            self.df["mem-hrs-alloc"]  = self.df["mem-alloc"] * self.df["elapsed-hours"] / GB_per_TB
            self.df["mem-hrs-unused"] = self.df["mem-hrs-alloc"] - self.df["mem-hrs-used"]
            self.df["mean-ratio"]     = self.df["mem-hrs-used"] / self.df["mem-hrs-alloc"]
            self.df["median-ratio"]   = self.df["mem-hrs-used"] / self.df["mem-hrs-alloc"]
            # compute various quantities by grouping by user
            d = {"mem-hrs-used":"sum",
                 "mem-hrs-alloc":"sum",
                 "mem-hrs-unused":"sum",
                 "elapsed-hours":"sum",
                 "cores":"mean",
                 "cpu-hours":"sum",
                 "account":pd.Series.mode,
                 "mean-ratio":"mean",
                 "median-ratio":"median",
                 "user":"size"}
            self.gp = self.df.groupby(["cluster", "partition", "user"]).agg(d)
            self.gp = self.gp.rename(columns={"user":"jobs"})
            self.gp.reset_index(drop=False, inplace=True)
            total_mem_hours = self.gp["mem-hrs-alloc"].sum()
            assert total_mem_hours != 0, "total_mem_hours found to be zero"
            self.gp["proportion"] = self.gp["mem-hrs-alloc"] / total_mem_hours
            self.gp["Ratio"] = self.gp["mem-hrs-used"] / self.gp["mem-hrs-alloc"]
            self.gp = self.gp.sort_values("mem-hrs-unused", ascending=False)
            cols = ["cluster",
                    "partition",
                    "user",
                    "account",
                    "proportion",
                    "mem-hrs-unused",
                    "mem-hrs-used",
                    "mem-hrs-alloc",
                    "Ratio",
                    "median-ratio",
                    "mean-ratio",
                    "elapsed-hours",
                    "cores",
                    "cpu-hours",
                    "jobs"]
            self.gp = self.gp[cols]
            renamings = {"user":"User",
                         "elapsed-hours":"hrs",
                         "mem-hrs-unused":"Mem-Hrs-Unused",
                         "cores":"avg-cores",
                         "cpu-hours":"cpu-hrs"}
            self.gp = self.gp.rename(columns=renamings)
            self.gp["emails"] = self.gp["User"].apply(lambda user:
                                     self.get_emails_sent_count(user, self.violation))
            cols = ["Mem-Hrs-Unused", "mem-hrs-used", "mem-hrs-alloc", "cpu-hrs"]
            self.gp[cols] = self.gp[cols].apply(round).astype("int64")
            cols = ["proportion", "Ratio", "mean-ratio", "median-ratio"]
            self.gp[cols] = self.gp[cols].apply(lambda x: round(x, 2))
            self.gp["avg-cores"] = self.gp["avg-cores"].apply(lambda x: round(x, 1))
            self.gp.reset_index(drop=True, inplace=True)
            self.gp.index += 1
            self.gp = self.gp.head(self.num_top_users)
            self.admin = self.gp.copy()
            self.gp = self.gp[(self.gp["Mem-Hrs-Unused"] > self.tb_hours_threshold) &
                              (self.gp["Ratio"] <= self.ratio_threshold) &
                              (self.gp["mean-ratio"] <= self.mean_ratio_threshold) &
                              (self.gp["median-ratio"] <= self.median_ratio_threshold)]

    def create_emails(self, method):
        g = GreetingFactory().create_greeting(method)
        for user in self.gp.User.unique():
            vfile = f"{self.vpath}/{self.violation}/{user}.csv"
            if self.has_sufficient_time_passed_since_last_email(vfile):
                usr = self.gp[self.gp.User == user].copy()
                jobs = self.df[self.df.user == user].copy()
                num_disp = self.num_jobs_display
                total_jobs = jobs.shape[0]
                case = f"{num_disp} of your {total_jobs} jobs" if total_jobs > num_disp else "your jobs"
                pct = round(100 * usr["mean-ratio"].values[0])
                unused = usr["Mem-Hrs-Unused"].values[0]
                if hasattr(self, "mem_per_node"):
                    hours_per_period = self.days_between_emails * 24
                    tb_mem_per_node = self.mem_per_node / 1e3
                    num_wasted_nodes = round(unused / hours_per_period / tb_mem_per_node)
                jobs = jobs.sort_values(by="mem-hrs-unused", ascending=False).head(num_disp)
                jobs = jobs[["jobid",
                             "mem-used",
                             "mem-alloc",
                             "mean-ratio",
                             "cores",
                             "elapsed-hours"]]
                jobs["mem-used"]   = jobs["mem-used"].apply(lambda x: f"{round(x)} GB")
                jobs["mem-alloc"]  = jobs["mem-alloc"].apply(lambda x: f"{round(x)} GB")
                jobs["mean-ratio"] = jobs["mean-ratio"].apply(lambda x: f"{round(100 * x)}%")
                jobs = jobs.sort_values(by="jobid")
                renamings = {"jobid":"JobID",
                             "mem-used":"Memory-Used",
                             "mem-alloc":"Memory-Allocated",
                             "mean-ratio":"Percent-Used",
                             "cores":"Cores",
                             "elapsed-hours":"Hours"}
                jobs = jobs.rename(columns=renamings)
                jobs["Hours"] = jobs["Hours"].apply(lambda hrs: round(hrs, 1))
                indent = 4 * " "
                tags = {}
                tags["<GREETING>"] = g.greeting(user)
                tags["<CASE>"] = case
                tags["<DAYS>"] = str(self.days_between_emails)
                tags["<CLUSTER>"] = self.cluster
                tags["<PARTITIONS>"] = ','.join(sorted(set(usr.partition)))
                tags["<PERCENT>"] = f"{pct}%"
                tags["<NUM-JOBS>"] = str(total_jobs)
                # is next line optional based on config params?
                if hasattr(self, "mem_per_node"):
                    tags["<NUM-WASTED-NODES>"] = str(num_wasted_nodes)
                tags["<UNUSED>"] = str(usr["Mem-Hrs-Unused"].values[0])
                table = jobs.to_string(index=False, justify="center").split("\n")
                tags["<TABLE>"] = "\n".join([indent + row for row in table])
                tags["<JOBSTATS>"] = f"{indent}$ jobstats {jobs.JobID.values[0]}"
                # need a way to send a stern message at times
                # if x > self.some_threshold and os.path.exists(stern_version) then self.email_file += "_stern"
                translator = EmailTranslator(self.email_files_path,
                                             self.email_file,
                                             tags)
                email = translator.replace_tags()
                usr["Cluster"] = self.cluster
                usr["Alert-Partitions"] = ",".join(sorted(set(self.partitions)))
                usr = usr[["User",
                           "Cluster",
                           "Alert-Partitions",
                           "Mem-Hrs-Unused",
                           "Ratio"]]
                self.emails.append((user, email, usr))

    def generate_report_for_admins(self, keep_index: bool=False) -> str:
        """Drop and rename some of the columns."""
        if self.admin.empty:
            column_names = ["User",
                            "Proportion",
                            "Mem-Hrs-Unused",
                            "Mem-Hrs-Used",
                            "Ratio",
                            "Mean-Ratio",
                            "Median-Ratio",
                            "CPU-Hrs",
                            "Jobs",
                            "Emails"]
            self.admin = pd.DataFrame(columns=column_names)
            return add_dividers(self.create_empty_report(self.admin), self.report_title)
        cols = ["User",
                "Mem-Hrs-Unused",
                "mem-hrs-used",
                "Ratio",
                "mean-ratio",
                "median-ratio",
                "proportion",
                "cpu-hrs",
                "jobs"]
        self.admin = self.admin[cols]
        self.admin["Emails"] = self.admin.User.apply(lambda user:
                                    self.get_emails_sent_count(user, self.violation))
        self.admin.Emails = self.format_email_counts(self.admin.Emails)
        column_names = pd.MultiIndex.from_tuples([('User', ''),
                                                  ('Unused', '(TB-Hrs)'),
                                                  ('Used', '(TB-Hrs)'),
                                                  ('Ratio', 'Overall'),
                                                  ('Ratio ', 'Mean'),
                                                  (' Ratio', 'Median'),
                                                  ('Proportion', ''),
                                                  ('CPU-Hrs', ''),
                                                  ('Jobs', ''),
                                                  ('Emails', '')])
        self.admin.columns = column_names
        report_str = self.admin.to_string(index=keep_index, justify="center")
        return add_dividers(report_str, self.report_title, units_row=True)
