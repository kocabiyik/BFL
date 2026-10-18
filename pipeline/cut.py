"""Cut the film: join the final clips in shot order with short crossfades,
burn in a few captions, add an end card and (optionally) one music track.

Usage:
    python pipeline/cut.py [--music music.mp3] [--drafts]

Reads out/video/<shot>.mp4 (or <shot>_draft.mp4 with --drafts), writes
out/film.mp4 (1080p H.264, 24 fps).
"""

import argparse
import os
import subprocess

from PIL import Image, ImageDraw, ImageFont

import bfl
from shots import SHOTS

VIDEO = os.path.join(bfl.ROOT, "out", "video")
FONT = "/System/Library/Fonts/Helvetica.ttc"
FADE = 0.5  # crossfade between shots, seconds
END_CARD = 3.0
# Captions burned in at the bottom left: shot id -> text.
CAPTIONS = {
    "01_mars": "Mars once had water. Was anything alive?",
    "02_liftoff": "July 30, 2020 · Cape Canaveral",
    "03_cruise": "7 months · 470 million km",
    "04_entry": "Entry · 19,500 km/h",
    "07_control": "February 18, 2021 · Touchdown confirmed",
}

parser = argparse.ArgumentParser()
parser.add_argument("--music")
parser.add_argument("--drafts", action="store_true")
args = parser.parse_args()


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", path], capture_output=True, text=True)
    return float(out.stdout)


def text_png(s, size, centered):
    """Full-frame transparent PNG with the caption (this ffmpeg has no drawtext)."""
    im = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)
    font = ImageFont.truetype(FONT, size)
    w, h = draw.textbbox((0, 0), s, font=font)[2:]
    x, y = ((1920 - w) // 2, (1080 - h) // 2) if centered else (80, 1080 - 110)
    draw.text((x + 2, y + 2), s, font=font, fill=(0, 0, 0, 150))
    draw.text((x, y), s, font=font, fill="white")
    path = os.path.join(bfl.ROOT, "out", "captions", f"{abs(hash(s))}.png")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.save(path)
    return path


inputs, chains, lengths = [], [], []
for i, shot in enumerate(SHOTS):
    path = os.path.join(VIDEO, f"{shot['id']}{'_draft' if args.drafts else ''}.mp4")
    inputs += ["-i", path]
    lengths.append(duration(path))
n = len(SHOTS)
# Caption PNGs are inputs after the clips; music (if any) comes last.
overlays = {shot["id"]: text_png(CAPTIONS[shot["id"]], 44, False)
            for shot in SHOTS if shot["id"] in CAPTIONS}
overlays["end"] = text_png("Dare Mighty Things", 84, True)
index = {}
for key, png in overlays.items():
    index[key] = n + len(index)
    inputs += ["-loop", "1", "-t", "5", "-i", png]

for i, shot in enumerate(SHOTS):
    f = f"[{i}:v]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,fps=24,format=yuv420p,setsar=1"
    if shot["id"] in index:
        chains.append(f"{f}[b{i}]")
        chains.append(f"[{index[shot['id']]}:v]format=rgba,fade=t=in:d=0.6:alpha=1,"
                      f"fade=t=out:st=4:d=0.6:alpha=1[c{i}]")
        chains.append(f"[b{i}][c{i}]overlay=shortest=0:eof_action=pass,format=yuv420p[v{i}]")
    else:
        chains.append(f"{f}[v{i}]")

# End card on black.
chains.append(f"color=black:s=1920x1080:r=24:d={END_CARD},format=yuv420p,setsar=1[eb]")
chains.append(f"[{index['end']}:v]format=rgba,fade=t=in:d=0.6:alpha=1[ec]")
chains.append(f"[eb][ec]overlay=shortest=1,format=yuv420p[v{n}]")
lengths.append(END_CARD)

# Crossfade chain.
prev, offset = "v0", 0.0
for i in range(1, n + 1):
    offset += lengths[i - 1] - FADE
    chains.append(f"[{prev}][v{i}]xfade=transition=fade:duration={FADE}:offset={offset:.3f}[x{i}]")
    prev = f"x{i}"
total = offset + lengths[n]
chains.append(f"[{prev}]fade=t=in:d=0.8,fade=t=out:st={total - 1:.3f}:d=1[vout]")

cmd = ["ffmpeg", "-y", *inputs]
maps = ["-map", "[vout]"]
if args.music:
    cmd += ["-i", args.music]
    chains.append(f"[{n + len(index)}:a]atrim=0:{total:.3f},afade=t=in:d=1,"
                  f"afade=t=out:st={total - 3:.3f}:d=3[aout]")
    maps += ["-map", "[aout]", "-c:a", "aac", "-b:a", "192k"]
out = os.path.join(bfl.ROOT, "out", "film.mp4")
cmd += ["-filter_complex", ";".join(chains), *maps, "-c:v", "libx264",
        "-preset", "medium", "-crf", "18", "-movflags", "+faststart", out]
subprocess.run(cmd, check=True)
print(f"saved out/film.mp4 ({total:.1f} s)")
