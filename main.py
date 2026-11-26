#!/usr/bin/env python3
"""World news of Thursday 26 November 2026, summed up in one image.

Draws a 1024x1024 newspaper-style front page with a pure-Python PNG
encoder (stdlib only, no network, deterministic output) and writes it to
/output/entry.png (or $MAKEFUN_OUTPUT_DIR/entry.png).

Stories shown (all first reported on 26 November 2026):
  1. Houthis claim a strike on Saudi Arabia's Ras Tanura refinery;
     Brent crude tops $94.
  2. Ukraine strikes two Russian oil refineries; Putin vows a response.
  3. An Israeli strike in Gaza City kills a senior Hamas security
     official as the ceasefire strains.
  4. Pakistan's first astronaut joins China's Tiangong space station.
  5. The US prepares new tariffs on China, the EU, Japan and others.
  6. Colombia marks ten years since its historic peace accord.
"""

import os
import struct
import zlib

W = 1024
H = 1024

# ---------------------------------------------------------------- palette
NAVY = (13, 24, 46)        # page background
PANEL = (22, 38, 63)       # panel background
PANEL_LINE = (52, 74, 105)  # panel border
WHITE = (245, 246, 248)
GOLD = (232, 184, 74)
LIGHT = (186, 198, 214)    # sub-line text
DARK = (10, 18, 34)

REGION_COLORS = {
    "MIDDLE EAST": (198, 122, 22),
    "EUROPE": (58, 123, 213),
    "GAZA": (192, 57, 43),
    "SPACE": (125, 91, 166),
    "TRADE": (46, 158, 107),
    "LATIN AMERICA": (31, 138, 138),
}

# ------------------------------------------------------- 5x7 bitmap font
# Each glyph: 7 rows of 5 bits, '1' = pixel on.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    "*": ("00000", "00100", "10101", "01110", "10101", "00100", "00000"),
}


def text_width(s, scale):
    return len(s) * 6 * scale - scale


def draw_text(px, x, y, s, scale, color, center=False):
    """Draw uppercase text; s is uppercased, unknown chars become spaces."""
    s = s.upper()
    if center:
        x -= text_width(s, scale) // 2
    cx = x
    for ch in s:
        glyph = FONT.get(ch, FONT[" "])
        for row in range(7):
            bits = glyph[row]
            for col in range(5):
                if bits[col] == "1":
                    fill_rect(px, cx + col * scale, y + row * scale,
                              scale, scale, color)
        cx += 6 * scale


# ------------------------------------------------------------- canvas ops
def new_canvas():
    return bytearray(NAVY[0] for _ in range(W * H * 3)) \
        if False else bytearray([NAVY[0], NAVY[1], NAVY[2]] * (W * H))


def set_px(px, x, y, color):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        px[i], px[i + 1], px[i + 2] = color


def fill_rect(px, x, y, w, h, color):
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W, x + w), min(H, y + h)
    for yy in range(y0, y1):
        base = (yy * W + x0) * 3
        for xx in range(x0, x1):
            i = base + (xx - x0) * 3
            px[i], px[i + 1], px[i + 2] = color


def rect_outline(px, x, y, w, h, color, t=2):
    fill_rect(px, x, y, w, t, color)
    fill_rect(px, x, y + h - t, w, t, color)
    fill_rect(px, x, y, t, h, color)
    fill_rect(px, x + w - t, y, t, h, color)


def draw_line(px, x0, y0, x1, y1, color, t=1):
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        for a in range(t):
            for b in range(t):
                set_px(px, x0 + a, y0 + b, color)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def fill_circle(px, cx, cy, r, color):
    for yy in range(cy - r, cy + r + 1):
        dx = int((r * r - (yy - cy) * (yy - cy)) ** 0.5) if abs(yy - cy) <= r else 0
        fill_rect(px, cx - dx, yy, 2 * dx + 1, 1, color)


def fill_triangle(px, p0, p1, p2, color):
    xs = [p0[0], p1[0], p2[0]]
    ys = [p0[1], p1[1], p2[1]]
    y0, y1 = min(ys), max(ys)
    for yy in range(y0, y1 + 1):
        xs_at = []
        for a in range(3):
            b = (a + 1) % 3
            xa, ya = xs[a], ys[a]
            xb, yb = xs[b], ys[b]
            if ya == yb:
                continue
            if min(ya, yb) <= yy <= max(ya, yb):
                xs_at.append(xa + (xb - xa) * (yy - ya) / (yb - ya))
        if len(xs_at) >= 2:
            fill_rect(px, int(min(xs_at)), yy,
                      int(max(xs_at)) - int(min(xs_at)) + 1, 1, color)


