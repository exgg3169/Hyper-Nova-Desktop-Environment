"""Small GTK helpers shared by the shell components."""

from .gtk import Gdk, GdkPixbuf, GdkX11, Gio, Gtk

TR_DAYS = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
TR_DAYS_SHORT = ["Pzt", "Sal", "Çar", "Per", "Cum", "Cmt", "Paz"]
TR_MONTHS = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz",
             "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]


def add_class(widget, *names):
    ctx = widget.get_style_context()
    for name in names:
        ctx.add_class(name)
    return widget


def set_class(widget, name, enabled):
    ctx = widget.get_style_context()
    if enabled:
        ctx.add_class(name)
    else:
        ctx.remove_class(name)


def clear(container):
    for child in container.get_children():
        child.destroy()


def image(icon, size):
    """Builds a Gtk.Image from a Gio.Icon, an icon name or a pixbuf."""
    if isinstance(icon, GdkPixbuf.Pixbuf):
        if icon.get_width() != size:
            icon = icon.scale_simple(size, size, GdkPixbuf.InterpType.BILINEAR)
        return Gtk.Image.new_from_pixbuf(icon)
    if isinstance(icon, Gio.Icon):
        img = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.DIALOG)
    else:
        img = Gtk.Image.new_from_icon_name(icon or "application-x-executable", Gtk.IconSize.DIALOG)
    img.set_pixel_size(size)
    return img


def make_shell_window(window, role):
    """Common setup for undecorated shell surfaces (panels, menus, docks)."""
    window.set_decorated(False)
    window.set_skip_taskbar_hint(True)
    window.set_skip_pager_hint(True)
    window.set_role(role)
    window.stick()
    screen = window.get_screen()
    visual = screen.get_rgba_visual()
    if visual is not None and screen.is_composited():
        window.set_visual(visual)
        add_class(window, "composited")
    return window


def event_time(widget=None):
    t = Gtk.get_current_event_time()
    if t:
        return t
    gdk_window = widget.get_window() if widget is not None else None
    if isinstance(gdk_window, GdkX11.X11Window):
        return GdkX11.x11_get_server_time(gdk_window)
    return 0


def primary_monitor_geometry():
    display = Gdk.Display.get_default()
    monitor = display.get_primary_monitor() or display.get_monitor(0)
    return monitor.get_geometry()


def popup_menu(menu, widget, event=None, above=True):
    menu.show_all()
    if widget is not None:
        if above:
            menu.popup_at_widget(widget, Gdk.Gravity.NORTH_WEST, Gdk.Gravity.SOUTH_WEST, event)
        else:
            menu.popup_at_widget(widget, Gdk.Gravity.SOUTH_WEST, Gdk.Gravity.NORTH_WEST, event)
    else:
        menu.popup_at_pointer(event)


def menu_item(label, callback=None, icon=None):
    if icon:
        item = Gtk.MenuItem()
        box = Gtk.Box(spacing=8)
        box.pack_start(image(icon, 16), False, False, 0)
        box.pack_start(Gtk.Label(label=label, xalign=0), True, True, 0)
        item.add(box)
    else:
        item = Gtk.MenuItem(label=label)
    if callback is not None:
        item.connect("activate", lambda *_: callback())
    return item


def human_size(num):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if num < 1024 or unit == "TB":
            return f"{num:.0f} {unit}" if unit == "B" else f"{num:.1f} {unit}"
        num /= 1024
