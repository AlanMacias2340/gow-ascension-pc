#!/usr/bin/env python3
"""Draws Ascension's emblem (an omega inside a ring of Greek key, white on
black, a sibling of Sparta's helmet and Olympus's temple) and makes every
icon from it:

    packaging/emblem.png               1024 x 1024, transparent
    packaging/icon.png                 256 x 256, on a black rounded square
    packaging/windows/ascension.ico    16 to 256 px
    packaging/macos/Ascension.icns     (macOS only: needs iconutil)

The omega is the series' own sign, and the one God of War: Ascension spins
on its loading screen.

Needs Pillow. The icons are committed, so a build does not run this; run it
again after changing the drawing.

    python3 packaging/make_icons.py
"""
import math
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
SIZE = 1024
SS = 4  # drawn this many times larger, then scaled down smoothly
WHITE = (255, 255, 255, 255)
CLEAR = (0, 0, 0, 0)


def ring(d, c, k):
    """Two circles with a Greek key (meander) between them, as on the other ports."""
    outer, inner = 470 * k, 350 * k
    width = 16 * k
    d.ellipse((c - outer, c - outer, c + outer, c + outer), outline=WHITE, width=int(width))
    d.ellipse((c - inner, c - inner, c + inner, c + inner), outline=WHITE, width=int(width))
    units = 28
    band_in, band_out = inner + 22 * k, outer - 22 * k
    depth = band_out - band_in

    def polar(angle, radius):
        return c + radius * math.cos(angle), c + radius * math.sin(angle)

    # One key unit in (along, across) fractions of its cell: a square spiral.
    key = [(0.0, 0.0), (0.0, 1.0), (0.8, 1.0), (0.8, 0.25), (0.35, 0.25), (0.35, 0.65), (0.55, 0.65)]
    for u in range(units):
        start = 2 * math.pi * u / units
        span = 2 * math.pi / units
        points = [(start + along * span, band_in + across * depth) for along, across in key]
        pixels = []
        for (a0, r0), (a1, r1) in zip(points, points[1:]):
            # Many small steps along each side so straight parts follow the circle.
            steps = max(2, int(abs(a1 - a0) / span * 12) + 1)
            for i in range(steps + 1):
                t = i / steps
                pixels.append(polar(a0 + (a1 - a0) * t, r0 + (r1 - r0) * t))
        d.line(pixels, fill=WHITE, width=int(18 * k), joint='curve')
        d.line([polar(start, band_in), polar(start + span, band_in)], fill=WHITE, width=int(18 * k))


def omega(d, c, k):
    """A capital omega: a thick ring open at the bottom, its two ends turning
    out into feet on a common baseline."""
    cx, cy = c, c - 30 * k          # the bowl sits a little above the centre
    r_out, r_in = 205 * k, 140 * k  # outer and inner edge of the stroke
    gap = 34                        # half the opening at the bottom, in degrees
    base = cy + 215 * k             # the feet's baseline (their lower edge)
    foot_h = 46 * k

    # The bowl, as a polygon between the two radii, so the ends are clean cuts.
    a0, a1 = math.radians(90 + gap), math.radians(90 - gap + 360)
    steps = 160
    outer = [(cx + r_out * math.cos(a0 + (a1 - a0) * i / steps),
              cy + r_out * math.sin(a0 + (a1 - a0) * i / steps)) for i in range(steps + 1)]
    inner = [(cx + r_in * math.cos(a1 - (a1 - a0) * i / steps),
              cy + r_in * math.sin(a1 - (a1 - a0) * i / steps)) for i in range(steps + 1)]
    d.polygon(outer + inner, fill=WHITE)

    # The legs: each end of the bowl runs down to the baseline, flaring inward
    # a little, and ends in a foot that reaches outward.
    for side in (-1, 1):
        # side -1 is the left end (angle past 90 degrees), +1 the right.
        ang = math.radians(90 - side * gap)
        ox, oy = cx + r_out * math.cos(ang), cy + r_out * math.sin(ang)
        ix, iy = cx + r_in * math.cos(ang), cy + r_in * math.sin(ang)
        # The leg: from the cut end straight down to the foot.
        leg = [(ix, iy), (ox, oy), (ox - side * 6 * k, base - foot_h), (ix + side * 10 * k, base - foot_h)]
        d.polygon(leg, fill=WHITE)
        # The foot: a bar from the leg's inner edge out past the bowl.
        x_in = ix + side * 10 * k
        x_out = cx + side * (r_out + 55 * k)
        x0, x1 = sorted((x_in, x_out))
        d.rectangle((x0, base - foot_h, x1, base), fill=WHITE)
        # A small serif lift at the outer tip of the foot.
        tip = x_out
        d.polygon([(tip, base - foot_h), (tip, base - foot_h - 22 * k),
                   (tip - side * 26 * k, base - foot_h)], fill=WHITE)


def emblem():
    n = SIZE * SS
    img = Image.new('RGBA', (n, n), CLEAR)
    d = ImageDraw.Draw(img)
    c = n / 2
    k = n / 1024  # the drawing is laid out on a 1024 grid
    ring(d, c, k)
    omega(d, c, k)
    return img.resize((SIZE, SIZE), Image.LANCZOS)


def on_square(picture, size, radius=0.18):
    """The emblem on a black rounded square, as Sparta's icon is."""
    n = size * SS
    square = Image.new('RGBA', (n, n), CLEAR)
    ImageDraw.Draw(square).rounded_rectangle((0, 0, n - 1, n - 1), radius=int(n * radius), fill=(0, 0, 0, 255))
    inner = picture.resize((int(n * 0.86), int(n * 0.86)), Image.LANCZOS)
    square.alpha_composite(inner, ((n - inner.size[0]) // 2, (n - inner.size[1]) // 2))
    return square.resize((size, size), Image.LANCZOS)


def windows(picture, out):
    out.parent.mkdir(parents=True, exist_ok=True)
    big = on_square(picture, 256)
    big.save(out, sizes=[(s, s) for s in (16, 24, 32, 48, 64, 128, 256)])


def macos(picture, out):
    if not shutil.which('iconutil'):
        print('no iconutil: the .icns is left as it is')
        return
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        iconset = Path(tmp) / 'Ascension.iconset'
        iconset.mkdir()
        for size in (16, 32, 128, 256, 512):
            on_square(picture, size).save(iconset / f'icon_{size}x{size}.png')
            on_square(picture, size * 2).save(iconset / f'icon_{size}x{size}@2x.png')
        subprocess.run(['iconutil', '-c', 'icns', str(iconset), '-o', str(out)], check=True)


def main():
    picture = emblem()
    picture.save(HERE / 'emblem.png')
    on_square(picture, 256).save(HERE / 'icon.png')
    windows(picture, HERE / 'windows' / 'ascension.ico')
    macos(picture, HERE / 'macos' / 'Ascension.icns')
    return 0


if __name__ == '__main__':
    sys.exit(main())
