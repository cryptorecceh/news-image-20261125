#!/usr/bin/env python3
"""Wednesday 25 November 2026 world news, summed up in one 1024x1024 image.

Pure Python 3.13 standard library: no third-party imports, no network,
no clock, no randomness. The page (masthead, timeline, three lead panels,
twelve medium stories, world map, 39-item story list, date check) is drawn
procedurally from the tables at the bottom of this file, and the PNG bytes
are encoded here as well, on top of stdlib zlib.

Run:  python3 main.py [--output entry.png] [--check]
The default output is /output/entry.png (or $MAKEFUN_OUTPUT_DIR/entry.png).
Two runs write byte-identical output.
"""

import argparse
import base64
import math
import os
import struct
import sys
import zlib

# ------------------------------------------------------------------ palette
PAPER = (247, 243, 235)
INK = (24, 24, 24)
RED = (166, 38, 38)
NAVY = (15, 28, 46)
GOLD = (212, 164, 65)
GREY = (96, 90, 74)
OCEAN = (214, 228, 232)
LAND = (232, 220, 190)
DUSK = (38, 52, 74)
CREAM = (239, 231, 214)
BURST = (205, 72, 25)
WHITE = (255, 255, 255)

# ------------------------------------------------------------------ fonts
# 1-bit bitmap fonts, rasterised from Liberation fonts when the first
# version of this renderer was built. Blob layout: glyphs in codepoint
# order; each glyph starts with one width byte, then
# ceil(width/8)*height bitmap bytes (MSB-first, row-major).
# CHARS is ASCII 32-126 plus middle dot, em dash, right quote, euro.
EXTRA = ["\u00b7", "\u2014", "\u2019", "\u20ac"]
CHARS = [chr(c) for c in range(32, 127)] + EXTRA

