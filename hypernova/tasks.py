"""Open window tracking (via libwnck) and the task buttons built on it."""

from . import apps, system
from .gtk import GLib, GObject, Gtk, Wnck
from .util import add_class, image, menu_item, popup_menu, set_class

TASK_TYPES = (Wnck.WindowType.NORMAL, Wnck.WindowType.DIALOG)
SHELL_CLASS = "hypernova-shell"


class Group:
    """Windows of one application, optionally tied to a .desktop entry."""

    def __init__(self, key, app=None, pinned=False):
        self.key = key
        self.app = app
        self.pinned = pinned
        self.windows = []

    @property
    def name(self):
        if self.app is not None:
            return self.app.name
        if self.windows:
            return self.windows[0].get_class_group_name() or self.windows[0].get_name()
        return self.key

    @property
    def active(self):
        return any(w.is_active() for w in self.windows)


class TaskModel(GObject.Object):
    """Wraps Wnck.Screen and coalesces its many signals into one "changed"."""

    __gsignals__ = {"changed": (GObject.SignalFlags.RUN_FIRST, None, ())}

    def __init__(self):
        super().__init__()
        self.screen = Wnck.Screen.get_default()
        self.screen.force_update()
        self._window_handlers = {}
        self._pending = 0
        self._app_cache = None
        self._screen_handlers = [
            self.screen.connect("window-opened", self._on_opened),
            self.screen.connect("window-closed", self._on_closed),
            self.screen.connect("active-window-changed", lambda *_: self._queue()),
        ]
        for win in self.screen.get_windows():
            self._watch(win)

    def destroy(self):
        for handler in self._screen_handlers:
            self.screen.disconnect(handler)
        for win, handlers in self._window_handlers.items():
            for handler in handlers:
                win.disconnect(handler)
        self._window_handlers.clear()
        if self._pending:
            GLib.source_remove(self._pending)

    def _watch(self, win):
        self._window_handlers[win] = [
            win.connect(signal, lambda *_: self._queue())
            for signal in ("name-changed", "icon-changed", "state-changed")
        ]

    def _on_opened(self, _screen, win):
        self._watch(win)
        self._queue()

    def _on_closed(self, _screen, win):
        for handler in self._window_handlers.pop(win, []):
            win.disconnect(handler)
        self._queue()

    def _queue(self):
        if not self._pending:
            self._pending = GLib.timeout_add(40, self._flush)

    def _flush(self):
        self._pending = 0
        self.emit("changed")
        return GLib.SOURCE_REMOVE

    def windows(self):
        result = []
        for win in self.screen.get_windows():
            if win.is_skip_tasklist() or win.get_window_type() not in TASK_TYPES:
                continue
            if (win.get_class_instance_name() or "").lower() == SHELL_CLASS:
                continue
            result.append(win)
        return result

    def active_window(self):
        win = self.screen.get_active_window()
        if win is None or win.get_window_type() == Wnck.WindowType.DESKTOP:
            return None
        if (win.get_class_instance_name() or "").lower() == SHELL_CLASS:
            return None
        return win

    def _app_for(self, win):
        if self._app_cache is None:
            self._app_cache = apps.all_apps()
        keys = {(win.get_class_group_name() or "").lower(), (win.get_class_instance_name() or "").lower()}
        keys.discard("")
        for attr in ("keys", "weak_keys"):
            for app in self._app_cache:
                if getattr(app, attr) & keys:
                    return app
        return None

    def invalidate_apps(self):
        self._app_cache = None

    def groups(self, pinned_ids):
        groups, by_key = [], {}
        for app_id in pinned_ids:
            app = apps.find(app_id)
            if app is None:
                continue
            group = Group(app.id, app, pinned=True)
            groups.append(group)
            by_key[app.id] = group
        for win in self.windows():
            app = self._app_for(win)
            key = app.id if app is not None else (win.get_class_group_name() or win.get_name())
            group = by_key.get(key)
            if group is None:
                group = by_key[key] = Group(key, app)
                groups.append(group)
            group.windows.append(win)
        return groups

    def toggle_showing_desktop(self):
        self.screen.toggle_showing_desktop(not self.screen.get_showing_desktop())


def toggle_window(win, widget):
    if win.is_active() and not win.is_minimized():
        win.minimize()
    else:
        win.activate(system_time(widget))


def system_time(widget):
    from .util import event_time
    return event_time(widget)


def window_icon(win, size):
    pixbuf = win.get_icon() if size > 16 else win.get_mini_icon()
    return image(pixbuf, size) if pixbuf is not None else image("application-x-executable", size)


def group_icon(group, size):
    if group.app is not None and group.app.icon is not None:
        return image(group.app.icon, size)
    if group.windows:
        return window_icon(group.windows[0], size)
    return image("application-x-executable", size)


