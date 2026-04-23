from abc import ABC, abstractmethod
from typing import Optional

class WatermarkRemover(ABC):
    @abstractmethod
    async def remove_image(self, input_path, output_path, mask=None):
        pass
    @abstractmethod
    async def remove_video(self, input_path, output_path, mask=None):
        pass
    @property
    @abstractmethod
    def provider_name(self):
        pass
    @property
    @abstractmethod
    def quota_remaining(self):
        pass
