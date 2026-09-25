"""Session and system actions: launching, power, opening places."""

import os
import sys

from . import apps
from .gtk import Gdk, Gio, GLib, Gtk

PACKAGE_PARENT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def spawn(argv, env=None):
    envp = None
    if env:
        merged = {**os.environ, **env}
        envp = [f"{k}={v}" for k, v in merged.items()]
    try:
        GLib.spawn_async(argv, envp=envp, flags=GLib.SpawnFlags.SEARCH_PATH)
        return True
    except GLib.Error as err:
        error_dialog(f"“{argv[0]}” çalıştırılamadı", err.message)
        return False


def run_command_line(cmdline):
    try:
        GLib.spawn_command_line_async(cmdline)
        return True
    except GLib.Error as err:
        error_dialog("Komut çalıştırılamadı", err.message)
        return False


def hypernova_command(*args):
    """Runs another HyperNova entry point with the same interpreter and package."""
    return spawn([sys.executable, "-m", "hypernova", *args], env={"PYTHONPATH": PACKAGE_PARENT})


def launch_app(app):
    try:
        app.launch()
    except GLib.Error as err:
        error_dialog(f"{app.name} başlatılamadı", err.message)


def open_uri(uri):
    ctx = Gdk.Display.get_default().get_app_launch_context()
    try:
        Gio.AppInfo.launch_default_for_uri(uri, ctx)
        return True
    except GLib.Error:
        pass
    manager = apps.first_available(apps.FILE_MANAGERS)
    if manager is not None and uri.startswith("file://"):
        manager.info.launch_uris([uri], ctx)
        return True
    error_dialog("Konum açılamadı", f"{uri} için bir uygulama bulunamadı.")
    return False


def open_path(path):
    return open_uri(Gio.File.new_for_path(os.path.expanduser(path)).get_uri())


def open_user_dir(kind):
    path = GLib.get_user_special_dir(kind) or GLib.get_home_dir()
    return open_path(path)


def open_trash():
    manager = apps.first_available(apps.FILE_MANAGERS)
    if manager is not None:
        try:
            manager.info.launch_uris(["trash:///"], Gdk.Display.get_default().get_app_launch_context())
            return True
        except GLib.Error:
            pass
    return open_path(os.path.join(GLib.get_user_data_dir(), "Trash", "files"))


def open_terminal():
    app = apps.first_available(apps.TERMINALS)
    if app is not None:
        launch_app(app)
    elif not spawn(["x-terminal-emulator"]):
        spawn(["xterm"])


def open_settings(page=None):
    return hypernova_command("settings", *([page] if page else []))


def logout():
    spawn(["openbox", "--exit"])


def power(action):
    if action == "logout":
        logout()
    elif action in ("poweroff", "reboot", "suspend"):
        spawn(["systemctl", action])
    elif action == "lock":
        spawn(["loginctl", "lock-session"])


def user_display_name():
    return GLib.get_real_name() if GLib.get_real_name() not in ("", "Unknown") else GLib.get_user_name()


def error_dialog(title, detail):
    dialog = Gtk.MessageDialog(message_type=Gtk.MessageType.ERROR, buttons=Gtk.ButtonsType.CLOSE, text=title)
    dialog.format_secondary_text(detail)
    dialog.set_title("HyperNova")
    dialog.connect("response", lambda d, _r: d.destroy())
    dialog.show()


def read_battery():
    base = "/sys/class/power_supply"
    try:
        names = sorted(os.listdir(base))
    except OSError:
        return None
    for name in names:
        if not name.startswith("BAT"):
            continue
        try:
            with open(os.path.join(base, name, "capacity")) as fh:
                level = int(fh.read().strip())
            with open(os.path.join(base, name, "status")) as fh:
                status = fh.read().strip()
        except (OSError, ValueError):
            continue
        return level, status in ("Charging", "Full")
    return None
