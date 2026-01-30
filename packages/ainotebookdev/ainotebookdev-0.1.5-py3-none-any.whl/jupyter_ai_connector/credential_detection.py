"""Local credential detection for the connector."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Iterable

import httpx

MASK_CHAR = "\u2022"
MASK_LENGTH = 32

OLLAMA_BASE_URL_ENV_VARS = ("JUPYTER_AI_OLLAMA_BASE_URL", "OLLAMA_BASE_URL")
OLLAMA_DEFAULT_BASE_URL = "http://localhost:11434"

VERTEX_PROJECT_ENV_VARS = (
    "JUPYTER_AI_VERTEX_PROJECT",
    "GOOGLE_CLOUD_PROJECT",
    "GCP_PROJECT_ID",
    "GCLOUD_PROJECT",
    "PROJECT_ID",
)
VERTEX_LOCATION_ENV_VARS = (
    "JUPYTER_AI_VERTEX_LOCATION",
    "GOOGLE_CLOUD_LOCATION",
    "GOOGLE_CLOUD_REGION",
    "GOOGLE_CLOUD_ZONE",
)
ADC_ENV_VAR = "GOOGLE_APPLICATION_CREDENTIALS"


def _first_env_value(names: Iterable[str]) -> tuple[str | None, str | None]:
    for name in names:
        value = os.environ.get(name)
        if value:
            return value, name
    return None, None


def _last4(value: str | None) -> str | None:
    if not value:
        return None
    return value[-4:]


def build_masked_key(last4: str | None) -> str | None:
    if not last4:
        return None
    return f"{MASK_CHAR * MASK_LENGTH}{last4}"


def detect_api_key_env_vars(names: Iterable[str]) -> dict[str, Any]:
    value, env_var = _first_env_value(names)
    present = env_var is not None
    last4 = _last4(value) if present else None
    return {
        "present": present,
        "source": "env" if present else None,
        "env_var": env_var,
        "last4": last4,
        "masked": build_masked_key(last4),
    }


def resolve_env_api_key(names: Iterable[str]) -> tuple[str | None, str | None]:
    value, env_var = _first_env_value(names)
    if not env_var:
        return None, None
    return value, env_var


def _default_adc_path() -> Path | None:
    if os.name == "nt":
        appdata = os.environ.get("APPDATA")
        if not appdata:
            return None
        return Path(appdata) / "gcloud" / "application_default_credentials.json"
    home = os.environ.get("HOME")
    if not home:
        return None
    return Path(home) / ".config" / "gcloud" / "application_default_credentials.json"


def _load_adc_project(path: str | None) -> str | None:
    if not path:
        return None
    try:
        payload = json.loads(Path(path).read_text())
    except Exception:
        return None
    if not isinstance(payload, dict):
        return None
    project = payload.get("quota_project_id") or payload.get("project_id")
    return project if isinstance(project, str) and project.strip() else None


def detect_vertex_adc() -> tuple[bool, str | None, str | None]:
    env_path = os.environ.get(ADC_ENV_VAR)
    if env_path:
        if Path(env_path).expanduser().exists():
            return True, "env", env_path
        return False, None, None
    default_path = _default_adc_path()
    if default_path and default_path.exists():
        return True, "file", str(default_path)
    return False, None, None


def detect_vertex_credentials(api_key_env_vars: Iterable[str]) -> dict[str, Any]:
    api_detection = detect_api_key_env_vars(api_key_env_vars)
    adc_present, adc_source, adc_path = detect_vertex_adc()
    project, _ = _first_env_value(VERTEX_PROJECT_ENV_VARS)
    if not project and adc_present:
        project = _load_adc_project(adc_path)
    location, _ = _first_env_value(VERTEX_LOCATION_ENV_VARS)
    return {
        "api_key": api_detection,
        "adc": {
            "present": adc_present,
            "source": adc_source,
            "path": adc_path,
        },
        "project": project,
        "location": location,
    }


def _get_ollama_base_url() -> str:
    value, _ = _first_env_value(OLLAMA_BASE_URL_ENV_VARS)
    return value or OLLAMA_DEFAULT_BASE_URL


async def detect_ollama() -> dict[str, Any]:
    base_url = _get_ollama_base_url()
    url = f"{base_url.rstrip('/')}/api/tags"

    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            return {
                "available": True,
                "base_url": base_url,
                "error": None,
            }
    except httpx.ConnectError:
        return {
            "available": False,
            "base_url": base_url,
            "error": "Cannot connect to Ollama server",
        }
    except httpx.HTTPStatusError as exc:
        return {
            "available": False,
            "base_url": base_url,
            "error": f"Ollama returned HTTP {exc.response.status_code}",
        }
    except Exception as exc:
        return {
            "available": False,
            "base_url": base_url,
            "error": str(exc),
        }
