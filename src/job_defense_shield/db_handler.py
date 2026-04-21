try:
    import MySQLdb
except ImportError:
    MySQLdb = None

try:
    import sqlalchemy
except ImportError:
    sqlalchemy = None

import sys
from datetime import datetime
from typing import Dict
from typing import Any
import configparser
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy import engine_from_config
from sqlalchemy.engine import URL


class ShieldDBHandler:

    """This class allows for summary statistics to be stored in an external
       MySQL/MariaDB database."""

    def __init__(self,
                 conn_params: Dict[str, Any],
                 clusters: str,
                 start_date: datetime,
                 verbose: bool) -> None:
        self.conn_params = conn_params
        self.external_db_enabled = conn_params.get("enabled", False)
        self.external_conn = None
        self.start_date = start_date
        self.clusters = ", ".join([f"'{cluster}'" for cluster in clusters.split(",")])
        self.verbose = verbose
        self.stats = None


    def get_external_connection(self) -> None:
        """Get connection to external MySQL/MariaDB database."""
        if MySQLdb is None or sqlalchemy is None:
            msg = ("MySQLdb or sqlalchemy module not available. Install "
                   "mysqlclient and sqlalchemy to use the external database "
                   "functionality.")
            raise ImportError(msg)

        if not self.external_db_enabled:
            msg = "Did not try to make DB connection since not enabled in config.py."
            print(msg)
            return None
 
        if self.external_conn is None:
            msg = "INFO: Connecting to external database for summary statistics"
            print(msg)
            try:
                if self.conn_params.get("config_file"):
                    cfg = configparser.ConfigParser()
                    cfg.read(self.conn_params["config_file"])
                    settings = dict(cfg.items("client"))
                    if "database" in self.conn_params:
                        db = self.conn_params["database"]
                        url = URL.create("mysql+mysqldb",
                                         username=settings["user"],
                                         password=settings["password"],
                                         host=settings["host"],
                                         database=db)
                    else:
                        url = URL.create("mysql+mysqldb",
                                         username=settings["user"],
                                         password=settings["password"],
                                         host=settings["host"],
                                         database=settings["database"])
                    if self.verbose:
                        msg = f"INFO: Config file connection URL: {url}"
                        print(msg)
                    self.external_conn = engine_from_config({"url": url}, prefix='')
                else:
                    user   = self.conn_params["user"]
                    passwd = self.conn_params["password"]
                    host   = self.conn_params["host"]
                    port   = self.conn_params.get("port", 3306)
                    db     = self.conn_params.get("database", "jobstats")
                    cnt = f"mysql+mysqldb://{user}:{passwd}@{host}:{port}/{db}"
                    if self.verbose:
                        msg = f"INFO: Connection URL: {cnt}"
                        print(msg)
                    self.external_conn = create_engine(cnt)
            except Exception as e:
                msg = f"ERROR: Could not connect to database using sqlalchemy: {e}"
                print(msg)
                sys.exit(1)


    def get_summary_stats(self) -> pd.DataFrame:
        """Return a pandas DataFrame of the summary statistics from external
           database."""
        cols = "jobid,cluster,admin_comment"
        if not self.external_db_enabled or self.external_conn is None:
            print("WARNING: Returning empty dataframe since no DB connection")
            return pd.DataFrame(columns=cols.split(","))
        fmt = "%Y-%m-%d %H:%M:%S"
        start = self.start_date.strftime(fmt)
        query = f"SELECT {cols} FROM job_summary WHERE created_at >= '{start}'"
        if self.clusters != "'all'":
            query += f" AND cluster IN ({self.clusters})"
        if self.verbose:
            print(f"INFO: Database query: {query}")
        try:
            self.stats = pd.read_sql(query, self.external_conn)
        except Exception as e:
            msg = f"ERROR: Failed to retrieve jobstats from external database: {e}"
            print(msg, file=sys.stderr)
            sys.exit(1)
        else:
            return self.stats
        finally:
            self.external_conn.dispose()
