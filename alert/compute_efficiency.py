import textwrap
import pandas as pd
from base import Alert
from efficiency import cpu_efficiency
from efficiency import gpu_efficiency
from utils import SECONDS_PER_HOUR
from utils import send_email
from utils import add_dividers
from greeting import GreetingFactory


class LowEfficiency(Alert):

    """Low CPU or GPU utilization. The first part computes the proportion
       of CPU/GPU hours for each user. How to turn the filters on or off
       for admin reports."""

    def __init__(self, df, days_between_emails, violation, vpath, subject, **kwargs):
        super().__init__(df, days_between_emails, violation, vpath, subject, **kwargs)

    def _filter_and_add_new_fields(self):
        # compute proportion (self.pr) using as much data as possible
        self.pr = self.df[(self.df.cluster == self.cluster) &
                          (self.df.partition.isin(self.partitions)) &
                          pd.notna(self.df[f"{self.xpu}-seconds"])].copy()
        self.pr = self.pr.groupby("user").agg({f"{self.xpu}-seconds":"sum"})
        self.pr = self.pr.reset_index(drop=False)
        total = self.pr[f"{self.xpu}-seconds"].sum()
        assert total != 0, f"Total {self.xpu}-seconds is zero"
        self.pr["proportion(%)"] = self.pr[f"{self.xpu}-seconds"].apply(lambda x: round(100 * x / total))
        self.pr = self.pr.rename(columns={f"{self.xpu}-seconds":f"{self.xpu}-seconds-all"})
        self.pr = self.pr.sort_values(by=f"{self.xpu}-seconds-all", ascending=False)

        # second dataframe (self.ce) based on admincomment
        self.ce = self.df[(self.df.cluster == self.cluster) &
                          (self.df.partition.isin(self.partitions)) &
                          (~self.df.user.isin(self.excluded_users)) &
                          (self.df["elapsedraw"] >= 0.5 * SECONDS_PER_HOUR) &
                          (self.df.admincomment != {})].copy()
        # next line prevents (unlikely) failure when creating "{self.xpu}-tuples"
        if self.ce.empty:
            return pd.DataFrame()
        self.ce = self.ce.merge(self.pr, how="left", on="user")
        if self.xpu == "cpu":
            self.ce[f"{self.xpu}-tuple"] = self.ce.apply(lambda row:
                                                         cpu_efficiency(row["admincomment"],
                                                                        row["elapsedraw"],
                                                                        row["jobid"],
                                                                        row["cluster"]),
                                                                        axis="columns")
        else:
            self.ce[f"{self.xpu}-tuple"] = self.ce.apply(lambda row:
                                                         gpu_efficiency(row["admincomment"],
                                                                        row["elapsedraw"],
                                                                        row["jobid"],
                                                                        row["cluster"]),
                                                                        axis="columns")
        cols = [f"{self.xpu}-seconds-used",
                f"{self.xpu}-seconds-total",
                f"{self.xpu}-error-code"]
        self.ce[cols] = pd.DataFrame(self.ce[f"{self.xpu}-tuple"].tolist(), index=self.ce.index)
        self.ce = self.ce[self.ce[f"{self.xpu}-error-code"] == 0]
        self.ce["interactive"] = self.ce["jobname"].apply(lambda x:
                                                          1 if x.startswith("sys/dashboard") or
                                                               x.startswith("interactive") else 0)
        d = {"user":"size",
             f"{self.xpu}-seconds-used":"sum",
             f"{self.xpu}-seconds-total":"sum",
             "partition":lambda series: ",".join(sorted(set(series))),
             "proportion(%)":"first",
             f"{self.xpu}-seconds-all":"first",
             "cores":"mean",
             "interactive":"sum"}
        self.ce = self.ce.groupby("user").agg(d).rename(columns={"user":"jobs"})
        self.ce = self.ce.sort_values(by=f"{self.xpu}-seconds-total", ascending=False)
        self.ce = self.ce.reset_index(drop=False)
        self.ce = self.ce.head(self.num_top_users)
        self.ce["eff(%)"] = 100.0 * self.ce[f"{self.xpu}-seconds-used"] / self.ce[f"{self.xpu}-seconds-total"]
        # next line prevents (unlikely) failure when creating "{self.xpu}-hours"
        if self.ce.empty:
            return pd.DataFrame()
        self.ce[f"{self.xpu}-hours"] = self.ce.apply(lambda row:
                                                     round(row[f"{self.xpu}-seconds-total"] / SECONDS_PER_HOUR),
                                                     axis="columns")
        # next line prevents (unlikely) division by zero when calculating "coverage"
        self.ce = self.ce[self.ce[f"{self.xpu}-seconds-all"] > 0]
        self.ce["coverage"] = self.ce.apply(lambda row:
                                            row[f"{self.xpu}-seconds-total"] / row[f"{self.xpu}-seconds-all"],
                                            axis="columns")
        self.ce["coverage"] = self.ce["coverage"].apply(lambda x: round(x, 2))
        self.ce["eff(%)"]   =   self.ce["eff(%)"].apply(lambda x: round(x))
        self.ce["cores"]    =    self.ce["cores"].apply(lambda x: round(x, 1))
        self.ce.index += 1
        filters = (self.ce["eff(%)"] <= self.eff_thres_pct) & \
                  (self.ce["proportion(%)"] >= self.proportion_thres_pct) & \
                  (self.ce[f"{self.xpu}-hours"] >= self.absolute_thres_hours)
        self.ce["cluster"] = self.cluster
        cols = ["user",
                "cluster",
                "partition",
                f"{self.xpu}-hours",
                "proportion(%)",
                "eff(%)",
                "jobs",
                "interactive",
                "cores",
                "coverage"]
        self.admin = self.ce[cols][filters].copy()
        self.ce = self.ce[cols][filters]

    def send_emails_to_users(self, method):
        rank_text = {1:"the most", 2:"the 2nd most", 3:"the 3rd most"}
        g = GreetingFactory().create_greeting(method)
        for user in self.ce.user.unique():
            vfile = f"{self.vpath}/{self.violation}/{user}.email.csv"
            if self.has_sufficient_time_passed_since_last_email(vfile):
                usr = self.ce[self.ce.user == user].copy()
                rank = self.ce.index[self.ce.user == user].tolist()[0]
                usr[f"{self.xpu.upper()}-rank"] = f"{rank}/{self.pr.shape[0]}"
                usr["eff(%)"] = usr["eff(%)"].apply(lambda x: f"{x}%")
                usr["cores"] = usr["cores"].apply(lambda x: str(x).replace(".0", ""))
                cols = ["user",
                        "cluster",
                        "partition",
                        "jobs",
                        f"{self.xpu}-hours",
                        f"{self.xpu.upper()}-rank",
                        "eff(%)",
                        "cores"]
                if self.xpu == "gpu":
                    cols.remove("cores")
                renamings = {"user":"User",
                             "cluster":"Cluster",
                             "partition":"Partition(s)",
                             "jobs":"Jobs",
                             f"{self.xpu}-hours":f"{self.xpu.upper()}-hours",
                             "eff(%)":"Efficiency",
                             "cores":"AvgCores"}
                usr = usr[cols].rename(columns=renamings)
                myrank = f"the {rank}th most" if rank > 3 else rank_text[rank]
                edays = self.days_between_emails
                s = f"{g.greeting(user)}"
                s +=f"Over the last {edays} days you have used {myrank} {self.xpu.upper()}-hours on {self.cluster_name} but\n"
                s +=f"your mean {self.xpu.upper()} efficiency is only {usr['Efficiency'].values[0]}:\n\n"
                usr_str = usr.drop(columns=["Cluster"]).to_string(index=False, justify="center")
                s += "\n".join([5 * " " + row for row in usr_str.split("\n")])
                s += "\n"
                target = self.eff_target_pct
                if self.xpu == "cpu":
                    s += textwrap.dedent(f"""
                    A good target value for "Efficiency" is {target}% and above. Please investigate the reason
                    for the low efficiency. Common reasons for low CPU efficiency are discussed here:

                         https://researchcomputing.princeton.edu/get-started/cpu-utilization
                    """)
                elif self.xpu == "gpu":
                    s += textwrap.dedent(f"""
                    A good target value for "Efficiency" is {target}% and above. Please investigate the reason
                    for the low efficiency. Common reasons for low GPU efficiency are discussed here:

                         https://researchcomputing.princeton.edu/support/knowledge-base/gpu-computing#low-util
                    """)
                s += textwrap.dedent(f"""
                Consult the documentation or write to the mailing list of the software that you
                are using for additional reasons for low {self.xpu.upper()} efficiency. You may also consider
                attending an in-person Research Computing help session:

                     https://researchcomputing.princeton.edu/support/help-sessions
                """)
                s += textwrap.dedent(f"""
                You can check the efficiency of completed and actively running jobs by using the
                \"jobstats\" command on a given JobID:

                     $ jobstats {self.df[self.df.user == user].jobid.values[0]}

                Replying to this automated email will open a support ticket with Research
                Computing. Let us know if we can be of help.
                """)
                subject = f"Jobs with Low Efficiency on {self.cluster_name}"
                send_email(s, f"{user}@princeton.edu", subject=subject)
                for email in self.admin_emails:
                    send_email(s, f"{email}", subject=f"{self.subject}")
                print(s)

                # append the new violations to the log file
                Alert.update_violation_log(usr, vfile)

    def generate_report_for_admins(self, title: str, keep_index: bool=False) -> str:
        """Return dataframe for admins."""
        if self.admin.empty:
            return ""
        else:
            return add_dividers(self.admin.to_string(index=keep_index, justify="center"), title)


class LowEfficiencyCPU(LowEfficiency):

    """Specialized implementation of LowEfficiency for CPUs."""

    def __init__(self, df, days_between_emails, violation, vpath, subject, **kwargs):
        self.xpu = "cpu"
        super().__init__(df, days_between_emails, violation, vpath, subject, **kwargs)


class LowEfficiencyGPU(LowEfficiency):

    """Specialized implementation of LowEfficiency for GPUs."""

    def __init__(self, df, days_between_emails, violation, vpath, subject, **kwargs):
        self.xpu = "gpu"
        super().__init__(df, days_between_emails, violation, vpath, subject, **kwargs)
