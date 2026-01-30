import asyncio
import json
import logging
import os
import re
import shlex
import shutil
import subprocess
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from dbus_next import Variant
from dbus_next.aio import MessageBus
from dbus_next.service import ServiceInterface, method

from claw_runner.config import load_config


# KRunner DBus interface docs:
# https://develop.kde.org/docs/plasma/krunner/
# Interface name: org.kde.krunner1
# Path: /runner

log = logging.getLogger("claw-runner")


@dataclass
class Match:
    id: str
    text: str
    subtext: str
    relevance: float
    icon: str


def _split_cmd(cmd: str) -> List[str]:
    # shlex.split handles quoted terminal command strings from config.json
    return shlex.split(cmd) if cmd.strip() else []


def _which_or_none(name: str) -> Optional[str]:
    try:
        return shutil.which(name)
    except Exception:
        return None


def _resolve_cli(cli: str) -> str:
    # Allow absolute/relative paths in config; otherwise resolve via PATH.
    if not cli:
        return "clawdbot"

    if os.path.isabs(cli) and os.access(cli, os.X_OK):
        return cli

    # If config provided a relative path, resolve relative to HOME.
    if ("/" in cli) and not os.path.isabs(cli):
        p = Path(os.path.expanduser(cli)).resolve()
        if p.exists() and os.access(str(p), os.X_OK):
            return str(p)

    found = _which_or_none(cli)
    if found:
        return found

    # common locations under user installs
    for p in (
        Path(os.path.expanduser("~/.local/bin")) / cli,
        Path("/usr/local/bin") / cli,
        Path("/usr/bin") / cli,
    ):
        if p.exists() and os.access(str(p), os.X_OK):
            return str(p)

    # Last resort: keep as-is so error output can mention it.
    return cli


def _resolve_terminal(config_terminal: str) -> List[str]:
    if config_terminal.strip():
        return _split_cmd(config_terminal)

    # Prefer desktop-integrated terminals first.
    candidates: List[List[str]] = [
        ["x-terminal-emulator", "-e"],
        ["konsole", "-e"],
        ["gnome-terminal", "--"],
        ["alacritty", "-e"],
        ["kitty", "-e"],
        ["xterm", "-e"],
    ]

    for cmd in candidates:
        if _which_or_none(cmd[0]):
            return cmd
    return []


def _run(
    args: Sequence[str],
    timeout_s: float = 2.0,
) -> Tuple[int, str, str]:
    try:
        proc = subprocess.run(
            list(args),
            text=True,
            capture_output=True,
            timeout=timeout_s,
        )
        return proc.returncode, proc.stdout or "", proc.stderr or ""
    except subprocess.TimeoutExpired as e:
        return 124, e.stdout or "", e.stderr or "Timed out"
    except Exception as e:
        return 127, "", str(e)


