import os
import sys
import re
import glob
import smtplib
import ssl
from datetime import datetime
from datetime import timedelta
from typing import Tuple
from typing import Optional
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import yaml
import numpy as np
import pandas as pd


# conversion factors
SECONDS_PER_MINUTE = 60
SECONDS_PER_HOUR = 3600
MINUTES_PER_HOUR = 60
HOURS_PER_DAY = 24

# slurm job states
states = {
  'BF'  :'BOOT_FAIL',
  'CLD' :'CANCELLED',
  'COM' :'COMPLETED',
  'DL'  :'DEADLINE',
  'F'   :'FAILED',
  'NF'  :'NODE_FAIL',
  'OOM' :'OUT_OF_MEMORY',
  'PD'  :'PENDING',
  'PR'  :'PREEMPTED',
  'R'   :'RUNNING',
  'RQ'  :'REQUEUED',
  'RS'  :'RESIZING',
  'RV'  :'REVOKED',
  'S'   :'SUSPENDED',
  'TO'  :'TIMEOUT'
  }
JOBSTATES = dict(zip(states.values(), states.keys()))

def show_history_of_emails_sent(vpath, mydir, title, day_ticks) -> None:
    """Display the history of emails sent to users."""
    files = sorted(glob.glob(f"{vpath}/{mydir}/*.csv"))
    if len(files) == 0:
        print(f"No underutilization files found in {vpath}/{mydir}")
        return None
    max_netid = max([len(f.split("/")[-1].split(".")[0]) for f in files])
    title += " (EMAILS SENT)"
    width = max(len(title), max_netid + day_ticks + 1)
    print("=" * width)
    print(title.center(width))
    print("=" * width)
    print(" " * (max_netid + day_ticks - 2) + "today")
    print(" " * (max_netid + day_ticks - 0) + "|")
    print(" " * (max_netid + day_ticks - 0) + "V")
    X = 0
    num_users = 0
    today = datetime.now().date()
    for f in files:
        netid = f.split("/")[-1].split(".")[0]
        df = pd.read_csv(f, parse_dates=["Email-Sent"], date_format="mixed", dayfirst=False)
        df["when"] = df["Email-Sent"].apply(lambda x: x.date())
        hits = df.when.unique()
        row = []
        for i in range(day_ticks):
            dt = today - timedelta(days=i)
            day_of_week = dt.weekday()
            char = "_"
            if day_of_week >= 5:
                char = " "
            if dt in hits:
                char = "X"
            row.append(char)
        s = " " * (max_netid - len(netid)) + netid + " "
        s += ''.join(row)[::-1]
        if "X" in s:
            print(s)
            X += s.count("X")
            num_users += 1
    print("\n" + "=" * width)
    print(f"Number of X: {X}")
    print(f"Number of users: {num_users}")
    print(f"Violation files: {vpath}/{mydir}/\n")
    return None

