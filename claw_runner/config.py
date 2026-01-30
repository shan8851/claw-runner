import json
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Config:
    dashboard_url: str = "http://127.0.0.1:18789/"

    # CLI binary name/path (clawdbot | openclaw, etc.)
    cli: str = "clawdbot"

    # systemd --user service names
    gateway_service: str = "clawdbot-gateway.service"
    # “daemon” here is intentionally generic: default to clawdbot-browser.service,
    # but can be pointed at claw-runner.service or anything else you want.
    daemon_service: str = "clawdbot-browser.service"

    # Terminal command used for “verbose” actions and logs.
    # If empty, we’ll auto-detect one.
    terminal: str = ""


def load_config() -> Config:
    # ~/.config/claw-runner/config.json
    path = Path(os.path.expanduser("~/.config/claw-runner/config.json"))
    if not path.exists():
        return Config()

    try:
        data = json.loads(path.read_text(encoding="utf-8"))

        def pick(*keys: str):
            for k in keys:
                if k in data:
                    return data.get(k)
            return None

        cfg = Config()

        dashboard_url = pick("dashboardUrl", "dashboard_url")
        cli = pick("cli", "binary", "command")
        gateway_service = pick("gatewayService", "gateway_service")
        daemon_service = pick("daemonService", "daemon_service")
        terminal = pick("terminal")

        if isinstance(dashboard_url, str) and dashboard_url.strip():
            cfg = Config(
                dashboard_url=dashboard_url.strip(),
                cli=cfg.cli,
                gateway_service=cfg.gateway_service,
                daemon_service=cfg.daemon_service,
                terminal=cfg.terminal,
            )
        if isinstance(cli, str) and cli.strip():
            cfg = Config(
                dashboard_url=cfg.dashboard_url,
                cli=cli.strip(),
                gateway_service=cfg.gateway_service,
                daemon_service=cfg.daemon_service,
                terminal=cfg.terminal,
            )
        if isinstance(gateway_service, str) and gateway_service.strip():
            cfg = Config(
                dashboard_url=cfg.dashboard_url,
                cli=cfg.cli,
                gateway_service=gateway_service.strip(),
                daemon_service=cfg.daemon_service,
                terminal=cfg.terminal,
            )
        if isinstance(daemon_service, str) and daemon_service.strip():
            cfg = Config(
                dashboard_url=cfg.dashboard_url,
                cli=cfg.cli,
                gateway_service=cfg.gateway_service,
                daemon_service=daemon_service.strip(),
                terminal=cfg.terminal,
            )
        if isinstance(terminal, str) and terminal.strip():
            cfg = Config(
                dashboard_url=cfg.dashboard_url,
                cli=cfg.cli,
                gateway_service=cfg.gateway_service,
                daemon_service=cfg.daemon_service,
                terminal=terminal.strip(),
            )

        return cfg
    except Exception:
        # fail closed to defaults
        return Config()
