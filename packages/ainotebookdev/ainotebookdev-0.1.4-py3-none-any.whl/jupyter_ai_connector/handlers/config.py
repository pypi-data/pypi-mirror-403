"""Config proxy handler."""

import json
import logging
import os
import time
from typing import Any

from .base import BaseProxyHandler
from ..credential_detection import (
    build_masked_key,
    detect_api_key_env_vars,
    detect_ollama,
    detect_vertex_credentials,
    resolve_env_api_key,
)

logger = logging.getLogger(__name__)

CATALOG_CACHE_TTL_SECONDS = float(os.environ.get("JAI_PROVIDER_CATALOG_TTL_SECONDS", "30"))
PRESET_DETECTION_PREFIX = "openai_compatible_preset:"
PREFERRED_PROFILE_KEY = "preferred_provider_profile"
PROFILE_PROVIDER_PREFIX = "openai_compatible"

_catalog_cache: dict[str, Any] = {
    "expires_at": 0.0,
    "payload": None,
}


def _normalize_env_vars(value: Any) -> tuple[str, ...]:
    if isinstance(value, (list, tuple)):
        return tuple(str(item) for item in value if isinstance(item, str) and item.strip())
    return ()


def _normalize_profile_id(profile_id: str) -> str:
    return profile_id.strip().lower()


def _profile_provider_key(profile_id: str) -> str:
    return f"{PROFILE_PROVIDER_PREFIX}:{_normalize_profile_id(profile_id)}"


def _get_profile(config: dict[str, Any], profile_id: str) -> dict[str, Any] | None:
    profiles = config.get("custom_provider_profiles")
    if not isinstance(profiles, list):
        return None
    normalized = _normalize_profile_id(profile_id)
    for entry in profiles:
        if not isinstance(entry, dict):
            continue
        candidate = entry.get("id")
        if isinstance(candidate, str) and _normalize_profile_id(candidate) == normalized:
            return entry
    return None


def _profile_requires_api_key(profile: dict[str, Any] | None) -> bool:
    if not profile:
        return False
    auth = profile.get("auth")
    if not isinstance(auth, dict):
        return False
    return auth.get("type") == "api_key"


def _has_valid_detection(detection: dict[str, Any]) -> bool:
    api_key = detection.get("api_key", {})
    if isinstance(api_key, dict) and api_key.get("present"):
        return True
    adc = detection.get("adc", {})
    if isinstance(adc, dict) and adc.get("present"):
        return True
    if detection.get("available"):
        return True
    return False


def _compute_needs_setup(
    user_config: dict[str, Any] | None,
    byok: dict[str, Any] | None,
    detected: dict[str, Any],
) -> bool:
    config = user_config.get("config") if isinstance(user_config, dict) else {}
    config = config if isinstance(config, dict) else {}
    preferred_provider = config.get("preferred_provider")

    if not preferred_provider:
        return True

    if preferred_provider == PROFILE_PROVIDER_PREFIX:
        profile_id = config.get(PREFERRED_PROFILE_KEY)
        if isinstance(profile_id, str) and profile_id.strip():
            profile = _get_profile(config, profile_id)
            if not profile:
                return True
            if _profile_requires_api_key(profile):
                provider_key = _profile_provider_key(profile_id)
                entry = byok.get(provider_key, {}) if isinstance(byok, dict) else {}
                return not bool(entry.get("present"))
            return False
        return True

    provider_byok = byok.get(preferred_provider, {}) if isinstance(byok, dict) else {}
    if provider_byok.get("present"):
        return False

    provider_detected = detected.get(preferred_provider, {})
    if isinstance(provider_detected, dict) and _has_valid_detection(provider_detected):
        return False

    return True


def _apply_masked_byok(byok: dict[str, Any]) -> None:
    for entry in byok.values():
        if not isinstance(entry, dict):
            continue
        if entry.get("masked"):
            continue
        last4 = entry.get("last4")
        if isinstance(last4, str) and last4.strip():
            entry["masked"] = build_masked_key(last4)


