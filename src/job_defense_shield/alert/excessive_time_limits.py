import pandas as pd
from ..base import Alert
from ..utils import SECONDS_PER_MINUTE as spm
from ..utils import SECONDS_PER_HOUR as sph
from ..utils import MINUTES_PER_HOUR as mph
from ..utils import seconds_to_slurm_time_format
from ..utils import add_dividers
from ..greeting import GreetingFactory
from ..email_translator import EmailTranslator


class ExcessiveTimeLimits(Alert):

    """Excessive run time limits."""

    def __init__(self, df, days_between_emails, violation, vpath, **kwargs):
        super().__init__(df, days_between_emails, violation, vpath, **kwargs)

    def _add_required_fields(self):
        m = self.mode.upper()
        if not hasattr(self, "email_subject"):
            self.email_subject = f"Requesting Too Much Time for {m} Jobs"
        if not hasattr(self, "report_title"):
            self.report_title = f"Excessive Run Time Limits for {m} Jobs"
        if not hasattr(self, "num_top_users"):
            self.num_top_users = 10
        if not hasattr(self, "num_jobs_display"):
            self.num_jobs_display = 10
        if not hasattr(self, "mean_ratio_threshold"):
            self.mean_ratio_threshold = 1.0
        if not hasattr(self, "median_ratio_threshold"):
            self.median_ratio_threshold = 1.0

    def _filter_and_add_new_fields(self):
        self.df = self.df[(self.df.cluster == self.cluster) &
                          (self.df.partition.isin(self.partitions)) &
                          (self.df.state.isin(["COMPLETED"])) &
                          (~self.df.user.isin(self.excluded_users)) &
                          (self.df["elapsed-hours"] >= self.min_run_time / mph)].copy()

        self.df = self.df[self.df.admincomment != {}]
        if not self.df.empty and hasattr(self, "nodelist"):
            self.df = self.filter_by_nodelist(self.df)
        self.gp = pd.DataFrame({"User":[]})
        if not self.df.empty:
            xpu = self.mode
            if xpu == "cpu":
                self.df[f"{xpu}-waste-hours"] = (self.df["limit-minutes"] * spm - self.df["elapsedraw"]) * self.df.cores / sph
                self.df[f"{xpu}-alloc-hours"] = self.df["limit-minutes"] * spm * self.df.cores / sph
            elif xpu == "gpu":
                self.df[f"{xpu}-waste-hours"] = (self.df["limit-minutes"] * spm - self.df["elapsedraw"]) * self.df.gpus / sph
                self.df[f"{xpu}-alloc-hours"] = self.df["limit-minutes"] * spm * self.df.gpus / sph
            self.df["mean-ratio"] = self.df[f"{xpu}-hours"] / self.df[f"{xpu}-alloc-hours"]
            self.df["median-ratio"] = self.df[f"{xpu}-hours"] / self.df[f"{xpu}-alloc-hours"]
            d = {f"{xpu}-waste-hours":"sum",
                 f"{xpu}-alloc-hours":"sum",
                 f"{xpu}-hours":"sum",
                 "user":"size",
                 "partition":lambda series: ",".join(sorted(set(series))),
                 "mean-ratio":"mean",
                 "median-ratio":"median"}
            self.gp = self.df.groupby("user").agg(d).rename(columns={"user":"jobs"})
            self.gp = self.gp.sort_values(by=f"{xpu}-hours", ascending=False).reset_index(drop=False)
            self.gp["rank"] = self.gp.index + 1
            self.gp = self.gp.sort_values(by=f"{xpu}-waste-hours", ascending=False).reset_index(drop=False)
            self.gp.index += 1
            self.gp["overall-ratio"] = self.gp[f"{xpu}-hours"] / self.gp[f"{xpu}-alloc-hours"]
            self.gp = self.gp[(self.gp[f"{xpu}-waste-hours"] > self.absolute_thres_hours) &
                              (self.gp["overall-ratio"] < self.overall_ratio_threshold) &
                              (self.gp["mean-ratio"] < self.mean_ratio_threshold) &
                              (self.gp["median-ratio"] < self.median_ratio_threshold)]
            if self.num_top_users:
                self.gp = self.gp[self.gp.index <= self.num_top_users]
            cols = ["user",
                    f"{xpu}-waste-hours",
                    f"{xpu}-hours",
                    "overall-ratio",
                    "mean-ratio",
                    "median-ratio",
                    "rank",
                    "jobs",
                    "partition"]
            self.gp = self.gp[cols]
            self.gp["cluster"] = self.cluster
            renamings = {"user":"User",
                         "partition":"Partitions",
                         f"{xpu}-waste-hours":f"{xpu.upper()}-Hours-Unused"}
            self.gp = self.gp.rename(columns=renamings)

    def create_emails(self, method):
        g = GreetingFactory().create_greeting(method)
        for user in self.gp.User.unique():
            vfile = f"{self.vpath}/{self.violation}/{user}.csv"
            if self.has_sufficient_time_passed_since_last_email(vfile):
                usr = self.gp[self.gp.User == user].copy()
                jobs = self.df[self.df.user == user].copy()
                xpu = self.mode
                num_disp = self.num_jobs_display
                total_jobs = jobs.shape[0]
                case = f"{num_disp} of your {total_jobs} jobs" if total_jobs > num_disp else "your jobs"
                jobs = jobs.sort_values(by=f"{xpu}-waste-hours", ascending=False).head(num_disp)
                jobs["Time-Used"] = jobs["elapsedraw"].apply(seconds_to_slurm_time_format)
                jobs["Time-Allocated"] = jobs["limit-minutes"].apply(lambda x:
                                                                     seconds_to_slurm_time_format(spm * x))
                jobs["Percent-Used"] = jobs["mean-ratio"].apply(lambda x: f"{round(100 * x)}%")
                cols = ["jobid", "Time-Used", "Time-Allocated", "Percent-Used", "cores"]
                jobs = jobs[cols].sort_values(by="jobid")
                renamings = {"jobid":"JobID", "cores":"CPU-Cores"}
                jobs = jobs.rename(columns=renamings)
                indent = 4 * " "
                table = jobs.to_string(index=False, justify="center").split("\n")
                tags = {}
                tags["<GREETING>"] = g.greeting(user)
                tags["<CASE>"] = case
                tags["<DAYS>"] = str(self.days_between_emails)
                tags["<CLUSTER>"] = self.cluster
                tags["<PARTITIONS>"] = usr.Partitions.values[0]
                tags["<MODE-UPPER>"] = self.mode.upper()
                tags["<AVERAGE>"] = str(round(100 * usr["mean-ratio"].values[0]))
                tags["<NUM-JOBS>"] = str(total_jobs)
                tags["<NUM-JOBS-DISPLAY>"] = str(total_jobs)
                tags["<TABLE>"] = "\n".join([indent + row for row in table])
                tags["<UNUSED-HOURS>"] = str(round(usr[f"{xpu.upper()}-Hours-Unused"].values[0]))
                translator = EmailTranslator(self.email_files_path,
                                             self.email_file,
                                             tags)
                email = translator.replace_tags()
                usr["Cluster"] = self.cluster
                usr["Alert-Partitions"] = ",".join(sorted(set(self.partitions)))
                usr["Jobs"] = total_jobs
                usr = usr[["User",
                           "Cluster",
                           "Alert-Partitions",
                           f"{xpu.upper()}-Hours-Unused",
                           "Jobs"]]
                self.emails.append((user, email, usr))

    def generate_report_for_admins(self, keep_index: bool=False) -> str:
        """Generate a table for system administrators."""
        xpu = self.mode
        if self.gp.empty:
            column_names = ["User",
                            f"{xpu.upper()}-Hours-Unused",
                            f"{xpu.upper()}-Hours",
                            "Ratio-Overall",
                            "Ratio-Mean",
                            "Ratio-Median",
                            f"{xpu.upper()}-Rank",
                            "Jobs",
                            "Emails"]
            self.gp = pd.DataFrame(columns=column_names)
            return add_dividers(self.create_empty_report(self.gp), self.report_title)
        self.gp = self.gp.drop(columns=["cluster", "Partitions"])
        self.gp["Emails"] = self.gp.User.apply(lambda user:
                                 self.get_emails_sent_count(user, self.violation))
        self.gp.Emails = self.format_email_counts(self.gp.Emails)
        cols = [f"{xpu.upper()}-Hours-Unused", f"{xpu}-hours"]
        self.gp[cols] = self.gp[cols].apply(round).astype("int64")
        cols = ["overall-ratio", "mean-ratio", "median-ratio"]
        self.gp[cols] = self.gp[cols].apply(lambda x: round(x, 2))
        column_names = pd.MultiIndex.from_tuples([('User', ''),
                                                  (f'{xpu.upper()}-Hours ', '(Unused)'),
                                                  (f'{xpu.upper()}-Hours', '(Used)'),
                                                  ('Ratio', 'Overall'),
                                                  ('Ratio ', 'Mean'),
                                                  (' Ratio', 'Median'),
                                                  (f'{xpu.upper()}-Rank', ''),
                                                  ('Jobs', ''),
                                                  ('Emails', '')])
        self.gp.columns = column_names
        report_str = self.gp.to_string(index=keep_index, justify="center")
        return add_dividers(report_str, self.report_title, units_row=True)

class ExcessiveTimeLimitsCPU(ExcessiveTimeLimits):

    """Specialized implementation of ExcessiveTimeLimits for CPUs."""

    def __init__(self, df, days_between_emails, violation, vpath, **kwargs):
        self.mode = "cpu"
        super().__init__(df, days_between_emails, violation, vpath, **kwargs)


class ExcessiveTimeLimitsGPU(ExcessiveTimeLimits):

    """Specialized implementation of ExcessiveTimeLimits for GPUs."""

    def __init__(self, df, days_between_emails, violation, vpath, **kwargs):
        self.mode = "gpu"
        super().__init__(df, days_between_emails, violation, vpath, **kwargs)