def fill_star(px, cx, cy, r_out, r_in, points, color):
    import math
    verts = []
    for i in range(points * 2):
        r = r_out if i % 2 == 0 else r_in
        ang = math.pi * i / points - math.pi / 2
        verts.append((cx + int(r * math.cos(ang)),
                      cy + int(r * math.sin(ang))))
    for i in range(1, len(verts) - 1):
        fill_triangle(px, verts[0], verts[i], verts[i + 1], color)


def draw_flame(px, cx, cy, s):
    """Simple flame: orange outer teardrop, yellow inner."""
    orange = (232, 122, 26)
    yellow = (250, 204, 60)
    fill_triangle(px, (cx - 12 * s, cy + 10 * s), (cx + 12 * s, cy + 10 * s),
                  (cx, cy - 18 * s), orange)
    fill_circle(px, cx, cy + 4 * s, 10 * s, orange)
    fill_triangle(px, (cx - 6 * s, cy + 8 * s), (cx + 6 * s, cy + 8 * s),
                  (cx, cy - 8 * s), yellow)
    fill_circle(px, cx, cy + 4 * s, 5 * s, yellow)


# -------------------------------------------------------------- pictograms
def pic_oil(px, cx, cy):
    """Oil derrick with flame."""
    steel = (150, 168, 190)
    draw_line(px, cx - 34, cy + 44, cx - 10, cy - 40, steel, 4)
    draw_line(px, cx + 34, cy + 44, cx + 10, cy - 40, steel, 4)
    draw_line(px, cx - 26, cy + 12, cx + 26, cy + 12, steel, 3)
    draw_line(px, cx - 18, cy - 14, cx + 18, cy - 14, steel, 3)
    draw_line(px, cx - 34, cy + 44, cx + 34, cy + 44, steel, 4)
    draw_flame(px, cx, cy - 52, 1)


def pic_refinery(px, cx, cy):
    """Refinery towers with a blast star."""
    grey = (150, 168, 190)
    fill_rect(px, cx - 52, cy - 6, 26, 50, grey)
    fill_rect(px, cx - 18, cy - 26, 26, 70, grey)
    fill_rect(px, cx + 16, cy + 6, 26, 38, grey)
    fill_rect(px, cx - 52, cy - 14, 26, 8, (110, 126, 148))
    fill_rect(px, cx - 18, cy - 34, 26, 8, (110, 126, 148))
    draw_line(px, cx - 52, cy + 44, cx + 42, cy + 44, grey, 4)
    fill_star(px, cx + 46, cy - 30, 22, 9, 8, (250, 204, 60))
    fill_star(px, cx + 46, cy - 30, 12, 5, 8, (232, 122, 26))


def pic_city(px, cx, cy):
    """City skyline, one building cracked, blast star above."""
    b1 = (120, 138, 162)
    b2 = (150, 168, 190)
    fill_rect(px, cx - 56, cy + 4, 30, 40, b1)
    fill_rect(px, cx - 20, cy - 22, 30, 66, b2)
    fill_rect(px, cx + 18, cy - 6, 30, 50, b1)
    # broken top on the middle tower: jagged crack, leaning slab
    fill_triangle(px, (cx - 20, cy - 22), (cx - 5, cy - 38), (cx + 10, cy - 22),
                  b2)
    draw_line(px, cx - 20, cy - 22, cx - 5, cy - 38, (60, 70, 92), 3)
    draw_line(px, cx - 5, cy - 38, cx + 10, cy - 22, (60, 70, 92), 3)
    fill_rect(px, cx + 2, cy - 14, 4, 20, (60, 70, 92))
    fill_star(px, cx + 52, cy - 34, 20, 8, 8, (250, 204, 60))
    fill_star(px, cx + 52, cy - 34, 10, 4, 8, (232, 122, 26))


