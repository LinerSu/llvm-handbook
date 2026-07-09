"""Render a storyboard JSON into an animated GIF (plus QA frame PNGs).

Public API:
    load_storyboard(path) -> Storyboard          (re-exported from model)
    render_frames(sb) -> List[PIL.Image.Image]
    write_outputs(sb, frames, gif_dir, frames_dir=None) -> dict

CLI:
    python3 _meta/anim/render.py _meta/anim/storyboards/X.json \
        --gif-dir data-structure/attachments [--frames-dir /path/to/scratch]

Output is deterministic: fixed fonts/palette, no timestamps — re-rendering an
unchanged storyboard reproduces identical GIF bytes (no iCloud/git churn).
Layout warnings (overflowing labels, oversize GIF) go to stderr as `WARN:` lines.
"""

import argparse
import json
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model import Storyboard, StoryboardError, load_storyboard  # noqa: E402
import draw as D  # noqa: E402

HEADER_H = 44
CAPTION_H = 66
NODE_GAP_X = 26   # horizontal breathing room inside a cell
NODE_GAP_Y = 30
GIF_COLORS = 64
GIF_BUDGET_BYTES = 1_500_000

F_TITLE = ("ui-bold", 17)
F_STEP = ("ui", 15)
F_LABEL = ("code", 14)
F_EDGE = ("ui", 12)
F_BADGE = ("code-bold", 13)
F_CAPTION = ("ui", 16)

_warnings = []


def _warn(msg):
    _warnings.append(msg)
    print("WARN: %s" % msg, file=sys.stderr)


def _canvas_size(sb):
    c = sb.canvas
    w = c.margin * 2 + c.cols * c.cell[0]
    h = HEADER_H + c.margin * 2 + c.rows * c.cell[1] + CAPTION_H
    return w, h


def _node_box(sb, node):
    c = sb.canvas
    col, row = node.at
    cx = c.margin + col * c.cell[0] + c.cell[0] / 2
    cy = HEADER_H + c.margin + row * c.cell[1] + c.cell[1] / 2
    hw = (c.cell[0] - NODE_GAP_X) / 2
    hh = (c.cell[1] - NODE_GAP_Y) / 2
    return (cx - hw, cy - hh, cx + hw, cy + hh)


def _wrap_caption(d, text, fnt, max_w):
    """Wrap caption text to max_w; respect explicit \\n; cap at 2 lines."""
    lines = []
    for para in text.split("\n"):
        words, cur = para.split(), ""
        for w in words:
            cand = (cur + " " + w).strip()
            if d.textlength(cand, font=fnt) <= max_w or not cur:
                cur = cand
            else:
                lines.append(cur)
                cur = w
        lines.append(cur)
    if len(lines) > 2:
        _warn("caption wraps to %d lines (max 2): %r" % (len(lines), text))
        lines = lines[:2]
    return "\n".join(lines)


def _check_glyphs(sb):
    """Warn about characters that would render as tofu boxes (missing glyphs)."""
    ui_texts = [sb.title, sb.summary_caption] + [f.caption for f in sb.frames] + [e.label for e in sb.edges]
    code_texts = [n.label for n in sb.nodes] + [b.text for f in sb.frames for b in f.badges] \
        + [v for f in sb.frames for v in f.set_labels.values()]
    for kind, size, texts in (("ui", F_CAPTION[1], ui_texts), ("code", F_LABEL[1], code_texts)):
        bad = D.missing_glyphs(kind, size, "".join(texts))
        if bad:
            _warn("font %r has no glyph for %s — would render as a box; reword (e.g. Helvetica "
                  "captions lack set/arrow symbols; node labels use Menlo, which has most)"
                  % (kind, " ".join("U+%04X %r" % (ord(c), c) for c in bad)))