def window_list_menu(group, widget):
    menu = Gtk.Menu()
    for win in group.windows:
        item = Gtk.MenuItem()
        box = Gtk.Box(spacing=8)
        box.pack_start(window_icon(win, 16), False, False, 0)
        label = Gtk.Label(label=win.get_name(), xalign=0)
        label.set_max_width_chars(48)
        label.set_ellipsize(3)
        box.pack_start(label, True, True, 0)
        item.add(box)
        item.connect("activate", lambda _i, w=win: w.activate(system_time(widget)))
        menu.append(item)
    return menu


def group_context_menu(shell, group, widget, container_word="görev çubuğuna"):
    menu = Gtk.Menu()
    if group.app is not None:
        menu.append(menu_item(group.app.name, lambda: system.launch_app(group.app), group.app.icon))
        menu.append(Gtk.SeparatorMenuItem())
        if shell.is_pinned(group.app.id):
            menu.append(menu_item("Sabitlemeyi kaldır", lambda: shell.set_pinned(group.app.id, False)))
        else:
            menu.append(menu_item(f"{container_word.capitalize()} sabitle", lambda: shell.set_pinned(group.app.id, True)))
    if group.windows:
        if len(group.windows) == 1:
            win = group.windows[0]
            menu.append(Gtk.SeparatorMenuItem())
            menu.append(menu_item("Simge durumuna küçült", win.minimize))
            menu.append(menu_item("Ekranı kapla" if not win.is_maximized() else "Önceki boyut",
                                  lambda: win.unmaximize() if win.is_maximized() else win.maximize()))
            menu.append(menu_item("Pencereyi kapat", lambda: win.close(system_time(widget)), "window-close"))
        else:
            menu.append(Gtk.SeparatorMenuItem())
            menu.append(menu_item("Tüm pencereleri kapat",
                                  lambda: [w.close(system_time(widget)) for w in list(group.windows)], "window-close"))
    return menu


def activate_group(group, widget, event=None):
    if not group.windows:
        if group.app is not None:
            system.launch_app(group.app)
        return
    if len(group.windows) == 1:
        toggle_window(group.windows[0], widget)
        return
    popup_menu(window_list_menu(group, widget), widget, event)


class GroupButton(Gtk.Button):
    """Icon-only task button used by the 7/10 taskbars and the Mac dock."""

    def __init__(self, shell, group, icon_size, css_class, container_word):
        super().__init__()
        self.group = group
        add_class(self, css_class)
        self.set_relief(Gtk.ReliefStyle.NONE)
        self.set_tooltip_text(group.name if len(group.windows) < 2 else f"{group.name} ({len(group.windows)} pencere)")
        overlay = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        overlay.pack_start(group_icon(group, icon_size), True, True, 0)
        indicator = add_class(Gtk.Box(), "indicator")
        indicator.set_halign(Gtk.Align.CENTER)
        overlay.pack_start(indicator, False, False, 0)
        self.add(overlay)
        set_class(self, "running", bool(group.windows))
        set_class(self, "active", group.active)
        set_class(self, "multi", len(group.windows) > 1)
        self.connect("clicked", lambda b: activate_group(group, b))
        self.connect("button-press-event", self._on_press, shell, container_word)

    def _on_press(self, widget, event, shell, container_word):
        if event.button == 3:
            popup_menu(group_context_menu(shell, self.group, widget, container_word), widget, event)
            return True
        if event.button == 2 and self.group.app is not None:
            system.launch_app(self.group.app)
            return True
        return False


class WindowButton(Gtk.ToggleButton):
    """Icon + title task button used by the XP taskbar."""

    def __init__(self, shell, win, width):
        super().__init__()
        self.win = win
        add_class(self, "hn-task")
        self.set_relief(Gtk.ReliefStyle.NONE)
        box = Gtk.Box(spacing=6)
        box.pack_start(window_icon(win, 16), False, False, 0)
        label = Gtk.Label(label=win.get_name(), xalign=0)
        label.set_ellipsize(3)
        box.pack_start(label, True, True, 0)
        self.add(box)
        self.set_size_request(width, -1)
        self.set_tooltip_text(win.get_name())
        self.set_active(win.is_active() and not win.is_minimized())
        set_class(self, "minimized", win.is_minimized())
        self.connect("button-release-event", self._on_release)
        self.connect("button-press-event", self._on_press, shell)

    def _on_release(self, widget, event):
        if event.button == 1:
            toggle_window(self.win, widget)
            return True
        return False

    def _on_press(self, widget, event, shell):
        if event.button == 3:
            group = Group(self.win.get_class_group_name() or "", None)
            group.windows = [self.win]
            popup_menu(group_context_menu(shell, group, widget), widget, event)
            return True
        return event.button == 1