F_SANS10 = "AwAAAAAAAAAAAAAAAAADAAAAQEBAQEAAQAAAAAQAAACgIAAAAAAAAAAABgAAAAgI/ED4EBAAAAAGAAAAeIBgMAgIeAAAAAkAAAAAAABiAIQAgABrABQAFAAjAAAAAAAAAAcAAAA4CDBklIh0AAAAAgAAAAAAAAAAAAAAAAAEAAAAIEBAQEBAQEAgAAQAAACAQAAgICAAQIAABAAAAADgYCAAAAAAAAAGAAAAAAAAeAAAAAAAAAMAAAAAAAAAAABAQAAABAAAAAAAAABgAAAAAAADAAAAAAAAAAAAQAAAAAMAAAAgAEBAQICAAAAABgAAAHBIiIiISHAAAAAGAAAAIGAgICAgeAAAAAYAAABwSAgQIEB4AAAABgAAAHAICDAICHAAAAAGAAAAEDAwUBD4EAAAAAYAAAB4QHAICAhwAAAABgAAADBAcEhISDAAAAAGAAAAeAgQICAgIAAAAAYAAABwSEhwSEhwAAAABgAAAHBICEh4CHAAAAADAAAAAABAAAAAQAAAAAMAAAAAAEAAAABAQAAABgAAAAAIMMAwCAAAAAAGAAAAAAB4AHgAAAAAAAYAAAAAQDAIMEAAAAAABgAAAHBICBAgACAAAAALAAAAAAAAHwAggE4AUgASgFsAQAAeAAAAAAAHAAAAECAoSHxEggAAAAcAAAB4RER4RER4AAAACAAAADxCQEBAQjwAAAAIAAAAeERCQkJEeAAAAAcAAAB8QEB8QEB8AAAABwAAAHxAQHhAQEAAAAAIAAAAPEJADkJCPAAAAAgAAABERER8REREAAAAAwAAAEBAQEBAQEAAAAAFAAAAMBAQEBCQcAAAAAcAAABESFBwUEhEAAAABgAAAEBAQEBAQHgAAAAJAAAAAAAAQwBjAGUARQBRAFkASQAAAAAAAAAIAAAAYmJSUkpGQgAAAAgAAAA8QkKCQkI8AAAABwAAAHhERER4QEAAAAAIAAAAPEJCgkJCPAgMAAgAAAB8RER4SEREAAAABwAAADhEQDgERHgAAAAHAAAA/BAQEBAQEAAAAAgAAABEREREREQ4AAAABwAAAIREREgoMBAAAAAKAAAAAAAAiICMgESAVQBRADMAIwAAAAAAAAAHAAAARAgwEChIRAAAAAcAAABESCgwEBAQAAAABwAAAHwIECAgQPwAAAADAAAAQEBAQEBAQEBAAAMAAACAgABAQAAgAAAAAwAAAMBAQEBAQEBAwAAFAAAAIFAQgAAAAAAAAAYAAAAAAAAAAAAAAPgABAAAQAAAAAAAAAAAAAAGAAAAAABwCHiIaAAAAAYAAABAQHBISEhwAAAABQAAAAAAcECAQHAAAAAGAAAACAh4SIhIeAAAAAYAAAAAAHBI+EBwAAAAAwAAAGBA4EBAQEAAAAAGAAAAAAB4CIgIaAhwAAYAAABAQHBISEhIAAAAAwAAAAAAQEBAQEAAAAADAAAAAABAQEBAQECAAAUAAABAQFBgYFBIAAAAAwAAAEBAQEBAQEAAAAAJAAAAAAAAAAAAAHYASQBJAEkASQAAAAAAAAAGAAAAAABwSEhISAAAAAYAAAAAAHBIiEhwAAAABgAAAAAAcEhISHBAQAAGAAAAAAB4SIhIeAgIAAQAAAAAAGBAQEBAAAAABQAAAAAAcEAwCHAAAAADAAAAAEDAQEBAQAAAAAYAAAAAAEhISEhoAAAABQAAAAAAiFBQUCAAAAAIAAAAAACSmmhsZAAAAAUAAAAAAFBQIFCIAAAABQAAAAAAiFBQMCAgQAAFAAAAAABwECBA8AAAAAQAAAAgQEBAwEBAQCAAAwAAAEBAQEBAQEBAQAAEAAAAwEBAQCBAQEDAAAYAAAAAAGAYAAAAAAAABAAAAAAAAEAAAAAAAAAKAAAAAAAAAAAAAAAAAAD/wAAAAAAAAAAAAAADAAAAQAAAAAAAAAAAAAYAAAA4QPBA8EA4AAAA"
F_SANS12 = "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"
F_SANSB10 = "AwAAAAAAAAAAAAAAAAAEAAAAQEBAQEAAQAAAAAUAAABQUFAAAAAAAAAABgAAACgIeFD4UBAAAAAGAAAAeMBgeAgIeAAAAAkAAAAAAABiAJQAlABrABSAFIAjAAAAAAAAAAgAAAA4KDh0XEx+AAAAAwAAAEBAQAAAAAAAAAAEAAAAIEBAQEBAQEAgAAQAAADAQGBgYGBgQMAABAAAAEDwYCAAAAAAAAAGAAAAACAg+DAgAAAAAAMAAAAAAAAAAABAQEAABAAAAAAAAADgAAAAAAADAAAAAAAAAAAAQAAAAAMAAABgQEBAQMCAAAAABgAAAHBYyMjIWHAAAAAGAAAAcHAwMDAweAAAAAYAAABwWBgQIED4AAAABgAAAHBYGDAYyHAAAAAGAAAAGDg4WNj8GAAAAAYAAAB4QHBYCNhwAAAABgAAADBYwPjISHAAAAAGAAAA+BgQMCAgIAAAAAYAAABwSFhwyMhwAAAABgAAAHDYyHgIWHAAAAAEAAAAAABAAAAAQAAAAAQAAAAAAEAAAABAAEAABgAAAAAIcMBwCAAAAAAGAAAAAAD4APgAAAAAAAYAAAAAwDgIOMAAAAAABwAAAHhICBgwADAAAAAKAAAAAAAAHgAhgE6AUoACgAaAWwBAAD4AAAAIAAAAGDgoLHxExgAAAAgAAAB8RER8RkZ8AAAACAAAADxmQMBAZjwAAAAIAAAAeExGRkZMeAAAAAcAAAB8QEB8QEB8AAAABwAAAHxAQHxAQEAAAAAIAAAAPGZAzkJmPAAAAAgAAABGRkZ+RkZGAAAAAwAAAEBAQEBAQEAAAAAGAAAAOBgYGBjYcAAAAAgAAABESFBwSExGAAAABwAAAEBAQEBAQHwAAAAJAAAAAAAAYwBnAGcAVwBbAFsASwAAAAAAAAAIAAAAZmZ2Vl5ORgAAAAgAAAA8ZkLCQmY8AAAABwAAAHhMREx4QEAAAAAIAAAAPGZCwkJmPAgOAAgAAAB8RkZ8TERGAAAABwAAAHhMYDwERHgAAAAHAAAA/DAwMDAwMAAAAAgAAABGRkZGRmQ4AAAABwAAAMRETGgoODAAAAAKAAAAAAAAzIDMgF2AVYB3AHMAMwAAAAAAAAAHAAAARGg4MDhsxAAAAAcAAADEbCgwEBAQAAAABwAAAHwIEDBgQPwAAAAEAAAAYEBAQEBAQEBgAAMAAACAwEBAQEBgAAAABAAAAOBgYGBgYGBg4AAGAAAAMHBIyAAAAAAAAAYAAAAAAAAAAAAAAPgABAAAQCAAAAAAAAAAAAAGAAAAAABwGHjYbAAAAAcAAABAQHhMTEx4AAAABgAAAAAAcEjASHAAAAAHAAAACAh4SMhIeAAAAAYAAAAAAHBI+EB4AAAABAAAAGBA4EBAQEAAAAAHAAAAAAB4SMhIeAh4AAcAAABAQHhISEhIAAAAAwAAAEAAQEBAQEAAAAADAAAAQABAQEBAQEDAAAYAAABAQFhQcFhIAAAAAwAAAEBAQEBAQEAAAAAJAAAAAAAAAAAAAFsASQBJAEkASQAAAAAAAAAHAAAAAABYSEhISAAAAAcAAAAAAHhMzEh4AAAABwAAAAAAeExMTHhAQAAHAAAAAAB4SMhIeAgIAAQAAAAAAHBAQEBAAAAABgAAAAAAcEB4CHgAAAAEAAAAAEDgQEBAYAAAAAcAAAAAAEhISEh4AAAABgAAAAAAyEhYcDAAAAAIAAAAAACb2mpmZgAAAAYAAAAAAEhwMHDIAAAABgAAAAAAyEhYMDAgYAAFAAAAAABwMCBA+AAAAAQAAAAwYGBgwGBgYDAAAwAAAEBAQEBAQEBAQAAEAAAAwGBgYDBgYGDAAAYAAAAAAGAYAAAAAAAABAAAAAAAAEAAAAAAAAAKAAAAAAAAAAAAAAAAAAD/wAAAAAAAAAAAAAADAAAAQEBAAAAAAAAAAAYAAAA4QOBA4EA4AAAA"
F_SANSB15 = "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"
F_SANSB22 = "BwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAIAAAAAAA4ODg4ODg4ODg4AAA4ODgAAAAAAAsAAAAAAAAAAAAAc4AzgDOAM4AzgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA0AAAAAAAAAAAAADGAMYAhACEB/8H/wGMAQgDGA/+B/4DGAIQBjAGMAAAAAAAAAAAAAAA0AAAAAAAAAAAIAH4A/4HLgcmByAH4AP4AfwAfgAnBicHJwfvA/4B+AAgACAAAAAAAAABQAAAAAAAAAAAAAAAAAAAA8BwB+BgBjDABjHABjGABjMABjd4B+b8A8zOAB3GABnGADHGAHDOAGD8AMB4AAAAAAAAAAAAAAAAAAAAAQAAAAAAAAAAAAAAPAD+AMcAxwDOAPwA+AHwg7HHOYcfhw8Hj4P/4fjgAAAAAAAAAAAAAGAAAAAABwcHBwcAAAAAAAAAAAAAAAAAAAAAgAAAAADhwcODg4OHBwcHBwcHA4ODg4HBwOCAAAAADgcHA4OBwcHBwcHBwcHBwcODhwcOAJAAAAAAAAAAAAABgAGABbAP8APAA+AHcAIgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAANAAAAAAAAAAAAAAAAAAAHAAcABwAHAH/wf/AHAAcABwAHAAcAAAAAAAAAAAAAAAAAAAAHAAAAAAAAAAAAAAAAAAAAAAA4ODgYMDAAAAgAAAAAAAAAAAAAAAAAfHx8AAAAAAAAAAAABwAAAAAAAAAAAAAAAAAAAAAAeHh4AAAAAAAHAAAAABwcGBg4ODgwMHBwcGBgYOAAAAAAAA0AAAAAAAAAAAAADwA/wDnAcOBw4HDgcOBw4HDgcOBw4HDgOcAfwA8AAAAAAAAAAAAAAA0AAAAAAAAAAAAABwAfAD8AdwAHAAcABwAHAAcABwAHAAcABwB/8H/wAAAAAAAAAAAAAA0AAAAAAAAAAAAAH4A/wHngcOAA4ADgAcADwAeAHgA8ADgAeAB/4H/gAAAAAAAAAAAAAA0AAAAAAAAAAAAAH4A/wHngcOAA4AHgD4APgAPgAOAA4HDgf+A/wB+AAAAAAAAAAAAAAA0AAAAAAAAAAAAAA8ADwAfAD8ANwB3AGcAxwHHAYcD/8P/wAcABwAHAAAAAAAAAAAAAAA0AAAAAAAAAAAAAP+A/4HgAcABwAHeAf8B/4ADgAPAA8HDgeeA/wB+AAAAAAAAAAAAAAA0AAAAAAAAAAAAAD4AfwD3gcOBwAHeAf8B54HDgcOBw4HDgPeAfwA+AAAAAAAAAAAAAAA0AAAAAAAAAAAAAf+B/4ADgAOABwAOAA4AHAAcADgAOAA4AHgAcABwAAAAAAAAAAAAAAA0AAAAAAAAAAAAAH4A/wHngcOBw4DjgH8AfwHjgcOBw8HDgeOA/wB+AAAAAAAAAAAAAAA0AAAAAAAAAAAAAHwA/wHnAcOBw4HDgcOB54D/gHuAA4HDge8A/wB8AAAAAAAAAAAAAAAgAAAAAAAAAADg4OAAAAAAAADg4OAAAAAAACAAAAAAAAAAAODg4AAAAAAAAODg4GBgwAAANAAAAAAAAAAAAAAAAAAAAEADwB/AfgH4AcABwAH4AH4AD8ADwABAAAAAAAAAAAAAAAAANAAAAAAAAAAAAAAAAAAAAAAAAf/B/8AAAAAAAAH/wf/AAAAAAAAAAAAAAAAAAAAAAAAANAAAAAAAAAAAAAAAAAABAAHgAfgAPwAPwAHAAcAPwD8B+AHgAQAAAAAAAAAAAAAAAAAAOAAAAAAAAAAAAAA/AH+A98HhwcHAAcAHgA8AHAAcAAAAAAAcABwAHAAAAAAAAAAAAAAAWAAAAAAAAAAAAAAAAAAAAAP4AA/+ABgDADABgGHswMP8wMYYwIwYQYwYwYgYwYgwwYwxgI/fAMeOAGAAAHAEAB/8AAfwAAAAAAAAAEAAAAAAAAAAAAAADwAPAB+AH4A5gDnAOcBw4HDgf+D/8OBx4HHAOcA4AAAAAAAAAAAAAEAAAAAAAAAAAAAB/8H/4eHx4HHgceDx/+H/4eDx4HngOeB54PH/8f/AAAAAAAAAAAAAAEAAAAAAAAAAAAAAH4B/4P/w8HngMcABwAHAAcABwAHgMPB4//A/4B+AAAAAAAAAAAAAAEAAAAAAAAAAAAAB/wH/wefh4PHgeeA54DngOeA54HngceDx4+H/wf8AAAAAAAAAAAAAADwAAAAAAAAAAAAB/+H/4eAB4AHgAeAB/+H/4eAB4AHgAeAB4AH/8f/wAAAAAAAAAAAAADgAAAAAAAAAAAAB/+H/4eAB4AHgAeAB/8H/weAB4AHgAeAB4AHgAeAAAAAAAAAAAAAAAEgAAAAAAAAAAAAAAAAAAAAfwAB/8AD/+ADweAHgMAHAAAHAAAHB/AHB/AHAHAHgHADwPAD//AB/8AAfwAAAAAAAAAAAAAAAAAAAAABAAAAAAAAAAAAAAeBx4HHgceBx4HHgcf/x//H/8eBx4HHgceBx4HHgcAAAAAAAAAAAAAAcAAAAAAHh4eHh4eHh4eHh4eHh4eAAAAAAADQAAAAAAAAAAAAAH4AfgAeAA4ADgAOAA4ADgAOAA4HDgceB/wD/AHwAAAAAAAAAAAAAAEAAAAAAAAAAAAAB4Hng8eHh48Hnge8B/gH/AfcB44HjweHh4PHgceA4AAAAAAAAAAAAADgAAAAAAAAAAAAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AH/4f/gAAAAAAAAAAAAAEwAAAAAAAAAAAAAAAAAAAHwPgHwPgH4PgH4PgH4fgHYbgHcbgHM7gHMzgHOzgHHzgHHjgHHjgHDjgHDDgAAAAAAAAAAAAAAAAAAAABAAAAAAAAAAAAAAeAx8DH4Mfgx3DHcMc4xzjHHMcOxw7HB8cHxwPHA8AAAAAAAAAAAAABIAAAAAAAAAAAAAAAAAAAAH8AAP/AA//gA8HgB4DwBwBwBwBwBwBwBwBwBwBwB4DwA8HgAf/AAP+AAH4AAAAAAAAAAAAAAAAAAAAAAPAAAAAAAAAAAAAH/gf/h4+Hg8eBx4HHg8ePh/8H/geAB4AHgAeAB4AAAAAAAAAAAAAAASAAAAAAAAAAAAAAAAAAAAB/AAD/gAP/4APB4AeA8AcAcAcAcAcAcAcAcAcAcAeA8APA4APj4AH/wAB/AAAOAAAPAAAH4AAD4AAAAAEAAAAAAAAAAAAAB/8H/8eHx4HngeeBx4fH/4f/B4cHh4eDh4PHgeeA4AAAAAAAAAAAAADwAAAAAAAAAAAAAP4D/wPHh4OHgAPAA/wA/wAfgAPHAccDx8eD/4D+AAAAAAAAAAAAAADgAAAAAAAAAAAAD/+P/4B4AHAAcABwAHAAcABwAHAAcABwAHAAcABwAAAAAAAAAAAAAAEAAAAAAAAAAAAABwHnAecB5wHnAecB5wHnAecB54HngcODw//B/4B+AAAAAAAAAAAAAADwAAAAAAAAAAAADwHHAccDx4ODg4OHAccBxwHOAO4A7gD8AHwAfAA4AAAAAAAAAAAAAAFQAAAAAAAAAAAAAAAAAAAOBwePD4cHD4cHD4cHDYcHHc4Dnc4Dmc4DmM4DuNwB+PwB+PwB8PgA8HgA8HgAAAAAAAAAAAAAAAAAAAAA8AAAAAAAAAAAAAcDw4ODxwHPAO4A/AB8AHwAfADuAc8BxwODhwPHAcAAAAAAAAAAAAAA8AAAAAAAAAAAAAcBx4ODh4PHAc8A7gD8AHwAeAA4ADgAOAA4ADgAOAAAAAAAAAAAAAAA4AAAAAAAAAAAAAf/B/8ADwAOAB4APAA4AHAA4AHgA8ADgAeAB/+H/4AAAAAAAAAAAAAAgAAAAAfn5wcHBwcHBwcHBwcHBwcHBwcH5+BwAAAADgYGBgcHBwMDA4ODgYGBwcAAAAAAAIAAAAAPz8HBwcHBwcHBwcHBwcHBwcHBz8/A0AAAAAAAAAAAAADwAPgA2AHcAYwDjAMOAwYHBwYDAAAAAAAAAAAAAAAAAAAAAAAAAAAA0AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAP/wAAAAAAgAAAAAcDgMAAAAAAAAAAAAAAAAAAAAAAAADQAAAAAAAAAAAAAAAAAAAAAPgD/AOcAw4ADgH+B/4HDgceBz4H7wPHAAAAAAAAAAAAAADgAAAAAAAAAAOAA4ADgAOAA7wD/gPPA4cDhwOHg4eDhwOHA88D/gc8AAAAAAAAAAAAAADQAAAAAAAAAAAAAAAAAAAAAPgD/AOOBw4HAAcABwAHAAcOA44D/AD4AAAAAAAAAAAAAADgAAAAAAAAAAAHAAcABwAHAecD/wOPBw8HBwcHBwcHBwcPA48D/wHnAAAAAAAAAAAAAADQAAAAAAAAAAAAAAAAAAAAAPgD/AOOBw4HDgf+B/4HAAcAA44D/AD4AAAAAAAAAAAAAACAAAAAAePjg4/v44ODg4ODg4ODg4AAAAAAAOAAAAAAAAAAAAAAAAAAAAAB5wP/A48HDwcHBwcHBwcHBw8DjwP/AecABwAHA44D/gD4AOAAAAAAAAAAA4ADgAOAA4ADvAP+A88DhwOHA4cDhwOHA4cDhwOHA4cAAAAAAAAAAAAAAHAAAAADg4AAA4ODg4ODg4ODg4ODgAAAAAAAcAAAAAODgAADg4ODg4ODg4ODg4ODg4cPDgDQAAAAAAAAAAOAA4ADgAOAA48DngOcA7gD8APwA/gDvAOcA44DjgOHAAAAAAAAAAAAAABwAAAAA4ODg4ODg4ODg4ODg4ODg4AAAAAAAUAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAc8eAN++APfvAOPHAOPHAOOHAOOHAOOHAOOHAOOHAOOHAOOHAAAAAAAAAAAAAAAAAAAAADgAAAAAAAAAAAAAAAAAAAABzwDfgPPA4cDhwOHA4cDhwOHA4cDhwOHAAAAAAAAAAAAAADgAAAAAAAAAAAAAAAAAAAAAPgB/gOPB4cHBwcHhweHBweHA48B/gD4AAAAAAAAAAAAAADgAAAAAAAAAAAAAAAAAAAABzwD/gPPA4cDhwOHg4eDhwOHA88D/gO8A4ADgAOAA4ADgADgAAAAAAAAAAAAAAAAAAAAAecD/wOPBw8HBwcHBwcHBwcPA48D/wHnAAcABwAHAAcABwCQAAAAAAAAAAAAAAAAAAAABzADcAPwA4ADgAOAA4ADgAOAA4ADgAOAAAAAAAAAAAAAAADQAAAAAAAAAAAAAAAAAAAAAfgD/AcOBwwHwAP4AP4AHgcOBw4D/gH4AAAAAAAAAAAAAACAAAAAAAGDg4/v44ODg4ODg4OD4eAAAAAAAOAAAAAAAAAAAAAAAAAAAAAHBwcHBwcHBwcHBwcHBwcHB48D3wP3AecAAAAAAAAAAAAAANAAAAAAAAAAAAAAAAAAAAAOBwcHBw4HDgOOA5wDnAHYAfgB+ADwAPAAAAAAAAAAAAAAASAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA4cOA4eOAY+OAY2MAc2cAc3cANzcANjYAPj4APj4AHhwAHBwAAAAAAAAAAAAAAAAAAAAADQAAAAAAAAAAAAAAAAAAAABw4HjgOcAfgB+ADwAPAB+AHcA5wHDg8PAAAAAAAAAAAAAADQAAAAAAAAAAAAAAAAAAAADwcHBwcOAw4DjAOcAZwB2AH4APgA8ABwAHAA4AHgB8AHgACwAAAAAAAAAAAAAAAAAAAAB/wH/AA4AHgAcADgAeABwAOAB4AH/Af8AAAAAAAAAAAAAACQAAAAAAAAAADwAfABwAHAAcABwAHAAcADgA8ADwADgAHAAcABwAHAAcABwAHAAfAA8ABwAAAAAwMDAwMDAwMDAwMDAwMDAwMDAwMDAJAAAAAAAAAADwAPgAPAAcABwAHAAcABwAHgAPAA8AHgAcABwAHAAcABwAHAA8APgA8AANAAAAAAAAAAAAAAAAAAAAAAAAAAA8AH8wR/AB4AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAIAAAAAAAAAAAAAAA4ODgAAAAAAAAAAAAAABYAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAD///z///wAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAHAAAAAAA4ODgQEDAAAAAAAAAAAAAAAAAAAA0AAAAAAAAAAAAAD4Af4DzgOHA4AP8AfgB4AP8AfwA4ADhwPOAf4AeAAAAAAAAAAAAAAA=="

