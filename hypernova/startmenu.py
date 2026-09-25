"""Start menus for every style, plus the Mac-style Launchpad."""

import os

from . import apps, dialogs, system
from .gtk import Gdk, GdkPixbuf, GLib, Gtk, Pango
from .util import add_class, clear, image, make_shell_window, menu_item, popup_menu

PLACES = [
    ("Belgeler", "folder-documents", lambda: system.open_user_dir(GLib.UserDirectory.DIRECTORY_DOCUMENTS)),
    ("Resimler", "folder-pictures", lambda: system.open_user_dir(GLib.UserDirectory.DIRECTORY_PICTURES)),
    ("Müzik", "folder-music", lambda: system.open_user_dir(GLib.UserDirectory.DIRECTORY_MUSIC)),
    ("İndirilenler", "folder-download", lambda: system.open_user_dir(GLib.UserDirectory.DIRECTORY_DOWNLOAD)),
]


def avatar(size):
    face = os.path.expanduser("~/.face")
    if os.path.exists(face):
        try:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(face, size, size, True)
            return Gtk.Image.new_from_pixbuf(pixbuf)
        except GLib.Error:
            pass
    return image("avatar-default", size)


class Popup(Gtk.Window):
    """An undecorated window that hides itself when it loses focus."""

    def __init__(self, shell, name):
        super().__init__(title="HyperNova Menü")
        self.shell = shell
        make_shell_window(self, "hn-popup")
        self.set_name(name)
        add_class(self, "hn-popup", f"style-{shell.style.id}")
        self.set_keep_above(True)
        self.set_type_hint(Gdk.WindowTypeHint.POPUP_MENU)
        self._menu_open = False
        self.hidden_at = 0
        self.connect("focus-out-event", self._on_focus_out)
        self.connect("key-press-event", self._on_key)
        self.connect("delete-event", lambda *_: self.hide_popup() or True)

    # Nested Gtk.Menus take the keyboard grab; don't treat that as "clicked away".
    def track_menu(self, menu):
        self._menu_open = True

        def done(*_):
            self._menu_open = False
            GLib.timeout_add(150, lambda: (not self.is_active() and self.hide_popup()) and False)
        menu.connect("deactivate", done)
        return menu

    def _on_focus_out(self, *_):
        if not self._menu_open:
            GLib.timeout_add(80, lambda: (not self.is_active() and not self._menu_open and self.hide_popup()) and False)
        return False

    def _on_key(self, _w, event):
        if event.keyval == Gdk.KEY_Escape:
            self.hide_popup()
            return True
        return False

    def show_popup(self, focus_search=False):
        self.reset()
        self.show_all()
        self.place()
        self.present_with_time(Gtk.get_current_event_time() or Gdk.CURRENT_TIME)
        if focus_search and getattr(self, "search", None) is not None:
            self.search.grab_focus()

    def hide_popup(self):
        if self.get_visible():
            self.hide()
            self.hidden_at = GLib.get_monotonic_time()

    def toggle(self, focus_search=False):
        if self.get_visible():
            self.hide_popup()
        elif GLib.get_monotonic_time() - self.hidden_at > 250_000:
            self.show_popup(focus_search)

    def place(self):
        geo = self.shell.monitor
        width, height = self.get_size()
        self.move(geo.x, geo.y + geo.height - self.shell.style.panel_height - height)

    def reset(self):
        pass

    # --- shared building blocks -------------------------------------------------

    def launch(self, app):
        self.hide_popup()
        system.launch_app(app)

    def run(self, callback):
        def handler(*_):
            self.hide_popup()
            callback()
        return handler

    def app_button(self, app, icon_size, css="hn-menu-app", subtitle=False):
        btn = add_class(Gtk.Button(), css)
        btn.set_relief(Gtk.ReliefStyle.NONE)
        box = Gtk.Box(spacing=8)
        box.pack_start(image(app.icon, icon_size), False, False, 0)
        labels = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        name = Gtk.Label(label=app.name, xalign=0)
        name.set_ellipsize(Pango.EllipsizeMode.END)
        labels.pack_start(name, False, False, 0)
        if subtitle and app.description:
            desc = add_class(Gtk.Label(label=app.description, xalign=0), "dim")
            desc.set_ellipsize(Pango.EllipsizeMode.END)
            labels.pack_start(desc, False, False, 0)
        labels.set_valign(Gtk.Align.CENTER)
        box.pack_start(labels, True, True, 0)
        btn.add(box)
        btn.set_tooltip_text(app.description or app.name)
        btn.connect("clicked", lambda *_: self.launch(app))
        btn.connect("button-press-event", self._app_context, app)
        return btn

    def _app_context(self, widget, event, app):
        if event.button != 3:
            return False
        menu = Gtk.Menu()
        menu.append(menu_item("Aç", lambda: self.launch(app)))
        if self.shell.is_pinned(app.id):
            menu.append(menu_item("Sabitlemeyi kaldır", lambda: self.shell.set_pinned(app.id, False)))
        else:
            menu.append(menu_item("Görev çubuğuna sabitle", lambda: self.shell.set_pinned(app.id, True)))
        popup_menu(self.track_menu(menu), None, event)
        return True

    def link_button(self, label, icon, callback, css="hn-menu-link", icon_size=24):
        btn = add_class(Gtk.Button(), css)
        btn.set_relief(Gtk.ReliefStyle.NONE)
        box = Gtk.Box(spacing=8)
        if icon:
            box.pack_start(image(icon, icon_size), False, False, 0)
        box.pack_start(Gtk.Label(label=label, xalign=0), True, True, 0)
        btn.add(box)
        btn.connect("clicked", self.run(callback))
        return btn

    def pinned_apps(self):
        return [app for app in (apps.find(i) for i in self.shell.pinned_ids()) if app is not None]

    def all_programs_menu(self):
        menu = Gtk.Menu()
        add_class(menu, "hn-programs-menu")
        for category, members in apps.by_category(apps.all_apps()):
            item = menu_item(category, icon="folder")
            sub = Gtk.Menu()
            for app in members:
                sub.append(menu_item(app.name, lambda a=app: self.launch(a), app.icon))
            item.set_submenu(sub)
            menu.append(item)
        return self.track_menu(menu)

    def power_menu(self):
        menu = Gtk.Menu()
        for action, label in (("suspend", "Uyku"), ("reboot", "Yeniden başlat"),
                              ("poweroff", "Kapat"), ("logout", "Oturumu kapat")):
            menu.append(menu_item(label, lambda a=action: (self.hide_popup(), system.power(a))))
        return self.track_menu(menu)

    @staticmethod
    def popup_beside(menu, widget):
        menu.show_all()
        menu.popup_at_widget(widget, Gdk.Gravity.NORTH_EAST, Gdk.Gravity.SOUTH_WEST, None)

    def searchable_list(self, container, query, icon_size, empty_text="Sonuç bulunamadı"):
        clear(container)
        results = [a for a in apps.all_apps() if a.matches(query)] if query else []
        for app in results[:40]:
            container.pack_start(self.app_button(app, icon_size, subtitle=True), False, False, 0)
        if query and not results:
            container.pack_start(add_class(Gtk.Label(label=empty_text), "dim"), False, False, 12)
        container.show_all()
        return results

    def launch_first(self, results):
        if results:
            self.launch(results[0])


