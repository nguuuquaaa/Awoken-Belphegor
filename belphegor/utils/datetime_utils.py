from datetime import datetime, timedelta
from pytz import timezone
import time

#=============================================================================================================================#

UTC = timezone("UTC")
JST = timezone("Asia/Tokyo")
PDT = timezone("US/Pacific")

def now_time(tzinfo=UTC) -> datetime:
    return datetime.now(tzinfo)

def as_jp_time(dt: datetime) -> str:
    return dt.astimezone(JST).strftime("%a, %Y-%m-%d at %I:%M:%S %p, UTC%z (Tokyo/Japan)")

def as_pdt_time(dt: datetime) -> str:
    return dt.astimezone(PDT).strftime("%a, %Y-%m-%d at %I:%M:%S %p, UTC%z (PDT)")

def format_datetime(dt: datetime) -> str:
    return dt.strftime("%a, %Y-%m-%d at %I:%M:%S %p, UTC%z")

def human_readable_time(seconds: int|float) -> str:
    """
    Return human-barely-readable time, i.e 1d02h03m04s
    """
    seconds = int(seconds)
    ts = ""
    d = seconds // 86400

    # days
    if d > 0:
        ts = f"{d}d"

    #hours
    h = (seconds % 86400) // 3600
    if h > 0 or (h == 0 and ts):
        ts = f"{ts}{h:02d}h"

    # minutes
    m = (seconds % 3600) // 60
    if m > 0 or (m == 0 and ts):
        ts = f"{ts}{m:02d}m"

    # seconds
    s = seconds % 60
    ts = f"{ts}{s:02d}s"
    if seconds == 0:
        ts = "0s"
    else:
        ts = ts.lstrip("0")

    return ts

#==================================================================================================================================================

class Timer:
    def __init__(self, interval: int|float = 10):
        self.start = time.monotonic()
        self.previous = self.start
        self.interval = interval

    def check(self) -> int|None:
        """Return time passed in seconds every [interval] seconds."""
        current = time.monotonic()
        if current - self.previous > self.interval:
            self.previous = current
            passed = int(current - self.start)
            return passed
        else:
            return None

    def check_h(self) -> str|None:
        """Return time passed in human readable format every [interval] seconds."""
        current = time.monotonic()
        if current - self.previous > self.interval:
            self.previous = current
            passed = int(current - self.start)
            return human_readable_time(passed)
        else:
            return None