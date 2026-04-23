import os, io, json, time, asyncio, logging, uuid, copy
import cv2
import numpy as np
from PIL import Image
import torch
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse
from concurrent.futures import ThreadPoolExecutor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Watermark Removal Service - Multi Model")
executor = ThreadPoolExecutor(max_workers=2)

OUTPUT_DIR = "/home/zfz/watermark-service/output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

_sd15_pipe = None
_lama_model = None
_mat_model = None
_easyocr_reader = None

def get_easyocr():
    global _easyocr_reader
    if _easyocr_reader is not None:
        return _easyocr_reader
    logger.info("Loading EasyOCR...")
    import easyocr
    _easyocr_reader = easyocr.Reader(["ch_sim", "en"], gpu=False, verbose=False)
    logger.info("EasyOCR loaded!")
    return _easyocr_reader

def get_sd15():
    global _sd15_pipe
    if _sd15_pipe is not None:
        return _sd15_pipe
    logger.info("Loading SD 1.5 Inpainting...")
    from diffusers import AutoPipelineForInpainting
    _sd15_pipe = AutoPipelineForInpainting.from_pretrained(
        "/home/zfz/watermark-service/models/sd-inpainting",
        torch_dtype=torch.float16,
        use_safetensors=True,
        safety_checker=None,
    ).to("cuda")
    _sd15_pipe.enable_attention_slicing()
    logger.info("SD 1.5 loaded!")
    return _sd15_pipe

def get_lama():
    global _lama_model
    if _lama_model is not None:
        return _lama_model
    logger.info("Loading LaMA model (torch.jit)...")
    _lama_model = torch.jit.load("/home/zfz/watermark-service/models/big-lama/big-lama.pt", map_location="cuda").eval()
    logger.info("LaMA loaded!")
    return _lama_model

def get_mat():
    global _mat_model
    if _mat_model is not None:
        return _mat_model
    logger.info("Loading MAT model...")
    import sys
    os.environ['TORCH_CUDA_ARCH_LIST'] = '6.0'
    sys.path.insert(0, '/home/zfz/watermark-service/MAT')
    from networks.mat import Generator
    from safetensors.torch import load_file
    device = torch.device("cuda")
    G = Generator(z_dim=512, c_dim=0, w_dim=512, img_resolution=512, img_channels=3).to(device).eval()
    st = load_file("/home/zfz/watermark-service/models/mat/MAT_Places_512_fp16.safetensors")
    state_dict = {k: v.float() for k, v in st.items()}
    missing, _ = G.load_state_dict(state_dict, strict=False)
    if missing:
        logger.warning("MAT missing %d keys (noise params - expected)", len(missing))
    _mat_model = G
    logger.info("MAT loaded!")
    return _mat_model

def _detect_text_easyocr(img_bgr, conf_threshold=0.25):
    """Detect text using EasyOCR. Returns list of (x1,y1,x2,y2,text,conf)."""
    try:
        reader = get_easyocr()
        results = reader.readtext(img_bgr)
        boxes = []
        for (bbox, text, conf) in results:
            if conf > conf_threshold:
                xs = [p[0] for p in bbox]
                ys = [p[1] for p in bbox]
                boxes.append((int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys)), text, conf))
                logger.info("EasyOCR: '%s' (%.2f) at (%d,%d)-(%d,%d)", text, conf,
                           int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys)))
        return boxes
    except Exception as e:
        logger.warning("EasyOCR failed: %s", e)
        return []

def build_mask(img, mask_data=None):
    h, w = img.shape[:2] if len(img.shape) == 3 else img.shape[:2]
    mask = np.zeros((h, w), dtype=np.uint8)
    if mask_data:
        if isinstance(mask_data, str):
            try:
                mask_data = json.loads(mask_data)
            except:
                mask_data = None
    if mask_data and isinstance(mask_data, list):
        all_vals = [v for rect in mask_data for v in rect if isinstance(v, (int, float))]
        is_normalized = bool(all_vals) and all(0 <= v <= 1.5 for v in all_vals)
        for rect in mask_data:
            if len(rect) == 4:
                if is_normalized:
                    x1, y1, x2, y2 = [int(v * w) if i % 2 == 0 else int(v * h) for i, v in enumerate(rect)]
                else:
                    x1, y1, x2, y2 = [int(v) for v in rect]
                y1, y2 = max(0, y1), min(h, y2)
                x1, x2 = max(0, x1), min(w, x2)
                mask[y1:y2, x1:x2] = 255
                kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (31, 31))
                mask = cv2.dilate(mask, kernel, iterations=2)
                # Feather with Gaussian blur
                mask_f = mask.astype(np.float32) / 255.0
                mask_f = cv2.GaussianBlur(mask_f, (41, 41), 0)
                mask = (mask_f > 0.4).astype(np.uint8) * 255
                kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11))
                mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel_close)
        return mask
    if np.count_nonzero(mask) == 0:
        mask = auto_detect_watermark(img)
    return mask

