#!/usr/bin/env bash
set -euo pipefail

systemctl --user disable --now claw-runner.service 2>/dev/null || true
rm -f "$HOME/.config/systemd/user/claw-runner.service"
rm -f "$HOME/.local/share/krunner/dbusplugins/ai.openclaw.ClawRunner.desktop"
rm -f "$HOME/.local/share/dbus-1/services/ai.openclaw.ClawRunner.service"

echo "Removed: ~/.config/systemd/user/claw-runner.service"
echo "Removed: ~/.local/share/krunner/dbusplugins/ai.openclaw.ClawRunner.desktop"
echo "Removed: ~/.local/share/dbus-1/services/ai.openclaw.ClawRunner.service"
echo "Note: venv and code remain at ~/giles/claw-runner"