class KRunnerInterface(ServiceInterface):
    def __init__(self):
        super().__init__("org.kde.krunner1")
        self.config = load_config()
        self._activation_token: Optional[str] = None

    @method()
    def Actions(self) -> "a(sss)":
        # Structure: (id, text, iconName)
        return [
            ["open", "Open", "applications-internet"],
            ["notify", "Notify", "dialog-information"],
            ["terminal", "Open in terminal", "utilities-terminal"],
            ["start", "Start", "media-playback-start"],
            ["stop", "Stop", "media-playback-stop"],
            ["restart", "Restart", "view-refresh"],
        ]

    @method()
    def Match(self, query: "s") -> "a(sssida{sv})":
        q = (query or "").strip()
        if not q:
            return []

        if not q.lower().startswith("claw"):
            return []

        url = self.config.dashboard_url
        query_l = q.lower().strip()

        # KRunner::QueryMatch::Type values (common): ExactMatch=100
        EXACT_MATCH = 100

        matches = []

        def add_match(
            mid: str,
            text: str,
            icon: str,
            relevance: float,
            subtext: str,
            actions: List[str],
        ):
            props: Dict[str, Variant] = {
                "subtext": Variant("s", subtext),
                "actions": Variant("as", actions),
            }
            matches.append([mid, text, icon, EXACT_MATCH, relevance, props])

        # Dashboard is always available when user types "claw".
        add_match(
            "open-dashboard",
            "Open OpenClaw dashboard",
            "applications-internet",
            1.0,
            url,
            ["open"],
        )

        wants_status = query_l in ("claw", "claw ") or "status" in query_l or "health" in query_l
        wants_gateway = "gateway" in query_l
        wants_daemon = "daemon" in query_l or "browser" in query_l
        wants_logs = "log" in query_l or "journal" in query_l
        wants_config = "config" in query_l
        wants_memory = "memory" in query_l or "mem" in query_l

        if wants_status:
            add_match(
                "status-concise",
                "Status (concise)",
                "dialog-information",
                0.92,
                "Gateway/TG/WA/Sessions summary",
                ["notify"],
            )
            add_match(
                "status-verbose",
                "Status (verbose)",
                "utilities-terminal",
                0.90,
                "Open terminal: <cli> status (--all if available)",
                ["terminal"],
            )

        if wants_gateway or (query_l in ("claw", "claw ")):
            add_match(
                "gateway",
                "Gateway service",
                "network-server",
                0.86,
                f"systemctl --user (unit: {self.config.gateway_service})",
                ["start", "stop", "restart"],
            )

        if wants_daemon or (query_l in ("claw", "claw ")):
            add_match(
                "daemon",
                "Daemon service",
                "preferences-system",
                0.85,
                f"systemctl --user (unit: {self.config.daemon_service})",
                ["start", "stop", "restart"],
            )

        if wants_logs or (query_l in ("claw", "claw ")):
            add_match(
                "logs-gateway",
                "Follow gateway logs",
                "text-x-log",
                0.80,
                f"journalctl --user -u {self.config.gateway_service} -f",
                ["terminal"],
            )
            add_match(
                "logs-daemon",
                "Follow daemon logs",
                "text-x-log",
                0.79,
                f"journalctl --user -u {self.config.daemon_service} -f",
                ["terminal"],
            )
            add_match(
                "logs-runner",
                "Follow claw-runner logs",
                "text-x-log",
                0.78,
                "journalctl --user -u claw-runner.service -f",
                ["terminal"],
            )

        if wants_config or (query_l in ("claw", "claw ")):
            add_match(
                "open-config",
                "Open claw-runner config",
                "document-edit",
                0.76,
                "~/.config/claw-runner/config.json",
                ["open"],
            )

        if wants_memory or (query_l in ("claw", "claw ")):
            add_match(
                "memory",
                "Memory status",
                "utilities-system-monitor",
                0.74,
                "Open terminal: <cli> status --all",
                ["terminal"],
            )

        return matches

    def _notify(self, message: str, seconds: int = 3) -> None:
        # Best-effort: kdialog → notify-send → logs
        log.info("notify: %s", message)
        try:
            if _which_or_none("kdialog"):
                subprocess.Popen(["kdialog", "--passivepopup", message, str(seconds)])
                return
            if _which_or_none("notify-send"):
                subprocess.Popen(["notify-send", "claw-runner", message])
                return
        except Exception:
            # Never crash the runner for notification failures.
            return

    def _open_url(self, url: str) -> None:
        env = os.environ.copy()
        if self._activation_token:
            env["XDG_ACTIVATION_TOKEN"] = self._activation_token

        candidates = [
            ["xdg-open", url],
            ["kde-open6", url],
            ["kde-open5", url],
            ["gio", "open", url],
        ]

        for cmd in candidates:
            exe = cmd[0]
            if _which_or_none(exe):
                try:
                    subprocess.Popen(cmd, env=env, start_new_session=True)
                    return
                except Exception:
                    continue

        # Last resort: let python pick a handler.
        try:
            webbrowser.open(url, new=0)
        except Exception:
            pass

    def _open_file(self, path: str) -> None:
        p = os.path.expanduser(path)
        self._open_url(f"file://{p}")

    def _ensure_default_config_file(self) -> Path:
        cfg_path = Path(os.path.expanduser("~/.config/claw-runner/config.json"))
        cfg_path.parent.mkdir(parents=True, exist_ok=True)
        if not cfg_path.exists():
            cfg_path.write_text(
                json.dumps(
                    {
                        "dashboardUrl": self.config.dashboard_url,
                        "cli": self.config.cli,
                        "gatewayService": self.config.gateway_service,
                        "daemonService": self.config.daemon_service,
                        "terminal": self.config.terminal,
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
        return cfg_path

    def _open_terminal(self, command: Sequence[str], title: str = "") -> None:
        term = _resolve_terminal(self.config.terminal)
        if not term:
            self._notify("No terminal emulator found")
            return

        # Some terminals accept a title flag, but it is inconsistent; keep simple.
        try:
            subprocess.Popen(
                list(term) + list(command),
                start_new_session=True,
            )
        except Exception as e:
            log.exception("Failed to open terminal")
            self._notify(f"Failed to open terminal: {e}")

    def _systemctl_user(self, verb: str, unit: str) -> Tuple[bool, str]:
        unit = (unit or "").strip()
        if not unit:
            return False, "No unit configured"

        rc, out, err = _run(["systemctl", "--user", verb, unit], timeout_s=8.0)
        if rc == 0:
            return True, f"{verb} {unit}: OK"
        msg = (err.strip() or out.strip() or f"systemctl rc={rc}").strip()
        return False, f"{verb} {unit}: {msg}"

    def _parse_status_text(self, text: str) -> Dict[str, object]:
        # Defensive parsing for unknown CLI formats.
        # Expected (examples):
        #  Gateway: OK
        #  Telegram: OK
        #  WhatsApp: DOWN
        #  Sessions: 3
        res: Dict[str, object] = {}

        def find_state(label: str) -> Optional[str]:
            m = re.search(rf"(?im)^\s*{re.escape(label)}\s*:\s*([^\n]+)$", text)
            if not m:
                return None
            return m.group(1).strip()

        res["gateway"] = find_state("Gateway") or find_state("gateway")
        res["telegram"] = find_state("Telegram") or find_state("TG")
        res["whatsapp"] = find_state("WhatsApp") or find_state("WA")

        m = re.search(r"(?im)^\s*Sessions\s*:\s*(\d+)\b", text)
        if m:
            try:
                res["sessions"] = int(m.group(1))
            except Exception:
                pass

        return res

    def _status_summary(self) -> str:
        cli = _resolve_cli(self.config.cli)

        # Prefer JSON if supported.
        for args in (
            [cli, "status", "--json"],
            [cli, "status", "--format", "json"],
        ):
            rc, out, err = _run(args, timeout_s=2.0)
            if rc != 0 or not out.strip():
                continue
            try:
                data = json.loads(out)
            except Exception:
                continue

            gateway = (data.get("gateway") or {})
            gateway_state = gateway.get("state")
            if gateway_state is None:
                gateway_state = gateway.get("reachable")

            gateway_ok = (
                gateway_state is True
                or (isinstance(gateway_state, str) and gateway_state.lower() in ("ok", "up", "reachable", "running"))
            )

            channels = data.get("channels") or data.get("channelStatus") or []

            def chan(name: str) -> str:
                for c in channels:
                    c_name = (c.get("channel") or c.get("name") or "").lower()
                    if c_name == name:
                        state = (c.get("state") or c.get("status") or "").upper()
                        return state or "?"
                return "?"

            tg = chan("telegram")
            wa = chan("whatsapp")

            session_count = None
            sessions = data.get("sessions")
            if isinstance(sessions, dict):
                session_count = sessions.get("active")
                if session_count is None:
                    session_count = sessions.get("count")
            if session_count is None:
                session_count = data.get("sessionCount")

            parts = ["Gateway: OK" if gateway_ok else "Gateway: DOWN", f"TG: {tg}", f"WA: {wa}"]
            if isinstance(session_count, int):
                parts.append(f"Sessions: {session_count}")
            return " · ".join(parts)

        # Fallback to plain text.
        rc, out, err = _run([cli, "status"], timeout_s=2.0)
        if rc != 0:
            msg = (err.strip() or out.strip() or "unavailable").strip()
            return f"Status: {msg}"

        parsed = self._parse_status_text(out)
        gateway_raw = str(parsed.get("gateway") or "").strip()
        gateway_ok = gateway_raw.lower() in ("ok", "up", "running", "reachable", "true")
        tg = str(parsed.get("telegram") or "?").strip().upper()
        wa = str(parsed.get("whatsapp") or "?").strip().upper()

        parts = ["Gateway: OK" if gateway_ok else "Gateway: DOWN", f"TG: {tg}", f"WA: {wa}"]
        if isinstance(parsed.get("sessions"), int):
            parts.append(f"Sessions: {parsed['sessions']}")
        return " · ".join(parts)

    @method()
    def SetActivationToken(self, token: "s") -> None:
        # Plasma passes an XDG activation token for proper focus-stealing prevention.
        self._activation_token = (token or "").strip() or None

    @method()
    def Run(self, matchId: "s", actionId: "s") -> None:
        # actionId is empty when user hits Enter; otherwise one of Actions().
        try:
            log.info("Run matchId=%s actionId=%s", matchId, actionId)

            if matchId == "open-dashboard":
                self._open_url(self.config.dashboard_url)
                return

            if matchId == "open-config":
                p = self._ensure_default_config_file()
                self._open_file(str(p))
                return

            if matchId == "status-concise":
                self._notify(self._status_summary())
                return

            if matchId in ("status-verbose", "memory"):
                cli = _resolve_cli(self.config.cli)
                # Prefer --all if supported; otherwise plain status.
                rc, out, _ = _run([cli, "status", "--all"], timeout_s=1.5)
                cmd = [cli, "status", "--all"] if rc == 0 else [cli, "status"]
                self._open_terminal(cmd)
                return

            if matchId == "logs-gateway":
                self._open_terminal(["journalctl", "--user", "-u", self.config.gateway_service, "-f"])
                return
            if matchId == "logs-daemon":
                self._open_terminal(["journalctl", "--user", "-u", self.config.daemon_service, "-f"])
                return
            if matchId == "logs-runner":
                self._open_terminal(["journalctl", "--user", "-u", "claw-runner.service", "-f"])
                return

            if matchId in ("gateway", "daemon"):
                unit = self.config.gateway_service if matchId == "gateway" else self.config.daemon_service
                verb = (actionId or "restart").strip() or "restart"
                if verb not in ("start", "stop", "restart"):
                    verb = "restart"
                ok, msg = self._systemctl_user(verb, unit)
                self._notify(msg, seconds=3 if ok else 6)
                return

        except Exception as e:
            log.exception("Run handler failed")
            self._notify(f"claw-runner error: {e}")
            return


async def main():
    logging.basicConfig(level=os.environ.get("CLAW_RUNNER_LOGLEVEL", "INFO"))

    bus = await MessageBus().connect()

    # Own a unique bus name.
    await bus.request_name("ai.openclaw.ClawRunner")

    iface = KRunnerInterface()
    bus.export("/runner", iface)

    log.info("claw-runner started")

    # Keep process alive.
    await asyncio.get_running_loop().create_future()


if __name__ == "__main__":
    asyncio.run(main())
