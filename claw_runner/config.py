import json
import os
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Mapping


@dataclass(frozen=True)
class Config:
    """User-configurable settings for the KRunner runner."""

    dashboard_url: str = "http://127.0.0.1:18789/"

    # CLI binary name/path (openclaw | clawdbot, etc.)
    cli: str = "openclaw"

    # systemd --user service names
    gateway_service: str = "openclaw-gateway.service"

    # Terminal command used for “verbose” actions and logs.
    # If empty, we’ll auto-detect one.
    terminal: str = ""


def load_config() -> Config:
    """Load ~/.config/claw-runner/config.json, falling back to defaults."""

    path = Path(os.path.expanduser("~/.config/claw-runner/config.json"))
    if not path.exists():
        return Config()

    try:
        raw: Any = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        # Fail closed to defaults if the file is unreadable or invalid JSON.
        return Config()

    if not isinstance(raw, Mapping):
        return Config()

    data: Mapping[str, Any] = raw

    def pick(*keys: str) -> Any:
        for k in keys:
            if k in data:
                return data.get(k)
        return None

    cfg = Config()

    dashboard_url = pick("dashboardUrl", "dashboard_url")
    cli = pick("cli", "binary", "command")
    gateway_service = pick("gatewayService", "gateway_service")
    terminal = pick("terminal")

    if isinstance(dashboard_url, str) and dashboard_url.strip():
        cfg = replace(cfg, dashboard_url=dashboard_url.strip())
    if isinstance(cli, str) and cli.strip():
        cfg = replace(cfg, cli=cli.strip())
    if isinstance(gateway_service, str) and gateway_service.strip():
        cfg = replace(cfg, gateway_service=gateway_service.strip())
    if isinstance(terminal, str) and terminal.strip():
        cfg = replace(cfg, terminal=terminal.strip())

    return cfg
