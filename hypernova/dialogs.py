"""Shutdown, run and about dialogs."""

import os

from . import VERSION, logo, system
from .gtk import Gdk, GLib, Gtk
from .util import add_class, image, make_shell_window


class ShellDialog(Gtk.Window):
    def __init__(self, style, title, name):
        super().__init__(title=title)
        make_shell_window(self, "hn-dialog")
        self.set_name(name)
        add_class(self, "hn-dialog", f"style-{style.id}")
        self.set_keep_above(True)
        self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        self.set_type_hint(Gdk.WindowTypeHint.DIALOG)
        self.connect("key-press-event", self._on_key)

    def _on_key(self, _w, event):
        if event.keyval == Gdk.KEY_Escape:
            self.destroy()
            return True
        return False


class PowerDialog(ShellDialog):
    ACTIONS = [
        ("suspend", "Beklemeye Al", "media-playback-pause", "hn-power-suspend"),
        ("poweroff", "Kapat", "system-shutdown", "hn-power-off"),
        ("reboot", "Yeniden Başlat", "system-reboot", "hn-power-reboot"),
        ("logout", "Oturumu Kapat", "system-log-out", "hn-power-logout"),
    ]

    def __init__(self, style, only=None):
        title = "Oturumu Kapat" if only == "logout" else "Bilgisayarı Kapat"
        super().__init__(style, title, "hn-power-dialog")
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        header = add_class(Gtk.Box(spacing=10), "hn-dialog-header")
        header.pack_start(add_class(Gtk.Label(label=title, xalign=0), "hn-dialog-title"), True, True, 0)
        header.pack_start(Gtk.Image.new_from_pixbuf(logo.pixbuf(40)), False, False, 0)
        outer.pack_start(header, False, False, 0)

        actions = add_class(Gtk.Box(spacing=18, homogeneous=True), "hn-dialog-body")
        for action, label, icon, css in self.ACTIONS:
            if only and action != only:
                continue
            btn = add_class(Gtk.Button(), "hn-power-btn", css)
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
            box.pack_start(image(icon, 40), False, False, 0)
            box.pack_start(Gtk.Label(label=label), False, False, 0)
            btn.add(box)
            btn.connect("clicked", self._run, action)
            actions.pack_start(btn, True, True, 0)
        outer.pack_start(actions, True, True, 0)

        footer = add_class(Gtk.Box(), "hn-dialog-footer")
        cancel = Gtk.Button(label="İptal")
        cancel.connect("clicked", lambda *_: self.destroy())
        footer.pack_end(cancel, False, False, 0)
        outer.pack_start(footer, False, False, 0)
        self.add(outer)
        self.show_all()
        self.present()

    def _run(self, _btn, action):
        self.destroy()
        system.power(action)


class RunDialog(ShellDialog):
    def __init__(self, style):
        super().__init__(style, "Çalıştır", "hn-run-dialog")
        box = add_class(Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10), "hn-dialog-body")
        row = Gtk.Box(spacing=12)
        row.pack_start(image("system-run", 32), False, False, 0)
        row.pack_start(Gtk.Label(label="Açmak istediğiniz programın, klasörün veya\n"
                                       "internet kaynağının adını yazın.", xalign=0), True, True, 0)
        box.pack_start(row, False, False, 0)
        self.entry = Gtk.Entry()
        self.entry.set_width_chars(40)
        self.entry.connect("activate", self._run)
        box.pack_start(self.entry, False, False, 0)
        buttons = Gtk.Box(spacing=8)
        ok = Gtk.Button(label="Tamam")
        ok.connect("clicked", self._run)
        cancel = Gtk.Button(label="İptal")
        cancel.connect("clicked", lambda *_: self.destroy())
        buttons.pack_end(cancel, False, False, 0)
        buttons.pack_end(ok, False, False, 0)
        box.pack_start(buttons, False, False, 0)
        self.add(box)
        self.show_all()
        self.present()

    def _run(self, *_):
        text = self.entry.get_text().strip()
        if not text:
            return
        self.destroy()
        if "://" in text:
            system.open_uri(text)
        elif os.path.exists(os.path.expanduser(text)):
            system.open_path(text)
        else:
            system.run_command_line(text)


def show_about(style):
    dialog = Gtk.AboutDialog()
    dialog.set_program_name("HyperNova OS")
    dialog.set_version(VERSION)
    dialog.set_comments(f"Arch Linux tabanlı HyperNova masaüstü ortamı\nEtkin stil: {style.name}")
    dialog.set_license_type(Gtk.License.MIT_X11)
    dialog.set_website("https://github.com/exgg3169/Hyper-Nova-Desktop-Environment")
    dialog.set_website_label("Kaynak kodu (GitHub)")
    dialog.set_logo(logo.pixbuf(128))
    dialog.set_keep_above(True)
    dialog.connect("response", lambda d, _r: d.destroy())
    dialog.show()
    GLib.idle_add(dialog.present)
