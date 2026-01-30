import asyncio
import json
import subprocess
from dataclasses import dataclass
from typing import List

from dbus_next.aio import MessageBus
from dbus_next.service import ServiceInterface, method

from claw_runner.config import load_config


# KRunner DBus interface docs:
# https://develop.kde.org/docs/plasma/krunner/
# Interface name: org.kde.krunner1
# Path: /runner
# Bus name: something unique


@dataclass
class Match:
    id: str
    text: str
    subtext: str
    relevance: float
    icon: str


class KRunnerInterface(ServiceInterface):
    def __init__(self):
        super().__init__("org.kde.krunner1")
        self.config = load_config()

    @method()
    def Actions(self) -> "as":
        # V1: only one action. KRunner calls this to show action buttons.
        return ["open"]

    @method()
    def Match(self, query: "s") -> "a(sssdss)":
        q = (query or "").strip()
        if not q:
            return []

        # Trigger keyword: claw
        if not q.lower().startswith("claw"):
            return []

        url = self.config.dashboard_url
        return [
            (
                "open-dashboard",  # id
                "Open Clawdbot dashboard",  # text
                url,  # subtext
                1.0,  # relevance
                "applications-internet",  # icon name
                "open",  # action id
            )
        ]

    @method()
    def Run(self, match_id: "s", action_id: "s") -> "b":
        # Called when user hits Enter or triggers an action.
        if match_id != "open-dashboard":
            return False

        url = self.config.dashboard_url
        try:
            # Use xdg-open so it works across DEs.
            subprocess.Popen(["xdg-open", url])
            return True
        except Exception:
            return False


async def main():
    bus = await MessageBus().connect()

    # Own a unique bus name.
    await bus.request_name("ai.openclaw.ClawRunner")

    iface = KRunnerInterface()
    bus.export("/runner", iface)

    # Keep process alive.
    await asyncio.get_running_loop().create_future()


if __name__ == "__main__":
    asyncio.run(main())
