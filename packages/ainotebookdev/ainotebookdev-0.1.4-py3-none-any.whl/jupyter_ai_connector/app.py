"""
Jupyter AI Connector Extension Application

This extension provides a same-origin proxy for the Jupyter AI SaaS Orchestrator.
It handles authentication mapping, endpoint proxying, and SSE streaming.
"""

from jupyter_server.extension.application import ExtensionApp
from traitlets import Unicode, Int, Float, Bool, Dict, observe
from jupyter_core.paths import jupyter_config_dir
import json
import os

from .handlers import setup_handlers

# Production SaaS defaults - baked in for easy distribution
DEFAULT_ORCHESTRATOR_URL = "https://api.ainotebook.dev"
DEFAULT_AUTH0_DOMAIN = "auth.ainotebook.dev"
DEFAULT_AUTH0_CLIENT_ID = "5oofBCIPUyxiSYWqtp0lvLLPbz7Ku4mh"
DEFAULT_AUTH0_AUDIENCE = "https://api.ainotebook.dev"


class JupyterAIConnectorExtension(ExtensionApp):
    """Jupyter AI Connector Server Extension.

    Configuration can be set via:
    - jupyter_server_config.py (traitlets)
    - Environment variables (override defaults)

    For SaaS users: No configuration needed - just install and sign in.
    For self-hosted: Set orchestrator_url to your deployment.
    """

    name = "jupyter_ai_connector"
    description = "Same-origin proxy for Jupyter AI SaaS Orchestrator"

    # Orchestrator configuration
    orchestrator_url = Unicode(
        config=True,
        help="URL of the Jupyter AI SaaS Orchestrator. "
        "Set via Jupyter config (e.g., jupyter_server_config.py) for self-hosted deployments.",
    )

    @observe("orchestrator_url")
    def _observe_orchestrator_url(self, change):
        """Log when orchestrator URL changes."""
        self.log.info(f"Orchestrator URL set to: {change['new']}")

    def _orchestrator_url_default(self):
        """Default to production SaaS."""
        return DEFAULT_ORCHESTRATOR_URL

    orchestrator_token = Unicode(
        config=True,
        help="Service token for authenticating with the orchestrator (optional if using Auth0). "
        "Set via Jupyter config for self-hosted deployments.",
    )

    def _orchestrator_token_default(self):
        """Default to empty (Auth0 preferred)."""
        return ""

    # Auth0 configuration - baked in for SaaS distribution
    auth0_domain = Unicode(
        config=True,
        help="Auth0 domain for user authentication. "
        "Set via Jupyter config for self-hosted deployments.",
    )

    def _auth0_domain_default(self):
        return DEFAULT_AUTH0_DOMAIN

    auth0_client_id = Unicode(
        config=True,
        help="Auth0 client ID for user authentication. "
        "Set via Jupyter config for self-hosted deployments.",
    )

    def _auth0_client_id_default(self):
        return DEFAULT_AUTH0_CLIENT_ID

    auth0_audience = Unicode(
        config=True,
        help="Auth0 API audience for user authentication. "
        "Set via Jupyter config for self-hosted deployments.",
    )

    def _auth0_audience_default(self):
        return DEFAULT_AUTH0_AUDIENCE

    token_store_path = Unicode(
        config=True,
        help="Path to encrypted token store file used when keyring is unavailable.",
    )

    def _token_store_path_default(self):
        config_dir = jupyter_config_dir()
        return os.path.join(config_dir, "jupyter_ai_connector", "token_store.json.enc")

    token_store_key_path = Unicode(
        config=True,
        help="Path to encrypted token store key file (created if missing).",
    )

    def _token_store_key_path_default(self):
        config_dir = jupyter_config_dir()
        return os.path.join(config_dir, "jupyter_ai_connector", "token_store.key")

    token_store_key = Unicode(
        "",
        config=True,
        help="Base64-encoded token store key (overrides token_store_key_path if set).",
    )

    token_store_preference_path = Unicode(
        config=True,
        help="Path to token storage preference file.",
    )

    def _token_store_preference_path_default(self):
        config_dir = jupyter_config_dir()
        return os.path.join(config_dir, "jupyter_ai_connector", "token_store.preference.json")

    token_store_file_enabled = Bool(
        True,
        config=True,
        help="Enable encrypted file-store fallback when keyring is unavailable.",
    )

    proxy_timeout = Int(
        30,
        config=True,
        help="Timeout in seconds for proxy requests",
    )

    max_payload_size = Int(
        25 * 1024 * 1024,  # 25MB default
        config=True,
        help="Maximum payload size in bytes (default: 25MB)",
    )

    heartbeat_interval = Float(
        15.0,
        config=True,
        help="Interval in seconds for SSE heartbeat messages (default: 15s)",
    )

    enable_sse_mux = Bool(
        config=True,
        help="Enable multiplexed SSE stream endpoints (default: True).",
    )

    def _enable_sse_mux_default(self):
        raw = os.environ.get("JAI_ENABLE_SSE_MUX")
        if raw is not None and raw != "":
            return raw.lower() in ("1", "true", "yes", "on")
        return True

    mux_stream_ttl_ms = Int(
        600000,
        config=True,
        help="Mux stream TTL in milliseconds (default: 600000).",
    )

    mux_max_subscriptions = Int(
        50,
        config=True,
        help="Maximum subscriptions per mux stream.",
    )

    mux_outbound_queue_max = Int(
        2000,
        config=True,
        help="Maximum queued mux events before closing the stream.",
    )

    mux_write_batch_size = Int(
        50,
        config=True,
        help="Maximum SSE frames to batch in a single flush.",
    )

    mux_sidecar_flush_ms = Int(
        5000,
        config=True,
        help="Flush interval for mux sidecar appends in milliseconds.",
    )

    dev_mode = Bool(
        False,
        config=True,
        help="Enable dev-only config switching endpoints and UI.",
    )

    lock_saas_defaults = Bool(
        True,
        config=True,
        help="Force baked-in SaaS defaults for orchestrator/Auth0, ignoring overrides.",
    )

    allow_hidden = Bool(
        True,
        config=True,
        help="Allow hidden files (e.g., .jupyter_ai) for local sidecar cache.",
    )

    dev_profile = Unicode(
        "",
        config=True,
        help="Active dev profile name (if dev_mode is enabled).",
    )

    dev_profiles = Dict(
        config=True,
        help="Named dev profiles for switching connector config at runtime.",
    )

    def _dev_profiles_default(self):
        if os.environ.get("JAI_ENABLE_DEV_PROFILES", "").lower() not in ("1", "true", "yes"):
            return {}
        return {
            "saas": {
                "orchestrator_url": DEFAULT_ORCHESTRATOR_URL,
                "auth0_domain": DEFAULT_AUTH0_DOMAIN,
                "auth0_client_id": DEFAULT_AUTH0_CLIENT_ID,
                "auth0_audience": DEFAULT_AUTH0_AUDIENCE,
                "orchestrator_token": "",
            },
            "local": {
                "orchestrator_url": "http://orchestrator:8000",
                "auth0_domain": "",
                "auth0_client_id": "",
                "auth0_audience": "",
                "orchestrator_token": "dev-token",
            },
        }

    dev_state_path = Unicode(
        config=True,
        help="Path to persist active dev profile selection (JSON).",
    )

    def _dev_state_path_default(self):
        config_dir = jupyter_config_dir()
        return os.path.join(config_dir, "jai_dev_profile.json")

    def _load_dev_state(self) -> dict:
        if not self.dev_state_path:
            return {}
        try:
            with open(self.dev_state_path, "r", encoding="utf-8") as handle:
                return json.load(handle)
        except FileNotFoundError:
            return {}
        except Exception as exc:
            self.log.warning(f"Failed to load dev state: {exc}")
            return {}

    def _save_dev_state(self, state: dict) -> None:
        if not self.dev_state_path:
            return
        try:
            os.makedirs(os.path.dirname(self.dev_state_path), exist_ok=True)
            with open(self.dev_state_path, "w", encoding="utf-8") as handle:
                json.dump(state, handle)
        except Exception as exc:
            self.log.warning(f"Failed to persist dev state: {exc}")

    def _filter_dev_config(self, config: dict) -> dict:
        allowed = {
            "orchestrator_url",
            "orchestrator_token",
            "auth0_domain",
            "auth0_client_id",
            "auth0_audience",
            "token_store_path",
            "token_store_key_path",
            "token_store_key",
            "token_store_preference_path",
            "token_store_file_enabled",
            "proxy_timeout",
            "max_payload_size",
            "heartbeat_interval",
            "enable_sse_mux",
            "mux_stream_ttl_ms",
            "mux_max_subscriptions",
            "mux_outbound_queue_max",
            "mux_write_batch_size",
            "mux_sidecar_flush_ms",
        }
        return {key: value for key, value in config.items() if key in allowed and value is not None}

    def _resolve_dev_profile(self, profile_name: str) -> dict:
        if not profile_name:
            return {}
        profile = self.dev_profiles.get(profile_name, {})
        if not isinstance(profile, dict):
            return {}
        return self._filter_dev_config(profile)

    def _build_base_config(self) -> dict:
        return {
            "orchestrator_url": self.orchestrator_url,
            "orchestrator_token": self.orchestrator_token,
            "proxy_timeout": self.proxy_timeout,
            "max_payload_size": self.max_payload_size,
            "heartbeat_interval": self.heartbeat_interval,
            "enable_sse_mux": self.enable_sse_mux,
            "mux_stream_ttl_ms": self.mux_stream_ttl_ms,
            "mux_max_subscriptions": self.mux_max_subscriptions,
            "mux_outbound_queue_max": self.mux_outbound_queue_max,
            "mux_write_batch_size": self.mux_write_batch_size,
            "mux_sidecar_flush_ms": self.mux_sidecar_flush_ms,
            "auth0_domain": self.auth0_domain,
            "auth0_client_id": self.auth0_client_id,
            "auth0_audience": self.auth0_audience,
            "token_store_path": self.token_store_path,
            "token_store_key_path": self.token_store_key_path,
            "token_store_key": self.token_store_key,
            "token_store_preference_path": self.token_store_preference_path,
            "token_store_file_enabled": self.token_store_file_enabled,
        }

    def _apply_saas_defaults(self, config: dict) -> None:
        config["orchestrator_url"] = DEFAULT_ORCHESTRATOR_URL
        config["auth0_domain"] = DEFAULT_AUTH0_DOMAIN
        config["auth0_client_id"] = DEFAULT_AUTH0_CLIENT_ID
        config["auth0_audience"] = DEFAULT_AUTH0_AUDIENCE

    def initialize_settings(self):
        """Initialize settings for the extension."""
        base_config = self._build_base_config()
        effective_config = dict(base_config)
        active_profile = ""

        if self.dev_mode:
            state = self._load_dev_state()
            profile_name = self.dev_profile or state.get("active_profile", "")
            if not profile_name and self.dev_profiles:
                profile_name = next(iter(self.dev_profiles.keys()))
            if profile_name:
                profile_config = self._resolve_dev_profile(profile_name)
                effective_config.update(profile_config)
                active_profile = profile_name
                if state.get("active_profile") != profile_name:
                    self._save_dev_state({"active_profile": profile_name})

        if self.lock_saas_defaults:
            self._apply_saas_defaults(effective_config)

        self.settings["jupyter_ai_connector"] = effective_config
        self.settings["jupyter_ai_connector_dev"] = {
            "enabled": self.dev_mode,
            "active_profile": active_profile,
            "profiles": self.dev_profiles,
            "state_path": self.dev_state_path,
            "base_config": base_config,
        }

        # Log configuration (without exposing secrets)
        self.log.info("Initializing Jupyter AI Connector")
        self.log.info(f"  orchestrator_url: {effective_config.get('orchestrator_url')}")
        self.log.info(f"  proxy_timeout: {effective_config.get('proxy_timeout')}s")
        self.log.info(f"  max_payload_size: {effective_config.get('max_payload_size')} bytes")
        self.log.info(f"  heartbeat_interval: {effective_config.get('heartbeat_interval')}s")
        self.log.info(f"  enable_sse_mux: {effective_config.get('enable_sse_mux')}")
        self.log.info(f"  mux_stream_ttl_ms: {effective_config.get('mux_stream_ttl_ms')}")
        self.log.info(f"  mux_max_subscriptions: {effective_config.get('mux_max_subscriptions')}")
        self.log.info(f"  mux_outbound_queue_max: {effective_config.get('mux_outbound_queue_max')}")
        self.log.info(f"  mux_write_batch_size: {effective_config.get('mux_write_batch_size')}")
        self.log.info(f"  mux_sidecar_flush_ms: {effective_config.get('mux_sidecar_flush_ms')}")
        self.log.info(
            f"  orchestrator_token: {'[SET]' if effective_config.get('orchestrator_token') else '[NOT SET]'}"
        )
        self.log.info(
            f"  auth0_domain: {effective_config.get('auth0_domain') or '[NOT SET]'}"
        )
        auth0_client_id = effective_config.get("auth0_client_id")
        self.log.info(
            f"  auth0_client_id: {auth0_client_id[:8]}... " if auth0_client_id else "  auth0_client_id: [NOT SET]"
        )
        self.log.info(f"  lock_saas_defaults: {self.lock_saas_defaults}")
        token_store_path = effective_config.get("token_store_path") or "[DISABLED]"
        self.log.info(f"  token_store_path: {token_store_path}")
        token_store_preference_path = effective_config.get("token_store_preference_path") or "[DISABLED]"
        self.log.info(f"  token_store_preference_path: {token_store_preference_path}")
        self.log.info(
            f"  token_store_file_enabled: {effective_config.get('token_store_file_enabled', True)}"
        )
        if self.dev_mode:
            self.log.info(f"  dev_mode: enabled (profile={active_profile or '[none]'})")
        try:
            contents_manager = self.serverapp.contents_manager
            if hasattr(contents_manager, "allow_hidden"):
                contents_manager.allow_hidden = self.allow_hidden
            if self.allow_hidden and hasattr(contents_manager, "hide_hidden"):
                contents_manager.hide_hidden = False
            self.log.info(f"  allow_hidden: {self.allow_hidden}")
        except Exception as exc:
            self.log.warning(f"Failed to apply allow_hidden setting: {exc}")

    def initialize_handlers(self):
        """Initialize HTTP handlers."""
        setup_handlers(self.serverapp.web_app, self.settings)

    async def stop_extension(self):
        """Cleanup when extension stops."""
        self.log.info("Jupyter AI Connector extension stopping")
        try:
            from .mux import get_mux_manager

            manager = get_mux_manager(self.settings)
            await manager.shutdown()
        except Exception as exc:
            self.log.warning(f"Failed to close mux streams: {exc}")