class XPMenu(Popup):
    def __init__(self, shell):
        super().__init__(shell, "hn-startmenu-xp")
        self.set_size_request(400, 470)
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        header = add_class(Gtk.Box(spacing=10), "hn-menu-header")
        pic = add_class(Gtk.Box(), "hn-avatar")
        pic.add(avatar(44))
        header.pack_start(pic, False, False, 0)
        header.pack_start(add_class(Gtk.Label(label=system.user_display_name(), xalign=0), "hn-username"),
                          True, True, 0)
        outer.pack_start(header, False, False, 0)

        body = Gtk.Box(homogeneous=True)
        self.left = add_class(Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2), "hn-menu-left")
        right = add_class(Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1), "hn-menu-right")
        body.pack_start(self.left, True, True, 0)
        body.pack_start(right, True, True, 0)
        outer.pack_start(body, True, True, 0)

        s = shell.style
        right.pack_start(self.link_button(f"{s.home_label}", "folder-documents",
                                          lambda: system.open_user_dir(GLib.UserDirectory.DIRECTORY_DOCUMENTS),
                                          "hn-menu-link-bold"), False, False, 0)
        for label, icon, cb in PLACES[1:]:
            right.pack_start(self.link_button(label + "im" if label == "Müzik" else label, icon, cb), False, False, 0)
        right.pack_start(self.link_button(s.computer_label, "computer", lambda: system.open_path("/"),
                                          "hn-menu-link-bold"), False, False, 0)
        right.pack_start(add_class(Gtk.Separator(), "hn-sep"), False, False, 4)
        right.pack_start(self.link_button("Denetim Masası", "preferences-system", system.open_settings),
                         False, False, 0)
        right.pack_start(self.link_button("Komut İstemi", "utilities-terminal", system.open_terminal),
                         False, False, 0)
        right.pack_start(add_class(Gtk.Separator(), "hn-sep"), False, False, 4)
        right.pack_start(self.link_button("HyperNova Hakkında", "help-about",
                                          lambda: dialogs.show_about(shell.style)), False, False, 0)
        right.pack_start(self.link_button("Çalıştır...", "system-run", lambda: dialogs.RunDialog(shell.style)),
                         False, False, 0)

        footer = add_class(Gtk.Box(spacing=6), "hn-menu-footer")
        logout = self.link_button("Oturumu Kapat", "system-log-out",
                                  lambda: dialogs.PowerDialog(shell.style, only="logout"), "hn-footer-btn")
        shutdown = self.link_button("Bilgisayarı Kapat", "system-shutdown",
                                    lambda: dialogs.PowerDialog(shell.style), "hn-footer-btn")
        footer.pack_end(shutdown, False, False, 0)
        footer.pack_end(logout, False, False, 0)
        outer.pack_start(footer, False, False, 0)
        self.add(outer)

    def reset(self):
        clear(self.left)
        for app in self.pinned_apps()[:8]:
            self.left.pack_start(self.app_button(app, 32, subtitle=True), False, False, 0)
        spacer = Gtk.Box()
        self.left.pack_start(spacer, True, True, 0)
        self.left.pack_start(add_class(Gtk.Separator(), "hn-sep"), False, False, 4)
        all_btn = add_class(Gtk.Button(), "hn-all-programs")
        all_btn.set_relief(Gtk.ReliefStyle.NONE)
        row = Gtk.Box(spacing=8)
        row.pack_start(add_class(Gtk.Label(label="Tüm Programlar"), "bold"), True, False, 0)
        row.pack_start(image("go-next", 18), False, False, 0)
        all_btn.add(row)
        all_btn.connect("clicked", lambda b: self.popup_beside(self.all_programs_menu(), b))
        self.left.pack_start(all_btn, False, False, 2)
        self.left.show_all()


