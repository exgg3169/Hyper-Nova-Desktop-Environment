"""Built-in wallpapers, drawn with cairo so they scale to any resolution."""

import math
import os

import cairo

from .gtk import Gdk, GdkPixbuf, GLib


def _hex(color, alpha=1.0):
    color = color.lstrip("#")
    r, g, b = (int(color[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return r, g, b, alpha


def _linear(x0, y0, x1, y1, stops):
    pat = cairo.LinearGradient(x0, y0, x1, y1)
    for offset, color, *alpha in stops:
        pat.add_color_stop_rgba(offset, *_hex(color, alpha[0] if alpha else 1.0))
    return pat


def _soft_ellipse(cr, cx, cy, rx, ry, color, alpha):
    cr.save()
    cr.translate(cx, cy)
    cr.scale(rx, ry)
    pat = cairo.RadialGradient(0, 0, 0, 0, 0, 1)
    pat.add_color_stop_rgba(0, *_hex(color, alpha))
    pat.add_color_stop_rgba(1, *_hex(color, 0))
    cr.set_source(pat)
    cr.arc(0, 0, 1, 0, 2 * math.pi)
    cr.fill()
    cr.restore()


def bliss(cr, w, h):
    """Blue sky over rolling green hills."""
    cr.set_source(_linear(0, 0, 0, h * 0.75, [(0, "#1b5bd4"), (0.55, "#4f95ee"), (1, "#b4d5fa")]))
    cr.paint()
    for cx, cy, rx, ry in [(0.18, 0.2, 0.16, 0.06), (0.3, 0.14, 0.1, 0.045), (0.62, 0.3, 0.2, 0.06),
                           (0.78, 0.22, 0.12, 0.05), (0.9, 0.12, 0.08, 0.03)]:
        _soft_ellipse(cr, cx * w, cy * h, rx * w, ry * h, "#ffffff", 0.85)
    cr.move_to(0, h * 0.64)
    cr.curve_to(w * 0.28, h * 0.5, w * 0.62, h * 0.56, w, h * 0.62)
    cr.line_to(w, h)
    cr.line_to(0, h)
    cr.close_path()
    cr.set_source(_linear(0, h * 0.5, 0, h, [(0, "#5fae2e"), (1, "#23660b")]))
    cr.fill()
    cr.move_to(0, h * 0.84)
    cr.curve_to(w * 0.3, h * 0.6, w * 0.66, h * 0.64, w, h * 0.76)
    cr.line_to(w, h)
    cr.line_to(0, h)
    cr.close_path()
    cr.set_source(_linear(0, h * 0.62, 0, h, [(0, "#8fd44c"), (0.5, "#56a824"), (1, "#2f7d12")]))
    cr.fill()


def harmony(cr, w, h):
    """Deep blue with glowing aurora ribbons."""
    pat = cairo.RadialGradient(w * 0.5, h * 0.45, 0, w * 0.5, h * 0.45, max(w, h) * 0.75)
    pat.add_color_stop_rgba(0, *_hex("#2a9be8"))
    pat.add_color_stop_rgba(0.45, *_hex("#0e5aa7"))
    pat.add_color_stop_rgba(1, *_hex("#031a3d"))
    cr.set_source(pat)
    cr.paint()
    cr.set_operator(cairo.OPERATOR_ADD)
    for i, color in enumerate(["#43c6ff", "#7ee8fa", "#3d7bff", "#a0f0ff"]):
        cr.save()
        cr.translate(0, h * (0.35 + i * 0.07))
        cr.move_to(-w * 0.1, h * 0.2)
        cr.curve_to(w * 0.25, -h * 0.25, w * 0.6, h * 0.35, w * 1.1, -h * 0.05)
        cr.set_line_width(h * (0.05 - i * 0.008))
        cr.set_source(_linear(0, 0, w, 0, [(0, color, 0), (0.5, color, 0.35), (1, color, 0)]))
        cr.stroke()
        cr.restore()
    cr.set_operator(cairo.OPERATOR_OVER)
    _soft_ellipse(cr, w * 0.5, h * 0.48, w * 0.12, w * 0.12, "#ffffff", 0.18)


def hero(cr, w, h):
    """A glowing four-pane window floating in dark blue light."""
    cr.set_source(_linear(0, 0, w, h, [(0, "#00132e"), (0.6, "#002f6c"), (1, "#004a9f")]))
    cr.paint()
    ox, oy = w * 0.54, h * 0.18
    pw, ph, gap = w * 0.13, h * 0.3, w * 0.01
    panes = []
    for col in range(2):
        for row in range(2):
            x0 = ox + col * (pw + gap)
            x1 = x0 + pw
            skew0, skew1 = 0.08 * (x0 - ox) / pw, 0.08 * (x1 - ox) / pw
            y0 = oy + row * (ph + gap) + h * skew0 * 0.4
            y1 = oy + row * (ph + gap) + h * skew1 * 0.4
            panes.append([(x0, y0 + ph * 0.0), (x1, y1 - ph * 0.05), (x1, y1 + ph * 0.95), (x0, y0 + ph)])
    cr.set_operator(cairo.OPERATOR_ADD)
    for pane in panes:
        cr.move_to(0, h * 0.95)
        cr.line_to(*pane[0])
        cr.line_to(*pane[3])
        cr.close_path()
        cr.set_source(_linear(0, h, pane[0][0], pane[0][1], [(0, "#0a4ea8", 0), (1, "#3a9bff", 0.22)]))
        cr.fill()
    cr.set_operator(cairo.OPERATOR_OVER)
    for pane in panes:
        cr.move_to(*pane[0])
        for pt in pane[1:]:
            cr.line_to(*pt)
        cr.close_path()
        cr.set_source(_linear(pane[0][0], pane[0][1], pane[2][0], pane[2][1],
                              [(0, "#8fd0ff"), (0.5, "#2f8cff"), (1, "#0d5fd8")]))
        cr.fill()
    _soft_ellipse(cr, ox + pw, oy + ph, pw * 2.2, ph * 1.6, "#3a9bff", 0.25)


def sierra(cr, w, h):
    """Layered mountains under an evening sky."""
    cr.set_source(_linear(0, 0, 0, h, [(0, "#2b2d6e"), (0.45, "#b35f86"), (0.75, "#f2a36b"), (1, "#f7c98b")]))
    cr.paint()
    _soft_ellipse(cr, w * 0.7, h * 0.52, w * 0.3, h * 0.2, "#ffd9a0", 0.45)
    ranges = [
        (0.55, "#7a4a86", [0, .08, .13, .22, .3, .38, .47, .55, .63, .72, .8, .9, 1],
         [.05, .02, .09, .0, .07, .03, .1, .01, .06, .02, .08, .03, .06]),
        (0.66, "#4f2e6b", [0, .1, .18, .27, .36, .46, .58, .67, .78, .88, 1],
         [.06, .01, .08, .03, .09, .02, .07, .0, .06, .02, .05]),
        (0.8, "#2a1a45", [0, .12, .24, .35, .5, .62, .75, .86, 1],
         [.04, .0, .06, .02, .07, .01, .05, .02, .04]),
    ]
    for base, color, xs, ys in ranges:
        cr.move_to(0, h)
        for x, y in zip(xs, ys):
            cr.line_to(x * w, (base - 0.12 + y) * h)
        cr.line_to(w, h)
        cr.close_path()
        cr.set_source_rgba(*_hex(color))
        cr.fill()


def nova(cr, w, h):
    """HyperNova's own nebula."""
    cr.set_source_rgb(*_hex("#07071a")[:3])
    cr.paint()
    for cx, cy, r, color, a in [(0.25, 0.3, 0.5, "#6d28d9", 0.7), (0.78, 0.7, 0.45, "#0891b2", 0.6),
                                (0.6, 0.2, 0.3, "#db2777", 0.45), (0.5, 0.55, 0.15, "#e0e7ff", 0.35)]:
        _soft_ellipse(cr, cx * w, cy * h, r * w, r * w, color, a)
    cr.set_source_rgba(1, 1, 1, 0.8)
    seed = 1234567
    for _ in range(260):
        seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
        x = (seed % 10000) / 10000 * w
        seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
        y = (seed % 10000) / 10000 * h
        cr.arc(x, y, 0.6 + (seed % 3) * 0.4, 0, 2 * math.pi)
        cr.fill()


BUILTIN = {
    "bliss": ("Huzur", bliss),
    "harmony": ("Aurora", harmony),
    "hero": ("Işık Penceresi", hero),
    "sierra": ("Gün Batımı", sierra),
    "nova": ("Nova Bulutsusu", nova),
}


def resolve(setting, style):
    """Returns ("builtin", id) or ("image", path) for a wallpaper setting."""
    if setting and setting.startswith("builtin:") and setting[8:] in BUILTIN:
        return "builtin", setting[8:]
    if setting and os.path.isfile(setting):
        return "image", setting
    return "builtin", style.wallpaper


def paint(cr, w, h, spec):
    kind, value = spec
    if kind == "image":
        try:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file(value)
        except GLib.Error:
            nova(cr, w, h)
            return
        scale = max(w / pixbuf.get_width(), h / pixbuf.get_height())
        cr.save()
        cr.translate((w - pixbuf.get_width() * scale) / 2, (h - pixbuf.get_height() * scale) / 2)
        cr.scale(scale, scale)
        Gdk.cairo_set_source_pixbuf(cr, pixbuf, 0, 0)
        cr.paint()
        cr.restore()
        return
    BUILTIN.get(value, BUILTIN["nova"])[1](cr, w, h)


def render_surface(w, h, spec):
    surface = cairo.ImageSurface(cairo.FORMAT_RGB24, max(1, w), max(1, h))
    paint(cairo.Context(surface), w, h, spec)
    return surface
