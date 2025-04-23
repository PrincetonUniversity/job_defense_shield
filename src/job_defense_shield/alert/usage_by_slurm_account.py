from ..base import Alert
from ..utils import add_dividers


class UsageBySlurmAccount(Alert):

    """Utilization of each user within each Slurm account."""

    def __init__(self, df, days_between_emails, violation, vpath, **kwargs):
        super().__init__(df, days_between_emails, violation, vpath, **kwargs)

    def _add_required_fields(self):
        if not hasattr(self, "report_title"):
            self.report_title = "Usage by Slurm Account"

    def _filter_and_add_new_fields(self):
        self.df = self.df[self.df["elapsedraw"] > 0].copy()
        # dataframe 1 of 2 where the results are summed over users
        d = {"user":lambda series: series.unique().size,
             "cpu-hours":"sum",
             "gpu-hours":"sum"}
        self.gp = self.df.groupby(["cluster", "partition", "account"]).agg(d)
        self.gp = self.gp.reset_index()
        self.gp = self.gp.rename(columns={"user":"users"})
        self.gp = self.gp.sort_values(by=["cluster", "partition", "cpu-hours"],
                                      ascending=[True, True, False])
        cols = ["cpu-hours", "gpu-hours"]
        self.gp[cols] = self.gp[cols].apply(round).astype("int64")
        for cluster in self.gp["cluster"].unique():
            for p in self.gp["partition"].unique():
                for field in ["cpu-hours", "gpu-hours"]:
                    total = self.gp[(self.gp["cluster"] == cluster) &
                               (self.gp["partition"] == p)][field].sum()
                    if total != 0:
                        self.gp[field] = self.gp.apply(lambda row:
                                         f"{row[field]} ({round(100 * row[field] / total)}%)"
                                         if row["cluster"] == cluster and
                                            row["partition"] == p
                                         else row[field], axis="columns")

        # dataframe 2 of 2 where the values for each user are explicit
        d = {"cpu-hours":"sum",
             "gpu-hours":"sum"}
        cols = ["cluster", "partition", "account"]
        self.by_user = self.df.groupby(cols + ["user"]).agg(d)
        self.by_user = self.by_user.reset_index()
        self.by_user = self.by_user.sort_values(by=cols + ["cpu-hours"],
                                                ascending=[True, True, True, False])
        cols = ["cpu-hours", "gpu-hours"]
        self.by_user[cols] = self.by_user[cols].apply(round).astype("int64")

    def generate_report_for_admins(self, keep_index: bool=False) -> str:
        by_acct = self.gp.to_string(index=keep_index, justify="center")
        by_user = self.by_user.to_string(index=keep_index, justify="center")
        return add_dividers(by_acct, self.report_title) + \
               add_dividers(by_user, self.report_title)
