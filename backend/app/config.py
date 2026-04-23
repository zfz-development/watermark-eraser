from pydantic_settings import BaseSettings
from pydantic import Field
import yaml
from pathlib import Path

class Settings(BaseSettings):
    SECRET_KEY: str = "dev-secret-key"
    DATABASE_URL: str = "sqlite:///./data.db"
    SMS_VERIFY_CODE: str = "888888"
    class Config:
        env_file = ".env"

settings = Settings()

def load_yaml_config():
    p = Path(__file__).parent.parent / "config.yaml"
    if p.exists():
        with open(p, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {}

yaml_config = load_yaml_config()