# Each entry: (name, characters, pixel height, blob, decoded byte size).
_FONT_TABLE = [
    ("sans10", CHARS, 13, F_SANS10, 1464),
    ("sans12", CHARS, 14, F_SANS12, 1709),
    ("sansb10", CHARS, 13, F_SANSB10, 1464),
    ("sansb15", CHARS, 18, F_SANSB15, 3123),
    ("sansb22", CHARS, 25, F_SANSB22, 4699),
]


def _load_fonts():
    """Turn the blobs above into {name: (height, {char: (width, rows)})}.

    Each glyph's rows are stored as a tuple of ints, one bitmask per row,
    so painting a glyph is a shift-and-test instead of a slice-and-mask.
    """
    fonts = {}
    for name, chars, height, blob, want in _FONT_TABLE:
        raw = base64.b64decode(blob)
        if len(raw) != want:
            raise ValueError("font %s decoded to %d bytes, expected %d"
                             % (name, len(raw), want))
        glyphs = {}
        pos = 0
        for ch in chars:
            w = raw[pos]
            pos += 1
            step = (w + 7) // 8
            rows = []
            for r in range(height):
                # Bitmap bytes are MSB-first; the glyph occupies the top w
                # bits of each step-byte row, so shift the row right to put
                # pixel 0 on bit (w - 1) before storing the bitmask.
                rows.append(int.from_bytes(
                    raw[pos + r * step:pos + (r + 1) * step], "big")
                    >> (step * 8 - w))
            glyphs[ch] = (w, tuple(rows))
            pos += step * height
        if pos != len(raw):
            raise ValueError("font %s parse ended at %d of %d"
                             % (name, pos, len(raw)))
        fonts[name] = (height, glyphs)
    # The sans10 '+' glyph in the blob lost its vertical stroke (only the
    # horizontal bar survived the rasterisation), so it printed as '-'.
    # Redraw it: a vertical stroke at column 2 with the bar on row 6.
    # Bitmasks for a 6-wide glyph, pixel i on bit (5 - i).
    fonts["sans10"][1]["+"] = (6, (0, 0, 0, 8, 8, 8, 30, 8, 8, 8, 0, 0, 0))
    return fonts


