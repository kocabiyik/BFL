"""Cut v2 of the film: the 18 shots of shots_v2.py, built for action.

Usage:
    python pipeline/cut_v2.py [--music music.mp3] [--drafts]
    python pipeline/cut_v2.py --use-draft 4a_entry   # keep a draft over its fhd
    python pipeline/cut_v2.py --no-captions          # HUD and end card only

Hard cuts inside each docs/clips.md clip, short crossfades between clips. Shots
with "shake" get a camera shake (scale up a little, then a jittering crop).
Each clip keeps its generated sound; clip 4 gets the 7-minutes-of-terror HUD
(countdown, speed, altitude). An optional music track goes under the mix.

Reads out/v2/video/<shot>.mp4 (or <shot>_draft.mp4 with --drafts, for shots
in --use-draft, or when the fhd clip is missing), writes
out/v2/film.mp4 (1080p H.264, 24 fps, AAC).
"""

import argparse
import os
import subprocess
from itertools import groupby

from PIL import Image, ImageDraw, ImageFont

import bfl
from shots_v2 import SHOTS

V2 = os.path.join(bfl.ROOT, "out", "v2")
VIDEO = os.path.join(V2, "video")
FONT = "/System/Library/Fonts/Helvetica.ttc"
MONO = "/System/Library/Fonts/Menlo.ttc"
W, H = 1920, 1080
FADE = 0.4      # crossfade between clips, seconds
END_CARD = 3.0
# Shake strength -> max offset in px. The frame is scaled up by twice this
# first, so the crop never shows an edge.
SHAKE_PX = {1: 8, 2: 18, 3: 32}
# Clip 4 HUD: (seconds into clip 4, altitude m, speed km/h), from the fact
# sheet in docs/clips.md. Touchdown lands ~7 s into 4e (28 + 7 = 35 s).
HUD_POINTS = [(0, 125000, 19500), (8, 11000, 1500), (15, 8000, 600),
              (21, 2100, 300), (28, 20, 2.7), (35, 0, 2.7), (36, 0, 0)]
TOUCHDOWN = 35.0
HUD_FPS = 8

parser = argparse.ArgumentParser()
parser.add_argument("--music")
parser.add_argument("--drafts", action="store_true")
parser.add_argument("--use-draft", nargs="*", default=[], help="shot ids")
parser.add_argument("--no-captions", action="store_true")
args = parser.parse_args()


def probe(path):
    """(duration, has_audio) of a clip."""
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                          "format=duration:stream=codec_type", "-of", "csv=p=0", path],
                         capture_output=True, text=True).stdout.split()
    return float(next(x for x in out if x[0].isdigit())), "audio" in out


