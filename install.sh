#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"

# 1) systemd user service
mkdir -p "$HOME/.config/systemd/user"
install -m 0644 "$ROOT/claw-runner.service" "$HOME/.config/systemd/user/claw-runner.service"

echo "Installed: ~/.config/systemd/user/claw-runner.service"

# 2) KRunner desktop entry (DBus runner registration)
# Plasma typically looks here for DBus runners:
#   ~/.local/share/krunner/dbusplugins/
mkdir -p "$HOME/.local/share/krunner/dbusplugins"
install -m 0644 "$ROOT/krunner/ai.openclaw.ClawRunner.desktop" "$HOME/.local/share/krunner/dbusplugins/ai.openclaw.ClawRunner.desktop"

echo "Installed: ~/.local/share/krunner/dbusplugins/ai.openclaw.ClawRunner.desktop"

# 3) DBus service activation file (so KRunner can activate the runner)
mkdir -p "$HOME/.local/share/dbus-1/services"
install -m 0644 "$ROOT/dbus/ai.openclaw.ClawRunner.service" "$HOME/.local/share/dbus-1/services/ai.openclaw.ClawRunner.service"

echo "Installed: ~/.local/share/dbus-1/services/ai.openclaw.ClawRunner.service"

echo

echo "Next:"
echo "  systemctl --user daemon-reload"
echo "  systemctl --user enable --now claw-runner.service"
echo "  # restart krunner (Plasma 6/5):"
echo "  kquitapp6 krunner || kquitapp5 krunner || true"
echo "  krunner &"