# ------------------------------------------------------------------ sheet
W, H = 1024, 1024
M = 20            # outer margin
CW = W - 2 * M    # content width


class Sheet:
    """A 1024x1024 RGB page held as one bytearray per scanline."""

    def __init__(self, bg=PAPER):
        self.rows = [bytearray(bytes(bg) * W) for _ in range(H)]

    def dot(self, x, y, c):
        if 0 <= x < W and 0 <= y < H:
            self.rows[y][x * 3:x * 3 + 3] = bytes(c)

    def box(self, x, y, w, h, c):
        x0 = max(x, 0)
        y0 = max(y, 0)
        x1 = min(x + w, W)
        y1 = min(y + h, H)
        if x1 <= x0 or y1 <= y0:
            return
        paint = bytes(c) * (x1 - x0)
        for row in self.rows[y0:y1]:
            row[x0 * 3:x1 * 3] = paint

    def hbar(self, x, y, w, c, t=1):
        self.box(x, y, w, t, c)

    def vbar(self, x, y, h, c, t=1):
        self.box(x, y, t, h, c)

    def frame(self, x, y, w, h, c, t=1):
        self.box(x, y, w, t, c)
        self.box(x, y + h - t, w, t, c)
        self.box(x, y, t, h, c)
        self.box(x + w - t, y, t, h, c)

    def spot(self, cx, cy, r, c):
        rr = r * r
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                if dx * dx + dy * dy <= rr:
                    self.dot(cx + dx, cy + dy, c)

    def fill_poly(self, pts, c):
        if len(pts) < 3:
            return
        top = min(p[1] for p in pts)
        bot = max(p[1] for p in pts)
        edges = list(zip(pts, pts[1:] + pts[:1]))
        for y in range(top, bot + 1):
            xs = []
            for (x0, y0), (x1, y1) in edges:
                if min(y0, y1) <= y < max(y0, y1):
                    xs.append((x0 * (y1 - y) + x1 * (y - y0)) // (y1 - y0))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                self.box(xs[i], y, xs[i + 1] - xs[i], 1, c)


FONTS = _load_fonts()


def glyph_w(font, ch):
    return FONTS[font][1].get(ch, (0, ()))[0]


def text_w(font, s):
    return sum(glyph_w(font, ch) for ch in s)


def paint(sheet, font, x, y, s, c, align="l"):
    """Paint s in font at (x, y) baseline-top; align l/c/r by x."""
    height, glyphs = FONTS[font]
    if align == "c":
        x -= text_w(font, s) // 2
    elif align == "r":
        x -= text_w(font, s)
    for ch in s:
        w, rows = glyphs.get(ch, (0, ()))
        if not w:
            continue
        for r, bits in enumerate(rows):
            yy = y + r
            if 0 <= yy < H:
                row = sheet.rows[yy]
                for i in range(w):
                    if bits >> (w - 1 - i) & 1:
                        xx = x + i
                        if 0 <= xx < W:
                            row[xx * 3:xx * 3 + 3] = bytes(c)
        x += w
    return x


def _check_chars(text, where):
    for ch in text:
        if ch not in CHARS and ch != " ":
            raise ValueError("unsupported char %r in %s" % (ch, where))


def wrap(font, s, max_w):
    """Greedy word wrap; returns a list of lines fitting max_w."""
    out = []
    for para in s.split("\n"):
        line = ""
        for word in para.split(" "):
            cand = word if not line else line + " " + word
            if text_w(font, cand) <= max_w:
                line = cand
            else:
                if line:
                    out.append(line)
                line = word
        if line:
            out.append(line)
    return out


def fit(font, s, max_w, max_lines, line_h, where):
    """Wrap s to at most max_lines lines; raise if it cannot fit."""
    lines = wrap(font, s, max_w)
    if len(lines) > max_lines:
        raise ValueError("%s needs %d lines, max %d"
                         % (where, len(lines), max_lines))
    return lines


def trunc(font, s, max_w, where):
    """Shorten s with an ellipsis so it fits max_w (binary search)."""
    if text_w(font, s) <= max_w:
        return s
    lo, hi = 0, len(s)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if text_w(font, s[:mid] + "...") <= max_w:
            lo = mid
        else:
            hi = mid - 1
    if lo == 0:
        raise ValueError("%s cannot fit even one char in %d px" % (where, max_w))
    return s[:lo] + "..."


def _png_chunk(kind, payload):
    return (struct.pack(">I", len(payload)) + kind + payload
            + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF))


