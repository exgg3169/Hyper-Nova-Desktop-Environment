"""The Windows-like taskbar used by the XP, 7 and 10 styles."""

import math

from . import apps, logo, system, tray
from .gtk import Gdk, Gtk
from .tasks import GroupButton, WindowButton
from .util import add_class, clear, image, make_shell_window


def _win10_logo(size):
    area = Gtk.DrawingArea()
    area.set_size_request(size, size)

    def draw(widget, cr):
        color = widget.get_style_context().get_color(widget.get_state_flags())
        cr.set_source_rgba(color.red, color.green, color.blue, color.alpha)
        gap = max(1, size // 12)
        half = (size - gap) / 2
        for x in (0, half + gap):
            for y in (0, half + gap):
                cr.rectangle(x, y, half, half)
        cr.fill()
    area.connect("draw", draw)
    return area


def _orb():
    area = Gtk.DrawingArea()
    area.set_size_request(36, 36)

    def draw(_w, cr):
        import cairo
        glow = cairo.RadialGradient(18, 14, 2, 18, 18, 18)
        glow.add_color_stop_rgb(0, 0.55, 0.85, 1.0)
        glow.add_color_stop_rgb(0.6, 0.1, 0.4, 0.75)
        glow.add_color_stop_rgb(1, 0.02, 0.15, 0.35)
        cr.set_source(glow)
        cr.arc(18, 18, 17, 0, 2 * math.pi)
        cr.fill_preserve()
        cr.set_source_rgba(1, 1, 1, 0.55)
        cr.set_line_width(1)
        cr.stroke()
        shine = cairo.LinearGradient(0, 2, 0, 18)
        shine.add_color_stop_rgba(0, 1, 1, 1, 0.55)
        shine.add_color_stop_rgba(1, 1, 1, 1, 0.0)
        cr.set_source(shine)
        cr.save()
        cr.translate(18, 10)
        cr.scale(13, 8)
        cr.arc(0, 0, 1, 0, 2 * math.pi)
        cr.restore()
        cr.fill()
        cr.translate(7, 7)
        logo.draw(cr, 22)
    area.connect("draw", draw)
    return area


class Taskbar(Gtk.Window):
    def __init__(self, shell):
        super().__init__(title="HyperNova Görev Çubuğu")
        self.shell = shell
        style = shell.style
        make_shell_window(self, "hn-panel")
        self.set_name("hn-taskbar")
        add_class(self, f"style-{style.id}")
        self.set_type_hint(Gdk.WindowTypeHint.DOCK)
        self.set_keep_above(True)
        geo = shell.monitor
        self.set_size_request(geo.width, style.panel_height)
        self.move(geo.x, geo.y + geo.height - style.panel_height)

        box = Gtk.Box()
        self.add(box)
        box.pack_start(self._start_button(), False, False, 0)
        if style.id == "win10":
            search = add_class(Gtk.Button(), "hn-taskbar-search")
            search.set_relief(Gtk.ReliefStyle.NONE)
            row = Gtk.Box(spacing=8)
            row.pack_start(image("system-search-symbolic", 16), False, False, 0)
            row.pack_start(Gtk.Label(label="Aramak için buraya yazın", xalign=0), True, True, 0)
            search.add(row)
            search.set_size_request(300, -1)
            search.connect("clicked", lambda *_: shell.toggle_menu(focus_search=True))
            box.pack_start(search, False, False, 0)
        if style.id == "xp":
            quick = add_class(Gtk.Box(spacing=0), "hn-quicklaunch")
            for app in (apps.find(i) for i in shell.pinned_ids()):
                if app is None:
                    continue
                btn = add_class(Gtk.Button(), "hn-quick")
                btn.set_relief(Gtk.ReliefStyle.NONE)
                btn.add(image(app.icon, 16))
                btn.set_tooltip_text(app.name)
                btn.connect("clicked", lambda _b, a=app: system.launch_app(a))
                quick.pack_start(btn, False, False, 0)
            box.pack_start(quick, False, False, 0)

        self.tasks = add_class(Gtk.Box(spacing=3 if style.task_labels else 0), "hn-tasklist")
        box.pack_start(self.tasks, True, True, 0)

        clock_mode = "single" if style.id == "xp" else "stacked"
        box.pack_start(tray.build(shell.settings, clock_mode, 16), False, False, 0)
        if style.id != "xp":
            peek = add_class(Gtk.Button(), "hn-showdesktop")
            peek.set_tooltip_text("Masaüstünü göster")
            peek.connect("clicked", lambda *_: shell.tasks.toggle_showing_desktop())
            box.pack_start(peek, False, False, 0)

        self._handler = shell.tasks.connect("changed", lambda *_: self.refresh())
        self.connect("destroy", lambda *_: shell.tasks.disconnect(self._handler))
        self.refresh()

    def _start_button(self):
        style = self.shell.style
        btn = add_class(Gtk.Button(), "hn-start")
        btn.set_relief(Gtk.ReliefStyle.NONE)
        btn.set_tooltip_text("Başlat")
        if style.id == "xp":
            row = Gtk.Box(spacing=5)
            row.pack_start(Gtk.Image.new_from_pixbuf(logo.pixbuf(22, (1, 1, 1, 0.95))), False, False, 0)
            row.pack_start(add_class(Gtk.Label(label="başlat"), "hn-start-label"), False, False, 0)
            btn.add(row)
        elif style.id == "win7":
            add_class(btn, "hn-start-orb")
            btn.add(_orb())
        else:
            btn.add(_win10_logo(16))
        btn.connect("clicked", lambda *_: self.shell.toggle_menu())
        return btn

    def refresh(self):
        clear(self.tasks)
        style = self.shell.style
        if style.task_labels:
            windows = self.shell.tasks.windows()
            available = self.shell.monitor.width - 420
            width = int(min(170, available / max(1, len(windows))))
            for win in windows:
                self.tasks.pack_start(WindowButton(self.shell, win, width), False, False, 0)
        else:
            for group in self.shell.tasks.groups(self.shell.pinned_ids()):
                btn = GroupButton(self.shell, group, style.task_icon_size, "hn-task-icon", "görev çubuğuna")
                self.tasks.pack_start(btn, False, False, 0)
        self.tasks.show_all()
