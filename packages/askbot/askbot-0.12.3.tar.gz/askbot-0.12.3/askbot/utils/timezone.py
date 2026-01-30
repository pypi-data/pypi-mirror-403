import zoneinfo
from django.utils import timezone
from django.conf import settings as django_settings

def make_aware(value, tz=None):
    """
    Makes a naive datetime.datetime in a given time zone aware.

    If conversion is ambigous regarding the daytime savings,
    assume that the daytime savings is on, b/c we
    don't care about such exactitude here
    """
    if timezone.is_aware(value):
        raise ValueError(
            "make_aware expects a naive datetime, got %s" % value)

    if tz is None:
        tz_code = django_settings.TIME_ZONE
        tz = zoneinfo.ZoneInfo(tz_code)

    return value.replace(tzinfo=tz)