def write_png(sheet, path):
    raw = b"".join(b"\x00" + bytes(row) for row in sheet.rows)
    out = (b"\x89PNG\r\n\x1a\n"
           + _png_chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
           + _png_chunk(b"IDAT", zlib.compress(raw, 9))
           + _png_chunk(b"IEND", b""))
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, "wb") as f:
        f.write(out)
    return len(out)


# ------------------------------------------------------------------ data
# Every story below was verified from a reputable source (Reuters, BBC,
# AFP, UEFA, Investopedia, Fool, WHO, CNN) on 25 Nov 2026; the full
# source notes live in news-research-2026-11-25.md. Times are first
# reported in the 25 Nov news cycle unless a date is given.
# Layout: (kicker, headline, deck, source, motif).
LEADS = [
    ("US COURTS",
     "Huawei convicted on 10 of 12 counts",
     "A Brooklyn jury found the telecom giant guilty of trade-secret theft "
     "and bank fraud after a three-month trial. Racketeering and "
     "obstruction charges were thrown out. Huawei faces billions in fines "
     "and vows to appeal - the verdict has become a symbol of the "
     "US-China tech war.",
     "REUTERS - 20:41 UTC, 24 NOV", "scales"),
    ("SAUDI ARABIA",
     "Houthis hit Riyadh's tallest tower, 11 hurt",
     "Yemen's Houthi fighters struck the tallest tower in the Saudi "
     "capital, wounding at least 11 people - the second such attack in "
     "under a week. Saudi Civil Defence posted a picture of the "
     "landmark tower, home to the Saudi Public Investment Fund. The UK "
     "imposed fresh sanctions on the group the same day.",
     "REUTERS - 00:29, 25 NOV CYCLE", "tower"),
    ("UKRAINE WAR",
     "Zelensky: Ukraine hit a Russian ship in the Gulf of Finland",
     "The president confirmed a drone-boat strike on a Russian cargo "
     "ship on Saturday, now under tow to St Petersburg. Norway urged "
     "caution. Russia said Ukraine attacked its Black Sea oil plants "
     "and vowed a response.",
     "REUTERS - STRIKE SAT 22 NOV", "ship"),
]