class Win7Menu(Popup):
    def __init__(self, shell):
        super().__init__(shell, "hn-startmenu-7")
        self.set_size_request(430, 520)
        body = Gtk.Box()
        left = add_class(Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4), "hn-menu-left")
        left.set_size_request(260, -1)
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.stack.set_vexpand(True)
        self.home = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self.stack.add_named(self.home, "home")
        self.all_list = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.add(self.all_list)
        self.stack.add_named(scroll, "all")
        self.results = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        rscroll = Gtk.ScrolledWindow()
        rscroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        rscroll.add(self.results)
        self.stack.add_named(rscroll, "search")
        left.pack_start(self.stack, True, True, 0)
        self.toggle_all = add_class(Gtk.Button(), "hn-all-programs")
        self.toggle_all.set_relief(Gtk.ReliefStyle.NONE)
        self.toggle_all.connect("clicked", self._flip)
        left.pack_start(add_class(Gtk.Separator(), "hn-sep"), False, False, 2)
        left.pack_start(self.toggle_all, False, False, 0)
        self.search = add_class(Gtk.SearchEntry(), "hn-search")
        self.search.set_placeholder_text("Programları ve dosyaları ara")
        self.search.connect("search-changed", self._on_search)
        self.search.connect("activate", lambda *_: self.launch_first(self._results))
        left.pack_start(self.search, False, False, 6)
        body.pack_start(left, False, False, 0)

        right = add_class(Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1), "hn-menu-right")
        right.set_size_request(170, -1)
        pic = add_class(Gtk.Box(), "hn-avatar")
        pic.set_halign(Gtk.Align.CENTER)
        pic.add(avatar(56))
        right.pack_start(pic, False, False, 8)
        right.pack_start(self.link_button(system.user_display_name(), None,
                                          lambda: system.open_path("~"), "hn-menu-link-bold"), False, False, 0)
        for label, icon, cb in PLACES:
            right.pack_start(self.link_button(label, None, cb), False, False, 0)
        right.pack_start(add_class(Gtk.Separator(), "hn-sep"), False, False, 4)
        right.pack_start(self.link_button(shell.style.computer_label, None, lambda: system.open_path("/")),
                         False, False, 0)
        right.pack_start(self.link_button("Denetim Masası", None, system.open_settings), False, False, 0)
        right.pack_start(self.link_button("Komut İstemi", None, system.open_terminal), False, False, 0)
        right.pack_start(self.link_button("Çalıştır...", None, lambda: dialogs.RunDialog(shell.style)),
                         False, False, 0)
        right.pack_start(Gtk.Box(), True, True, 0)
        power = Gtk.Box()
        power.set_halign(Gtk.Align.END)
        shut = add_class(Gtk.Button(label="Kapat"), "hn-shutdown")
        shut.connect("clicked", self.run(lambda: system.power("poweroff")))
        more = add_class(Gtk.Button(), "hn-shutdown-more")
        more.add(Gtk.Arrow(arrow_type=Gtk.ArrowType.RIGHT, shadow_type=Gtk.ShadowType.NONE))
        more.connect("clicked", lambda b: self.popup_beside(self.power_menu(), b))
        power.pack_start(shut, False, False, 0)
        power.pack_start(more, False, False, 0)
        right.pack_start(power, False, False, 8)
        body.pack_start(right, True, True, 0)
        self.add(body)
        self._results = []

    def _flip(self, *_):
        showing_all = self.stack.get_visible_child_name() == "all"
        self._show_page("home" if showing_all else "all")

    def _show_page(self, name):
        self.stack.set_visible_child_name(name)
        text = "◂  Geri" if name != "home" else "Tüm Programlar  ▸"
        clear(self.toggle_all)
        self.toggle_all.add(Gtk.Label(label=text, xalign=0))
        self.toggle_all.show_all()

    def _on_search(self, entry):
        query = entry.get_text().strip()
        if not query:
            self._show_page("home")
            return
        self._results = self.searchable_list(self.results, query, 24)
        self._show_page("search")

    def reset(self):
        self.search.set_text("")
        clear(self.home)
        for app in self.pinned_apps()[:9]:
            self.home.pack_start(self.app_button(app, 32), False, False, 0)
        clear(self.all_list)
        for category, members in apps.by_category(apps.all_apps()):
            exp = add_class(Gtk.Expander(label=category), "hn-category")
            inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            for app in members:
                inner.pack_start(self.app_button(app, 16, "hn-menu-app-small"), False, False, 0)
            exp.add(inner)
            self.all_list.pack_start(exp, False, False, 0)
        self._show_page("home")


