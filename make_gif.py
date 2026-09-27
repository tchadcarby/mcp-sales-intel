#!/usr/bin/env python3
"""Assemble the rendered screens into a looping GIF.

Replaces the shell pipeline: ImageMagick's `ls`-style output leaked `[0]`
frame suffixes into the ffmpeg concat list, which then failed to open.

Deterministic here, no shell quoting, no glob surprises.
"""
from __future__ import annotations

import pathlib
import re
import subprocess
import sys

OUT = pathlib.Path("/home/cloudstrife/projects/mcp-sales-intel/demo")
FPS = 20
HOLD = 14   # repeats per screen (~0.7s)
FADE = 6    # fade frames
TAIL = 34   # final hold
BG = "#0f1216"


def _run(cmd: list[str]) -> str:
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"{cmd[0]} failed: {r.stderr[:300]}")
    return r.stdout.strip()


def normalise(frames: list[pathlib.Path]) -> list[pathlib.Path]:
    """Trim dead space, then pad to a COMMON size so the GIF is uniform.

    Vision review of the first build showed ~70% of each frame was empty
    black — the pango -extent canvas was sized for the tallest screen, so
    shorter screens got big empty regions. Trim first, then pad to the
    largest trimmed size.
    """
    trimmed: list[pathlib.Path] = []
    for f in frames:
        t = f.with_name(f.stem + "_t.png")
        subprocess.run(["convert", str(f), "-trim", "+repage", str(t)], check=True)
        trimmed.append(t)

    dims = [
        tuple(map(int, _run(["identify", "-format", "%w %h", str(t)]).split()))
        for t in trimmed
    ]
    # +1px safety: identical dims across frames is a GIF/ffmpeg requirement
    cw = max(w for w, _ in dims) + 1
    ch = max(h for _, h in dims) + 1

    out: list[pathlib.Path] = []
    for t in trimmed:
        p = t.with_name(t.stem.replace("_t", "") + "_n.png")
        subprocess.run(
            ["convert", str(t), "-background", BG, "-gravity", "northwest",
             "-extent", f"{cw}x{ch}", str(p)],
            check=True,
        )
        t.unlink(missing_ok=True)
        out.append(p)
    print(f"normalised: trimmed -> {cw}x{ch} (was {dims[0][0]}x{dims[0][1]}+)")
    return out


def main() -> int:
    # only the raw rendered screens (sNN.png), never the _t/_n intermediates
    frames = sorted(
        p for p in OUT.glob("s*.png")
        if not p.stem.endswith(("_t", "_n"))
    )
    if not frames:
        print("no frames rendered", file=sys.stderr)
        return 1

    # clear stale intermediates from a previous run
    for p in OUT.glob("s*_t.png"):
        p.unlink(missing_ok=True)
    for p in OUT.glob("s*_n.png"):
        p.unlink(missing_ok=True)

    frames = normalise(frames)

    seq: list[pathlib.Path] = []
    for i, f in enumerate(frames):
        seq.extend([f] * HOLD)
        if i < len(frames) - 1:
            seq.extend([frames[i + 1]] * FADE)
    seq.extend([frames[-1]] * TAIL)

    # collapse consecutive duplicates
    dedup: list[pathlib.Path] = []
    for f in seq:
        if not dedup or dedup[-1] != f:
            dedup.append(f)

    listing = OUT / "seq.txt"
    # ffmpeg's concat demuxer ignored our per-file durations when the repeated
    # source images are byte-identical, collapsing the loop to ~0.08s.
    # ImageMagick's native GIF writer honours -delay reliably, so use it.
    with listing.open("w", encoding="utf-8") as fh:
        fh.write("\n".join(str(f) for f in dedup))

    gif = OUT / "mcp-demo.gif"
    delay_cs = round(100.0 / FPS)  # GIF delay is in centiseconds
    cmd = [
        "convert", "-delay", str(delay_cs), "-loop", "0",
        "-layers", "OptimizeTransparency",
        *[str(f) for f in dedup],
        "-colors", "160", str(gif),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("convert failed:", r.stderr[:800], file=sys.stderr)
        return r.returncode

    size = gif.stat().st_size
    # frame count + duration via ffprobe
    dur = "?"
    try:
        p = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-count_frames", "-show_entries",
             "stream=nb_read_frames,width,height", "-of", "csv=p=0", str(gif)],
            capture_output=True, text=True, timeout=60,
        )
        dur = p.stdout.strip() or "?"
    except Exception:
        pass

    print(f"GIF: {gif}")
    print(f"  bytes      : {size:,}")
    print(f"  screens    : {len(frames)}")
    print(f"  w x h, frms: {dur}")
    # Fiverr accepts up to 16MB
    print(f"  fiverr ok  : {'YES' if size <= 16 * 1024 * 1024 else 'TOO BIG'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
