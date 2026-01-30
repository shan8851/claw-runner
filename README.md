# claw-runner

A tiny **KRunner** integration for **OpenClaw / Clawdbot**.

Type `claw` in KRunner to get quick actions (open dashboard, status, logs, gateway control).

## Supported environments

- KDE Plasma / KRunner (DBus runner: `org.kde.krunner1`)
- systemd **user** services (`systemctl --user ...`)
- Linux terminals (auto-detects common terminals; configurable)

## Status & actions

Type `claw` in KRunner:

- Open OpenClaw dashboard
- Status (concise notification)
- Status (verbose in terminal)
- Gateway: start/stop/restart (via `systemctl --user`)
- Logs: follow `journalctl --user -f` for gateway + claw-runner
- Open config

## Install

### Option A: Install as a user service (recommended)

```bash
./install.sh
systemctl --user daemon-reload
systemctl --user enable --now claw-runner.service
```

If KRunner doesn’t pick it up immediately, restart KRunner:

```bash
kquitapp6 krunner || kquitapp5 krunner || true
krunner &
```

### Option B: Run manually (dev)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
./bin/claw-runner
```

## Uninstall

```bash
./uninstall.sh
systemctl --user daemon-reload
```

## Config

Config file:

`~/.config/claw-runner/config.json`

Example:

```json
{
  "dashboardUrl": "http://127.0.0.1:18789/",
  "cli": "clawdbot",
  "gatewayService": "clawdbot-gateway.service",
  "terminal": "kitty"
}
```

### Terminal selection

Precedence:

1. `terminal` in config
2. `$TERMINAL`
3. auto-detect (`kitty`, `konsole`, `gnome-terminal`, `alacritty`, `x-terminal-emulator`, `xterm`)

The terminal is opened **and kept open** after commands finish.

Advanced: you can include `{cmd}` in `terminal` to fully control invocation, e.g.

```json
{ "terminal": "konsole --hold -e sh -lc {cmd}" }
```

## OpenClaw links

- OpenClaw repo: https://github.com/openclaw/openclaw (project home)
- Docs: https://docs.openclaw.ai/ (if you’re using the hosted docs)

## Contributing

PRs welcome.

- Keep changes small and focused
- Prefer defensive parsing (CLI output formats can evolve)
- Test on KDE/Plasma + KRunner

Local dev loop:

```bash
./bin/claw-runner
# then use KRunner: type "claw"
```

## Roadmap / ideas

- Better structured channel status once the CLI JSON schema stabilizes
- Add more actions (open gateway dashboard, open sessions list)
- Optional per-action terminal titles (terminal-dependent)
- Packaging (AUR / distro packages)
