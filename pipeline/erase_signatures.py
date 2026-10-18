"""Remove painted signatures inside the training images with FLUX Erase.

Usage:
    python pipeline/erase_signatures.py [name ...]

Run after prep_space_colony.py. Edits data/space_colony/train/<name>.jpg in
place; boxes are fractions (left, top, right, bottom) of the prepped image.
"""

import base64
import io
import os
import sys

from PIL import Image, ImageDraw

import bfl

TRAIN = os.path.join(bfl.ROOT, "data", "space_colony", "train")
SIGNATURES = {
    "ARC-1974-AC73-9344": (0.81, 0.94, 0.92, 1.0),
    "ARC-1976-AC76-0296": (0.54, 0.85, 0.595, 0.90),
    "ARC-1976-AC76-0297": (0.83, 0.85, 0.895, 0.90),
    "ARC-1976-AC76-1089": (0.70, 0.86, 0.81, 0.91),
    "ARC-1978-AC78-0238": (0.84, 0.71, 0.90, 0.76),
    "ARC-1977-AC77-1069": (0.67, 0.835, 0.745, 0.865),
}

for name in sys.argv[1:] or SIGNATURES:
    l, t, r, b = SIGNATURES[name]
    path = os.path.join(TRAIN, f"{name}.jpg")
    im = Image.open(path).convert("RGB")
    mask = Image.new("L", im.size, 0)
    ImageDraw.Draw(mask).rectangle(
        (l * im.width, t * im.height, r * im.width, b * im.height), fill=255)
    png = io.BytesIO()
    mask.save(png, "PNG")
    mask_path = os.path.join(bfl.ROOT, "out", "masks", f"{name}.png")
    os.makedirs(os.path.dirname(mask_path), exist_ok=True)
    mask.save(mask_path)
    src = io.BytesIO()
    im.save(src, "PNG")
    result = bfl.run("flux-tools/erase-v1", {
        "image": base64.b64encode(src.getvalue()).decode(),
        "mask": base64.b64encode(png.getvalue()).decode(),
    })
    tmp = bfl.download(result["sample"], os.path.join(bfl.ROOT, "out", "erased", f"{name}.png"))
    Image.open(tmp).convert("RGB").resize(im.size).save(path, quality=95)