class _State(object):
    """Cumulative frame state."""

    def __init__(self, sb):
        self.node_style = {n.id: "normal" for n in sb.nodes}
        self.edge_style = {e.key: "normal" for e in sb.edges}
        self.labels = {n.id: n.label for n in sb.nodes}
        self.badges = []  # list of Badge

    def apply(self, frame):
        self.node_style.update(frame.nodes)
        self.edge_style.update(frame.edges)
        self.labels.update(frame.set_labels)
        if frame.clear_badges:
            self.badges = []
        self.badges.extend(frame.badges)


def _render_one(sb, state, caption, step_text, frame_idx):
    w, h = _canvas_size(sb)
    img = Image.new("RGB", (w, h), D.BG)
    d = ImageDraw.Draw(img)

    # header: title left, step counter right
    d.text((sb.canvas.margin, (HEADER_H - 18) / 2), sb.title,
           font=D.font(*F_TITLE), fill=D.HEADER_TEXT)
    sw = d.textlength(step_text, font=D.font(*F_STEP))
    d.text((w - sb.canvas.margin - sw, (HEADER_H - 16) / 2), step_text,
           font=D.font(*F_STEP), fill=D.HEADER_TEXT)
    d.line([(0, HEADER_H), (w, HEADER_H)], fill=D.CAPTION_BG, width=2)

    boxes = {n.id: _node_box(sb, n) for n in sb.nodes}
    shapes = {n.id: n.shape for n in sb.nodes}

    # edges under nodes
    for e in sb.edges:
        b0, b1 = boxes[e.src], boxes[e.dst]
        c0 = ((b0[0] + b0[2]) / 2, (b0[1] + b0[3]) / 2)
        c1 = ((b1[0] + b1[2]) / 2, (b1[1] + b1[3]) / 2)
        style = state.edge_style[e.key]
        if e.curve == "none":
            p0 = D.border_point(b0, shapes[e.src], c1)
            p1 = D.border_point(b1, shapes[e.dst], c0)
            anchor = D.straight_arrow(d, p0, p1, style, arrow=e.arrow)
        else:
            # aim start/end slightly toward the bulge side so the curve leaves the border cleanly
            side = e.curve
            dxy = (c1[0] - c0[0], c1[1] - c0[1])
            perp = (dxy[1], -dxy[0]) if side == "left" else (-dxy[1], dxy[0])
            mid = ((c0[0] + c1[0]) / 2 + perp[0] * 0.3, (c0[1] + c1[1]) / 2 + perp[1] * 0.3)
            p0 = D.border_point(b0, shapes[e.src], mid)
            p1 = D.border_point(b1, shapes[e.dst], mid)
            anchor = D.curved_arrow(d, p0, p1, side, style, arrow=e.arrow)
        if e.label:
            D.edge_label(d, anchor, e.label, D.font(*F_EDGE))

    # nodes + labels
    for n in sb.nodes:
        box = boxes[n.id]
        style = state.node_style[n.id]
        D.node_shape(d, n.shape, box, style)
        text = state.labels[n.id]
        fnt = D.font(*F_LABEL)
        tw, th = D.text_size(d, text, fnt)
        inner_w = (box[2] - box[0]) - 14
        inner_h = (box[3] - box[1]) - 10
        if n.shape == "diamond":
            inner_w *= 0.62
        if tw > inner_w or th > inner_h:
            _warn("frame %d: node '%s' label overflows its box (%.0fx%.0f > %.0fx%.0f): %r"
                  % (frame_idx, n.id, tw, th, inner_w, inner_h, text))
        color = D.NODE_STYLES[style][2]
        D.centered_text(d, ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2), text, fnt, color)

    # badges over everything
    for b in state.badges:
        D.badge(d, boxes[b.node], b.text, b.style, D.font(*F_BADGE))

    # caption bar
    d.rectangle([(0, h - CAPTION_H), (w, h)], fill=D.CAPTION_BG)
    cap = _wrap_caption(d, caption, D.font(*F_CAPTION), w - 2 * sb.canvas.margin)
    d.multiline_text((sb.canvas.margin, h - CAPTION_H + 12), cap,
                     font=D.font(*F_CAPTION), fill=D.CAPTION_TEXT, spacing=6)
    return img


