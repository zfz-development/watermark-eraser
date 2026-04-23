# GPU Watermark Removal Service - Docker Deployment

## Quick Start

1. Copy model files to models/ directory:
   - models/sd-inpainting/ - SD 1.5 Inpainting model (safetensors only, exclude .ckpt)
   - models/big-lama/ - BigLama model (optional)
   - models/mat/ - MAT model (optional)

2. Build and run:
   `ash
   docker compose build
   docker compose up -d
   `

3. Verify:
   `ash
   curl http://localhost:8900/health
   `

## Model Preparation

### From existing GPU server (192.168.96.181):
`ash
# Copy safetensors only (exclude .ckpt ~4GB)
rsync -avz --exclude='*.ckpt' --exclude='.cache' --exclude='__pycache__' \
  zfz@192.168.96.181:/home/zfz/watermark-service/models/ ./models/
`

Or manually:
- models/sd-inpainting/ - Copy everything EXCEPT sd-v1-5-inpainting.ckpt and .cache/
- models/big-lama/ - Copy the model directory
- models/mat/ - Copy the model directory

## Prerequisites on new server
- NVIDIA driver (525+)
- Docker Engine (20.10+)
- NVIDIA Container Toolkit (
vidia-container-toolkit)
- CUDA 12.x compatible GPU (8GB+ VRAM)

## API Endpoints
- POST /inpaint - Image watermark removal
- POST /inpaint_video - Video watermark removal
- GET /health - Health check
