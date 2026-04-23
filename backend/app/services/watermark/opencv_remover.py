"""
OpenCV-based watermark removal engine.
Supports: semi-transparent text watermarks, logo watermarks, corner badges.
Strategy: detect watermark region -> inpaint with telea/navier-stokes.
"""
import json
import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Tuple, List
from app.services.watermark.base import WatermarkRemover


class OpenCVRemover(WatermarkRemover):
    """Free, CPU-only watermark remover using OpenCV inpainting."""

    # Watermark detection thresholds
    MIN_ALPHA_CONFIDENCE = 30  # minimum confidence a pixel is watermark
    MIN_AREA_RATIO = 0.0005    # minimum watermark area relative to image
    MAX_AREA_RATIO = 0.40      # skip if "watermark" area is too large (probably wrong)

    @property
    def provider_name(self):
        return "opencv"

    @property
    def quota_remaining(self):
        return -1  # unlimited

    async def remove_image(self, input_path, output_path, mask=None):
        """Remove watermark from a single image.
        
        Args:
            input_path: path to input image
            output_path: path to save result
            mask: optional mask path or list of [x1,y1,x2,y2] rectangles
        """
        try:
            img = cv2.imread(str(input_path))
            if img is None:
                return {"success": False, "error": f"Cannot read image: {input_path}"}

            h, w = img.shape[:2]

            # Build mask
            if mask is not None:
                mask_img = self._build_mask_from_input(mask, w, h)
            else:
                mask_img = self._auto_detect_watermark(img)

            if mask_img is None or np.count_nonzero(mask_img) == 0:
                # No watermark detected, copy original
                cv2.imwrite(str(output_path), img)
                return {"success": True, "method": "none_detected", "output": str(output_path)}

            # Apply inpainting (Telea is faster than Navier-Stokes on CPU)
            # Use 3px radius for small text, 7px for larger areas
            white_ratio = np.count_nonzero(mask_img) / mask_img.size
            radius = 3 if white_ratio < 0.02 else 7

            result = cv2.inpaint(img, mask_img, radius, cv2.INPAINT_TELEA)

            cv2.imwrite(str(output_path), result)

            # Post-process: blend inpainted region slightly for more natural look
            if white_ratio > 0.005:
                self._refine_edges(result, mask_img, radius=2)

            cv2.imwrite(str(output_path), result)

            return {
                "success": True,
                "method": "opencv_inpaint",
                "watermark_area_ratio": round(white_ratio, 4),
                "inpaint_radius": radius,
                "output": str(output_path)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def remove_video(self, input_path, output_path, mask=None):
        """Remove watermark from video by processing frame by frame.
        
        Note: CPU processing, ~0.5-2 fps depending on resolution.
        """
        try:
            import subprocess
            
            # Extract video info
            probe = subprocess.run(
                ["ffprobe", "-v", "quiet", "-print_format", "json",
                 "-show_streams", "-show_format", str(input_path)],
                capture_output=True, text=True, timeout=30
            )
            info = json.loads(probe.stdout)
            
            video_stream = next(
                (s for s in info.get("streams", []) if s.get("codec_type") == "video"),
                None
            )
            if not video_stream:
                return {"success": False, "error": "No video stream found"}
            
            fps = float(video_stream.get("r_frame_rate", "25").split("/")[0])
            w = int(video_stream.get("width", 0))
            h = int(video_stream.get("height", 0))
            duration = float(info.get("format", {}).get("duration", 0))
            
            # First pass: detect watermark from first frame
            cap = cv2.VideoCapture(str(input_path))
            ret, first_frame = cap.read()
            cap.release()
            
            if not ret:
                return {"success": False, "error": "Cannot read video"}
            
            if mask is not None:
                mask_img = self._build_mask_from_input(mask, w, h)
            else:
                mask_img = self._auto_detect_watermark(first_frame)
            
            if mask_img is None or np.count_nonzero(mask_img) == 0:
                # No watermark, just copy
                import shutil
                shutil.copy2(str(input_path), str(output_path))
                return {"success": True, "method": "none_detected", "output": str(output_path)}
            
            # Process video: extract frames -> inpaint -> reassemble
            temp_dir = Path(output_path).parent / f"_frames_{Path(output_path).stem}"
            temp_dir.mkdir(exist_ok=True)
            
            # Extract frames
            subprocess.run([
                "ffmpeg", "-y", "-i", str(input_path),
                "-qscale:v", "2",
                str(temp_dir / "frame_%06d.png")
            ], capture_output=True, timeout=300)
            
            frames = sorted(temp_dir.glob("frame_*.png"))
            total = len(frames)
            
            for i, frame_path in enumerate(frames):
                frame = cv2.imread(str(frame_path))
                white_ratio = np.count_nonzero(mask_img) / mask_img.size
                radius = 3 if white_ratio < 0.02 else 7
                result = cv2.inpaint(frame, mask_img, radius, cv2.INPAINT_TELEA)
                cv2.imwrite(str(frame_path), result)
                
                if (i + 1) % 30 == 0:
                    print(f"Progress: {i+1}/{total}")
            
            # Reassemble video
            subprocess.run([
                "ffmpeg", "-y", "-framerate", str(fps),
                "-i", str(temp_dir / "frame_%06d.png"),
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
                str(output_path)
            ], capture_output=True, timeout=300)
            
            # Cleanup
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
            
            return {
                "success": True,
                "method": "opencv_video_inpaint",
                "frames_processed": total,
                "output": str(output_path)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _auto_detect_watermark(self, img: np.ndarray) -> Optional[np.ndarray]:
        """Auto-detect semi-transparent watermark regions.
        
        Works best with:
        - Semi-transparent text watermarks (white/gray on various backgrounds)
        - Repeating pattern watermarks
        - Fixed-position watermarks (corners, bottom)
        """
        h, w = img.shape[:2]
        
        # Convert to different color spaces for analysis
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        # Strategy 1: Detect semi-transparent white/gray text
        # Watermark text usually has similar brightness across different backgrounds
        # but slightly different from actual image content
        
        # Calculate local variance - watermark areas have low texture variance
        kernel_size = max(15, min(w, h) // 20)
        if kernel_size % 2 == 0:
            kernel_size += 1
        
        # Local mean and std dev
        mean = cv2.blur(gray, (kernel_size, kernel_size))
        mean_sq = cv2.blur(gray.astype(np.float32) ** 2, (kernel_size, kernel_size))
        std = np.sqrt(np.maximum(mean_sq - mean.astype(np.float32) ** 2, 0))
        
        # Strategy 2: Detect high-frequency repeating patterns (tiling watermarks)
        # Use frequency domain analysis
        f = np.fft.fft2(gray.astype(np.float32))
        fshift = np.fft.fftshift(f)
        magnitude = np.abs(fshift)
        
        # Suppress DC component and low frequencies
        rows, cols = gray.shape
        crow, ccol = rows // 2, cols // 2
        mask_freq = np.ones_like(magnitude)
        r = min(rows, cols) // 8
        mask_freq[crow-r:crow+r, ccol-r:ccol+r] = 0
        
        high_freq = magnitude * mask_freq
        high_freq_norm = (high_freq - high_freq.min()) / (high_freq.max() - high_freq.min() + 1e-8)
        
        # Reconstruct high-frequency component
        f_filtered = fshift * mask_freq
        f_ishift = np.fft.ifftshift(f_filtered)
        high_freq_img = np.abs(np.fft.ifft2(f_ishift)).astype(np.uint8)
        
        # Combine detection: low variance + specific brightness patterns
        # Typical watermark: slightly brighter than surroundings, low texture
        std_norm = (std - std.min()) / (std.max() - std.min() + 1e-8)
        
        # Detect watermark candidates
        # Semi-transparent white watermark: high value in gray, low texture
        gray_norm = gray.astype(np.float32) / 255.0
        mean_norm = mean.astype(np.float32) / 255.0
        
        # Pixels that are bright but in low-texture areas
        brightness_mask = gray_norm > 0.7
        low_texture_mask = std_norm < 0.3
        
        # High frequency pattern detection
        hf_norm = high_freq_img.astype(np.float32) / (high_freq_img.max() + 1e-8)
        pattern_mask = hf_norm > 0.3
        
        # Combine
        combined = (brightness_mask.astype(np.float32) * 0.3 + 
                   low_texture_mask.astype(np.float32) * 0.2 +
                   pattern_mask.astype(np.float32) * 0.5)
        
        # Threshold
        _, binary = cv2.threshold(combined.astype(np.float32) * 255, 
                                  self.MIN_ALPHA_CONFIDENCE, 255, cv2.THRESH_BINARY)
        binary = binary.astype(np.uint8)
        
        # Morphological cleanup
        kernel_small = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        kernel_medium = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel_medium)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel_small)
        
        # Fill holes in detected regions
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        area_threshold_min = w * h * self.MIN_AREA_RATIO
        area_threshold_max = w * h * self.MAX_AREA_RATIO
        
        result_mask = np.zeros_like(binary)
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area_threshold_min < area < area_threshold_max:
                cv2.drawContours(result_mask, [cnt], -1, 255, -1)
        
        # Also detect common fixed positions (corners, bottom strip)
        corner_mask = self._detect_corner_watermark(img)
        if corner_mask is not None:
            result_mask = cv2.bitwise_or(result_mask, corner_mask)
        
        # Final cleanup
        result_mask = cv2.morphologyEx(result_mask, cv2.MORPH_CLOSE, kernel_medium)
        result_mask = cv2.GaussianBlur(result_mask, (3, 3), 0)
        _, result_mask = cv2.threshold(result_mask, 127, 255, cv2.THRESH_BINARY)
        
        return result_mask if np.count_nonzero(result_mask) > 0 else None

    def _detect_corner_watermark(self, img: np.ndarray) -> Optional[np.ndarray]:
        """Detect watermarks in common positions: bottom-right corner, etc."""
        h, w = img.shape[:2]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        mask = np.zeros_like(gray)
        
        # Check bottom-right corner (very common for watermarks)
        corner_size = min(w, h) // 4
        if corner_size > 50:
            corner = gray[h-corner_size:h, w-corner_size:w]
            
            # Check if corner has text-like features (high contrast edges)
            edges = cv2.Canny(corner, 50, 150)
            edge_density = np.count_nonzero(edges) / edges.size
            
            if 0.02 < edge_density < 0.15:  # Has some edges but not too many
                # Check if it is semi-transparent (values clustered around mean)
                mean_val = np.mean(corner)
                std_val = np.std(corner)
                
                if std_val < 40:  # Low variation = possibly semi-transparent overlay
                    # Check brightness
                    if mean_val > 150:  # Bright watermark
                        mask[h-corner_size:h, w-corner_size:w] = 255
                        return mask
        
        return None

    def _build_mask_from_input(self, mask_input, w: int, h: int) -> np.ndarray:
        """Build mask from user input (file path or rectangle coordinates)."""
        mask_img = np.zeros((h, w), dtype=np.uint8)
        
        if isinstance(mask_input, str) and Path(mask_input).exists():
            # Mask from file
            m = cv2.imread(str(mask_input), cv2.IMREAD_GRAYSCALE)
            if m is not None:
                mask_img = cv2.resize(m, (w, h))
                _, mask_img = cv2.threshold(mask_img, 127, 255, cv2.THRESH_BINARY)
        elif isinstance(mask_input, (list, tuple)):
            # Rectangle coordinates [x1, y1, x2, y2]
            for rect in mask_input:
                if len(rect) == 4:
                    x1, y1, x2, y2 = [int(v) for v in rect]
                    mask_img[y1:y2, x1:x2] = 255
        elif isinstance(mask_input, str):
            # Try parsing as JSON
            import json
            try:
                data = json.loads(mask_input)
                if isinstance(data, list):
                    for rect in data:
                        if len(rect) == 4:
                            x1, y1, x2, y2 = [int(v) for v in rect]
                            mask_img[y1:y2, x1:x2] = 255
            except:
                pass
        
        return mask_img

    def _refine_edges(self, img: np.ndarray, mask: np.ndarray, radius: int = 2):
        """Slightly blend inpainted region edges for more natural look."""
        # Dilate mask slightly and feather edges
        dilated = cv2.dilate(mask, None, iterations=radius)
        edge = dilated - mask  # Edge region only
        
        if np.count_nonzero(edge) == 0:
            return
        
        # Apply slight Gaussian blur to edge region only
        blurred = cv2.GaussianBlur(img, (3, 3), 0)
        edge_mask = edge.astype(np.float32) / 255.0
        edge_mask_3ch = np.stack([edge_mask] * 3, axis=-1)
        
        img = (img * (1 - edge_mask_3ch) + blurred * edge_mask_3ch).astype(np.uint8)
