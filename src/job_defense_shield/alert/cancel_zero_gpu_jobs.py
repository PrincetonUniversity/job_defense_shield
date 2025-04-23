import os
import subprocess
import pickle
import pandas as pd
from ..base import Alert
from ..utils import SECONDS_PER_MINUTE as spm
from ..utils import SECONDS_PER_HOUR as sph
from ..utils import MINUTES_PER_HOUR as mph
from ..efficiency import num_gpus_with_zero_util
from ..greeting import GreetingFactory
from ..email_translator import EmailTranslator


class CancelZeroGpuJobs(Alert):

    """Send warnings and automatically cancel jobs with zero GPU utilization.
       Jobs with a limit-minutes that is less than self.cancel_minutes cannot
       be excluded since real limit may be UNLIMITED."""

    def __init__(self, df, days_between_emails, violation, vpath, **kwargs):
        super().__init__(df, days_between_emails, violation, vpath, **kwargs)

    def _add_required_fields(self):
        if not hasattr(self, "email_subject"):
            self.email_subject = "Jobs with 0% GPU Utilization"
        if not hasattr(self, "gpu_frac_threshold"):
            self.gpu_frac_threshold = 1.0
        if not hasattr(self, "do_not_cancel"):
            self.do_not_cancel = False
        self.jobids_to_cancel = []
        

    def _filter_and_add_new_fields(self):
        if not hasattr(self, "first_warning_minutes") and \
           not hasattr(self, "second_warning_minutes"):
            lower = self.cancel_minutes * spm
        else:
            lower = self.first_warning_minutes * spm
        upper = (self.cancel_minutes + self.sampling_period_minutes) * spm
        self.df = self.df[(self.df.state == "RUNNING") &
                          (self.df.gpus > 0) &
                          (self.df.cluster == self.cluster) &
                          (self.df.partition.isin(self.partitions)) &
                          (self.df.elapsedraw >= lower) &
                          (self.df.elapsedraw <  upper) &
                          (~self.df.user.isin(self.excluded_users))].copy()
        if not self.df.empty and hasattr(self, "nodelist"):
            self.df = self.filter_by_nodelist()
        self.df.rename(columns={"user":"User"}, inplace=True)

        """
        On the caching of jobs that are known to using GPUs. First, read pickle
        file containing the jobid's of jobs that are known to using the GPUs
        from previous iteration. Create a list called pre_approved that contains
        these jobid's for the current running jobs. Note then len(pre_approved)
        will be less than or equal to len(jobs_using_gpus) since jobs_using_gpus
        includes jobs that have finished since the previous iteration. Filter
        out the pre_approved jobs.

        Calculate the number of "Unused-GPUs" for each running job that was not
        previously known to be using the GPUs. Create a list called
        jobs_using_gpus containing the jobid's of the new jobs that are using
        the GPUs. Add this list to pre_approved and write this to file. Note
        that the jobs in pre_approved and jobs_using_gpus do not overlap.
        """

        # read cache file containing jobid's that are known to be using the gpus
        pre_approved = []
        if hasattr(self, "jobid_cache_path") and os.path.isdir(self.jobid_cache_path):
            jobid_cache_file = os.path.join(self.jobid_cache_path, ".jobid_cache.pkl")
            if os.path.isfile(jobid_cache_file):
                with open(jobid_cache_file, "rb") as fp:
                    jobs_using_gpus = pickle.load(fp)
                pre_approved = self.df[self.df.jobid.isin(jobs_using_gpus)].jobid.tolist()
                self.df = self.df[~self.df.jobid.isin(pre_approved)]
        if not self.df.empty:
            self.df.admincomment = Alert.get_admincomment_for_running_jobs(self)
            self.df["zero-tuple"] = self.df.apply(lambda row:
                                         num_gpus_with_zero_util(row["admincomment"],
                                                                 row["jobid"],
                                                                 row["cluster"]),
                                                                 axis="columns")
            cols = ["GPUs-Unused", "error_code"]
            self.df[cols] = pd.DataFrame(self.df["zero-tuple"].tolist(),
                                         index=self.df.index)
            self.df = self.df[self.df["error_code"] == 0]
            # write cache file of jobid's that are known to be using the gpus
            if hasattr(self, "jobid_cache_path"):
                jobs_using_gpus = self.df[self.df["GPUs-Unused"] == 0].jobid.tolist()
                jobid_cache_file = os.path.join(self.jobid_cache_path, ".jobid_cache.pkl")
                with open(jobid_cache_file, "wb") as fp:
                    pickle.dump(pre_approved + jobs_using_gpus, fp)
            self.df["gpu_frac"] = (self.df["gpus"] - self.df["GPUs-Unused"]) / self.df["gpus"]
            self.df = self.df[self.df["gpu_frac"] < self.gpu_frac_threshold]
            # filter interactive jobs if such settings are found in config.yaml
            if hasattr(self, "max_interactive_hours") and \
               hasattr(self, "max_interactive_gpus"):
                self.df["interactive"] = self.df["jobname"].apply(lambda x: True
                                                                  if x.startswith("sys/dashboard") or
                                                                     x.startswith("interactive")
                                                                  else False)
                msk = (self.df["interactive"]) & \
                      (self.df.gpus <= self.max_interactive_gpus) & \
                      (self.df["limit-minutes"] <= self.max_interactive_hours * mph)
                self.df = self.df[~msk]
            self.df = self.df[["jobid",
                               "User",
                               "cluster",
                               "partition",
                               "gpus",
                               "GPUs-Unused",
                               "elapsedraw"]]
            renamings = {"gpus":"GPUs-Allocated",
                         "jobid":"JobID",
                         "cluster":"Cluster",
                         "partition":"Partition"}
            self.df.rename(columns=renamings, inplace=True)
            self.df["GPU-Util"] = "0%"
            self.df["Hours"] = self.df.elapsedraw.apply(lambda x: round(x / sph, 1))

    def create_emails(self, method):
        """Note that the violation history of a user is not considered here
           since this alert is considered urgent."""
        g = GreetingFactory().create_greeting(method)
        for user in self.df.User.unique():
            indent = 4 * " "
            tags = {}
            tags["<GREETING>"] = g.greeting(user)
            tags["<CLUSTER>"] = self.cluster
            tags["<PARTITIONS>"] = ",".join(sorted(set(self.partitions)))
            tags["<SAMPLING>"] = str(self.sampling_period_minutes)
            tags["<CANCEL-MIN>"] = str(self.cancel_minutes)
            tags["<CANCEL-HRS>"] = f"{round(self.cancel_minutes / mph)}"
            #################
            # first warning #
            #################
            if hasattr(self, "first_warning_minutes"):
                upper = (self.first_warning_minutes + self.sampling_period_minutes) * spm
                usr = self.df[(self.df.elapsedraw < upper) &
                              (self.df.User == user)].copy()
                if not usr.empty:
                    usr.drop(columns=["User", "elapsedraw"], inplace=True)
                    table = usr.to_string(index=False, justify="center").split("\n")
                    tags["<MINUTES-1ST>"] = str(self.first_warning_minutes)
                    tags["<HOURS-1ST>"] = f"{round(self.first_warning_minutes / mph)}"
                    tags["<TABLE>"] = "\n".join([indent + row for row in table])
                    tags["<JOBSTATS>"] = f"{indent}$ jobstats {usr.JobID.values[0]}"
                    tags["<SCANCEL>"] = f"{indent}$ scancel {usr.JobID.values[0]}"
                    translator = EmailTranslator(self.email_files_path,
                                                 self.email_file_first_warning,
                                                 tags)
                    email = translator.replace_tags()
                    self.emails.append((user, email, None))

            ##################
            # second warning #
            ##################
            if hasattr(self, "first_warning_minutes") and \
               hasattr(self, "second_warning_minutes"):
                lower = self.second_warning_minutes * spm
                upper = (self.second_warning_minutes + self.sampling_period_minutes) * spm
                usr = self.df[(self.df.elapsedraw >= lower) &
                              (self.df.elapsedraw <  upper) &
                              (self.df.User == user)].copy()
                if not usr.empty:
                    usr.drop(columns=["User", "elapsedraw"], inplace=True)
                    table = usr.to_string(index=False, justify="center").split("\n")
                    tags["<MINUTES-1ST>"] = str(self.first_warning_minutes)
                    tags["<MINUTES-2ND>"] = str(self.second_warning_minutes)
                    tags["<TABLE>"] = "\n".join([indent + row for row in table])
                    tags["<JOBSTATS>"] = f"{indent}$ jobstats {usr.JobID.values[0]}"
                    tags["<SCANCEL>"] = f"{indent}$ scancel {usr.JobID.values[0]}"
                    translator = EmailTranslator(self.email_files_path,
                                                 self.email_file_second_warning,
                                                 tags)
                    email = translator.replace_tags()
                    self.emails.append((user, email, None))

            ################
            # cancellation #
            ################
            lower = self.cancel_minutes * spm
            usr = self.df[(self.df.elapsedraw >= lower) &
                          (self.df.User == user)].copy()
            if not usr.empty:
                usr["State"] = "CANCELLED"
                tbl = usr[["JobID",
                           "Cluster",
                           "Partition",
                           "State",
                           "GPUs-Allocated",
                           "GPU-Util",
                           "Hours"]].copy()
                table = tbl.to_string(index=False, justify="center").split("\n")
                tags["<TABLE>"] = "\n".join([indent + row for row in table])
                tags["<JOBSTATS>"] = f"{indent}$ jobstats {tbl.JobID.values[0]}"
                tags["<SCANCEL>"] = f"{indent}$ scancel {tbl.JobID.values[0]}"
                translator = EmailTranslator(self.email_files_path,
                                             self.email_file_cancel,
                                             tags)
                email = translator.replace_tags()
                usr["Alert-Partitions"] = ",".join(sorted(set(self.partitions)))
                usr["User"] = user
                usr = usr[["User",
                           "Cluster",
                           "Alert-Partitions",
                           "JobID",
                           "Partition",
                           "GPUs-Allocated",
                           "GPUs-Unused",
                           "Hours"]]
                self.emails.append((user, email, usr))
                self.jobids_to_cancel.extend(usr.JobID.tolist())

    def cancel_jobs(self) -> None:
        """Call scancel on each jobid. For this to work, the code must be ran by
           a user with sufficient privileges."""
        if not self.do_not_cancel:
            for jobid in self.jobids_to_cancel:
                cmd = f"scancel {jobid}"
                _ = subprocess.run(cmd,
                                   stdout=subprocess.PIPE,
                                   shell=True,
                                   timeout=10,
                                   text=True,
                                   check=True)
                print(f"INFO: Cancelled job {jobid} due to zero GPU utilization.")
