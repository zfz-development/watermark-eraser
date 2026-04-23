from app.services.watermark.base import WatermarkRemover

class PlaceholderRemover(WatermarkRemover):
    @property
    def provider_name(self):
        return "placeholder"
    @property
    def quota_remaining(self):
        return 0
    async def remove_image(self, input_path, output_path, mask=None):
        return {"success": False, "status": "pending_config"}
    async def remove_video(self, input_path, output_path, mask=None):
        return {"success": False, "status": "pending_config"}