def render_frames(sb):
    """Render every frame (plus the auto summary frame, if summary_caption is set).

    Returns (frames, durations_ms) — kept in lockstep.
    """
    _check_glyphs(sb)
    state = _State(sb)
    frames, durations = [], []
    total = len(sb.frames) + (1 if sb.summary_caption else 0)
    for i, f in enumerate(sb.frames):
        state.apply(f)
        img = _render_one(sb, state, f.caption, "%d/%d" % (i + 1, total), i)
        frames.append(img)
        durations.append(f.duration_ms if f.duration_ms else sb.step_ms)
    if sb.summary_caption:
        img = _render_one(sb, state, sb.summary_caption, "%d/%d" % (total, total), len(sb.frames))
        frames.append(img)
        durations.append(sb.hold_ms)
    else:
        durations[-1] = max(durations[-1], sb.hold_ms)
    return frames, durations


def write_outputs(sb, frames, durations, gif_dir, frames_dir=None):
    """Write <gif_dir>/<id>.gif; if frames_dir, also f00.png.. + a contact sheet."""
    os.makedirs(gif_dir, exist_ok=True)
    gif_path = os.path.join(gif_dir, sb.id + ".gif")
    pal = [f.convert("P", palette=Image.ADAPTIVE, colors=GIF_COLORS) for f in frames]
    pal[0].save(gif_path, save_all=True, append_images=pal[1:],
                duration=durations, loop=0, optimize=False, disposal=1)
    gif_bytes = os.path.getsize(gif_path)
    if gif_bytes > GIF_BUDGET_BYTES:
        _warn("gif is %.2f MB — over the 1.5 MB budget; cut frames or shrink the canvas"
              % (gif_bytes / 1e6))

    result = {"gif": gif_path, "gif_bytes": gif_bytes,
              "frame_count": len(frames), "warnings": list(_warnings)}
    if frames_dir:
        os.makedirs(frames_dir, exist_ok=True)
        paths = []
        for i, f in enumerate(frames):
            p = os.path.join(frames_dir, "f%02d.png" % i)
            f.save(p)
            paths.append(p)
        # contact sheet: numbered thumbnails, 3 per row
        scale, per_row, pad = 0.42, 3, 10
        tw = int(frames[0].width * scale)
        th = int(frames[0].height * scale)
        rows = (len(frames) + per_row - 1) // per_row
        sheet = Image.new("RGB", (per_row * (tw + pad) + pad, rows * (th + pad + 18) + pad), D.BG)
        sd = ImageDraw.Draw(sheet)
        for i, f in enumerate(frames):
            x = pad + (i % per_row) * (tw + pad)
            y = pad + (i // per_row) * (th + pad + 18)
            sheet.paste(f.resize((tw, th), Image.LANCZOS), (x, y))
            sd.text((x, y + th + 2), "frame %d" % i, font=D.font("ui", 13), fill=D.HEADER_TEXT)
        sheet_path = os.path.join(frames_dir, sb.id + "-sheet.png")
        sheet.save(sheet_path)
        result["frames"] = paths
        result["sheet"] = sheet_path
    return result


def main(argv=None):
    ap = argparse.ArgumentParser(description="Render a storyboard JSON to an animated GIF.")
    ap.add_argument("storyboard", help="path to the storyboard .json")
    ap.add_argument("--gif-dir", required=True, help="output dir for the .gif (a facet attachments/ dir)")
    ap.add_argument("--frames-dir", default=None, help="optional dir for QA frame PNGs + contact sheet")
    args = ap.parse_args(argv)
    try:
        sb = load_storyboard(args.storyboard)
    except StoryboardError as e:
        print("STORYBOARD ERROR: %s" % e, file=sys.stderr)
        return 2
    frames, durations = render_frames(sb)
    result = write_outputs(sb, frames, durations, args.gif_dir, args.frames_dir)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
