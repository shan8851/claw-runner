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
    def Actions(self) -> "a(sss)":
        # Return a list of supported actions.
        # Structure: (id, text, iconName)
        return [["open", "Open", "applications-internet"]]

    @method()
    def Match(self, query: "s") -> "a(sssida{sv})":
        q = (query or "").strip()
        if not q:
            return []

        if not q.lower().startswith("claw"):
            return []

        url = self.config.dashboard_url

        # KRunner::QueryMatch::Type values (common):
        # ExactMatch=100, PossibleMatch=30, etc.
        EXACT_MATCH = 100

        props = {
            "subtext": url,
            "urls": [url],
            # Show our single action.
            "actions": ["open"],
        }

        return [
            [
                "open-dashboard",  # id
                "Open Clawdbot dashboard",  # text
                "applications-internet",  # iconName
                EXACT_MATCH,  # type (int)
                1.0,  # relevance (double)
                props,  # properties (a{sv})
            ]
        ]

    @method()
    def Run(self, matchId: "s", actionId: "s") -> None:
        # actionId is empty when user hits Enter; otherwise one of Actions().
        if matchId != "open-dashboard":
            return

        url = self.config.dashboard_url
        try:
            subprocess.Popen(["xdg-open", url])
        except Exception:
            return


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
