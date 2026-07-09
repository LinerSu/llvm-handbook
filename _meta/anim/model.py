"""Storyboard data model + JSON validation for the vault's GIF animations.

A storyboard is a declarative JSON description of a CFG-style diagram and a
sequence of cumulative frames (each frame inherits the previous frame's state
and applies overrides). See `storyboard-spec.md` for the authoring guide.

Python 3.9-compatible (system python on macOS): no `X | Y` unions, no `match`.
"""

import json
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

STYLES = ("normal", "active", "done", "dim", "new", "error")
SHAPES = ("box", "rounded", "diamond")
CURVES = ("none", "left", "right")

ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")


class StoryboardError(ValueError):
    """Validation error that names the offending key/frame."""


def _require(cond, msg):
    if not cond:
        raise StoryboardError(msg)


@dataclass
class Canvas:
    cols: int
    rows: int
    cell: Tuple[int, int]  # (width, height) of one grid cell, px
    margin: int


@dataclass
class Node:
    id: str
    at: Tuple[int, int]  # (col, row) grid position
    label: str
    shape: str = "box"


@dataclass
class Edge:
    src: str
    dst: str
    curve: str = "none"
    label: str = ""

    @property
    def key(self):
        return "%s->%s" % (self.src, self.dst)


@dataclass
class Badge:
    node: str
    text: str
    style: str = "new"


@dataclass
class Frame:
    caption: str
    nodes: Dict[str, str] = field(default_factory=dict)   # node id -> style
    edges: Dict[str, str] = field(default_factory=dict)   # "a->b"   -> style
    set_labels: Dict[str, str] = field(default_factory=dict)
    badges: List[Badge] = field(default_factory=list)
    clear_badges: bool = False
    duration_ms: Optional[int] = None


@dataclass
class Storyboard:
    id: str
    title: str
    canvas: Canvas
    nodes: List[Node]
    edges: List[Edge]
    frames: List[Frame]
    step_ms: int = 1400
    hold_ms: int = 3200
    summary_caption: str = ""

    def node_ids(self):
        return [n.id for n in self.nodes]

    def edge_keys(self):
        return [e.key for e in self.edges]


def _parse_canvas(raw):
    _require(isinstance(raw, dict), "canvas: must be an object")
    for k in ("cols", "rows", "cell"):
        _require(k in raw, "canvas: missing key '%s'" % k)
    cell = raw["cell"]
    _require(
        isinstance(cell, list) and len(cell) == 2 and all(isinstance(v, int) for v in cell),
        "canvas.cell: must be [width, height] ints",
    )
    c = Canvas(
        cols=int(raw["cols"]),
        rows=int(raw["rows"]),
        cell=(cell[0], cell[1]),
        margin=int(raw.get("margin", 24)),
    )
    _require(1 <= c.cols <= 6 and 1 <= c.rows <= 6, "canvas: cols/rows must be 1..6")
    _require(120 <= c.cell[0] <= 320 and 70 <= c.cell[1] <= 240, "canvas.cell: width 120..320, height 70..240")
    return c


def _parse_nodes(raw, canvas):
    _require(isinstance(raw, list) and raw, "nodes: must be a non-empty array")
    nodes, seen = [], set()
    for i, n in enumerate(raw):
        where = "nodes[%d]" % i
        _require(isinstance(n, dict), "%s: must be an object" % where)
        for k in ("id", "at", "label"):
            _require(k in n, "%s: missing key '%s'" % (where, k))
        nid = n["id"]
        _require(ID_RE.match(nid or ""), "%s.id: '%s' must match %s" % (where, nid, ID_RE.pattern))
        _require(nid not in seen, "%s.id: duplicate node id '%s'" % (where, nid))
        seen.add(nid)
        at = n["at"]
        _require(
            isinstance(at, list) and len(at) == 2 and all(isinstance(v, int) for v in at),
            "%s.at: must be [col, row] ints" % where,
        )
        _require(
            0 <= at[0] < canvas.cols and 0 <= at[1] < canvas.rows,
            "%s.at: [%s, %s] outside canvas grid %dx%d" % (where, at[0], at[1], canvas.cols, canvas.rows),
        )
        shape = n.get("shape", "box")
        _require(shape in SHAPES, "%s.shape: '%s' not one of %s" % (where, shape, SHAPES))
        nodes.append(Node(id=nid, at=(at[0], at[1]), label=str(n["label"]), shape=shape))
    positions = {}
    for n in nodes:
        _require(n.at not in positions, "nodes: '%s' and '%s' share grid cell %s" % (positions.get(n.at), n.id, list(n.at)))
        positions[n.at] = n.id
    return nodes


