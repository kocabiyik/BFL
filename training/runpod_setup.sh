#!/usr/bin/env bash
# Train the nsc7 style LoRA on a rented CUDA GPU (RunPod / Lambda, 24 GB+ VRAM,
# e.g. RTX 4090, L40S or A100). Ubuntu image with Python 3.10+ and CUDA 12.x.
#
# 1. From the Mac, copy the dataset and config to the pod:
#      rsync -av data/space_colony/train training/nsc7_lora.yaml \
#            training/runpod_setup.sh root@<pod>:/workspace/nsc7/ -e "ssh -p <port>"
# 2. On the pod:
#      export HF_TOKEN=hf_...      # accept the Klein Base license on HF first
#      bash /workspace/nsc7/runpod_setup.sh
# 3. Watch samples in /workspace/ai-toolkit/output/nsc7-style-lora/samples/
#    (every 250 steps). ~2-3 h for 2000 steps.
set -euo pipefail

WORK=/workspace
cd "$WORK"

if [ ! -d ai-toolkit ]; then
  git clone https://github.com/ostris/ai-toolkit.git   # main: has arch flux3
  cd ai-toolkit
  git submodule update --init --recursive
  python3 -m venv venv
  source venv/bin/activate
  pip install --upgrade pip
  pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124
  pip install -r requirements.txt
else
  cd ai-toolkit
  source venv/bin/activate
fi

: "${HF_TOKEN:?export HF_TOKEN first (Klein Base download)}"
huggingface-cli login --token "$HF_TOKEN"

mkdir -p data/space_colony config
rsync -a "$WORK/nsc7/train/" data/space_colony/train/
cp "$WORK/nsc7/nsc7_lora.yaml" config/
echo "dataset: $(ls data/space_colony/train/*.jpg | wc -l) images"

python run.py config/nsc7_lora.yaml

# After picking a checkpoint (e.g. step 1500), publish it:
#   huggingface-cli upload <user>/nsc7-style-lora \
#     output/nsc7-style-lora/nsc7-style-lora_000001500.safetensors
