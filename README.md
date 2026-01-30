# claw-runner

A tiny **KRunner** integration for **OpenClaw**.

Type `claw` in KRunner to get quick actions (V1: open the dashboard).

## Status & actions

Type `claw` in KRunner to get:

- Open dashboard
- Status (concise notification)
- Status (verbose in terminal)
- Gateway/Daemon: start/stop/restart (via `systemctl --user`)
- Logs: follow `journalctl -f` for gateway/daemon/runner
- Open config
- Memory status (currently opens verbose status)

## How it works

This is a **DBus-based KRunner runner** implementing `org.kde.krunner1`.

Instead of a big desktop app, it runs as a small user service and returns matches
to KRunner.

## Install (dev)

### 1) Install deps

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Run it

```bash
./bin/claw-runner
```

Then open KRunner and type: `claw`

## Install (user service)

```bash
./install.sh
systemctl --user daemon-reload
systemctl --user enable --now claw-runner.service
```

Restart KRunner if needed:

```bash
kquitapp6 krunner || kquitapp5 krunner || true
krunner &
```

## Uninstall

```bash
./uninstall.sh
```

## Config

Default dashboard URL: `http://127.0.0.1:18789/`

You can override it in:

`~/.config/claw-runner/config.json`

```json
{
  "dashboardUrl": "http://127.0.0.1:18789/",
  "cli": "clawdbot",
  "gatewayService": "clawdbot-gateway.service",
  "daemonService": "clawdbot-browser.service",
  "terminal": "x-terminal-emulator -e"
}
```

Notes:
- `cli` can be a bare name (resolved via PATH) or an absolute path.
- If `terminal` is empty, claw-runner auto-detects (x-terminal-emulator/konsole/gnome-terminal/alacritty/kitty/xterm).

