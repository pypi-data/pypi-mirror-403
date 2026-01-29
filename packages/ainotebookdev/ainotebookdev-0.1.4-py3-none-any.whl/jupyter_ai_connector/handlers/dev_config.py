"""Dev-only config switching handlers."""

import json
from typing import Any

from jupyter_server.base.handlers import APIHandler

from .oauth import reset_token_store


class DevConfigBaseHandler(APIHandler):
    """Base handler for dev config endpoints."""

    def get_dev_settings(self) -> dict[str, Any]:
        return self.settings.get("jupyter_ai_connector_dev", {})

    def get_connector_settings(self) -> dict[str, Any]:
        return self.settings.get("jupyter_ai_connector", {})

    def dev_enabled(self) -> bool:
        return bool(self.get_dev_settings().get("enabled"))

    def ensure_dev_enabled(self) -> bool:
        if not self.dev_enabled():
            self.set_status(404)
            self.write({"error": "Dev config not enabled"})
            self.finish()
            return False
        return True

    def apply_profile(self, profile_name: str, profile: dict[str, Any]) -> None:
        connector_settings = self.get_connector_settings()
        for key, value in profile.items():
            connector_settings[key] = value
        self.settings["jupyter_ai_connector"] = connector_settings

        dev_settings = self.get_dev_settings()
        dev_settings["active_profile"] = profile_name
        self.settings["jupyter_ai_connector_dev"] = dev_settings

        state_path = dev_settings.get("state_path") or ""
        if state_path:
            try:
                from pathlib import Path

                path = Path(state_path)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps({"active_profile": profile_name}), encoding="utf-8")
            except Exception:
                pass

        reset_token_store()


class DevConfigHandler(DevConfigBaseHandler):
    """Get/set dev config profile."""

    async def get(self):
        if not self.ensure_dev_enabled():
            return
        dev_settings = self.get_dev_settings()
        self.write({
            "enabled": True,
            "activeProfile": dev_settings.get("active_profile") or "",
            "profiles": dev_settings.get("profiles") or {},
        })
        self.finish()

    async def post(self):
        if not self.ensure_dev_enabled():
            return
        try:
            payload = json.loads(self.request.body or b"{}")
        except json.JSONDecodeError:
            self.set_status(400)
            self.write({"error": "Invalid JSON"})
            self.finish()
            return

        profile_name = payload.get("profile")
        dev_settings = self.get_dev_settings()
        profiles = dev_settings.get("profiles") or {}
        if not profile_name or profile_name not in profiles:
            self.set_status(400)
            self.write({"error": "Unknown profile", "available": sorted(profiles.keys())})
            self.finish()
            return

        profile = profiles.get(profile_name) or {}
        if not isinstance(profile, dict):
            self.set_status(400)
            self.write({"error": "Invalid profile config"})
            self.finish()
            return

        self.apply_profile(profile_name, profile)
        self.write({"status": "ok", "activeProfile": profile_name})
        self.finish()


class DevConfigUiHandler(DevConfigBaseHandler):
    """Simple dev UI to switch profiles."""

    async def get(self):
        if not self.ensure_dev_enabled():
            return
        dev_settings = self.get_dev_settings()
        active = dev_settings.get("active_profile") or ""
        profiles = dev_settings.get("profiles") or {}
        options = "\n".join(
            f'<option value="{name}"{" selected" if name == active else ""}>{name}</option>'
            for name in sorted(profiles.keys())
        )
        html = """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Jupyter AI Dev Config</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; padding: 24px; }}
    .card {{ max-width: 520px; margin: 0 auto; border: 1px solid #ddd; border-radius: 8px; padding: 16px; }}
    label {{ display: block; margin-bottom: 8px; font-weight: 600; }}
    select, button {{ font-size: 14px; padding: 8px 12px; }}
    button {{ margin-left: 8px; }}
  </style>
</head>
<body>
  <div class="card">
    <h2>Jupyter AI Dev Config</h2>
    <p>Switch the active connector profile (dev builds only).</p>
    <label for="profile">Active profile</label>
    <select id="profile">{options}</select>
    <button id="apply">Apply</button>
    <p id="status"></p>
  </div>
  <script>
    const applyBtn = document.getElementById('apply');
    const profileSel = document.getElementById('profile');
    const status = document.getElementById('status');
    applyBtn.addEventListener('click', async () => {
      status.textContent = 'Applying...';
      const resp = await fetch('./config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ profile: profileSel.value })
      });
      if (!resp.ok) {
        const data = await resp.json().catch(() => ({}));
        status.textContent = data.error || 'Failed';
        return;
      }
      const data = await resp.json();
      status.textContent = `Active profile: ${data.activeProfile}`;
    });
  </script>
</body>
</html>"""
        self.set_header("Content-Type", "text/html; charset=utf-8")
        self.write(html)
        self.finish()
