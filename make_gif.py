#!/usr/bin/env python3
"""Assemble the rendered screens into a looping GIF.

Replaces the shell pipeline: ImageMagick's `ls`-style output leaked `[0]`
frame suffixes into the ffmpeg concat list, which then failed to open.

Deterministic here, no shell quoting, no glob surprises.
"""
from __future__ import annotations

import pathlib
import subprocess
import sys

OUT = pathlib.Path("/home/cloudstrife/projects/mcp-sales-intel/demo")
FPS = 20
HOLD = 14   # repeats per screen (~0.7s)
FADE = 6    # fade frames
TAIL = 34   # final hold


def main() -> int:
    frames = sorted(OUT.glob("s*.png"))
    if not frames:
        print("no frames rendered", file=sys.stderr)
        return 1

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
    with listing.open("w", encoding="utf-8") as fh:
        for f in dedup:
            fh.write(f"file '{f}'\nduration 0.05\n")
        fh.write(f"file '{dedup[-1]}'\n")  # concat demuxer needs a final entry

    gif = OUT / "mcp-demo.gif"
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "concat", "-safe", "0", "-i", str(listing),
        "-vf",
        "fps=20,scale=trunc(iw/2)*2:trunc(ih/2)*2:flags=lanczos,"
        "split[s0][s1];[s0]palettegen=max_colors=160[p];"
        "[s1][p]paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle",
        "-loop", "0", str(gif),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("ffmpeg failed:", r.stderr[:800], file=sys.stderr)
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
