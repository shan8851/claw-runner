import json
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Config:
    dashboard_url: str = "http://127.0.0.1:18789/"


def load_config() -> Config:
    # ~/.config/claw-runner/config.json
    path = Path(os.path.expanduser("~/.config/claw-runner/config.json"))
    if not path.exists():
        return Config()

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        url = data.get("dashboardUrl") or data.get("dashboard_url")
        if isinstance(url, str) and url.strip():
            return Config(dashboard_url=url.strip())
    except Exception:
        # fail closed to defaults
        pass

    return Config()
