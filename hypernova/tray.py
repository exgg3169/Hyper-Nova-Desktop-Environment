"""Notification-area widgets: clock, volume, network and battery."""

import shutil
import subprocess

from . import system
from .gtk import GLib, Gtk
from .util import TR_DAYS, TR_DAYS_SHORT, TR_MONTHS, add_class, image


def _popover(relative_to, child):
    pop = Gtk.Popover.new(relative_to)
    add_class(pop, "hn-popover")
    child.set_margin_top(10)
    child.set_margin_bottom(10)
    child.set_margin_start(10)
    child.set_margin_end(10)
    pop.add(child)
    return pop


class Clock(Gtk.Button):
    def __init__(self, settings, mode="stacked"):
        super().__init__()
        self.settings = settings
        self.mode = mode
        add_class(self, "hn-tray-btn", "hn-clock")
        self.set_relief(Gtk.ReliefStyle.NONE)
        self.label = Gtk.Label()
        self.label.set_justify(Gtk.Justification.CENTER)
        self.add(self.label)
        self.connect("clicked", self._show_calendar)
        self._timer = GLib.timeout_add_seconds(1, self._tick)
        self.connect("destroy", lambda *_: GLib.source_remove(self._timer))
        self._tick()

    def _time_text(self, now):
        fmt = "%H:%M" if self.settings["clock_24h"] else "%I:%M %p"
        if self.settings["show_seconds"]:
            fmt = fmt.replace("%M", "%M:%S")
        return now.format(fmt)

    def _tick(self):
        now = GLib.DateTime.new_now_local()
        time_text = self._time_text(now)
        date_text = f"{now.get_day_of_month():02d}.{now.get_month():02d}.{now.get_year()}"
        if self.mode == "stacked":
            self.label.set_text(f"{time_text}\n{date_text}")
        elif self.mode == "mac":
            day = TR_DAYS_SHORT[now.get_day_of_week() - 1]
            self.label.set_text(f"{day} {now.get_day_of_month()} {TR_MONTHS[now.get_month() - 1][:3]}  {time_text}")
        else:
            self.label.set_text(time_text)
        self.set_tooltip_text(
            f"{TR_DAYS[now.get_day_of_week() - 1]}, {now.get_day_of_month()} "
            f"{TR_MONTHS[now.get_month() - 1]} {now.get_year()}")
        return GLib.SOURCE_CONTINUE

    def _show_calendar(self, *_):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        now = GLib.DateTime.new_now_local()
        title = add_class(Gtk.Label(label=f"{TR_DAYS[now.get_day_of_week() - 1]}, {now.get_day_of_month()} "
                                          f"{TR_MONTHS[now.get_month() - 1]} {now.get_year()}"), "hn-popover-title")
        box.pack_start(title, False, False, 0)
        box.pack_start(Gtk.Calendar(), False, False, 0)
        _popover(self, box).show_all()