def pic_space(px, cx, cy):
    """Rocket rising to a space station, stars around."""
    white = (235, 238, 244)
    # stars
    for sx, sy in [(-58, -42), (-44, 34), (52, -38), (60, 28), (8, -48)]:
        fill_star(px, cx + sx, cy + sy, 6, 2, 4, GOLD)
    # station ring
    fill_circle(px, cx + 46, cy - 34, 16, (90, 110, 140))
    fill_circle(px, cx + 46, cy - 34, 11, NAVY)
    fill_rect(px, cx + 30, cy - 38, 32, 8, (120, 138, 162))
    # rocket body
    fill_rect(px, cx - 52, cy - 10, 24, 48, white)
    fill_triangle(px, (cx - 52, cy - 10), (cx - 28, cy - 10),
                  (cx - 40, cy - 34), (232, 122, 26))
    fill_triangle(px, (cx - 52, cy + 38), (cx - 60, cy + 52),
                  (cx - 52, cy + 52), (192, 57, 43))
    fill_triangle(px, (cx - 28, cy + 38), (cx - 20, cy + 52),
                  (cx - 28, cy + 52), (192, 57, 43))
    fill_circle(px, cx - 40, cy + 6, 6, (58, 123, 213))
    draw_flame(px, cx - 40, cy + 62, 1)


def pic_trade(px, cx, cy):
    """Rising bar chart with an arrow, and a container ship."""
    green = (46, 158, 107)
    # bars end at cy-8, arrow rising over them
    bars = [14, 24, 36, 48]
    for i, bh in enumerate(bars):
        fill_rect(px, cx - 62 + i * 20, cy - 8 - bh, 14, bh, green)
    draw_line(px, cx - 66, cy - 2, cx + 18, cy - 54, GOLD, 4)
    fill_triangle(px, (cx + 18, cy - 54), (cx + 4, cy - 54),
                  (cx + 18, cy - 40), GOLD)
    # container ship below the chart: stacked containers on a hull
    fill_rect(px, cx - 43, cy + 0, 16, 12, (125, 91, 166))
    fill_rect(px, cx - 25, cy + 0, 16, 12, (46, 158, 107))
    fill_rect(px, cx - 52, cy + 12, 16, 12, (192, 57, 43))
    fill_rect(px, cx - 34, cy + 12, 16, 12, (58, 123, 213))
    fill_rect(px, cx - 16, cy + 12, 16, 12, (232, 184, 74))
    fill_rect(px, cx - 58, cy + 24, 116, 12, (150, 168, 190))
    fill_triangle(px, (cx + 58, cy + 24), (cx + 58, cy + 36),
                  (cx + 74, cy + 36), (150, 168, 190))
    draw_line(px, cx - 64, cy + 44, cx + 74, cy + 44, (58, 123, 213), 3)


def pic_peace(px, cx, cy):
    """Dove over an olive branch."""
    white = (235, 238, 244)
    # branch
    draw_line(px, cx - 58, cy + 40, cx + 58, cy + 40, (46, 158, 107), 4)
    for lx in (-44, -16, 12, 40):
        fill_circle(px, cx + lx, cy + 32, 7, (46, 158, 107))
    # dove body
    fill_circle(px, cx - 6, cy - 6, 26, white)
    fill_circle(px, cx - 26, cy - 10, 10, white)
    fill_circle(px, cx + 26, cy - 22, 12, white)
    fill_triangle(px, (cx + 36, cy - 24), (cx + 50, cy - 20),
                  (cx + 36, cy - 16), (232, 184, 74))
    fill_circle(px, cx + 30, cy - 26, 3, DARK)
    # wing
    fill_circle(px, cx - 2, cy - 26, 16, (210, 216, 226))
    fill_circle(px, cx - 2, cy - 30, 12, white)


PICTOGRAMS = {
    "OIL": pic_oil,
    "REFINERY": pic_refinery,
    "CITY": pic_city,
    "SPACE": pic_space,
    "TRADE": pic_trade,
    "PEACE": pic_peace,
}

