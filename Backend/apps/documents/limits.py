from rest_framework import status
from rest_framework.exceptions import APIException

from apps.documents.constants import AI_LIMITS, ASK_FULL, ASK_TOO_MANY, UPLOAD_FULL, UPLOAD_TOO_MANY
from apps.users.ratelimit import check_window
from apps.users.views import client_ip


class TooMany(APIException):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS


MESSAGES = {"ask": (ASK_TOO_MANY, ASK_FULL), "upload": (UPLOAD_TOO_MANY, UPLOAD_FULL)}


def spend(kind, request):
    """Count one use of Gemini by this person, from this address, or raise a 429 if a share is used up."""
    too_many, full = MESSAGES[kind]
    checks = [
        (scope, identifier)
        for scope, identifier in (
            (f"{kind}_user_hour", request.user.pk),
            (f"{kind}_user_day", request.user.pk),
            (f"{kind}_ip_day", client_ip(request)),
        )
        if scope in AI_LIMITS
    ]
    for scope, identifier in checks:
        if not check_window(identifier, scope, *AI_LIMITS[scope]):
            raise TooMany(too_many)
    # Checked last, so one person being turned away doesn't use up the site's share.
    if not check_window("all", f"{kind}_all_day", *AI_LIMITS[f"{kind}_all_day"]):
        raise TooMany(full)
