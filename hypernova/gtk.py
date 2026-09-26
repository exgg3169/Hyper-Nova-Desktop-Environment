"""Pins the GObject introspection versions used across HyperNova."""

import gi

gi.require_version("Gdk", "3.0")
gi.require_version("GdkX11", "3.0")
gi.require_version("Gtk", "3.0")
gi.require_version("Wnck", "3.0")

from gi.repository import (  # noqa: E402
    Gdk,
    GdkPixbuf,
    GdkX11,
    Gio,
    GLib,
    GObject,
    Gtk,
    Pango,
    Wnck,
)

__all__ = ["Gdk", "GdkPixbuf", "GdkX11", "Gio", "GLib", "GObject", "Gtk", "Pango", "Wnck"]
