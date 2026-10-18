"""Generate the film's keyframes with FLUX 3 Image Klein (distilled) and the
nsc7 style LoRA. Runs on the GPU box, in its own venv (diffusers from main).

Usage:
    python pipeline/keyframes.py --lora nsc7-style-lora_000001500.safetensors
    python pipeline/keyframes.py --lora ... --only 08_rover 06_skycrane
    python pipeline/keyframes.py --base            # no LoRA, for comparison

Text keyframes use the shot prompt as written (content only, like the
training captions) plus the trigger. Edit keyframes (rover consistency) run
the instruction and the reference frame through the prompt upsampler, drop
its opening medium sentence, and end the caption with the trigger.

Writes out/keyframes/<shot>_start.png, <shot>_end.png and prompts.json.
"""

import argparse
import json
import os
import re

import torch
from diffusers import ModularPipeline
from PIL import Image

from shots import SHOTS, TRIGGER

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Distilled: 16 steps, no guidance. Base (what the LoRA was trained on) is
# the fallback while distilled access is pending: 50 steps, guidance 3.5.
MODELS = {"distilled": ("black-forest-labs/flux-3-image-klein", {}),
          "base": ("black-forest-labs/flux-3-image-klein-base",
                   {"num_inference_steps": 50})}  # guider default: CFG 3.5
PUP = "black-forest-labs/flux-3-image-klein-pup"
WIDTH, HEIGHT = 1536, 864  # 16:9, ~1.3 MP, multiples of 16
# First sentence of an upsampled caption that names a medium, not content.
MEDIUM = re.compile(r"photograph|painting|illustration|render|artwork|gouache|"
                    r"acrylic|airbrush|drawing|image|style|depiction", re.I)

parser = argparse.ArgumentParser()
parser.add_argument("--lora", help="LoRA .safetensors from training")
parser.add_argument("--scale", type=float, default=0.75)
parser.add_argument("--base", action="store_true", help="no LoRA")
parser.add_argument("--model", choices=MODELS, default="distilled")
parser.add_argument("--seed", type=int, default=1975)
parser.add_argument("--only", nargs="*", help="shot ids to (re)generate")
parser.add_argument("--out", default=os.path.join(ROOT, "out", "keyframes"))
args = parser.parse_args()
if not args.base and not args.lora:
    parser.error("--lora or --base")

repo, SAMPLING = MODELS[args.model]
pipe = ModularPipeline.from_pretrained(repo)
pipe.load_components(dtype=torch.bfloat16)
pipe.to("cuda")
if not args.base:
    pipe.load_lora_weights(args.lora, adapter_name="style")
    pipe.set_adapters("style", args.scale)

_pup = None


def upsample_edit(instruction, image):
    """Reference + instruction -> full caption, via the Klein prompt upsampler."""
    global _pup
    if _pup is None:
        from huggingface_hub import hf_hub_download
        from transformers import AutoProcessor, Qwen3_5ForConditionalGeneration
        processor = AutoProcessor.from_pretrained(PUP)
        model = Qwen3_5ForConditionalGeneration.from_pretrained(
            PUP, dtype=torch.bfloat16, device_map="auto").eval()
        system = json.load(open(hf_hub_download(PUP, "system_prompts.json")))["i2i"]
        _pup = processor, model, system
    processor, model, system = _pup
    text = ("Reference images follow in order (the first image, the second image, ...).\n"
            f"User request: {instruction}\nOutput the caption.")
    messages = [{"role": "system", "content": system},
                {"role": "user", "content": [{"type": "image", "image": image},
                                             {"type": "text", "text": text}]}]
    inputs = processor.apply_chat_template(
        messages, add_generation_prompt=True, tokenize=True, return_dict=True,
        return_tensors="pt", enable_thinking=False).to(model.device)
    with torch.no_grad():
        out = model.generate(**inputs, max_new_tokens=3584, do_sample=False)
    caption = processor.decode(out[0, inputs["input_ids"].shape[1]:],
                               skip_special_tokens=True).strip()
    first, _, rest = caption.partition(". ")
    return rest if rest and MEDIUM.search(first) else caption


def generate(spec, frames):
    """One keyframe from a shot's "key" or "end" spec; returns (image, prompt)."""
    generator = torch.Generator().manual_seed(args.seed)
    if "prompt" in spec:
        prompt = f"{spec['prompt']} {TRIGGER}"
        image = pipe(prompt=prompt, width=WIDTH, height=HEIGHT,
                     generator=generator, output="images", **SAMPLING)[0]
    else:
        ref = frames[spec["edit_of"]]
        prompt = f"{upsample_edit(spec['edit'], ref)} {TRIGGER}"
        image = pipe(prompt=prompt, image=ref, width=WIDTH, height=HEIGHT,
                     generator=generator, output="images", **SAMPLING)[0]
    return image, prompt


os.makedirs(args.out, exist_ok=True)
log_path = os.path.join(args.out, "prompts.json")
log = json.load(open(log_path)) if os.path.exists(log_path) else {}
# Text keyframes first: edits reference them (06_skycrane edits 08_rover).
order = sorted(SHOTS, key=lambda s: "edit_of" in s["key"])
frames = {}
for shot in order:
    for part in ("key", "end"):
        spec = shot.get(part)
        if not spec:
            continue
        name = f"{shot['id']}_{'start' if part == 'key' else 'end'}"
        path = os.path.join(args.out, f"{name}.png")
        if args.only and shot["id"] not in args.only and os.path.exists(path):
            if part == "key":
                frames[shot["id"]] = Image.open(path).convert("RGB")
            continue
        image, prompt = generate(spec, frames)
        image.save(path)
        if part == "key":
            frames[shot["id"]] = image
        log[name] = {"prompt": prompt, "seed": args.seed, "model": args.model,
                     "lora": None if args.base else os.path.basename(args.lora),
                     "scale": None if args.base else args.scale}
        json.dump(log, open(log_path, "w"), indent=1)
        print("saved", os.path.relpath(path, ROOT), flush=True)