class Win10Menu(Popup):
    TILE_COLORS = ["tile-blue", "tile-teal", "tile-purple", "tile-green", "tile-orange", "tile-red"]

    def __init__(self, shell):
        super().__init__(shell, "hn-startmenu-10")
        self.set_size_request(660, 560)
        body = Gtk.Box()

        strip = add_class(Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2), "hn-menu-strip")
        strip.pack_start(self._strip_button("open-menu-symbolic", "Başlat", None), False, False, 0)
        strip.pack_start(Gtk.Box(), True, True, 0)
        strip.pack_start(self._strip_button("avatar-default-symbolic", system.user_display_name(),
                                            lambda: system.open_path("~")), False, False, 0)
        strip.pack_start(self._strip_button("folder-documents-symbolic", "Belgeler", PLACES[0][2]), False, False, 0)
        strip.pack_start(self._strip_button("folder-pictures-symbolic", "Resimler", PLACES[1][2]), False, False, 0)
        strip.pack_start(self._strip_button("emblem-system-symbolic", "Ayarlar", system.open_settings),
                         False, False, 0)
        power = self._strip_button("system-shutdown-symbolic", "Güç", None)
        power.connect("clicked", lambda b: self.popup_beside(self.power_menu(), b))
        strip.pack_start(power, False, False, 0)
        body.pack_start(strip, False, False, 0)

        middle = add_class(Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4), "hn-menu-list")
        middle.set_size_request(270, -1)
        self.search = add_class(Gtk.SearchEntry(), "hn-search")
        self.search.set_placeholder_text("Aramak için buraya yazın")
        self.search.connect("search-changed", self._on_search)
        self.search.connect("activate", lambda *_: self.launch_first(self._results))
        middle.pack_start(self.search, False, False, 6)
        self.list = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.add(self.list)
        middle.pack_start(scroll, True, True, 0)
        body.pack_start(middle, False, False, 0)

        right = add_class(Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6), "hn-menu-tiles")
        right.pack_start(add_class(Gtk.Label(label="Sabitlenenler", xalign=0), "hn-section-title"), False, False, 0)
        self.tiles = Gtk.FlowBox()
        self.tiles.set_selection_mode(Gtk.SelectionMode.NONE)
        self.tiles.set_max_children_per_line(3)
        self.tiles.set_min_children_per_line(3)
        self.tiles.set_row_spacing(4)
        self.tiles.set_column_spacing(4)
        self.tiles.set_valign(Gtk.Align.START)
        right.pack_start(self.tiles, True, True, 0)
        body.pack_start(right, True, True, 0)
        self.add(body)
        self._results = []

    def _strip_button(self, icon, tooltip, callback):
        btn = add_class(Gtk.Button(), "hn-strip-btn")
        btn.set_relief(Gtk.ReliefStyle.NONE)
        btn.add(image(icon, 18))
        btn.set_tooltip_text(tooltip)
        if callback is not None:
            btn.connect("clicked", self.run(callback))
        return btn

    def _fill_list(self, entries):
        clear(self.list)
        letter = None
        for app in entries:
            first = app.name[:1].upper()
            first = first if first.isalpha() else "#"
            if first != letter:
                letter = first
                self.list.pack_start(add_class(Gtk.Label(label=letter, xalign=0), "hn-letter"), False, False, 0)
            self.list.pack_start(self.app_button(app, 24), False, False, 0)
        self.list.show_all()

    def _on_search(self, entry):
        query = entry.get_text().strip()
        if not query:
            self._results = []
            self._fill_list(apps.all_apps())
            return
        self._results = [a for a in apps.all_apps() if a.matches(query)]
        clear(self.list)
        self.list.pack_start(add_class(Gtk.Label(label="En iyi eşleşme", xalign=0), "hn-letter"), False, False, 0)
        for app in self._results[:30]:
            self.list.pack_start(self.app_button(app, 24, subtitle=True), False, False, 0)
        if not self._results:
            self.list.pack_start(add_class(Gtk.Label(label="Sonuç bulunamadı"), "dim"), False, False, 12)
        self.list.show_all()

    def reset(self):
        self.search.set_text("")
        self._fill_list(apps.all_apps())
        for child in self.tiles.get_children():
            child.destroy()
        for index, app in enumerate(self.pinned_apps()[:12]):
            tile = add_class(Gtk.Button(), "hn-tile", self.TILE_COLORS[index % len(self.TILE_COLORS)])
            tile.set_relief(Gtk.ReliefStyle.NONE)
            tile.set_size_request(100, 100)
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
            box.set_valign(Gtk.Align.CENTER)
            box.pack_start(image(app.icon, 36), False, False, 0)
            label = Gtk.Label(label=app.name)
            label.set_ellipsize(Pango.EllipsizeMode.END)
            label.set_max_width_chars(12)
            box.pack_start(label, False, False, 0)
            tile.add(box)
            tile.set_tooltip_text(app.name)
            tile.connect("clicked", lambda _b, a=app: self.launch(a))
            tile.connect("button-press-event", self._app_context, app)
            self.tiles.add(tile)
        self.tiles.show_all()


