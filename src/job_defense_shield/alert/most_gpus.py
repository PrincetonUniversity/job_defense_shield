import pandas as pd
from ..base import Alert
from ..utils import add_dividers
from ..efficiency import gpu_efficiency
from ..utils import JOBSTATES


class MostGPUs(Alert):

    """Top 10 users by the highest number of allocated GPUs in a job. Only
       one job per user is shown."""

    def __init__(self, df, days_between_emails, violation, vpath, **kwargs):
        super().__init__(df, days_between_emails, violation, vpath, **kwargs)

    def _add_required_fields(self):
        if not hasattr(self, "report_title"):
            self.report_title = "Jobs with the Most GPUs (1 Job per User)"

    def _filter_and_add_new_fields(self):
        cols = ["jobid",
                "user",
                "cluster",
                "gpus",
                "nodes",
                "cores",
                "state",
                "partition",
                "elapsed-hours",
                "admincomment",
                "elapsedraw"]
        self.gp = self.df[cols].groupby("user").apply(lambda d:
                                                      d.iloc[d["gpus"].argmax()])
        self.gp = self.gp.sort_values("gpus", ascending=False)[:10]
        self.gp.rename(columns={"elapsed-hours":"Hours"}, inplace=True)
        self.gp.state = self.gp.state.apply(lambda x: JOBSTATES[x])
        if not self.gp.empty:
            self.gp["GPU-eff-tpl"] = self.gp.apply(lambda row:
                                          gpu_efficiency(row["admincomment"],
                                                         row["elapsedraw"],
                                                         row["jobid"],
                                                         row["cluster"],
                                                         single=True)
                                          if row["admincomment"] != {}
                                          else ("--", 0), axis="columns")
            cols = ["GPU-eff", "error-code"]
            self.gp[cols] = pd.DataFrame(self.gp["GPU-eff-tpl"].tolist(),
                                         index=self.gp.index)
            self.gp = self.gp[self.gp["error-code"] == 0]
            self.gp["GPU-eff"] = self.gp["GPU-eff"].apply(lambda x:
                                                          x if x == "--"
                                                          else f"{round(x)}%")
            self.gp["Hours"] = self.gp["Hours"].apply(lambda h: str(round(h, 1))
                                                      if h < 2 else str(round(h)))
            renamings = {"jobid":"JobID",
                         "user":"User",
                         "cluster":"Cluster",
                         "gpus":"GPUs",
                         "nodes":"Nodes",
                         "cores":"Cores",
                         "state":"State",
                         "partition":"Partition",
                         "GPU-eff":"GPU-Eff"}
            self.gp.rename(columns=renamings, inplace=True)
            cols = ["JobID",
                    "User",
                    "Cluster",
                    "GPUs",
                    "Nodes",
                    "Cores",
                    "State",
                    "Partition",
                    "Hours",
                    "GPU-Eff"]
            self.gp = self.gp[cols]

    def generate_report_for_admins(self, keep_index: bool=False) -> str:
        if self.gp.empty:
            return add_dividers(self.create_empty_report(self.gp),
                                self.report_title)
        report_str = self.gp.to_string(index=keep_index, justify="center")
        return add_dividers(report_str, self.report_title)