def auto_detect_watermark(img):
    h, w = img.shape[:2]
    mask = np.zeros((h, w), dtype=np.uint8)
    # 1. Try EasyOCR first (much better than PaddleOCR for semi-transparent text)
    boxes = _detect_text_easyocr(img, conf_threshold=0.25)
    for (x1, y1, x2, y2, text, conf) in boxes:
        exp = 10
        x1, y1 = max(0, x1 - exp), max(0, y1 - exp)
        x2, y2 = min(w, x2 + exp), min(h, y2 + exp)
        mask[y1:y2, x1:x2] = 255
    if np.count_nonzero(mask) > 0:
        logger.info("EasyOCR detected %d text regions", len(boxes))
        return mask
    # 2. Fallback: morphological top-hat for semi-transparent watermarks
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
    for ksize in [15, 25, 35]:
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (ksize, ksize))
        tophat = cv2.morphologyEx(gray, cv2.MORPH_TOPHAT, kernel)
        thresh = max(3, tophat.mean() + 2.0 * tophat.std())
        _, th_mask = cv2.threshold(tophat, thresh, 255, cv2.THRESH_BINARY)
        mask = cv2.bitwise_or(mask, th_mask)
    for ksize in [15, 25]:
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (ksize, ksize))
        blackhat = cv2.morphologyEx(gray, cv2.MORPH_BLACKHAT, kernel)
        thresh = max(3, blackhat.mean() + 2.0 * blackhat.std())
        _, bh_mask = cv2.threshold(blackhat, thresh, 255, cv2.THRESH_BINARY)
        mask = cv2.bitwise_or(mask, bh_mask)
    _, bright = cv2.threshold(gray, 235, 255, cv2.THRESH_BINARY)
    _, dark = cv2.threshold(gray, 25, 255, cv2.THRESH_BINARY_INV)
    mask = cv2.bitwise_or(mask, bright)
    mask = cv2.bitwise_or(mask, dark)
    kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel_close)
    kernel_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel_open)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    area_min, area_max = w * h * 0.00003, w * h * 0.10
    mask_clean = np.zeros_like(mask)
    for cnt in contours:
        if area_min < cv2.contourArea(cnt) < area_max:
            cv2.drawContours(mask_clean, [cnt], -1, 255, -1)
    return mask_clean

def _color_correction(inpaint_rgb, original_rgb, mask):
    """Match color/brightness of inpainted region to surrounding area."""
    mask_bool = mask > 127
    if np.count_nonzero(mask_bool) < 10:
        return inpaint_rgb
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (31, 31))
    dilated = cv2.dilate(mask, kernel, iterations=2)
    border = (dilated > 127) & (mask < 127)
    if np.count_nonzero(border) < 10:
        return inpaint_rgb
    bp = original_rgb[border].astype(np.float32)
    ip = inpaint_rgb[mask_bool].astype(np.float32)
    if len(bp) < 10 or len(ip) < 10:
        return inpaint_rgb
    result = inpaint_rgb.copy().astype(np.float32)
    for ch in range(3):
        rm, rs = bp[:, ch].mean(), bp[:, ch].std() + 1e-6
        im, is_ = ip[:, ch].mean(), ip[:, ch].std() + 1e-6
        scale = rs / is_
        shift = rm - im * scale
        channel = result[:, :, ch].copy()
        channel[mask_bool] = channel[mask_bool] * scale + shift
        result[:, :, ch] = channel
    return result.clip(0, 255).astype(np.uint8)

def do_inpaint_lama(input_path, output_path, mask_data=None, **kwargs):
    """Call standalone lama_inpaint.py script for consistent results."""
    import subprocess
    mask_str = mask_data if isinstance(mask_data, str) else json.dumps(mask_data or [])
    cmd = [
        "python3", "/home/zfz/watermark-service/lama_inpaint.py",
        input_path, output_path, mask_str
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120,
                                cwd="/home/zfz/watermark-service",
                                env={**os.environ, "VIRTUAL_ENV": "/home/zfz/watermark-service/venv",
                                     "PATH": "/home/zfz/watermark-service/venv/bin:" + os.environ.get("PATH", "")})
        if result.returncode != 0:
            logger.error("lama_inpaint.py failed: %s", result.stderr[:500])
            return {"success": False, "error": result.stderr[:200]}
        logger.info("LaMA done: %s", output_path)
        return {"success": True, "method": "lama"}
    except subprocess.TimeoutExpired:
        logger.error("lama_inpaint.py timed out")
        return {"success": False, "error": "timeout"}
    except Exception as e:
        logger.error("lama_inpaint.py error: %s", str(e))
        return {"success": False, "error": str(e)}