# Layout: (headline, deck). Twelve stories, three columns by four rows.
MEDIUM = [
    ("CIA, ODNI hit by cyber breach",
     "The CIA and the Office of the Director of National Intelligence "
     "suffered a cyber breach, CNN and Reuters reported."),
    ("Israel strike kills Hamas security chief",
     "An Israeli strike killed Naim Abu Nakhla, Hamas's security chief, "
     "in Gaza City. Six more died in other strikes."),
    ("Nvidia rally fizzles in a day",
     "Nvidia fell 5.86% to $155.38 after Monday's 31.5% surge; the "
     "Nasdaq lost 1.48% while the Dow rose 0.85% to 50,018.70."),
    ("Turkish helicopter crash kills five",
     "A Turkish Air Force AS-532 helicopter crashed after taking off "
     "from Eskisehir for a training flight, killing five crew members."),
    ("Cartagena supermarket siege: 25 held",
     "Armed men seized a Cartagena supermarket, holding 25 people "
     "hostage, the president said. Five older women were freed."),
    ("WHO evacuates Ebola staff in DR Congo",
     "Health workers were evacuated from a hospital in Akwe, Ituri, "
     "the Ebola epicentre, after sheltering there for three days amid "
     "fighting."),
    ("Sarkozy and wife ordered to trial",
     "Nicolas Sarkozy and wife Carla Bruni were ordered to trial; a "
     "pre-trial hearing is set for 1 April 2027."),
    ("Putin: Ukraine hits oil plants, vows payback",
     "Putin said Ukraine has kept attacking Russian oil refineries "
     "despite requests from Trump to refrain, and pledged to retaliate."),
    ("South Korea unveils sweeping crypto bill",
     "Seoul's draft act caps major exchange shareholders at 20% and "
     "permits domestic token issuance and won stablecoins."),
    ("Champions League: Real roar back 5-1",
     "Real Madrid came from a goal down to crush PSV 5-1. Arsenal "
     "drew 1-1 with Dortmund; Man City drew 2-2 with Napoli."),
    ("Senegal regain AFCON title on appeal",
     "Senegal regained the Africa Cup of Nations title after a sports "
     "court appeal overturned the result."),
    ("Four tankers hit mines in Hormuz",
     "Three tankers caught fire after hitting mines in the Strait of "
     "Hormuz, Iran said; a fourth tanker then hit a mine."),
]

# Layout: (title, source). Twenty items in the left column.
LIST_A = [
    ("Houthis 60km from Aden, ready to attack", "France 24"),
    ("Houthis won't seize Aden, army says", "Reuters"),
    ("Russia calls ship strikes 'terrorism'", "BD Global Times"),
    ("Norway urges caution on Finland strike", "Reuters"),
    ("UK sanctions four Houthi leaders", "BBC"),
    ("IRGC hit container ship in Hormuz", "dailysummaryof"),
    ("Iran widens Hormuz crackdown to tugboats", "gCaptain"),
    ("US probes Iran cyberattacks on 50 ships", "WSJ"),
    ("Germans split on Ukraine aid: 53% oppose", "Reuters"),
    ("Lukashenko: fly with Zelensky to Moscow", "Reuters"),
    ("Latvia sees war 'tipping point' in 2026", "Reuters"),
    ("Sweden to vote on Kristersson as PM", "Reuters"),
    ("Eisenkot clinches first coalition deal", "Reuters"),
    ("Fort Hood shooter seeks execution stay", "Reuters"),
    ("Giuliani awarded Medal of Freedom", "Reuters"),
    ("Abrego Garcia to leave US voluntarily", "CBS"),
    ("Huckabee doubts Israel aid ends in 2026", "Reuters"),
    ("O'Hare radar fault delays flights", "FAA"),
    ("UK prisoner admits killing Huntley", "Reuters"),
    ("Turkish party aide quits in fund probe", "Reuters"),
]

# Layout: (title, source). Nineteen items in the right column.
LIST_B = [
    ("Car bomb wounds 20+ in Villavicencio", "BBC"),
    ("DR Congo army plane missing in east", "BBC"),
    ("Murmansk governor held for corruption", "BBC"),
    ("Landmine casualties surge in Syria", "BBC"),
    ("Gaza death toll reaches 74,746", "WAFA"),
    ("Oxfam: pollution risks in 99% of Gaza", "Oxfam"),
    ("266m face acute food insecurity", "WFP"),
    ("WHO chief: lift Cuba oil blockade", "Reuters"),
    ("Spain challenges Madrid unborn law", "Reuters"),
    ("Singapore probes Megaspeed after US ban", "Google News"),
    ("Sigonella base shut after drone sightings", "Google News"),
    ("Microsoft 'Code Red' after major outage", "Google News"),
    ("Tidal to ban AI tracks, delete 29m", "TechCrunch"),
    ("OpenAI GPT-6 designs proteins in lab", "TechCrunch"),
    ("Claude authors proof on VP vs VNP", "BeInCrypto"),
    ("BlackRock tokenized fund launches in HK", "Cointelegraph"),
    ("Ansem wallet hacked, $2.57m drained", "EventGraph"),
    ("CFTC approves prediction-market rules", "Cointelegraph"),
    ("Meta puts Muse in Instagram DMs", "TechCrunch"),
]

# Layout: (time, text). First-reported times in the 25 Nov cycle.
TIMELINE = [
    ("00:29", "Houthis strike Riyadh tower again, 11 hurt"),
    ("01:09", "UK sanctions Houthi leaders"),
    ("01:11", "Indonesia charges ex-police chief with treason"),
    ("01:40", "Singapore probes Megaspeed after US ban"),
    ("02:42", "Israeli strikes kill six in Gaza"),
    ("03:02", "SpaceX runs classified Space Force mission"),
]

# Layout: (event, date). Events in the image dated other than 25 Nov.
DATECHECK = [
    ("Huawei verdict", "Tue 24 Nov"),
    ("Turkish helicopter crash", "Tue 24 Nov"),
    ("Cartagena hostages", "Tue 24 Nov"),
    ("Houthis 60km from Aden", "Tue 24 Nov"),
    ("US markets close", "Tue 24 Nov"),
    ("Champions League MD5", "Tue 24 Nov eve"),
    ("Gaza strikes (Abu Nakhla + 6)", "Tue 24 Nov"),
    ("WHO DRC evacuation", "Tue 24 Nov"),
    ("Finland ship strike", "Sat 22 Nov"),
    ("Senegal AFCON appeal", "Tue 24 Nov"),
    ("Huang reinstated", "Mon 23 Nov"),
    ("Nvidia +31.5% rally", "Mon 23 Nov"),
]

# Layout: (label, latitude, longitude). Fifteen map points.
MAP_DOTS = [
    ("Brooklyn", 40.65, -73.95),
    ("Riyadh", 24.71, 46.68),
    ("Gulf of Finland", 59.85, 24.50),
    ("Gaza City", 31.50, 34.47),
    ("Langley", 38.95, -77.15),
    ("Eskisehir", 39.78, 30.52),
    ("Cartagena", 10.39, -75.48),
    ("Ituri", 1.70, 30.00),
    ("Hormuz", 26.60, 56.30),
    ("Aden", 12.80, 45.03),
    ("Paris", 48.86, 2.35),
    ("Seoul", 37.57, 126.98),
    ("Jakarta", -6.20, 106.85),
    ("Singapore", 1.35, 103.82),
    ("Madrid", 40.42, -3.70),
]

