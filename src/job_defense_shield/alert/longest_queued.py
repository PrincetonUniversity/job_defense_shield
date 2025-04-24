from time import time
import pandas as pd
from ..utils import SECONDS_PER_HOUR as sph
from ..utils import HOURS_PER_DAY as hpd
from ..utils import add_dividers
from ..base import Alert


class LongestQueuedJobs(Alert):

    """Find the pending jobs with the longest queue times while ignoring
       array jobs. Only jobs that have been eligible to run for 3 days
       or more are shown. One job per user."""

    def __init__(self, df, days_between_emails, violation, vpath, **kwargs):
        super().__init__(df, days_between_emails, violation, vpath, **kwargs)

    def _add_required_fields(self):
        if not hasattr(self, "report_title"):
            self.report_title = "Longest Queue Times (1 job per user, ignoring job arrays)"

    def _filter_and_add_new_fields(self):
        # filter the dataframe
        self.df = self.df[self.df.state == "PENDING"].copy()
        # remove array jobs
        self.df = self.df[~self.df.jobid.str.contains("_")]
        # add new fields
        self.df["s-days"] = round((time() - self.df["submit"]) / sph / hpd)
        self.df["e-days"] = round((time() - self.df["eligible"]) / sph / hpd)
        self.df["s-days"] = self.df["s-days"].astype("int64")
        self.df["e-days"] = self.df["e-days"].astype("int64")
        cols = ["jobid",
                "user",
                "cluster",
                "nodes",
                "qos",
                "partition",
                "s-days",
                "e-days"]
        self.df = self.df[cols].groupby("user").apply(lambda d:
                                                      d.iloc[d["s-days"].argmax()])
        self.df.sort_values("s-days", ascending=False, inplace=True)
        self.df = self.df[self.df["s-days"] >= 3][:10]
        column_names = pd.MultiIndex.from_tuples([('JobID', ''),
                                                  ('User', ''),
                                                  ('Cluster', ''),
                                                  ('Nodes', ''),
                                                  ('QOS', ''),
                                                  ('Partition', ''),
                                                  ('Submit', '(Days)'),
                                                  ('Eligible', '(Days)')])
        self.df.columns = column_names

    def generate_report_for_admins(self, keep_index: bool=False) -> str:
        if self.df.empty:
            cols = [name[0] for name in self.df.columns.tolist()]
            self.df = pd.DataFrame(columns=cols)
            return add_dividers(self.create_empty_report(self.df),
                                self.report_title)
        report_str = self.df.to_string(index=keep_index, justify="center")
        return add_dividers(report_str, self.report_title, units_row=True)
