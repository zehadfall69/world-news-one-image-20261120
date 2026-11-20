#!/usr/bin/env python3
"""Sum up 20 November 2026's world news in one image.

A pure-standard-library Python program: it draws a newspaper-style front
page (masthead, lead story, four story panels and a news ticker) onto a
1024x1024 canvas and writes it as a PNG to $MAKEFUN_OUTPUT_DIR/entry.png
(/output/entry.png in the grader). No network, no randomness, no clock:
two runs write exactly the same bytes.
"""

import os
import struct
import zlib

W = 1024
H = 1024

# ---------------------------------------------------------------- canvas --

PAPER = (246, 241, 231)
INK = (20, 22, 28)
NAVY = (23, 42, 74)
RED = (179, 32, 44)
GOLD = (224, 165, 38)
WHITE = (255, 255, 255)
GRAY = (96, 98, 104)
LIGHT = (232, 224, 205)
GREEN = (28, 124, 72)
BLUE = (52, 96, 164)
SKY = (168, 200, 226)

canvas = bytearray(W * H * 3)


def px(x, y, color):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        canvas[i] = color[0]
        canvas[i + 1] = color[1]
        canvas[i + 2] = color[2]


def rect(x, y, w, h, color):
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            px(xx, yy, color)


def frame(x, y, w, h, color, t=2):
    rect(x, y, w, t, color)
    rect(x, y + h - t, w, t, color)
    rect(x, y, t, h, color)
    rect(x + w - t, y, t, h, color)


def line(x0, y0, x1, y1, color, t=2):
    dx = x1 - x0
    dy = y1 - y0
    steps = max(abs(dx), abs(dy), 1)
    r = t // 2
    for s in range(steps + 1):
        x = x0 + dx * s // steps
        y = y0 + dy * s // steps
        rect(x - r, y - r, t, t, color)


