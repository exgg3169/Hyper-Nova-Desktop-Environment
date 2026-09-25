"""HyperNova Ayarları: style picker, wallpaper, taskbar and about pages."""

import math
import os
import platform
import socket

import cairo

from . import VERSION, apps, logo, styles, wallpapers
from .config import Settings
from .gtk import Gio, GLib, Gtk
from .util import add_class, clear, human_size, image

CSS = b"""
.hn-card { padding: 8px; border-radius: 10px; border: 2px solid transparent; }
.hn-card:hover { background-color: alpha(@theme_selected_bg_color, 0.12); }
.hn-card.selected { border-color: @theme_selected_bg_color; background-color: alpha(@theme_selected_bg_color, 0.18); }
.hn-page-title { font-size: 20px; font-weight: bold; }
.hn-card-title { font-weight: bold; }
.hn-about-title { font-size: 26px; font-weight: bold; }
"""


def _rounded(cr, x, y, w, h, r):
    cr.new_sub_path()
    cr.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    cr.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    cr.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    cr.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
    cr.close_path()


def _grad(x0, y0, x1, y1, *stops):
    pat = cairo.LinearGradient(x0, y0, x1, y1)
    for offset, rgba in stops:
        pat.add_color_stop_rgba(offset, *rgba)
    return pat


def draw_style_preview(cr, w, h, style):
    """A miniature of the style: wallpaper, a window and the panel layout."""
    wallpapers.paint(cr, w, h, ("builtin", style.wallpaper))
    # a sample window
    wx, wy, ww, wh = w * 0.18, h * 0.16, w * 0.52, h * 0.5
    cr.set_source_rgb(0.97, 0.97, 0.97)
    _rounded(cr, wx, wy, ww, wh, 4 if style.id != "xp" else 2)
    cr.fill()
    title_h = h * 0.07
    if style.id == "xp":
        cr.set_source(_grad(0, wy, 0, wy + title_h, (0, (0.2, 0.5, 0.98, 1)), (1, (0.0, 0.3, 0.85, 1))))
    elif style.id == "win7":
        cr.set_source(_grad(0, wy, 0, wy + title_h, (0, (0.62, 0.78, 0.92, 1)), (1, (0.42, 0.6, 0.8, 1))))
    elif style.id == "win10":
        cr.set_source_rgb(1, 1, 1)
    else:
        cr.set_source_rgb(0.9, 0.9, 0.9)
    cr.rectangle(wx, wy, ww, title_h)
    cr.fill()
    r = title_h * 0.22
    if style.id == "mac":
        for i, color in enumerate(((1, 0.37, 0.34), (1, 0.74, 0.18), (0.16, 0.79, 0.25))):
            cr.set_source_rgb(*color)
            cr.arc(wx + title_h * 0.5 + i * r * 3, wy + title_h / 2, r, 0, 2 * math.pi)
            cr.fill()
    else:
        for i in range(3):
            cr.set_source_rgb(*((0.85, 0.25, 0.2) if i == 0 else ((0.3, 0.3, 0.3) if style.id == "win10" else (1, 1, 1))))
            cr.rectangle(wx + ww - (i + 1) * r * 3.2, wy + title_h / 2 - r, r * 2, r * 2)
            cr.fill()

    if style.layout == "mac":
        cr.set_source_rgba(0.96, 0.96, 0.96, 0.9)
        cr.rectangle(0, 0, w, h * 0.06)
        cr.fill()
        dw, dh = w * 0.5, h * 0.11
        cr.set_source_rgba(0.95, 0.95, 0.97, 0.6)
        _rounded(cr, (w - dw) / 2, h - dh - h * 0.03, dw, dh, dh * 0.3)
        cr.fill()
        colors = [(0.2, 0.6, 1), (1, 0.4, 0.3), (0.3, 0.8, 0.4), (1, 0.75, 0.2), (0.6, 0.4, 0.9), (0.5, 0.5, 0.5)]
        size = dh * 0.7
        for i, color in enumerate(colors):
            cr.set_source_rgb(*color)
            _rounded(cr, (w - dw) / 2 + dh * 0.2 + i * (size + dh * 0.15), h - dh - h * 0.03 + dh * 0.15,
                     size, size, size * 0.25)
            cr.fill()
        return

    bar = h * 0.09
    y = h - bar
    if style.id == "xp":
        cr.set_source(_grad(0, y, 0, h, (0, (0.2, 0.45, 0.88, 1)), (1, (0.1, 0.26, 0.66, 1))))
        cr.rectangle(0, y, w, bar)
        cr.fill()
        cr.set_source(_grad(0, y, 0, h, (0, (0.36, 0.74, 0.34, 1)), (1, (0.17, 0.45, 0.15, 1))))
        _rounded(cr, -bar, y, w * 0.2 + bar, bar, bar / 2)
        cr.fill()
        cr.set_source_rgb(0.08, 0.6, 0.93)
        cr.rectangle(w * 0.82, y, w * 0.18, bar)
        cr.fill()
    elif style.id == "win7":
        cr.set_source(_grad(0, y, 0, h, (0, (0.25, 0.4, 0.55, 0.9)), (1, (0.08, 0.17, 0.27, 0.95))))
        cr.rectangle(0, y, w, bar)
        cr.fill()
        cr.set_source_rgb(0.3, 0.65, 0.95)
        cr.arc(bar * 0.9, y + bar / 2, bar * 0.42, 0, 2 * math.pi)
        cr.fill()
        for i in range(3):
            cr.set_source_rgba(1, 1, 1, 0.25)
            _rounded(cr, bar * 1.8 + i * bar * 1.4, y + bar * 0.12, bar * 1.2, bar * 0.76, 2)
            cr.fill()
    else:
        cr.set_source_rgb(0.06, 0.06, 0.06)
        cr.rectangle(0, y, w, bar)
        cr.fill()
        cr.set_source_rgb(1, 1, 1)
        s = bar * 0.18
        for dx in (0, s * 1.2):
            for dy in (0, s * 1.2):
                cr.rectangle(bar * 0.35 + dx, y + bar * 0.3 + dy, s, s)
        cr.fill()
        cr.set_source_rgb(0.95, 0.95, 0.95)
        cr.rectangle(bar * 1.2, y + bar * 0.12, w * 0.25, bar * 0.76)
        cr.fill()
        for i in range(3):
            cr.set_source_rgb(0.46, 0.73, 0.93)
            cr.rectangle(w * 0.25 + bar * 1.6 + i * bar * 1.3, y + bar * 0.88, bar * 0.9, bar * 0.1)
            cr.fill()


