import asyncio
import json
import shutil
import subprocess
from dataclasses import dataclass
from typing import List

from dbus_next import Variant
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
        query_l = q.lower().strip()

        # KRunner::QueryMatch::Type values (common):
        # ExactMatch=100, PossibleMatch=30, etc.
        EXACT_MATCH = 100

        matches = []

        # 1) Dashboard
        props_dash = {
            "subtext": Variant("s", url),
            "urls": Variant("as", [url]),
            "actions": Variant("as", ["open"]),
        }
        matches.append(
            [
                "open-dashboard",
                "Open OpenClaw dashboard",
                "applications-internet",
                EXACT_MATCH,
                1.0,
                props_dash,
            ]
        )

        # 2) Status (only show if query implies it, or user just typed claw)
        if query_l in ("claw", "claw ") or "status" in query_l:
            props_status = {
                "subtext": Variant("s", "Quick health summary"),
                "actions": Variant("as", ["open"]),
            }
            matches.append(
                [
                    "status",
                    "Status (concise)",
                    "dialog-information",
                    EXACT_MATCH,
                    0.9,
                    props_status,
                ]
            )

        return matches

    @method()
    def _notify(self, message: str) -> None:
        # Best-effort: kdialog → notify-send → stderr (ignored)
        try:
            if shutil.which("kdialog"):
                subprocess.Popen(["kdialog", "--passivepopup", message, "3"])
                return
            if shutil.which("notify-send"):
                subprocess.Popen(["notify-send", "claw-runner", message])
                return
        except Exception:
            return

    def _status_summary(self) -> str:
        # Use `clawdbot status --json` (or configured CLI) and compress it.
        cli = self.config.cli
        try:
            out = subprocess.check_output([cli, "status", "--json"], text=True)
            data = json.loads(out)
        except Exception:
            return "Status: unavailable"

        # Heuristics: the JSON shape can evolve; be defensive.
        gateway = (data.get("gateway") or {})
        gateway_state = gateway.get("state") or gateway.get("reachable")
        gateway_ok = (
            gateway_state is True
            or (isinstance(gateway_state, str) and gateway_state.lower() in ("ok", "reachable"))
        )

        channels = data.get("channels") or []
        def chan(name: str) -> str:
            for c in channels:
                if (c.get("channel") or "").lower() == name:
                    state = (c.get("state") or "").upper()
                    return state or "?"
            return "?"

        tg = chan("telegram")
        wa = chan("whatsapp")

        sessions = data.get("sessions") or {}
        session_count = sessions.get("active") or sessions.get("count")
        if session_count is None:
            session_count = data.get("sessionCount")

        parts = []
        parts.append("Gateway: OK" if gateway_ok else "Gateway: DOWN")
        parts.append(f"TG: {tg}")
        parts.append(f"WA: {wa}")
        if isinstance(session_count, int):
            parts.append(f"Sessions: {session_count}")

        return " · ".join(parts)

    def Run(self, matchId: "s", actionId: "s") -> None:
        # actionId is empty when user hits Enter; otherwise one of Actions().
        if matchId == "open-dashboard":
            url = self.config.dashboard_url
            try:
                subprocess.Popen(["xdg-open", url])
            except Exception:
                pass
            return

        if matchId == "status":
            self._notify(self._status_summary())
            return

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