# ---------------------------------------------------------------- stories
STORIES = [
    {
        "region": "MIDDLE EAST",
        "pic": "OIL",
        "headline": ["OIL UNDER FIRE"],
        "sub": ["HOUTHIS CLAIM STRIKE", "ON SAUDI REFINERY", "BRENT TOPS $94"],
    },
    {
        "region": "EUROPE",
        "pic": "REFINERY",
        "headline": ["UKRAINE HITS", "REFINERIES"],
        "sub": ["KYIV STRIKES TWO", "RUSSIAN OIL PLANTS", "PUTIN VOWS RESPONSE"],
    },
    {
        "region": "GAZA",
        "pic": "CITY",
        "headline": ["GAZA STRIKE", "KILLS HAMAS CHIEF"],
        "sub": ["SENIOR SECURITY", "OFFICIAL DEAD AS", "CEASEFIRE STRAINS"],
    },
    {
        "region": "SPACE",
        "pic": "SPACE",
        "headline": ["FIRST PAKISTANI", "IN ORBIT"],
        "sub": ["ASTRONAUT JOINS", "CHINA'S TIANGONG", "SPACE STATION"],
    },
    {
        "region": "TRADE",
        "pic": "TRADE",
        "headline": ["US READIES", "NEW TARIFFS"],
        "sub": ["CHINA, EU, JAPAN", "AND 14 MORE IN", "TRADE PROBE"],
    },
    {
        "region": "LATIN AMERICA",
        "pic": "PEACE",
        "headline": ["COLOMBIA MARKS", "10 YEARS OF PEACE"],
        "sub": ["DECADE SINCE", "HISTORIC ACCORD", "UN PRAISES PROGRESS"],
    },
]


def draw_panel(px, x, y, w, h, story):
    fill_rect(px, x, y, w, h, PANEL)
    rect_outline(px, x, y, w, h, PANEL_LINE, 2)
    color = REGION_COLORS[story["region"]]
    # region tag strip
    fill_rect(px, x + 2, y + 2, w - 4, 34, color)
    draw_text(px, x + w // 2, y + 10, story["region"], 2, WHITE, center=True)
    # pictogram
    PICTOGRAMS[story["pic"]](px, x + w // 2, y + 108)
    # headline
    hy = y + 178
    for i, line in enumerate(story["headline"]):
        draw_text(px, x + w // 2, hy + i * 26, line, 3, WHITE, center=True)
    # sub-lines
    sy = hy + len(story["headline"]) * 26 + 10
    for i, line in enumerate(story["sub"]):
        draw_text(px, x + w // 2, sy + i * 18, line, 2, LIGHT, center=True)


def draw_page(px):
    # header
    draw_text(px, W // 2, 26, "THE WORLD IN ONE DAY", 2, GOLD, center=True)
    draw_text(px, W // 2, 52, "26 NOVEMBER 2026", 6, WHITE, center=True)
    draw_text(px, W // 2, 108, "THURSDAY - SIX STORIES FROM AROUND THE GLOBE",
              2, LIGHT, center=True)
    fill_rect(px, 32, 140, W - 64, 3, GOLD)

    # panels: 3 columns x 2 rows
    pw, ph = 322, 320
    xs = [16, 16 + pw + 11, 16 + 2 * (pw + 11)]
    ys = [164, 164 + ph + 16]
    for i, story in enumerate(STORIES):
        draw_panel(px, xs[i % 3], ys[i // 3], pw, ph, story)

    # footer
    fy = 836
    fill_rect(px, 32, fy, W - 64, 2, PANEL_LINE)
    draw_text(px, W // 2, fy + 18, "ONE DAY IN THE WORLD", 4, GOLD,
              center=True)
    draw_text(px, W // 2, fy + 62,
              "DRAWN FROM THE DAY'S REPORTED NEWS - 26 NOVEMBER 2026",
              2, LIGHT, center=True)
    draw_text(px, W // 2, fy + 88, "OIL - WAR - SPACE - TRADE - PEACE",
              2, LIGHT, center=True)


# ------------------------------------------------------------ PNG encoder
def chunk(ctype, data):
    out = struct.pack(">I", len(data)) + ctype + data
    out += struct.pack(">I", zlib.crc32(ctype + data) & 0xFFFFFFFF)
    return out


def encode_png(px):
    raw = bytearray()
    for yy in range(H):
        raw.append(0)  # filter: none
        raw += px[yy * W * 3:(yy + 1) * W * 3]
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    return png


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    px = new_canvas()
    draw_page(px)
    data = encode_png(px)
    with open(os.path.join(out_dir, "entry.png"), "wb") as f:
        f.write(data)


if __name__ == "__main__":
    main()
