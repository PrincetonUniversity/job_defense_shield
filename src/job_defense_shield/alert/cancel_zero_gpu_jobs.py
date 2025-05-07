import os
import sys
import subprocess
import time
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

    """
    Send warnings and automatically cancel jobs with 0% GPU utilization.
    There are two approaches: cancelling based on utilization during the
    first N hours of the job (fixed window) and cancelling based on the
    the last N hours of the job (sliding window).

    When both approaches are used, only jobs that have ran for cancel_minutes
    plus sliding_warning_minutes will be considered when applying the latter.
    This ensures that there will be no overlap between the two. Each approach
    can be used on its own without the other if desired.

    Jobs with an elapsed time plus (sliding cancel - slide warning) that
    are less than limit-minutes cannot be excluded since real limit may
    be UNLIMITED. Would need to add new column to track UNLIMITED jobs.
    Users still receive warnings in these cases. Such jobs are also not
    excluded using the fixed window approach.
    """

    def __init__(self, df, days_between_emails, violation, vpath, **kwargs):
        super().__init__(df, days_between_emails, violation, vpath, **kwargs)

    def _add_required_fields(self):
        if not hasattr(self, "email_subject"):
            self.email_subject = "Jobs with 0% GPU Utilization"
        if not hasattr(self, "gpu_frac_threshold"):
            self.gpu_frac_threshold = 1.0
        if not hasattr(self, "do_not_cancel"):
            self.do_not_cancel = False
        if not hasattr(self, "warning_frac"):
            self.warning_frac = 1.0
        if not hasattr(self, "fraction_of_period"):
            self.fraction_of_period = 0.5
        if (self.num_cancel_alerts > 1) and \
           (self.fraction_of_period >= 0.9 / self.num_cancel_alerts):
            self.fraction_of_period = 0.75 / self.num_cancel_alerts
            print(f"INFO: Forcing fraction_of_period to {self.fraction_of_period}")

    def _filter_and_add_new_fields(self):
        clus_part = f"{self.cluster} ({','.join(sorted(set(self.partitions)))})"
        print(f"INFO: Cancellation of GPU jobs at 0% utilization on {clus_part} is enabled.")
        start_time = time.time()
        self.lg = self.df.copy()
        #########################################
        ## FIXED WINDOW OVER THE FIRST N HOURS ##
        #########################################
        if hasattr(self, "cancel_minutes"):
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
                self.df = self.filter_by_nodelist(self.df)
            self.df.rename(columns={"user":"User"}, inplace=True)
            self.cancellations = []

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
                prts = "_".join(sorted(set(self.partitions)))
                jobid_cache_file = os.path.join(self.jobid_cache_path,
                                                f".jobid_cache_{self.cluster}_{prts}.pkl")
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
                                                                     row["cluster"],
                                                                     verbose=False),
                                                                     axis="columns")
                cols = ["GPUs-Unused", "error_code"]
                self.df[cols] = pd.DataFrame(self.df["zero-tuple"].tolist(),
                                             index=self.df.index)
                self.df = self.df[self.df["error_code"] == 0]
                # write cache file of jobid's that are known to be using the gpus
                if hasattr(self, "jobid_cache_path"):
                    jobs_using_gpus = self.df[self.df["GPUs-Unused"] == 0].jobid.tolist()
                    prts = "_".join(sorted(set(self.partitions)))
                    jobid_cache_file = os.path.join(self.jobid_cache_path,
                                                    f".jobid_cache_{self.cluster}_{prts}.pkl")
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

        ##########################################
        ## SLIDING WINDOW OVER THE LAST N HOURS ##
        ##########################################
        if hasattr(self, "sliding_warning_minutes") and \
           hasattr(self, "sliding_cancel_minutes"):
            if hasattr(self, "cancel_minutes"):
                lower = (self.cancel_minutes + self.sliding_warning_minutes) * spm
            else:
                lower = self.sliding_warning_minutes * spm
            self.lg = self.lg[(self.lg.state == "RUNNING") &
                              (self.lg.gpus > 0) &
                              (self.lg.cluster == self.cluster) &
                              (self.lg.partition.isin(self.partitions)) &
                              (self.lg.elapsedraw >= lower) &
                              (~self.lg.user.isin(self.excluded_users))].copy()
            if not self.lg.empty and hasattr(self, "nodelist"):
                self.lg = self.filter_by_nodelist(self.lg)
            self.sliding_warnings = []
            self.sliding_cancellations = []

            if not self.lg.empty:
                if hasattr(self, "max_interactive_hours") and \
                   hasattr(self, "max_interactive_gpus"):
                    self.lg["interactive"] = self.lg["jobname"].apply(lambda x: True
                                                                      if x.startswith("sys/dashboard") or
                                                                         x.startswith("interactive")
                                                                      else False)
                    msk = (self.lg["interactive"]) & \
                          (self.lg.gpus <= self.max_interactive_gpus) & \
                          (self.lg["limit-minutes"] <= self.max_interactive_hours * mph)
                    self.lg = self.lg[~msk]
                if not hasattr(self, "jobid_cache_path"):
                    print("ERROR: 'jobid_cache_path' must be defined to use sliding_cancel_minutes.")
                    self.lg = pd.DataFrame(columns=self.lg.columns)
                elif not os.path.isdir(self.jobid_cache_path):
                    print("ERROR: 'jobid_cache_path' must exist to use sliding_cancel_minutes.")
                    self.lg = pd.DataFrame(columns=self.lg.columns)
                else:
                    prts = "_".join(sorted(set(self.partitions)))
                    jobid_cache_file = os.path.join(self.jobid_cache_path,
                                                    f".sliding_cache_{self.cluster}_{prts}.csv")
                    if os.path.isfile(jobid_cache_file):
                        # make jobid string since pandas will do this if array job is found
                        cache = pd.read_csv(jobid_cache_file,
                                            dtype={"jobid":str,
                                                   "checked_time":"int64",
                                                   "idle_gpus":"int64"})
                    else:
                        cache = pd.DataFrame(columns=["jobid", "checked_time", "idle_gpus"])

                    def num_idle_gpus_sliding_window(jobid: str,
                                                     window_seconds: int) -> int:
                        """Calculate the number of idle GPUs during the period of the
                           sliding window which is the last N seconds from now. Current
                           version of call to get_job_stats() updates seven properties
                           when only one is needed. Would be nice to pass list of
                           properties that are needed."""
                        sys.path.append(self.jobstats_module_path)
                        sys.path.append(self.jobstats_config_path)
                        from jobstats import Jobstats
                        from config import PROM_SERVER
                        stats = Jobstats(jobid=jobid,
                                         cluster=self.cluster,
                                         prom_server=PROM_SERVER)
                        stats.diff = window_seconds
                        stats.end = time.time()
                        stats.get_job_stats()
                        admincomment = eval(stats.report_job_json(encode=False))
                        n, error_code = num_gpus_with_zero_util(admincomment,
                                                                jobid,
                                                                self.cluster,
                                                                verbose=False)
                        return n if error_code == 0 else 0
                        
                    """
                    If jobid is not in the cache then can only send warning even if GPUs
                    have been idle for sliding_cancel_minutes or longer. This ensures that
                    the user gets a warning before the cancellation. This case will be
                    encountered when the code is first ran and the cache does not exists or
                    when a new job runs for longer than sliding_warning_minutes.

                    To make sure that the code does not run longer than the cron sampling
                    period, the time is checked. The loop is terminated if the cumulative
                    time of the loop approaches the cron sampling period. Eventually all of
                    the running jobs will be cached and the code will execute quickly.

                    Note that n is set to 0 if the fraction of active GPUs was greater than
                    or equal to gpu_frac_threshold. This allows us to use n_prev == 0 later.

                    The loop below runs on jobs from lowest jobid to highest. This is good
                    because the oldest jobs (lowest jobid) have already been cached. Do not
                    want to lose cache data in rare cases when code does not finish before
                    break is reached.
                    """

                    start_time_sliding = time.time()
                    prom_query = 0
                    num_cached_jobs = 0
                    print(f"INFO: Looking for idle GPUs for {len(self.lg)} jobs ... ",
                          end="",
                          flush=True)
                    self.id_time_gpus = []
                    warning_seconds = self.sliding_warning_minutes * spm
                    cancel_seconds = self.sliding_cancel_minutes * spm
                    early_break = False
                    for jobid, num_gpus in zip(self.lg.jobid, self.lg.gpus):
                        jobid = str(jobid)
                        now = round(time.time())
                        if jobid not in cache.jobid.values:
                            n = num_idle_gpus_sliding_window(jobid, warning_seconds)
                            prom_query += 1
                            if 1.0 - n / num_gpus >= self.gpu_frac_threshold:
                                self.id_time_gpus.append([jobid, now, 0])
                            else:
                                self.sliding_warnings.append(jobid)
                                self.id_time_gpus.append([jobid, now, n])
                        else:
                            time_prev = cache[cache.jobid == jobid]["checked_time"].values[0]
                            n_prev = cache[cache.jobid == jobid]["idle_gpus"].values[0]
                            if n_prev == 0:
                                if now - time_prev >= self.warning_frac * warning_seconds:
                                    n = num_idle_gpus_sliding_window(jobid, warning_seconds)
                                    prom_query += 1
                                    if 1.0 - n / num_gpus >= self.gpu_frac_threshold:
                                        self.id_time_gpus.append([jobid, now, 0])
                                    else:
                                        self.sliding_warnings.append(jobid)
                                        self.id_time_gpus.append([jobid, now, n])
                                else:
                                    self.id_time_gpus.append([jobid, time_prev, n_prev])
                            else:
                                if now - time_prev >= cancel_seconds - warning_seconds:
                                    n = num_idle_gpus_sliding_window(jobid, cancel_seconds)
                                    prom_query += 1
                                    if 1.0 - n / num_gpus >= self.gpu_frac_threshold:
                                        self.id_time_gpus.append([jobid, now, 0])
                                    else:
                                        self.sliding_cancellations.append(jobid)
                                        self.id_time_gpus.append([jobid, now, n])
                                else:
                                    self.id_time_gpus.append([jobid, time_prev, n_prev])
                        total_time = time.time() - start_time
                        if total_time > self.fraction_of_period * self.sampling_period_minutes * spm:
                            early_break = True
                            break
                        num_cached_jobs += 1
                    p = f"done ({round(time.time() - start_time_sliding)} seconds, {prom_query} queries)."
                    print(p, flush=True)
                    if early_break:
                        p = f"INFO: Only cached {num_cached_jobs} of {len(self.lg)} jobs. Will try again on next call."
                        print(p)
                    out = pd.DataFrame(self.id_time_gpus,
                                       columns=["jobid", "checked_time", "idle_gpus"])
                    out.to_csv(jobid_cache_file, index=False)

    def create_emails(self, method):
        """Note that the violation history of a user is not considered here
           since this alert is considered urgent. That is, emails are sent
           immediately."""
        if hasattr(self, "cancel_minutes") and not self.df.empty:
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
                    self.cancellations.extend(usr.JobID.tolist())

        if hasattr(self, "sliding_warning_minutes") and \
           hasattr(self, "sliding_cancel_minutes") and \
           not self.lg.empty:
            idle = pd.DataFrame(self.id_time_gpus, columns=["jobid",
                                                            "checked_time",
                                                            "GPUs-Unused"])
            idle.jobid = idle.jobid.astype("str")
            self.lg = pd.merge(self.lg, idle, how="left", on="jobid")
            g = GreetingFactory().create_greeting(method)
            ###################
            # sliding warning #
            ###################
            self.lg["warning"] = self.lg.jobid.apply(lambda j:
                                                     True if j in self.sliding_warnings
                                                     else False)
            wn = self.lg[self.lg["warning"]].copy()
            wn["GPUs-Unused"] = wn["GPUs-Unused"].astype(int)
            wn["GPU-Util"] = "0%"
            wn["Hours"] = wn.elapsedraw.apply(lambda x: round(x / sph, 1))
            wn = wn[["jobid",
                     "user",
                     "cluster",
                     "partition",
                     "state",
                     "gpus",
                     "GPUs-Unused",
                     "GPU-Util",
                     "Hours"]]
            renamings = {"jobid":"JobID",
                         "user":"User",
                         "cluster":"Cluster",
                         "gpus":"GPUs",
                         "partition":"Partition",
                         "state":"State"}
            wn.rename(columns=renamings, inplace=True)
            for user in wn.User.unique():
                usr = wn[wn.User == user].copy()
                usr.drop(columns=["User"], inplace=True)
                table = usr.to_string(index=False, justify="center").split("\n")
                indent = 4 * " "
                tags = {}
                tags["<GREETING>"] = g.greeting(user)
                tags["<CLUSTER>"] = self.cluster
                tags["<PARTITIONS>"] = ",".join(sorted(set(self.partitions)))
                tags["<SAMPLING>"] = str(self.sampling_period_minutes)
                tags["<WARNING-MIN>"] = str(self.sliding_warning_minutes)
                tags["<WARNING-HRS>"] = f"{round(self.sliding_warning_minutes / mph)}"
                tags["<CANCEL-MIN>"] = str(self.sliding_cancel_minutes)
                tags["<CANCEL-HRS>"] = f"{round(self.sliding_cancel_minutes / mph)}"
                tags["<TABLE>"] = "\n".join([indent + row for row in table])
                tags["<JOBSTATS>"] = f"{indent}$ jobstats {usr.JobID.values[0]}"
                tags["<SCANCEL>"] = f"{indent}$ scancel {usr.JobID.values[0]}"
                translator = EmailTranslator(self.email_files_path,
                                             self.email_file_sliding_warning,
                                             tags)
                email = translator.replace_tags()
                self.emails.append((user, email, None))

            ##################
            # sliding cancel #
            ##################
            self.lg["cancel"] = self.lg.jobid.apply(lambda j:
                                                    True if j in self.sliding_cancellations
                                                    else False)
            cl = self.lg[self.lg["cancel"]].copy()
            cl["GPUs-Unused"] = cl["GPUs-Unused"].astype(int)
            cl["State"] = "CANCELLED"
            cl["GPU-Util"] = "0%"
            cl["Hours"] = cl.elapsedraw.apply(lambda x: round(x / sph, 1))
            cl = cl[["jobid",
                     "user",
                     "cluster",
                     "partition",
                     "State",
                     "gpus",
                     "GPUs-Unused",
                     "GPU-Util",
                     "Hours"]]
            renamings = {"jobid":"JobID",
                         "user":"User",
                         "cluster":"Cluster",
                         "partition":"Partition",
                         "gpus":"GPUs-Allocated"}
            cl.rename(columns=renamings, inplace=True)
            for user in cl.User.unique():
                usr = cl[cl.User == user].copy()
                usr.drop(columns=["User"], inplace=True)
                usr.rename(columns={"GPUs-Allocated":"GPUs"}, inplace=True)
                table = usr.to_string(index=False, justify="center").split("\n")
                indent = 4 * " "
                tags = {}
                tags["<GREETING>"] = g.greeting(user)
                tags["<CLUSTER>"] = self.cluster
                tags["<CANCEL-MIN>"] = str(self.sliding_cancel_minutes)
                tags["<CANCEL-HRS>"] = f"{round(self.sliding_cancel_minutes / mph)}"
                tags["<TABLE>"] = "\n".join([indent + row for row in table])
                tags["<JOBSTATS>"] = f"{indent}$ jobstats {usr.JobID.values[0]}"
                tags["<SCANCEL>"] = f"{indent}$ scancel {usr.JobID.values[0]}"
                translator = EmailTranslator(self.email_files_path,
                                             self.email_file_sliding_cancel,
                                             tags)
                email = translator.replace_tags()
                usr = cl[cl.User == user].copy()
                usr["Alert-Partitions"] = ",".join(sorted(set(self.partitions)))
                usr = usr[["User",
                           "Cluster",
                           "Alert-Partitions",
                           "JobID",
                           "Partition",
                           "GPUs-Allocated",
                           "GPUs-Unused",
                           "Hours"]]
                self.emails.append((user, email, usr))

    def cancel_jobs(self) -> None:
        """Call scancel on each jobid. For this to work, the code must be ran by
           a user with sufficient privileges."""
        if not self.do_not_cancel:
            jobids_to_cancel = []
            if hasattr(self, "cancel_minutes"):
                jobids_to_cancel += self.cancellations
            if hasattr(self, "sliding_warning_minutes") and \
               hasattr(self, "sliding_cancel_minutes"):
                jobids_to_cancel += self.sliding_cancellations
            for jobid in jobids_to_cancel:
                cmd = f"scancel {jobid}"
                _ = subprocess.run(cmd,
                                   stdout=subprocess.PIPE,
                                   shell=True,
                                   timeout=10,
                                   text=True,
                                   check=True)
                print(f"INFO: Cancelled job {jobid} on {self.cluster} due to 0% GPU utilization.")
