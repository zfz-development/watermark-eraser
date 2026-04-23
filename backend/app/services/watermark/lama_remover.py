"""
LaMA inpainting engine using ONNX Runtime (CPU).
Model: opencv/inpainting_lama (88MB)
Input: image [1,3,512,512] + mask [1,1,512,512] -> output [1,3,512,512]
"""
import cv2
import numpy as np
import onnxruntime as ort
from pathlib import Path
from typing import Optional
import json
import sys
from app.services.watermark.base import WatermarkRemover


class LamaRemover(WatermarkRemover):
    _session = None

    def __init__(self):
        self._load_model()

    def _load_model(self):
        if LamaRemover._session is not None:
            return
        model_path = Path(__file__).resolve().parent.parent.parent.parent.parent / "models" / "lama" / "inpainting_lama_2025jan.onnx"
        if not model_path.exists():
            raise FileNotFoundError(f"LaMA model not found: {model_path}")
        LamaRemover._session = ort.InferenceSession(str(model_path), providers=["CPUExecutionProvider"])

    @property
    def provider_name(self):
        return "lama"

    @property
    def quota_remaining(self):
        return -1

    def _inpaint(self, img: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """Run LaMA inpainting. Returns result same size as input img."""
        h, w = img.shape[:2]
        # Prepare image: BGR -> RGB, normalize to [0,1], resize to 512
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img_resized = cv2.resize(img_rgb, (512, 512))
        img_input = (img_resized.astype(np.float32) / 255.0).transpose(2, 0, 1)[np.newaxis]  # [1,3,512,512]

        # Prepare mask: resize to 512, binarize
        mask_resized = cv2.resize(mask, (512, 512))
        mask_input = (mask_resized.astype(np.float32) > 127)[np.newaxis, np.newaxis]  # [1,1,512,512]
        mask_input = mask_input.astype(np.float32)

        outputs = LamaRemover._session.run(None, {"image": img_input, "mask": mask_input})
        result = outputs[0][0].transpose(1, 2, 0)  # [512,512,3]
        result = result.clip(0, 255).astype(np.uint8)
        result = cv2.cvtColor(result, cv2.COLOR_RGB2BGR)
        result = cv2.resize(result, (w, h))
        return result

    async def remove_image(self, input_path, output_path, mask=None):
        try:
            img = cv2.imread(str(input_path))
            if img is None:
                return {"success": False, "error": f"Cannot read image: {input_path}"}
            h, w = img.shape[:2]

            if mask is not None:
                mask_img = self._build_mask(mask, w, h)
            else:
                mask_img = self._auto_detect_watermark(img)

            if mask_img is None or np.count_nonzero(mask_img) == 0:
                cv2.imwrite(str(output_path), img)
                return {"success": True, "method": "none_detected", "output": str(output_path)}

            result = self._inpaint(img, mask_img)
            cv2.imwrite(str(output_path), result)
            return {"success": True, "method": "lama_inpaint", "output": str(output_path)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def remove_video(self, input_path, output_path, mask=None):
        try:
            import subprocess, shutil

            cap = cv2.VideoCapture(str(input_path))
            if not cap.isOpened():
                return {"success": False, "error": "Cannot open video"}
            fps = cap.get(cv2.CAP_PROP_FPS) or 25
            w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            ret, first = cap.read()
            cap.release()
            if not ret:
                return {"success": False, "error": "Cannot read frames"}

            if mask is not None:
                mask_img = self._build_mask(mask, w, h)
            else:
                mask_img = self._auto_detect_watermark(first)

            if mask_img is None or np.count_nonzero(mask_img) == 0:
                shutil.copy2(str(input_path), str(output_path))
                return {"success": True, "method": "none_detected", "output": str(output_path)}

            temp_dir = Path(output_path).parent / f"_lama_frames_{Path(output_path).stem}"
            temp_dir.mkdir(exist_ok=True)

            subprocess.run(["ffmpeg", "-y", "-i", str(input_path), "-qscale:v", "2",
                          str(temp_dir / "frame_%06d.png")], capture_output=True, timeout=600)

            frames = sorted(temp_dir.glob("frame_*.png"))
            total = len(frames)
            for i, fp in enumerate(frames):
                frame = cv2.imread(str(fp))
                result = self._inpaint(frame, mask_img)
                cv2.imwrite(str(fp), result)
                if (i + 1) % 30 == 0 or (i + 1) == total:
                    print(f"LAMA video: {i+1}/{total}")

            subprocess.run(["ffmpeg", "-y", "-framerate", str(fps),
                          "-i", str(temp_dir / "frame_%06d.png"),
                          "-c:v", "libx264", "-pix_fmt", "yuv420p",
                          str(output_path)], capture_output=True, timeout=600)

            shutil.rmtree(temp_dir, ignore_errors=True)
            return {"success": True, "method": "lama_video", "frames_processed": total, "output": str(output_path)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _auto_detect_watermark(self, img):
        h, w = img.shape[:2]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Frequency domain: detect repeating patterns
        f = np.fft.fft2(gray.astype(np.float32))
        fshift = np.fft.fftshift(f)
        rows, cols = gray.shape
        crow, ccol = rows // 2, cols // 2
        r = min(rows, cols) // 8
        mask_freq = np.ones((rows, cols), dtype=np.float32)
        mask_freq[crow-r:crow+r, ccol-r:ccol+r] = 0
        f_filtered = fshift * mask_freq
        f_ishift = np.fft.ifftshift(f_filtered)
        hf_img = np.abs(np.fft.ifft2(f_ishift)).astype(np.uint8)

        # Texture analysis
        ks = max(15, min(w, h) // 20)
        if ks % 2 == 0: ks += 1
        mean = cv2.blur(gray, (ks, ks))
        mean_sq = cv2.blur(gray.astype(np.float32) ** 2, (ks, ks))
        std = np.sqrt(np.maximum(mean_sq - mean.astype(np.float32) ** 2, 0))
        std_norm = std / (std.max() + 1e-8)
        gray_norm = gray.astype(np.float32) / 255.0

        brightness = (gray_norm > 0.65).astype(np.float32)
        low_tex = (std_norm < 0.25).astype(np.float32)
        hf_norm = hf_img.astype(np.float32) / (hf_img.max() + 1e-8)
        pattern = (hf_norm > 0.25).astype(np.float32)

        combined = brightness * 0.3 + low_tex * 0.2 + pattern * 0.5
        _, binary = cv2.threshold((combined * 255).astype(np.float32), 40, 255, cv2.THRESH_BINARY)
        binary = binary.astype(np.uint8)

        kern = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kern)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kern)

        area_min, area_max = w * h * 0.0003, w * h * 0.35
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        result = np.zeros_like(binary)
        for cnt in contours:
            a = cv2.contourArea(cnt)
            if area_min < a < area_max:
                cv2.drawContours(result, [cnt], -1, 255, -1)
        result = cv2.morphologyEx(result, cv2.MORPH_CLOSE, kern)
        return result if np.count_nonzero(result) > 0 else None

    def _build_mask(self, mask_input, w, h):
        m = np.zeros((h, w), dtype=np.uint8)
        if isinstance(mask_input, str) and Path(mask_input).exists():
            raw = cv2.imread(str(mask_input), cv2.IMREAD_GRAYSCALE)
            if raw is not None:
                m = cv2.resize(raw, (w, h))
                _, m = cv2.threshold(m, 127, 255, cv2.THRESH_BINARY)
        elif isinstance(mask_input, (list, tuple)):
            for rect in mask_input:
                if len(rect) == 4:
                    x1, y1, x2, y2 = [int(v) for v in rect]
                    m[y1:y2, x1:x2] = 255
        elif isinstance(mask_input, str):
            try:
                data = json.loads(mask_input)
                if isinstance(data, list):
                    for rect in data:
                        if len(rect) == 4:
                            x1, y1, x2, y2 = [int(v) for v in rect]
                            m[y1:y2, x1:x2] = 255
            except: pass
        return m