# Cartographic displacement, in pixels, for map dots that sit too close
# to read apart: Brooklyn and Langley are 5 px apart on this map, so
# their dots merge into one blob. Nudging them a few pixels each way
# keeps each dot readable; the shift is ~2 degrees, inside the map's
# own roughness.
MAP_NUDGE = {0: (3, -3), 4: (-3, 3)}

# Rough continent outlines, as (lon, lat) pairs per polygon.
CONTINENTS = [
    (-168, 66, -140, 66, -140, 70, -130, 70, -130, 60, -120, 60, -120, 48,
     -125, 40, -115, 30, -105, 25, -97, 26, -90, 20, -83, 9, -79, 9, -75, 12,
     -85, 15, -92, 15, -95, 18, -105, 22, -115, 30, -125, 40, -125, 48,
     -135, 58, -150, 60, -165, 60, -168, 66),
    (-75, 5, -60, 5, -55, -5, -40, -10, -35, -25, -45, -35, -58, -40, -65, -35,
     -70, -20, -75, -5, -80, 5, -75, 5),
    (-10, 37, -5, 35, 0, 35, 5, 38, 10, 38, 15, 45, 20, 42, 25, 40, 30, 36,
     35, 36, 40, 30, 35, 28, 30, 20, 25, 12, 20, 15, 12, 5, 10, 8, 5, 10, 0,
     15, -5, 10, -10, 12, -15, 8, -17, 12, -20, 15, -15, 25, -10, 30, -5, 35,
     -10, 37),
    (30, 70, 45, 70, 60, 70, 70, 70, 80, 75, 100, 75, 120, 70, 140, 70,
     160, 65, 180, 65, 170, 60, 160, 55, 140, 40, 130, 35, 125, 40, 120, 30,
     110, 20, 105, 10, 100, 5, 95, 15, 90, 22, 85, 20, 80, 10, 75, 10, 70, 25,
     60, 25, 55, 25, 50, 30, 45, 30, 40, 35, 35, 36, 30, 42, 25, 45, 20, 50,
     15, 55, 10, 60, 5, 65, 10, 70, 15, 70, 20, 70, 25, 70, 30, 70),
    (-50, -75, -50, -70, -55, -65, -60, -60, -65, -55, -70, -55, -70, -60,
     -75, -65, -80, -70, -85, -75, -80, -75, -60, -75, -50, -75),
    (110, -10, 120, -20, 130, -30, 140, -40, 150, -35, 145, -25, 140, -15,
     135, -10, 130, -5, 125, 0, 120, -5, 115, -10, 110, -10),
]


# ------------------------------------------------------------------ motifs
def _motif_scales(sheet, x, y):
    cx = x + 160
    sheet.vbar(cx - 1, y + 2, 38, INK, 2)
    sheet.hbar(cx - 52, y + 8, 104, INK, 2)
    sheet.hbar(cx - 15, y + 40, 30, INK, 2)
    for sgn in (-1, 1):
        px = cx + sgn * 52
        sheet.fill_poly([(px, y + 10), (px - 17, y + 27), (px + 17, y + 27)],
                        NAVY)
        sheet.spot(px, y + 8, 2, RED)


def _motif_tower(sheet, x, y):
    cx = x + 160
    sheet.box(cx - 15, y + 8, 30, 34, NAVY)
    sheet.box(cx - 19, y + 4, 38, 4, NAVY)
    sheet.vbar(cx - 1, y - 2, 6, INK, 2)
    sheet.box(cx + 1, y - 2, 10, 5, RED)
    for r in range(4):
        for c in range(3):
            sheet.dot(cx - 9 + c * 9, y + 13 + r * 7, GOLD)


def _motif_ship(sheet, x, y):
    cx = x + 160
    sheet.fill_poly([(cx - 62, y + 27), (cx + 62, y + 27),
                     (cx + 46, y + 40), (cx - 46, y + 40)], NAVY)
    sheet.box(cx - 26, y + 17, 52, 10, NAVY)
    sheet.vbar(cx - 1, y + 3, 16, INK, 2)
    sheet.box(cx + 1, y + 3, 13, 6, RED)
    sheet.hbar(cx - 72, y + 41, 144, GREY, 1)


MOTIFS = {"scales": _motif_scales, "tower": _motif_tower, "ship": _motif_ship}


# ------------------------------------------------------------------ layout
def _masthead(sheet):
    paint(sheet, "sansb22", M, 12, "THE WORLD IN ONE PAGE", INK)
    paint(sheet, "sansb15", W - M, 14, "WEDNESDAY 25 NOVEMBER 2026", INK,
          "r")
    paint(sheet, "sans10", W - M, 36, "54 STORIES - TIMES AS REPORTED",
          GREY, "r")
    paint(sheet, "sans12", M, 46,
          "Every story that mattered today, on one page.", GREY)
    sheet.hbar(M, 82, CW, INK, 3)
    sheet.hbar(M, 87, CW, GOLD, 2)


def _timeline(sheet):
    y0 = 94
    paint(sheet, "sansb10", M, y0, "THE DAY - WEDNESDAY 25 NOVEMBER 2026",
          RED)
    for i, (when, text) in enumerate(TIMELINE):
        x = M + i * 164
        if i:
            sheet.vbar(x - 2, y0 + 14, 38, GREY, 1)
        paint(sheet, "sansb10", x, y0 + 18, when, RED)
        lines = fit("sans10", text, 158, 2, 12, "timeline %s" % when)
        for j, line in enumerate(lines):
            paint(sheet, "sans10", x, y0 + 33 + j * 12, line, INK)
    sheet.hbar(M, 152, CW, GREY, 1)


