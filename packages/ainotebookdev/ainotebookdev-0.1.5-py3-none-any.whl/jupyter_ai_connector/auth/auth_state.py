"""Auth state sentinel persistence.

Stores non-secret auth state (storage preference, auto-connect, last user) to avoid
touching the OS keychain until the user opts in.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

STORAGE_PREFERENCE_KEY = "storage_preference"
AUTO_CONNECT_KEY = "auto_connect"
LAST_USER_KEY = "last_user"
LAST_LOGIN_AT_KEY = "last_login_at"

VALID_STORAGE_PREFERENCES: set[str] = {"keyring", "file", "memory"}


def normalize_storage_preference(value: str | None) -> str | None:
    if value in VALID_STORAGE_PREFERENCES:
        return value
    return None


def _coerce_auto_connect(value: Any, storage_preference: str | None) -> bool:
    if isinstance(value, bool):
        return value
    if storage_preference in ("file", "keyring"):
        return True
    return False


def _sanitize_last_user(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    allowed = ("email", "name", "sub", "idp", "picture")
    sanitized = {key: value.get(key) for key in allowed if value.get(key) is not None}
    return sanitized or None


def get_auth_state_path(settings: dict | None) -> Path | None:
    if not settings:
        return None
    connector_settings = settings.get("jupyter_ai_connector", {})
    raw = connector_settings.get("token_store_preference_path") or ""
    if not raw:
        return None
    return Path(raw).expanduser()


def load_auth_state(settings: dict | None) -> dict[str, Any]:
    path = get_auth_state_path(settings)
    if not path or not path.exists():
        return {
            STORAGE_PREFERENCE_KEY: None,
            AUTO_CONNECT_KEY: False,
            LAST_USER_KEY: None,
            LAST_LOGIN_AT_KEY: None,
        }
    try:
        raw = path.read_text(encoding="utf-8")
        payload = json.loads(raw)
    except Exception as exc:
        logger.warning(f"Failed to read auth state: {exc}")
        payload = {}

    if not isinstance(payload, dict):
        payload = {}

    preference = normalize_storage_preference(
        payload.get(STORAGE_PREFERENCE_KEY) or payload.get("preference")
    )
    auto_connect = _coerce_auto_connect(payload.get(AUTO_CONNECT_KEY), preference)
    last_user = _sanitize_last_user(payload.get(LAST_USER_KEY))
    last_login_at = payload.get(LAST_LOGIN_AT_KEY)
    if not isinstance(last_login_at, (int, float, str)):
        last_login_at = None

    return {
        STORAGE_PREFERENCE_KEY: preference,
        AUTO_CONNECT_KEY: auto_connect,
        LAST_USER_KEY: last_user,
        LAST_LOGIN_AT_KEY: last_login_at,
    }


def update_auth_state(settings: dict | None, updates: dict[str, Any]) -> dict[str, Any]:
    path = get_auth_state_path(settings)
    if not path:
        return {}
    current = load_auth_state(settings)
    current_preference = current.get(STORAGE_PREFERENCE_KEY)
    next_state = dict(current)
    preference_changed = False

    if STORAGE_PREFERENCE_KEY in updates:
        next_state[STORAGE_PREFERENCE_KEY] = normalize_storage_preference(
            updates.get(STORAGE_PREFERENCE_KEY)
        )
        preference_changed = next_state[STORAGE_PREFERENCE_KEY] != current_preference

    if AUTO_CONNECT_KEY in updates:
        next_state[AUTO_CONNECT_KEY] = _coerce_auto_connect(
            updates.get(AUTO_CONNECT_KEY),
            next_state.get(STORAGE_PREFERENCE_KEY),
        )
    else:
        auto_connect_value = next_state.get(AUTO_CONNECT_KEY)
        if preference_changed:
            auto_connect_value = None
        next_state[AUTO_CONNECT_KEY] = _coerce_auto_connect(
            auto_connect_value,
            next_state.get(STORAGE_PREFERENCE_KEY),
        )

    if LAST_USER_KEY in updates:
        next_state[LAST_USER_KEY] = _sanitize_last_user(updates.get(LAST_USER_KEY))

    if LAST_LOGIN_AT_KEY in updates:
        value = updates.get(LAST_LOGIN_AT_KEY)
        next_state[LAST_LOGIN_AT_KEY] = value if isinstance(value, (int, float, str)) else None

    _write_auth_state(path, next_state)
    return next_state


def _write_auth_state(path: Path, state: dict[str, Any]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(state)
        tmp_path = path.with_suffix(path.suffix + ".tmp")
        tmp_path.write_text(payload, encoding="utf-8")
        os.replace(tmp_path, path)
        os.chmod(path, 0o600)
    except Exception as exc:
        logger.warning(f"Failed to persist auth state: {exc}")
