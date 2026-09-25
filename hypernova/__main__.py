"""Entry point: `python -m hypernova [settings | --write-openbox-config | shell options]`."""

import sys


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    from .gtk import GLib

    if argv and argv[0] == "settings":
        GLib.set_prgname("hypernova-settings")
        from .settings_app import SettingsApp
        return SettingsApp(argv[1:]).run([sys.argv[0]])

    if argv and argv[0] == "--write-openbox-config":
        from . import config, openbox, styles
        print(openbox.write_config(styles.get(config.Settings()["style"])))
        return 0

    if argv and argv[0] in ("-h", "--help"):
        print(__doc__)
        print("Shell options: --toggle-menu --search --run --terminal --open-home --power --rebuild")
        return 0

    GLib.set_prgname("hypernova-shell")
    from .shell import ShellApp
    return ShellApp().run([sys.argv[0], *argv])


if __name__ == "__main__":
    sys.exit(main())
