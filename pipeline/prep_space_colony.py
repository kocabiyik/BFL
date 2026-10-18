"""Turn the raw NASA paintings into a training set: drop rejects, crop the
photo mats/borders, and resize to about 2048 px on the long side.

Usage:
    python pipeline/prep_space_colony.py [name ...]

Reads data/space_colony/raw/, writes data/space_colony/train/<nasa_id>.jpg.
Captions (<nasa_id>.txt) are written separately.
"""

import glob
import os
import sys

from PIL import Image, ImageChops

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "space_colony", "raw")
OUT = os.path.join(ROOT, "data", "space_colony", "train")

DROP = {
    "ARC-1977-AC77-0475-10",  # 768 px, colour bar
    "ARC-1978-A78-0238",      # black-and-white copy of AC78-0238
    "ARC-1977-AC77-0475-3",   # near-duplicate of 0475-2
    "ARC-1977-AC77-0475-4",   # near-duplicate of 0475-7
    "ARC-1975-AC75-1917",     # "USA" lettering
    "ARC-1977-AC77-0475-5",   # Venus overload; mostly sky
    "ARC-1977-AC77-0475-6",   # Venus overload
    "ARC-1972-AC72-1279",     # multi-panel chart, not one picture
    "ARC-1973-AC73-9345",     # allegorical figure, a different look
}
# One artist only: Rick Guidice. Don Davis's paintings and the uncredited
# ones (same 1975 batch as Davis's AC75-1920) would blend two hands.
DROP |= {
    "ARC-1975-AC75-1886", "ARC-1975-AC75-1920", "ARC-1975-AC75-2621",
    "ARC-1977-AC77-0475-9", "ARC-1977-AC77-0475-11", "ARC-1977-AC77-0475-12",
    "ARC-1975-AC75-1918", "ARC-1975-AC75-1921", "ARC-1975-AC75-1923",
    "ARC-1975-AC75-1924", "ARC-1976-AC76-0525",
}
# Manual crop boxes (fractions left, top, right, bottom) where the automatic
# mat detection is not enough. Filled in after reviewing the contact sheet.
MANUAL = {
    "ARC-1975-AC75-1086": (0.11, 0.04, 0.89, 0.89),
    "ARC-1975-AC75-1923": (0.13, 0.16, 0.87, 0.83),
    "ARC-1976-AC76-0296": (0.125, 0.12, 0.875, 0.94),
    "ARC-1976-AC76-0297": (0.14, 0.06, 0.86, 0.83),
    "ARC-1977-AC77-0475-1": (0.08, 0.01, 0.905, 0.99),
    "ARC-1977-AC77-0475-12": (0.08, 0.01, 0.82, 0.98),
}
# Second crop on the trimmed image (same fractions): leftover mat edges, and
# signatures that sit on an edge. Signatures inside the picture are removed
# by erase_signatures.py instead.
TRIM = {
    "ARC-1975-AC75-1086-1": (0.04, 0.0, 1.0, 1.0),     # vertical signature
    "ARC-1975-AC75-1086": (0.0, 0.0, 1.0, 0.925),     # signature
    "ARC-1975-AC75-1886": (0.0, 0.0, 1.0, 0.95),      # signature
    "ARC-1975-AC75-2621": (0.0, 0.0, 1.0, 0.925),     # signature + date
    "ARC-1977-AC77-0475-2": (0.0, 0.04, 1.0, 0.98),
    "ARC-1977-AC77-0475-8": (0.035, 0.0, 0.97, 0.93),
    "ARC-1977-AC77-0475-9": (0.0, 0.045, 1.0, 0.98),
    "ARC-1977-AC77-0475-11": (0.0, 0.02, 1.0, 0.94),
    "ARC-1977-AC77-0475-12": (0.0, 0.0, 1.0, 0.965),
    "ARC-1978-AC78-0330-1": (0.0, 0.0, 1.0, 0.935),   # signature
    "ARC-1978-AC78-0330-2": (0.0, 0.0, 1.0, 0.945),   # signature
    "ARC-1978-AC78-0330-3": (0.0, 0.0, 1.0, 0.925),   # signature
}
LONG_SIDE = 2048
INSET = 0.015  # shave the mat's edge line and any tape


def trim_mat(im):
    """Crop a flat border whose colour matches the image corners."""
    small = im.copy()
    small.thumbnail((800, 800))
    sx, sy = im.width / small.width, im.height / small.height
    box = (0, 0, small.width, small.height)
    for corner in ((0, 0), (small.width - 1, small.height - 1)):
        bg = Image.new("RGB", small.size, small.getpixel(corner))
        diff = ImageChops.difference(small, bg).convert("L").point(lambda v: 255 if v > 28 else 0)
        found = diff.getbbox()
        if found:
            box = (max(box[0], found[0]), max(box[1], found[1]),
                   min(box[2], found[2]), min(box[3], found[3]))
    w, h = box[2] - box[0], box[3] - box[1]
    # Space art with black edges: corners are "background" but so are the
    # stars' surroundings; ignore detections that would cut too much.
    if w < 0.5 * small.width or h < 0.5 * small.height:
        box = (0, 0, small.width, small.height)
    ix, iy = INSET * w, INSET * h
    return im.crop((int((box[0] + ix) * sx), int((box[1] + iy) * sy),
                    int((box[2] - ix) * sx), int((box[3] - iy) * sy)))


os.makedirs(OUT, exist_ok=True)
for path in sorted(glob.glob(os.path.join(RAW, "*.jpg"))):
    name = os.path.splitext(os.path.basename(path))[0]
    if name in DROP or (sys.argv[1:] and name not in sys.argv[1:]):
        continue
    im = Image.open(path).convert("RGB")
    if name in MANUAL:
        l, t, r, b = MANUAL[name]
        im = im.crop((int(l * im.width), int(t * im.height),
                      int(r * im.width), int(b * im.height)))
    else:
        im = trim_mat(im)
    if name in TRIM:
        l, t, r, b = TRIM[name]
        im = im.crop((int(l * im.width), int(t * im.height),
                      int(r * im.width), int(b * im.height)))
    im.thumbnail((LONG_SIDE, LONG_SIDE), Image.LANCZOS)
    im.save(os.path.join(OUT, f"{name}.jpg"), quality=95)
    print(f"{name} {im.width}x{im.height}")
