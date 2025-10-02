# import pytz
from zoneinfo import ZoneInfo
from django.conf import settings
from django.utils import timezone

def system_now():
    # tz = pytz.timezone(getattr(settings, "SYSTEM_TIMEZONE", "UTC"))
    tz = ZoneInfo(getattr(settings, "SYSTEM_TIMEZONE", "UTC"))
    return timezone.now().astimezone(tz)

