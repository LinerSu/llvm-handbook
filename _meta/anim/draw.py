"""PIL drawing primitives for storyboard rendering: shapes, arrows, text, badges.

Owns the visual style (palette, fonts, stroke widths) so storyboard authors
never pick raw colors — they use the named styles from `model.STYLES`.
"""

import math
from typing import Dict, List, Optional, Tuple

from PIL import ImageDraw, ImageFont

# ---- palette (flat colors only: quantizes cleanly to a GIF palette) ----

BG = (250, 250, 247)
HEADER_TEXT = (60, 60, 60)
CAPTION_BG = (240, 239, 233)
CAPTION_TEXT = (25, 25, 25)

# style -> (fill, outline, text, stroke_width)
NODE_STYLES = {
    "normal": ((255, 255, 255), (74, 74, 74), (26, 26, 26), 2),
    "active": ((255, 224, 138), (184, 134, 11), (26, 26, 26), 3),
    "done":   ((216, 239, 216), (62, 124, 62), (26, 26, 26), 2),
    "dim":    ((242, 242, 242), (187, 187, 187), (150, 150, 150), 2),
    "new":    ((207, 224, 255), (43, 95, 191), (26, 26, 26), 3),
    "error":  ((255, 255, 255), (192, 57, 43), (26, 26, 26), 3),
}

# style -> (line color, width)
EDGE_STYLES = {
    "normal": ((106, 106, 106), 2),
    "active": ((184, 134, 11), 4),
    "done":   ((62, 124, 62), 3),
    "dim":    ((204, 204, 204), 2),
    "new":    ((43, 95, 191), 4),
    "error":  ((192, 57, 43), 3),
}

_FONT_CACHE = {}


def font(kind, size):
    """kind: 'ui' (Helvetica) or 'code' (Menlo); bold variants 'ui-bold'/'code-bold'."""
    key = (kind, size)
    if key not in _FONT_CACHE:
        paths = {
            "ui": ("/System/Library/Fonts/Helvetica.ttc", 0),
            "ui-bold": ("/System/Library/Fonts/Helvetica.ttc", 1),
            "code": ("/System/Library/Fonts/Menlo.ttc", 0),
            "code-bold": ("/System/Library/Fonts/Menlo.ttc", 1),
        }
        path, index = paths[kind]
        try:
            _FONT_CACHE[key] = ImageFont.truetype(path, size, index=index)
        except OSError:
            _FONT_CACHE[key] = ImageFont.load_default()
    return _FONT_CACHE[key]


_TOFU_SIG = {}


def _mask_bytes(fnt, ch):
    from PIL import Image
    mask = fnt.getmask(ch)
    if mask.size[0] == 0:
        return b""
    return Image.frombytes("L", mask.size, bytes(mask)).tobytes()


def missing_glyphs(kind, size, text):
    """Chars in `text` that the font would render as a tofu box."""
    fnt = font(kind, size)
    key = (kind, size)
    if key not in _TOFU_SIG:
        _TOFU_SIG[key] = _mask_bytes(fnt, "￿")  # guaranteed-unmapped codepoint
    sig = _TOFU_SIG[key]
    out = []
    for ch in set(text):
        if ord(ch) > 0x2000 and _mask_bytes(fnt, ch) == sig and ch not in out:
            out.append(ch)
    return out


def text_size(d, text, fnt):
    """(width, height) of possibly-multiline text."""
    box = d.multiline_textbbox((0, 0), text, font=fnt, spacing=4)
    return box[2] - box[0], box[3] - box[1]


def centered_text(d, center, text, fnt, fill):
    w, h = text_size(d, text, fnt)
    d.multiline_text((center[0] - w / 2, center[1] - h / 2), text,
                     font=fnt, fill=fill, spacing=4, align="center")
    return w, h


# ---- shapes -------------------------------------------------------------

def node_shape(d, shape, box, style_name):
    """Draw a node body. box = (x0, y0, x1, y1)."""
    fill, outline, _, sw = NODE_STYLES[style_name]
    x0, y0, x1, y1 = box
    if shape == "rounded":
        d.rounded_rectangle(box, radius=12, fill=fill, outline=outline, width=sw)
    elif shape == "diamond":
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        pts = [(cx, y0), (x1, cy), (cx, y1), (x0, cy)]
        d.polygon(pts, fill=fill, outline=outline)
        # polygon outline width is 1; retrace for weight
        d.line(pts + [pts[0]], fill=outline, width=sw, joint="curve")
    else:  # box
        d.rectangle(box, fill=fill, outline=outline, width=sw)


