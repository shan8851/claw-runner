#!/usr/bin/env bash
set -euo pipefail

mkdir -p "$HOME/.config/systemd/user"
install -m 0644 "$(dirname "$0")/claw-runner.service" "$HOME/.config/systemd/user/claw-runner.service"

echo "Installed: ~/.config/systemd/user/claw-runner.service"
echo "Next: systemctl --user daemon-reload && systemctl --user enable --now claw-runner.service"
