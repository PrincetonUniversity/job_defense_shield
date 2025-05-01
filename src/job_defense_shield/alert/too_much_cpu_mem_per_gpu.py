import pandas as pd
from ..base import Alert
from ..utils import add_dividers
from ..utils import MINUTES_PER_HOUR as mph
from ..efficiency import cpu_memory_usage
from ..greeting import GreetingFactory
from ..email_translator import EmailTranslator


class TooMuchCpuMemPerGpu(Alert):

    """Find jobs that allocating too much CPU memory per GPU."""

    def __init__(self, df, days_between_emails, violation, vpath, **kwargs):
        super().__init__(df, days_between_emails, violation, vpath, **kwargs)

    def _add_required_fields(self):
        if not hasattr(self, "email_subject"):
            self.email_subject = "Consider Allocating Less CPU Memory per GPU"
        if not hasattr(self, "report_title"):
            self.report_title = "Too Much CPU Memory Per GPU"
        if not hasattr(self, "mem_eff_thres"):
            self.mem_eff_thres = 1.0

    def _filter_and_add_new_fields(self):
        self.df = self.df[(self.df.cluster == self.cluster) &
                          (self.df.partition.isin(self.partitions)) &
                          (self.df.gpus > 0) &
                          (self.df.state != "OUT_OF_MEMORY") &
                          (~self.df.user.isin(self.excluded_users)) &
                          (self.df["elapsed-hours"] >= self.min_run_time / mph)].copy()
        if not self.df.empty and self.include_running_jobs:
            self.df.admincomment = self.get_admincomment_for_running_jobs()
        self.df = self.df[self.df.admincomment != {}]
        if not self.df.empty and hasattr(self, "nodelist"):
            self.df = self.filter_by_nodelist(self.df)
        self.df.rename(columns={"user":"User"}, inplace=True)
        if not self.df.empty:
            self.df["memory-tuple"] = self.df.apply(lambda row:
                                           cpu_memory_usage(row["admincomment"],
                                                            row["jobid"],
                                                            row["cluster"]),
                                                            axis="columns")
            cols = ["CPU-Mem-Used", "mem-alloc", "error_code"]
            self.df[cols] = pd.DataFrame(self.df["memory-tuple"].tolist(), index=self.df.index)
            self.df = self.df[self.df["error_code"] == 0]
            self.df["CPU-Mem-per-GPU"] = self.df["mem-alloc"] / self.df.gpus
            self.df = self.df[self.df["CPU-Mem-per-GPU"] > self.cpu_mem_per_gpu_limit]
            self.df["Mem-Eff"] = self.df["CPU-Mem-Used"] / self.df["mem-alloc"]
            # should user be ignored if even just one of their jobs is efficient?
            self.df = self.df[self.df["Mem-Eff"] < self.mem_eff_thres]
            self.df["CPU-Mem-per-GPU"] = self.df["CPU-Mem-per-GPU"].apply(lambda x:
                                              str(round(x, 1)).replace(".0", "") + " GB")
            self.df["CPU-Mem-per-GPU-Limit"] = f"{self.cpu_mem_per_gpu_target} GB"
            self.df["mem-alloc"] = self.df["mem-alloc"].apply(round)
            cols = ["jobid",
                    "User",
                    "elapsed-hours",
                    "Mem-Eff",
                    "mem-alloc",
                    "partition",
                    "gpus",
                    "CPU-Mem-per-GPU",
                    "CPU-Mem-per-GPU-Limit",
                    "CPU-Mem-Used"]
            self.df = self.df[cols]
            renamings = {"jobid":"JobID",
                         "mem-alloc":"CPU-Mem",
                         "partition":"Partition",
                         "gpus":"GPUs",
                         "elapsed-hours":"Hours"}
            self.df = self.df.rename(columns=renamings)
            self.df["Hours"] = self.df["Hours"].apply(lambda x: str(round(x, 1))
                                                      if x < 5 else str(round(x)))
            self.df = self.df.sort_values("User", ascending=True)

    def create_emails(self, method):
        g = GreetingFactory().create_greeting(method)
        for user in self.df.User.unique():
            vfile = f"{self.vpath}/{self.violation}/{user}.csv"
            if self.has_sufficient_time_passed_since_last_email(vfile):
                usr = self.df[self.df.User == user].copy()
                # use the rounded values since those will appear in the email
                usr["Mem-Eff"] = usr["Mem-Eff"].apply(lambda x: round(100 * x))
                # compute recommended memory for first job
                jobid = usr.JobID.values[0]
                mem_eff = usr["Mem-Eff"].values[0] / 100
                cpu_mem_alloc = usr["CPU-Mem"].values[0]
                num_gpus = usr["GPUs"].values[0]
                mem_per_gpu = max(8, round(1.2 * mem_eff * cpu_mem_alloc / num_gpus))
                usr["Mem-Eff"] = usr["Mem-Eff"].apply(lambda x: f"{x}%")
                usr["CPU-Mem"] = usr["CPU-Mem"].apply(lambda x: f"{x} GB")
                tbl = usr.drop(columns=["User", "Partition", "CPU-Mem-Used"]).copy()
                indent = 4 * " "
                table = tbl.to_string(index=False, justify="center").split("\n")
                tags = {}
                tags["<GREETING>"] = g.greeting(user)
                tags["<CLUSTER>"] = self.cluster
                tags["<NAME>"] = self.cluster_name
                tags["<TARGET>"] = str(self.cpu_mem_per_gpu_target)
                tags["<CORES>"] = str(self.cores_per_node)
                tags["<MEMORY>"] = str(self.cpu_mem_per_node)
                tags["<MEM-PER-GPU>"] = str(mem_per_gpu)
                tags["<GPUS>"] = str(self.gpus_per_node)
                tags["<DAYS>"] = str(self.days_between_emails)
                tags["<TABLE>"] = "\n".join([indent + row for row in table])
                tags["<JOBSTATS>"] = f"{indent}$ jobstats {jobid}"
                tags["<JOBID>"] = str(jobid)
                tags["<PARTITIONS>"] = ",".join(sorted(set(self.partitions)))
                translator = EmailTranslator(self.email_files_path,
                                             self.email_file,
                                             tags)
                email = translator.replace_tags()
                usr["Cluster"] = self.cluster
                usr["Alert-Partitions"] = ",".join(sorted(set(self.partitions)))
                usr["CPU-Mem-per-GPU"] = usr["CPU-Mem-per-GPU"].apply(lambda x:
                                                                      x.replace(" GB", ""))
                usr = usr[["User",
                           "Cluster",
                           "Alert-Partitions",
                           "JobID",
                           "Partition",
                           "GPUs",
                           "CPU-Mem-per-GPU",
                           "Hours"]]
                self.emails.append((user, email, usr))

    def generate_report_for_admins(self, keep_index: bool=False) -> str:
        if self.df.empty:
            column_names = ["JobID",
                            "User",
                            "Hours",
                            "Mem-Eff",
                            "CPU-Mem",
                            "GPUs",
                            "CPU-Mem-per-GPU",
                            "CPU-Mem-per-GPU-Limit",
                            "Emails"]
            self.df = pd.DataFrame(columns=column_names)
            return add_dividers(self.create_empty_report(self.df), self.report_title)
        self.df.drop(columns=["CPU-Mem-Used"], inplace=True)
        self.df["CPU-Mem"] = self.df["CPU-Mem"].apply(lambda x: f"{x} GB")
        self.df["Mem-Eff"] = self.df["Mem-Eff"].apply(lambda x: f"{round(100 * x)}%")
        self.df["Emails"] = self.df.User.apply(lambda user:
                                 self.get_emails_sent_count(user, self.violation))
        self.df.Emails = self.format_email_counts(self.df.Emails)
        report_str = self.df.to_string(index=keep_index, justify="center")
        return add_dividers(report_str, self.report_title)
