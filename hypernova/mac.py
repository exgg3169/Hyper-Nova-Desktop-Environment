"""The Mac-like layout: a global menu bar on top and a centred dock."""

from . import dialogs, logo, system, tray
from .gtk import Gdk, GLib, Gtk
from .tasks import GroupButton, system_time
from .util import add_class, clear, image, make_shell_window, menu_item, popup_menu

DOCK_MARGIN = 6


class MenuBar(Gtk.Window):
    def __init__(self, shell):
        super().__init__(title="HyperNova Menü Çubuğu")
        self.shell = shell
        make_shell_window(self, "hn-panel")
        self.set_name("hn-menubar")
        self.set_type_hint(Gdk.WindowTypeHint.DOCK)
        self.set_keep_above(True)
        geo = shell.monitor
        self.set_size_request(geo.width, shell.style.panel_height)
        self.move(geo.x, geo.y)

        box = Gtk.Box(spacing=2)
        self.add(box)
        nova = self._item(None, self._nova_menu)
        nova.add(Gtk.Image.new_from_pixbuf(logo.pixbuf(16, (0.1, 0.1, 0.12, 1))))
        add_class(nova, "hn-nova-button")
        box.pack_start(nova, False, False, 0)
        self.app_name = self._item("Masaüstü", self._window_menu)
        add_class(self.app_name, "hn-appname")
        box.pack_start(self.app_name, False, False, 0)
        box.pack_start(self._item("Dosya", self._file_menu), False, False, 0)
        box.pack_start(self._item("Git", self._go_menu), False, False, 0)
        box.pack_start(self._item("Pencere", self._window_menu), False, False, 0)
        box.pack_start(self._item("Yardım", self._help_menu), False, False, 0)
        box.pack_start(Gtk.Box(), True, True, 0)
        box.pack_start(tray.build(shell.settings, "mac", 16), False, False, 0)

        self._handler = shell.tasks.connect("changed", lambda *_: self.refresh())
        self.connect("destroy", lambda *_: shell.tasks.disconnect(self._handler))
        self.refresh()

    def _item(self, label, menu_factory):
        btn = add_class(Gtk.Button(), "hn-menubar-item")
        btn.set_relief(Gtk.ReliefStyle.NONE)
        if label:
            btn.add(Gtk.Label(label=label))
        btn.connect("clicked", lambda b: popup_menu(menu_factory(), b, None, above=False))
        return btn

    def refresh(self):
        win = self.shell.tasks.active_window()
        name = "Masaüstü"
        if win is not None:
            app = self.shell.tasks._app_for(win)
            name = app.name if app is not None else (win.get_class_group_name() or win.get_name())
        child = self.app_name.get_child()
        child.set_text(name)

    def _nova_menu(self):
        style = self.shell.style
        menu = Gtk.Menu()
        menu.append(menu_item("Bu Nova Hakkında", lambda: dialogs.show_about(style)))
        menu.append(Gtk.SeparatorMenuItem())
        menu.append(menu_item("Sistem Ayarları…", system.open_settings))
        menu.append(menu_item("Uygulamalar", self.shell.toggle_menu))
        menu.append(Gtk.SeparatorMenuItem())
        menu.append(menu_item("Uyut", lambda: system.power("suspend")))
        menu.append(menu_item("Yeniden Başlat…", lambda: dialogs.PowerDialog(style, only="reboot")))
        menu.append(menu_item("Kapat…", lambda: dialogs.PowerDialog(style, only="poweroff")))
        menu.append(Gtk.SeparatorMenuItem())
        menu.append(menu_item(f"{system.user_display_name()} Oturumunu Kapat…",
                              lambda: dialogs.PowerDialog(style, only="logout")))
        return menu

    def _file_menu(self):
        menu = Gtk.Menu()
        menu.append(menu_item("Yeni Terminal Penceresi", system.open_terminal))
        menu.append(menu_item("Ev Klasörünü Aç", lambda: system.open_path("~")))
        menu.append(Gtk.SeparatorMenuItem())
        menu.append(menu_item("Çalıştır…", lambda: dialogs.RunDialog(self.shell.style)))
        return menu

    def _go_menu(self):
        menu = Gtk.Menu()
        dirs = GLib.UserDirectory
        menu.append(menu_item("Ev", lambda: system.open_path("~"), "user-home"))
        menu.append(menu_item("Belgeler", lambda: system.open_user_dir(dirs.DIRECTORY_DOCUMENTS), "folder-documents"))
        menu.append(menu_item("İndirilenler", lambda: system.open_user_dir(dirs.DIRECTORY_DOWNLOAD), "folder-download"))
        menu.append(menu_item("Resimler", lambda: system.open_user_dir(dirs.DIRECTORY_PICTURES), "folder-pictures"))
        menu.append(menu_item(self.shell.style.computer_label, lambda: system.open_path("/"), "drive-harddisk"))
        menu.append(menu_item(self.shell.style.trash_label, system.open_trash, "user-trash"))
        return menu

    def _window_menu(self):
        menu = Gtk.Menu()
        win = self.shell.tasks.active_window()
        if win is None:
            item = menu_item("Etkin pencere yok")
            item.set_sensitive(False)
            menu.append(item)
            return menu
        menu.append(menu_item("Küçült", win.minimize))
        menu.append(menu_item("Önceki Boyut" if win.is_maximized() else "Ekranı Kapla",
                              lambda: win.unmaximize() if win.is_maximized() else win.maximize()))
        menu.append(Gtk.SeparatorMenuItem())
        menu.append(menu_item("Pencereyi Kapat", lambda: win.close(system_time(self))))
        menu.append(Gtk.SeparatorMenuItem())
        menu.append(menu_item("Masaüstünü Göster", self.shell.tasks.toggle_showing_desktop))
        return menu

    def _help_menu(self):
        menu = Gtk.Menu()
        menu.append(menu_item("HyperNova Hakkında", lambda: dialogs.show_about(self.shell.style)))
        menu.append(menu_item("Kaynak Kodu", lambda: system.open_uri(
            "https://github.com/exgg3169/Hyper-Nova-Desktop-Environment")))
        return menu