class Volume(Gtk.Button):
    """Master volume through wpctl (PipeWire) or pactl (PulseAudio)."""

    def __init__(self, size):
        super().__init__()
        add_class(self, "hn-tray-btn")
        self.set_relief(Gtk.ReliefStyle.NONE)
        self.size = size
        self.set_tooltip_text("Ses")
        self._icon = None
        self._refresh_icon()
        self.connect("clicked", self._show)

    @staticmethod
    def available():
        return bool(shutil.which("wpctl") or shutil.which("pactl"))

    @staticmethod
    def get_level():
        try:
            if shutil.which("wpctl"):
                out = subprocess.run(["wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@"],
                                     capture_output=True, text=True, timeout=2).stdout
                parts = out.split()
                return int(float(parts[1]) * 100), "MUTED" in out
            out = subprocess.run(["pactl", "get-sink-volume", "@DEFAULT_SINK@"],
                                 capture_output=True, text=True, timeout=2).stdout
            level = int(out.split("/")[1].strip().rstrip("%"))
            muted = "yes" in subprocess.run(["pactl", "get-sink-mute", "@DEFAULT_SINK@"],
                                            capture_output=True, text=True, timeout=2).stdout
            return level, muted
        except (OSError, IndexError, ValueError, subprocess.SubprocessError):
            return None, False

    @staticmethod
    def set_level(level):
        if shutil.which("wpctl"):
            system.spawn(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", f"{level / 100:.2f}"])
        else:
            system.spawn(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{level}%"])

    @staticmethod
    def toggle_mute():
        if shutil.which("wpctl"):
            system.spawn(["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "toggle"])
        else:
            system.spawn(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "toggle"])

    def _refresh_icon(self, level=None, muted=False):
        if level is None:
            level, muted = self.get_level()
        if muted or level == 0:
            name = "audio-volume-muted-symbolic"
        elif level is None or level > 66:
            name = "audio-volume-high-symbolic"
        elif level > 33:
            name = "audio-volume-medium-symbolic"
        else:
            name = "audio-volume-low-symbolic"
        if self._icon is not None:
            self._icon.destroy()
        self._icon = image(name, self.size)
        self.add(self._icon)
        self._icon.show()

    def _show(self, *_):
        level, muted = self.get_level()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.pack_start(add_class(Gtk.Label(label="Ses düzeyi"), "hn-popover-title"), False, False, 0)
        scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
        scale.set_size_request(220, -1)
        scale.set_value(level or 0)
        scale.connect("value-changed", lambda s: (self.set_level(int(s.get_value())),
                                                  self._refresh_icon(int(s.get_value()), False)))
        box.pack_start(scale, False, False, 0)
        mute = Gtk.CheckButton(label="Sesi kapat")
        mute.set_active(muted)
        mute.connect("toggled", lambda *_: self.toggle_mute())
        box.pack_start(mute, False, False, 0)
        _popover(self, box).show_all()


class Network(Gtk.Button):
    def __init__(self, size):
        super().__init__()
        add_class(self, "hn-tray-btn")
        self.set_relief(Gtk.ReliefStyle.NONE)
        self.size = size
        self._icon = None
        self._timer = GLib.timeout_add_seconds(10, self._refresh)
        self.connect("destroy", lambda *_: GLib.source_remove(self._timer))
        self.connect("clicked", self._open)
        self._refresh()

    @staticmethod
    def available():
        return bool(shutil.which("nmcli"))

    def _refresh(self):
        try:
            state = subprocess.run(["nmcli", "-t", "-f", "STATE", "general"],
                                   capture_output=True, text=True, timeout=2).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            state = ""
        online = state.startswith("connected")
        self.set_tooltip_text("İnternet erişimi var" if online else "Bağlı değil")
        if self._icon is not None:
            self._icon.destroy()
        self._icon = image("network-wired-symbolic" if online else "network-offline-symbolic", self.size)
        self.add(self._icon)
        self._icon.show()
        return GLib.SOURCE_CONTINUE

    def _open(self, *_):
        if shutil.which("nm-connection-editor"):
            system.spawn(["nm-connection-editor"])
        elif shutil.which("nmtui"):
            system.open_terminal()


class Battery(Gtk.Box):
    def __init__(self, size):
        super().__init__(spacing=4)
        add_class(self, "hn-battery")
        self.size = size
        self._icon = None
        self.label = Gtk.Label()
        self.pack_end(self.label, False, False, 0)
        self._timer = GLib.timeout_add_seconds(30, self._refresh)
        self.connect("destroy", lambda *_: GLib.source_remove(self._timer))
        self._refresh()

    @staticmethod
    def available():
        return system.read_battery() is not None

    def _refresh(self):
        info = system.read_battery()
        if info is None:
            return GLib.SOURCE_CONTINUE
        level, charging = info
        step = min(100, (level + 5) // 10 * 10)
        name = f"battery-level-{step}{'-charging' if charging else ''}-symbolic"
        if self._icon is not None:
            self._icon.destroy()
        self._icon = image(name, self.size)
        self.pack_start(self._icon, False, False, 0)
        self._icon.show()
        self.label.set_text(f"%{level}")
        self.set_tooltip_text(f"Pil: %{level}{' (şarj oluyor)' if charging else ''}")
        return GLib.SOURCE_CONTINUE


def build(settings, clock_mode, icon_size=16):
    box = add_class(Gtk.Box(spacing=2), "hn-tray")
    if Network.available():
        box.pack_start(Network(icon_size), False, False, 0)
    if Volume.available():
        box.pack_start(Volume(icon_size), False, False, 0)
    if Battery.available():
        box.pack_start(Battery(icon_size), False, False, 0)
    box.pack_start(Clock(settings, clock_mode), False, False, 0)
    return box
