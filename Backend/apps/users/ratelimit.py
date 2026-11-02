import time
from datetime import timedelta

from django.db.models import F
from django.utils import timezone

from apps.users.models import RateWindow


def check_window(identifier, scope, limit, window_seconds):
    """Count one hit in the current fixed window and return whether it is within the limit."""
    now = timezone.now()
    RateWindow.objects.filter(expires_at__lt=now).delete()
    epoch = int(time.time())
    key = f"{scope}:{identifier}:{epoch - epoch % window_seconds}"
    RateWindow.objects.get_or_create(
        key=key, defaults={"expires_at": now + timedelta(seconds=window_seconds + 1)}
    )
    RateWindow.objects.filter(key=key).update(count=F("count") + 1)
    return RateWindow.objects.get(key=key).count <= limit
