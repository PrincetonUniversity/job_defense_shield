import math
import pandas as pd
from ..base import Alert
from ..efficiency import cpu_memory_usage
from ..efficiency import cpu_nodes_with_zero_util
from ..utils import add_dividers
from ..utils import MINUTES_PER_HOUR as mph
from ..greeting import GreetingFactory
from ..email_translator import EmailTranslator


class MultinodeCpuFragmentation(Alert):

    """Find multinode CPU jobs that use too many nodes. Ignore jobs
       with 0% CPU utilization on a node since those will captured
       by a different alert."""

    def __init__(self, df, days_between_emails, violation, vpath, **kwargs):
        super().__init__(df, days_between_emails, violation, vpath, **kwargs)

    def _add_required_fields(self):
        if not hasattr(self, "email_subject"):
            self.email_subject = "Multinode CPU Jobs with Fragmentation"
        if not hasattr(self, "report_title"):
            self.report_title = "Multinode CPU Jobs with Fragmentation"
        if not hasattr(self, "min_nodes"):
            self.min_nodes_thres = 2

    def is_fragmented(self, cores_per_node, mem_per_node_used) -> bool:
        """Classify the job as fragmented or not based on cores per node
           and memory usage."""
        if cores_per_node < self.cores_fraction * self.cores_per_node and \
           mem_per_node_used < (1 - self.safety_fraction) * self.mem_per_node:
            return True
        return False

    def min_nodes_needed(self, nodes, cores, mem_per_node_used) -> int:
        """Return the minimum number of nodes needed based on the total
           number of allocated CPU-cores and total memory used. Note
           that this calculation assumes the memory usage is evenly
           distributed across the nodes."""
        min_nodes_by_cores = math.ceil(cores / self.cores_per_node)
        total_mem_used = nodes * mem_per_node_used
        mem_per_node_safe = (1 - self.safety_fraction) * self.mem_per_node
        min_nodes_by_memory = math.ceil(total_mem_used / mem_per_node_safe)
        return max(min_nodes_by_cores, min_nodes_by_memory)

    def _filter_and_add_new_fields(self):
        self.df = self.df[(self.df.cluster == self.cluster) &
                          (self.df.partition.isin(self.partitions)) &
                          (self.df.nodes >= self.min_nodes_thres) &
                          (self.df["gpus"] == 0) &
                          (~self.df.user.isin(self.excluded_users)) &
                          (self.df.state != "OUT_OF_MEMORY") &
                          (self.df["elapsed-hours"] >= self.min_run_time / mph)].copy()
        if not self.df.empty and self.include_running_jobs:
            self.df.admincomment = self.get_admincomment_for_running_jobs()
        self.df = self.df[self.df.admincomment != {}]
        if not self.df.empty and hasattr(self, "nodelist"):
            self.df = self.filter_by_nodelist(self.df)
        # add new fields
        if not self.df.empty:
            self.df["nodes-tuple"] = self.df.apply(lambda row:
                                     cpu_nodes_with_zero_util(row["admincomment"],
                                                              row["jobid"],
                                                              row["cluster"]),
                                                              axis="columns")
            cols = ["nodes-unused", "error_code"]
            self.df[cols] = pd.DataFrame(self.df["nodes-tuple"].tolist(), index=self.df.index)
            self.df = self.df[(self.df["error_code"] == 0) & (self.df["nodes-unused"] == 0)]
            if not self.df.empty:
                self.df["cores-per-node"] = self.df["cores"] / self.df["nodes"]
                self.df["cores-per-node"] = self.df["cores-per-node"].apply(lambda x: round(x, 1))
                self.df["memory-tuple"] = self.df.apply(lambda row:
                                                        cpu_memory_usage(row["admincomment"],
                                                                         row["jobid"],
                                                                         row["cluster"]),
                                                                         axis="columns")
                cols = ["memory-used", "memory-alloc", "error_code"]
                self.df[cols] = pd.DataFrame(self.df["memory-tuple"].tolist(), index=self.df.index)
                self.df = self.df[self.df["error_code"] == 0]
                self.df["memory-per-node-used"] = self.df["memory-used"] / self.df["nodes"]
                self.df["memory-per-node-used"] = self.df["memory-per-node-used"].apply(round)
                self.df = self.df.rename(columns={"elapsed-hours":"hours",
                                                  "memory-per-node-used":"mem-per-node-used"})
                self.df = self.df.sort_values(["cluster", "user"], ascending=[True, True])
                self.df["hours"] = self.df["hours"].apply(lambda x: str(round(x, 1))
                                                          if x < 5 else str(round(x)))
                if hasattr(self, "cores_per_node_thres"):
                    self.df = self.df[self.df["cores-per-node"] < self.cores_per_node_thres]
                    self.df["mem-per-node-used"] = self.df["mem-per-node-used"].apply(lambda x: f"{x} GB")
                    self.df["cores-per-node"] = self.df["cores-per-node"].apply(lambda x:
                                                                                str(x).replace(".0", ""))
                    cols = ["jobid",
                            "user",
                            "cluster",
                            "partition",
                            "nodes",
                            "cores",
                            "mem-per-node-used",
                            "cores-per-node",
                            "hours"]
                    self.df = self.df[cols]
                    self.df["min-nodes"] = "N/A"
                else:
                    if not self.df.empty:
                        self.df = self.df[self.df.apply(lambda row:
                                                        self.is_fragmented(row["cores-per-node"],
                                                                           row["mem-per-node-used"]),
                                                                           axis="columns")]
                        if not self.df.empty:
                            self.df["min-nodes"] = self.df.apply(lambda row:
                                                                 self.min_nodes_needed(row["nodes"],
                                                                                       row["cores"],
                                                                                       row["mem-per-node-used"]),
                                                                                       axis="columns")
                            self.df = self.df[self.df["min-nodes"] < self.df["nodes"]]
                            self.df["mem-per-node-used"] = self.df["mem-per-node-used"].apply(lambda x: f"{x} GB")
                            self.df["cores-per-node"] = self.df["cores-per-node"].apply(lambda x:
                                                                                        str(x).replace(".0", ""))
                            cols = ["jobid",
                                    "user",
                                    "cluster",
                                    "partition",
                                    "nodes",
                                    "cores",
                                    "mem-per-node-used",
                                    "cores-per-node",
                                    "hours",
                                    "min-nodes"]
                            self.df = self.df[cols]

    def create_emails(self, method):
        g = GreetingFactory().create_greeting(method)
        for user in self.df.user.unique():
            vfile = f"{self.vpath}/{self.violation}/{user}.csv"
            if self.has_sufficient_time_passed_since_last_email(vfile):
                usr = self.df[self.df.user == user].copy()
                renamings = {"jobid":"JobID",
                             "cluster":"Cluster",
                             "partition":"Partition",
                             "nodes":"Nodes",
                             "mem-per-node-used":"Mem-per-Node",
                             "cores-per-node":"Cores-per-Node",
                             "hours":"Hours",
                             "min-nodes":"Nodes-Needed"}
                usr = usr.rename(columns=renamings)
                indent = 4 * " "
                tags = {}
                tags["<GREETING>"] = g.greeting(user)
                tags["<DAYS>"] = str(self.days_between_emails)
                tags["<CLUSTER>"] = self.cluster
                tags["<PARTITIONS>"] = ",".join(sorted(set(usr.Partition)))
                if not hasattr(self, "cores_per_node_thres"):
                    min_nodes = usr["Nodes-Needed"].mode().values[0]
                    tags["<CPN>"] = str(self.cores_per_node)
                    tags["<MPN>"] = str(self.mem_per_node)
                    tbl = usr.drop(columns=["user", "Partition", "cores"]).copy()
                    table = tbl.to_string(index=False, justify="center").split("\n")
                    tags["<TABLE>"] = "\n".join([indent + row for row in table])
                    sb = f"{indent}#SBATCH --nodes={min_nodes}\n"
                    sb += f"{indent}#SBATCH --ntasks-per-node={self.cores_per_node}"
                    tags["<SBATCH>"] = sb
                    tags["<NUM-CORES>"] = str(min_nodes * self.cores_per_node)
                else:
                    tbl = usr.drop(columns=["user", "Partition", "cores", "Nodes-Needed"]).copy()
                    table = tbl.to_string(index=False, justify="center").split("\n")
                    tags["<TABLE>"] = "\n".join([indent + row for row in table])
                tags["<JOBSTATS>"] = f"{indent}$ jobstats {usr.JobID.values[0]}"
                translator = EmailTranslator(self.email_files_path,
                                             self.email_file,
                                             tags)
                email = translator.replace_tags()
                usr["User"] = user
                usr["Cluster"] = self.cluster
                usr["Alert-Partitions"] = ",".join(sorted(set(self.partitions)))
                usr = usr[["User",
                           "Cluster",
                           "Alert-Partitions",
                           "JobID",
                           "Partition",
                           "Nodes",
                           "Cores-per-Node",
                           "Mem-per-Node",
                           "Hours",
                           "Nodes-Needed"]]
                self.emails.append((user, email, usr))

    def generate_report_for_admins(self, keep_index: bool=False) -> str:
        if self.df.empty:
            column_names = ["JobID",
                            "User",
                            "Nodes",
                            "Cores",
                            "Mem-per-Node-Used",
                            "Cores-per-Node",
                            "Hours",
                            "Min-Nodes",
                            "Emails"]
            self.df = pd.DataFrame(columns=column_names)
            return add_dividers(self.create_empty_report(self.df), self.report_title)
        self.df["Emails"] = self.df.user.apply(lambda user:
                                 self.get_emails_sent_count(user, self.violation))
        self.df.Emails = self.format_email_counts(self.df.Emails)
        self.df = self.df.drop(columns=["cluster", "partition"])
        renamings = {"jobid":"JobID",
                     "user":"User",
                     "nodes":"Nodes",
                     "cores":"Cores",
                     "mem-per-node-used":"Mem-per-Node-Used",
                     "cores-per-node":"Cores-per-Node",
                     "hours":"Hours",
                     "min-nodes":"Min-Nodes"}
        self.df = self.df.rename(columns=renamings)
        report_str = self.df.to_string(index=keep_index, justify="center")
        return add_dividers(report_str, self.report_title)
