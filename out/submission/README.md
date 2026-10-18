# Perseverance — nsc7 style

**Style:** 1970s NASA Ames space art by Rick Guidice (one artist): hand-painted gouache/acrylic, airbrushed gradients, saturated violet, magenta and orange, crisp hard-edged hardware against brushy skies. Trigger `nsc7 style`.

**Data:** 22 public-domain paintings from images.nasa.gov (NASA Ames, 1972–1978), all credited to Rick Guidice in their NASA metadata. Mats cropped, signatures removed with FLUX Erase, content-only captions.

**Checkpoint:** step 1000 of 2000 (rank 32, lr 1e-4, Klein Base on one RTX PRO 6000 on Nebius). Picked from the 250-step samples: full style by 1000; by 1250 subjects started drifting toward the training compositions.

**LoRA:** https://huggingface.co/kocabiyik/nsc7-style-lora

- `training_images/`: 6 of the 22 training images
- `base_vs_lora/`: Klein Base vs. the LoRA, same prompt and seed (1975)