def border_point(box, shape, toward):
    """Point on the node border along the ray from box center toward `toward`."""
    x0, y0, x1, y1 = box
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    dx, dy = toward[0] - cx, toward[1] - cy
    if dx == 0 and dy == 0:
        return cx, cy
    if shape == "diamond":
        # |dx|/hw + |dy|/hh = 1 on the rhombus border
        hw, hh = (x1 - x0) / 2, (y1 - y0) / 2
        t = 1.0 / (abs(dx) / hw + abs(dy) / hh)
    else:
        hw, hh = (x1 - x0) / 2, (y1 - y0) / 2
        tx = hw / abs(dx) if dx else float("inf")
        ty = hh / abs(dy) if dy else float("inf")
        t = min(tx, ty)
    return cx + dx * t, cy + dy * t


# ---- arrows -------------------------------------------------------------

def _arrowhead(d, tip, tangent, color, size=11):
    ang = math.atan2(tangent[1], tangent[0])
    spread = math.radians(26)
    p1 = (tip[0] - size * math.cos(ang - spread), tip[1] - size * math.sin(ang - spread))
    p2 = (tip[0] - size * math.cos(ang + spread), tip[1] - size * math.sin(ang + spread))
    d.polygon([tip, p1, p2], fill=color)


def straight_arrow(d, p0, p1, style_name, arrow=True):
    color, width = EDGE_STYLES[style_name]
    d.line([p0, p1], fill=color, width=width)
    if arrow:
        _arrowhead(d, p1, (p1[0] - p0[0], p1[1] - p0[1]), color)
    return ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2)  # label anchor


def curved_arrow(d, p0, p1, side, style_name, bend=0.45, arrow=True):
    """Quadratic bezier from p0 to p1 bulging to `side` ('left'/'right' of travel)."""
    color, width = EDGE_STYLES[style_name]
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    dist = math.hypot(dx, dy) or 1.0
    # unit perpendicular; 'left' = 90° counter-clockwise from travel direction
    px, py = (dy / dist, -dx / dist) if side == "left" else (-dy / dist, dx / dist)
    off = min(bend * dist, 110)
    ctrl = ((p0[0] + p1[0]) / 2 + px * off, (p0[1] + p1[1]) / 2 + py * off)
    steps = 24
    pts = []
    for i in range(steps + 1):
        t = i / steps
        x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * ctrl[0] + t ** 2 * p1[0]
        y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * ctrl[1] + t ** 2 * p1[1]
        pts.append((x, y))
    d.line(pts, fill=color, width=width, joint="curve")
    if arrow:
        _arrowhead(d, pts[-1], (pts[-1][0] - pts[-2][0], pts[-1][1] - pts[-2][1]), color)
    return pts[steps // 2]  # label anchor at t=0.5


def edge_label(d, anchor, text, fnt):
    w, h = text_size(d, text, fnt)
    pad = 3
    box = (anchor[0] - w / 2 - pad, anchor[1] - h / 2 - pad,
           anchor[0] + w / 2 + pad, anchor[1] + h / 2 + pad)
    d.rectangle(box, fill=BG)
    d.multiline_text((anchor[0] - w / 2, anchor[1] - h / 2), text,
                     font=fnt, fill=(90, 90, 90), spacing=2, align="center")


# ---- badges -------------------------------------------------------------

def badge(d, node_box, text, style_name, fnt):
    """Small pill pinned at the node's top-right corner."""
    fill, outline, _, _ = NODE_STYLES[style_name]
    w, h = text_size(d, text, fnt)
    pad_x, pad_y = 7, 3
    x1, y0 = node_box[2], node_box[1]
    box = (x1 - w / 2 - pad_x, y0 - h / 2 - pad_y - 4,
           x1 + w / 2 + pad_x, y0 + h / 2 + pad_y - 4)
    d.rounded_rectangle(box, radius=(box[3] - box[1]) / 2, fill=fill, outline=outline, width=2)
    d.multiline_text((x1 - w / 2, y0 - h / 2 - 4), text, font=fnt, fill=(26, 26, 26), align="center")
