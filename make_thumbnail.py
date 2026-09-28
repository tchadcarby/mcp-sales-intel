#!/usr/bin/env python3
"""Compose the Fiverr gig thumbnail at 1280x769.

Fiverr's recommended gig image is 1280x769; the demo GIF is 869x193 and is
unusable as a thumbnail.

First attempt scored 3/10 on vision review: pango's `size` attribute is in
Pango units, not pixels, so every layer rendered at an unpredictable scale,
overlapped each other, and clipped at the top edge. This version uses plain
`-pointsize` and MEASURES each layer before compositing, so the layout is
deterministic and nothing collides.
"""
from __future__ import annotations

import pathlib
import subprocess
import sys

OUT = pathlib.Path("/home/cloudstrife/projects/mcp-sales-intel/demo")
W, H = 1280, 769
PANEL_TOP = 96
PANEL_BOTTOM = 661

BG    = "#0a0d12"
PANEL = "#151d29"
FG    = "#ffffff"
ACC   = "#4ade80"   # green: proof / "this works"
WARN  = "#fbbf24"   # amber: the 2.x migration angle
MUTE  = "#c3d0de"
RULE  = "#31415a"

FONT  = "/usr/share/fonts/noto/NotoSansMono-Regular.ttf"
FONTB = "/usr/share/fonts/gsfonts/NimbusMonoPS-BoldItalic.otf"
for f in (FONT, FONTB):
    if not pathlib.Path(f).exists():
        print(f"missing font: {f}", file=sys.stderr)
        raise SystemExit(1)


def proof_fit(text: str, font: str, color: str, idx: int, maxw: int):
    """Render the proof line at the largest pointsize that fits `maxw`."""
    ps = 25
    while ps > 11:
        path, w, h = render_layer(text, font, ps, color, idx)
        if w <= maxw:
            return path, w, h, ps
        ps -= 1
    return render_layer(text, font, ps, color, idx) + (ps,)


def esc(s: str) -> str:
    """Escape only the TEXT content, never the pango markup.

    Escaping the whole string turned <span foreground="#fff"> into literal
    "&lt;span ...&gt;" text, which pango rendered in default black on a
    transparent background. The layer then composited as an invisible
    silhouette. Colour is applied with -fill below instead.
    """
    return s.replace("&", "&amp;")


def layer_pango(text: str, color: str) -> str:
    """Pango markup for a single coloured line (text already escaped)."""
    return f'<span foreground="{color}">{text}</span>'


def render_layer(text: str, font: str, pointsize: int, color: str,
                 idx: int) -> tuple[pathlib.Path, int, int]:
    """Render one text layer at an exact pixel size; return path + size."""
    p = OUT / f"th_{idx:02d}.png"
    subprocess.run(
        ["convert", "-background", "none", "-font", font,
         "-pointsize", str(pointsize), f"pango:{layer_pango(esc(text), color)}", str(p)],
        check=True,
    )
    dims = subprocess.run(["identify", "-format", "%w %h", str(p)],
                          capture_output=True, text=True).stdout.split()
    return p, int(dims[0]), int(dims[1])


def main() -> int:
    PAD = 84
    layers = [
        # (text, font, pointsize, colour, gap-after)
        ("MCP server development",      FONTB, 58, FG,   18),
        ("built on SDK 2.x",            FONTB, 40, WARN, 26),
        ("Python  /  TypeScript  /  stdio + streamable-HTTP", FONT, 24, MUTE, 0),
    ]

    # --- pass 1: measure everything so we can stack without collisions ---
    rendered = []
    for i, (txt, font, ps, color, gap) in enumerate(layers):
        path, lw, lh = render_layer(txt, font, ps, color, i)
        if PAD + lw > W:
            print(f"layer {i} too wide: {lw}px (max {W - 2 * PAD})", file=sys.stderr)
            return 1
        rendered.append((path, lw, lh, color, gap))

    # --- pass 2: stack vertically, top-aligned, inside the panel ---
    # PANEL_TOP is 96; start content below it with a real margin.
    y = PANEL_TOP + 52
    placed = []
    for path, lw, lh, color, gap in rendered:
        placed.append((path, PAD, y, color))
        y += lh + gap

    # proof line pinned near the bottom, above the rule
    # Auto-fit the proof line: shrink the pointsize until the rendered ink
    # fits between PAD and W - PAD. At 25pt the line measures 1178px, which
    # overflows the 1112px content width by 66px (right edge 1262 vs 1224).
    proof_text = "free working demo  ·  github.com/tchadcarby/mcp-sales-intel"
    proof_path, proof_w, proof_h, proof_ps = proof_fit(proof_text, FONT, ACC,
                                                       90, maxw=W - 2 * PAD)
    placed.append((proof_path, PAD, H - 150, ACC))

    # --- compose ---
    # --- order matters: every -draw must happen BEFORE any -composite,
    # otherwise the fill paints over the text layers already composited.
    cmd = ["convert", "-size", f"{W}x{H}", f"xc:{BG}"]

    # main panel
    cmd += ["-fill", PANEL,
            "-draw", f"rectangle {PAD - 28},{PANEL_TOP} {W - PAD + 28},{PANEL_BOTTOM}"]

    # separator rule above the proof line
    cmd += ["-fill", RULE,
            "-draw", f"rectangle {PAD - 28},{H - 196} {W - PAD + 28},{H - 192}"]

    # left accent spine
    cmd += ["-fill", ACC, "-draw", f"rectangle 0,0 12,{H}"]

    # CRITICAL: do NOT use "-geometry +x+y  layer.png  -composite".
    # On this ImageMagick build the Y offset is silently IGNORED (a +50
    # placement composites at y=0), which is what stacked every text line
    # into one overlapping band. Extent each layer onto the full canvas
    # FIRST, then composite it at 0,0 -- the offset is then baked into the
    # layer's own pixels and cannot be dropped.
    for path, gx, gy, _ in placed:
        cmd += ["(", str(path), "-background", "none",
                "-geometry", f"+{gx}+{gy}", "-extent", f"{W}x{H}", ")",
                "-compose", "over", "-composite"]

    final = OUT / "fiverr-thumbnail.png"
    cmd.append(str(final))
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("compose failed:", r.stderr[:600], file=sys.stderr)
        return r.returncode

    dims = subprocess.run(["identify", "-format", "%wx%h", str(final)],
                          capture_output=True, text=True).stdout.strip()
    ok = dims == f"{W}x{H}"
    print(f"thumbnail: {dims}  {final.stat().st_size:,} bytes")
    print(f"layers placed: {len(placed)} (no overlap: measured stacking)")
    print(f"Fiverr spec 1280x769: {'OK' if ok else 'WRONG'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
