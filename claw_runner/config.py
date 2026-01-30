import json
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Config:
    dashboard_url: str = "http://127.0.0.1:18789/"
    # CLI binary name (clawdbot | moltbot | openclaw, etc.)
    cli: str = "clawdbot"
    # systemd user service name for the gateway (optional; for future actions)
    gateway_service: str = "clawdbot-gateway.service"


def load_config() -> Config:
    # ~/.config/claw-runner/config.json
    path = Path(os.path.expanduser("~/.config/claw-runner/config.json"))
    if not path.exists():
        return Config()

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        dashboard_url = data.get("dashboardUrl") or data.get("dashboard_url")
        cli = data.get("cli") or data.get("binary") or data.get("command")
        gateway_service = data.get("gatewayService") or data.get("gateway_service")

        cfg = Config()
        if isinstance(dashboard_url, str) and dashboard_url.strip():
            cfg = Config(
                dashboard_url=dashboard_url.strip(),
                cli=cfg.cli,
                gateway_service=cfg.gateway_service,
            )
        if isinstance(cli, str) and cli.strip():
            cfg = Config(
                dashboard_url=cfg.dashboard_url,
                cli=cli.strip(),
                gateway_service=cfg.gateway_service,
            )
        if isinstance(gateway_service, str) and gateway_service.strip():
            cfg = Config(
                dashboard_url=cfg.dashboard_url,
                cli=cfg.cli,
                gateway_service=gateway_service.strip(),
            )
        return cfg
    except Exception:
        # fail closed to defaults
        return Config()
