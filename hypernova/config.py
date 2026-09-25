"""Persistent user settings (~/.config/hypernova/settings.json)."""

import json
import os

from .gtk import Gio, GLib, GObject

CONFIG_DIR = os.path.join(GLib.get_user_config_dir(), "hypernova")
SETTINGS_PATH = os.path.join(CONFIG_DIR, "settings.json")

DEFAULTS = {
    "style": "win10",
    # "" uses the style's own wallpaper, "builtin:<id>" a generated one,
    # anything else is an image path.
    "wallpaper": "",
    "clock_24h": True,
    "show_seconds": False,
    # None means "not customised yet": sensible defaults are picked at runtime.
    "pinned": None,
    "desktop_icons": True,
}


def _read():
    try:
        with open(SETTINGS_PATH, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


class Settings(GObject.Object):
    """Settings store; with watch=True it also reloads on external edits."""

    __gsignals__ = {"changed": (GObject.SignalFlags.RUN_FIRST, None, (object,))}

    def __init__(self, watch=False):
        super().__init__()
        self._data = {**DEFAULTS, **_read()}
        self._monitor = None
        self._reload_id = 0
        if watch:
            os.makedirs(CONFIG_DIR, exist_ok=True)
            gfile = Gio.File.new_for_path(SETTINGS_PATH)
            self._monitor = gfile.monitor_file(Gio.FileMonitorFlags.WATCH_MOVES, None)
            self._monitor.connect("changed", self._on_file_changed)

    def __getitem__(self, key):
        return self._data.get(key, DEFAULTS.get(key))

    def update(self, **values):
        changed = {key for key, value in values.items() if self._data.get(key) != value}
        if not changed:
            return
        self._data.update(values)
        self._write()
        self.emit("changed", changed)

    def _write(self):
        os.makedirs(CONFIG_DIR, exist_ok=True)
        tmp = SETTINGS_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(self._data, fh, indent=2, ensure_ascii=False)
        os.replace(tmp, SETTINGS_PATH)

    def _on_file_changed(self, *_args):
        if self._reload_id:
            GLib.source_remove(self._reload_id)
        self._reload_id = GLib.timeout_add(150, self._reload)

    def _reload(self):
        self._reload_id = 0
        fresh = {**DEFAULTS, **_read()}
        changed = {key for key in fresh.keys() | self._data.keys() if fresh.get(key) != self._data.get(key)}
        if changed:
            self._data = fresh
            self.emit("changed", changed)
        return GLib.SOURCE_REMOVE
