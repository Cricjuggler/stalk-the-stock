"""
Strip backgrounds from Stalky source images and save them with the right
filenames into formcheck/frontend/assets/.

USAGE
-----
1. Save your source PNGs/JPGs into formcheck/tools/_source/ using these names:

     headshot.<ext>          -> becomes stalky.png            (BLACK bg)
     full.<ext>              -> becomes stalky-full.png       (WHITE bg)
     pose-thinking.<ext>     -> becomes stalky-thinking.png   (WHITE bg)
     pose-excited.<ext>      -> becomes stalky-excited.png    (WHITE bg)
     pose-sad.<ext>          -> becomes stalky-sad.png        (WHITE bg)
     pose-wink.<ext>         -> becomes stalky-wink.png       (WHITE bg)

   Any of <ext> = png / jpg / jpeg / webp works. Missing files are skipped —
   you only need the ones you actually want to use.

2. From the formcheck/ folder, run:

     pip install Pillow numpy
     python tools/prepare_avatars.py

3. Refresh http://localhost:8000 — Stalky shows up.
"""
from __future__ import annotations
from pathlib import Path
import sys

try:
    from PIL import Image
    import numpy as np
except ImportError:
    print("Missing dependency. Run:  pip install Pillow numpy")
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
SRC = Path(__file__).resolve().parent / "_source"
OUT = ROOT / "frontend" / "assets"

EXTS = (".png", ".jpg", ".jpeg", ".webp")

# (basename, output filename, background to strip)
JOBS = [
    ("headshot",      "stalky.png",          "white"),
    ("full",          "stalky-full.png",     "white"),
    ("pose-thinking", "stalky-thinking.png", "white"),
    ("pose-excited",  "stalky-excited.png",  "white"),
    ("pose-sad",      "stalky-sad.png",      "white"),
    ("pose-wink",     "stalky-wink.png",     "white"),
]


def find_source(basename: str) -> Path | None:
    for ext in EXTS:
        p = SRC / f"{basename}{ext}"
        if p.exists():
            return p
    return None


def remove_background(img_path: Path, out_path: Path, bg: str, threshold: int = 28) -> int:
    """Alpha-key near-pure white or near-pure black pixels.

    Uses a soft falloff so anti-aliased edges don't hard-clip and leave a halo.
    Returns the number of fully-transparent pixels written.
    """
    img = Image.open(img_path).convert("RGBA")
    arr = np.array(img).astype(np.int16)
    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    existing_alpha = arr[:, :, 3].astype(np.uint8)

    if bg == "white":
        # distance from pure white (per-pixel max of channel deltas)
        dist = np.maximum.reduce([255 - r, 255 - g, 255 - b])
    elif bg == "black":
        dist = np.maximum.reduce([r, g, b])
    else:
        raise ValueError(f"unknown bg: {bg}")

    # alpha = 0 where dist <= threshold; full opaque past 2 * threshold; soft ramp between
    computed_alpha = np.clip((dist - threshold) * (255 / max(threshold, 1)), 0, 255).astype(np.uint8)
    # Preserve existing transparency: anything already transparent stays transparent
    alpha = np.minimum(existing_alpha, computed_alpha)
    arr[:, :, 3] = alpha

    out = Image.fromarray(arr.astype(np.uint8))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out.save(out_path)
    return int((alpha == 0).sum())


def main():
    SRC.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)

    print(f"Source dir: {SRC}")
    print(f"Output dir: {OUT}\n")

    saved = 0
    skipped = 0
    for basename, out_name, bg in JOBS:
        src = find_source(basename)
        if src is None:
            print(f"  -  skip   {basename}.*  (no source file)")
            skipped += 1
            continue
        out_path = OUT / out_name
        keyed = remove_background(src, out_path, bg=bg)
        rel_in = src.relative_to(ROOT)
        rel_out = out_path.relative_to(ROOT)
        print(f"  ok {rel_in}  ->  {rel_out}   [{keyed:,} bg px keyed, bg={bg}]")
        saved += 1

    print(f"\n{saved} saved, {skipped} skipped.")
    if saved == 0:
        print("No source files found. Drop your images into:")
        print(f"   {SRC}")
        sys.exit(1)


if __name__ == "__main__":
    main()
