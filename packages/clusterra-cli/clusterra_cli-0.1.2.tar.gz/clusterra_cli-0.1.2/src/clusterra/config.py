import json
from pathlib import Path
from typing import Optional
from pydantic import BaseModel
import os

CONFIG_DIR = Path.home() / ".clusterra"
CONFIG_FILE = CONFIG_DIR / "config.json"

class Config(BaseModel):
    api_url: str = "https://api.clusterra.cloud"
    api_token: Optional[str] = None

def load_config() -> Config:
    if not CONFIG_FILE.exists():
        return Config()
    
    try:
        with open(CONFIG_FILE, "r") as f:
            data = json.load(f)
            return Config(**data)
    except (json.JSONDecodeError, OSError):
        return Config()

def save_config(config: Config):
    CONFIG_DIR.mkdir(exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config.model_dump(), f, indent=2)

def get_config() -> Config:
    # Environment variables override config file
    config = load_config()
    if os.getenv("CLUSTERRA_API_URL"):
        config.api_url = os.getenv("CLUSTERRA_API_URL")
    if os.getenv("CLUSTERRA_API_TOKEN"):
        config.api_token = os.getenv("CLUSTERRA_API_TOKEN")
    return config
