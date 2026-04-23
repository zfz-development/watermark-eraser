import os, uuid
from datetime import datetime
from pathlib import Path

UPLOAD_DIR = Path(__file__).parent.parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_IMAGES = {"jpg", "jpeg", "png", "webp"}
ALLOWED_VIDEOS = {"mp4", "mov", "avi"}
MAX_IMAGE_SIZE = 30 * 1024 * 1024
MAX_VIDEO_SIZE = 500 * 1024 * 1024

def generate_file_id():
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    rand = str(uuid.uuid4().int)[:6]
    return f"FILE{ts}{rand}"

def get_file_ext(filename):
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

def save_upload_file(file_data, filename, file_id):
    ext = get_file_ext(filename)
    save_name = f"{file_id}.{ext}"
    save_path = UPLOAD_DIR / save_name
    with open(save_path, "wb") as f:
        f.write(file_data)
    return str(save_path)

def get_file_path(file_id):
    for f in UPLOAD_DIR.iterdir():
        if f.name.startswith(file_id):
            return str(f)
    return ""
