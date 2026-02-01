# claw-runner

A small **KRunner** DBus runner for **OpenClaw / Clawdbot**.

Type `claw` in KRunner to get quick actions (open dashboard, view status, follow logs, and control the gateway user service).

## Features

- KDE Plasma / KRunner DBus runner (`org.kde.krunner1`)
- Works with **systemd user services** (`systemctl --user ...`)
- Concise status as a desktop notification
- Verbose actions open in a terminal and stay open
- Configurable CLI binary/path and terminal command

## Requirements

- Linux + KDE Plasma (KRunner)
- Python 3
- `dbus-next` (see `requirements.txt`)
- Optional: a terminal emulator (auto-detected)
- Optional: `kdialog` or `notify-send` (for notifications)

## Install (user service)

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

## Usage

Open KRunner and type:

- `claw` — shows the main actions
- `claw status` — status actions
- `claw logs` — log-follow actions
- `claw gateway` — gateway start/stop/restart

## Config

Config file:

- `~/.config/claw-runner/config.json`

The runner will create a default config file when you use **Open config** in KRunner.

Example:

```json
{
  "dashboardUrl": "http://127.0.0.1:18789/",
  "cli": "openclaw",
  "gatewayService": "openclaw-gateway.service",
  "terminal": "kitty"
}
```

### Terminal selection

Precedence:

1. `terminal` in config
2. `$TERMINAL`
3. auto-detect (`x-terminal-emulator`, `kitty`, `alacritty`, `konsole`, `gnome-terminal`, `xterm`)

Advanced: include `{cmd}` to fully control invocation, e.g.

```json
{ "terminal": "konsole --hold -e sh -lc {cmd}" }
```

## Security notes

- `claw-runner` never shells out with untrusted strings as a single command. It uses argv-style subprocess calls.
- The terminal actions run via `sh -lc ...` to support common terminal conventions; the command is built from a fixed argv list.
- URL opening is restricted to `http(s)` and `file` schemes.

## Uninstall

```bash
./uninstall.sh
systemctl --user daemon-reload
```

## Development

Run it directly:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
./bin/claw-runner
```

Logs:

```bash
journalctl --user -u claw-runner.service -f
```

## Versioning

This repo uses semantic versioning tags (`vX.Y.Z`). See `CHANGELOG.md`.

## OpenClaw links

- OpenClaw repo: https://github.com/openclaw/openclaw
- Docs: https://docs.openclaw.ai/

## Contributing

PRs welcome.

- Keep changes small and focused
- Prefer defensive parsing (CLI output formats can evolve)
- Test on KDE Plasma / KRunner
