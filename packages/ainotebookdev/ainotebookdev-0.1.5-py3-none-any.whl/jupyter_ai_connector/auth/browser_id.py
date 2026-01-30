"""Stable browser identifier helpers.

Provides a long-lived browser-scoped ID used to key Auth0 tokens independently
of Jupyter's ephemeral anonymous usernames.
"""

from __future__ import annotations

import secrets
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from jupyter_server.base.handlers import APIHandler


COOKIE_NAME = "jai_browser_id"
COOKIE_MAX_AGE_DAYS = 365


def _is_secure(handler: "APIHandler") -> bool:
    proto = handler.request.headers.get("X-Forwarded-Proto", handler.request.protocol)
    if proto and "," in proto:
        proto = proto.split(",", 1)[0].strip()
    return proto == "https"


def _cookie_path(handler: "APIHandler") -> str:
    base_url = handler.settings.get("base_url", "/") or "/"
    if not base_url.startswith("/"):
        base_url = f"/{base_url}"
    return base_url


def _generate_browser_id() -> str:
    # 32 url-safe chars ~ 192 bits of entropy
    return secrets.token_urlsafe(24)


def get_browser_id(handler: "APIHandler") -> str | None:
    try:
        value = handler.get_cookie(COOKIE_NAME)
    except Exception:
        return None
    if not value or not isinstance(value, str):
        return None
    return value


def get_or_set_browser_id(handler: "APIHandler") -> str:
    value = get_browser_id(handler)
    if value:
        return value
    value = _generate_browser_id()
    handler.set_cookie(
        COOKIE_NAME,
        value,
        httponly=True,
        samesite="lax",
        secure=_is_secure(handler),
        expires_days=COOKIE_MAX_AGE_DAYS,
        path=_cookie_path(handler),
    )
    return value


def get_token_user_ids(handler: "APIHandler") -> list[str]:
    """Return token lookup keys in priority order.

    Primary key uses the stable browser ID, with a legacy fallback to
    Jupyter's current_user.username for backwards compatibility.
    """
    ids: list[str] = []
    browser_id = get_or_set_browser_id(handler)
    if browser_id:
        ids.append(f"browser:{browser_id}")
    try:
        legacy = handler.current_user.username if handler.current_user else "anonymous"
    except Exception:
        legacy = "anonymous"
    if legacy and legacy not in ids:
        ids.append(legacy)
    return ids
