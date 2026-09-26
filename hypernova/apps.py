"""Installed application discovery (freedesktop .desktop files)."""

from .gtk import Gdk, Gio

CATEGORIES = [
    ("Development", "Geliştirme"),
    ("Education", "Eğitim"),
    ("Game", "Oyunlar"),
    ("Graphics", "Grafik"),
    ("Network", "İnternet"),
    ("AudioVideo", "Ses ve Video"),
    ("Office", "Ofis"),
    ("Science", "Bilim"),
    ("Settings", "Ayarlar"),
    ("System", "Sistem"),
    ("Utility", "Donatılar"),
]
OTHER_CATEGORY = "Diğer"

FILE_MANAGERS = ["pcmanfm.desktop", "org.gnome.Nautilus.desktop", "thunar.desktop", "nemo.desktop", "caja.desktop"]
TERMINALS = ["lxterminal.desktop", "xfce4-terminal.desktop", "org.gnome.Terminal.desktop",
             "org.gnome.Console.desktop", "foot.desktop", "alacritty.desktop", "xterm.desktop", "debian-xterm.desktop"]
BROWSERS = ["firefox.desktop", "chromium.desktop", "org.mozilla.firefox.desktop", "google-chrome.desktop"]
EDITORS = ["org.xfce.mousepad.desktop", "mousepad.desktop", "org.gnome.TextEditor.desktop", "gedit.desktop", "l3afpad.desktop"]
SETTINGS_ID = "hypernova-settings.desktop"


class App:
    __slots__ = ("id", "info", "name", "description", "icon", "categories", "keys", "weak_keys")

    def __init__(self, info):
        self.info = info
        self.id = info.get_id()
        self.name = info.get_display_name() or info.get_name() or self.id
        self.description = info.get_description() or ""
        self.icon = info.get_icon()
        cats = info.get_categories() if isinstance(info, Gio.DesktopAppInfo) else None
        self.categories = [c for c in (cats or "").split(";") if c]
        # Window classes are matched against "keys" first; "weak_keys" (name and
        # executable) are only a fallback because several entries can share them.
        base = self.id[:-8] if self.id.endswith(".desktop") else self.id
        keys = {base.lower(), base.split(".")[-1].lower()}
        wm_class = info.get_startup_wm_class() if isinstance(info, Gio.DesktopAppInfo) else None
        if wm_class:
            keys.add(wm_class.lower())
        self.keys = keys
        weak = {self.name.lower()}
        executable = info.get_executable()
        if executable:
            weak.add(executable.rsplit("/", 1)[-1].lower())
        self.weak_keys = weak

    @property
    def category(self):
        for key, label in CATEGORIES:
            if key in self.categories:
                return label
        return OTHER_CATEGORY

    def matches(self, query):
        query = query.casefold()
        return (query in self.name.casefold()
                or query in self.description.casefold()
                or any(query in k for k in self.keys | self.weak_keys))

    def launch(self):
        ctx = Gdk.Display.get_default().get_app_launch_context()
        self.info.launch([], ctx)


def all_apps():
    apps = [App(info) for info in Gio.AppInfo.get_all() if info.should_show() and info.get_id()]
    apps.sort(key=lambda a: a.name.casefold())
    return apps


def find(app_id):
    try:
        info = Gio.DesktopAppInfo.new(app_id)
    except TypeError:
        info = None
    return App(info) if info is not None else None


def first_available(candidates):
    for app_id in candidates:
        app = find(app_id)
        if app is not None:
            return app
    return None


def default_pinned():
    pinned = []
    for group in (FILE_MANAGERS, BROWSERS, TERMINALS, EDITORS):
        app = first_available(group)
        if app is not None:
            pinned.append(app.id)
    pinned.append(SETTINGS_ID)
    return pinned


def by_category(apps):
    groups = {}
    for app in apps:
        groups.setdefault(app.category, []).append(app)
    order = [label for _, label in CATEGORIES] + [OTHER_CATEGORY]
    return [(label, groups[label]) for label in order if label in groups]