def text_png(s, size, centered):
    """Full-frame transparent PNG with the caption (this ffmpeg has no drawtext)."""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)
    font = ImageFont.truetype(FONT, size)
    w, h = draw.textbbox((0, 0), s, font=font)[2:]
    x, y = ((W - w) // 2, (H - h) // 2) if centered else (80, H - 110)
    draw.text((x + 2, y + 2), s, font=font, fill=(0, 0, 0, 150))
    draw.text((x, y), s, font=font, fill="white")
    path = os.path.join(V2, "captions", f"{abs(hash(s))}.png")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.save(path)
    return path


def hud_frames(length):
    """PNG sequence for the clip 4 HUD; returns the ffmpeg input pattern."""
    folder = os.path.join(V2, "hud")
    os.makedirs(folder, exist_ok=True)
    font = ImageFont.truetype(MONO, 34)
    big = ImageFont.truetype(MONO, 64)
    for n in range(int(length * HUD_FPS) + 1):
        t = n / HUD_FPS
        i = max(k for k, p in enumerate(HUD_POINTS) if p[0] <= t or k == 0)
        (t0, a0, s0), (t1, a1, s1) = HUD_POINTS[i], HUD_POINTS[min(i + 1, len(HUD_POINTS) - 1)]
        f = min(1.0, (t - t0) / (t1 - t0)) if t1 > t0 else 1.0
        alt, speed = a0 + (a1 - a0) * f, s0 + (s1 - s0) * f
        left = max(0.0, 420 * (1 - t / TOUCHDOWN))  # 7:00 -> 0:00 at touchdown
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        draw = ImageDraw.Draw(im)
        color = (255, 90, 60) if left < 60 else (255, 255, 255)
        lines = [(f"T-{int(left) // 60}:{int(left) % 60:02d}", big, color),
                 (f"ALT {alt / 1000:7.1f} km" if alt >= 1000 else f"ALT {alt:7.0f} m", font, "white"),
                 (f"SPD {speed:7.0f} km/h", font, "white")]
        y = 60
        for s, fnt, fill in lines:
            w = draw.textbbox((0, 0), s, font=fnt)[2]
            draw.text((W - 80 - w + 2, y + 2), s, font=fnt, fill=(0, 0, 0, 150))
            draw.text((W - 80 - w, y), s, font=fnt, fill=fill)
            y += draw.textbbox((0, 0), s, font=fnt)[3] + 14
        im.save(os.path.join(folder, f"{n:04d}.png"))
    return os.path.join(folder, "%04d.png")


inputs, chains = [], []


def add_input(*opts):
    inputs.extend(opts)
    return len([x for x in inputs if x == "-i"]) - 1


lengths = {}
for shot in SHOTS:
    path = os.path.join(VIDEO, f"{shot['id']}.mp4")
    if args.drafts or shot["id"] in args.use_draft or not os.path.exists(path):
        if not args.drafts and shot["id"] not in args.use_draft:
            print(f"{shot['id']}: no fhd clip, using the draft")
        path = os.path.join(VIDEO, f"{shot['id']}_draft.mp4")
    i = add_input("-i", path)
    length, has_audio = probe(path)
    lengths[shot["id"]] = length
    sid = shot["id"]

    v = f"[{i}:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps=24"
    px = SHAKE_PX.get(shot["shake"])
    if px:
        py = round(px * H / W)
        # Two detuned sines per axis: irregular, never more than px off centre.
        v += (f",scale={W + 2 * px}:{H + 2 * py},crop={W}:{H}:"
              f"'{px}+{px}*(0.6*sin(31*t)+0.4*sin(57*t+1.3))':"
              f"'{py}+{py}*(0.6*sin(37*t+0.7)+0.4*sin(61*t+2.1))'")
    v += ",setsar=1,format=yuv420p"
    if shot.get("caption") and not args.no_captions:
        c = add_input("-loop", "1", "-t", f"{min(length, 5):.3f}", "-i", text_png(shot["caption"], 44, False))
        chains.append(f"{v}[b_{sid}]")
        chains.append(f"[{c}:v]format=rgba,fade=t=in:d=0.4:alpha=1,"
                      f"fade=t=out:st={min(length, 5) - 0.5:.3f}:d=0.5:alpha=1[c_{sid}]")
        chains.append(f"[b_{sid}][c_{sid}]overlay=eof_action=pass,format=yuv420p[v_{sid}]")
    else:
        chains.append(f"{v}[v_{sid}]")

    a = (f"[{i}:a]" if has_audio else
         f"anullsrc=r=48000:cl=stereo,atrim=0:{length:.3f}[n_{sid}];[n_{sid}]")
    a += f"aresample=48000,aformat=channel_layouts=stereo,apad,atrim=0:{length:.3f}"
    if sid == "4e_skycrane":  # the rockets die out: silence before mission control
        a += f",afade=t=out:st={length - 1.5:.3f}:d=1"
    chains.append(f"{a},asetpts=N/SR/TB[a_{sid}]")

# Hard cuts inside a clip.
clips = []
for k, group in groupby(SHOTS, key=lambda s: s["clip"]):
    group = list(group)
    pairs = "".join(f"[v_{s['id']}][a_{s['id']}]" for s in group)
    chains.append(f"{pairs}concat=n={len(group)}:v=1:a=1[cv{k}][ca{k}]")
    clips.append((k, sum(lengths[s["id"]] for s in group)))

# HUD over clip 4.
clip4 = dict(clips)[4]
hud = add_input("-framerate", str(HUD_FPS), "-i", hud_frames(clip4))
chains.append(f"[{hud}:v]format=rgba,fps=24[hud]")
chains.append("[cv4][hud]overlay=eof_action=pass,format=yuv420p[cv4h]")
video_label = {k: f"cv{k}" for k, _ in clips} | {4: "cv4h"}

# End card on black, silent.
end = add_input("-loop", "1", "-t", str(END_CARD), "-i", text_png("Dare Mighty Things", 84, True))
chains.append(f"color=black:s={W}x{H}:r=24:d={END_CARD},format=yuv420p,setsar=1[eb]")
chains.append(f"[{end}:v]format=rgba,fade=t=in:d=0.6:alpha=1[ec]")
chains.append("[eb][ec]overlay=shortest=1,format=yuv420p[cvend]")
chains.append(f"anullsrc=r=48000:cl=stereo,atrim=0:{END_CARD}[caend]")
segments = [(video_label[k], f"ca{k}", length) for k, length in clips]
segments.append(("cvend", "caend", END_CARD))
# xfade needs one frame rate and timebase on both sides.
for label, _, _ in segments:
    chains.append(f"[{label}]fps=24,settb=1/24[{label}n]")
segments = [(f"{v}n", a, length) for v, a, length in segments]

# Crossfades between clips.
(pv, pa, length), offset = segments[0], 0.0
for n, (sv, sa, slen) in enumerate(segments[1:], 1):
    offset += length - FADE
    chains.append(f"[{pv}][{sv}]xfade=transition=fade:duration={FADE}:offset={offset:.3f}[xv{n}]")
    chains.append(f"[{pa}][{sa}]acrossfade=d={FADE}[xa{n}]")
    pv, pa, length = f"xv{n}", f"xa{n}", slen
total = offset + length
chains.append(f"[{pv}]fade=t=in:d=0.8,fade=t=out:st={total - 1:.3f}:d=1[vout]")
mix = f"[{pa}]"
if args.music:
    m = add_input("-i", args.music)
    chains.append(f"[{m}:a]aresample=48000,aformat=channel_layouts=stereo,"
                  f"atrim=0:{total:.3f},volume=0.35[mus]")
    chains.append(f"{mix}[mus]amix=inputs=2:normalize=0:duration=first[mixed]")
    mix = "[mixed]"
chains.append(f"{mix}loudnorm=I=-16:TP=-1.5:LRA=11,"
              f"afade=t=in:d=0.5,afade=t=out:st={total - 2:.3f}:d=2[aout]")

out = os.path.join(V2, "film.mp4")
cmd = ["ffmpeg", "-y", *inputs, "-filter_complex", ";".join(chains),
       "-map", "[vout]", "-map", "[aout]", "-c:v", "libx264", "-preset", "medium",
       "-crf", "18", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
       "-movflags", "+faststart", out]
subprocess.run(cmd, check=True)
print(f"saved out/v2/film.mp4 ({total:.1f} s)")