def _parse_edges(raw, node_ids):
    _require(isinstance(raw, list), "edges: must be an array")
    edges, seen = [], set()
    for i, e in enumerate(raw):
        where = "edges[%d]" % i
        _require(isinstance(e, dict), "%s: must be an object" % where)
        for k in ("from", "to"):
            _require(k in e, "%s: missing key '%s'" % (where, k))
            _require(e[k] in node_ids, "%s.%s: unknown node '%s'" % (where, k, e[k]))
        curve = e.get("curve", "none")
        _require(curve in CURVES, "%s.curve: '%s' not one of %s" % (where, curve, CURVES))
        edge = Edge(src=e["from"], dst=e["to"], curve=curve, label=str(e.get("label", "")))
        _require(edge.key not in seen, "%s: duplicate edge '%s'" % (where, edge.key))
        seen.add(edge.key)
        edges.append(edge)
    return edges


def _parse_style_map(raw, valid_keys, where, kind):
    _require(isinstance(raw, dict), "%s.%s: must be an object" % (where, kind))
    out = {}
    for k, v in raw.items():
        _require(k in valid_keys, "%s.%s: unknown %s '%s'" % (where, kind, kind.rstrip("s"), k))
        _require(v in STYLES, "%s.%s['%s']: style '%s' not one of %s" % (where, kind, k, v, STYLES))
        out[k] = v
    return out


def _parse_frames(raw, node_ids, edge_keys):
    _require(isinstance(raw, list) and raw, "frames: must be a non-empty array")
    frames = []
    for i, f in enumerate(raw):
        where = "frames[%d]" % i
        _require(isinstance(f, dict), "%s: must be an object" % where)
        _require("caption" in f, "%s: missing key 'caption'" % where)
        fr = Frame(caption=str(f["caption"]))
        if "nodes" in f:
            fr.nodes = _parse_style_map(f["nodes"], node_ids, where, "nodes")
        if "edges" in f:
            fr.edges = _parse_style_map(f["edges"], edge_keys, where, "edges")
        if "set_labels" in f:
            _require(isinstance(f["set_labels"], dict), "%s.set_labels: must be an object" % where)
            for k in f["set_labels"]:
                _require(k in node_ids, "%s.set_labels: unknown node '%s'" % (where, k))
            fr.set_labels = {k: str(v) for k, v in f["set_labels"].items()}
        if "badges" in f:
            _require(isinstance(f["badges"], list), "%s.badges: must be an array" % where)
            for j, b in enumerate(f["badges"]):
                bwhere = "%s.badges[%d]" % (where, j)
                _require(isinstance(b, dict) and "node" in b and "text" in b, "%s: needs {node, text}" % bwhere)
                _require(b["node"] in node_ids, "%s.node: unknown node '%s'" % (bwhere, b["node"]))
                style = b.get("style", "new")
                _require(style in STYLES, "%s.style: '%s' not one of %s" % (bwhere, style, STYLES))
                fr.badges.append(Badge(node=b["node"], text=str(b["text"]), style=style))
        fr.clear_badges = bool(f.get("clear_badges", False))
        if "duration_ms" in f:
            _require(isinstance(f["duration_ms"], int) and 200 <= f["duration_ms"] <= 10000,
                     "%s.duration_ms: must be an int in 200..10000" % where)
            fr.duration_ms = f["duration_ms"]
        frames.append(fr)
    return frames


def load_storyboard(path):
    """Parse + validate a storyboard JSON file. Raises StoryboardError naming the bad key."""
    with open(path, "r", encoding="utf-8") as fh:
        try:
            raw = json.load(fh)
        except json.JSONDecodeError as e:
            raise StoryboardError("%s: not valid JSON — %s" % (path, e))
    _require(isinstance(raw, dict), "top level: must be an object")
    for k in ("id", "title", "canvas", "nodes", "edges", "frames"):
        _require(k in raw, "top level: missing key '%s'" % k)
    _require(ID_RE.match(raw["id"] or ""), "id: '%s' must match %s (it names the .gif)" % (raw["id"], ID_RE.pattern))
    canvas = _parse_canvas(raw["canvas"])
    nodes = _parse_nodes(raw["nodes"], canvas)
    node_ids = [n.id for n in nodes]
    edges = _parse_edges(raw["edges"], node_ids)
    frames = _parse_frames(raw["frames"], node_ids, [e.key for e in edges])
    defaults = raw.get("defaults", {})
    _require(isinstance(defaults, dict), "defaults: must be an object")
    step_ms = int(defaults.get("step_ms", 1400))
    hold_ms = int(defaults.get("hold_ms", 3200))
    _require(400 <= step_ms <= 5000, "defaults.step_ms: must be 400..5000")
    _require(step_ms <= hold_ms <= 15000, "defaults.hold_ms: must be step_ms..15000")
    _require(len(frames) <= 24, "frames: max 24 frames (GIF size budget)")
    return Storyboard(
        id=raw["id"],
        title=str(raw["title"]),
        canvas=canvas,
        nodes=nodes,
        edges=edges,
        frames=frames,
        step_ms=step_ms,
        hold_ms=hold_ms,
        summary_caption=str(raw.get("summary_caption", "")),
    )
