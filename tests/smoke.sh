#!/bin/sh
# Headless smoke test: runs the shell in every style (and the settings app)
# on a virtual X server with Openbox, and fails on any Python traceback.
# Needs: Xvfb, openbox, dbus-run-session, python-gobject, GTK3, libwnck3.
set -u
cd "$(dirname "$0")/.."
PYTHON="${PYTHON:-python3}"
TMP="$(mktemp -d)"
export HOME="$TMP" XDG_CONFIG_HOME="$TMP/config" XDG_DATA_HOME="$TMP/data" XDG_CACHE_HOME="$TMP/cache"
export PYTHONPATH="$PWD" NO_AT_BRIDGE=1 DISPLAY=:77

Xvfb :77 -screen 0 1280x800x24 >/dev/null 2>&1 &
XVFB=$!
trap 'kill $XVFB 2>/dev/null; rm -rf "$TMP"' EXIT
sleep 1
openbox >/dev/null 2>&1 &
sleep 1

fail=0
check() {
    if grep -q "Traceback" "$TMP/log"; then
        echo "FAIL: $1"; cat "$TMP/log"; fail=1
    else
        echo "ok:   $1"
    fi
}

for style in xp win7 win10 mac; do
    mkdir -p "$XDG_CONFIG_HOME/hypernova"
    printf '{"style": "%s"}\n' "$style" > "$XDG_CONFIG_HOME/hypernova/settings.json"
    dbus-run-session -- sh -c "
        timeout 8 $PYTHON -m hypernova &
        sleep 3
        $PYTHON -m hypernova --toggle-menu; sleep 1
        $PYTHON -m hypernova --toggle-menu; sleep 1
        $PYTHON -m hypernova --rebuild; sleep 1
        wait" >"$TMP/log" 2>&1
    check "shell ($style)"
done

dbus-run-session -- timeout 4 $PYTHON -m hypernova settings >"$TMP/log" 2>&1
check "settings app"
$PYTHON -m hypernova --write-openbox-config >"$TMP/log" 2>&1
check "openbox config"

exit $fail
