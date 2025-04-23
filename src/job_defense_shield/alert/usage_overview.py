from ..base import Alert
from ..utils import add_dividers


class UsageOverview(Alert):

    """Usage by cluster and partition."""

    def __init__(self, df, days_between_emails, violation, vpath, **kwargs):
        super().__init__(df, days_between_emails, violation, vpath, **kwargs)

    def _add_required_fields(self):
        if not hasattr(self, "report_title"):
            self.report_title = "Usage Overview by Cluster"

    def _filter_and_add_new_fields(self):
        def compute_utilization(fields: list, simple: bool=True):
            """Aggregate the data based on fields."""
            d = {"user":lambda series: series.unique().size,
                 "cpu-hours":"sum",
                 "gpu-hours":"sum"}
            gp = self.df.groupby(fields).agg(d)
            gp = gp.rename(columns={"user":"users"})
            gp = gp.reset_index().sort_values(by=["cluster", "cpu-hours"],
                                              ascending=[True, False])
            cols = ["cpu-hours", "gpu-hours"]
            gp[cols] = gp[cols].apply(round).astype("int64")
            if simple:
                for column in ["cpu-hours", "gpu-hours"]:
                    total = gp[column].sum()
                    if total != 0:
                        gp[column] = gp[column].apply(lambda x:
                                                      f"{x} ({round(100 * x / total)}%)")
            else:
                for cluster in gp["cluster"].unique():
                    for field in ["cpu-hours", "gpu-hours"]:
                        total = gp[gp["cluster"] == cluster][field].sum()
                        if total != 0:
                            gp[field] = gp.apply(lambda row:
                                                 f"{row[field]} ({round(100 * row[field] / total)}%)"
                                                 if row["cluster"] == cluster
                                                 else row[field], axis="columns")
            return gp

        self.df = self.df[self.df["elapsedraw"] > 0].copy()
        self.by_cluster = compute_utilization(["cluster"])
        self.by_cluster["cpu-hours"] = self.format_email_counts(self.by_cluster["cpu-hours"])
        self.by_cluster["gpu-hours"] = self.format_email_counts(self.by_cluster["gpu-hours"])
        self.by_partition = compute_utilization(["cluster", "partition"], simple=False)
        self.special = self.by_partition.copy()
        self.special["cpu-hours"] = self.format_email_counts(self.special["cpu-hours"])
        self.special["gpu-hours"] = self.format_email_counts(self.special["gpu-hours"])
        renamings = {"cluster":"Cluster",
                     "partition":"Partition",
                     "users":"Users",
                     "cpu-hours":"CPU-Hours",
                     "gpu-hours":"GPU-Hours"}
        self.by_cluster.rename(columns=renamings, inplace=True)
        self.special.rename(columns=renamings, inplace=True)
 
    def generate_report_for_admins(self, keep_index: bool=False) -> str:
        clus = self.by_cluster.to_string(index=keep_index, justify="center")
        part = self.special.to_string(index=False, justify="center")
        return add_dividers(clus, self.report_title) + \
               add_dividers(part, f"{self.report_title} and Partition")
