#!/usr/bin/env python3
"""Render the demo session to uniform-size frames with ImageMagick+pango.

Three bugs this replaces (all hit during the first build):
  1. pango renders at INTRINSIC text size unless -size precedes the `pango:`
     input, so every frame came out a different pixel size and the GIF broke.
     Frames are now forced onto a fixed canvas with -extent.
  2. Blank lines collapsed to zero height -> emitted as &nbsp; instead.
  3. Pango requires '#'-prefixed colours; bare hex fails to parse.
"""
from __future__ import annotations

import os
import pathlib
import subprocess
import sys

BG, FG, ACC, CYA, YEL = "#0f1216", "#d6e2ea", "#4ade80", "#38bdf8", "#fbbf24"
LINES_PER_FRAME = 11


def colour_for(s: str) -> str:
    if s.startswith("mcp-sales-intel"):
        return ACC
    if "verdict:" in s or s.startswith(">"):
        return CYA
    if s.lstrip().startswith("$") and any(c.isdigit() for c in s):
        return YEL
    if s.startswith("OK"):
        return ACC
    return FG


def main() -> int:
    if len(sys.argv) < 6:
        print("usage: render_frames.py <session.txt> <outdir> <font> <W> <H>",
              file=sys.stderr)
        return 2

    src, out, font = sys.argv[1], sys.argv[2], sys.argv[3]
    w, h = int(sys.argv[4]), int(sys.argv[5])
    cw, ch = w + 68, h + 68  # 34px border each side

    lines = pathlib.Path(src).read_text(encoding="utf-8", errors="replace").split("\n")
    while lines and not lines[0].strip():
        lines.pop(0)
    if not lines:
        print("empty session", file=sys.stderr)
        return 1

    frames = [
        lines[i : i + LINES_PER_FRAME]
        for i in range(0, len(lines), LINES_PER_FRAME)
    ]

    paths = []
    for idx, chunk in enumerate(frames):
        rows = []
        for ln in chunk:
            s = ln.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            if not s.strip():
                rows.append("<span>&#160;</span>")
            elif s.startswith("mcp-sales-intel"):
                rows.append(f'<span foreground="{ACC}"><b>{s}</b></span>')
            else:
                rows.append(f'<span foreground="{colour_for(s)}">{s}</span>')

        pango = f'<span font="{font}">' + "\n".join(rows) + "</span>"
        p = os.path.join(out, f"s{idx:02d}.png")
        # -size MUST precede `pango:`; -extent forces an exact uniform canvas.
        subprocess.run(
            [
                "convert", "-size", f"{w}x{h}", "-background", BG,
                "pango:" + pango, "-pointsize", "20", "-gravity", "northwest",
                "-bordercolor", BG, "-border", "34", "-extent", f"{cw}x{ch}", p,
            ],
            check=True,
        )
        paths.append(p)

    pathlib.Path(os.path.join(out, "frames.txt")).write_text("\n".join(paths))
    print(f"frames: {len(paths)}  canvas: {cw}x{ch}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