class Dock(Gtk.Window):
    def __init__(self, shell):
        super().__init__(title="HyperNova Dock")
        self.shell = shell
        make_shell_window(self, "hn-panel")
        self.set_name("hn-dock")
        self.set_type_hint(Gdk.WindowTypeHint.DOCK)
        self.set_keep_above(True)
        self.box = add_class(Gtk.Box(spacing=4), "hn-dock-box")
        self.add(self.box)
        self._last_width = 0
        self.connect("size-allocate", self._reposition)
        self._handler = shell.tasks.connect("changed", lambda *_: self.refresh())
        self.connect("destroy", lambda *_: shell.tasks.disconnect(self._handler))
        self.refresh()

    @staticmethod
    def height_for(style):
        return style.dock_icon_size + 26

    def _reposition(self, *_):
        width, height = self.get_size()
        geo = self.shell.monitor
        self.move(geo.x + (geo.width - width) // 2, geo.y + geo.height - height - DOCK_MARGIN)

    def _icon_button(self, icon, tooltip, callback):
        btn = add_class(Gtk.Button(), "hn-dock-item")
        btn.set_relief(Gtk.ReliefStyle.NONE)
        inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        inner.pack_start(icon, True, True, 0)
        inner.pack_start(add_class(Gtk.Box(), "indicator"), False, False, 0)
        btn.add(inner)
        btn.set_tooltip_text(tooltip)
        btn.connect("clicked", lambda *_: callback())
        return btn

    def refresh(self):
        clear(self.box)
        size = self.shell.style.dock_icon_size
        launchpad = self._icon_button(Gtk.Image.new_from_pixbuf(logo.pixbuf(size)), "Uygulamalar",
                                      self.shell.toggle_menu)
        self.box.pack_start(launchpad, False, False, 0)
        for group in self.shell.tasks.groups(self.shell.pinned_ids()):
            self.box.pack_start(GroupButton(self.shell, group, size, "hn-dock-item", "dock'a"), False, False, 0)
        self.box.pack_start(add_class(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL), "hn-dock-sep"),
                            False, False, 4)
        self.box.pack_start(self._icon_button(image("user-trash", size),
                                              self.shell.style.trash_label, system.open_trash), False, False, 0)
        self.box.show_all()
        self.resize(1, 1)
