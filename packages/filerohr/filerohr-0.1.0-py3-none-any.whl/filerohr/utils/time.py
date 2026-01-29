import datetime
import zoneinfo


def get_zoneinfo(tz: str | None = None):
    if tz:
        return zoneinfo.ZoneInfo(tz)
    else:
        from filerohr.config import TZ

        return zoneinfo.ZoneInfo(TZ)


def as_timezone(dt: datetime.datetime, *, tz: str | None = None):
    return dt.astimezone(get_zoneinfo(tz))


def now():
    return datetime.datetime.now(get_zoneinfo())
