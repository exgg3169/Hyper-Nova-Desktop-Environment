"""The HyperNova shell process: owns every desktop surface of the session."""

from . import apps, dialogs, openbox, paths, startmenu, styles, system
from .config import Settings
from .desktop import DesktopWindow
from .gtk import Gdk, Gio, GLib, Gtk, Wnck
from .mac import Dock, MenuBar
from .taskbar import Taskbar
from .tasks import TaskModel
from .util import primary_monitor_geometry

COMMANDS = ("--toggle-menu", "--search", "--run", "--terminal", "--open-home", "--power", "--rebuild")


class StyleSheets:
    def __init__(self):
        self.providers = []

    def load(self, style):
        screen = Gdk.Screen.get_default()
        for provider in self.providers:
            Gtk.StyleContext.remove_provider_for_screen(screen, provider)
        self.providers = []
        for offset, name in enumerate(("common.css", f"{style.id}.css")):
            provider = Gtk.CssProvider()
            try:
                provider.load_from_path(paths.data_file("styles", name))
            except GLib.Error as err:
                print(f"hypernova: {name}: {err.message}")
                continue
            Gtk.StyleContext.add_provider_for_screen(
                screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + offset)
            self.providers.append(provider)


class Shell:
    def __init__(self, app):
        self.app = app
        self.settings = Settings(watch=True)
        self.settings.connect("changed", self._on_settings_changed)
        self.sheets = StyleSheets()
        self.tasks = TaskModel()
        self.surfaces = []
        self.menu = None
        self._default_pinned = None
        self._rebuild_id = 0
        self._style_id = self.settings["style"]

        screen = Gdk.Screen.get_default()
        screen.connect("monitors-changed", lambda *_: self.queue_rebuild())
        screen.connect("size-changed", lambda *_: self.queue_rebuild())
        screen.connect("composited-changed", lambda *_: self.queue_rebuild())
        self._app_monitor = Gio.AppInfoMonitor.get()
        self._app_monitor.connect("changed", self._on_apps_changed)
        self.build()

    @property
    def style(self):
        return styles.get(self.settings["style"])

    @property
    def monitor(self):
        return primary_monitor_geometry()

    # --- lifecycle --------------------------------------------------------------

    def build(self):
        style = self.style
        self.sheets.load(style)
        self.surfaces = [DesktopWindow(self)]
        if style.layout == "mac":
            self.surfaces += [MenuBar(self), Dock(self)]
        else:
            self.surfaces.append(Taskbar(self))
        self.menu = startmenu.create(self)
        for surface in self.surfaces:
            surface.show_all()

    def teardown(self):
        for surface in self.surfaces:
            surface.destroy()
        self.surfaces = []
        if self.menu is not None:
            self.menu.destroy()
            self.menu = None

    def queue_rebuild(self):
        if not self._rebuild_id:
            self._rebuild_id = GLib.timeout_add(200, self._rebuild)

    def _rebuild(self):
        self._rebuild_id = 0
        self.teardown()
        self.build()
        return GLib.SOURCE_REMOVE

    def _on_settings_changed(self, _settings, keys):
        if "style" in keys and self.settings["style"] != self._style_id:
            self._style_id = self.settings["style"]
            openbox.write_config(self.style)
            openbox.reconfigure()
        self.queue_rebuild()

    def _on_apps_changed(self, *_):
        self._default_pinned = None
        self.tasks.invalidate_apps()
        self.queue_rebuild()

    # --- pinned applications --------------------------------------------------

    def pinned_ids(self):
        pinned = self.settings["pinned"]
        if pinned is not None:
            return list(pinned)
        if self._default_pinned is None:
            self._default_pinned = apps.default_pinned()
        return list(self._default_pinned)

    def is_pinned(self, app_id):
        return app_id in self.pinned_ids()

    def set_pinned(self, app_id, pinned):
        ids = [i for i in self.pinned_ids() if i != app_id]
        if pinned:
            ids.append(app_id)
        self.settings.update(pinned=ids)

    # --- actions ------------------------------------------------------------------

    def toggle_menu(self, focus_search=False):
        if self.menu is not None:
            self.menu.toggle(focus_search)

    def close_popups(self):
        if self.menu is not None:
            self.menu.hide_popup()

    def command(self, args):
        if "--rebuild" in args:
            self.queue_rebuild()
        if "--toggle-menu" in args:
            self.toggle_menu()
        if "--search" in args:
            self.toggle_menu(focus_search=True)
        if "--run" in args:
            dialogs.RunDialog(self.style)
        if "--terminal" in args:
            system.open_terminal()
        if "--open-home" in args:
            system.open_path("~")
        if "--power" in args:
            dialogs.PowerDialog(self.style)


class ShellApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="org.hypernova.Shell",
                         flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE)
        self.shell = None

    def do_command_line(self, cmdline):
        args = cmdline.get_arguments()[1:]
        if self.shell is None:
            if any(arg in COMMANDS for arg in args):
                print("hypernova-shell is not running")
                return 1
            Wnck.set_client_type(Wnck.ClientType.PAGER)
            self.hold()
            self.shell = Shell(self)
            return 0
        self.shell.command(args)
        return 0
