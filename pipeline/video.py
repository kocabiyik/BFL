"""Turn the keyframes into clips with the FLUX 3 video API.

Usage:
    python pipeline/video.py                    # draft every shot (hd, fast)
    python pipeline/video.py --only 06_skycrane # redo one draft
    python pipeline/video.py --final            # draft_enhance the kept drafts (fhd)
    python pipeline/video.py --v2 [--final]     # v2 shot list, out/v2/, with audio

Reads out/keyframes/<shot>_start.png (+ _end.png), writes
out/video/<shot>_draft.mp4 + <shot>_draft.json (the draft_cache), then
out/video/<shot>.mp4 with --final. Shots run in parallel. No audio: one
music track goes under the whole film in the cut. v2 keeps each clip's
generated sound (rumble, roar, chute snap) and mixes it in the cut.
"""

import argparse
import json
import os
from concurrent.futures import ThreadPoolExecutor

import bfl

parser = argparse.ArgumentParser()
parser.add_argument("--only", nargs="*", help="shot ids")
parser.add_argument("--final", action="store_true", help="draft_enhance to fhd")
parser.add_argument("--v2", action="store_true", help="shots_v2, with audio")
args = parser.parse_args()
if args.v2:
    from shots_v2 import HOLD, SHOTS
else:
    from shots import HOLD, SHOTS

BASE = os.path.join(bfl.ROOT, "out", *(["v2"] if args.v2 else []))
KEYS = os.path.join(BASE, "keyframes")
OUT = os.path.join(BASE, "video")


def draft(shot):
    start = bfl.b64(os.path.join(KEYS, f"{shot['id']}_start.png"))
    end = os.path.join(KEYS, f"{shot['id']}_end.png")
    keyframes = ([[0, start], [shot["duration"], bfl.b64(end)]]
                 if os.path.exists(end) else start)
    result = bfl.run("flux-3-video", {
        "mode": "i2v", "prompt": f"{shot['motion']} {HOLD}",
        "keyframes": keyframes, "duration": shot["duration"],
        "aspect_ratio": "16:9", "generate_audio": args.v2, "draft": True,
    }, poll_every=5.0)
    with open(os.path.join(OUT, f"{shot['id']}_draft.json"), "w") as f:
        json.dump(result, f)
    bfl.download(result["sample"], os.path.join(OUT, f"{shot['id']}_draft.mp4"))


def final(shot):
    with open(os.path.join(OUT, f"{shot['id']}_draft.json")) as f:
        cache = json.load(f)["draft_cache"]
    # The cache carries the prompt and audio setting; the API rejects them here.
    result = bfl.run("flux-3-video", {
        "mode": "draft_enhance", "draft_cache": cache, "resolution": "fhd",
    }, poll_every=5.0)
    bfl.download(result["sample"], os.path.join(OUT, f"{shot['id']}.mp4"))


os.makedirs(OUT, exist_ok=True)
shots = [s for s in SHOTS if not args.only or s["id"] in args.only]
# The API allows 8 active tasks per endpoint.
with ThreadPoolExecutor(min(len(shots), 8)) as pool:
    for future in [pool.submit(final if args.final else draft, s) for s in shots]:
        future.result()