class Launchpad(Popup):
    """Full-screen app grid for the Mac style."""

    def __init__(self, shell):
        super().__init__(shell, "hn-launchpad")
        geo = shell.monitor
        self.set_default_size(geo.width, geo.height)
        self.set_size_request(geo.width, geo.height)
        self.set_type_hint(Gdk.WindowTypeHint.NORMAL)
        events = Gtk.EventBox()
        events.set_visible_window(False)
        events.connect("button-press-event", self._background_click)
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        outer.set_margin_top(60)
        outer.set_margin_bottom(60)
        self.search = add_class(Gtk.SearchEntry(), "hn-search")
        self.search.set_placeholder_text("Ara")
        self.search.set_halign(Gtk.Align.CENTER)
        self.search.set_size_request(260, -1)
        self.search.connect("search-changed", lambda *_: self._fill())
        self.search.connect("activate", lambda *_: self.launch_first(self._results))
        outer.pack_start(self.search, False, False, 0)
        self.grid = Gtk.FlowBox()
        self.grid.set_selection_mode(Gtk.SelectionMode.NONE)
        self.grid.set_max_children_per_line(7)
        self.grid.set_min_children_per_line(3)
        self.grid.set_row_spacing(24)
        self.grid.set_column_spacing(24)
        self.grid.set_halign(Gtk.Align.CENTER)
        self.grid.set_valign(Gtk.Align.START)
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.add(self.grid)
        outer.pack_start(scroll, True, True, 0)
        events.add(outer)
        self.add(events)
        self._results = []

    def _background_click(self, _w, event):
        if event.button == 1:
            self.hide_popup()
        return False

    def place(self):
        geo = self.shell.monitor
        self.move(geo.x, geo.y)

    def _fill(self):
        for child in self.grid.get_children():
            child.destroy()
        query = self.search.get_text().strip()
        self._results = [a for a in apps.all_apps() if not query or a.matches(query)]
        for app in self._results:
            btn = add_class(Gtk.Button(), "hn-lp-item")
            btn.set_relief(Gtk.ReliefStyle.NONE)
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
            box.pack_start(image(app.icon, 64), False, False, 0)
            label = Gtk.Label(label=app.name)
            label.set_ellipsize(Pango.EllipsizeMode.END)
            label.set_max_width_chars(14)
            box.pack_start(label, False, False, 0)
            btn.add(box)
            btn.set_size_request(120, -1)
            btn.connect("clicked", lambda _b, a=app: self.launch(a))
            btn.connect("button-press-event", self._app_context, app)
            self.grid.add(btn)
        self.grid.show_all()

    def reset(self):
        self.search.set_text("")
        self._fill()

    def show_popup(self, focus_search=True):
        super().show_popup(True)


MENUS = {"xp": XPMenu, "win7": Win7Menu, "win10": Win10Menu, "launchpad": Launchpad}


def create(shell):
    return MENUS[shell.style.menu](shell)
