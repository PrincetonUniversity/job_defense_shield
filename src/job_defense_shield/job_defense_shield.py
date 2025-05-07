import os
import sys
import argparse
from datetime import datetime
from datetime import timedelta
import numpy as np
import pandas as pd
import yaml

from .utils import SECONDS_PER_HOUR as sph
from .utils import gpus_per_job
from .utils import send_email
from .utils import show_history_of_emails_sent
from .workday import WorkdayFactory
from .efficiency import get_stats_dict
from .raw_job_data import SlurmSacct
from .cleaner import SacctCleaner

from .alert.cancel_zero_gpu_jobs import CancelZeroGpuJobs
from .alert.gpu_model_too_powerful import GpuModelTooPowerful
from .alert.zero_util_gpu_hours import ZeroUtilGPUHours
from .alert.excess_cpu_memory import ExcessCPUMemory
from .alert.zero_cpu_utilization import ZeroCPU
from .alert.most_gpus import MostGPUs
from .alert.most_cores import MostCores
from .alert.usage_overview import UsageOverview
from .alert.usage_by_slurm_account import UsageBySlurmAccount
from .alert.longest_queued import LongestQueuedJobs
from .alert.jobs_overview import JobsOverview
from .alert.excessive_time_limits import ExcessiveTimeLimitsCPU
from .alert.excessive_time_limits import ExcessiveTimeLimitsGPU
from .alert.serial_allocating_multiple_cores import SerialAllocatingMultipleCores
from .alert.multinode_cpu_fragmentation import MultinodeCpuFragmentation
from .alert.multinode_gpu_fragmentation import MultinodeGpuFragmentation
from .alert.compute_efficiency import LowEfficiencyCPU
from .alert.compute_efficiency import LowEfficiencyGPU
from .alert.too_many_cores_per_gpu import TooManyCoresPerGpu
from .alert.too_much_cpu_mem_per_gpu import TooMuchCpuMemPerGpu


