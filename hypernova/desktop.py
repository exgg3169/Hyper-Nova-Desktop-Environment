"""The desktop surface: wallpaper, desktop icons and the desktop menu."""

from . import dialogs, styles, system, wallpapers
from .gtk import Gdk, Gtk, Pango
from .util import add_class, image, menu_item, popup_menu


class DesktopIcon(Gtk.EventBox):
    def __init__(self, label, icon, callback):
        super().__init__()
        self.set_visible_window(False)
        add_class(self, "hn-desktop-icon")
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        box.pack_start(image(icon, 48), False, False, 0)
        text = Gtk.Label(label=label)
        text.set_line_wrap(True)
        text.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        text.set_justify(Gtk.Justification.CENTER)
        text.set_max_width_chars(12)
        box.pack_start(text, False, False, 0)
        box.set_size_request(86, 80)
        self.add(box)
        self.callback = callback
        self.connect("button-press-event", self._on_press)

    def _on_press(self, _w, event):
        if event.button == 1 and event.type == Gdk.EventType._2BUTTON_PRESS:
            self.callback()
            return True
        if event.button == 1:
            parent = self.get_parent()
            for sibling in parent.get_children():
                sibling.get_style_context().remove_class("selected")
            self.get_style_context().add_class("selected")
            return True
        return False


class DesktopWindow(Gtk.Window):
    def __init__(self, shell):
        super().__init__(title="HyperNova Masaüstü")
        self.shell = shell
        self.set_name("hn-desktop")
        self.set_type_hint(Gdk.WindowTypeHint.DESKTOP)
        self.set_decorated(False)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)
        self.set_keep_below(True)
        self.set_role("hn-desktop")
        self.stick()
        screen = self.get_screen()
        self.set_size_request(screen.get_width(), screen.get_height())
        self.move(0, 0)
        self._cache = None
        self._spec = wallpapers.resolve(shell.settings["wallpaper"], shell.style)

        overlay = Gtk.Overlay()
        area = Gtk.DrawingArea()
        area.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        area.connect("draw", self._draw)
        area.connect("button-press-event", self._on_press)
        overlay.add(area)
        if shell.settings["desktop_icons"]:
            overlay.add_overlay(self._icons())
        self.add(overlay)

    def _icons(self):
        style = self.shell.style
        geo = self.shell.monitor
        box = add_class(Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8), "hn-desktop-icons")
        box.set_valign(Gtk.Align.START)
        top = geo.y + (style.panel_height if style.layout == "mac" else 0) + 12
        box.set_margin_top(top)
        if style.layout == "mac":
            box.set_halign(Gtk.Align.END)
            box.set_margin_end(self.get_screen().get_width() - (geo.x + geo.width) + 12)
        else:
            box.set_halign(Gtk.Align.START)
            box.set_margin_start(geo.x + 12)
        entries = [
            (style.computer_label, "computer", lambda: system.open_path("/")),
            (style.home_label, "user-home", lambda: system.open_path("~")),
            (style.trash_label, "user-trash", system.open_trash),
            ("Terminal", "utilities-terminal", system.open_terminal),
            ("HyperNova Ayarları", "preferences-system", system.open_settings),
        ]
        for label, icon, callback in entries:
            box.pack_start(DesktopIcon(label, icon, callback), False, False, 0)
        return box

    def _draw(self, widget, cr):
        width, height = widget.get_allocated_width(), widget.get_allocated_height()
        if self._cache is None or self._cache.get_width() != width or self._cache.get_height() != height:
            self._cache = wallpapers.render_surface(width, height, self._spec)
        cr.set_source_surface(self._cache, 0, 0)
        cr.paint()
        return False

    def _on_press(self, widget, event):
        self.shell.close_popups()
        if event.button != 3:
            return False
        menu = Gtk.Menu()
        style_item = menu_item("Masaüstü stili")
        sub = Gtk.Menu()
        group = None
        for style_id in styles.ORDER:
            s = styles.STYLES[style_id]
            item = Gtk.RadioMenuItem.new_with_label_from_widget(group, s.name)
            group = item
            item.set_active(s.id == self.shell.style.id)
            item.connect("activate", lambda i, sid=s.id: i.get_active() and self.shell.settings.update(style=sid))
            sub.append(item)
        style_item.set_submenu(sub)
        menu.append(style_item)
        menu.append(menu_item("Duvar kağıdını değiştir…", lambda: system.open_settings("wallpaper")))
        menu.append(Gtk.SeparatorMenuItem())
        menu.append(menu_item("Terminal aç", system.open_terminal, "utilities-terminal"))
        menu.append(menu_item("Çalıştır…", lambda: dialogs.RunDialog(self.shell.style), "system-run"))
        menu.append(menu_item("HyperNova Ayarları", system.open_settings, "preferences-desktop"))
        popup_menu(menu, None, event)
        return True
