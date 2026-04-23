from app.services.watermark.base import WatermarkRemover
from app.services.watermark.placeholder import PlaceholderRemover
from app.services.watermark.opencv_remover import OpenCVRemover
from app.services.watermark.lama_remover import LamaRemover

_engines = {
    "placeholder": PlaceholderRemover,
    "opencv": OpenCVRemover,
    "lama": LamaRemover,
}

def get_engine(name="lama") -> WatermarkRemover:
    cls = _engines.get(name)
    if cls is None:
        raise ValueError(f"Unknown engine: {name}. Available: {list(_engines.keys())}")
    return cls()