def main():

    parser = argparse.ArgumentParser(description='Job Defense Shield')
    parser.add_argument('--cancel-zero-gpu-jobs', action='store_true', default=False,
                        help='Cancel running jobs with zero GPU utilization')
    parser.add_argument('--zero-util-gpu-hours', action='store_true', default=False,
                        help='Identify users with the most zero GPU utilization hours')
    parser.add_argument('--zero-cpu-utilization', action='store_true', default=False,
                        help='Identify completed CPU jobs with zero utilization')
    parser.add_argument('--low-cpu-efficiency', action='store_true', default=False,
                        help='Identify users with low CPU efficiency')
    parser.add_argument('--low-gpu-efficiency', action='store_true', default=False,
                        help='Identify users with low GPU efficiency')
    parser.add_argument('--excess-cpu-memory', action='store_true', default=False,
                        help='Identify users that are allocating too much CPU memory')
    parser.add_argument('--gpu-model-too-powerful', action='store_true', default=False,
                        help='Identify jobs that should use less powerful GPUs')
    parser.add_argument('--multinode-cpu-fragmentation', action='store_true', default=False,
                        help='Identify CPU jobs that are split across too many nodes')
    parser.add_argument('--multinode-gpu-fragmentation', action='store_true', default=False,
                        help='Identify GPU jobs that are split across too many nodes')
    parser.add_argument('--excessive-time-cpu', action='store_true', default=False,
                        help='Identify users with excessive run time limits for CPU jobs')
    parser.add_argument('--excessive-time-gpu', action='store_true', default=False,
                        help='Identify users with excessive run time limits for GPU jobs')
    parser.add_argument('--serial-allocating-multiple', action='store_true', default=False,
                        help='Indentify serial codes allocating multiple CPU-cores')
    parser.add_argument('--too-many-cores-per-gpu', action='store_true', default=False,
                        help='Indentify jobs allocating too many CPU-cores per GPU')
    parser.add_argument('--too-much-cpu-mem-per-gpu', action='store_true', default=False,
                        help='Indentify jobs allocating too much CPU memory per GPU')
    parser.add_argument('--usage-overview', action='store_true', default=False,
                        help='Generate a usage report by cluster and partition')
    parser.add_argument('--usage-by-slurm-account', action='store_true', default=False,
                        help='Generate a usage report by cluster, partition and account')
    parser.add_argument('--longest-queued', action='store_true', default=False,
                        help='List the longest queued jobs')
    parser.add_argument('--most-cores', action='store_true', default=False,
                        help='List the largest jobs by number of allocated CPU-cores')
    parser.add_argument('--most-gpus', action='store_true', default=False,
                        help='List the largest jobs by number of allocated GPUs')
    parser.add_argument('--jobs-overview', action='store_true', default=False,
                        help='List the users with the most jobs')
    parser.add_argument('-d', '--days', type=int, default=7, metavar='N',
                        help='Use job data over N previous days from now (default: 7)')
    parser.add_argument('-S', '--starttime', type=str, default=None,
                        help='Start date/time of window (e.g., 2025-01-01T09:00:00)')
    parser.add_argument('-E', '--endtime', type=str, default=None,
                        help='End date/time of window (e.g., 2025-01-31T22:00:00)')
    parser.add_argument('-M', '--clusters', type=str, default="all",
                        help='Specify cluster(s) (e.g., --clusters=frontier,summit)')
    parser.add_argument('-r', '--partition', type=str, default="",
                        help='Specify partition(s) (e.g., --partition=cpu,bigmem)')
    parser.add_argument('--config-file', type=str, default=None,
                        help='Absolute path to the configuration file')
    parser.add_argument('--email', action='store_true', default=False,
                        help='Send email alerts to users and administrators')
    parser.add_argument('--no-emails-to-users', action='store_true', default=False,
                        help='Do not send emails to users but only to administrators (--email is required)')
    parser.add_argument('--no-emails-to-admins', action='store_true', default=False,
                        help='Do not send emails to admins (--email is required)')
    parser.add_argument('--report', action='store_true', default=False,
                        help='Send an email report to administrators')
    parser.add_argument('--check', action='store_true', default=False,
                        help='Show the history of emails sent to users')
    parser.add_argument('-s', '--strict-start', action='store_true', default=False,
                        help='Only include usage during time window and not before')
    args = parser.parse_args()

    if not args.email and args.no_emails_to_users:
        print("--no-emails-to-users must appear with --email. Exiting ...")
        sys.exit()

    if not args.email and args.no_emails_to_admins:
        print("--no-emails-to-admins must appear with --email. Exiting ...")
        sys.exit()

    head = "\nJob Defense Shield (1.1.1)\n"
    head += "github.com/PrincetonUniversity/job_defense_shield\n\n"
    fmt = "%a %b %-d, %Y at %-I:%M %p"
    head += f"INFO: {datetime.now().strftime(fmt)}\n"
    head += f"INFO: Python {sys.version}\n"
    head += f"INFO: Pandas {pd.__version__}\n"
    print(head, end="")

    # read configuration file
    jds_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    cwd_path = os.path.join(os.getcwd(), "config.yaml")
    if args.config_file and os.path.isfile(args.config_file):
        msg = f"INFO: Configuration file is {args.config_file}\n"
        print(msg, end="")
        head += msg
        with open(args.config_file, "r", encoding="utf-8") as fp:
            cfg = yaml.safe_load(fp)
    elif args.config_file and not os.path.isfile(args.config_file):
        print(f"ERROR: Configuration file does not exist ({args.config_file}). Exiting ...")
        sys.exit()
    elif args.config_file is None and os.path.isfile(jds_path):
        msg = f"INFO: Configuration file is {jds_path}\n"
        print(msg, end="")
        head += msg
        with open(jds_path, "r", encoding="utf-8") as fp:
            cfg = yaml.safe_load(fp)
    elif args.config_file is None and os.path.isfile(cwd_path):
        msg = f"INFO: Configuration file is {cwd_path}\n"
        print(msg, end="")
        head += msg
        with open(cwd_path, "r", encoding="utf-8") as fp:
            cfg = yaml.safe_load(fp)
    else:
        print("ERROR: Configuration file not found. Exiting ...")
        sys.exit()

    if "violation-logs-path" not in cfg:
        print('ERROR: "violation-logs-path" must be specified in the configuration file.')
        sys.exit()
    if not os.path.exists(cfg["violation-logs-path"]): 
        dir_path = cfg["violation-logs-path"]
        try:
            os.makedirs(dir_path)
        except OSError:
            print(f"ERROR: Unable to create directory {dir_path}")
            raise
        except FileExistsError:
            print(f"ERROR: Path {dir_path} already exists")
            raise
        except PermissionError:
            print(f"ERROR: Permission denied: Unable to create {dir_path}")
            raise
        except Exception as e:
            print(f"ERROR: An error occurred when making {dir_path}: {e}")
            raise

    if "jobstats-module-path" not in cfg:
        cfg["jobstats-module-path"] = "/usr/local/jobstats/"
    if "jobstats-config-path" not in cfg:
        cfg["jobstats-config-path"] = "/etc/jobstats/"
    if "verbose" not in cfg:
        cfg["verbose"] = False
    if "external-emails" not in cfg:
        cfg["external-emails"] = {}
    if "greeting-method" not in cfg:
        print('INFO: Setting greeting-method to "basic"')
        cfg["greeting-method"] = "basic"
    if "workday-method" not in cfg:
        print('INFO: Setting workday-method to "always"')
        cfg["workday-method"] = "always"
    if "partition-renamings" not in cfg:
        cfg["partition-renamings"] = {}

    sys_cfg = {"no_emails_to_users":   args.no_emails_to_users,
               "no_emails_to_admins":  args.no_emails_to_admins,
               "jobstats_module_path": cfg["jobstats-module-path"],
               "jobstats_config_path": cfg["jobstats-config-path"],
               "email_files_path":     cfg["email-files-path"],
               "verbose":              cfg["verbose"],
               "sender":               cfg["sender"],
               "reply_to":             cfg["reply-to"],
               "email_domain":         cfg["email-domain-name"],
               "external_emails":      cfg["external-emails"]}

    greeting_method = cfg["greeting-method"]
    violation_logs_path = cfg["violation-logs-path"]
    workday_method = cfg["workday-method"]
    holidays_file = cfg["holidays-file"] if "holidays-file" in cfg else None
    is_workday = WorkdayFactory(holidays_file).create_workday(workday_method).is_workday()
    if not is_workday:
        print("INFO: Today is not a workday. Emails to users and administrators will not")
        print("      be sent except for GPU jobs at 0% utilization. To force emails,")
        print("      modify config.yaml with 'workday-method: always'")

    if cfg["verbose"]:
        for key in cfg.keys():
            if any([c.isnumeric() for c in key]):
                print(4 * " " + key)
        for key in cfg.keys():
            if "serial-allocating-multiple" in key:
                print("serial-allocating-multiple", cfg[key]["cluster"], cfg[key]["partitions"])
 
    #######################
    ## CHECK EMAILS SENT ##
    #######################
    if args.check:
        if args.days == 7:
            print("\n\nINFO: Checking with --days=60, instead of the default of 7.\n")
            args.days = 60
        if args.cancel_zero_gpu_jobs:
            show_history_of_emails_sent(violation_logs_path,
                                        "cancel_zero_gpu_jobs",
                                        "CANCEL JOBS WITH ZERO GPU UTILIZATION",
                                        args.days)
        if args.zero_util_gpu_hours:
            show_history_of_emails_sent(violation_logs_path,
                                        "zero_util_gpu_hours",
                                        "GPU-HOURS AT 0% GPU UTILIZATION",
                                        args.days)
        if args.zero_cpu_utilization:
            show_history_of_emails_sent(violation_logs_path,
                                        "zero_cpu_utilization",
                                        "ZERO CPU UTILIZATION OF A RUNNING JOB",
                                        args.days)
        if args.gpu_model_too_powerful:
            show_history_of_emails_sent(violation_logs_path,
                                        "gpu_model_too_powerful",
                                        "GPU MODEL TOO POWERFUL",
                                        args.days)
        if args.low_cpu_efficiency:
            show_history_of_emails_sent(violation_logs_path,
                                        "low_cpu_efficiency",
                                        "LOW CPU EFFICIENCY",
                                        args.days)
        if args.low_gpu_efficiency:
            show_history_of_emails_sent(violation_logs_path,
                                        "low_gpu_efficiency",
                                        "LOW GPU EFFICIENCY",
                                        args.days)
        if args.multinode_cpu_fragmentation:
            show_history_of_emails_sent(violation_logs_path,
                                        "multinode_cpu_fragmentation",
                                        "MULTINODE CPU FRAGMENTATION",
                                        args.days)
        if args.multinode_gpu_fragmentation:
            show_history_of_emails_sent(violation_logs_path,
                                        "multinode_gpu_fragmentation",
                                        "MULTINODE GPU FRAGMENTATION",
                                        args.days)
        if args.excess_cpu_memory:
            show_history_of_emails_sent(violation_logs_path,
                                        "excess_cpu_memory",
                                        "EXCESS CPU MEMORY",
                                        args.days)
        if args.serial_allocating_multiple:
            show_history_of_emails_sent(violation_logs_path,
                                        "serial_allocating_multiple",
                                        "SERIAL CODE ALLOCATING MULTIPLE CPU-CORES",
                                        args.days)
        if args.too_many_cores_per_gpu:
            show_history_of_emails_sent(violation_logs_path,
                                        "too_many_cores_per_gpu",
                                        "TOO MANY CPU-CORES PER GPU",
                                        args.days)
        if args.too_much_cpu_mem_per_gpu:
            show_history_of_emails_sent(violation_logs_path,
                                        "too_much_cpu_mem_per_gpu",
                                        "TOO MUCH CPU MEMORY PER GPU",
                                        args.days)
        if args.excessive_time_cpu:
            show_history_of_emails_sent(violation_logs_path,
                                        "excessive_time_limits_cpu",
                                        "EXCESSIVE TIME LIMITS (CPU)",
                                        args.days)

        if args.excessive_time_gpu:
            show_history_of_emails_sent(violation_logs_path,
                                        "excessive_time_limits_gpu",
                                        "EXCESSIVE TIME LIMITS (GPU)",
                                        args.days)
        if args.most_gpus or \
           args.most_cores or \
           args.usage_overview or \
           args.usage_by_slurm_account or \
           args.jobs_overview or \
           args.longest_queued:
            print(("Nothing to check for --most-gpus, --most-cores, "
                   "--usage-overview, --usage-by-slurm-account, "
                   "--jobs-overview or --longest-queued."))
        sys.exit()

    # pandas display settings
    pd.set_option("display.max_rows", None)
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 1000)

    if args.starttime is None or args.endtime is None:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=args.days)
    else:
        # check format
        pass

    fields = ["jobid",
              "user",
              "cluster",
              "account",
              "partition",
              "cputimeraw",
              "elapsedraw",
              "timelimitraw",
              "nnodes",
              "ncpus",
              "alloctres",
              "submit",
              "eligible",
              "start",
              "end",
              "qos",
              "state",
              "admincomment",
              "jobname"]
    # jobname must be last in list below to catch "|" characters in jobname
    assert fields[-1] == "jobname"
    fields = ",".join(fields)

    use_cache = False if (args.email or args.report) else True
    raw = SlurmSacct(args.days,
                     args.starttime,
                     args.endtime,
                     fields,
                     args.clusters,
                     args.partition)
    raw = raw.get_job_data()

    # clean the raw data
    field_renamings = {"cputimeraw":"cpu-seconds",
                       "nnodes":"nodes",
                       "ncpus":"cores",
                       "timelimitraw":"limit-minutes"}
    partition_renamings = cfg["partition-renamings"]
    df = SacctCleaner(raw, field_renamings, partition_renamings).clean()
    pending = df[df.state == "PENDING"].copy()
    df = df[(df.state != "PENDING") & (df.elapsedraw > 0)]

    num_nulls = df.isnull().sum().sum()
    if num_nulls:
        print(f"Number of null values in df: {num_nulls}")

    if args.strict_start:
        # remove usage before the start of the time window
        df["secs-from-start"] = df["start"] - start_date.timestamp()
        df["secs-from-start"] = df["secs-from-start"].apply(lambda x: x if x < 0 else 0)
        df["elapsedraw"] = df["elapsedraw"] + df["secs-from-start"]

    def add_new_and_derived_fields(df):
        df["cpu-seconds"] = df["elapsedraw"] * df["cores"]
        df["gpus"] = df.alloctres.apply(gpus_per_job)
        df["gpu-seconds"] = df["elapsedraw"] * df["gpus"]
        df["cpu-only-seconds"] = np.where(df["gpus"] == 0, df["cpu-seconds"], 0)
        df["elapsed-hours"] = df["elapsedraw"] / sph
        df.loc[df["start"] != "Unknown", "start-date"] = pd.to_datetime(df["start"].astype(int), unit='s').dt.strftime("%a %-m/%d")
        df["cpu-hours"] = df["cpu-seconds"] / sph
        df["gpu-hours"] = df["gpu-seconds"] / sph
        df["admincomment"] = df["admincomment"].apply(get_stats_dict)
        return df

    df = add_new_and_derived_fields(df)
    df.reset_index(drop=True, inplace=True)

    s = "\n"
    ###########################################
    ## CANCEL JOBS WITH ZERO GPU UTILIZATION ##
    ###########################################
    if args.cancel_zero_gpu_jobs:
        alerts = [alert for alert in cfg.keys() if "cancel-zero-gpu-jobs" in alert]
        for alert in alerts:
            params = cfg[alert]
            params.update(sys_cfg)
            params.update({"num_cancel_alerts":len(alerts)})
            cancel_gpu = CancelZeroGpuJobs(df,
                                           days_between_emails=1,
                                           violation="cancel_zero_gpu_jobs",
                                           vpath=violation_logs_path,
                                           **params)
            if args.email:
                cancel_gpu.create_emails(greeting_method)
                cancel_gpu.send_emails_to_users()
                cancel_gpu.cancel_jobs()


    ################################
    ## ZERO UTILIZATION GPU-HOURS ##
    ################################
    if args.zero_util_gpu_hours:
        alerts = [alert for alert in cfg.keys() if "zero-util-gpu-hours" in alert]
        for alert in alerts:
            params = cfg[alert]
            params.update(sys_cfg)
            zero_gpu_hours = ZeroUtilGPUHours(df,
                                   days_between_emails=args.days,
                                   violation="zero_util_gpu_hours",
                                   vpath=violation_logs_path,
                                   **params)
            if args.email and is_workday:
                zero_gpu_hours.create_emails(greeting_method)
                zero_gpu_hours.send_emails_to_users()
            s += zero_gpu_hours.generate_report_for_admins(keep_index=True)
            s += zero_gpu_hours.add_report_metadata(start_date, end_date)


    ############################
    ## TOO MANY CORES PER GPU ##
    ############################
    if args.too_many_cores_per_gpu:
        alerts = [alert for alert in cfg.keys() if "too-many-cores-per-gpu" in alert]
        for alert in alerts:
            params = cfg[alert]
            params.update(sys_cfg)
            cpg = TooManyCoresPerGpu(df,
                                     days_between_emails=args.days,
                                     violation="too_many_cores_per_gpu",
                                     vpath=violation_logs_path,
                                     **params)
            if args.email and is_workday:
                cpg.create_emails(greeting_method)
                cpg.send_emails_to_users()
            s += cpg.generate_report_for_admins()
            s += cpg.add_report_metadata(start_date, end_date)


    #################################
    ## TOO MUCH CPU MEMORY PER GPU ##
    #################################
    if args.too_much_cpu_mem_per_gpu:
        alerts = [alert for alert in cfg.keys() if "too-much-cpu-mem-per-gpu" in alert]
        for alert in alerts:
            params = cfg[alert]
            params.update(sys_cfg)
            mpg = TooMuchCpuMemPerGpu(df,
                                      days_between_emails=args.days,
                                      violation="too_much_cpu_mem_per_gpu",
                                      vpath=violation_logs_path,
                                      **params)
            if args.email and is_workday:
                mpg.create_emails(greeting_method)
                mpg.send_emails_to_users()
            s += mpg.generate_report_for_admins()
            s += mpg.add_report_metadata(start_date, end_date)


    #################################
    ## MULTINODE GPU FRAGMENTATION ##
    #################################
    if args.multinode_gpu_fragmentation:
        alerts = [alert for alert in cfg.keys() if "multinode-gpu-fragmentation" in alert]
        for alert in alerts:
            params = cfg[alert]
            params.update(sys_cfg)
            gpu_frag = MultinodeGpuFragmentation(df,
                                   days_between_emails=args.days,
                                   violation="multinode_gpu_fragmentation",
                                   vpath=violation_logs_path,
                                   **params)
            if args.email and is_workday:
                gpu_frag.create_emails(greeting_method)
                gpu_frag.send_emails_to_users()
            s += gpu_frag.generate_report_for_admins()
            s += gpu_frag.add_report_metadata(start_date, end_date)


    ########################
    ## LOW GPU EFFICIENCY ##
    ########################
    if args.low_gpu_efficiency:
        alerts = [alert for alert in cfg.keys() if "low-gpu-efficiency" in alert]
        for alert in alerts:
            params = cfg[alert]
            params.update(sys_cfg)
            low_gpu = LowEfficiencyGPU(df,
                                       days_between_emails=args.days,
                                       violation="low_gpu_efficiency",
                                       vpath=violation_logs_path,
                                       **params)
            if args.email and is_workday:
                low_gpu.create_emails(greeting_method)
                low_gpu.send_emails_to_users()
            s += low_gpu.generate_report_for_admins()
            s += low_gpu.add_report_metadata(start_date, end_date)


    #################################
    ## EXCESSIVE TIME LIMITS (GPU) ##
    #################################
    if args.excessive_time_gpu:
        alerts = [alert for alert in cfg.keys() if "excessive-time-gpu" in alert]
        for alert in alerts:
            params = cfg[alert]
            params.update(sys_cfg)
            time_limits = ExcessiveTimeLimitsGPU(
                                              df,
                                              days_between_emails=args.days,
                                              violation="excessive_time_limits_gpu",
                                              vpath=violation_logs_path,
                                              **params)
            if args.email and is_workday:
                time_limits.create_emails(greeting_method)
                time_limits.send_emails_to_users()
            s += time_limits.generate_report_for_admins()
            s += time_limits.add_report_metadata(start_date, end_date)


    ############################
    ## GPU MODEL TOO POWERFUL ##
    ############################
    if args.gpu_model_too_powerful:
        alerts = [alert for alert in cfg.keys() if "gpu-model-too-powerful" in alert]
        for alert in alerts:
            params = cfg[alert]
            params.update(sys_cfg)
            too_power = GpuModelTooPowerful(df,
                                            days_between_emails=args.days,
                                            violation="gpu_model_too_powerful",
                                            vpath=violation_logs_path,
                                            **params)
            if args.email and is_workday:
                too_power.create_emails(greeting_method)
                too_power.send_emails_to_users()
            s += too_power.generate_report_for_admins()
            s += too_power.add_report_metadata(start_date, end_date)


    ##########################
    ## ZERO CPU UTILIZATION ##
    ##########################
    if args.zero_cpu_utilization:
        alerts = [alert for alert in cfg.keys() if "zero-cpu-utilization" in alert]
        for alert in alerts:
            params = cfg[alert]
            params.update(sys_cfg)
            zero_cpu = ZeroCPU(df,
                               days_between_emails=args.days,
                               violation="zero_cpu_utilization",
                               vpath=violation_logs_path,
                               **params)
            if args.email and is_workday:
                zero_cpu.create_emails(greeting_method)
                zero_cpu.send_emails_to_users()
            s += zero_cpu.generate_report_for_admins()
            s += zero_cpu.add_report_metadata(start_date, end_date)


    ########################
    ## LOW CPU EFFICIENCY ##
    ########################
    if args.low_cpu_efficiency:
        alerts = [alert for alert in cfg.keys() if "low-cpu-efficiency" in alert]
        for alert in alerts:
            params = cfg[alert]
            params.update(sys_cfg)
            low_cpu = LowEfficiencyCPU(df,
                                       days_between_emails=args.days,
                                       violation="low_cpu_efficiency",
                                       vpath=violation_logs_path,
                                       **params)
            if args.email and is_workday:
                low_cpu.create_emails(greeting_method)
                low_cpu.send_emails_to_users()
            s += low_cpu.generate_report_for_admins()
            s += low_cpu.add_report_metadata(start_date, end_date)


    #######################
    ## EXCESS CPU MEMORY ##
    #######################
    if args.excess_cpu_memory:
        alerts = [alert for alert in cfg.keys() if "excess-cpu-memory" in alert]
        for alert in alerts:
            params = cfg[alert]
            params.update(sys_cfg)
            mem_hours = ExcessCPUMemory(df,
                                        days_between_emails=args.days,
                                        violation="excess_cpu_memory",
                                        vpath=violation_logs_path,
                                        **params)
            if args.email and is_workday:
                mem_hours.create_emails(greeting_method)
                mem_hours.send_emails_to_users()
            s += mem_hours.generate_report_for_admins(keep_index=True)
            s += mem_hours.add_report_metadata(start_date, end_date)


    ###########################################
    ## SERIAL CODE ALLOCATING MULTIPLE CORES ##
    ###########################################
    if args.serial_allocating_multiple:
        alerts = [alert for alert in cfg.keys() if "serial-allocating-multiple" in alert]
        for alert in alerts:
            params = cfg[alert]
            params.update(sys_cfg)
            serial = SerialAllocatingMultipleCores(df,
                                     days_between_emails=args.days,
                                     violation="serial_allocating_multiple",
                                     vpath=violation_logs_path,
                                     **params)
            if args.email and is_workday:
                serial.create_emails(greeting_method)
                serial.send_emails_to_users()
            s += serial.generate_report_for_admins(keep_index=True)
            s += serial.add_report_metadata(start_date, end_date)


    #################################
    ## MULTINODE CPU FRAGMENTATION ##
    #################################
    if args.multinode_cpu_fragmentation:
        alerts = [alert for alert in cfg.keys() if "multinode-cpu-fragmentation" in alert]
        for alert in alerts:
            params = cfg[alert]
            params.update(sys_cfg)
            cpu_frag = MultinodeCpuFragmentation(df,
                                   days_between_emails=args.days,
                                   violation="multinode_cpu_fragmentation",
                                   vpath=violation_logs_path,
                                   **params)
            if args.email and is_workday:
                cpu_frag.create_emails(greeting_method)
                cpu_frag.send_emails_to_users()
            s += cpu_frag.generate_report_for_admins(keep_index=False)
            s += cpu_frag.add_report_metadata(start_date, end_date)


    #################################
    ## EXCESSIVE TIME LIMITS (CPU) ##
    #################################
    if args.excessive_time_cpu:
        alerts = [alert for alert in cfg.keys() if "excessive-time-cpu" in alert]
        for alert in alerts:
            params = cfg[alert]
            params.update(sys_cfg)
            time_limits = ExcessiveTimeLimitsCPU(
                                              df,
                                              days_between_emails=args.days,
                                              violation="excessive_time_limits_cpu",
                                              vpath=violation_logs_path,
                                              **params)
            if args.email and is_workday:
                time_limits.create_emails(greeting_method)
                time_limits.send_emails_to_users()
            s += time_limits.generate_report_for_admins()
            s += time_limits.add_report_metadata(start_date, end_date)


    ####################
    ## USAGE OVERVIEW ##
    ####################
    if args.usage_overview:
        usage = UsageOverview(df,
                              days_between_emails=args.days,
                              violation="null",
                              vpath=violation_logs_path)
        s += usage.generate_report_for_admins()
        s += usage.add_report_metadata(start_date,
                                       end_date,
                                       dates_only=True)


    ############################
    ## USAGE BY SLURM ACCOUNT ##
    ############################
    if args.usage_by_slurm_account:
        usage_acc = UsageBySlurmAccount(df,
                                        days_between_emails=args.days,
                                        violation="null",
                                        vpath=violation_logs_path)
        s += usage_acc.generate_report_for_admins()
        s += usage_acc.add_report_metadata(start_date,
                                           end_date,
                                           dates_only=True)


    #########################
    ## LONGEST QUEUED JOBS ##
    #########################
    if args.longest_queued:
        queued = LongestQueuedJobs(pending,
                                   days_between_emails=args.days,
                                   violation="null",
                                   vpath=violation_logs_path)
        s += queued.generate_report_for_admins()
        s += queued.add_report_metadata(start_date,
                                        end_date,
                                        dates_only=True)


    ###################
    ## JOBS OVERVIEW ##
    ###################
    if args.jobs_overview:
        jobs = JobsOverview(df,
                            days_between_emails=args.days,
                            violation="null",
                            vpath=violation_logs_path)
        s += jobs.generate_report_for_admins()
        s += jobs.add_report_metadata(start_date,
                                      end_date,
                                      dates_only=True)


    ####################
    ## MOST CPU-CORES ##
    ####################
    if args.most_cores:
        most_cores = MostCores(df,
                               days_between_emails=args.days,
                               violation="null",
                               vpath=violation_logs_path)
        s += most_cores.generate_report_for_admins()
        s += most_cores.add_report_metadata(start_date,
                                            end_date,
                                            dates_only=True)


    ###############
    ## MOST GPUS ##
    ###############
    if args.most_gpus:
        most_gpus = MostGPUs(df,
                             days_between_emails=args.days,
                             violation="null",
                             vpath=violation_logs_path)
        s += most_gpus.generate_report_for_admins()
        s += most_gpus.add_report_metadata(start_date,
                                           end_date,
                                           dates_only=True)


    ####################################
    ## SEND REPORT BY EMAIL TO ADMINS ##
    ####################################
    if args.report:
        if "report-emails" in cfg and "sender" in cfg:
            for report_email in cfg["report-emails"]:
                send_email(head + s,
                           report_email,
                           subject="Cluster Utilization Report",
                           sender=cfg["sender"],
                           reply_to=cfg["reply-to"])
        else:
            msg = ("ERROR: --report was found but report-emails and/or "
                   "sender were not defined in config.yaml.\n\n")
            print(msg)

    print(s, end="\n\n")


if __name__ == "__main__":
    main()
