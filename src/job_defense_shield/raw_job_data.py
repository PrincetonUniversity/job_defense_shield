"""Abstract and concrete classes to get the raw job data."""

import os
import sys
import subprocess
from time import time
from datetime import datetime
from abc import ABC, abstractmethod
from typing import List
import pandas as pd


class RawJobData(ABC):

    """Abstract base class to get the raw job data."""

    @abstractmethod
    def get_job_data(self):
        pass


class SlurmSacct(RawJobData):

    """Call sacct to get the raw job data from the Slurm database."""

    def __init__(self,
                 start: datetime,
                 end: datetime,
                 fields: List[str],
                 clusters: str,
                 partitions: str) -> None:
        self.start_datetime = start
        self.end_datetime = end
        self.fields = ",".join(fields)
        self.clusters = clusters
        self.partitions = partitions

    @staticmethod
    def datetime_to_sacct(dt: datetime) -> str:
        """Convert a Python datetime to sacct format."""
        ymd = dt.strftime('%Y-%m-%d')
        hms = dt.strftime('%H:%M:%S')
        return f"{ymd}T{hms}"

    def get_job_data(self) -> pd.DataFrame:
        """Return the sacct data in a pandas dataframe."""
        # convert slurm timestamps to seconds
        os.environ["SLURM_TIME_FORMAT"] = "%s"
        sacct_start = self.datetime_to_sacct(self.start_datetime)
        sacct_end   = self.datetime_to_sacct(self.end_datetime)
        cmd = f"sacct -a -X -P -n -S {sacct_start} -E {sacct_end} "
        cmd += f"-M {self.clusters} -o {self.fields}"
        if self.partitions:
            cmd += f" -r {self.partitions}"
        print("INFO: Calling sacct ... ", end="", flush=True)
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
                   "in config.yml and -M <clusters> -r <partition>. Try running again\n"
                   "using the only option --usage-overview to see what is available.")
            print(msg)
            sys.exit()
        raw.columns = cols
        return raw