def seconds_to_slurm_time_format(seconds: int) -> str:
    """Convert the number of seconds to DD-HH:MM:SS"""
    hour = seconds // 3600
    if hour >= 24:
        days = "%d-" % (hour // 24)
        hour %= 24
        hour = days + ("%02d:" % hour)
    else:
        if hour > 0:
            hour = "%02d:" % hour
        else:
            hour = '00:'
    seconds = seconds % (24 * 3600)
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    return "%s%02d:%02d" % (hour, minutes, seconds)

def read_config_file(config_file: Optional[str],
                     jds_path: Optional[str],
                     cwd_path: Optional[str],
                     head: str,
                     no_emails_to_users: bool,
                     no_emails_to_admins: bool) -> Tuple[dict, dict, str]:
    """Find and read the YAML configuration file. Return a dictionary of
       the alerts (cfg), a dictionary of the system settings (sys_cfg), and
       the output text (head)."""
    if config_file and os.path.isfile(config_file):
        msg = f"INFO: Configuration file is {config_file}\n"
        print(msg, end="")
        head += msg
        with open(config_file, "r", encoding="utf-8") as fp:
            cfg = yaml.safe_load(fp)
    elif config_file and not os.path.isfile(config_file):
        print(f"ERROR: Configuration file does not exist ({config_file}). Exiting ...")
        sys.exit()
    elif config_file is None and os.path.isfile(jds_path):
        msg = f"INFO: Configuration file is {jds_path}\n"
        print(msg, end="")
        head += msg
        with open(jds_path, "r", encoding="utf-8") as fp:
            cfg = yaml.safe_load(fp)
    elif config_file is None and os.path.isfile(cwd_path):
        msg = f"INFO: Configuration file is {cwd_path}\n"
        print(msg, end="")
        head += msg
        with open(cwd_path, "r", encoding="utf-8") as fp:
            cfg = yaml.safe_load(fp)
    else:
        print("ERROR: Configuration file not found. Exiting ...")
        sys.exit()

    # check for and/or create the violation logs directory
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
    if "email-method" not in cfg:
        cfg["email-method"] = "simple"
    if "email-domain-name" not in cfg:
        cfg["email-domain-name"] = None
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
    if "show-empty-reports" not in cfg:
        cfg["show-empty-reports"] = False
    if "partition-renamings" not in cfg:
        cfg["partition-renamings"] = {}
    if "smtp-server" not in cfg:
        cfg["smtp-server"] = None
    if "smtp-user" not in cfg:
        cfg["smtp-user"] = None
    if "smtp-password" not in cfg:
        cfg["smtp-password"] = None
    smtp_password_from_env = os.getenv("JOBSTATS_SMTP_PASSWORD")
    if smtp_password_from_env:
        cfg["smtp-password"] = smtp_password_from_env
    if "smtp-port" not in cfg:
        cfg["smtp-port"] = None
    if "ldap-server" not in cfg:
        cfg["ldap-server"] = None
    if "ldap-dn" not in cfg:
        cfg["ldap-dn"] = None
    if "ldap-base-dn" not in cfg:
        cfg["ldap-base-dn"] = None
    if "ldap-password" not in cfg:
        cfg["ldap-password"] = None
    if "ldap-uid" not in cfg:
        cfg["ldap-uid"] = "uid"
    if "ldap-displayname" not in cfg:
        cfg["ldap-displayname"] = "displayname"
    if "ldap-mail" not in cfg:
        cfg["ldap-mail"] = "mail"

    # ldap parameters
    ldap_params = {"ldap_server":      cfg["ldap-server"],
                   "ldap_dn":          cfg["ldap-dn"],
                   "ldap_base_dn":     cfg["ldap-base-dn"],
                   "ldap_password":    cfg["ldap-password"],
                   "ldap_uid":         cfg["ldap-uid"],
                   "ldap_displayname": cfg["ldap-displayname"],
                   "ldap_mail":        cfg["ldap-mail"]}

    # system or global configuration settings
    sys_cfg = {"no_emails_to_users":   no_emails_to_users,
               "no_emails_to_admins":  no_emails_to_admins,
               "jobstats_module_path": cfg["jobstats-module-path"],
               "jobstats_config_path": cfg["jobstats-config-path"],
               "email_files_path":     cfg["email-files-path"],
               "verbose":              cfg["verbose"],
               "sender":               cfg["sender"],
               "reply_to":             cfg["reply-to"],
               "email_method":         cfg["email-method"],
               "email_domain":         cfg["email-domain-name"],
               "external_emails":      cfg["external-emails"],
               "smtp_server":          cfg["smtp-server"],
               "smtp_user":            cfg["smtp-user"],
               "smtp_password":        cfg["smtp-password"],
               "smtp_port":            cfg["smtp-port"],
               "show_empty_reports":   cfg["show-empty-reports"],
               "ldap":                 ldap_params}
    return cfg, sys_cfg, head


def display_alerts(cfg: dict) -> str:
    """Return a listing of the alerts found in the configuration file."""
    alerts = ["cancel-zero-gpu-jobs",
              "zero-util-gpu-hours",
              "low-gpu-efficiency",
              "too-much-cpu-mem-per-gpu",
              "too-many-cores-per-gpu",
              "gpu-model-too-powerful",
              "multinode-gpu-fragmentation",
              "excessive-time-gpu",
              "zero-cpu-utilization",
              "excess-cpu-memory",
              "low-cpu-efficiency",
              "serial-allocating-multiple",
              "multinode-cpu-fragmentation",
              "excessive-time-cpu"]
    indent = 2 * " "
    count = 0
    output = "INFO: The following alerts were found in the configuration file:\n"
    for key in cfg.keys():
        for alert in alerts:
            if alert in key:
                count += 1
                count_fmt = count if count > 9 else f" {count}"
                output += f"{4 * indent}{count_fmt}. {key}\n"
                cluster = cfg[key]["cluster"]
                partitions = ",".join(cfg[key]["partitions"])
                output += f"{7 * indent}cluster: {cluster}\n"
                output += f"{7 * indent}partitions: {partitions}\n"
    return f"{output}{4 * indent}None" if count == 0 else output[:-1]

def prepare_datetimes(starttime: Optional[str],
                      endtime: Optional[str],
                      days: int) -> Tuple[datetime, datetime]:
    """If user only supplies --days then calculate start and end based
       on current time. Otherwise calculate start and end based on what
       is provided."""
    fmt = "%Y-%m-%dT%H:%M:%S"
    if starttime is not None and endtime is None:
        start_date = datetime.strptime(starttime, fmt)
        end_date = start_date + timedelta(days=days)
        return start_date, end_date
    elif starttime is None and endtime is not None:
        end_date = datetime.strptime(endtime, fmt)
        start_date = end_date - timedelta(days=days)
        return start_date, end_date
    elif starttime is not None and endtime is not None:
        start_date = datetime.strptime(starttime, fmt)
        end_date = datetime.strptime(endtime, fmt)
        return start_date, end_date
    else:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        return start_date, end_date

def gpus_per_job(tres: str) -> int:
    """Return the number of allocated GPUs."""
    gpus = re.findall(r"gres/gpu=\d+", tres)
    return int(gpus[0].replace("gres/gpu=", "")) if gpus else 0

def apply_strict_start(df: pd.DataFrame,
                       start_date: datetime) -> pd.DataFrame:
    """Remove usage before the start of the time window. By default
       Slurm sacct will include job data from before the starting
       value."""
    df["secs-from-start"] = df["start"] - start_date.timestamp()
    df["secs-from-start"] = df["secs-from-start"].apply(lambda x: x if x < 0 else 0)
    df["elapsedraw"] = df["elapsedraw"] + df["secs-from-start"]
    df.drop(columns=["secs-from-start"], inplace=True)
    return df

def add_new_and_derived_fields(df: pd.DataFrame) -> pd.DataFrame:
    """Add new fields to the dataframe."""
    df["cpu-seconds"] = df["elapsedraw"] * df["cores"]
    df["gpus"] = df.alloctres.apply(gpus_per_job)
    df["gpu-seconds"] = df["elapsedraw"] * df["gpus"]
    df["cpu-only-seconds"] = np.where(df["gpus"] == 0, df["cpu-seconds"], 0)
    df["elapsed-hours"] = df["elapsedraw"] / SECONDS_PER_HOUR
    df.loc[df["start"] != "Unknown", "start-date"] = pd.to_datetime(df["start"].astype(int),
                                                                    unit='s').dt.strftime("%a %-m/%d")
    df["cpu-hours"] = df["cpu-seconds"] / SECONDS_PER_HOUR
    df["gpu-hours"] = df["gpu-seconds"] / SECONDS_PER_HOUR
    return df

def add_dividers(df_str: str,
                 title: str="",
                 pre: str="\n\n\n",
                 units_row: bool=False,
                 clusters: bool=False) -> str:
    """Add horizontal dividers to the output tables."""
    rows = df_str.split("\n")
    width = max([len(row) for row in rows] + [len(title)])
    heading = title.center(width)
    divider = "-" * width
    divider_half = "- " * (width // 2)
    if title and not units_row:
        rows.insert(0, heading)
        rows.insert(1, divider)
        rows.insert(3, divider)
        if clusters:
            cluster_change = []
            prev = rows[4].split()[0]
            for i, row in enumerate(rows[4:]):
                curr = row.split()[0]
                if curr != prev:
                    cluster_change.append(i + 4)
                    prev = curr
            for i, idx in enumerate(cluster_change):
               rows.insert(idx + i, divider_half)
    elif title and units_row:
        rows.insert(0, heading)
        rows.insert(1, divider)
        rows.insert(4, divider)
    else:
        rows.insert(0, divider)
        rows.insert(2, divider)
    rows.append(divider)
    return pre + "\n".join(rows) + "\n"

def send_email(email_body: str,
               addressee: str,
               subject: str,
               sender: str,
               reply_to: str,
               smtp_server: Optional[str],
               smtp_user: Optional[str],
               smtp_password: Optional[str],
               smtp_port: Optional[int],
               verbose: bool) -> None:
    """Send an email using simple HTML. If smtp_server is not None then use
       an external SMTP server as specified in the configuration file. One
       advantage of using MIMEMultipart is that an attachment could be added
       as a new feature."""
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = addressee
    msg.add_header("reply-to", reply_to)
    text = ""
    font = '<font face="Courier New, Courier, monospace">'
    html = f'<html><head></head><body>{font}<pre>{email_body}</pre></font></body></html>'
    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')
    msg.attach(part1)
    msg.attach(part2)
    if smtp_server:
        if verbose:
            print(f"INFO: SMTP server: {smtp_server}")
            print(f"INFO: SMTP user: {smtp_user}")
            passwd = smtp_password[0] + (len(smtp_password) - 1) * "*"
            print(f"INFO: SMTP password: {passwd}")
            print(f"INFO: SMTP port: {smtp_port}")
        try:
            context = ssl.create_default_context()
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls(context=context)
                server.login(smtp_user, smtp_password)
                server.sendmail(sender, addressee, msg.as_string())
        except Exception as e:
            print(f"ERROR: Failed to send email using external SMTP server: {e}")
    else:
        with smtplib.SMTP('localhost') as server:
            server.sendmail(sender, addressee, msg.as_string())

def send_email_enhanced(email_body: str,
                        addressee: str,
                        subject: str,
                        sender: str,
                        reply_to: str) -> None:
    """Send an email using HTML. Use nested tables and styles:
       https://kinsta.com/blog/html-email/
       and https://www.emailvendorselection.com/create-html-email/"""
    from email.message import EmailMessage
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = addressee
    msg.add_header("reply-to", reply_to)
    html = '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
    html += '<meta name="viewport" content="width=device-width,initial-scale=1">'
    html += '<title></title></head><body><table width="600px" border="0"><tr>'
    html += f'<td align="center">{email_body}</td></tr></table></body></html>'
    msg.set_content(html, subtype="html")
    with smtplib.SMTP('localhost') as server:
        server.send_message(msg)