def do_inpaint_sd15(input_path, output_path, mask_data=None, prompt="clean, high quality, natural"):
    pipe = get_sd15()
    img = Image.open(input_path).convert("RGB")
    w, h = img.size
    mask_img = build_mask(np.array(img), mask_data)
    if np.count_nonzero(mask_img) == 0:
        img.save(output_path)
        return {"success": True, "method": "none_detected"}
    mask_pil = Image.fromarray(mask_img).convert("RGB")
    MAX_DIM = 768
    if w > MAX_DIM or h > MAX_DIM:
        ratio = min(MAX_DIM / w, MAX_DIM / h)
        nw = max(8, int(w * ratio) // 8 * 8)
        nh = max(8, int(h * ratio) // 8 * 8)
        img_resized = img.resize((nw, nh), Image.LANCZOS)
        mask_resized = mask_pil.resize((nw, nh), Image.LANCZOS)
    else:
        nw = w if w % 8 == 0 else (w // 8) * 8
        nh = h if h % 8 == 0 else (h // 8) * 8
        img_resized = img
        mask_resized = mask_pil
    neg_prompt = "watermark, text, logo, signature, low quality, blur, artifacts"
    result = pipe(prompt=prompt, negative_prompt=neg_prompt, image=img_resized,
                  mask_image=mask_resized, num_inference_steps=30, guidance_scale=7.5,
                  width=nw, height=nh).images[0]
    if result.size != (w, h):
        result = result.resize((w, h), Image.LANCZOS)
    result.save(output_path)
    logger.info("SD15 done: %s", output_path)
    return {"success": True, "method": "sd15"}

def do_inpaint_mat(input_path, output_path, mask_data=None, **kwargs):
    G = get_mat()
    device = torch.device("cuda")
    img_bgr = cv2.imread(input_path)
    if img_bgr is None:
        return {"success": False, "error": "Cannot read image"}
    h, w = img_bgr.shape[:2]
    mask_img = build_mask(img_bgr, mask_data)
    if np.count_nonzero(mask_img) == 0:
        logger.warning("NO MASK DETECTED - returning original image")
        cv2.imwrite(output_path, img_bgr)
        return {"success": True, "method": "none_detected"}
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    TILE_SIZE = 512
    if max(h, w) <= TILE_SIZE:
        result_rgb = _mat_single_pass(G, img_rgb, mask_img, device)
    else:
        result_rgb = _mat_tiled_pass(G, img_rgb, mask_img, device, tile_size=TILE_SIZE)
    mask_blurred = cv2.GaussianBlur(mask_img.astype(np.float32), (21, 21), 0) / 255.0
    mask_soft = mask_blurred[:, :, np.newaxis]
    blended = (result_rgb.astype(np.float32) * mask_soft + img_rgb.astype(np.float32) * (1 - mask_soft)).astype(np.uint8)
    result_bgr = cv2.cvtColor(blended, cv2.COLOR_RGB2BGR)
    cv2.imwrite(output_path, result_bgr)
    logger.info("MAT done: %s", output_path)
    return {"success": True, "method": "mat"}

def _mat_single_pass(G, img_rgb, mask_img, device):
    h, w = img_rgb.shape[:2]
    target = 512
    scale = min(target / h, target / w)
    new_h, new_w = int(h * scale), int(w * scale)
    img_resized = cv2.resize(img_rgb, (new_w, new_h), interpolation=cv2.INTER_AREA)
    mask_resized = cv2.resize(mask_img, (new_w, new_h), interpolation=cv2.INTER_NEAREST)
    padded_img = np.zeros((target, target, 3), dtype=np.uint8)
    padded_img[:new_h, :new_w] = img_resized
    padded_mask = np.ones((target, target), dtype=np.uint8) * 255
    padded_mask[:new_h, :new_w] = 255 - mask_resized
    img_tensor = torch.from_numpy(padded_img.astype(np.float32) / 127.5 - 1.0).permute(2, 0, 1).unsqueeze(0).to(device)
    mask_tensor = torch.from_numpy(padded_mask.astype(np.float32) / 255.0).unsqueeze(0).unsqueeze(0).to(device)
    z = torch.randn(1, G.z_dim, device=device)
    label = torch.zeros([1, G.c_dim], device=device)
    with torch.no_grad():
        output = G(img_tensor, mask_tensor, z, label, noise_mode='random')
    result = (output[0].permute(1, 2, 0).cpu().numpy() * 127.5 + 127.5).clip(0, 255).astype(np.uint8)
    result = result[:new_h, :new_w]
    result = cv2.resize(result, (w, h), interpolation=cv2.INTER_LANCZOS4)
    return result

def _mat_tiled_pass(G, img_rgb, mask_img, device, tile_size=512):
    h, w = img_rgb.shape[:2]
    result_rgb = img_rgb.copy()
    num_labels, labels = cv2.connectedComponents(mask_img)
    for label_id in range(1, num_labels):
        component = (labels == label_id).astype(np.uint8) * 255
        ys, xs = np.where(component > 0)
        if len(ys) == 0:
            continue
        cy, cx = int(ys.mean()), int(xs.mean())
        tile_y1 = max(0, cy - tile_size // 2)
        tile_y2 = min(h, tile_y1 + tile_size)
        tile_x1 = max(0, cx - tile_size // 2)
        tile_x2 = min(w, tile_x1 + tile_size)
        if tile_y2 - tile_y1 < tile_size and tile_y1 > 0:
            tile_y1 = max(0, tile_y2 - tile_size)
        if tile_x2 - tile_x1 < tile_size and tile_x1 > 0:
            tile_x1 = max(0, tile_x2 - tile_size)
        tile_img = img_rgb[tile_y1:tile_y2, tile_x1:tile_x2].copy()
        tile_mask = mask_img[tile_y1:tile_y2, tile_x1:tile_x2].copy()
        if np.count_nonzero(tile_mask) == 0:
            continue
        inpainted = _mat_single_pass(G, tile_img, tile_mask, device)
        tile_mask_bool = tile_mask > 127
        tile_mask_f = tile_mask_bool[:, :, np.newaxis].astype(np.float32)
        blended = (inpainted.astype(np.float32) * tile_mask_f + tile_img.astype(np.float32) * (1 - tile_mask_f)).astype(np.uint8)
        result_rgb[tile_y1:tile_y2, tile_x1:tile_x2] = blended
    return result_rgb

@app.on_event("startup")
async def startup():
    pass

@app.post("/inpaint")
async def inpaint(image: UploadFile = File(...), mask: str = Form(None), prompt: str = Form("clean, high quality, natural"), model: str = Form("lama")):
    content = await image.read()
    input_path = os.path.join(OUTPUT_DIR, f"input_{uuid.uuid4().hex[:8]}.png")
    output_path = os.path.join(OUTPUT_DIR, f"output_{uuid.uuid4().hex[:8]}.png")
    with open(input_path, "wb") as f:
        f.write(content)
    if model == "sd15":
        fn = do_inpaint_sd15
    elif model == "lama":
        fn = do_inpaint_lama
    elif model == "mat":
        fn = do_inpaint_mat
    else:
        model = "lama"
        fn = do_inpaint_lama
    loop = asyncio.get_event_loop()
    import functools
    result = await loop.run_in_executor(executor, functools.partial(fn, input_path, output_path, mask_data=mask, prompt=prompt))
    if not result.get("success"):
        return JSONResponse(status_code=500, content={"success": False, "error": result.get("error", "unknown")})
    return FileResponse(output_path, media_type="image/png", filename="result.png")

@app.post("/inpaint_video")
async def inpaint_video(video: UploadFile = File(...), mask: str = Form(None)):
    content = await video.read()
    input_path = os.path.join(OUTPUT_DIR, f"input_{uuid.uuid4().hex[:8]}.mp4")
    output_path = os.path.join(OUTPUT_DIR, f"output_{uuid.uuid4().hex[:8]}.mp4")
    with open(input_path, "wb") as f:
        f.write(content)
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(executor, do_inpaint_lama, input_path, output_path, mask)
    if result.get("success"):
        return FileResponse(output_path, media_type="video/mp4", filename="result.mp4")
    return JSONResponse(status_code=500, content={"success": False, "error": result.get("error", "unknown")})

@app.get("/health")
async def health():
    models = []
    if _lama_model is not None: models.append("lama")
    if _sd15_pipe is not None: models.append("sd15")
    if _mat_model is not None: models.append("mat")
    gpu_ok = torch.cuda.is_available()
    return {"status": "ok", "gpu": gpu_ok, "gpu_name": torch.cuda.get_device_name(0) if gpu_ok else None, "loaded_models": models, "default_model": "lama"}