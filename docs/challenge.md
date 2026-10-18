# BFL challenge: teach FLUX 3 Image Klein a new style, then make a film with it

FLUX 3 Image Klein is our new open-weights image model. It has 5.6B parameters, does text to image and image editing, and runs on a single consumer GPU. Diffusers and AI Toolkit support it from day zero, so you can train a LoRA on it today.

The challenge: train a LoRA that gives Klein a style it can't do out of the box, generate keyframes with it, and turn those keyframes into a film of 45 seconds or more with the FLUX 3 video model. Then cut the film. An LLM can do the editing for you.

Training the LoRA is the easy part. Most of the work, and most of the difference between entries, is in finding and cleaning the images you train on.

*(Original PDF shows a collage here: "Images generated with FLUX 3 Image Klein".)*

## What you have

| | |
|---|---|
| FLUX 3 Image Klein base, non distilled model - train on this | [black-forest-labs/flux-3-image-klein-base](https://huggingface.co/black-forest-labs/flux-3-image-klein-base) |
| FLUX 3 Image Klein, step distilled model, faster generations | [black-forest-labs/flux-3-image-klein](https://huggingface.co/black-forest-labs/flux-3-image-klein) |
| Prompt upsampler | [black-forest-labs/flux-3-image-klein-pup](https://huggingface.co/black-forest-labs/flux-3-image-klein-pup), or any LLM with our [system prompts](https://huggingface.co/black-forest-labs/flux-3-image-klein-pup/blob/main/system_prompts.json) |
| Klein docs, with a full LoRA example | [docs.bfl.ai/flux_3/flux3_image_klein](https://docs.bfl.ai/flux_3/flux3_image_klein) |
| AI Toolkit, training with a GUI or CLI | [github.com/ostris/ai-toolkit](https://github.com/ostris/ai-toolkit) |
| Diffusers training script | [README_flux3_klein.md](https://github.com/huggingface/diffusers/blob/main/examples/dreambooth/README_flux3_klein.md) |
| FLUX 3 video, API | [docs.bfl.ai/flux_3/flux3_video](https://docs.bfl.ai/flux_3/flux3_video) |
| API key | [dashboard.bfl.ai](https://dashboard.bfl.ai/) |
| API credits | Hackathon credit code (see the original PDF; not committed to this public repo). Redeem it at https://dashboard.bfl.ai/redeem |

## 1. Pick a style Klein doesn't have

Describe the style by its attributes (palette, stroke, texture, materials), run that through the prompt upsampler, and generate it with Klein. If the base model already gets close, pick something else. Pixel art, for example, is already in the base model (it's on the docs page).

Directions that work well:

- Your own hand: 25 pages of your sketchbook or notebook, photographed flat in daylight. No model has seen them.
- Your company's illustration or photo style, if you own the assets. Train on the look and keep the logos out of the images.
- One public-domain artist or collection the model doesn't know by name. The LoRAs on our docs page use the 16th-century Shahnameh of Shah Tahmasp and Ivan Bilibin's folk-tale illustrations.
- NASA's 1970s space colony paintings: public domain, search "space colony" on [images.nasa.gov](https://images.nasa.gov/).
- A material or a process: cyanotypes, linocuts, embroidery, paper cutouts, risograph prints. Best if you made them.

Three style LoRAs from our docs, all trained on Klein Base:

- Persian miniature, `shtm style`
- Russian folk illustration, `bilb style`
- `ohwj style`

## 2. Build the dataset

| | |
|---|---|
| Images | 20 to 40. The LoRA on our docs page used 20 |
| Resolution | About 1 megapixel or more, any aspect ratio |
| Captions | One `.txt` per image with the same file name |
| Trigger | A made-up word plus "style", for example `zqvr style`, at the end of every caption |

*(Original PDF shows six of the 20 training images behind the Persian miniature LoRA: one source, a different scene in every image.)*

The images:

- The style is the only thing every image shares. Vary the subject, framing, setting and light. If half the images are portraits, the LoRA treats portraits as part of the style.
- Use one source. Two artists or two periods in one set average into a look that is neither.
- Anything that repeats across the set shows up in every output: text, signatures, watermarks, borders, page edges, a scan's color cast, the same background. Crop it out or drop the image. Text in training images comes back as fake lettering in your outputs.
- Drop duplicates, near-duplicates, collages and low-resolution images.
- Use images you have the rights to: your own work, public domain, or CC0. Good sources: [Wikimedia Commons](https://commons.wikimedia.org/), [Library of Congress free-to-use sets](https://www.loc.gov/free-to-use/), [NYPL Digital Collections](https://digitalcollections.nypl.org/) (filter to public domain), the [Rijksmuseum collection](https://www.rijksmuseum.nl/en/collection).

The captions:

- Describe what is in the image, never how it looks: subject, action, setting, composition, in two or three sentences, then the trigger. Because the captions never name the style, the LoRA learns it through the trigger.
- A caption from our Persian miniature LoRA:

  > A crowned ruler in a green robe sits on a throne inside an ornate tiled palace hall, attended by courtiers and guards while musicians sit in the foreground. In a narrow panel at the right, grooms and soldiers stand among horses and decorated elephants in a flowering landscape. shtm style

- Caption with a vision model (Qwen3-VL, Claude, Gemini, GPT), then search the captions for style words: painting, illustration, drawing, watercolor, ink, sketch, vintage, style. Vision models add them even when told not to. Rewrite those captions.

An agent can do most of this step: have it write the scraper, remove duplicates, build a contact sheet you review in one look, caption, and clean the captions.

## 3. Train on Klein Base

AI Toolkit: install from `main`, then pick **FLUX.3 Image Klein (base)** in the UI, or use `arch: flux3` in a config. This is the config from our docs, with fewer steps for a hackathon and a sample block so you can watch it learn:

```yaml
job: extension
config:
  name: klein-style-lora
  process:
    - type: diffusion_trainer
      training_folder: output
      device: cuda:0
      network:
        type: lora
        linear: 32
        linear_alpha: 32
      save:
        dtype: bf16
        save_every: 250
      datasets:
        - folder_path: data/my_style           # images + .txt captions ending in "zqvr style"
          caption_ext: txt
          resolution: [1024]
      train:
        batch_size: 1
        steps: 2000
        lr: 1e-4
        optimizer: adamw
        dtype: bf16
      model:
        name_or_path: black-forest-labs/flux-3-image-klein-base
        arch: flux3
      sample:
        sample_every: 250
        width: 1024
        height: 1024
        guidance_scale: 3.5                    # Klein Base settings
        sample_steps: 50
        prompts:                               # subjects that are NOT in your dataset
          - "A lighthouse on a rocky cliff above a stormy sea at night. zqvr style"
          - "A woman cycling through a city street in the rain. zqvr style"
          - "A cat asleep on a windowsill next to a potted plant. zqvr style"
```

Diffusers: `train_dreambooth_lora_flux3_klein.py` with the same settings (rank 32, learning rate 1e-4, 2000 steps). It reads per-image captions from a dataset through `--dataset_name` and `--caption_column`. See the [README](https://github.com/huggingface/diffusers/blob/main/examples/dreambooth/README_flux3_klein.md).

Our 4000-step run took about 4.5 hours on one GPU, so 2000 steps takes a bit over 2 hours. The comparisons on our docs page use the checkpoint from step 1500.

Pick the checkpoint by looking at the samples:

- Early checkpoints apply the style weakly.
- Late checkpoints start copying the training set: the same compositions and figures, repeated artifacts, and the new subjects in your test prompts stop working. Take the last checkpoint before that happens.
- The loss keeps going down after the images get worse. Don't use it to pick.

*(Original PDF shows two pairs, same prompt and seed: Klein Base on the left, the Persian miniature LoRA at step 1500 on the right — a fox and crow under a full moon, and a sailing ship in a storm.)*

## 4. Generate the keyframes

Train on Base, generate on Klein (distilled). The LoRA loads into it as is.

| Setting | Value |
|---|---|
| Steps | 16 |
| Guidance (CFG) | 1 |
| LoRA scale | 0.75 (0.5 to 1.0) |

```python
import torch
from diffusers import ModularPipeline

pipe = ModularPipeline.from_pretrained("black-forest-labs/flux-3-image-klein")
pipe.load_components(dtype=torch.bfloat16)
pipe.to("cuda")

pipe.load_lora_weights("output/klein-style-lora/klein-style-lora_000001500.safetensors", adapter_name="style")
pipe.set_adapters("style", 0.75)

image = pipe(
    prompt=(
        "A lighthouse keeper climbs the spiral stairs of a tall lighthouse at dusk, carrying a lantern. "
        "Through the window behind him, waves break against the rocks below. zqvr style"
    ),
    output="images",
)[0]
image.save("shot1_start.png")
```

- Write prompts the way you wrote the captions: two or three sentences of content, then the trigger. The LoRA examples on our docs page are prompted this way.
- For more detail, run the request through the upsampler, then delete its opening medium phrase and end the caption with your trigger. With no style in the request, the upsampler opens with a photograph ("Full-color outdoor photograph, ..."), which works against your LoRA.
- Generate keyframes in your film's aspect ratio.
- For consistent characters, generate one hero frame and make the other keyframes from it with Klein's image editing: pass it as `image=` and run the change (new pose, new angle, later in the day) through the upsampler together with the frame. A one-line instruction sent as typed reframes the whole shot. Regenerating from text gives you a different character every time. Klein keeps its quality across chained edits.

*(Original PDF shows one image, three chained edits: an empty room, then a sofa, a sleeping cat, evening lamplight.)*

## 5. Make it move

The video model never sees your LoRA. Your style reaches the film through the frames you give it.

The simplest way in is a start frame: one image from your LoRA becomes the exact first frame of the clip, and the prompt says what happens next. Three LoRA frames from this page, each used as the start frame of a 10-second clip (videos embedded in the original PDF):

- `persian_miniature_fox_crow.mp4` — Persian miniature LoRA
- `persian_miniature_ship.mp4` — Persian miniature LoRA
- `folk_illustration_knight.mp4` — Russian folk illustration LoRA

Tips:

- 45 seconds is 4 to 6 shots of 8 to 12 seconds. One clip is 5 to 20 seconds.
- Pin an end frame too when a shot has to land somewhere, for example on the start frame of your next shot: `"keyframes": [[0, start], [10, end]]`. You can pin up to 10 frames per clip, each at a timestamp.
- Name the medium in the video prompt and say that it holds. The Persian miniature clips above use: "The image never turns into realism or 3D; it stays a flat hand-painted Persian miniature the whole time."
- Iterate in draft: `"draft": true` costs about a third of a full render and comes back faster. Render the take you keep at full quality with `"mode": "draft_enhance"`, which reproduces that exact take.
- To make a shot longer than 20 seconds, continue it with `"mode": "v2v"` and the clip as `start_video` (5 to 15 more seconds).

Four keyframes pinned at 0:00, 0:03, 0:07 and 0:10, and the clip FLUX 3 generated between them: <https://cdn.sanity.io/files/2gpum2i6/production/afc86a790f1a835db3cff62e58dd658c3d47fc59.mp4>

```bash
curl -s -X POST https://api.bfl.ai/v1/flux-3-video \
  -H "x-key: $BFL_API_KEY" -H "Content-Type: application/json" \
  -d '{
    "mode": "i2v",
    "prompt": "the keeper reaches the top of the stairs and lifts the lantern to the window, the beam sweeping out over the sea",
    "keyframes": "https://example.com/shot1_start.png",
    "duration": 10,
    "aspect_ratio": "16:9",
    "draft": true
  }'
```

Poll the `polling_url` in the response until `status` is `Ready`.

Audio is on by default and each clip gets its own, so the sound changes at every cut. Either describe the same sound in every prompt, or set `"generate_audio": false` and put one track under the whole film in the edit.

Stylized looks hold in motion. Three text-to-video clips from our video docs:

- [Black-and-white cartoon](https://cdn.sanity.io/files/2gpum2i6/production/95a79d0f1046a3b74aecd78c94ccdcba8d5bdfc5.mp4)
- [1980s cel anime](https://cdn.sanity.io/files/2gpum2i6/production/3471a6e0c6bdcf5d8cd27d76eee5412d832ab373.mp4)
- [Low-poly 3D](https://cdn.sanity.io/files/2gpum2i6/production/aaf25c1cee9bec53385a281eecd983e60efad549.mp4)

## 6. Cut it

Download the clips and give them to an LLM with your shot list. Ask for the ffmpeg command that trims, orders, crossfades and adds the audio, for example: "Here are 6 clips and my shot list. Trim each clip to the part that matches the list, join them in order with short crossfades, put `music.mp3` under the whole film, export 1080p H.264."

To change one shot without regenerating it, use [FLUX Video Edit](https://docs.bfl.ai/flux_tools/flux_video_edit): send the clip (up to 15 seconds) and say what should be different. Everything the prompt doesn't mention stays as shot: length, framing, camera, timing and audio. Six edits of the same ten-second clip from our docs:

- [Source clip](https://cdn.sanity.io/files/2gpum2i6/production/f1654af36e7694775939b1aa8a2bb0419ff819ea.mp4)
- ["Remove the orange bucket."](https://cdn.sanity.io/files/2gpum2i6/production/c447e0d2a8b0a516f98e657bf3153b2c6f774a4d.mp4)
- ["Make it snow, with flakes settling on the crate and the fish."](https://cdn.sanity.io/files/2gpum2i6/production/6746b8b4f2b0ca345b63b5d6a9047761a1982b72.mp4)
- ["A gull swoops down and steals a fish from the crate."](https://cdn.sanity.io/files/2gpum2i6/production/257c4060dccce2469356550bc98ee6e5275ac0a8.mp4)
- ["Replace the harbour behind him with a Mediterranean harbour at midday, bright sun and white buildings."](https://cdn.sanity.io/files/2gpum2i6/production/2431d7fcecd4d2acfc109d32d37979cb5124ed2c.mp4)
- ["Make the whole clip a hand-drawn watercolour animation."](https://cdn.sanity.io/files/2gpum2i6/production/690b1eeae99db89b8ad2aecb2f849f21573c1f4b.mp4)
- ["Say the same sentence entirely in German, with no English words."](https://cdn.sanity.io/files/2gpum2i6/production/46467ec2395c7d1e0d9fc2e4e557aed9d194d067.mp4)

```bash
curl -s -X POST https://api.bfl.ai/v1/flux-tools/video-edit-v1 \
  -H "x-key: $BFL_API_KEY" -H "Content-Type: application/json" \
  -d '{
    "video": "https://example.com/shot3.mp4",
    "prompt": "Make it snow, with flakes settling on the crate and the fish."
  }'
```

## Submit

- The film, 45 seconds or more
- The LoRA, as a Hugging Face link
- 6 of your training images, and one base vs. LoRA pair with the same prompt and seed
- Three lines: the style, where the data came from, which checkpoint you picked

## What we look for

- A style Klein can't do without your LoRA. The base vs. LoRA pair shows it.
- The style holds for the whole film, beyond the first frame.
- The film tells something from start to end: a story, a product moment, a music video.
- The dataset: clean, consistent, well captioned.
