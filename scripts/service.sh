#!/bin/bash
# Keep the bridge running on this computer, in the background, and start it again after a restart.
#
#   scripts/service.sh install    start `anytvart bridge` now and every time this computer starts
#   scripts/service.sh remove     stop it and remove it
#   scripts/service.sh status     say whether it is on, and show the end of the log
#
# Only needed with an always-on computer. Without one, nothing on the computer runs after setup.
# macOS: a launchd agent (~/Library/LaunchAgents). Linux: a systemd user service (the Linux and
# Raspberry Pi path is built but not yet tested). Windows: not supported.
#
# Mac: the first time the bridge talks to a TV, macOS asks whether it may "find devices on your
# local network". Choose Allow, or the bridge cannot reach any TV (docs/TROUBLESHOOTING.md).

set -u
ROOT=$(cd "$(dirname "$0")/.." && pwd)
BIN="$ROOT/.venv/bin/anytvart"
CONFIG="$ROOT/config.json"
LOG="$ROOT/data/bridge.log"
LABEL="io.github.any-tv-art.bridge"
ACTION="${1:-status}"

if [ "$ACTION" = "install" ]; then
  [ -x "$BIN" ] || { echo "Set up first: python3 -m venv .venv && .venv/bin/pip install -e ."; exit 1; }
  [ -f "$CONFIG" ] || { echo "No config.json yet: copy config.example.json to config.json and fill it in."; exit 1; }
  mkdir -p "$ROOT/data"
fi

case "$(uname -s)" in
  Darwin)
    PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
    case "$ACTION" in
      install)
        mkdir -p "$HOME/Library/LaunchAgents"
        cat > "$PLIST" << PLIST_END
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key>
  <array>
    <!-- Python itself, not the .venv/bin/anytvart wrapper: in a folder whose path has a space, pip
         makes that wrapper a /bin/sh script, and macOS privacy rules (Downloads, Documents,
         Desktop) can block /bin/sh while still allowing Python (seen on our Mac). -->
    <string>$ROOT/.venv/bin/python</string>
    <string>-m</string><string>anytvart</string>
    <string>--config</string><string>$CONFIG</string>
    <string>bridge</string>
  </array>
  <key>EnvironmentVariables</key>
  <dict><key>PATH</key><string>/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin</string></dict>
  <key>KeepAlive</key><true/>
  <key>RunAtLoad</key><true/>
  <key>ThrottleInterval</key><integer>30</integer>
  <key>WorkingDirectory</key><string>$ROOT</string>
  <key>StandardOutPath</key><string>$LOG</string>
  <key>StandardErrorPath</key><string>$LOG</string>
</dict>
</plist>
PLIST_END
        launchctl bootout "gui/$(id -u)/$LABEL" 2> /dev/null
        launchctl bootstrap "gui/$(id -u)" "$PLIST" && echo "On. Log: data/bridge.log"
        ;;
      remove)
        launchctl bootout "gui/$(id -u)/$LABEL" 2> /dev/null
        rm -f "$PLIST" && echo "Off. The TVs keep their art app; \`anytvart undo\` takes it off."
        ;;
      *)
        if launchctl print "gui/$(id -u)/$LABEL" > /dev/null 2>&1; then echo "On (launchd: $LABEL)"; else echo "Off"; fi
        [ -f "$LOG" ] && tail -n 5 "$LOG"
        ;;
    esac
    ;;
  Linux)
    UNIT="$HOME/.config/systemd/user/any-tv-art.service"
    case "$ACTION" in
      install)
        mkdir -p "$(dirname "$UNIT")"
        printf '[Unit]\nDescription=any-tv-art bridge\nAfter=network-online.target\n\n[Service]\nWorkingDirectory=%s\nExecStart="%s" --config "%s" bridge\nRestart=always\nRestartSec=30\n\n[Install]\nWantedBy=default.target\n' \
          "$ROOT" "$BIN" "$CONFIG" > "$UNIT"
        systemctl --user daemon-reload
        systemctl --user enable --now any-tv-art.service && echo "On. Log: journalctl --user -u any-tv-art"
        echo "So it also runs when nobody is logged in: sudo loginctl enable-linger $USER"
        ;;
      remove)
        systemctl --user disable --now any-tv-art.service 2> /dev/null
        rm -f "$UNIT"
        systemctl --user daemon-reload
        echo "Off."
        ;;
      *)
        systemctl --user is-active any-tv-art.service > /dev/null 2>&1 && echo "On (systemd user service)" || echo "Off"
        journalctl --user -u any-tv-art -n 5 --no-pager 2> /dev/null
        ;;
    esac
    ;;
  *)
    echo "This script knows macOS and Linux."
    exit 1
    ;;
esac
