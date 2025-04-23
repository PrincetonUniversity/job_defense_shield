"""Classes to decide work days versus holidays."""

from datetime import datetime
from abc import ABC, abstractmethod
from pandas.tseries.holiday import USFederalHolidayCalendar


class Workday(ABC):

    """Abstract base class for deciding on workdays."""

    @staticmethod
    def is_weekend():
        day_of_week = datetime.now().weekday()
        return day_of_week > 4

    @abstractmethod
    def is_workday(self) -> bool:
        pass


class WorkdayUSA(Workday):

    """Do not send emails on weekends and US federal holidays."""

    def is_workday(self) -> bool:
        """Determine if today is a work day."""
        date_today = datetime.now().strftime("%Y-%m-%d")
        cal = USFederalHolidayCalendar()
        us_holiday = bool(date_today in cal.holidays())
        return (not us_holiday) and (not self.is_weekend())


class WorkdayAlways(Workday):

    """Everyday is a workday."""

    def is_workday(self) -> bool:
        return True


class WorkdayFile(Workday):

    """Do not send emails on weekends and holidays that are specified
       in a custom file (set holidays-file in config.yaml)."""

    def __init__(self, holidays_file):
        self.holidays_file = holidays_file

    def is_workday(self) -> bool:
        try:
            with open(self.holidays_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except FileNotFoundError:
            msg = f"Error: {self.holidays_file} not found."
            print(msg)
            raise
        except IOError:
            print(f"Error: Could not read file at {self.holidays_file}")
            raise
        except Exception as e:
            print(f"Error: Could not read {self.holidays_file} ({e})")
            raise
        else:
            holidays = [line.strip() for line in lines]
            date_today = datetime.now().strftime("%Y-%m-%d")
            return date_today not in holidays and not self.is_weekend()


class WorkdayCustom(Workday):

    """Write custom code for your institution."""

    def is_workday(self) -> bool:
        pass


class WorkdayFactory:

    """The factory pattern is used to dynamically choose the method
       based on the setting in the configuration file."""

    def __init__(self, holidays_file):
        self.holidays_file = holidays_file

    def create_workday(self, method):
        if method == "usa":
            return WorkdayUSA()
        elif method == "always":
            return WorkdayAlways()
        elif method == "file":
            return WorkdayFile(self.holidays_file)
        elif method == "custom":
            return WorkdayCustom()
        else:
            msg = 'Unknown workday. Use either "usa", "always", "file" or "custom".'
            raise ValueError(msg)
