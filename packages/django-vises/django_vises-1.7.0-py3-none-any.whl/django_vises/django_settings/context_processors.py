from typing import Any

from django.conf import settings


def env_vars(request) -> dict[str, Any]:
    return {"EV": settings.EV}