class Card(Gtk.Button):
    def __init__(self, title, subtitle, painter, width=240, height=150):
        super().__init__()
        self.set_relief(Gtk.ReliefStyle.NONE)
        add_class(self, "hn-card")
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        area = Gtk.DrawingArea()
        area.set_size_request(width, height)
        area.connect("draw", lambda widget, cr: self._draw(widget, cr, painter))
        box.pack_start(area, False, False, 0)
        box.pack_start(add_class(Gtk.Label(label=title, xalign=0), "hn-card-title"), False, False, 0)
        if subtitle:
            sub = add_class(Gtk.Label(label=subtitle, xalign=0), "dim-label")
            sub.set_line_wrap(True)
            sub.set_max_width_chars(30)
            box.pack_start(sub, False, False, 0)
        self.add(box)

    @staticmethod
    def _draw(widget, cr, painter):
        w, h = widget.get_allocated_width(), widget.get_allocated_height()
        _rounded(cr, 0, 0, w, h, 8)
        cr.clip()
        painter(cr, w, h)

    def set_selected(self, selected):
        ctx = self.get_style_context()
        (ctx.add_class if selected else ctx.remove_class)("selected")


class SettingsWindow(Gtk.ApplicationWindow):
    def __init__(self, app, page):
        super().__init__(application=app, title="HyperNova Ayarları")
        self.set_default_size(900, 620)
        self.set_icon(logo.pixbuf(64))
        self.settings = Settings()

        provider = Gtk.CssProvider()
        provider.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_screen(self.get_screen(), provider,
                                                 Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        sidebar = Gtk.StackSidebar()
        sidebar.set_stack(self.stack)
        sidebar.set_size_request(200, -1)
        pane = Gtk.Box()
        pane.pack_start(sidebar, False, False, 0)
        pane.pack_start(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL), False, False, 0)
        pane.pack_start(self.stack, True, True, 0)
        self.add(pane)

        self.stack.add_titled(self._page(self._appearance()), "appearance", "Görünüm")
        self.stack.add_titled(self._page(self._wallpaper()), "wallpaper", "Duvar Kağıdı")
        self.stack.add_titled(self._page(self._taskbar()), "taskbar", "Görev Çubuğu ve Dock")
        self.stack.add_titled(self._page(self._about()), "about", "Hakkında")
        self.show_all()
        if page and self.stack.get_child_by_name(page) is not None:
            self.stack.set_visible_child_name(page)

    @staticmethod
    def _page(content):
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        content.set_margin_top(24)
        content.set_margin_bottom(24)
        content.set_margin_start(28)
        content.set_margin_end(28)
        scroll.add(content)
        return scroll

    @staticmethod
    def _title(text, subtitle=None):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        box.pack_start(add_class(Gtk.Label(label=text, xalign=0), "hn-page-title"), False, False, 0)
        if subtitle:
            sub = add_class(Gtk.Label(label=subtitle, xalign=0), "dim-label")
            sub.set_line_wrap(True)
            box.pack_start(sub, False, False, 0)
        return box

    @staticmethod
    def _flow():
        flow = Gtk.FlowBox()
        flow.set_selection_mode(Gtk.SelectionMode.NONE)
        flow.set_homogeneous(True)
        flow.set_max_children_per_line(4)
        flow.set_column_spacing(12)
        flow.set_row_spacing(12)
        flow.set_valign(Gtk.Align.START)
        return flow

    # --- Appearance ------------------------------------------------------------

    def _appearance(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        box.pack_start(self._title("Masaüstü stili",
                                   "HyperNova'nın görünümünü ve düzenini seçin. Değişiklik anında uygulanır."),
                       False, False, 0)
        flow = self._flow()
        self.style_cards = {}
        for style_id in styles.ORDER:
            style = styles.STYLES[style_id]
            card = Card(style.name, style.description, lambda cr, w, h, s=style: draw_style_preview(cr, w, h, s))
            card.connect("clicked", self._pick_style, style_id)
            self.style_cards[style_id] = card
            flow.add(card)
        box.pack_start(flow, False, False, 0)
        self._mark_style()
        hint = add_class(Gtk.Label(xalign=0), "dim-label")
        hint.set_markup("İpucu: masaüstüne sağ tıklayarak da stil değiştirebilirsiniz. "
                        "<b>Ctrl+Esc</b> veya <b>Super+Boşluk</b> Başlat menüsünü açar.")
        hint.set_line_wrap(True)
        box.pack_start(hint, False, False, 0)
        return box

    def _pick_style(self, _card, style_id):
        self.settings.update(style=style_id)
        self._mark_style()

    def _mark_style(self):
        current = styles.get(self.settings["style"]).id
        for style_id, card in self.style_cards.items():
            card.set_selected(style_id == current)

    # --- Wallpaper ----------------------------------------------------------------

    def _wallpaper(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        box.pack_start(self._title("Duvar kağıdı", "Yerleşik bir duvar kağıdı ya da kendi resminizi seçin."),
                       False, False, 0)
        flow = self._flow()
        self.wallpaper_cards = {}
        default = Card("Stilin varsayılanı", None,
                       lambda cr, w, h: wallpapers.paint(cr, w, h, ("builtin", styles.get(self.settings["style"]).wallpaper)),
                       200, 120)
        default.connect("clicked", self._pick_wallpaper, "")
        self.wallpaper_cards[""] = default
        flow.add(default)
        for wp_id, (name, _painter) in wallpapers.BUILTIN.items():
            card = Card(name, None, lambda cr, w, h, i=wp_id: wallpapers.paint(cr, w, h, ("builtin", i)), 200, 120)
            card.connect("clicked", self._pick_wallpaper, f"builtin:{wp_id}")
            self.wallpaper_cards[f"builtin:{wp_id}"] = card
            flow.add(card)
        box.pack_start(flow, False, False, 0)
        row = Gtk.Box(spacing=12)
        choose = Gtk.Button(label="Resim seç…")
        choose.connect("clicked", self._choose_image)
        row.pack_start(choose, False, False, 0)
        self.wallpaper_path = add_class(Gtk.Label(xalign=0), "dim-label")
        row.pack_start(self.wallpaper_path, True, True, 0)
        box.pack_start(row, False, False, 0)
        self._mark_wallpaper()
        return box

    def _pick_wallpaper(self, _card, value):
        self.settings.update(wallpaper=value)
        self._mark_wallpaper()

    def _mark_wallpaper(self):
        current = self.settings["wallpaper"] or ""
        for key, card in self.wallpaper_cards.items():
            card.set_selected(key == current)
        custom = current and not current.startswith("builtin:")
        self.wallpaper_path.set_text(f"Seçili resim: {current}" if custom else "")

    def _choose_image(self, *_):
        dialog = Gtk.FileChooserNative.new("Duvar kağıdı seç", self, Gtk.FileChooserAction.OPEN, "Seç", "İptal")
        image_filter = Gtk.FileFilter()
        image_filter.set_name("Resimler")
        image_filter.add_pixbuf_formats()
        dialog.add_filter(image_filter)
        pictures = GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_PICTURES)
        if pictures and os.path.isdir(pictures):
            dialog.set_current_folder(pictures)
        if dialog.run() == Gtk.ResponseType.ACCEPT:
            self._pick_wallpaper(None, dialog.get_filename())
        dialog.destroy()

    # --- Taskbar ------------------------------------------------------------------

    def _taskbar(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        box.pack_start(self._title("Görev çubuğu ve Dock"), False, False, 0)
        for key, label in (("clock_24h", "Saati 24 saat biçiminde göster"),
                           ("show_seconds", "Saatte saniyeleri göster"),
                           ("desktop_icons", "Masaüstü simgelerini göster")):
            row = Gtk.Box(spacing=12)
            row.pack_start(Gtk.Label(label=label, xalign=0), True, True, 0)
            switch = Gtk.Switch()
            switch.set_active(bool(self.settings[key]))
            switch.connect("notify::active", lambda s, _p, k=key: self.settings.update(**{k: s.get_active()}))
            row.pack_start(switch, False, False, 0)
            box.pack_start(row, False, False, 0)

        box.pack_start(Gtk.Separator(), False, False, 6)
        box.pack_start(self._title("Sabitlenmiş uygulamalar",
                                   "Görev çubuğunda, Dock'ta ve Başlat menüsünde görünen uygulamalar."),
                       False, False, 0)
        self.pinned_box = Gtk.ListBox()
        self.pinned_box.set_selection_mode(Gtk.SelectionMode.NONE)
        box.pack_start(self.pinned_box, False, False, 0)
        add = Gtk.Button(label="Uygulama ekle…")
        add.set_halign(Gtk.Align.START)
        add.connect("clicked", self._add_pinned)
        box.pack_start(add, False, False, 0)
        self._fill_pinned()
        return box

    def _pinned_ids(self):
        pinned = self.settings["pinned"]
        return list(pinned) if pinned is not None else apps.default_pinned()

    def _fill_pinned(self):
        clear(self.pinned_box)
        ids = self._pinned_ids()
        for index, app_id in enumerate(ids):
            app = apps.find(app_id)
            row = Gtk.Box(spacing=10)
            row.set_margin_top(4)
            row.set_margin_bottom(4)
            row.set_margin_start(8)
            row.set_margin_end(8)
            row.pack_start(image(app.icon if app else "application-x-executable", 24), False, False, 0)
            row.pack_start(Gtk.Label(label=app.name if app else f"{app_id} (yüklü değil)", xalign=0), True, True, 0)
            for icon, delta, tip in (("go-up-symbolic", -1, "Yukarı taşı"), ("go-down-symbolic", 1, "Aşağı taşı")):
                btn = Gtk.Button.new_from_icon_name(icon, Gtk.IconSize.BUTTON)
                btn.set_tooltip_text(tip)
                btn.set_sensitive(0 <= index + delta < len(ids))
                btn.connect("clicked", self._move_pinned, index, delta)
                row.pack_start(btn, False, False, 0)
            remove = Gtk.Button.new_from_icon_name("list-remove-symbolic", Gtk.IconSize.BUTTON)
            remove.set_tooltip_text("Kaldır")
            remove.connect("clicked", self._remove_pinned, app_id)
            row.pack_start(remove, False, False, 0)
            self.pinned_box.add(row)
        self.pinned_box.show_all()

    def _move_pinned(self, _btn, index, delta):
        ids = self._pinned_ids()
        ids[index], ids[index + delta] = ids[index + delta], ids[index]
        self.settings.update(pinned=ids)
        self._fill_pinned()

    def _remove_pinned(self, _btn, app_id):
        self.settings.update(pinned=[i for i in self._pinned_ids() if i != app_id])
        self._fill_pinned()

    def _add_pinned(self, *_):
        dialog = Gtk.AppChooserDialog.new_for_content_type(self, Gtk.DialogFlags.MODAL, "application/octet-stream")
        widget = dialog.get_widget()
        widget.set_show_all(True)
        dialog.set_heading("Sabitlenecek uygulamayı seçin")
        if dialog.run() == Gtk.ResponseType.OK:
            info = dialog.get_app_info()
            if info is not None and info.get_id() not in self._pinned_ids():
                self.settings.update(pinned=self._pinned_ids() + [info.get_id()])
                self._fill_pinned()
        dialog.destroy()

    # --- About --------------------------------------------------------------------

    def _about(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_halign(Gtk.Align.CENTER)
        box.pack_start(Gtk.Image.new_from_pixbuf(logo.pixbuf(128)), False, False, 8)
        box.pack_start(add_class(Gtk.Label(label="HyperNova OS"), "hn-about-title"), False, False, 0)
        box.pack_start(add_class(Gtk.Label(label=f"HyperNova Masaüstü {VERSION}"), "dim-label"), False, False, 0)
        grid = Gtk.Grid(column_spacing=18, row_spacing=6)
        grid.set_margin_top(16)
        rows = [
            ("Temel sistem", _os_name()),
            ("Çekirdek", platform.release()),
            ("Bilgisayar adı", socket.gethostname()),
            ("İşlemci", f"{os.cpu_count() or 1} çekirdek · {platform.machine()}"),
            ("Bellek", _memory()),
            ("Etkin stil", styles.get(self.settings["style"]).name),
            ("Lisans", "MIT — tamamen açık kaynak"),
        ]
        for index, (key, value) in enumerate(rows):
            grid.attach(add_class(Gtk.Label(label=key, xalign=1), "dim-label"), 0, index, 1, 1)
            grid.attach(Gtk.Label(label=value, xalign=0, selectable=True), 1, index, 1, 1)
        box.pack_start(grid, False, False, 0)
        link = Gtk.LinkButton.new_with_label("https://github.com/exgg3169/Hyper-Nova-Desktop-Environment",
                                             "Kaynak kodu GitHub'da")
        box.pack_start(link, False, False, 8)
        return box


def _os_name():
    try:
        with open("/etc/os-release", encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("PRETTY_NAME="):
                    return line.split("=", 1)[1].strip().strip('"')
    except OSError:
        pass
    return platform.system()


def _memory():
    try:
        with open("/proc/meminfo", encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("MemTotal:"):
                    return human_size(int(line.split()[1]) * 1024)
    except (OSError, ValueError):
        pass
    return "bilinmiyor"


class SettingsApp(Gtk.Application):
    def __init__(self, args):
        super().__init__(application_id="org.hypernova.Settings", flags=Gio.ApplicationFlags.DEFAULT_FLAGS)
        self.page = args[0] if args else None
        self.window = None

    def do_activate(self):
        if self.window is None:
            self.window = SettingsWindow(self, self.page)
        self.window.present()