def circle(cx, cy, rad, color, fill=False, t=2):
    if fill:
        for yy in range(cy - rad, cy + rad + 1):
            for xx in range(cx - rad, cx + rad + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= rad * rad:
                    px(xx, yy, color)
    else:
        for yy in range(cy - rad - t, cy + rad + t + 1):
            for xx in range(cx - rad - t, cx + rad + t + 1):
                d = (xx - cx) ** 2 + (yy - cy) ** 2
                if (rad - t) ** 2 <= d <= (rad + t) ** 2:
                    px(xx, yy, color)


def star(cx, cy, r_out, r_in, color):
    import math

    pts = []
    for i in range(10):
        r = r_out if i % 2 == 0 else r_in
        a = -math.pi / 2 + i * math.pi / 5
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    minx = int(min(p[0] for p in pts))
    maxx = int(max(p[0] for p in pts))
    miny = int(min(p[1] for p in pts))
    maxy = int(max(p[1] for p in pts))
    for yy in range(miny, maxy + 1):
        for xx in range(minx, maxx + 1):
            inside = False
            j = len(pts) - 1
            for i in range(len(pts)):
                xi, yi = pts[i]
                xj, yj = pts[j]
                if (yi > yy) != (yj > yy) and xx < (xj - xi) * (yy - yi) / (yj - yi) + xi:
                    inside = not inside
                j = i
            if inside:
                px(xx, yy, color)


# ------------------------------------------------------------------ font --
# A 5x7 bitmap font, drawn by hand for this poster. Each glyph is seven
# rows of five bits, written as strings so the letterforms stay readable.

FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11100", "10010", "10001", "10001", "10001", "10010", "11100"),
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
    "W": ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    "X": ("10001", "01010", "00100", "00100", "00100", "01010", "10001"),
    "Y": ("10001", "01010", "00100", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "+": ("00000", "00100", "00100", "01110", "00100", "00100", "00000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "•": ("00000", "00000", "01110", "01110", "01110", "00000", "00000"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
}


def text_width(text, scale):
    return len(text) * 6 * scale - scale


def draw_text(x, y, text, scale, color):
    for ch in text.upper():
        glyph = FONT.get(ch, FONT[" "])
        for row in range(7):
            bits = glyph[row]
            for col in range(5):
                if bits[col] == "1":
                    rect(x + col * scale, y + row * scale, scale, scale, color)
        x += 6 * scale
    return x


def draw_centered(cx, y, text, scale, color):
    draw_text(cx - text_width(text, scale) // 2, y, text, scale, color)


def wrap(text, scale, max_width):
    words = text.split()
    lines = []
    cur = ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if text_width(trial, scale) <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_wrapped(x, y, text, scale, color, max_width, line_pitch=None, center_in=None):
    if line_pitch is None:
        line_pitch = 9 * scale
    for ln in wrap(text, scale, max_width):
        if center_in is not None:
            draw_centered(center_in, y, ln, scale, color)
        else:
            draw_text(x, y, ln, scale, color)
        y += line_pitch
    return y


# ----------------------------------------------------------------- icons --

def flag_usa(x, y, w, h):
    rect(x, y, w, h, WHITE)
    stripe = h // 7
    for i in range(0, 7, 2):
        rect(x, y + i * stripe, w, stripe, RED)
    rect(x, y, w * 2 // 5, stripe * 4, NAVY)
    for r in range(4):
        for c in range(5):
            px(x + 8 + c * 13, y + 6 + r * 11, WHITE)
            rect(x + 7 + c * 13, y + 5 + r * 11, 3, 3, WHITE)
    frame(x, y, w, h, INK, 2)


def flag_china(x, y, w, h):
    rect(x, y, w, h, RED)
    star(x + 26, y + 24, 16, 7, GOLD)
    for dx, dy in ((46, 8), (52, 22), (52, 36), (44, 48)):
        star(x + dx, y + dy, 6, 3, GOLD)
    frame(x, y, w, h, INK, 2)


def flag_russia(x, y, w, h):
    third = h // 3
    rect(x, y, w, third, WHITE)
    rect(x, y + third, w, third, BLUE)
    rect(x, y + 2 * third, w, h - 2 * third, RED)
    frame(x, y, w, h, INK, 2)


def icon_scales(cx, cy):
    line(cx, cy - 42, cx, cy + 34, INK, 4)
    line(cx - 44, cy - 34, cx + 44, cy - 34, INK, 4)
    circle(cx, cy - 44, 6, GOLD, fill=True)
    for side in (-1, 1):
        tip = cx + side * 44
        line(tip, cy - 34, tip - 14, cy + 2, INK, 2)
        line(tip, cy - 34, tip + 14, cy + 2, INK, 2)
        line(tip - 18, cy + 2, tip + 18, cy + 2, INK, 3)
        line(tip - 18, cy + 2, tip, cy + 12, INK, 2)
        line(tip + 18, cy + 2, tip, cy + 12, INK, 2)
    rect(cx - 26, cy + 36, 52, 6, INK)


def icon_chart(cx, cy):
    line(cx - 44, cy - 40, cx - 44, cy + 38, INK, 3)
    line(cx - 44, cy + 38, cx + 46, cy + 38, INK, 3)
    bars = ((-34, 14), (-12, 2), (10, -12), (32, -26))
    for bx, top in bars:
        rect(cx + bx, cy + top, 15, 38 - top, GREEN)
    line(cx - 36, cy + 2, cx - 4, cy - 12, RED, 4)
    line(cx - 4, cy - 12, cx + 38, cy - 32, RED, 4)
    line(cx + 24, cy - 32, cx + 40, cy - 33, RED, 4)
    line(cx + 40, cy - 33, cx + 39, cy - 18, RED, 4)


def icon_bridge(cx, cy):
    rect(cx - 52, cy - 34, 8, 62, INK)
    rect(cx + 44, cy - 34, 8, 62, INK)
    line(cx - 56, cy + 6, cx + 56, cy + 6, INK, 5)
    for t in range(-56, 57, 8):
        top = cy - 34 + int(26 * ((t / 56) ** 2))
        line(cx + t, top, cx + t, cy + 6, NAVY, 2)
    line(cx - 56, cy - 34, cx, cy - 8, NAVY, 3)
    line(cx, cy - 8, cx + 56, cy - 34, NAVY, 3)
    for wx in range(cx - 54, cx + 46, 18):
        line(wx, cy + 22, wx + 5, cy + 17, BLUE, 3)
        line(wx + 5, cy + 17, wx + 10, cy + 22, BLUE, 3)
    star(cx + 30, cy - 44, 11, 5, GOLD)


def icon_globe(cx, cy):
    circle(cx, cy, 40, NAVY, fill=False, t=3)
    for k in range(-2, 3):
        yy = cy + k * 16
        half = int((40 ** 2 - (k * 16) ** 2) ** 0.5)
        line(cx - half, yy, cx + half, yy, BLUE, 2)
    for xx in range(cx - 40, cx + 41, 4):
        dx = xx - cx
        half = int((40 ** 2 - dx * dx) ** 0.5)
        if abs(dx) in (0, 20, 36):
            line(xx, cy - half, xx, cy + half, BLUE, 2)
    circle(cx + 30, cy - 46, 12, GOLD, fill=True)
    line(cx + 30, cy - 30, cx + 30, cy - 22, RED, 3)


# ---------------------------------------------------------------- layout --

def panel(x, y, w, h, kicker, icon, headline, sub):
    rect(x, y, w, h, WHITE)
    frame(x, y, w, h, INK, 2)
    rect(x, y, w, 6, RED)
    icon(x + 58, y + h // 2 + 4)
    tx = x + 122
    draw_text(tx, y + 18, kicker, 2, RED)
    ly = y + 42
    for ln in headline:
        draw_text(tx, ly, ln, 3, INK)
        ly += 28
    draw_wrapped(tx, ly + 4, sub, 2, GRAY, w - 140)


def main():
    rect(0, 0, W, H, PAPER)
    frame(14, 14, W - 28, H - 28, INK, 3)

    # Masthead
    draw_centered(W // 2, 40, "FRIDAY · 20 NOVEMBER 2026", 3, RED)
    draw_centered(W // 2, 74, "THE WORLD IN ONE PICTURE", 6, INK)
    rect(48, 122, W - 96, 4, INK)
    rect(48, 132, W - 96, 2, INK)
    draw_centered(W // 2, 142, "THE DAY'S WORLD NEWS, SUMMED UP IN A SINGLE IMAGE", 2, GRAY)

    # Lead story: the Shenzhen three-way summit
    lx, ly, lw, lh = 48, 172, W - 96, 262
    rect(lx, ly, lw, lh, WHITE)
    frame(lx, ly, lw, lh, INK, 2)
    rect(lx, ly, lw, 6, NAVY)
    draw_centered(W // 2, ly + 20, "DIPLOMACY · SHENZHEN", 2, RED)
    fw, fh, fy = 176, 104, ly + 44
    gap = 44
    total = fw * 3 + gap * 2
    fx = (W - total) // 2
    flag_usa(fx, fy, fw, fh)
    flag_china(fx + fw + gap, fy, fw, fh)
    flag_russia(fx + 2 * (fw + gap), fy, fw, fh)
    for i, name in enumerate(("USA", "CHINA", "RUSSIA")):
        draw_centered(fx + i * (fw + gap) + fw // 2, fy + fh + 8, name, 2, GRAY)
    draw_centered(W // 2, ly + 180, "TRUMP, XI AND PUTIN MEET", 5, INK)
    draw_wrapped(
        0,
        ly + 222,
        "THE FIRST THREE-WAY SUMMIT OF THE US, CHINA AND RUSSIA ISSUES A FOUR-POINT PEACE DECLARATION",
        2,
        GRAY,
        lw - 90,
        center_in=W // 2,
    )

    # Four story panels, two by two
    pw, ph, gx, gy = (W - 96 - 16) // 2, 180, 48, 450
    panel(gx, gy, pw, ph, "THE HAGUE · JUSTICE", icon_scales,
          ("UN COURT: MYANMAR", "COMMITTED GENOCIDE"),
          "THE ICJ FINDS THE 2017 CAMPAIGN AGAINST THE ROHINGYA WAS GENOCIDE - REFUGEES CHEER THE VERDICT")
    panel(gx + pw + 16, gy, pw, ph, "WALL STREET · AI", icon_chart,
          ("ANTHROPIC SOARS", "ON MARKET DEBUT"),
          "SHARES JUMP 17% IN A RECORD AI LISTING AS THE S&P 500 FALLS 2% FOR A FIFTH STRAIGHT DAY")
    panel(gx, gy + ph + 16, pw, ph, "UKRAINE · WAR", icon_bridge,
          ("UKRAINE STRIKES", "CRIMEA BRIDGE"),
          "A THIRD HIT IN FOUR DAYS - PUTIN RULES OUT ANY TRUCE AND VOWS A HARSHER RESPONSE")
    panel(gx + pw + 16, gy + ph + 16, pw, ph, "CLIMATE · COP31", icon_globe,
          ("CLIMATE DEAL DROPS", "FOSSIL FUELS"),
          "OUTCRY AS THE COP31 DRAFT ERASES THE PHASE-OUT, WITH TALKS AT CRUNCH TIME AND NO DEAL IN SIGHT")

    # News ticker
    ty = 838
    rect(48, ty, W - 96, 112, NAVY)
    draw_text(72, ty + 14, "ALSO TODAY", 2, GOLD)
    draw_wrapped(
        72,
        ty + 38,
        "US SENATE REJECTS A CURB ON TRUMP'S IRAN WAR POWERS, 51-48 • A HOUTHI MISSILE DAMAGES RIYADH'S TALLEST TOWER AS OIL EDGES UP • VOYAGER 1 PHONES HOME FROM ONE LIGHT-DAY AWAY",
        2,
        WHITE,
        W - 96 - 48,
    )

    # Footer
    draw_centered(W // 2, 968, "SUMMED UP FROM THE WIRE REPORTS OF 20 NOVEMBER 2026", 2, GRAY)
    draw_centered(W // 2, 990, "DRAWN ENTIRELY BY A PYTHON PROGRAM - NO PHOTOGRAPHS", 2, GRAY)

    # ------------------------------------------------------------- PNG out --
    raw = bytearray()
    for yy in range(H):
        raw.append(0)
        raw += canvas[yy * W * 3:(yy + 1) * W * 3]

    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        c += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        return c

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")

    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "entry.png"), "wb") as f:
        f.write(png)


if __name__ == "__main__":
    main()
