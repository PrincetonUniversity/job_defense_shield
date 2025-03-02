from base import Alert
from efficiency import cpu_efficiency
from utils import add_dividers
from utils import JOBSTATES


class MostCores(Alert):

    """Top 10 users by the highest number of allocated CPU-cores in a job. Only
     one job per user is shown."""

    def __init__(self, df, days_between_emails, violation, vpath, **kwargs):
        super().__init__(df, days_between_emails, violation, vpath, **kwargs)

    def _add_required_fields(self):
        if not hasattr(self, "report_title"):
            self.report_title = "Jobs with the Most CPU-Cores (1 Job per User)"

    def _filter_and_add_new_fields(self):
        cols = ["jobid", "user", "cluster", "cores", "nodes", "gpus", "state",
              "partition", "elapsed-hours", "admincomment", "elapsedraw"]
        self.gp = self.df[cols].groupby("user").apply(lambda d: d.iloc[d["cores"].argmax()])
        self.gp = self.gp.sort_values("cores", ascending=False)[:10]
        self.gp = self.gp.rename(columns={"elapsed-hours":"hours"})
        self.gp.state = self.gp.state.apply(lambda x: JOBSTATES[x])
        self.gp["CPU-eff-tpl"] = self.gp.apply(lambda row:
                                             cpu_efficiency(row["admincomment"],
                                                            row["elapsedraw"],
                                                            row["jobid"],
                                                            row["cluster"], single=True)
                                         if row["admincomment"] != {} else ("--", 0), axis="columns")
        self.gp["CPU-eff"] = self.gp["CPU-eff-tpl"].apply(lambda tpl: tpl[0])
        self.gp["CPU-eff"] = self.gp["CPU-eff"].apply(lambda x: x if x == "--" else f"{round(x)}%")
        self.gp["hours"] = self.gp["hours"].apply(lambda hrs: round(hrs, 1))
        cols = ["jobid", "user", "cluster", "cores", "nodes", "gpus",
              "state", "partition", "hours", "CPU-eff"]
        self.gp = self.gp[cols]

    def generate_report_for_admins(self, keep_index: bool=False) -> str:
        if self.gp.empty:
            return add_dividers(self.create_empty_report(self.gp), self.report_title)
        report_str = self.gp.to_string(index=keep_index, justify="center")
        return add_dividers(report_str, self.report_title)
