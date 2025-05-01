import os
import sys
from time import time
from datetime import datetime
from abc import abstractmethod
import pandas as pd

from .utils import send_email
from .utils import SECONDS_PER_HOUR as sph
from .utils import HOURS_PER_DAY as hpd
from .efficiency import get_nodelist


class Alert:

    """Base class for all alerts. The named parameters in props will
       overwrite the default values of attributes. For example, if
       excluded_users is defined in the alert in config.yaml then it
       will take on those values (if not then it will be an empty list)."""

    def __init__(self,
                 df: pd.DataFrame,
                 days_between_emails: int,
                 violation: str,
                 vpath: str,
                 **props: dict) -> None:
        self.df = df
        self.days_between_emails = days_between_emails
        self.violation = violation
        self.vpath = vpath
        self.vbase = os.path.join(self.vpath, self.violation)
        self.excluded_users = []
        self.emails = []
        self.email_file = None
        self.admin_emails = []
        self.min_run_time = 0
        self.include_running_jobs = False
        # next line needed for send_emails_to_users
        self.warnings_to_admin = True
        for key in props:
            setattr(self, key, props[key])
        if hasattr(self, "partitions") and isinstance(self.partitions, str):
            self.partitions = [self.partitions]
        self._add_required_fields()
        self._filter_and_add_new_fields()
        if self.vbase and not os.path.exists(self.vbase):
            os.mkdir(self.vbase)

    @abstractmethod
    def _add_required_fields(self) -> None:
        """Add fields that were not defined in the configuration file.

        Returns:
            None
        """

    @abstractmethod
    def _filter_and_add_new_fields(self) -> None:
        """Filter the dataframe and add new fields.

        Returns:
            None
        """

    @abstractmethod
    def create_emails(self) -> None:
        """Create emails to the users.

        Returns:
            None
        """

    def send_emails_to_users(self) -> None:
        """Send emails to users and administrators. Update the violation
           log file of each user. The value of usr can be None in
           cancel_zero_gpu_jobs."""
        if not self.no_emails_to_users:
            for user, email, usr in self.emails:
                if user in self.external_emails:
                    user_email_address = self.external_emails[user]
                else:
                    user_email_address = f"{user}{self.email_domain}"
                send_email(email,
                           user_email_address,
                           subject=self.email_subject,
                           sender=self.sender,
                           reply_to=self.reply_to)
                print(email)
                if usr is not None:
                    vfile = f"{self.vpath}/{self.violation}/{user}.csv"
                    self.update_violation_log(usr, vfile)
        if not self.no_emails_to_admins:
            for user, email, usr in self.emails:
                for admin_email in self.admin_emails:
                    if usr is not None or (usr is None and self.warnings_to_admin):
                        send_email(email,
                                   admin_email,
                                   subject=self.email_subject,
                                   sender=self.sender,
                                   reply_to=self.reply_to)
                if self.no_emails_to_users:
                    print(email)

    @abstractmethod
    def generate_report_for_admins(self, keep_index: bool=False) -> str:
        """Generate a report for system administrators.

        Returns:
            A table of data as a string.
        """

    @staticmethod
    def create_empty_report(df_empty: pd.DataFrame) -> str:
        heading = "  ".join(df_empty)
        return heading + "\n" + "no entries".center(len(heading))

    def add_report_metadata(self,
                            start_date: datetime,
                            end_date: datetime,
                            dates_only: bool=False) -> str:
        """Add data to the bottom of the report."""
        s = ""
        if not dates_only:
            s += f"   Cluster: {self.cluster}\n" 
            s += f"Partitions: {', '.join(self.partitions)}\n" 
        fmt = "%a %b %d, %Y at %I:%M %p"
        s += f"     Start: {start_date.strftime(fmt)}\n" 
        s += f"       End: {end_date.strftime(fmt)}\n" 
        return s

    def get_admincomment_for_running_jobs(self) -> pd.Series:
        """Query the Prometheus server for the admincomment of
        jobs in a RUNNING state."""
        sys.path.append(self.jobstats_module_path)
        sys.path.append(self.jobstats_config_path)
        from jobstats import Jobstats
        from config import PROM_SERVER
        num_jobs = len(self.df[self.df.state == "RUNNING"])
        print(f"INFO: Querying server for AdminComment on {num_jobs} running jobs ... ",
              end="",
              flush=True)
        start = time()
        adminc = self.df.apply(lambda row:
                               eval(Jobstats(jobid=row["jobid"],
                                             cluster=row["cluster"],
                                             prom_server=PROM_SERVER).report_job_json(False))
                               if row["state"] == "RUNNING"
                               else row["admincomment"], axis="columns")
        print(f"done ({round(time() - start)} seconds).", flush=True)
        return adminc

    def filter_by_nodelist(self, jb: pd.DataFrame) -> pd.DataFrame:
        """If the alert contains a nodelist then filter out the jobs
           that ran on nodes that are not in the nodelist. This function
           is useful when the cluster and partition do not provide
           sufficient control. The approach is to subtract the nodelist
           from the nodes that each job used. If the length of the
           resulting set is zero then the job used only nodes in the
           nodelist."""
        jb["node-tuple"] = jb.apply(lambda row:
                                    get_nodelist(row["admincomment"],
                                                 row["jobid"],
                                                 row["cluster"]),
                                                 axis="columns")
        cols = ["job_nodes", "error_code"]
        jb[cols] = pd.DataFrame(jb["node-tuple"].tolist(),
                                index=jb.index)
        jb = jb[jb["error_code"] == 0]
        self.nodelist = set(self.nodelist)
        jb["num_other_nodes"] = jb["job_nodes"].apply(lambda jns:
                                                      len(jns - self.nodelist))
        jb = jb[jb["num_other_nodes"] == 0]
        cols = ["node-tuple", "job_nodes", "error_code", "num_other_nodes"]
        jb.drop(columns=cols, inplace=True)
        print("INFO: Applied nodelist")
        return jb

    def has_sufficient_time_passed_since_last_email(self, vfile: str) -> bool:
        """Return boolean specifying whether sufficient time has passed."""
        last_sent_email_date = datetime(1970, 1, 1)
        if os.path.isfile(vfile):
            vhist = pd.read_csv(vfile,
                                parse_dates=["Email-Sent"],
                                date_format="mixed",
                                dayfirst=False)
            alert_partitions = ",".join(sorted(set(self.partitions)))
            vhist = vhist[(vhist["Cluster"] == self.cluster) &
                          (vhist["Alert-Partitions"] == alert_partitions)]
            if not vhist.empty:
                last_sent_email_date = vhist["Email-Sent"].max()
        seconds_since_last_email = datetime.now().timestamp() - last_sent_email_date.timestamp()
        seconds_threshold = self.days_between_emails * hpd * sph 
        return seconds_since_last_email >= seconds_threshold

    def get_emails_sent_count(self, user: str, violation: str) -> str:
        """Return the number of emails sent to a user for a given violation in the
           last N days."""
        root_violations = os.path.join(self.vpath, violation)
        if not os.path.exists(root_violations):
            print(f"Warning: {root_violations} not found in get_emails_sent_count()")
        user_violations = f"{root_violations}/{user}.csv"
        if os.path.isfile(user_violations):
            vhist = pd.read_csv(user_violations,
                                parse_dates=["Email-Sent"],
                                date_format="mixed",
                                dayfirst=False)
            alert_partitions = ",".join(sorted(set(self.partitions)))
            vhist = vhist[(vhist["Cluster"] == self.cluster) &
                          (vhist["Alert-Partitions"] == alert_partitions)]
            if not vhist.empty:
                num_emails_sent = vhist["Email-Sent"].unique().size
                dt = datetime.now() - vhist["Email-Sent"].unique().max()
                days_ago_last_email_sent = round(dt.total_seconds() / hpd / sph)
                return f"{num_emails_sent} ({days_ago_last_email_sent})"
        return "0 (-)"

    def format_email_counts(self, counts: pd.Series) -> pd.Series:
        """Return the email sent counts with proper alignment of the two
           different quantities."""
        if counts.empty:
            return counts
        if counts.tolist() == ["0 (-)"] * len(counts):
            return pd.Series(["0"] * len(counts), index=counts.index)
        max_len = max([len(count.split()[1]) for count in counts.tolist()])
        def fix_spacing(item: str):
            num_sent, days_ago = item.split()
            pair = f"{num_sent}{(max_len - len(days_ago)) * ' '} {days_ago}"
            return pair.replace("(-)", "   ")
        return counts.apply(fix_spacing)

    @staticmethod
    def update_violation_log(usr: pd.DataFrame, vfile: str) -> None:
        """Append the new violations to file."""
        usr["Email-Sent"] = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
        if os.path.isfile(vfile):
            curr = pd.read_csv(vfile)
            curr = pd.concat([curr, usr]).drop_duplicates()
            curr.to_csv(vfile, index=False, header=True, encoding="utf-8")
        else:
            usr.to_csv(vfile, index=False, header=True, encoding="utf-8")

    def __len__(self) -> int:
        """Returns the number of rows in the df dataframe."""
        return len(self.df)

    def __str__(self) -> str:
        """Returns the df dataframe as a string."""
        return self.df.to_string()
