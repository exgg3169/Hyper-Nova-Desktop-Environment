"""The HyperNova logo, drawn with cairo at any size."""

import math

import cairo

from .gtk import Gdk


def draw(cr, size, monochrome=None):
    s = size / 64.0
    cr.save()
    cr.scale(s, s)
    points = []
    for i in range(8):
        angle = -math.pi / 2 + i * math.pi / 4
        radius = 29 if i % 2 == 0 else 10
        points.append((32 + radius * math.cos(angle), 32 + radius * math.sin(angle)))
    cr.move_to(*points[0])
    for pt in points[1:]:
        cr.line_to(*pt)
    cr.close_path()
    if monochrome:
        cr.set_source_rgba(*monochrome)
        cr.fill()
    else:
        ray = cairo.LinearGradient(0, 0, 64, 64)
        ray.add_color_stop_rgb(0, 0.13, 0.83, 0.93)
        ray.add_color_stop_rgb(1, 0.66, 0.33, 0.97)
        cr.set_source(ray)
        cr.fill()
        core = cairo.RadialGradient(32, 32, 0, 32, 32, 15)
        core.add_color_stop_rgba(0, 1, 1, 1, 1)
        core.add_color_stop_rgba(0.4, 0.77, 0.71, 0.99, 0.95)
        core.add_color_stop_rgba(1, 0.49, 0.23, 0.93, 0)
        cr.set_source(core)
        cr.arc(32, 32, 15, 0, 2 * math.pi)
        cr.fill()
    cr.restore()


def surface(size, monochrome=None):
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, size, size)
    draw(cairo.Context(surf), size, monochrome)
    return surf


def pixbuf(size, monochrome=None):
    return Gdk.pixbuf_get_from_surface(surface(size, monochrome), 0, 0, size, size)


def write_png(path, size):
    surface(size).write_to_png(path)