def _leads(sheet):
    y0 = 156
    lead_w, gap = 321, 10
    for i, (kicker, head, deck, source, motif) in enumerate(LEADS):
        x = M + i * (lead_w + gap)
        if i:
            sheet.vbar(x - gap // 2 - 1, y0, 236, GREY, 1)
        paint(sheet, "sansb10", x, y0 + 8, kicker, RED)
        lines = fit("sansb15", head, lead_w, 3, 18, "lead %d headline" % i)
        for j, line in enumerate(lines):
            paint(sheet, "sansb15", x, y0 + 26 + j * 18, line, INK)
        MOTIFS[motif](sheet, x, y0 + 86)
        lines = fit("sans10", deck, lead_w, 5, 12, "lead %d deck" % i)
        for j, line in enumerate(lines):
            paint(sheet, "sans10", x, y0 + 136 + j * 12, line, INK)
        sheet.hbar(x, y0 + 204, lead_w, GREY, 1)
        paint(sheet, "sans10", x, y0 + 212, source, GREY)


def _medium(sheet):
    y0 = 398
    cell_w, cell_h, gap = 321, 59, 10
    for r in range(1, 4):
        sheet.hbar(M, y0 + r * cell_h, CW, GREY, 1)
    for c in range(1, 3):
        sheet.vbar(M + c * (cell_w + gap) - gap // 2 - 1, y0, 4 * cell_h,
                   GREY, 1)
    for i, (head, deck) in enumerate(MEDIUM):
        r, c = divmod(i, 3)
        x = M + c * (cell_w + gap)
        y = y0 + r * cell_h
        lines = fit("sansb10", head, cell_w, 2, 13, "medium %d headline" % i)
        for j, line in enumerate(lines):
            paint(sheet, "sansb10", x, y + 2 + j * 13, line, INK)
        lines = fit("sans10", deck, cell_w, 2, 12, "medium %d deck" % i)
        for j, line in enumerate(lines):
            paint(sheet, "sans10", x, y + 30 + j * 12, line, INK)


def _project(lon, lat, mx, my, mw, mh):
    return (mx + (lon + 180.0) * mw / 360.0,
            my + (75.0 - lat) * mh / 130.0)


def _bottom(sheet):
    y0 = 640
    paint(sheet, "sansb10", M, y0 + 6, "WHERE IT HAPPENED", RED)
    mx, my, mw, mh = M, y0 + 24, 480, 184
    sheet.box(mx, my, mw, mh, OCEAN)
    for poly in CONTINENTS:
        pts = []
        for k in range(0, len(poly), 2):
            px, py = _project(poly[k], poly[k + 1], mx, my, mw, mh)
            # Clamp to the frame so no continent spills onto the legend.
            pts.append((min(max(int(px), mx), mx + mw - 1),
                        min(max(int(py), my), my + mh - 1)))
        sheet.fill_poly(pts, LAND)
    sheet.frame(mx, my, mw, mh, INK, 1)
    for i, (label, lat, lon) in enumerate(MAP_DOTS):
        px, py = _project(lon, lat, mx, my, mw, mh)
        dx, dy = MAP_NUDGE.get(i, (0, 0))
        sheet.spot(int(px) + dx, int(py) + dy, 4, RED)
        paint(sheet, "sansb10", int(px) + dx + 6, int(py) + dy - 5,
              str(i + 1), RED)
    for i, (label, lat, lon) in enumerate(MAP_DOTS):
        r, c = divmod(i, 3)
        lx = M + c * 160
        ly = y0 + 214 + r * 17
        sheet.spot(lx + 4, ly + 5, 3, RED)
        paint(sheet, "sans10", lx + 11, ly, "%d. %s" % (i + 1, label), INK)
    for x, col_w, title, items in (
            (512, 244, "MORE FROM THE DAY", LIST_A),
            (764, 240, "AROUND THE WORLD", LIST_B)):
        paint(sheet, "sansb10", x, y0 + 6, title, RED)
        for i, (title, source) in enumerate(items):
            text = trunc("sans10", "- %s - %s" % (title, source), col_w,
                         "list %s" % title)
            paint(sheet, "sans10", x, y0 + 22 + i * 14, text, INK)


def _datecheck(sheet):
    y0 = 942
    paint(sheet, "sansb10", M, y0, "DATE CHECK - STORIES FROM OTHER DAYS",
          RED)
    for i, (event, when) in enumerate(DATECHECK):
        r, c = divmod(i, 4)
        x = M + c * 246
        y = y0 + 17 + r * 16
        text = trunc("sans10", "- %s: %s" % (event, when), 240,
                     "datecheck %s" % event)
        paint(sheet, "sans10", x, y, text, INK)


def _footer(sheet):
    paint(sheet, "sans10", M, 1010,
          "54 STORIES - SOURCES: REUTERS, BBC, AFP, UEFA, INVESTOPEDIA, "
          "CNN, WHO", GREY)
    paint(sheet, "sans10", W - M, 1010, "WEDNESDAY 25 NOVEMBER 2026", GREY,
          "r")


def build():
    sheet = Sheet()
    _masthead(sheet)
    _timeline(sheet)
    _leads(sheet)
    _medium(sheet)
    _bottom(sheet)
    _datecheck(sheet)
    _footer(sheet)
    return sheet


def validate():
    counts = {"leads": len(LEADS), "medium": len(MEDIUM),
              "list": len(LIST_A) + len(LIST_B),
              "timeline": len(TIMELINE), "datecheck": len(DATECHECK),
              "map_dots": len(MAP_DOTS)}
    expect = {"leads": 3, "medium": 12, "list": 39,
              "timeline": 6, "datecheck": 12, "map_dots": 15}
    for key, want in expect.items():
        if counts[key] != want:
            raise ValueError("%s: got %d, want %d" % (key, counts[key], want))
    texts = ["THE WORLD IN ONE PAGE", "WEDNESDAY 25 NOVEMBER 2026",
             "54 STORIES - TIMES AS REPORTED",
             "Every story that mattered today, on one page.",
             "THE DAY - WEDNESDAY 25 NOVEMBER 2026",
             "WHERE IT HAPPENED", "MORE FROM THE DAY", "AROUND THE WORLD",
             "DATE CHECK - STORIES FROM OTHER DAYS"]
    for kicker, head, deck, source, _motif in LEADS:
        texts += [kicker, head, deck, source]
    for head, deck in MEDIUM:
        texts += [head, deck]
    for title, source in LIST_A + LIST_B:
        texts += [title, source]
    for when, text in TIMELINE:
        texts += [when, text]
    for event, when in DATECHECK:
        texts += [event, when]
    for label, _lat, _lon in MAP_DOTS:
        texts.append(label)
    for t in texts:
        _check_chars(t, "text %r" % t[:40])
    return counts


def png_bytes(sheet):
    raw = b"".join(b"\x00" + bytes(row) for row in sheet.rows)
    return (b"\x89PNG\r\n\x1a\n"
            + _png_chunk(b"IHDR",
                         struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
            + _png_chunk(b"IDAT", zlib.compress(raw, 9))
            + _png_chunk(b"IEND", b""))


def main(argv=None):
    ap = argparse.ArgumentParser(description="Render the 25 Nov 2026 news "
                                             "image.")
    ap.add_argument("--output", default=None,
                    help="PNG path (default /output/entry.png)")
    ap.add_argument("--check", action="store_true",
                    help="validate and report, do not write a file")
    args = ap.parse_args(argv)
    counts = validate()
    sheet = build()
    data = png_bytes(sheet)
    if args.check:
        print("stories: %d leads + %d medium + %d list = %d"
              % (counts["leads"], counts["medium"], counts["list"],
                 counts["leads"] + counts["medium"] + counts["list"]))
        print("timeline: %d slots, datecheck: %d rows, map: %d dots"
              % (counts["timeline"], counts["datecheck"], counts["map_dots"]))
        print("size: %dx%d, PNG %d bytes (limit 1048576)"
              % (W, H, len(data)))
        if len(data) > 1048576:
            raise SystemExit("PNG over the 1 MiB limit")
        print("check OK")
        return 0
    out = args.output or os.path.join(
        os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"), "entry.png")
    d = os.path.dirname(out)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(out, "wb") as f:
        f.write(data)
    print("wrote %s (%d bytes)" % (out, len(data)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
