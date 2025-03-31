"""Abstract and concrete classes to get the raw job data."""

import os
import sys
import subprocess
from time import time
from datetime import datetime
from datetime import timedelta
from abc import ABC, abstractmethod
import pandas as pd


class RawJobData(ABC):

    """Abstract base class to get the raw job data."""

    @abstractmethod
    def get_job_data(self):
        pass


class SlurmSacct(RawJobData):

    """Call sacct to get the raw job data from the Slurm database."""

    def __init__(self, days, start, end, fields, clusters, partitions):
        self.days = days
        self.start_datetime = start
        self.end_datetime = end
        self.fields = fields
        self.clusters = clusters
        self.partitions = partitions

    def verify_datetime(self, dt):
        ymd = dt.strftime('%Y-%m-%d')
        hms = dt.strftime('%H:%M:%S')
        return f"{ymd}T{hms}"

    def get_job_data(self) -> pd.DataFrame:
        """Return the sacct data in a pandas dataframe."""
        # convert slurm timestamps to seconds
        os.environ["SLURM_TIME_FORMAT"] = "%s"
        start = datetime.now() - timedelta(days=self.days)
        end = datetime.now()
        self.start_datetime = self.verify_datetime(start)
        self.end_datetime   = self.verify_datetime(end)
        cmd = f"sacct -a -X -P -n -S {self.start_datetime} -E {self.end_datetime} "
        cmd += f"-M {self.clusters} -o {self.fields}"
        if self.partitions:
            cmd += f" -r {self.partitions}"
        print(f"INFO: Calling sacct ... ", end="", flush=True)
        start = time()
        try:
            result = subprocess.run(cmd,
                                    stdout=subprocess.PIPE,
                                    encoding="utf8",
                                    check=True,
                                    text=True,
                                    shell=True)
            result.check_returncode()
        except subprocess.CalledProcessError as error:
            msg = f"Error running sacct.\n{error.stderr}"
            raise RuntimeError(msg) from error
        print(f"done ({round(time() - start)} seconds).", flush=True)
        rows = result.stdout.split('\n')
        if rows != [] and rows[-1] == "":
            rows = rows[:-1]
        cols = self.fields.split(",")
        raw = pd.DataFrame([row.split("|")[:len(cols)] for row in rows])
        if raw.empty:
            msg = ("\nCall to sacct resulted in no job data. If this is surprising\n"
                   "then check the spelling of your cluster and/or partition names\n"
                   "in config.yml and -M <clusters> -r <partition>. Run again using\n"
                   "the only option --usage-overview to see what is available.")
            print(msg)
            sys.exit()
        raw.columns = cols
        return raw
