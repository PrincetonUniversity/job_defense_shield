import re
import glob
import smtplib
from datetime import datetime
from datetime import timedelta
import pandas as pd
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

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

def gpus_per_job(tres: str) -> int:
    """Return the number of allocated GPUs."""
    gpus = re.findall(r"gres/gpu=\d+", tres)
    return int(gpus[0].replace("gres/gpu=", "")) if gpus else 0

def add_dividers(df_str: str,
                 title: str="",
                 pre: str="\n\n\n",
                 units_row: bool=False) -> str:
    rows = df_str.split("\n")
    width = max([len(row) for row in rows] + [len(title)])
    heading = title.center(width)
    divider = "-" * width
    if title and not units_row:
        rows.insert(0, heading)
        rows.insert(1, divider)
        rows.insert(3, divider)
    elif title and units_row:
        rows.insert(0, heading)
        rows.insert(1, divider)
        rows.insert(4, divider)
    else:
        rows.insert(0, divider)
        rows.insert(2, divider)
    rows.append(divider)
    return pre + "\n".join(rows) + "\n"

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

def send_email(email_body, addressee, subject, sender, reply_to):
    """Send an email using simple HTML."""
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
    s = smtplib.SMTP('localhost')
    s.sendmail(sender, addressee, msg.as_string())
    s.quit()
    return None

def send_email_enhanced(email_body, addressee, subject, sender, reply_to):
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
    with smtplib.SMTP('localhost') as s:
        s.send_message(msg)