class ConfigProxyHandler(BaseProxyHandler):
    """Proxy config requests to the orchestrator."""

    def _build_upstream_url(self, path: str) -> str:
        url = f"{self.orchestrator_url}/v1/config/{path}"
        query = self.request.query
        if query:
            url = f"{url}?{query}"
        return url

    async def _get_provider_catalog(self) -> dict[str, Any]:
        now = time.monotonic()
        cached = _catalog_cache.get("payload")
        expires_at = _catalog_cache.get("expires_at", 0.0)
        if cached and isinstance(cached, dict) and expires_at > now:
            return cached
        try:
            response = await self.http_client.get(
                self._build_upstream_url("providers/tiered"),
                headers=await self.get_upstream_headers(),
            )
            response.raise_for_status()
            payload = response.json()
            if isinstance(payload, dict):
                _catalog_cache["payload"] = payload
                _catalog_cache["expires_at"] = now + CATALOG_CACHE_TTL_SECONDS
                return payload
        except Exception as exc:
            logger.warning("Failed to load provider catalog: %s", exc)
        return cached if isinstance(cached, dict) else {}

    async def _build_local_detection(self, catalog: dict[str, Any]) -> dict[str, Any]:
        detected: dict[str, Any] = {}
        primary = catalog.get("primary") if isinstance(catalog, dict) else None
        if isinstance(primary, list):
            for entry in primary:
                if not isinstance(entry, dict):
                    continue
                provider_id = entry.get("id")
                if not isinstance(provider_id, str) or not provider_id:
                    continue
                env_vars = _normalize_env_vars(entry.get("api_key_env_vars"))
                if provider_id == "vertex":
                    detected["vertex"] = detect_vertex_credentials(env_vars)
                    continue
                if env_vars:
                    detected[provider_id] = {"api_key": detect_api_key_env_vars(env_vars)}

        presets_root = catalog.get("openai_compatible") if isinstance(catalog, dict) else None
        if isinstance(presets_root, dict):
            presets = []
            primary_presets = presets_root.get("primary")
            secondary_presets = presets_root.get("secondary")
            if isinstance(primary_presets, list):
                presets.extend(primary_presets)
            if isinstance(secondary_presets, list):
                presets.extend(secondary_presets)
            for preset in presets:
                if not isinstance(preset, dict):
                    continue
                preset_id = preset.get("id")
                if not isinstance(preset_id, str) or not preset_id:
                    continue
                env_vars = _normalize_env_vars(preset.get("api_key_env_vars"))
                if not env_vars:
                    continue
                key = f"{PRESET_DETECTION_PREFIX}{preset_id}"
                detected[key] = {"api_key": detect_api_key_env_vars(env_vars)}

        local = catalog.get("local") if isinstance(catalog, dict) else None
        if isinstance(local, list):
            for entry in local:
                if not isinstance(entry, dict):
                    continue
                provider_id = entry.get("id")
                if provider_id == "ollama":
                    detected["ollama"] = await detect_ollama()
                    break

        return detected

    async def _get_user_config(self) -> None:
        response = await self.http_client.get(
            self._build_upstream_url("user"),
            headers=await self.get_upstream_headers(),
        )

        self.set_status(response.status_code)
        if response.status_code >= 400:
            self.write(response.content)
            self.finish()
            return

        try:
            payload = response.json()
        except Exception:
            self.write(response.content)
            self.finish()
            return

        if not isinstance(payload, dict):
            self.write(response.content)
            self.finish()
            return

        catalog = await self._get_provider_catalog()
        detected = await self._build_local_detection(catalog)
        byok = payload.get("byok")
        if isinstance(byok, dict):
            _apply_masked_byok(byok)
        payload["detected"] = detected
        payload["needs_setup"] = _compute_needs_setup(payload.get("user_config"), byok, detected)

        self.set_header("Content-Type", "application/json")
        self.write(json.dumps(payload))
        self.finish()

    def _get_provider_env_vars(self, catalog: dict[str, Any], provider_id: str) -> tuple[str, ...]:
        primary = catalog.get("primary") if isinstance(catalog, dict) else None
        if isinstance(primary, list):
            for entry in primary:
                if not isinstance(entry, dict):
                    continue
                if entry.get("id") != provider_id:
                    continue
                return _normalize_env_vars(entry.get("api_key_env_vars"))
        return ()

    def _get_preset_env_vars(self, catalog: dict[str, Any], preset_id: str) -> tuple[str, ...]:
        presets_root = catalog.get("openai_compatible") if isinstance(catalog, dict) else None
        if not isinstance(presets_root, dict):
            return ()
        for group in ("primary", "secondary"):
            presets = presets_root.get(group)
            if not isinstance(presets, list):
                continue
            for preset in presets:
                if not isinstance(preset, dict):
                    continue
                if preset.get("id") != preset_id:
                    continue
                return _normalize_env_vars(preset.get("api_key_env_vars"))
        return ()

    def _read_json_body(self) -> dict[str, Any]:
        if not self.request.body:
            return {}
        try:
            payload = json.loads(self.request.body)
        except Exception:
            return {}
        return payload if isinstance(payload, dict) else {}

    async def get(self, path: str):
        """Get configuration.

        GET /ai/config/*
        """
        if not await self.ensure_upstream_auth():
            return
        if path == "user":
            await self._get_user_config()
            return
        try:
            response = await self.http_client.get(
                self._build_upstream_url(path),
                headers=await self.get_upstream_headers(),
            )

            self.set_status(response.status_code)
            self.write(response.content)
            self.finish()

        except Exception as e:
            logger.exception("Failed to get config")
            await self.handle_error(500, str(e), code="PROXY_ERROR")

    async def put(self, path: str):
        """Update configuration.

        PUT /ai/config/*
        """
        if not await self.ensure_upstream_auth():
            return
        try:
            body = self.request.body
            if len(body) > self.max_payload_size:
                await self.handle_error(413, "Payload too large", code="PAYLOAD_TOO_LARGE")
                return

            response = await self.http_client.put(
                self._build_upstream_url(path),
                content=body,
                headers=await self.get_upstream_headers(),
            )

            self.set_status(response.status_code)
            self.write(response.content)
            self.finish()

        except Exception as e:
            logger.exception("Failed to update config")
            await self.handle_error(500, str(e), code="PROXY_ERROR")

    async def post(self, path: str):
        """Create or confirm configuration.

        POST /ai/config/*
        """
        if not await self.ensure_upstream_auth():
            return
        if path.startswith("confirm-detected/"):
            provider_id = path.split("/", 1)[1]
            await self._confirm_detected_provider(provider_id)
            return
        if path.startswith("openai_compatible/presets/") and path.endswith("/confirm-detected"):
            parts = path.split("/")
            if len(parts) >= 4:
                preset_id = parts[2]
                await self._confirm_detected_preset(preset_id)
                return
        try:
            body = self.request.body
            if len(body) > self.max_payload_size:
                await self.handle_error(413, "Payload too large", code="PAYLOAD_TOO_LARGE")
                return

            response = await self.http_client.post(
                self._build_upstream_url(path),
                content=body,
                headers=await self.get_upstream_headers(),
            )

            self.set_status(response.status_code)
            self.write(response.content)
            self.finish()

        except Exception as e:
            logger.exception("Failed to post config")
            await self.handle_error(500, str(e), code="PROXY_ERROR")

    async def _confirm_detected_provider(self, provider_id: str) -> None:
        body = self._read_json_body()
        catalog = await self._get_provider_catalog()
        env_vars = self._get_provider_env_vars(catalog, provider_id)
        api_key = None
        auth_method = body.get("auth_method")
        if provider_id != "vertex" or auth_method != "adc":
            api_key, _ = resolve_env_api_key(env_vars)
        if api_key:
            body["api_key"] = api_key

        payload = json.dumps(body or {})
        response = await self.http_client.post(
            self._build_upstream_url(f"confirm-detected/{provider_id}"),
            content=payload,
            headers=await self.get_upstream_headers(),
        )
        self.set_status(response.status_code)
        self.write(response.content)
        self.finish()

    async def _confirm_detected_preset(self, preset_id: str) -> None:
        body = self._read_json_body()
        catalog = await self._get_provider_catalog()
        env_vars = self._get_preset_env_vars(catalog, preset_id)
        api_key, _ = resolve_env_api_key(env_vars)
        if api_key:
            body["api_key"] = api_key

        payload = json.dumps(body or {})
        response = await self.http_client.post(
            self._build_upstream_url(f"openai_compatible/presets/{preset_id}/confirm-detected"),
            content=payload,
            headers=await self.get_upstream_headers(),
        )
        self.set_status(response.status_code)
        self.write(response.content)
        self.finish()

    async def delete(self, path: str):
        """Delete configuration.

        DELETE /ai/config/*
        """
        if not await self.ensure_upstream_auth():
            return
        try:
            response = await self.http_client.delete(
                self._build_upstream_url(path),
                headers=await self.get_upstream_headers(),
            )

            self.set_status(response.status_code)
            self.write(response.content)
            self.finish()

        except Exception as e:
            logger.exception("Failed to delete config")
            await self.handle_error(500, str(e), code="PROXY_ERROR")
