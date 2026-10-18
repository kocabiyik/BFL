"""Base check: can FLUX 3 Image Klein make the 1970s NASA Ames look without a
LoRA? Generates each film subject twice with a fixed seed:

  trigger: content + "nsc7 style"  (what the LoRA will get; base vs LoRA pair)
  attrs:   content + the style described by its attributes (best effort
           without a LoRA; if this already matches the dataset, pick
           another style)

Usage:
    python pipeline/base_check.py

Writes out/base_check/<subject>_<variant>.png and a contact sheet.
"""

import os

from PIL import Image, ImageDraw, ImageFont

import bfl

OUT = os.path.join(bfl.ROOT, "out", "base_check")
SEED = 1975

# Film subjects that are NOT in the training set (docs/clips.md).
SUBJECTS = {
    "rover": "The Perseverance rover, a six-wheeled car-sized robot with a tall camera mast, sits alone on a rock-strewn crater floor on Mars, with a low ridge on the horizon and a dusty butterscotch sky.",
    "liftoff": "An Atlas V rocket lifts off from its launch pad at dawn, a bright flame and a huge billowing cloud of white exhaust spreading across the ground beside the steel launch tower.",
    "parachute": "A cone-shaped spacecraft descends over a dusty red planet under a huge red and white striped parachute, high above craters and canyons, with the curved horizon below.",
    "skycrane": "A rocket-powered descent stage hovers above the Martian surface, lowering a six-wheeled rover on three cables while its thrusters kick up swirling dust.",
}
STYLE = ("Rendered as a 1970s NASA concept painting: hand-painted gouache and "
         "acrylic on illustration board, airbrushed gradients, saturated "
         "magenta, violet and orange palette, crisp hard-edged hardware with "
         "brushy textured backgrounds, speckled starfields, visible brush "
         "strokes and slightly faded printed color.")

os.makedirs(OUT, exist_ok=True)
paths = []
for subject, content in SUBJECTS.items():
    for variant, prompt in (("trigger", f"{content} nsc7 style"),
                            ("attrs", f"{content} {STYLE}")):
        path = os.path.join(OUT, f"{subject}_{variant}.png")
        if not os.path.exists(path):
            result = bfl.run("flux-3-image-klein", {
                "prompt": prompt, "aspect_ratio": "16:9", "seed": SEED,
                "output_format": "png"}, poll_every=2.0)
            bfl.download(result["sample"], path)
        paths.append((f"{subject} / {variant}", path))

font = ImageFont.load_default(size=22)
sheet = Image.new("RGB", (2 * 800, len(SUBJECTS) * 480), "black")
draw = ImageDraw.Draw(sheet)
for i, (label, path) in enumerate(paths):
    im = Image.open(path)
    im.thumbnail((790, 445))
    x, y = (i % 2) * 800, (i // 2) * 480
    sheet.paste(im, (x, y))
    draw.text((x + 6, y + 450), label, fill="yellow", font=font)
sheet.save(os.path.join(OUT, "sheet.jpg"), quality=88)
print("sheet:", os.path.relpath(os.path.join(OUT, "sheet.jpg"), bfl.ROOT))
